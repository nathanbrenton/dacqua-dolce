#!/usr/bin/env python3
"""PT36 supplementary *partial* host metadata; not a provisioning authorization.

Run as the ordinary SSH user, never as root. sudo -n is confined to two
hardcoded read-only subprocesses. Raw nginx configuration is held in memory
only and never printed, logged, or serialized.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

HOST_PATTERN = re.compile(r'(?:\*\.)?[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?')
PG_PATTERN = re.compile(r'[^\x00-\x1f\x7f]{1,63}')
LIMIT = 2_000_000
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C', 'HOME': '/nonexistent', 'PGCONNECT_TIMEOUT': '3'}


def section(values=(), status='failed', detail=''):
    values = sorted(set(values))
    digest = hashlib.sha256(json.dumps(values, ensure_ascii=True, separators=(',', ':')).encode('ascii')).hexdigest()
    return {'status': status, 'values': values, 'detail': detail, 'sha256': digest}


def invoke(argv, runner=subprocess.run):
    try:
        result = runner(argv, capture_output=True, text=False, timeout=12, check=False, env=ENV)
        if result.returncode or len(result.stdout) > LIMIT:
            return None
        return result.stdout.decode('utf-8', errors='strict')
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        return None


def nginx_names(raw):
    names, ambiguous = [], False
    for line in raw.splitlines():
        line = line.split('#', 1)[0].strip()
        if not re.match(r'^server_name(?:\s|;)', line):
            continue
        if not line.endswith(';') or '{' in line or '}' in line:
            ambiguous = True
            continue
        tokens = line[:-1].split()
        if len(tokens) < 2:
            ambiguous = True
            continue
        for token in tokens[1:]:
            if token == '_' or '..' in token or not HOST_PATTERN.fullmatch(token):
                ambiguous = True
            else:
                names.append(token.lower().rstrip('.'))
    return section(names, 'partial', 'On-disk nginx -T names only; effective routing, default/listen and active configuration not proven' + ('; ambiguous directive encountered' if ambiguous else ''))


def postgres_names(raw):
    values = raw.splitlines()
    if len(values) != len(set(values)) or any(not PG_PATTERN.fullmatch(x) for x in values):
        return section(detail='Malformed, duplicate or invalid catalog output')
    return section(values, 'partial', 'Local postgres cluster only; ownership, privileges and additional clusters not verified')


def collect(runner=subprocess.run, hostname='unverified-host'):
    cmds = {
        'nginx_server_names': ['sudo', '-n', '/usr/sbin/nginx', '-T'],
        'database_names': ['sudo', '-n', '-u', 'postgres', '/usr/bin/psql', '-X', '-w', '-A', '-t', '-v', 'ON_ERROR_STOP=1', '-d', 'postgres', '-c', 'SELECT datname FROM pg_catalog.pg_database ORDER BY datname'],
        'database_roles': ['sudo', '-n', '-u', 'postgres', '/usr/bin/psql', '-X', '-w', '-A', '-t', '-v', 'ON_ERROR_STOP=1', '-d', 'postgres', '-c', 'SELECT rolname FROM pg_catalog.pg_roles ORDER BY rolname'],
    }
    data = {}
    for key, argv in cmds.items():
        raw = invoke(argv, runner)
        data[key] = section(detail='Command failed or permission denied; absence not established') if raw is None else (nginx_names(raw) if key == 'nginx_server_names' else postgres_names(raw))
    return {
        'format': 'pt36-admin-metadata-v1', 'source': 'separately_privileged_read_only_observations',
        'host_label': re.sub(r'[^A-Za-z0-9_.-]', '_', hostname)[:128],
        'collected_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'sections': data, 'ready_to_apply': False,
        'notice': 'Partial identifiers only. Not merged into PT33 v2 evidence. No provisioning clearance.'
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--acknowledge-sensitive-read', action='store_true', help='Explicit approval to read raw nginx config in memory without export')
    args = parser.parse_args(argv)
    try:
        if platform.system() != 'Linux' or os.geteuid() == 0:
            raise ValueError('Linux non-root operator required')
        if not args.acknowledge_sensitive_read:
            raise ValueError('explicit sensitive-read acknowledgement required')
        target = args.output.expanduser().absolute()
        if target.exists() or target.is_symlink() or not target.parent.is_dir() or any(p.is_symlink() for p in target.parents):
            raise ValueError('unsafe or existing destination')
        if str(target).startswith(('/etc/', '/srv/', '/var/', '/usr/', '/root/', '/proc/', '/sys/', '/dev/')):
            raise ValueError('system output path forbidden')
        if target.parent.stat().st_mode & 0o077:
            raise ValueError('output directory must be private (mode 0700)')
        record = collect(hostname=platform.node())
        blob = (json.dumps(record, indent=2, sort_keys=True) + '\n').encode()
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        with os.fdopen(fd, 'wb') as handle:
            handle.write(blob)
        print('PASS: private supplementary metadata written (partial/non-authorizing)')
        print('Sections:', ', '.join(f'{k}={v["status"]}' for k, v in sorted(record['sections'].items())))
        return 0
    except (OSError, ValueError) as exc:
        print('PT36 REFUSED:', exc, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
