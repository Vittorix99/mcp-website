"""Every HTTP/callable entry point declares its authentication, and the public surface is an explicit list.

Static (AST) so it needs no emulator or credentials: adding an endpoint without one of the guarded decorators, or
adding a new public endpoint without a conscious allowlist change, fails here before it can be released.
"""
import ast
from pathlib import Path

API = Path(__file__).resolve().parents[3] / 'api'

# Reviewed public surface (no credentials needed). Writes here must validate input and stay idempotent/abuse-bounded.
PUBLIC_READ = {
    'get_settings', 'get_setting', 'get_membership_price_public', 'deployment_health', 'get_all_events', 'get_next_event',
    'get_event_by_id', 'get_event_guide', 'get_published_radio_episodes', 'get_latest_radio_episode', 'get_radio_episode',
    'get_radio_seasons', 'check_participants', 'validate_discount_code',
}
PUBLIC_WRITE = {
    'contact_us', 'newsletter_signup', 'create_order_event', 'capture_order_event', 'sender_webhook',
    'entrance_verify_scan_token', 'entrance_validate',
}
CALLABLE = {'verify_admin'}  # Firebase callable: the handler itself verifies the admin claim


def _classify():
    rows = {}
    for path in sorted(API.rglob('*.py')):
        if path.parent.name == 'decorators':
            continue  # the guarded wrappers themselves
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            names = {ast.unparse(item.func if isinstance(item, ast.Call) else item) for item in node.decorator_list}
            if names & {'public_endpoint', 'admin_endpoint', 'member_endpoint', 'https_fn.on_request', 'https_fn.on_call'}:
                rows[f'{path.relative_to(API)}:{node.name}'] = names
    return rows


def test_every_entry_point_is_guarded_or_explicitly_public():
    assert len(_classify()) > 100  # the scan really sees the whole API
    problems = []
    for where, names in _classify().items():
        name = where.rsplit(':', 1)[1]
        if 'admin_endpoint' in names or 'member_endpoint' in names:
            continue
        if 'public_endpoint' in names:
            if name not in PUBLIC_READ | PUBLIC_WRITE:
                problems.append(f'{where}: new public endpoint needs a reviewed allowlist entry')
        elif 'https_fn.on_call' in names:
            if name not in CALLABLE:
                problems.append(f'{where}: unreviewed callable')
        elif 'require_admin' not in names:
            problems.append(f'{where}: raw on_request without admin guard')
    assert problems == []


def test_public_allowlist_has_no_stale_entries_and_no_duplicate_names():
    public = {where.rsplit(':', 1)[1] for where, names in _classify().items() if 'public_endpoint' in names}
    assert public == PUBLIC_READ | PUBLIC_WRITE
    assert PUBLIC_READ.isdisjoint(PUBLIC_WRITE)
    all_names = [where.rsplit(':', 1)[1] for where in _classify()]
    assert len(all_names) == len(set(all_names))  # one function name = one Cloud Run service
