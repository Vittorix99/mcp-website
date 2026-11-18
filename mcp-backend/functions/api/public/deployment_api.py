"""Public release identity; contains no provider configuration or credentials."""
import os
import re
from flask import jsonify
from api.decorators import public_endpoint
from config.runtime_settings import get_runtime_policy


@public_endpoint(methods=('GET',))
def deployment_health(req):
    sha = os.environ.get('MCP_RELEASE_SHA', '')
    digest = os.environ.get('MCP_CONFIG_DIGEST', '')
    if not re.fullmatch('[0-9a-f]{40}', sha) or not re.fullmatch('[0-9a-f]{64}', digest):
        response = jsonify({'status': 'unversioned'})
        response.status_code = 503
    else:
        settings = get_runtime_policy()
        response = jsonify({'status': 'ok', 'environment': settings.environment.value,
            'project_id': settings.firebase.project_id, 'release_sha': sha,
            'configuration_digest': digest})
    response.headers['Cache-Control'] = 'no-store'
    return response
