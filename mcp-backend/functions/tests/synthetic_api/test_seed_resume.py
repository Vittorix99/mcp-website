"""OPS-09: deterministic exports and interrupted imports in the guarded demo emulator."""
import importlib.util
import os
from datetime import date
from pathlib import Path

import pytest
from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore

from config.firebase_config import db
from tests.synthetic_api.conftest import _loader as loader

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location('ops09_generator', ROOT / 'scripts/staging/generate.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


@pytest.fixture
def exported_records(tmp_path, monkeypatch):
    dataset = generator.generate(seed=42, as_of=date(2026, 11, 12), email_base='owner@example.com',
                                 member_count=120, event_count=12)
    monkeypatch.setattr(generator, 'ROOT', tmp_path)
    output = tmp_path / '.local/staging/ops09'
    generator.write_export(dataset, output)
    records, manifest = loader.read_export(output)
    assert manifest['members'] == 120 and manifest['events'] == 12
    assert len(records) > 800  # Exercise interruption after more than one 400-write batch.
    return records


def image():
    paths = sorted(loader._document_paths(db))
    result = {}
    for offset in range(0, len(paths), 400):
        refs = [db.document(path) for path in paths[offset:offset + 400]]
        result.update({snap.reference.path: snap.to_dict() for snap in db.get_all(refs)})
    return result


def load(records):
    return loader.load(records, project='demo-mcp-test', host=os.environ['FIRESTORE_EMULATOR_HOST'],
                       hub=os.environ['FIREBASE_EMULATOR_HUB'])


def test_repeated_import_has_identical_documents_without_duplicates(exported_records):
    expected = {row['path']: row['data'] for row in exported_records}
    assert load(exported_records) == len(expected)
    assert image() == expected
    assert load(exported_records) == len(expected)
    assert image() == expected


class InterruptedBatch:
    def __init__(self, client, batch, index):
        self.client, self.batch, self.index = client, batch, index

    def set(self, *args, **kwargs):
        return self.batch.set(*args, **kwargs)

    def commit(self, **kwargs):
        if self.index == 2 and self.client.failure == 'before_commit':
            raise RuntimeError('synthetic interruption before commit')
        result = self.batch.commit(**kwargs)
        if self.index == 2 and self.client.failure == 'after_commit':
            raise RuntimeError('synthetic lost commit acknowledgement')
        return result


class InterruptedClient:
    def __init__(self, client, failure):
        self.client, self.failure = client, failure
        self.batch_count = 0
        self.closed = False

    def __getattr__(self, name):
        return getattr(self.client, name)

    def batch(self):
        self.batch_count += 1
        return InterruptedBatch(self, self.client.batch(), self.batch_count)

    def get_all(self, *args, **kwargs):
        if self.failure == 'readback':
            raise RuntimeError('synthetic readback interruption')
        return self.client.get_all(*args, **kwargs)

    def close(self):
        self.closed = True
        self.client.close()


@pytest.mark.parametrize('failure,committed', [('before_commit', 400), ('after_commit', 800), ('readback', None)])
def test_partial_or_unacknowledged_import_can_resume_without_duplicates(
        exported_records, monkeypatch, failure, committed):
    original_client = firestore.Client
    clients = []

    def client_factory(*args, **kwargs):
        assert kwargs['project'] == 'demo-mcp-test'
        assert isinstance(kwargs['credentials'], AnonymousCredentials)
        wrapped = InterruptedClient(original_client(*args, **kwargs), failure if not clients else None)
        clients.append(wrapped)
        return wrapped

    monkeypatch.setattr(firestore, 'Client', client_factory)
    with pytest.raises(RuntimeError, match='synthetic'):
        load(exported_records)
    assert len(clients) == 1 and clients[0].closed
    prefix = exported_records if committed is None else exported_records[:committed]
    assert image() == {row['path']: row['data'] for row in prefix}

    assert load(exported_records) == len(exported_records)
    assert len(clients) == 2 and clients[1].closed
    assert image() == {row['path']: row['data'] for row in exported_records}


def test_foreign_document_blocks_import_without_any_seed_writes(exported_records):
    ref = db.document('memberships/operator-document')
    ref.set({'name': 'Synthetic operator fixture', 'preserve': True})
    before = image()

    with pytest.raises(ValueError, match='foreign/stale'):
        load(exported_records)

    assert image() == before
