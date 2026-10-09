#!/usr/bin/env python3
"""PT33-B v0.5 guarded OFFLINE manifest/evidence verification. No host access."""
import argparse
import json
import os
from pathlib import Path
import sys

import plan_business
from evaluate_production_evidence import assess
from evidence_contract import validate_v2


def verify(manifest, evidence, schema, *, now=None, max_age_hours=24):
    """Require a valid new-business manifest and a current v2 host snapshot."""
    errors = plan_business.validate_schema(manifest, schema)
    if not errors:
        try:
            errors = plan_business.semantic_checks(manifest)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError('invalid manifest structure') from exc
    if errors:
        raise ValueError('invalid business manifest: ' + '; '.join(errors))
    if not isinstance(evidence, dict) or evidence.get('evidence_version') != 2:
        raise ValueError('integrated verification requires version 2 host evidence')
    # validate_v2 rejects stale, contradictory, unsupported, or altered evidence.
    validate_v2(evidence, now=now, max_age_hours=max_age_hours)
    result = assess(manifest, evidence, now=now, max_age_hours=max_age_hours)
    # Report does not contain provider credentials or inventory contents.
    return {
        'assessment_version': 'pt33-b-v0.5-increment7',
        'business_id': manifest['business']['id'],
        'instance_id': manifest['instance']['id'],
        'host_assessment': result,
        'independent_provider_ownership': {key: 'requires_manual_verification' for key in evidence['external_verification']},
        'remaining_gates': [
            'Confirm authorized target host and collection privileges',
            'Review NGINX effective routing including wildcard/default/upstream behavior',
            'Review PostgreSQL cluster coverage and database/role ownership',
            'Review Unix numeric IDs and systemd alias/override coverage',
            'Review filesystem ownership, permissions, mounts, and existing paths',
            'Confirm each external provider account is independently owned',
            'Verify backup, restore, DNS, TLS, monitoring, and billing separation',
        ],
        'ready_to_apply': False,
    }



def safe_report_output(path):
    """Validate report destination, accommodating macOS /var -> /private/var.

    Do not follow arbitrary symlink ancestors or existing output symlinks.
    The resulting path is still created with O_EXCL to prevent overwrite.
    """
    output = path.expanduser().absolute()
    if not output.parent.is_dir() or output.is_symlink():
        raise ValueError('unsafe report output path')
    permitted_aliases = {}
    if sys.platform == 'darwin':
        permitted_aliases = {'/var': '/private/var', '/tmp': '/private/tmp'}
    for ancestor in output.parents:
        if ancestor.is_symlink():
            if permitted_aliases.get(str(ancestor)) != str(ancestor.resolve()):
                raise ValueError('unsafe report output path')
    # Also reject hidden symlinks along the canonical path after approved OS aliases.
    real_parent = output.parent.resolve(strict=True)
    if any(ancestor.is_symlink() for ancestor in (real_parent, *real_parent.parents)):
        raise ValueError('unsafe report output path')
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path,
                        help='New offline report path; refuses overwrite')
    parser.add_argument('--max-age-hours', type=float, default=24)
    args = parser.parse_args(argv)
    try:
        root = Path(__file__).resolve().parents[2]
        schema = json.loads((root / 'docs/production/pt33/business-manifest.schema.json').read_text())
        manifest = json.loads(args.manifest.read_text())
        evidence = json.loads(args.evidence.read_text())
        report = verify(manifest, evidence, schema, max_age_hours=args.max_age_hours)
        output = safe_report_output(args.output)
        if output == args.manifest.absolute() or output == args.evidence.absolute():
            raise ValueError('input file cannot be report output')
        payload = (json.dumps(report, sort_keys=True, indent=2) + '\n').encode('utf-8')
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as handle:
            handle.write(payload)
        print('PASS: offline guarded assessment written:', output)
        print('NOTE: report is non-authorizing; ready_to_apply=false')
        return 0
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print('PT33-B INTEGRATED VERIFICATION REFUSED:', exc, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
