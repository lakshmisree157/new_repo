"""
Pet/Animal routes for the pet adoption backend.
Endpoints:
  - POST /api/pets — Create new animal (center only)
  - GET /api/pets — List all animals
  - GET /api/pets/<id> — Get animal details
  - POST /api/pets/<id>/vet-record — Add vet record (center only)
  - PUT /api/pets/<id>/status — Mark as adopted (center only)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from backend.controllers.pet_controller import (
    create_animal,
    get_all_animals,
    get_animal_by_id,
    add_vet_record,
    update_animal_adoption_status,
    get_animals_by_center,
    update_animal_details
)
from backend.models.sql_models import AdoptionCenter
from config.py_db import engine
from sqlalchemy.orm import sessionmaker

# Create blueprint
pet_bp = Blueprint('pets', __name__, url_prefix='/api/pets')
Session = sessionmaker(bind=engine)


def role_required(*required_roles):
    """
    Decorator to enforce role-based access control.
    Usage: @role_required('center', 'admin')
    """
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


def get_center_id_for_user(user_id):
    """Lookup center_id for the given center user."""
    session = Session()
    try:
        center = session.query(AdoptionCenter).filter(AdoptionCenter.user_id == user_id).first()
        return center.center_id if center else None
    finally:
        session.close()


@pet_bp.route('', methods=['POST'])
@jwt_required()
@role_required('center', 'admin')
def create_pet():
    """
    POST /api/pets
    Create a new animal record (center or admin only).
    
    Headers:
    Authorization: Bearer <access_token>  (must have role='center' or 'admin')
    
    Request body:
    {
        "name": "Buddy",
        "species": "dog",
        "breed": "Golden Retriever",
        "age": 36,
        "gender": "male",
        "description": "Friendly and energetic puppy",
        "center_id": 1
    }
    
    Response: 201 Created
    {
        "message": "Animal created successfully",
        "animal_id": "507f1f77bcf86cd799439011",
        "name": "Buddy",
        "species": "dog",
        "center_id": 1
    }
    """
    data = request.json or {}
    
    # Validate required fields
    required = ['name', 'species', 'center_id']
    if not all(k in data for k in required):
        return jsonify(error='Missing required fields: name, species, center_id'), 400
    # Restrict species to dogs only for this project
    if data.get('species') and data.get('species').lower() != 'dog':
        return jsonify(error='Only species "dog" is supported in this demo'), 400
    
    result, status_code = create_animal(
        name=data['name'],
        species=data['species'],
        center_id=data['center_id'],
        breed=data.get('breed'),
        age=data.get('age'),
        gender=data.get('gender'),
        description=data.get('description')
    )
    return jsonify(result), status_code


@pet_bp.route('', methods=['GET'])
def list_pets():
    """
    GET /api/pets
    List all animals with optional filters.
    No authentication required for listing.
    
    Query parameters:
    - center_id: filter by center
    - is_adopted: filter by adoption status (true/false)
    - species: filter by species
    - limit: max results (default: 50)
    - skip: pagination offset (default: 0)
    
    Example: GET /api/pets?center_id=1&species=dog&limit=10
    
    Response: 200 OK
    {
        "total": 2,
        "limit": 10,
        "skip": 0,
        "animals": [
            {
                "id": "507f1f77bcf86cd799439011",
                "name": "Buddy",
                "species": "dog",
                "breed": "Golden Retriever",
                "age": 36,
                "gender": "male",
                "description": "Friendly and energetic",
                "center_id": 1,
                "vet_records": [],
                "is_adopted": false,
                "created_at": "2025-11-14T10:30:00",
                "updated_at": "2025-11-14T10:30:00"
            }
        ]
    }
    """
    # Parse query parameters
    center_id = request.args.get('center_id', type=int)
    is_adopted = request.args.get('is_adopted', type=lambda x: x.lower() == 'true')
    species = request.args.get('species', type=str) or 'dog'
    limit = request.args.get('limit', default=50, type=int)
    skip = request.args.get('skip', default=0, type=int)
    
    result, status_code = get_all_animals(
        center_id=center_id,
        is_adopted=is_adopted,
        species=species,
        limit=limit,
        skip=skip
    )
    return jsonify(result), status_code


@pet_bp.route('/<animal_id>', methods=['GET'])
def get_pet(animal_id):
    """
    GET /api/pets/<animal_id>
    Get animal details with all vet records.
    No authentication required.
    
    Response: 200 OK
    {
        "animal": {
            "id": "507f1f77bcf86cd799439011",
            "name": "Buddy",
            "species": "dog",
            "breed": "Golden Retriever",
            "age": 36,
            "gender": "male",
            "description": "Friendly and energetic",
            "center_id": 1,
            "vet_records": [
                {
                    "file_url": "https://example.com/vet_report_1.pdf",
                    "summary": "Annual checkup. All healthy.",
                    "stats": {"weight": 30.5, "heart_rate": 75, "activity_level": 85},
                    "temperament_score": 8.5,
                    "last_updated": "2025-11-10T14:20:00"
                }
            ],
            "is_adopted": false,
            "created_at": "2025-11-14T10:30:00",
            "updated_at": "2025-11-14T10:30:00"
        }
    }
    """
    result, status_code = get_animal_by_id(animal_id)
    return jsonify(result), status_code


@pet_bp.route('/<animal_id>', methods=['PATCH'])
@jwt_required()
@role_required('center', 'admin')
def edit_pet(animal_id):
    """
    PATCH /api/pets/<animal_id>
    Update editable animal fields (center/admin only).
    """
    data = request.json or {}
    editable = ['name', 'breed', 'age', 'gender', 'description', 'is_adopted']
    updates = {}

    for field in editable:
        if field in data:
            value = data.get(field)
            if field == 'age' and value is not None:
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    return jsonify(error='Age must be a number'), 400
            if field == 'is_adopted' and value is not None:
                value = bool(value)
            updates[field] = value

    if not updates:
        return jsonify(error='No editable fields provided'), 400

    allowed_center_id = None
    claims = get_jwt()
    if claims.get('role') == 'center':
        try:
            user_id = int(get_jwt_identity())
        except (TypeError, ValueError):
            return jsonify(error='Invalid user identity'), 400
        center_id = get_center_id_for_user(user_id)
        if center_id is None:
            return jsonify(error='Center profile not found'), 404
        allowed_center_id = center_id

    result, status_code = update_animal_details(animal_id, allowed_center_id=allowed_center_id, **updates)
    return jsonify(result), status_code


@pet_bp.route('/<animal_id>/vet-record', methods=['POST'])
@jwt_required()
@role_required('center', 'admin')
def add_vet_report(animal_id):
    """
    POST /api/pets/<animal_id>/vet-record
    Add a veterinary record to an animal (center or admin only).
    
    Headers:
    Authorization: Bearer <access_token>  (must have role='center' or 'admin')
    
    Request body:
    {
        "file_url": "https://example.com/vet_report.pdf",
        "summary": "Annual checkup. All vitals normal.",
        "stats": {
            "weight": 30.5,
            "heart_rate": 75,
            "activity_level": 85
        },
        "temperament_score": 8.5
    }
    
    Response: 201 Created
    {
        "message": "Vet record added successfully",
        "animal_id": "507f1f77bcf86cd799439011",
        "vet_records_count": 1,
        "animal": { ... full animal object ... }
    }
    """
    data = request.json or {}
    
    result, status_code = add_vet_record(
        animal_id=animal_id,
        file_url=data.get('file_url'),
        summary=data.get('summary'),
        stats=data.get('stats'),
        temperament_score=data.get('temperament_score')
    )
    return jsonify(result), status_code


@pet_bp.route('/<animal_id>/status', methods=['PUT'])
@jwt_required()
@role_required('center', 'admin')
def update_pet_status(animal_id):
    """
    PUT /api/pets/<animal_id>/status
    Mark animal as adopted or available (center or admin only).
    
    Headers:
    Authorization: Bearer <access_token>  (must have role='center' or 'admin')
    
    Request body:
    {
        "is_adopted": true
    }
    
    Response: 200 OK
    {
        "message": "Animal marked as adopted",
        "animal_id": "507f1f77bcf86cd799439011",
        "is_adopted": true
    }
    """
    data = request.json or {}
    
    if 'is_adopted' not in data:
        return jsonify(error='Missing field: is_adopted'), 400
    
    result, status_code = update_animal_adoption_status(
        animal_id=animal_id,
        is_adopted=data['is_adopted']
    )
    return jsonify(result), status_code


@pet_bp.route('/center/<int:center_id>/animals', methods=['GET'])
@jwt_required()
@role_required('center', 'admin')
def get_center_animals(center_id):
    """
    GET /api/pets/center/<center_id>/animals
    Get all animals managed by a center (center or admin only).
    
    Headers:
    Authorization: Bearer <access_token>  (must have role='center' or 'admin')
    
    Response: 200 OK
    {
        "center_id": 1,
        "total": 5,
        "animals": [
            { ... animal objects ... }
        ]
    }
    """
    # Optional: verify that the requesting user owns this center
    claims = get_jwt()
    user_id = get_jwt_identity()
    user_role = claims.get('role')
    
    # For center users, restrict to their own center
    # (This would require an additional DB lookup to verify ownership)
    # For now, admins can see all, centers can see any (improve with center ownership check)
    
    result, status_code = get_animals_by_center(center_id)
    return jsonify(result), status_code
