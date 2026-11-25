#!/usr/bin/env python3
"""Load a reviewed synthetic export into the STAGING Firestore only (owner-operated, explicit --apply).

Refuses any other project, an emulator host, a non-private personal credential, and a database that already
holds documents outside the export. Staging has no Firestore triggers or schedulers deployed, so writes cannot
send mail or call providers; the export itself must not request delivery (checked by read_export).
"""
import argparse
import json
import os
from pathlib import Path
import stat
import sys

import load_emulator as base

PROJECT = 'mcp-website-dev-39539'


def validate_credential(path, env):
    """Owner's personal OAuth credential, private file, quota project pinned to staging."""
    if env.get('FIRESTORE_EMULATOR_HOST'):
        raise ValueError('Emulator host must not be set')
    credential = Path(path)
    status = credential.lstat()
    if (not credential.is_absolute() or not stat.S_ISREG(status.st_mode) or status.st_mode & 0o077 or
            status.st_uid != os.getuid()):
        raise ValueError('Credential must be an absolute private file')
    data = json.loads(credential.read_text())
    if (data.get('type') != 'authorized_user' or data.get('quota_project_id') != PROJECT or
            data.get('private_key') or data.get('service_account_impersonation_url')):
        raise ValueError('Credential must be a personal OAuth credential with the staging quota project')
    return credential


def load(records, credential):
    from google.cloud import firestore
    import google.oauth2.credentials
    creds = google.oauth2.credentials.Credentials.from_authorized_user_file(str(credential))
    client = firestore.Client(project=PROJECT, credentials=creds)
    try:
        if client.project != PROJECT:
            raise ValueError('Unexpected Firestore project')
        base.validate_existing(base._document_paths(client), records)
        for offset in range(0, len(records), 400):
            batch = client.batch()
            for row in records[offset:offset + 400]:
                batch.set(client.document(row['path']), row['data'])
            batch.commit(timeout=60)
        verified = 0
        for offset in range(0, len(records), 400):
            refs = [client.document(row['path']) for row in records[offset:offset + 400]]
            expected = {row['path']: row['data'] for row in records[offset:offset + 400]}
            for snapshot in client.get_all(refs, timeout=60):
                if not snapshot.exists or snapshot.to_dict() != expected[snapshot.reference.path]:
                    raise ValueError('Readback data does not match export')
                verified += 1
        if verified != len(records):
            raise ValueError('Readback document count does not match export')
        base.validate_existing(base._document_paths(client), records)
        return verified
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--credential', type=Path, required=True)
    parser.add_argument('--apply', action='store_true', help='Write to staging; default is offline validation only')
    args = parser.parse_args()
    try:
        credential = validate_credential(args.credential, os.environ)
        records, manifest = base.read_export(args.directory)
        verified = load(records, credential) if args.apply else 0
    except Exception as error:
        # Exceptions can include document values; expose only their type.
        sys.exit(f'Import failed ({type(error).__name__}); no success claimed. Writes may be partial; '
                 'rerun the same export after resolving the cause.')
    print(json.dumps({'mode': 'staging-write' if args.apply else 'offline-check', 'project': PROJECT,
                      'documents': len(records), 'members': manifest['members'], 'events': manifest['events'],
                      'verified_documents': verified, 'deletes': 0}))


if __name__ == '__main__':
    main()
