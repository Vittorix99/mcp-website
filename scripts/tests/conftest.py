"""Release tests use synthetic commits; resolve their component source trees deterministically."""
import hashlib
import re
import subprocess

import pytest

_REAL_RUN = subprocess.run
_TREE_QUERY = re.compile(r'^([0-9a-f]{40}):(.+)$')


_RELEASE_MODULES = {'test_deployment_release', 'test_bootstrap_staging'}


@pytest.fixture(autouse=True)
def synthetic_component_trees(request, monkeypatch):
    """`git rev-parse <sha>:<path>` for a made-up commit returns a stable fake object id.

    The id depends on the path and on SYNTHETIC_TREE_SALT[path] so a test can simulate a
    change to one component without touching the other. Real repositories are unaffected:
    every other command, and any query for an existing object, runs unchanged.
    """
    salt = {}
    if request.module.__name__ not in _RELEASE_MODULES:
        yield salt
        return

    def run(args, *a, **kw):
        if isinstance(args, list) and args[:2] == ['git', 'rev-parse'] and len(args) == 3:
            match = _TREE_QUERY.match(args[2])
            if match:
                path = match.group(2)
                value = hashlib.sha1(f'{path}:{salt.get(path, "")}'.encode()).hexdigest()
                return subprocess.CompletedProcess(args, 0, stdout=value + '\n', stderr='')
        return _REAL_RUN(args, *a, **kw)
    monkeypatch.setattr(subprocess, 'run', run)
    yield salt
