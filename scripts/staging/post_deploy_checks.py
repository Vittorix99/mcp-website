#!/usr/bin/env python3
"""Public, read-only checks of a deployed environment: API contract, authentication guards, site pages.

Only GET requests without credentials (or with a deliberately invalid token), so nothing can be created or changed
and no secret is needed. Prints check names and statuses, never response bodies. Exit code 1 on any failed check.
"""
import argparse
import json
import re
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

PROJECTS = {'mcp-website-dev-39539', 'mcp-website-2a1ad'}
BAD_TOKEN = 'Bearer invalid.synthetic.token'
LEAK = re.compile(r'Traceback|File "/|\bat [A-Za-z.]+\(|PRIVATE KEY|secret_key', re.I)


def fetch(url, headers=None):
    request = Request(url, headers={'Cache-Control': 'no-cache', **(headers or {})})
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, response.headers.get('Content-Type', ''), response.read(2_000_000).decode('utf-8', 'replace')
    except HTTPError as error:
        return error.code, error.headers.get('Content-Type', ''), error.read(200_000).decode('utf-8', 'replace')


def checks(project):
    api = f'https://us-central1-{project}.cloudfunctions.net/'
    site = f'https://{project}.web.app'
    yield from [
        # Authentication guards: a missing or invalid token never reaches the handler (admin and member surfaces).
        ('admin without token', api + 'get_all_admins', None, {401, 403}, 'json'),
        ('admin invalid token', api + 'get_all_admins', {'Authorization': BAD_TOKEN}, {401, 403}, 'json'),
        ('member without token', api + 'member_get_me', None, {401}, 'json'),
        ('member invalid token', api + 'member_get_me', {'Authorization': BAD_TOKEN}, {401}, 'json'),
        # Public API contract and input validation: JSON answers, client errors rather than server errors, no stack traces.
        ('events list', api + 'get_all_events', None, {200}, 'json'),
        ('next event', api + 'get_next_event', None, {200, 404}, 'json'),
        ('membership price', api + 'get_membership_price_public', None, {200}, 'json'),
        ('event without id', api + 'get_event_by_id', None, {400, 404}, 'json'),
        # Site: the main public pages render server-side.
        ('site home', site + '/', None, {200}, 'html'),
        ('site events', site + '/events', None, {200}, 'html'),
        ('site radio', site + '/radio', None, {200}, 'html'),
        ('site contact', site + '/contact', None, {200}, 'html'),
        ('site robots', site + '/robots.txt', None, {200}, 'text'),
    ]


def run(project, fetcher=fetch):
    failures = []
    for name, url, headers, statuses, kind in checks(project):
        try:
            status, content_type, body = fetcher(url, headers)
        except Exception as error:  # network or TLS failure is a failed check, not a crash
            failures.append((name, type(error).__name__))
            continue
        problem = None
        if status not in statuses:
            problem = f'status {status}, expected {sorted(statuses)}'
        elif LEAK.search(body):
            problem = 'response exposes diagnostic internals'
        elif kind == 'json':
            try:
                json.loads(body)
            except ValueError:
                problem = 'body is not JSON'
        elif kind == 'html' and not ('text/html' in content_type and '</html>' in body.lower()):
            problem = 'not a complete HTML page'
        print(('FAIL ' if problem else 'ok   ') + f'{name}: {problem or status}', flush=True)
        if problem:
            failures.append((name, problem))
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, choices=sorted(PROJECTS))
    args = parser.parse_args()
    failures = run(args.project)
    print(f'{len(failures)} failed checks' if failures else 'All post-deploy checks passed.')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
