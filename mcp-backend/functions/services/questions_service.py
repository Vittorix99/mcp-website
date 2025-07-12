from config.firebase_config import db
from flask import jsonify


def create_question_service(data):
    required_fields = ['input', 'note', 'question', 'varName']
    if not all(field in data for field in required_fields):
        return {'error': 'Missing required fields'}, 400

    try:
        question_ref = db.collection('questions').add(data)
        return {
            'message': 'Question created successfully',
            'questionId': question_ref[1].id
        }, 201
    except Exception as e:
        return {'error': str(e)}, 500


def get_all_questions_service():
    try:
        questions = db.collection('questions').stream()
        questions_list = [{**doc.to_dict(), 'id': doc.id} for doc in questions]
        return jsonify(questions_list), 200
    except Exception as e:
        return {'error': str(e)}, 500


def get_question_by_id_service(question_id):
    try:
        question_ref = db.collection('questions').document(question_id)
        question = question_ref.get()

        if not question.exists:
            return {'error': f"Question with ID {question_id} not found"}, 404

        return jsonify({
            'id': question.id,
            **question.to_dict()
        }), 200
    except Exception as e:
        return {'error': str(e)}, 500


def delete_question_service(question_id):
    try:
        question_ref = db.collection('questions').document(question_id)
        question = question_ref.get()

        if not question.exists:
            return {'error': f"Question with ID {question_id} not found"}, 404

        question_ref.delete()
        return {'message': 'Question deleted successfully'}, 200
    except Exception as e:
        return {'error': str(e)}, 500


def update_question_service(question_id, update_data):
    try:
        question_ref = db.collection('questions').document(question_id)
        question = question_ref.get()

        if not question.exists:
            return {'error': f"Question with ID {question_id} not found"}, 404

        question_ref.update(update_data)
        return {'message': 'Question updated successfully'}, 200
    except Exception as e:
        return {'error': str(e)}, 500
