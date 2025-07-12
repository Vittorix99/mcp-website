from firebase_functions import https_fn
from flask import request, jsonify
from config.firebase_config import cors
from services.questions_service import (
    create_question_service,
    get_all_questions_service,
    get_question_by_id_service,
    delete_question_service,
    update_question_service
)
from services.admin.auth_services import require_admin
from config.firebase_config import region

@https_fn.on_request(cors=cors, region=region)
@require_admin
def create_question(req):
    if req.method != 'POST':
        return 'Invalid request method', 405

    req_json = req.get_json()
    if not req_json:
        return {'error': 'Missing required fields'}, 400

    return create_question_service(req_json)


@https_fn.on_request(cors=cors, region=region)
def get_all_questions(req):
    if req.method != 'GET':
        return 'Invalid request method', 405

    return get_all_questions_service()


@https_fn.on_request(cors=cors, region=region)
def get_question_by_id(req):
    if req.method != 'GET':
        return 'Invalid request method', 405

    question_id = req.args.get('id')
    if not question_id:
        return {'error': 'Missing question ID'}, 400

    return get_question_by_id_service(question_id)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def delete_question(req):
    if req.method != 'DELETE':
        return 'Invalid request method', 405

    question_id = req.args.get('id')
    if not question_id:
        return {'error': 'Missing question ID'}, 400

    return delete_question_service(question_id)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def update_question(req):
    if req.method != 'PUT':
        return 'Invalid request method', 405

    req_json = req.get_json()
    if not req_json or 'id' not in req_json:
        return {'error': 'Missing question ID or data'}, 400

    question_id = req_json['id']
    update_data = req_json['updatedData']
    return update_question_service(question_id, update_data)
