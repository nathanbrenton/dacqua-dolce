#!/usr/bin/env python3
"""Conservative PT33 v0.5 Linux resource observations. No privileged escalation.

Deliberately never claims COMPLETE from enumerations that may omit resources.
PostgreSQL and NGINX inspection require separate explicit opt-in; no secret export.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import platform
import re
import socket
import subprocess
import sys

from evidence_contract import PROVIDERS, SECTIONS, EXTRA_SECTIONS, NGINX_SECTIONS, section_digest, validate_v2


def _section(values=(), status='partial', method='not_inspected', detail=''):
    values = sorted(set(values))
    return {'status': status, 'values': values, 'method': method,
            'detail': detail, 'sha256': section_digest(values)}


def _run(argv, runner):
    try:
        result = runner(argv, capture_output=True, text=True, timeout=8, check=False,
                        env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C'})
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or len(result.stdout) > 2_000_000:
        return None
    return result.stdout


def collect_sections(runner=subprocess.run, *, candidate_paths=(), path_probe=None, nginx_runner=None, postgres_runner=None):
    """Read identifiers only; failures are distinct from known resource collisions."""
    sections = {name: _section(status='unsupported', method='not_collected',
                              detail='No safe exhaustive metadata collection configured') for name in SECTIONS + EXTRA_SECTIONS + NGINX_SECTIONS}
    # Never read shadow databases. NSS enumeration is not an exhaustive directory lookup.
    passwd = _run(['getent', 'passwd'], runner)
    if passwd is None:
        for key in ('service_users', 'unix_uids'):
            sections[key] = _section(status='failed', method='getent_passwd', detail='NSS command unavailable or failed')
    else:
        names, uids, malformed = [], [], False
        for line in passwd.splitlines():
            fields = line.split(':')
            if (len(fields) != 7 or not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_.-]*\$?', fields[0])
                    or not fields[2].isdigit() or int(fields[2]) > 4294967295):
                malformed = True
                break
            names.append(fields[0]); uids.append(int(fields[2]))
        for key, values in (('service_users', names), ('unix_uids', uids)):
            sections[key] = _section(values, 'partial', 'getent_passwd',
                'Malformed NSS row' if malformed else 'NSS cannot prove namespace absence')
    groups = _run(['getent', 'group'], runner)
    if groups is None:
        for key in ('unix_groups', 'unix_gids'):
            sections[key] = _section(status='failed', method='getent_group', detail='NSS group query unavailable or failed')
    else:
        names, gids, malformed = [], [], False
        for line in groups.splitlines():
            fields = line.split(':')
            if (len(fields) != 4 or not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_.-]*\$?', fields[0])
                    or not fields[2].isdigit() or int(fields[2]) > 4294967295):
                malformed = True
                break
            names.append(fields[0]); gids.append(int(fields[2]))
        for key, values in (('unix_groups', names), ('unix_gids', gids)):
            sections[key] = _section(values, 'partial', 'getent_group',
                'Malformed NSS group row' if malformed else 'NSS cannot prove namespace absence')
    # Unit files and loaded units are different views. Both remain partial:
    # transient names, aliases, generators, namespaces and races are possible.
    sources = (
        (['systemctl', 'list-unit-files', '--all', '--no-pager', '--no-legend', '--plain'], 'unit_files'),
        (['systemctl', 'list-units', '--all', '--no-pager', '--no-legend', '--plain'], 'loaded_units'),
    )
    known, failed, malformed = [], False, False
    for argv, label in sources:
        output = _run(argv, runner)
        if output is None:
            failed = True
            continue
        for line in output.splitlines():
            fields = line.split()
            if not fields or not fields[0].endswith(('.service', '.timer', '.socket', '.target', '.path', '.mount', '.slice', '.automount', '.swap')):
                malformed = True
                continue
            if len(fields) < 2:
                malformed = True
                continue
            known.append(fields[0])
    sections['systemd_units'] = _section(known, 'partial' if known or not failed else 'failed',
        'systemctl_unit_files_and_loaded',
        'Partial: installed and loaded identifiers; one source failed or malformed' if failed or malformed
        else 'Partial: aliases, generators and future/transient units may be omitted')
    # Port evidence remains conservative: a listener on any address may conflict.
    # Bind-address observations are additional identifiers, never allocation clearance.
    socks = _run(['ss', '-H', '-ltn'], runner)
    if socks is None:
        for key in ('ports', 'tcp_bindings'):
            sections[key] = _section(status='failed', method='ss_listening_tcp', detail='Socket query unavailable or failed')
    else:
        ports, bindings, malformed = [], [], False
        for line in socks.splitlines():
            fields = line.split()
            if len(fields) < 5 or fields[0] != 'LISTEN':
                malformed = True
                break
            endpoint = fields[3]
            match = re.fullmatch(r'(.+):([0-9]{1,5})', endpoint)
            if not match or not 1 <= int(match.group(2)) <= 65535:
                malformed = True
                break
            address, port = match.group(1), int(match.group(2))
            # Accept numeric IPv4, bracketed IPv6, or ss wildcard only.
            import ipaddress
            try:
                if address not in ('*', '[::]'):
                    ipaddress.ip_address(address.strip('[]'))
            except ValueError:
                malformed = True
                break
            ports.append(port)
            bindings.append(f'{address}:{port}')
        for key, values in (('ports', ports), ('tcp_bindings', bindings)):
            sections[key] = _section(values, 'partial', 'ss_listening_tcp',
                'Malformed/unknown listener; partial observations only' if malformed
                else 'Visible TCP listeners only; namespaces and future binds unknown')
    # Only explicitly supplied proposed resource roots are probed; neither /srv
    # nor any other large directory tree is walked. Existing ancestor symlinks
    # are conservatively treated as path collisions at the proposed root.
    # A missing path is NOT clearance: inspection remains partial.
    if candidate_paths:
        probe = path_probe or os.lstat
        found, errors = [], False
        for raw in candidate_paths:
            if not isinstance(raw, str) or not raw.startswith('/') or '\x00' in raw or '..' in Path(raw).parts:
                raise ValueError('unsafe candidate path')
            target = Path(raw)
            if str(target) == '/':
                raise ValueError('root is not a candidate path')
            chain = [target, *list(target.parents)[:-1]]
            for item in chain:
                try:
                    import stat
                    metadata = probe(str(item))
                    if item == target or stat.S_ISLNK(metadata.st_mode):
                        found.append(str(target))
                        break
                except FileNotFoundError:
                    continue
                except (OSError, ValueError):
                    errors = True
                    break
        sections['paths'] = _section(found, 'partial', 'candidate_path_lstat',
            'Partial: candidate roots and ancestor symlinks only; errors or denied access' if errors
            else 'Partial: target existence only; no full filesystem or mount namespace inventory')
    else:
        sections['paths'] = _section(status='unsupported', method='not_collected', detail='No candidate paths supplied')
    # nginx -T validates/includes the effective on-disk configuration but can
    # expose secret-bearing directives. Raw stdout/stderr are NEVER serialized,
    # logged, or returned. This is opt-in and remains partial even on success.
    if nginx_runner is not None:
        sections['nginx_server_names'] = inspect_nginx_names(nginx_runner)
    if postgres_runner is not None:
        sections.update(inspect_postgres_metadata(postgres_runner))
    return sections


# Local PostgreSQL metadata only. The environment supplied by _run strips PG*
# variables, so neither PGHOST/PGPASSWORD nor service files are consulted through
# environment variables. -X disables psqlrc; -w disables password prompts.
# A connection failure means failed inspection, NEVER an empty namespace.
_PG_IDENTIFIER = re.compile(r"[^\x00-\x1f\x7f]{1,63}")


def inspect_postgres_metadata(runner):
    """Opt-in non-interactive local catalog names; do not fetch records or secrets."""
    queries = {
        'database_names': ("SELECT datname FROM pg_catalog.pg_database ORDER BY datname", 'pg_database_datname'),
        'database_roles': ("SELECT rolname FROM pg_catalog.pg_roles ORDER BY rolname", 'pg_roles_rolname'),
    }
    output = {}
    for category, (query, method) in queries.items():
        argv = ['psql', '-X', '-w', '-A', '-t', '-d', 'postgres', '-c', query]
        data = _run(argv, runner)
        if data is None:
            output[category] = _section(status='failed', method=method,
                detail='Local metadata query failed or was inaccessible; no absence assertion')
            continue
        values = data.splitlines()
        # Reject partial/malformed output rather than silently dropping entries.
        if any(not _PG_IDENTIFIER.fullmatch(v) for v in values) or len(values) != len(set(values)):
            output[category] = _section(status='failed', method=method,
                detail='Malformed or contradictory catalog identifiers; no absence assertion')
            continue
        output[category] = _section(values, 'partial', method,
            'One local PostgreSQL cluster only; visibility, other clusters and races unverified')
    return output


# Restrict observations to harmless DNS identifiers; reject quoted, variable,
# regex and non-ASCII names. Wildcards are retained as collision warnings.
_NGINX_HOST = re.compile(r'(?:\*\.)?[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?')


def inspect_nginx_names(runner):
    """Opt-in sanitized hostnames from nginx -T; never provide raw output."""
    output = _run(['nginx', '-T'], runner)
    if output is None:
        return _section(status='failed', method='nginx_T_sanitized',
                        detail='NGINX test/dump inaccessible or failed; no absence assertion')
    names = []
    ambiguous = False
    # nginx -T emits file markers and include expansion; inspect only bounded
    # single-line server_name directives. Complex/multiline directives are not
    # defensibly parsed here and require separate review.
    for line in output.splitlines():
        stripped = line.split('#', 1)[0].strip()
        if not re.match(r'^server_name(?:\s|;)', stripped):
            continue
        if not stripped.endswith(';') or '{' in stripped or '}' in stripped:
            ambiguous = True
            continue
        tokens = stripped[:-1].split()
        if len(tokens) < 2:
            ambiguous = True
            continue
        for name in tokens[1:]:
            if name == '_' or name == '':
                ambiguous = True
            elif _NGINX_HOST.fullmatch(name) and '..' not in name:
                names.append(name.lower().rstrip('.'))
            else:
                ambiguous = True
    return _section(names, 'partial', 'nginx_T_sanitized',
                    'Partial: complex/default/wildcard/listen/include semantics need manual review' +
                    ('; ambiguous server_name found' if ambiguous else ''))


def build_v2(manifest, *, runner=subprocess.run, system=None, now=None, hostname=None, nginx_runner=None, postgres_runner=None):
    if (system or platform.system()) != 'Linux':
        raise ValueError('Debian/Linux-only v0.5 collector; use legacy collector on macOS')
    instance = manifest['instance']['id']
    if not isinstance(instance, str) or not instance or len(instance) > 128:
        raise ValueError('invalid target instance')
    stamp = now or dt.datetime.now(dt.timezone.utc)
    if stamp.tzinfo is None or stamp.utcoffset() != dt.timedelta():
        raise ValueError('collection clock must use UTC')
    # Host fingerprint is explicitly a label, not independently authenticated.
    node = hostname if hostname is not None else socket.gethostname()
    host_id = re.sub(r'[^A-Za-z0-9_.-]', '_', node)[:128] or 'unknown'
    evidence = {
        'evidence_version': 2, 'resource_scope': 'single_debian_host_read_only',
        'host_id': host_id, 'target_instance_id': instance,
        'source': 'read_only_host_collector', 'collector_version': 'pt33-v0.5-increment6',
        'collected_at_utc': stamp.isoformat(), 'sections': collect_sections(runner, candidate_paths=[manifest['instance'][key] for key in ('service_root', 'config_root', 'state_root') if key in manifest['instance']], nginx_runner=nginx_runner, postgres_runner=postgres_runner),
        'external_verification': {provider: 'unverified' for provider in PROVIDERS},
        'ready_to_apply': False,
    }
    validate_v2(evidence, now=stamp)
    return evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New output path; refuses overwrite')
    parser.add_argument('--inspect-nginx', action='store_true', help='Opt in to in-memory nginx -T parsing; raw config never exported')
    parser.add_argument('--inspect-postgres', action='store_true', help='Opt in to local non-interactive PostgreSQL catalog-name queries')
    args = parser.parse_args(argv)
    try:
        if platform.system() != 'Linux':
            raise ValueError('Linux-only collector')
        manifest = json.loads(args.manifest.read_text())
        # Reuse canonical schema and semantic validation; never bypass planner.
        import plan_business
        schema = json.loads((Path(__file__).resolve().parents[2] / 'docs/production/pt33/business-manifest.schema.json').read_text())
        errors = plan_business.validate_schema(manifest, schema) or plan_business.semantic_checks(manifest)
        if errors:
            raise ValueError('invalid manifest: ' + '; '.join(errors))
        target = args.output.expanduser().absolute()
        if any(p.is_symlink() for p in (target, *target.parents)) or not target.parent.is_dir():
            raise ValueError('unsafe output path')
        if str(target).startswith(('/etc/', '/srv/', '/var/', '/usr/', '/root/', '/proc/', '/sys/', '/dev/')):
            raise ValueError('system output path refused')
        evidence = build_v2(manifest, nginx_runner=subprocess.run if args.inspect_nginx else None, postgres_runner=subprocess.run if args.inspect_postgres else None)
        payload = (json.dumps(evidence, indent=2, sort_keys=True) + '\n').encode()
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as output:
            output.write(payload)
        print('PASS: bounded read-only Debian evidence written:', target)
        print('NOTE: partial/unsupported coverage, no deployment clearance; ready_to_apply=false')
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print('PT33-B COLLECTION REFUSED:', exc, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
