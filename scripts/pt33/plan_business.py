#!/usr/bin/env python3
"""PT33-B v0.1: pure offline validation and planning. No apply/render/write modes."""
import argparse
import hashlib
import ipaddress
import json
import re
import sys
from pathlib import Path, PurePosixPath

PROTECTED = ('dacqua', 'dacqua-dolce', 'dacqua_dolce', 'dacquadolce.com')
ALLOWED_MODES = {'new_business'}
ACCOUNT_TYPES = ('domain_registrar', 'hosting', 'proton_mail', 'postmark', 'cloudflare',
                 'better_stack', 'aws_storage', 'tax_provider', 'payment_provider')


def validate_schema(value, spec, where='$'):
    errors = []
    expected = spec.get('type')
    if expected:
        allowed = expected if isinstance(expected, list) else [expected]
        kind = 'null' if value is None else ('boolean' if isinstance(value, bool) else 'integer' if isinstance(value, int) else 'string' if isinstance(value, str) else 'array' if isinstance(value, list) else 'object' if isinstance(value, dict) else 'other')
        if kind not in allowed:
            return [f'{where}: expected {allowed}, got {kind}']
    if 'const' in spec and value != spec['const']:
        errors.append(f'{where}: must equal {spec["const"]!r}')
    if 'enum' in spec and value not in spec['enum']:
        errors.append(f'{where}: invalid enum value')
    if isinstance(value, str):
        if len(value) < spec.get('minLength', 0):
            errors.append(f'{where}: too short')
        if 'pattern' in spec and not re.fullmatch(spec['pattern'], value):
            errors.append(f'{where}: invalid format')
    if isinstance(value, int) and not isinstance(value, bool):
        if value < spec.get('minimum', value) or value > spec.get('maximum', value):
            errors.append(f'{where}: integer out of range')
    if isinstance(value, dict):
        for key in spec.get('required', []):
            if key not in value:
                errors.append(f'{where}.{key}: missing')
        if spec.get('additionalProperties') is False:
            for key in sorted(set(value) - set(spec.get('properties', {}))):
                errors.append(f'{where}.{key}: unknown field')
        for key, child in spec.get('properties', {}).items():
            if key in value:
                errors += validate_schema(value[key], child, f'{where}.{key}')
    if isinstance(value, list):
        if spec.get('uniqueItems') and len(set(map(json.dumps, value))) != len(value):
            errors.append(f'{where}: duplicate entries')
        for index, item in enumerate(value):
            errors += validate_schema(item, spec.get('items', {}), f'{where}[{index}]')
    return errors


def semantic_checks(m):
    errors = []
    business, instance, net, db, provider, backup, data = (
        m[x] for x in ('business', 'instance', 'network', 'database', 'providers', 'backup', 'data'))
    if data['mode'] != 'fresh' or data['seed_profile'] is not None:
        errors.append('new_business: requires fresh database and null seed_profile (unapproved application seed)')
    if not instance['id'].startswith(business['id'] + '-'):
        errors.append('instance.id must begin with business.id followed by hyphen')
    if instance['environment'] not in instance['id'].split('-'):
        errors.append('instance.id must include environment token')
    for group in (('service_root', 'config_root', 'state_root'),):
        for key in group:
            path = instance[key]
            normalized = str(PurePosixPath(path))
            if not path.startswith('/') or '//' in path or '/./' in path or '..' in path.split('/') or normalized != path or path in ('/srv', '/etc', '/var/lib'):
                errors.append(f'instance.{key}: unsafe path')
    for key, prefix in [('service_root', '/srv/'), ('config_root', '/etc/'), ('state_root', '/var/lib/')]:
        if not instance[key].startswith(prefix) or instance[key] == prefix.rstrip('/'):
            errors.append(f'instance.{key}: unexpected root')
    identities = [('business.id', business['id']), ('instance.id', instance['id']),
                  ('instance.service_user', instance['service_user']), ('instance.systemd_unit', instance['systemd_unit']),
                  ('database.name', db['name']), ('database.migrator_role', db['migrator_role']),
                  ('database.runtime_role', db['runtime_role']), ('backup.namespace', backup['namespace']),
                  ('network.canonical_host', net['canonical_host'])]
    identities += [(f'instance.{key}', instance[key]) for key in ('service_root', 'config_root', 'state_root')]
    identities += [(f'network.{key}', net[key]) for key in ('session_cookie_name', 'csrf_cookie_name')]
    for key, value in identities:
        if any(term in value.lower() for term in PROTECTED):
            errors.append(f'{key}: protected D\u2019Acqua identity collision')
    if db['name'] in (db['runtime_role'], db['migrator_role']) or db['runtime_role'] == db['migrator_role']:
        errors.append('database identifiers/roles must be distinct')
    if db['runtime_secret_ref'] == db['migrator_secret_ref']:
        errors.append('database secret bindings must be distinct')
    if net['session_cookie_name'] == net['csrf_cookie_name']:
        errors.append('cookie names must be distinct')
    if net['canonical_host'] in net['aliases'] or len(set(net['aliases'])) != len(net['aliases']):
        errors.append('network hostnames must be unique')
    hosts = [net['canonical_host'], *net['aliases']]
    for host in hosts:
        if host != host.lower() or not re.fullmatch(r'(?=.{4,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', host):
            errors.append('invalid DNS hostname: ' + host)
    if not re.fullmatch(r'[a-z][a-z0-9_-]{2,63}', backup['namespace']):
        errors.append('backup.namespace: invalid format')
    if provider['email_from'] is not None and not provider['email_from'].lower().endswith('@' + net['canonical_host']):
        errors.append('providers.email_from must use canonical hostname for this initial contract')
    bindings = [(k, v) for k, v in {**db, **provider, **backup}.items() if k.endswith(('_ref', 'credential_ref')) and v is not None]
    for key, value in bindings:
        if not re.fullmatch(r'[a-z][a-z0-9_]{2,62}', value):
            errors.append(f'{key}: secret reference must be a logical identifier (not a secret value)')
        if any(term in value.lower() for term in PROTECTED):
            errors.append(f'{key}: protected D\u2019Acqua secret binding')
    if (provider['turnstile_site_key_ref'] is None) != (provider['turnstile_secret_ref'] is None):
        errors.append('turnstile requires both logical bindings or neither')
    if (provider['postmark_token_ref'] is None) != (provider['email_from'] is None):
        errors.append('Postmark sender and logical token binding must be set together')
    return sorted(set(errors))


