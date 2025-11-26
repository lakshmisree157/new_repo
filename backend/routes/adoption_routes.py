"""
Adoption-related routes: create/list/update adoption requests,
post-adoption tracking, and admin logs viewing.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from backend.controllers.adoption_controller import (
    create_adoption_request,
    get_requests_by_center,
    get_requests_by_adopter,
    update_request_status,
    add_post_adoption_tracking
)
from backend.models.sql_models import AdminLog
from config.py_db import engine
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)

adopt_bp = Blueprint('adoptions', __name__, url_prefix='/api/adoptions')


def role_required(*required_roles):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')
            if user_role not in required_roles:
                return jsonify(error='Forbidden: insufficient permissions'), 403
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator


@adopt_bp.route('/request', methods=['POST'])
@jwt_required()
@role_required('adopter')
def create_request():
    data = request.json or {}
    if not data.get('center_id') or not data.get('animal_mongo_id'):
        return jsonify(error='Missing center_id or animal_mongo_id'), 400

    user_id = get_jwt_identity()
    result, status = create_adoption_request(
        adopter_user_id=user_id,
        center_id=data['center_id'],
        animal_mongo_id=data['animal_mongo_id']
    )
    return jsonify(result), status


@adopt_bp.route('/center/<int:center_id>/requests', methods=['GET'])
@jwt_required()
@role_required('center', 'admin')
def center_requests(center_id):
    result, status = get_requests_by_center(center_id)
    return jsonify(result), status


@adopt_bp.route('/my', methods=['GET'])
@jwt_required()
@role_required('adopter')
def my_requests():
    user_id = get_jwt_identity()
    result, status = get_requests_by_adopter(user_id)
    return jsonify(result), status


@adopt_bp.route('/user/<int:user_id>/requests', methods=['GET'])
@jwt_required()
@role_required('adopter')
def user_requests(user_id):
    """
    GET /api/adoptions/user/<user_id>/requests
    Returns adoption requests for a specific adopter user (restricted to adopter role)
    """
    # Ensure the user_id matches the JWT identity for security
    jwt_user_id = get_jwt_identity()
    if str(user_id) != jwt_user_id:
        return jsonify(error='Forbidden: can only access your own requests'), 403

    result, status = get_requests_by_adopter(user_id)
    return jsonify(result), status


@adopt_bp.route('/request/<int:request_id>/status', methods=['PATCH'])
@jwt_required()
@role_required('center', 'admin')
def patch_request_status(request_id):
    data = request.json or {}
    new_status = data.get('status')
    if not new_status:
        return jsonify(error='Missing status'), 400
    result, status = update_request_status(request_id, new_status)
    return jsonify(result), status


@adopt_bp.route('/request/<int:request_id>/post-tracking', methods=['POST'])
@jwt_required()
def post_tracking(request_id):
    data = request.json or {}
    followup_date = data.get('followup_date')
    notes = data.get('notes')
    health_status = data.get('health_status')

    result, status = add_post_adoption_tracking(
        request_id=request_id,
        followup_date=followup_date,
        notes=notes,
        health_status=health_status
    )
    return jsonify(result), status


@adopt_bp.route('/request/<int:request_id>', methods=['DELETE'])
@jwt_required()
@role_required('adopter')
def delete_request(request_id):
    """
    DELETE /api/adoptions/request/<request_id>
    Allows adopters to delete their pending adoption requests
    """
    from backend.controllers.adoption_controller import delete_adoption_request
    user_id = get_jwt_identity()
    result, status = delete_adoption_request(request_id, user_id)
    return jsonify(result), status


@adopt_bp.route('/admin/logs', methods=['GET'])
@jwt_required()
@role_required('admin')
def admin_logs():
    session = Session()
    try:
        logs = session.query(AdminLog).order_by(AdminLog.timestamp.desc()).limit(200).all()
        data = [
            {
                'log_id': l.log_id,
                'admin_id': l.admin_id,
                'action_type': l.action_type,
                'details': l.details,
                'timestamp': l.timestamp.isoformat()
            } for l in logs
        ]
        return jsonify({'total': len(data), 'logs': data}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500
    finally:
        session.close()


@adopt_bp.route('/admin/pending-centers', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_pending_centers():
    result, status = list_unverified_centers()
    return jsonify(result), status


@adopt_bp.route('/admin/verify-center/<int:center_id>', methods=['POST'])
@jwt_required()
@role_required('admin')
def verify_adoption_center(center_id):
    admin_user_id = get_jwt_identity()
    result, status = verify_center(center_id, admin_user_id)
    return jsonify(result), status
