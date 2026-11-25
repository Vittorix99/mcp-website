"""Offline staging-migration boundaries; no owner credentials, cloud calls or deployment."""
import json
from pathlib import Path
import sys

import pytest
from test_bootstrap_staging import environment

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/deployment'))
import migrate_staging as migrate  # noqa: E402

ENDPOINTS = [dict(id='get_event', kind='http'), dict(id='on_member', kind='event')]


def manifest_for(env):
    return migrate.bootstrap.prepare(env, ENDPOINTS)


def functions(manifest, python=('get_event',), site=1):
    build = f"projects/{manifest['project']}/serviceAccounts/" + manifest['identities']['BUILD_SERVICE_ACCOUNT']
    rows = [dict(name=f"projects/{manifest['project']}/locations/us-central1/functions/{name}",
        labels={'firebase-functions-codebase': 'python_codebase'}, buildConfig={'serviceAccount': build},
        serviceConfig={'serviceAccountEmail': manifest['identities']['RUNTIME_SERVICE_ACCOUNT']}) for name in python]
    rows += [dict(name=f"projects/{manifest['project']}/locations/us-central1/functions/ssrsite{i}",
        labels={'firebase-functions-codebase': 'firebase-frameworks-' + manifest['project']},
        buildConfig={'serviceAccount': build},
        serviceConfig={'serviceAccountEmail': manifest['identities']['WEB_RUNTIME_SERVICE_ACCOUNT']}) for i in range(site)]
    return rows


def test_existing_inventory_must_match_the_approved_http_and_ssr_set():
    manifest = manifest_for(environment())
    hosting = {'releases': [{'type': 'DEPLOY'}]}
    migrate.validate_existing_inventory(manifest, functions(manifest), hosting)
    for rows, release_info in [(functions(manifest, python=()), hosting),                    # nothing deployed yet
                               (functions(manifest, python=('get_event', 'extra')), hosting),  # unknown function
                               (functions(manifest, site=0), hosting),                       # no SSR
                               (functions(manifest, site=2), hosting),                       # two SSR
                               (functions(manifest), {}), (functions(manifest), {'releases': []})]:
        with pytest.raises(ValueError):
            migrate.validate_existing_inventory(manifest, rows, release_info)


def test_apply_needs_its_own_explicit_approval(monkeypatch):
    env = {**environment(), 'BOOTSTRAP_OPERATOR_ADC': '/synthetic/private-adc.json'}
    manifest = manifest_for(env)
    # The bootstrap approvals must not stand in for the migration approval.
    for approvals in [{}, {'BOOTSTRAP_CLOUD_APPROVED': 'true', 'BOOTSTRAP_DATA_REVIEWED': 'true'},
                      {'MIGRATION_APPROVED': 'yes'}]:
        with pytest.raises(ValueError, match='explicit migration approval'):
            migrate.apply(manifest, {**env, **approvals})


def run_apply(tmp_path, monkeypatch, *, fail_on=None):
    env = {**environment(), 'MIGRATION_APPROVED': 'true', 'BOOTSTRAP_OPERATOR_ADC': '/synthetic/private-adc.json'}
    manifest = manifest_for(env)
    scratch = tmp_path / '.local/release'
    scratch.mkdir(parents=True)
    bootstrap = migrate.bootstrap
    monkeypatch.setattr(migrate, 'ROOT', tmp_path)
    monkeypatch.setattr(bootstrap, 'discover_endpoints', lambda: ENDPOINTS)
    monkeypatch.setattr(bootstrap, 'source_check', lambda *a: None)
    repository = {'name': f"projects/{manifest['project']}/locations/us-central1/repositories/gcf-artifacts",
        'labels': {}, 'cleanupPolicies': {'keep': {'action': 'KEEP'}, 'old': {'action': 'DELETE'}}, 'cleanupPolicyDryRun': True}
    monkeypatch.setattr(bootstrap, 'operator_cloud', lambda *a: lambda m, *args: json.dumps(
        repository if args[:2] == ('artifacts', 'repositories') else functions(manifest)))
    monkeypatch.setattr(migrate.release, 'cloud_preflight', lambda *a, **k: None)
    monkeypatch.setattr(migrate.release, 'hosting', lambda *a, **k: {'releases': [{'type': 'DEPLOY'}]})
    monkeypatch.setattr(migrate.release, 'write_configuration', lambda *a: None)
    calls, verifications = [], []
    real_command = migrate.release.command

    def command(args, **kwargs):
        if args[:2] == ['git', 'rev-parse']:  # component identity lookup, not a CLI command
            return real_command(args, **kwargs)
        calls.append(args[-1])
        assert Path(args[1]).name == 'firebase-migrate.cjs', 'migration must never use the bootstrap or release CLI entry'
        assert kwargs['env']['GOOGLE_APPLICATION_CREDENTIALS'] == env['BOOTSTRAP_OPERATOR_ADC']
        assert list(Path(kwargs['env']['XDG_CONFIG_HOME']).iterdir()) == []
        if args[-1] == fail_on:
            raise ValueError('TOKEN-SENTINEL')
        return ''
    monkeypatch.setattr(migrate.release, 'command', command)
    monkeypatch.setattr(bootstrap, 'verify_deployed', lambda m, c, **kw: verifications.append(kw))
    try:
        migrate.apply(manifest, env)
        error = None
    except ValueError as raised:
        error = raised
    return calls, verifications, error, json.loads((scratch / 'migration-result.json').read_text()), scratch


