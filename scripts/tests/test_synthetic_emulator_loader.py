import importlib.util
from pathlib import Path
import json
import pytest

ROOT = Path(__file__).resolve().parents[2]

def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'scripts/staging/{name}.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

loader = module('load_emulator')
generator = module('generate')

@pytest.mark.parametrize('project,host', [
    ('mcp-website-dev-39539', '127.0.0.1:8080'),
    ('mcp-website-2a1ad', '127.0.0.1:8080'),
    ('demo-mcp-local', 'example.com:8080'),
    ('demo-mcp-local', '127.0.0.1:8080@evil.example'),
    ('demo-mcp-local', '127.0.0.1:0'),
])
def test_cloud_or_non_loopback_target_is_rejected(project, host):
    with pytest.raises(ValueError):
        loader.validate_target(project, host)


def test_local_demo_target_is_accepted():
    assert loader.validate_target('demo-mcp-local', '127.0.0.1:8080') == '127.0.0.1:8080'


def test_checksum_tampering_is_rejected_before_any_client_exists(tmp_path, monkeypatch):
    from datetime import date
    data = generator.generate(seed=42, as_of=date(2026, 11, 7), email_base='owner@example.com', member_count=30, event_count=12)
    monkeypatch.setattr(generator, 'ROOT', tmp_path)
    output = tmp_path / '.local/staging/data'
    generator.write_export(data, output)
    rows, manifest = loader.read_export(output)
    assert len(rows) == manifest['document_count']
    timestamp = next(row['data']['scanned_at'] for row in rows if row['path'].startswith('entrance_scans/'))
    assert timestamp.tzinfo is not None
    with (output / 'records.jsonl').open('a') as handle:
        handle.write(json.dumps({'path':'memberships/unknown','data':{}})+'\n')
    with pytest.raises(ValueError):
        loader.read_export(output)


@pytest.mark.parametrize('emulators', [
    {},
    {'firestore': {'host': '127.0.0.1', 'port': 8180}, 'functions': {'port': 5001}},
    {'firestore': {'host': '127.0.0.1', 'port': 8080}},
])
def test_import_requires_matching_firestore_and_no_functions(emulators):
    with pytest.raises(ValueError):
        loader.validate_emulators(emulators, '127.0.0.1:8180')


def test_dedicated_firestore_only_hub_is_accepted():
    loader.validate_emulators({'firestore': {'host': '127.0.0.1', 'port': 8180}}, '127.0.0.1:8180')


def test_existing_foreign_or_stale_documents_are_rejected():
    from datetime import date
    settings = dict(as_of=date(2026, 11, 7), email_base='owner@example.com', member_count=30, event_count=12)
    first = generator.generate(seed=42, **settings)
    second = generator.generate(seed=43, **settings)
    old_paths = {r['path'] for r in first['records']}
    new_paths = {r['path'] for r in second['records']}
    assert old_paths - new_paths
    with pytest.raises(ValueError):
        loader.validate_existing(old_paths, second['records'])
    loader.validate_existing(new_paths, second['records'])
    loader.validate_existing(set(), second['records'])
    loader.validate_existing(set(list(new_paths)[:3]), second['records'])


def test_firebase_rules_path_is_inside_its_config_project_root():
    candidates = [ROOT / 'scripts/staging/firebase.emulator.json', ROOT / 'firebase.synthetic-emulator.json']
    configs = [p for p in candidates if p.exists()]
    assert len(configs) == 1
    config = configs[0]
    rules = (config.parent / json.loads(config.read_text())['firestore']['rules']).resolve()
    assert rules.is_relative_to(config.parent)
    assert rules.is_file()


def test_recursive_inventory_forwards_sdk_emulator_metadata():
    from types import SimpleNamespace
    database = 'projects/demo-mcp-test/databases/(default)'
    metadata = [('authorization', 'emulator-sdk-marker')]
    def run_query(*, request, timeout, metadata=None):
        assert metadata == client._rpc_metadata, 'Missing SDK emulator authorization metadata'
        return [SimpleNamespace(document=SimpleNamespace(name=database + '/documents/events/syn-event-000'))]
    client = SimpleNamespace(_database_string=database, _rpc_metadata=metadata,
                             _firestore_api=SimpleNamespace(run_query=run_query))
    assert loader._document_paths(client) == {'events/syn-event-000'}
