import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('ci_evidence', ROOT / 'scripts/ci/ci_evidence.py')
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)

SHA, HEAD = 'a' * 40, 'b' * 40
PR = {'number': 7, 'merged_at': '2026-11-28T10:00:00Z', 'base': {'ref': 'main'}, 'merge_commit_sha': SHA, 'head': {'sha': HEAD}}


def fake_api(pulls=(PR,), pr_runs=({'conclusion': 'success'},), release_runs=(), jobs=()):
    def api(path):
        if path.endswith('/pulls'):
            return list(pulls)
        if '/workflows/pr.yml/runs' in path:
            return {'workflow_runs': list(pr_runs)}
        if '/workflows/release.yml/runs' in path:
            return {'workflow_runs': list(release_runs)}
        if path.endswith('/jobs?per_page=50'):
            return {'jobs': list(jobs)}
        raise AssertionError(path)
    return api


def run(event='push', api=None, tree=lambda ref: 't', **kw):
    return evidence.decide(event, SHA, 'o/r', api=api or fake_api(), tree=tree, fetch=lambda n: None, **kw)


def test_push_reuses_ci_only_for_the_identical_tree_of_one_merged_pull_request():
    assert run()[0] is True
    # The branch was behind main: the squash tree differs from the head tree, so nothing is reused.
    assert run(tree=lambda ref: 't1' if ref == HEAD else 't2')[0] is False


def test_push_without_proof_runs_the_full_suite():
    assert run(api=fake_api(pr_runs=({'conclusion': 'failure'}, {'conclusion': 'cancelled'})))[0] is False
    assert run(api=fake_api(pr_runs=()))[0] is False
    assert run(api=fake_api(pulls=()))[0] is False
    assert run(api=fake_api(pulls=(PR, {**PR, 'number': 8})))[0] is False
    assert run(api=fake_api(pulls=({**PR, 'merge_commit_sha': 'c' * 40},)))[0] is False
    assert run(api=fake_api(pulls=({**PR, 'merged_at': None},)))[0] is False
    assert run(api=fake_api(pulls=({**PR, 'base': {'ref': 'dev'}},)))[0] is False


def test_dispatch_reuses_only_a_passed_gate_of_the_same_commit():
    ok = fake_api(release_runs=({'id': 5},), jobs=({'name': 'gate', 'conclusion': 'success'},))
    assert run('workflow_dispatch', api=ok)[0] is True
    assert run('workflow_dispatch', api=fake_api(release_runs=({'id': 5},), jobs=({'name': 'gate', 'conclusion': 'failure'},)))[0] is False
    assert run('workflow_dispatch', api=fake_api(release_runs=({'id': 5},), jobs=({'name': 'verify', 'conclusion': 'success'},)))[0] is False
    assert run('workflow_dispatch', api=fake_api())[0] is False


def test_unknown_events_and_api_failures_fail_closed_without_leaking_payloads():
    assert run('pull_request')[0] is False
    def broken(path):
        raise RuntimeError('PRIVATE_SENTINEL')
    reuse, reason = run(api=broken)
    assert reuse is False and 'PRIVATE_SENTINEL' not in reason and 'RuntimeError' in reason