def test_apply_updates_backend_then_site_and_verifies_each_phase_with_the_existing_ssr(tmp_path, monkeypatch):
    calls, verifications, error, result, scratch = run_apply(tmp_path, monkeypatch)
    assert error is None
    assert calls == ['validate', 'backend', 'hosting']
    # Identities are checked before the first update (stamps differ until then), then after each phase.
    assert verifications == [{'web': 1, 'stamps': False}, {'web': 1}, {'hosting': True, 'web': 1}]
    assert result['status'] == 'migrated-not-a-rollback-baseline'
    assert set(result) == {'schema', 'project', 'sha', 'components', 'status'}
    assert list(scratch.glob('operator-*')) == []


def test_failed_phase_stops_without_retry_rollback_or_leaking_diagnostics(tmp_path, monkeypatch):
    calls, verifications, error, result, _ = run_apply(tmp_path, monkeypatch, fail_on='backend')
    assert 'SENTINEL' not in str(error) and 'no automatic rollback or retry' in str(error)
    assert calls == ['validate', 'backend'] and verifications == [{'web': 1, 'stamps': False}]
    assert result['status'] == 'incomplete-owner-investigation-required'


def test_registry_retention_must_not_be_able_to_delete_images_during_migration():
    name = 'projects/p/locations/us-central1/repositories/gcf-artifacts'
    keep, delete = {'action': 'KEEP'}, {'action': 'DELETE'}
    for repository in [{'name': name, 'labels': {'firebase-functions-cleanup-opted-out': 'true'}},
                       {'name': name, 'cleanupPolicies': {'a': keep}},
                       {'name': name, 'cleanupPolicies': {'a': keep, 'b': delete}, 'cleanupPolicyDryRun': True}]:
        migrate.validate_migration_retention(repository, name)
    for repository in [{'name': name}, {'name': name, 'cleanupPolicies': {}},
                       {'name': name, 'cleanupPolicies': {'a': keep, 'b': delete}},
                       {'name': name, 'cleanupPolicies': {'a': keep, 'b': delete}, 'cleanupPolicyDryRun': False},
                       {'name': 'projects/other/locations/us-central1/repositories/gcf-artifacts',
                        'labels': {'firebase-functions-cleanup-opted-out': 'true'}}]:
        with pytest.raises(ValueError):
            migrate.validate_migration_retention(repository, name)


def test_identities_are_checked_before_the_first_update(tmp_path, monkeypatch):
    manifest = manifest_for(environment())
    good = functions(manifest)
    migrate.bootstrap.verify_deployed(manifest, lambda *a: json.dumps(good), web=1, stamps=False)
    wrong_runtime = [{**good[0], 'serviceConfig': {'serviceAccountEmail': 'other@x.iam.gserviceaccount.com'}}, good[1]]
    wrong_build = [{**good[0], 'buildConfig': {}}, good[1]]
    for rows in [wrong_runtime, wrong_build]:
        with pytest.raises(ValueError):
            migrate.bootstrap.verify_deployed(manifest, lambda *a: json.dumps(rows), web=1, stamps=False)
