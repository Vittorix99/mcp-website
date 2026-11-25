from flask import Flask, request
import pytest


@pytest.mark.parametrize('method,status', [('GET', 200), ('POST', 405)])
def test_health_identifies_release_without_exposing_environment(monkeypatch, method, status):
    monkeypatch.setenv('MCP_BACKEND_TREE', 'a' * 40)
    monkeypatch.setenv('MCP_CONFIG_DIGEST', 'b' * 64)
    monkeypatch.setenv('MAILERSEND_API_KEY', 'private-sentinel')
    from api.public.deployment_api import deployment_health
    app = Flask('health')
    app.add_url_rule('/health', view_func=lambda: deployment_health(request), methods=['GET', 'POST'])
    result = app.test_client().open('/health', method=method)
    assert result.status_code == status
    assert 'private-sentinel' not in result.get_data(as_text=True)
    if method == 'GET':
        assert result.get_json() == {'status': 'ok', 'environment': 'test',
            'project_id': 'demo-mcp-test', 'backend_tree': 'a' * 40, 'configuration_digest': 'b' * 64}
        assert result.headers['Cache-Control'] == 'no-store'


@pytest.mark.parametrize('tree,digest', [('', ''), ('invalid-private-sentinel', 'b' * 64), ('a' * 40, 'wrong')])
def test_health_rejects_unversioned_or_malformed_release(monkeypatch, tree, digest):
    monkeypatch.setenv('MCP_BACKEND_TREE', tree)
    monkeypatch.setenv('MCP_CONFIG_DIGEST', digest)
    from api.public.deployment_api import deployment_health
    app = Flask('health-invalid')
    app.add_url_rule('/health', view_func=lambda: deployment_health(request))
    result = app.test_client().get('/health')
    assert result.status_code == 503
    assert result.get_json() == {'status': 'unversioned'}


def test_health_ignores_the_release_commit_so_unrelated_commits_do_not_change_identity(monkeypatch):
    monkeypatch.setenv('MCP_BACKEND_TREE', 'a' * 40)
    monkeypatch.setenv('MCP_CONFIG_DIGEST', 'b' * 64)
    monkeypatch.setenv('MCP_RELEASE_SHA', 'c' * 40)
    from api.public.deployment_api import deployment_health
    app = Flask('health-no-sha')
    app.add_url_rule('/health', view_func=lambda: deployment_health(request))
    body = app.test_client().get('/health').get_json()
    assert 'release_sha' not in body and body['backend_tree'] == 'a' * 40