def plan(manifest, source_sha):
    i, n, b, d = (manifest[x] for x in ('instance', 'network', 'business', 'database'))
    return {
        'plan_version': 1, 'mode': 'new_business', 'execution': 'read_only_dry_run',
        'source_revision': source_sha, 'business_id': b['id'], 'instance_id': i['id'],
        'resources': {
            'service_user': i['service_user'], 'systemd_unit': i['systemd_unit'],
            'roots': [i['service_root'], i['config_root'], i['state_root']],
            'database': d['name'], 'migrator_role': d['migrator_role'], 'runtime_role': d['runtime_role'],
            'bind_host': n['bind_host'], 'port': n['port'],
            'hostnames': [n['canonical_host'], *n['aliases']],
            'cookie_names': [n['session_cookie_name'], n['csrf_cookie_name']],
            'backup_namespace': manifest['backup']['namespace']},
        'provider_accounts_required': [{'provider': p, 'separate_business_account': True, 'ownership_verified': False} for p in ACCOUNT_TYPES],
        'required_external_checks': [
            'Verify each provider is owned and billed independently for this business, with its own MFA/recovery and credentials',
            'Verify target host is authorized and free of user/path/unit/port/NGINX collisions',
            'Verify target PostgreSQL instance has no DB/role collisions and role privileges are isolated',
            'Verify DNS ownership, sender authentication, Turnstile binding and backup destination separately',
            'Rehearse secure provisioning and negative isolation tests before any apply implementation'],
        'stages': ['manifest and source verification', 'provider account ownership', 'host security preflight',
                   'identity/path collision review', 'database privilege plan', 'secret custody plan',
                   'immutable release build plan', 'fresh migrations/no inherited data', 'NGINX/TLS/provider review',
                   'backup and restore rehearsal', 'security and readiness acceptance', 'activation authorization'],
        'ready_to_apply': False,
        'disclaimer': 'Offline plan only. No live resource/account collision or ownership checks have been performed.'
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', required=True)
    p.add_argument('--schema', required=True)
    p.add_argument('--source-revision', required=True)
    p.add_argument('--mode', default='new_business', choices=sorted(ALLOWED_MODES))
    p.add_argument('--format', default='json', choices=['json', 'summary'])
    args = p.parse_args()
    if not re.fullmatch(r'[0-9a-f]{40}', args.source_revision):
        p.error('source revision must be an exact lowercase 40-character Git SHA')
    try:
        m = json.loads(Path(args.manifest).read_text())
        schema = json.loads(Path(args.schema).read_text())
    except (ValueError, OSError) as exc:
        p.error(f'cannot load manifest/schema: {exc}')
    if not isinstance(m, dict) or not isinstance(schema, dict):
        p.error('manifest and schema must be JSON objects')
    issues = validate_schema(m, schema)
    if not issues:
        issues += semantic_checks(m)
    if issues:
        print('PT33-B VALIDATION FAILED\n' + '\n'.join(' - '+s for s in issues), file=sys.stderr)
        return 2
    result = plan(m, args.source_revision)
    result['manifest_sha256'] = hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest()
    if args.format == 'json':
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f'PASS: offline manifest validation for {result["instance_id"]}')
        print('NOTE: all live collisions/provider ownership remain UNVERIFIED; no resources changed')
    return 0

if __name__ == '__main__':
    sys.exit(main())
