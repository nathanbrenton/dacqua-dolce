"""PT33-B v0.5 offline evidence contract. No host or provider access.

A complete snapshot is a *reviewed claim about one bounded source*, never
proof that a future allocation is safe. Cryptographic digests detect accidental
modification, not malicious forgery or provider-account independence.
"""
import datetime as dt
import hashlib
import json

SECTIONS = ('service_users', 'systemd_units', 'paths', 'ports',
            'database_names', 'database_roles')
EXTRA_SECTIONS = ('unix_groups', 'unix_uids', 'unix_gids', 'tcp_bindings')
NGINX_SECTIONS = ('nginx_server_names',)
STATUSES = ('complete', 'partial', 'failed', 'unsupported')
PROVIDERS = ('domain_registrar', 'cloudflare', 'vultr', 'proton_mail',
             'postmark', 'better_stack', 'aws')


def section_digest(values):
    """Digest precisely the canonical JSON list; not an authenticity signature."""
    encoded = json.dumps(values, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=True).encode('ascii')
    return hashlib.sha256(encoded).hexdigest()


def _timestamp(value, name):
    if not isinstance(value, str):
        raise ValueError(name + ' must be an ISO-8601 timestamp')
    try:
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError(name + ' invalid timestamp') from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta():
        raise ValueError(name + ' must explicitly use UTC')
    return parsed


def validate_v2(evidence, now=None, max_age_hours=24):
    """Return normalized evidence freshness; refuse malformed/contradictory input.

    A caller must explicitly choose the maximum age. Default 24 hours is a
    conservative *review policy*, not a guarantee of live resource availability.
    """
    if isinstance(max_age_hours, bool) or not isinstance(max_age_hours, (float, int)) or not 0 < max_age_hours <= 720:
        raise ValueError('max_age_hours must be >0 and <=720')
    if not isinstance(evidence, dict) or set(evidence) != {
        'evidence_version', 'resource_scope', 'host_id', 'target_instance_id',
        'source', 'collector_version', 'collected_at_utc', 'sections',
        'external_verification', 'ready_to_apply'}:
        raise ValueError('invalid v2 evidence fields')
    if evidence['evidence_version'] != 2 or evidence['resource_scope'] != 'single_debian_host_read_only':
        raise ValueError('unsupported v2 version or scope')
    for field in ('host_id', 'target_instance_id', 'source', 'collector_version'):
        if not isinstance(evidence[field], str) or not evidence[field].strip() or len(evidence[field]) > 128:
            raise ValueError('invalid identity/provenance: ' + field)
    if evidence['source'] not in ('reviewed_manual_inventory', 'read_only_host_collector'):
        raise ValueError('unsupported evidence source')
    if evidence['ready_to_apply'] is not False:
        raise ValueError('v2 evidence must never authorize apply')
    stamp = _timestamp(evidence['collected_at_utc'], 'collected_at_utc')
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('now must be timezone-aware')
    if stamp > now or now - stamp > dt.timedelta(hours=max_age_hours):
        raise ValueError('v2 evidence future-dated or stale')
    sections = evidence['sections']
    if not isinstance(sections, dict) or not (set(sections) == set(SECTIONS) or set(sections) == set(SECTIONS) | set(EXTRA_SECTIONS) or
            set(sections) == set(SECTIONS) | set(EXTRA_SECTIONS) | set(NGINX_SECTIONS)):
        raise ValueError('missing or unexpected evidence sections')
    for name, entry in sections.items():
        if not isinstance(entry, dict) or set(entry) != {'status', 'values', 'method', 'detail', 'sha256'}:
            raise ValueError('invalid section structure: ' + name)
        if entry['status'] not in STATUSES:
            raise ValueError('invalid inspection status: ' + name)
        if not isinstance(entry['method'], str) or not entry['method'].strip() or len(entry['method']) > 128:
            raise ValueError('missing inspection method: ' + name)
        if not isinstance(entry['detail'], str) or len(entry['detail']) > 256:
            raise ValueError('invalid inspection detail: ' + name)
        values = entry['values']
        if not isinstance(values, list) or len(values) > 100000:
            raise ValueError('invalid inventory list: ' + name)
        if entry['status'] in ('failed', 'unsupported') and values:
            raise ValueError('failed/unsupported section cannot claim values: ' + name)
        for v in values:
            if name in ('ports', 'unix_uids', 'unix_gids'):
                valid = type(v) is int and ((1 <= v <= 65535) if name == 'ports' else (0 <= v <= 4294967295))
            else:
                valid = isinstance(v, str) and 0 < len(v) <= 512 and not any(ord(c) < 32 for c in v)
            if not valid:
                raise ValueError('invalid resource identifier: ' + name)
        if len(values) != len(set(values)):
            raise ValueError('duplicate inventory entries: ' + name)
        if entry['sha256'] != section_digest(values):
            raise ValueError('section integrity mismatch: ' + name)
    # Cross-section consistency: a binding observation must also list its port.
    # This is evidence integrity, not proof of port availability.
    if 'tcp_bindings' in sections:
        bindings = sections['tcp_bindings']['values']
        ports = set(sections['ports']['values'])
        for item in bindings:
            if not isinstance(item, str) or ':' not in item:
                raise ValueError('invalid TCP binding identifier')
            address, port_text = item.rsplit(':', 1)
            try:
                import ipaddress
                if address not in ('*', '[::]'):
                    ipaddress.ip_address(address.strip('[]'))
                port = int(port_text)
                if not 1 <= port <= 65535 or port_text != str(port):
                    raise ValueError('port range or encoding')
            except ValueError as exc:
                raise ValueError('invalid TCP binding identifier') from exc
            if port not in ports:
                raise ValueError('contradictory TCP binding and port evidence')
    external = evidence['external_verification']
    if not isinstance(external, dict) or set(external) != set(PROVIDERS) or any(x != 'unverified' for x in external.values()):
        raise ValueError('provider ownership must remain unverified for host evidence')
    return {'age_hours': round((now-stamp).total_seconds()/3600, 3), 'timestamp_precision': 'exact'}
