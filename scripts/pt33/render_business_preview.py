#!/usr/bin/env python3
"""PT33-B v0.2 inert offline preview renderer. No command execution, account access or apply."""
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import plan_business as core

KINDS = ('business_ids','instance_ids','service_users','systemd_units','paths','database_names','database_roles','hostnames','ports','cookie_names','backup_namespaces')
PROVIDERS = core.ACCOUNT_TYPES


def validate_inventory(inv):
    if not isinstance(inv, dict) or set(inv) != {'inventory_version','reserved'} or inv['inventory_version'] != 1:
        raise ValueError('inventory must have inventory_version=1 and reserved only')
    r = inv['reserved']
    if not isinstance(r, dict) or set(r) != set(KINDS):
        raise ValueError('inventory requires exact reserved categories')
    for kind, values in r.items():
        if not isinstance(values, list) or any(type(x) is not (int if kind == 'ports' else str) for x in values):
            raise ValueError('inventory category has invalid values: ' + kind)
        if len(values) != len(set(values)):
            raise ValueError('inventory contains duplicate values: ' + kind)
    return r


def collision_checks(plan, reserved):
    res = plan['resources']
    intended = {
        'business_ids':[plan['business_id']], 'instance_ids':[plan['instance_id']],
        'service_users':[res['service_user']], 'systemd_units':[res['systemd_unit']],
        'paths':res['roots'], 'database_names':[res['database']],
        'database_roles':[res['migrator_role'],res['runtime_role']],
        'hostnames':res['hostnames'], 'ports':[res['port']],
        'cookie_names':res['cookie_names'], 'backup_namespaces':[res['backup_namespace']]
    }
    errors = []
    for kind in KINDS:
        for item in intended[kind]:
            for used in reserved[kind]:
                if item == used or (kind == 'paths' and (item.startswith(used.rstrip('/')+'/') or used.startswith(item.rstrip('/')+'/'))):
                    errors.append(f'collision: {kind}: {item!r} conflicts with reserved {used!r}')
    return errors


