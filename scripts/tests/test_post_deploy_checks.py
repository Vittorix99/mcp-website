import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('post_deploy_checks', ROOT / 'scripts/staging/post_deploy_checks.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)

PROJECT = 'mcp-website-dev-39539'


def healthy(url, headers):
    if 'admin_get_radio_episodes' in url:
        return 401, 'text/html; charset=utf-8', 'No authorization token provided'
    if 'member_get_me' in url:
        return 401, 'application/json', '{"error": "Authorization token missing"}'
    if 'get_event_by_id' in url:
        return 400, 'application/json', '{"error": "Invalid request"}'
    if 'get_next_event' in url:
        return 404, 'application/json', '{"error": "none"}'
    if url.endswith('robots.txt'):
        return 200, 'text/plain', 'User-agent: *'
    if '.web.app' in url:
        return 200, 'text/html; charset=utf-8', '<html><body>ok</body></html>'
    return 200, 'application/json', '[]'


def test_a_healthy_environment_passes_every_check(capsys):
    assert checks.run(PROJECT, healthy) == []
    assert capsys.readouterr().out.count('ok   ') == len(list(checks.checks(PROJECT)))


def test_an_unguarded_admin_endpoint_is_reported():
    def open_admin(url, headers):
        return (200, 'application/json', '[]') if 'admin_get_radio_episodes' in url else healthy(url, headers)
    assert [name for name, _ in checks.run(PROJECT, open_admin)] == ['admin without token', 'admin invalid token']


def test_stack_traces_server_errors_and_broken_pages_are_failures():
    def broken(url, headers):
        if 'get_event_by_id' in url:
            return 400, 'application/json', '{"error": "Traceback (most recent call last)"}'
        if 'get_membership_price_public' in url:
            return 500, 'application/json', '{}'
        if url.endswith('/events'):
            return 200, 'text/html', '<html>truncated'
        if url.endswith('/radio'):
            raise TimeoutError()
        return healthy(url, headers)
    assert [name for name, _ in checks.run(PROJECT, broken)] == [
        'membership price', 'event without id', 'site events', 'site radio']


def test_checks_never_send_a_valid_credential_or_a_write_method():
    # Requests carry no body and only a deliberately invalid token.
    for _, url, headers, _, _ in checks.checks(PROJECT):
        assert url.startswith('https://')
        assert headers in (None, {'Authorization': checks.BAD_TOKEN})
