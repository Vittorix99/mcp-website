#!/usr/bin/env python3
"""Decide whether the full CI suite already covers this exact commit tree, so a release can skip repeating it.

Reuse is allowed only with evidence tied to the *same tree*:
  - push to main: the commit is the squash/merge of exactly one merged PR into main, the PR head has the same
    tree as this commit (the branch was up to date), and the "Core WS1 checks" workflow succeeded on that head;
  - manual dispatch on main: an earlier push run of release.yml for the same commit finished its `gate` job.
Any doubt (several PRs, different tree, no successful run, API error) means: run the full suite.
"""
import json
import os
import subprocess
import sys

PR_WORKFLOW = 'pr.yml'
RELEASE_WORKFLOW = 'release.yml'


def gh_json(path):
    out = subprocess.run(['gh', 'api', path], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def tree_of(ref):
    return subprocess.run(['git', 'rev-parse', ref + '^{tree}'], capture_output=True, text=True, check=True).stdout.strip()


def fetch_pull_head(number):
    subprocess.run(['git', 'fetch', '--no-tags', '--quiet', 'origin', f'pull/{number}/head'], check=True)


def decide(event, sha, repo, *, api=gh_json, tree=tree_of, fetch=fetch_pull_head):
    """Return (reuse, reason). Never raises: failures become (False, reason)."""
    try:
        if event == 'push':
            pulls = [item for item in api(f'repos/{repo}/commits/{sha}/pulls')
                     if item.get('merged_at') and item.get('base', {}).get('ref') == 'main']
            if len(pulls) != 1 or pulls[0].get('merge_commit_sha') != sha:
                return False, 'commit is not the merge of exactly one pull request'
            number, head = pulls[0]['number'], pulls[0]['head']['sha']
            fetch(number)
            if tree(head) != tree(sha):
                return False, 'pull request head tree differs from the merged tree (branch was not up to date)'
            runs = api(f'repos/{repo}/actions/workflows/{PR_WORKFLOW}/runs?head_sha={head}&event=pull_request'
                       '&status=completed&per_page=30').get('workflow_runs', [])
            if any(run.get('conclusion') == 'success' for run in runs):
                return True, f'checks passed on pull request #{number} with the identical tree'
            return False, 'no successful checks on the pull request head'
        if event == 'workflow_dispatch':
            runs = api(f'repos/{repo}/actions/workflows/{RELEASE_WORKFLOW}/runs?head_sha={sha}&event=push'
                       '&status=completed&per_page=30').get('workflow_runs', [])
            for run in runs:
                jobs = api(f"repos/{repo}/actions/runs/{run['id']}/jobs?per_page=50").get('jobs', [])
                if any(job.get('name') == 'gate' and job.get('conclusion') == 'success' for job in jobs):
                    return True, f"gate already passed for this commit in run {run['id']}"
            return False, 'no earlier push run with a passed gate for this commit'
        return False, 'event does not allow reuse'
    except Exception as error:  # fail closed, never print API payloads
        return False, 'evidence unavailable (' + type(error).__name__ + ')'


def main():
    reuse, reason = decide(os.environ.get('GITHUB_EVENT_NAME', ''), os.environ.get('GITHUB_SHA', ''),
                           os.environ.get('GITHUB_REPOSITORY', ''))
    print(('Reusing verified CI: ' if reuse else 'Running the full suite: ') + reason)
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output, 'a') as handle:
            handle.write('reuse=' + ('true' if reuse else 'false') + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