def render(m, p):
    i, n, d, b = [m[x] for x in ('instance','network','database','business')]
    # Draft files deliberately use non-live .txt extensions and unmistakable markers.
    return {
        '01-READ-FIRST.txt': 'PT33-B NON-EXECUTABLE PREVIEW. NOT FOR DEPLOYMENT.\n'
            'Provider accounts, host collisions, DB privilege design and backup ownership UNVERIFIED.\n'
            'Never copy these drafts into /etc, systemd, PostgreSQL or NGINX.\n',
        '02-systemd.preview.txt': '\n'.join([
            '# PREVIEW ONLY - NOT A UNIT FILE', '[Unit]', 'Description=PROPOSED ' + b['display_name'] + ' API',
            '[Service]', 'User=' + i['service_user'], 'WorkingDirectory=' + i['service_root'] + '/current/backend',
            'EnvironmentFile=' + i['config_root'] + '/app.env',
            'ExecStart=REQUIRES_APPLICATION_COMMAND_AUDIT', '[Install]', 'WantedBy=multi-user.target', '']),
        '03-nginx.preview.txt': '\n'.join([
            '# PREVIEW ONLY - TLS, routing and headers require independent audit',
            'server {', '    listen 80;', '    server_name ' + ' '.join([n['canonical_host'],*n['aliases']]) + ';',
            '    # PROPOSED UPSTREAM: http://' + n['bind_host'] + ':' + str(n['port']),
            '    # NO ACTIVE PROXY DIRECTIVES: security/TLS review required', '}', '']),
        '04-environment.preview.txt': '\n'.join([
            '# PREVIEW ONLY - DO NOT USE AS RUNTIME ENVIRONMENT',
            '# No secret values. Bindings must be resolved via separately commissioned credential store.',
            'BUSINESS_ID=' + b['id'], 'INSTANCE_ID=' + i['id'],
            'DB_NAME=' + d['name'], 'DB_RUNTIME_ROLE=' + d['runtime_role'],
            'DB_MIGRATOR_ROLE=' + d['migrator_role'],
            'DB_RUNTIME_SECRET_REFERENCE=' + d['runtime_secret_ref'],
            'DB_MIGRATOR_SECRET_REFERENCE=' + d['migrator_secret_ref'],
            'SESSION_COOKIE_NAME=' + n['session_cookie_name'],
            'CSRF_COOKIE_NAME=' + n['csrf_cookie_name'],
            'APP_SETTINGS_MAPPING=REQUIRES_SOURCE_AUDIT', '']),
        '05-database.preview.txt': '\n'.join([
            '# NONEXECUTABLE DATABASE DESIGN NOTES - NOT SQL',
            'database: ' + d['name'], 'migrator_role: ' + d['migrator_role'],
            'runtime_role: ' + d['runtime_role'],
            'roles_distinct: required', 'owner_privilege_model: review required',
            'password_values: never included', 'fresh_schema_only: required', '']),
        '06-provider-ownership.preview.json': json.dumps({
            'business_id':b['id'], 'account_isolation':'independent per business',
            'required_accounts':[{'provider':k, 'owner_business_id':b['id'],
                                  'ownership_verified':False, 'credentials_verified':False,
                                  'billing_mfa_recovery_verified':False} for k in PROVIDERS]
        }, sort_keys=True, indent=2)+'\n'
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--schema', required=True)
    parser.add_argument('--inventory', required=True, help='Explicit supplied OFFLINE inventory, not live inspection')
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--output-dir', required=True, help='Must be a previously nonexistent directory')
    args=parser.parse_args(argv)
    if not re.fullmatch('[0-9a-f]{40}', args.source_revision):
        parser.error('exact 40 character lowercase Git SHA required')
    try:
        m=json.loads(Path(args.manifest).read_text())
        schema=json.loads(Path(args.schema).read_text())
        inv=json.loads(Path(args.inventory).read_text())
        if not isinstance(m,dict) or not isinstance(schema,dict):
            raise ValueError('manifest/schema must be objects')
        errors=core.validate_schema(m,schema)
        if not errors: errors=core.semantic_checks(m)
        if errors: raise ValueError('; '.join(errors))
        reserved=validate_inventory(inv)
        p=core.plan(m,args.source_revision)
        errors=collision_checks(p,reserved)
        if errors: raise ValueError('; '.join(errors))
        # macOS uses /var -> /private/var for its OS-managed temporary directory.
        # Permit that precise system alias only, never arbitrary ancestor symlinks.
        output=Path(args.output_dir).expanduser().absolute()
        if output.exists() or output.is_symlink():
            raise ValueError('output path already exists; overwrite forbidden')
        mac_temp=Path(tempfile.gettempdir()).resolve()
        temp_root=Path('/private/var/folders')
        is_macos_temp=(sys.platform == 'darwin' and
                       mac_temp.is_relative_to(temp_root) and
                       output.resolve(strict=False).is_relative_to(mac_temp))
        for parent in [output,*output.parents]:
            if parent.is_symlink():
                if not (is_macos_temp and parent == Path('/var') and
                        parent.resolve() == Path('/private/var')):
                    raise ValueError('symlink in output path forbidden')
        banned=('/etc','/srv','/var','/usr','/bin','/sbin','/root','/proc','/sys','/dev',
                '/private/etc','/private/var','/private/tmp')
        lexical=os.path.normpath(str(output))
        real=str(output.resolve(strict=False))
        def protected(path):
            return any(path == root or path.startswith(root+'/') for root in banned)
        if ((protected(lexical) or protected(real)) and not is_macos_temp) or '..' in output.parts:
            raise ValueError('unsafe output directory')
        files=render(m,p)
        p['inventory_sha256']=hashlib.sha256(Path(args.inventory).read_bytes()).hexdigest()
        p['manifest_sha256']=hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest()
        p['inventory_scope']='supplied_offline_only'
        p['inventory_live_verified']=False
        p['ready_to_apply']=False
        files['00-plan.json']=json.dumps(p,indent=2,sort_keys=True)+'\n'
        output.mkdir(parents=True,exist_ok=False)
        for filename, content in sorted(files.items()):
            (output / filename).write_text(content)
        print('PASS: wrote '+str(len(files))+' NON-EXECUTABLE preview files to '+str(output))
        print('NOTE: inventory and provider ownership remain UNVERIFIED against live resources; ready_to_apply=false')
        return 0
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print('PT33-B PREVIEW REFUSED: '+str(exc),file=sys.stderr)
        return 2

if __name__=='__main__': sys.exit(main())
