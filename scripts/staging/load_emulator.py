#!/usr/bin/env python3
"""Load generated records into a loopback emulator. No cloud target is accepted."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.request import ProxyHandler, build_opener

PATHS = (
    r'memberships/syn-member-\d{5}', r'events/syn-event-\d{3}',
    r'orders/SYNTHETIC-ORDER-\d{6}', r'purchases/syn-purchase-\d{6}',
    r'scan_tokens/syn-history-scanner-\d{3}',
    r'participants/syn-event-\d{3}/participants_event/syn-participant-\d{5}',
    r'entrance_scans/syn-event-\d{3}/scans/syn-member-\d{5}',
)


def validate_target(project, host):
    if project not in {'demo-mcp-local', 'demo-mcp-test'}:
        raise ValueError('Only the two local demo projects are allowed')
    match = re.fullmatch(r'127\.0\.0\.1:([0-9]{1,5})', host)
    if not match or not 1 <= int(match[1]) <= 65535:
        raise ValueError('A literal 127.0.0.1 emulator endpoint is required')
    return host


def _timestamps(value):
    if isinstance(value, dict):
        if set(value) == {'$timestamp'}:
            parsed = datetime.fromisoformat(value['$timestamp'])
            if parsed.tzinfo is None:
                raise ValueError('Export timestamps must include timezone')
            return parsed
        return {key: _timestamps(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_timestamps(item) for item in value]
    return value


def validate_emulators(emulators, host):
    firestore = emulators.get('firestore', {})
    if 'functions' in emulators or f"{firestore.get('host')}:{firestore.get('port')}" != host:
        raise ValueError('Use a dedicated Firestore-only emulator; Functions triggers must be absent')


def validate_existing(existing_paths, records):
    expected_paths = {row['path'] for row in records}
    if set(existing_paths) - expected_paths:
        raise ValueError('Emulator contains foreign/stale documents; use a fresh dedicated session')


def _document_paths(client):
    from google.cloud.firestore_v1.types import StructuredQuery
    parent = client._database_string + '/documents'
    query = StructuredQuery(
        select=StructuredQuery.Projection(fields=[StructuredQuery.FieldReference(field_path='__name__')]),
        from_=[StructuredQuery.CollectionSelector(all_descendants=True)],
    )
    paths = set()
    for response in client._firestore_api.run_query(
            request={'parent': parent, 'structured_query': query},
            metadata=client._rpc_metadata, timeout=60):
        if response.document.name:
            if not response.document.name.startswith(parent + '/'):
                raise ValueError('Unexpected document database')
            paths.add(response.document.name[len(parent) + 1:])
    return paths


def read_export(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    records = [json.loads(line) for line in (directory / 'records.jsonl').read_text().splitlines()]
    payload = json.dumps(records, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    if (manifest.get('format_version') != 1 or len(records) != manifest.get('document_count')
            or hashlib.sha256(payload.encode()).hexdigest() != manifest.get('document_sha256')):
        raise ValueError('Export is incomplete or checksum does not match')
    seen = set()
    for row in records:
        path = row['path']
        if path in seen or not any(re.fullmatch(pattern, path) for pattern in PATHS):
            raise ValueError('Duplicate or unexpected document path')
        seen.add(path)
        data = row['data']
        if data.get('send_ticket_on_create') or data.get('send_card_on_create'):
            raise ValueError('Bulk export must not request email delivery')
        if path.startswith('scan_tokens/') and data.get('is_active') is not False:
            raise ValueError('Historical scanner tokens must be inactive')
    return _timestamps(records), manifest


def load(records, *, project, host, hub):
    host = validate_target(project, host)
    hub = validate_target(project, hub)
    opener = build_opener(ProxyHandler({}))
    with opener.open(f'http://{hub}/emulators', timeout=5) as response:
        validate_emulators(json.load(response), host)
    # Import only after target validation. Anonymous credentials prevent any ADC fallback.
    from google.auth.credentials import AnonymousCredentials
    from google.cloud import firestore
    os.environ['FIRESTORE_EMULATOR_HOST'] = host
    client = firestore.Client(project=project, credentials=AnonymousCredentials())
    try:
        if client._emulator_host != host:
            raise ValueError('Firestore client is not bound to the selected emulator')
        validate_existing(_document_paths(client), records)
        for offset in range(0, len(records), 400):
            batch = client.batch()
            for row in records[offset:offset + 400]:
                batch.set(client.document(row['path']), row['data'])
            batch.commit(timeout=30)
        verified = 0
        for offset in range(0, len(records), 400):
            refs = [client.document(row['path']) for row in records[offset:offset + 400]]
            expected = {row['path']: row['data'] for row in records[offset:offset + 400]}
            for snapshot in client.get_all(refs, timeout=30):
                if not snapshot.exists or snapshot.to_dict() != expected[snapshot.reference.path]:
                    raise ValueError('Readback data does not match export')
                verified += 1
        if verified != len(records):
            raise ValueError('Readback document count does not match export')
        validate_existing(_document_paths(client), records)
        return verified
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--project', default='demo-mcp-local')
    parser.add_argument('--host', default='127.0.0.1:8080')
    parser.add_argument('--hub', default='127.0.0.1:4400')
    parser.add_argument('--apply', action='store_true', help='Write to emulator; default is offline validation only')
    args = parser.parse_args()
    try:
        validate_target(args.project, args.host)
        records, manifest = read_export(args.directory)
        verified = load(records, project=args.project, host=args.host, hub=args.hub) if args.apply else 0
    except Exception as error:
        # Exceptions can include document values; expose only their type.
        partial = ' Emulator writes may be partial.' if args.apply else ''
        parser.exit(2, f'Import failed ({type(error).__name__}); no success claimed.{partial} '
                       'Rerun the same export after resolving cause.\n')
    print(json.dumps({'mode': 'emulator-write' if args.apply else 'offline-check',
                      'documents': len(records), 'members': manifest['members'], 'events': manifest['events'],
                      'verified_documents': verified, 'cloud_writes': 0,
                      'auth_accounts_created': 0, 'deletes': 0}))


if __name__ == '__main__':
    main()
