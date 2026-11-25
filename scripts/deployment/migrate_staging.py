#!/usr/bin/env python3
"""One-time staging migration to per-component identity, explicitly operated by the owner.

Updates the existing HTTP functions and the SSR site in place with personal operator credentials, as a
documented exception to the OIDC release. It never creates or deletes and is not a rollback baseline.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import bootstrap_staging as bootstrap
import release

ROOT = release.ROOT
require = release.require


def validate_existing_inventory(manifest, functions, hosting):
    """The migration only applies to the exact environment the bootstrap created."""
    codebase = lambda row: row.get('labels', {}).get('firebase-functions-codebase')
    python = {row['name'].rsplit('/', 1)[-1] for row in functions if codebase(row) == 'python_codebase'}
    site = [row for row in functions if codebase(row) == 'firebase-frameworks-' + manifest['project']]
    expected = {row['id'] for row in manifest['bootstrap']['endpoints'] if row['kind'] == 'http'}
    require(python == expected and len(site) == 1 and len(functions) == len(python) + len(site),
        'existing staging inventory matches the approved HTTP and SSR set')
    require(isinstance(hosting, dict) and bool(hosting.get('releases')), 'existing Hosting release')


def validate_migration_retention(repository, name):
    """No image may be deleted while 130 functions are being replaced; dry run and keep-only policies are fine."""
    policies = list(repository.get('cleanupPolicies', {}).values())
    require(repository.get('name') == name and
        (repository.get('labels', {}).get('firebase-functions-cleanup-opted-out') == 'true' or
         (bool(policies) and (repository.get('cleanupPolicyDryRun') is True or
                              all(policy.get('action') != 'DELETE' for policy in policies)))),
        'artifact retention that cannot delete images during migration')


def apply(manifest, env):
    require(env.get('MIGRATION_APPROVED') == 'true', 'explicit migration approval')
    clean_env = {key: value for key, value in env.items() if key != 'GOOGLE_APPLICATION_CREDENTIALS'}
    require(manifest == bootstrap.prepare(clean_env, bootstrap.discover_endpoints()), 'unchanged migration plan')
    bootstrap.source_check(env)
    credential = env.get('BOOTSTRAP_OPERATOR_ADC', '')
    require(Path(credential).is_absolute(), 'explicit private operator ADC path')
    cloud = bootstrap.operator_cloud(env)
    release.cloud_preflight(manifest, cloud=cloud)
    functions = json.loads(cloud(manifest, 'functions', 'list', '--regions=-', '--format=json(name,labels)'))
    validate_existing_inventory(manifest, functions, release.hosting(manifest, '/releases?pageSize=1', cloud=cloud))
    # Everything that could fail after the first update is checked before it: registry retention and the
    # deployed build/runtime identities (stamps are expected to differ until the migration has run).
    repository = json.loads(cloud(manifest, 'artifacts', 'repositories', 'describe', 'gcf-artifacts',
        '--location', release.REGION, '--format=json(name,labels,cleanupPolicies,cleanupPolicyDryRun)'))
    validate_migration_retention(repository,
        'projects/' + manifest['project'] + '/locations/' + release.REGION + '/repositories/gcf-artifacts')
    bootstrap.verify_deployed(manifest, cloud, web=1, stamps=False)
    release.write_configuration(manifest)
    scratch = ROOT / '.local/release'
    base = bootstrap.operator_environment(env)
    base.update({key: env[key] for key in ['BOOTSTRAP_OPERATOR_EMAIL', 'BOOTSTRAP_APPROVED_SHA', 'MIGRATION_APPROVED']})
    base.update(BOOTSTRAP_OPERATOR_ADC=credential, GOOGLE_APPLICATION_CREDENTIALS=credential,
        MCP_RELEASE_CONFIG=str(scratch / 'config.json'), GCLOUD_PROJECT=manifest['project'],
        GOOGLE_CLOUD_PROJECT=manifest['project'], FIREBASE_CLI_EXPERIMENTS='webframeworks',
        NEXT_TELEMETRY_DISABLED='1', FIREBASE_CLI_DISABLE_UPDATE_CHECK='1')

    def firebase(target):
        # A different empty configstore per process prevents cached Firebase login overriding ADC.
        with tempfile.TemporaryDirectory(prefix='operator-', dir=scratch) as profile:
            release.command(['node', str(ROOT / 'scripts/deployment/firebase-migrate.cjs'), target],
                env={**base, 'XDG_CONFIG_HOME': profile})
    firebase('validate')
    result = dict(schema=1, project=manifest['project'], sha=manifest['sha'],
        components=manifest['components'], status='started')
    record = scratch / 'migration-result.json'
    record.write_text(json.dumps(result) + '\n')
    try:
        firebase('backend')
        bootstrap.verify_deployed(manifest, cloud, web=1)
        firebase('hosting')
        bootstrap.verify_deployed(manifest, cloud, hosting=True, web=1)
    except Exception:
        result['status'] = 'incomplete-owner-investigation-required'
        record.write_text(json.dumps(result) + '\n')
        raise ValueError('Migration stopped; inspect public result and cloud inventory; no automatic rollback or retry') from None
    result['status'] = 'migrated-not-a-rollback-baseline'
    record.write_text(json.dumps(result) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'apply'])
    args = parser.parse_args()
    manifest = bootstrap.prepare(os.environ, bootstrap.discover_endpoints())
    bootstrap.source_check(os.environ)
    # Validate against the real pinned CLI selector, without authenticating or deploying.
    result = subprocess.run(['node', str(ROOT / 'scripts/deployment/firebase-bootstrap.cjs'), 'selectors'],
        cwd=ROOT, env=bootstrap.operator_environment(os.environ),
        input=json.dumps(manifest['bootstrap']['endpoints']), text=True, capture_output=True)
    require(result.returncode == 0, 'exact pinned CLI HTTP selector')
    plan = ROOT / '.local/release/migration-plan.json'
    if args.operation == 'prepare':
        plan.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        plan.write_text(json.dumps(manifest, sort_keys=True) + '\n')
        print('Public staging migration plan prepared offline; no cloud authentication or deployment.')
    else:
        require(json.loads(plan.read_text()) == manifest, 'approved prepared migration plan')
        apply(manifest, os.environ)
        print('Staging backend and SSR migrated and verified in place; run two ordinary releases to build a rollback baseline.')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Guarded staging migration failed; diagnostics withheld.', file=sys.stderr)
        sys.exit(1)
