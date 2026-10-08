#!/usr/bin/env python3
"""PT33-B v0.3 read-only scoped host observations. No SSH, network, SQL, or provider access."""
import argparse
import datetime as dt
import json
import os
import platform
import pwd
import re
import socket
import subprocess
import sys
from pathlib import Path

KINDS = ('service_user', 'systemd_unit', 'service_root', 'config_root', 'state_root', 'port')

def local_observations(manifest, system=None, runner=None):
    system = system or platform.system()
    i, n = manifest['instance'], manifest['network']
    targets = {
        'service_user': i['service_user'], 'systemd_unit': i['systemd_unit'],
        'service_root': i['service_root'], 'config_root': i['config_root'],
        'state_root': i['state_root'], 'port': n['port'],
    }
    found = {}
    try:
        pwd.getpwnam(i['service_user'])
        found['service_user'] = 'present'
    except KeyError:
        found['service_user'] = 'absent_in_local_passwd_database'
    except (OSError, PermissionError):
        found['service_user'] = 'unverified'
    if system == 'Linux':
        unit_paths = [Path('/etc/systemd/system') / i['systemd_unit'], Path('/run/systemd/system') / i['systemd_unit'], Path('/usr/lib/systemd/system') / i['systemd_unit'], Path('/lib/systemd/system') / i['systemd_unit']]
        found['systemd_unit'] = 'present' if any(p.exists() or p.is_symlink() for p in unit_paths) else 'unverified_systemd_other_paths_possible'
    else:
        found['systemd_unit'] = 'not_applicable_non_linux'
    for key in ('service_root','config_root','state_root'):
        p = Path(i[key])
        found[key] = 'present' if p.exists() or p.is_symlink() else 'absent_at_inspection'
    # Running lsof reads OS socket metadata only, never service arguments or environment.
    run = runner or subprocess.run
    try:
        process = run(['lsof','-nP','-iTCP','-sTCP:LISTEN','-F','n'], capture_output=True, text=True, timeout=8, check=False)
        if process.returncode not in (0,1):
            found['port'] = 'unverified_lsof_error'
        else:
            observed_ports = set()
            for line in process.stdout.splitlines():
                if not line.startswith('n'):
                    continue
                match = re.search(r':([0-9]{1,5})(?:\s|$)', line[1:])
                if match:
                    observed_ports.add(int(match.group(1)))
            found['port'] = 'listening' if n['port'] in observed_ports else 'not_observed_in_visible_tcp_listeners'
    except (OSError, subprocess.TimeoutExpired):
        found['port'] = 'unverified_lsof_unavailable'
    return targets, found


def build(manifest, system=None, runner=None):
    targets, states = local_observations(manifest, system, runner)
    return {
        'evidence_version': 1,
        'collected_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'host_identity': {'hostname': socket.gethostname(), 'os': system or platform.system()},
        'scope': 'local_machine_only',
        'method': 'read_only_scoped_observations',
        'target_business_id': manifest['business']['id'],
        'target_instance_id': manifest['instance']['id'],
        'observations': {key: {'target': targets[key], 'observation': states[key],
            'collision': states[key] in ('present','listening'),
            'availability_verified': False} for key in KINDS},
        'unverified': ['postgresql_database_and_roles', 'dns_and_tls', 'nginx_effective_configuration',
            'firewall_and_udp', 'backup_namespace_and_restore', 'provider_account_ownership',
            'other_hosts', 'filesystem_permissions_and_mounts'],
        'ready_to_apply': False,
        'warning': 'Local observations are not proof of resource availability. Do not treat this as provisioning authorization.'
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--schema', required=True)
    parser.add_argument('--output', required=True, help='New local JSON filename; must not exist')
    args = parser.parse_args(argv)
    try:
        # Local imports after argument parsing support test import and no unintended side effects.
        import plan_business as planner
        m = json.loads(Path(args.manifest).read_text())
        schema = json.loads(Path(args.schema).read_text())
        errors = planner.validate_schema(m, schema)
        if not errors:
            errors = planner.semantic_checks(m)
        if errors:
            raise ValueError('invalid manifest: ' + '; '.join(errors))
        target = Path(args.output).expanduser().absolute()
        if target.exists() or target.is_symlink():
            raise ValueError('output already exists; refusing overwrite')
        for part in target.parents:
            if part.is_symlink():
                raise ValueError('symlinked output parent refused')
        if not target.parent.is_dir():
            raise ValueError('output parent must already exist')
        if os.path.normpath(str(target)).startswith(('/etc/','/srv/','/var/','/usr/','/root/','/proc/','/sys/','/dev/')):
            raise ValueError('system destination refused')
        evidence = build(m)
        payload = (json.dumps(evidence, indent=2, sort_keys=True) + '\n').encode()
        # Atomic exclusive creation, mode 0600; no overwriting concurrent files.
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as out:
            out.write(payload)
        print('PASS: read-only host observations saved:', target)
        print('NOTE: NOT proof of availability; DB/provider/remote checks UNVERIFIED; ready_to_apply=false')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('PT33-B INVENTORY REFUSED:', exc, file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
