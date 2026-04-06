"""
Authentication routes for the pet adoption backend.
Endpoints:
  - POST /api/auth/register
  - POST /api/auth/login
  - GET /api/auth/profile (protected)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from functools import wraps

from backend.controllers.auth_controller import (
    register_user,
    login_user,
    get_user_profile,
    update_adopter_profile,
    update_center_profile,
    firebase_login,
    firebase_register
)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def role_required(*required_roles):
    """
    Decorator to enforce role-based access control.
    Usage: @role_required('admin', 'center')
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')
            if user_role not in required_roles:
                return jsonify(error='Forbidden: insufficient permissions'), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /api/auth/register
    Register a new user (any role: admin, adopter, center).
    
    Request body:
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "secure_password",
        "role": "adopter",  // or "admin", "center"
        // If role="center":
        "center_name": "Pawsome Shelter",
        "location": "123 Main St",
        "contact_number": "555-1234"
        // If role="adopter":
        "full_name": "John Doe",
        "address": "123 Main St",
        "phone_number": "555-9999",
        "lifestyle": "active",
        "home_environment": "house"
    }
    
    Response: 201 Created
    {
        "message": "User registered successfully",
        "user": {
            "user_id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "role": "adopter"
        }
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify(error='Request body is required'), 400
    
    # Extract required fields
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    
    if not all([username, email, password, role]):
        return jsonify(error='Missing required fields: username, email, password, role'), 400
    
    # Extract optional role-specific fields
    kwargs = {
        'center_name': data.get('center_name'),
        'location': data.get('location'),
        'contact_number': data.get('contact_number'),
        'full_name': data.get('full_name'),
        'address': data.get('address'),
        'phone_number': data.get('phone_number'),
        'lifestyle': data.get('lifestyle'),
        'home_environment': data.get('home_environment'),
        'family_composition': data.get('family_composition'),
        'pet_experience': data.get('pet_experience'),

        'preferred_pet_age_min': data.get('preferred_pet_age_min'),
        'preferred_pet_age_max': data.get('preferred_pet_age_max')
    }
    
    result, status_code = register_user(username, email, password, role, **kwargs)
    return jsonify(result), status_code


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Login user and get JWT token.
    
    Request body:
    {
        "email": "john@example.com",
        "password": "secure_password"
    }
    
    Response: 200 OK
    {
        "message": "Login successful",
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user_id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "adopter"
    }
    """
    data = request.json or {}

    if not data.get('email') or not data.get('password'):
        return jsonify(error='Missing email or password'), 400

    result, status_code = login_user(
        email=data['email'],
        password=data['password']
    )
    return jsonify(result), status_code


@auth_bp.route('/profile', methods=['GET', 'PATCH'])
@jwt_required()
def profile():
    """
    GET /api/auth/profile
    Get current user profile (protected - requires valid JWT token).

    PATCH /api/auth/profile
    Update current user profile (protected - requires valid JWT token).

    Headers:
    Authorization: Bearer <access_token>

    GET Response: 200 OK
    {
        "message": "Profile retrieved",
        "user": {
            "user_id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "role": "adopter",
            "created_at": "2025-11-14T10:30:00"
        }
    }

    PATCH Request body:
    {
        "full_name": "Updated Name",  // for adopters
        "address": "New Address",     // for adopters
        "phone_number": "123-456-7890", // for adopters
        "lifestyle": "active",        // for adopters
        "home_environment": "house",  // for adopters
        "family_composition": "single", // for adopters
        "pet_experience": "experienced", // for adopters

        "preferred_pet_age_min": 6,   // for adopters
        "preferred_pet_age_max": 24,  // for adopters
        "center_name": "New Center",  // for centers
        "location": "New Location",   // for centers
        "contact_number": "098-765-4321" // for centers
    }

    PATCH Response: 200 OK
    {
        "message": "Profile updated successfully"
    }

    If role='center', also includes center data.
    If role='adopter', also includes adopter data.
    """
    if request.method == 'GET':
        try:
            user_id = get_jwt_identity()
            result, status_code = get_user_profile(user_id=user_id)
            return jsonify(result), status_code
        except Exception as e:
            return jsonify(error=str(e)), 500
    elif request.method == 'PATCH':
        data = request.json or {}
        user_id = get_jwt_identity()

        claims = get_jwt()
        role = claims.get('role')

        if role == 'adopter':
            result, status = update_adopter_profile(user_id, **data)
        elif role == 'center':
            result, status = update_center_profile(user_id, **data)
        else:
            return jsonify(error='Invalid role'), 400

        return jsonify(result), status


@auth_bp.route('/admin/only', methods=['GET'])
@role_required('admin')
def admin_only():
    """
    GET /api/auth/admin/only
    Admin-only protected route (example).
    
    Headers:
    Authorization: Bearer <access_token>  (must have role='admin')
    
    Response: 200 OK
    {
        "message": "Admin access granted",
        "user_id": 1
    }
    """
    user_id = get_jwt_identity()
    return jsonify(message='Admin access granted', user_id=user_id), 200


@auth_bp.route('/center/info', methods=['GET'])
@role_required('center', 'admin')
def center_info():
    """
    GET /api/auth/center/info
    Adoption center or admin-only route (example).
    
    Headers:
    Authorization: Bearer <access_token>  (must have role='center' or 'admin')
    
    Response: 200 OK
    {
        "message": "Center info access granted",
        "user_id": 1,
        "role": "center"
    }
    """
    user_id = get_jwt_identity()
    claims = get_jwt()
    return jsonify(
        message='Center info access granted',
        user_id=user_id,
        role=claims['role']
    ), 200


@auth_bp.route('/firebase-login', methods=['POST'])
def firebase_login_route():
    """
    POST /api/auth/firebase-login
    Verification of Firebase ID Token and user login.
    """
    data = request.json or {}
    id_token = data.get('idToken')
    
    if not id_token:
        return jsonify(error='Missing idToken'), 400
        
    result, status_code = firebase_login(id_token)
    return jsonify(result), status_code


@auth_bp.route('/firebase-register', methods=['POST'])
def firebase_register_route():
    """
    POST /api/auth/firebase-register
    Complete registration for a new Firebase user.
    """
    data = request.json or {}
    id_token = data.get('idToken')
    role = data.get('role')
    username = data.get('username')
    
    if not id_token or not role:
        return jsonify(error='Missing idToken or role'), 400
        
    # Extra fields for profile
    kwargs = {
        'center_name': data.get('center_name'),
        'location': data.get('location'),
        'contact_number': data.get('contact_number'),
        'full_name': data.get('full_name'),
        'address': data.get('address'),
        'phone_number': data.get('phone_number'),
        'lifestyle': data.get('lifestyle'),
        'home_environment': data.get('home_environment'),
        'family_composition': data.get('family_composition'),
        'pet_experience': data.get('pet_experience'),
        'preferred_pet_age_min': data.get('preferred_pet_age_min'),
        'preferred_pet_age_max': data.get('preferred_pet_age_max')
    }
    
    result, status_code = firebase_register(id_token, role, username, **kwargs)
    return jsonify(result), status_code
