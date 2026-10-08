#!/usr/bin/env python3
"""PT33-B v0.4: fail-closed OFFLINE assessment of sanitized host evidence.

Never contacts hosts/providers, mutates infrastructure or asserts apply readiness.
"""
import argparse
import datetime as dt
import json
from pathlib import Path

CATEGORIES = {
    'service_user': ('service_users', lambda m: [m['instance']['service_user']]),
    'systemd_unit': ('systemd_units', lambda m: [m['instance']['systemd_unit']]),
    'paths': ('paths', lambda m: [m['instance'][k] for k in ('service_root', 'config_root', 'state_root')]),
    'port': ('ports', lambda m: [m['network']['port']]),
    'database': ('database_names', lambda m: [m['database']['name']]),
    'db_roles': ('database_roles', lambda m: [m['database']['runtime_role'],m['database']['migrator_role']]),
}
REQUIRED = {'host_id','source','inspection_date_utc','collected_at_utc','evidence_version','resource_scope','reserved','coverage'}

def assess(manifest, evidence, now=None, max_age_days=1):
    if not isinstance(evidence,dict) or set(evidence)!=REQUIRED:
        raise ValueError('evidence fields missing or unexpected')
    if evidence['evidence_version'] != 1 or evidence['resource_scope'] != 'debian_production_manual_read_only':
        raise ValueError('unsupported evidence version/scope')
    if not isinstance(evidence['host_id'],str) or not evidence['host_id']:
        raise ValueError('host identity required')
    if evidence['source'] != 'manual_terminal_inspection_reviewed':
        raise ValueError('untrusted source type')
    date=dt.date.fromisoformat(evidence['inspection_date_utc'])
    now=now or dt.datetime.now(dt.timezone.utc)
    if date > now.date() or (now.date()-date).days > max_age_days:
        raise ValueError('evidence date in future or stale')
    # A calendar date alone cannot establish a time-bounded fresh snapshot.
    precise=evidence['collected_at_utc']
    if precise is not None:
        stamp=dt.datetime.fromisoformat(precise.replace('Z','+00:00'))
        if stamp.tzinfo is None or stamp>now or now-stamp>dt.timedelta(days=max_age_days):
            raise ValueError('timestamp missing timezone, in future, or stale')
    if not isinstance(evidence['reserved'],dict) or not isinstance(evidence['coverage'],dict):
        raise ValueError('reserved/coverage must be objects')
    conflicts=[]; unknown=[]; checked=[]
    for kind,(section,values) in CATEGORIES.items():
        if section not in evidence['reserved'] or not isinstance(evidence['reserved'][section],list):
            raise ValueError('missing inventory section: '+section)
        if not all(isinstance(v, (int if section=='ports' else str)) for v in evidence['reserved'][section]):
            raise ValueError('invalid inventory value: '+section)
        if evidence['coverage'].get(section) not in ('observed','partial','unverified'):
            raise ValueError('missing/invalid evidence coverage: '+section)
        requested=values(manifest)
        stored=evidence['reserved'][section]
        for value in requested:
            if section=='paths':
                collision=any(value==other or value.startswith(other.rstrip('/')+'/') or other.startswith(value.rstrip('/')+'/') for other in stored)
            else:
                collision=value in stored
            if collision: conflicts.append({'category':section,'value':value})
            elif evidence['coverage'][section] != 'observed': unknown.append({'category':section,'value':value})
            else: checked.append({'category':section,'value':value,'finding':'not_observed'})
    return {'evidence_host':evidence['host_id'],'scope':evidence['resource_scope'],
            'evidence_date_utc':evidence['inspection_date_utc'],
            'timestamp_precision':'exact' if precise else 'calendar_day_only',
            'collisions':conflicts,'not_observed':checked,'unverified':unknown,
            'external_providers':'UNVERIFIED','nginx_effective_configuration':'UNVERIFIED',
            'backup_and_dns':'UNVERIFIED','ready_to_apply':False}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--output',type=Path,help='Optional new report file; refuses overwrite')
    a=p.parse_args(argv)
    try:
        result=assess(json.loads(a.manifest.read_text()),json.loads(a.evidence.read_text()))
        out=json.dumps(result,sort_keys=True,indent=2)+'\n'
        if a.output:
            with a.output.open('x') as f:f.write(out)
            print('PASS: wrote non-authorizing assessment to',a.output)
        else:print(out,end='')
        return 0
    except (ValueError,KeyError,OSError,TypeError,json.JSONDecodeError) as e:
        print('PT33-B EVIDENCE REFUSED:',str(e))
        return 2
if __name__=='__main__':raise SystemExit(main())
