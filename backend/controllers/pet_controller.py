"""
Pet/Animal controller: handles CRUD operations for animals and vet records.
Uses MongoEngine for MongoDB integration.
Cross-database references: center_id links to MySQL adoption_centers table.
"""
from database.mongodb.models.animal import Animal, VetRecord
from datetime import datetime
from bson import ObjectId


def create_animal(name, species, center_id, breed=None, age=None, gender=None, description=None):
    """
    Create a new animal record.
    
    Args:
        name: Animal name
        species: Species (dog, cat, etc.)
        center_id: FK to MySQL adoption_centers.center_id
        breed, age, gender, description: optional fields
    
    Returns:
        dict with animal_id or error dict
    """
    try:
        animal = Animal(
            name=name,
            species=species,
            breed=breed,
            age=age,
            gender=gender,
            description=description,
            center_id=center_id,
            vet_records=[]
        )
        animal.save()
        return {
            'message': 'Animal created successfully',
            'animal_id': str(animal.id),
            'name': animal.name,
            'species': animal.species,
            'center_id': animal.center_id
        }, 201

    except Exception as e:
        return {'error': str(e)}, 500


def get_all_animals(center_id=None, is_adopted=None, species=None, limit=50, skip=0):
    """
    List all animals with optional filters.

    Args:
        center_id: optional filter by center
        is_adopted: optional filter by adoption status
        species: optional filter by species
        limit, skip: pagination

    Returns:
        list of animals or error dict
    """
    try:
        query = Animal.objects()

        if center_id is not None:
            query = query(center_id=center_id)
        if is_adopted is not None:
            query = query(is_adopted=is_adopted)
        if species is not None:
            query = query(species=species)

        total = query.count()
        animals = query.skip(skip).limit(limit).order_by('-created_at')

        # Get center names for each animal
        from backend.models.sql_models import AdoptionCenter
        from config.py_db import engine
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            animal_dicts = []
            for a in animals:
                animal_dict = a.to_dict()
                # Add center name
                center = session.query(AdoptionCenter).filter(AdoptionCenter.center_id == a.center_id).first()
                animal_dict['center_name'] = center.center_name if center else 'Unknown Center'
                animal_dicts.append(animal_dict)

            return {
                'total': total,
                'limit': limit,
                'skip': skip,
                'animals': animal_dicts
            }, 200
        finally:
            session.close()

    except Exception as e:
        return {'error': str(e)}, 500


def get_animal_by_id(animal_id):
    """
    Get animal details with all vet records.
    
    Args:
        animal_id: MongoDB ObjectId as string
    
    Returns:
        animal dict with vet records or error dict
    """
    try:
        animal = Animal.objects(id=animal_id).first()
        if not animal:
            return {'error': 'Animal not found'}, 404
        
        return {'animal': animal.to_dict()}, 200

    except Exception as e:
        return {'error': str(e)}, 500


def add_vet_record(animal_id, file_url=None, summary=None, stats=None, temperament_score=None, allowed_center_id=None, aggression_level=None, anxiety_level=None, sociability=None, obedience=None, health_behavior_flags=None):
    """
    Add a veterinary record to an animal.
    
    Args:
        animal_id: MongoDB ObjectId as string
        file_url: link to vet report
        summary: visit summary
        stats: dict with health metrics (weight, heart_rate, etc.)
        temperament_score: 0-1 behavioral score (computed)
        aggression_level, anxiety_level, sociability, obedience: 0-5 scales
        health_behavior_flags: binary/ordinal indicators
    
    Returns:
        dict with updated animal or error dict
    """
    try:
        animal = Animal.objects(id=animal_id).first()
        if not animal:
            return {'error': 'Animal not found'}, 404

        if allowed_center_id is not None and animal.center_id != allowed_center_id:
            return {'error': 'Forbidden: cannot add vet record to another center\'s animal'}, 403

        # Compute temperament_score if not provided
        if temperament_score is None:
            from ml_model.scripts.nlp_test_pipeline import calculate_temperament_score
            pet_data = {
                "weight": stats.get("weight", 0) if stats else 0,
                "heart_rate_bpm": stats.get("heart_rate", 0) if stats else 0,
                "activity_level": stats.get("activity_level", 0) if stats else 0,
                "medical_flags": health_behavior_flags or [],
                "vet_notes": summary or "",
                "aggression_level": aggression_level or 0,
                "anxiety_level": anxiety_level or 0,
                "sociability": sociability or 0,
                "obedience": obedience or 0
            }
            result = calculate_temperament_score(pet_data)
            temperament_score = result["temperament_score"]

        vet_record = VetRecord(
            file_url=file_url,
            summary=summary,
            stats=stats or {},
            temperament_score=temperament_score,
            last_updated=datetime.utcnow()
        )
        
        animal.vet_records.append(vet_record)
        animal.updated_at = datetime.utcnow()
        animal.save()
        
        return {
            'message': 'Vet record added successfully',
            'animal_id': str(animal.id),
            'vet_records_count': len(animal.vet_records),
            'temperament_score': temperament_score,
            'animal': animal.to_dict()
        }, 201

    except Exception as e:
        return {'error': str(e)}, 500


def update_animal_adoption_status(animal_id, is_adopted):
    """
    Mark animal as adopted or available.
    
    Args:
        animal_id: MongoDB ObjectId as string
        is_adopted: boolean
    
    Returns:
        dict with updated animal or error dict
    """
    try:
        animal = Animal.objects(id=animal_id).first()
        if not animal:
            return {'error': 'Animal not found'}, 404
        
        animal.is_adopted = is_adopted
        animal.updated_at = datetime.utcnow()
        animal.save()
        
        return {
            'message': f'Animal marked as {"adopted" if is_adopted else "available"}',
            'animal_id': str(animal.id),
            'is_adopted': animal.is_adopted
        }, 200

    except Exception as e:
        return {'error': str(e)}, 500


def get_animals_by_center(center_id):
    """
    Get all animals in a center (helper for center staff).
    
    Args:
        center_id: MySQL adoption_centers.center_id
    
    Returns:
        list of animals or error dict
    """
    try:
        animals = Animal.objects(center_id=center_id).order_by('-created_at')

        from backend.models.sql_models import AdoptionCenter
        from config.py_db import engine
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            center = session.query(AdoptionCenter).filter(AdoptionCenter.center_id == center_id).first()
            center_name = center.center_name if center else 'Unknown Center'

            animal_dicts = []
            for a in animals:
                animal_dict = a.to_dict()
                animal_dict['center_name'] = center_name
                animal_dicts.append(animal_dict)

            return {
                'center_id': center_id,
                'total': animals.count(),
                'animals': animal_dicts
            }, 200
        finally:
            session.close()

    except Exception as e:
        return {'error': str(e)}, 500


def update_animal_details(animal_id, allowed_center_id=None, **updates):
    """
    Update editable fields for an animal.

    Args:
        animal_id: MongoDB ObjectId string
        allowed_center_id: optional center_id that must match the animal
        updates: key/value pairs for editable fields
    """
    try:
        animal = Animal.objects(id=animal_id).first()
        if not animal:
            return {'error': 'Animal not found'}, 404

        if allowed_center_id is not None and animal.center_id != allowed_center_id:
            return {'error': 'Forbidden: cannot edit another center\'s animal'}, 403

        # Prevent editing if the animal is adopted
        if animal.is_adopted:
            return {'error': 'Cannot edit details of an adopted animal'}, 403

        editable_fields = {'name', 'breed', 'age', 'gender', 'description', 'is_adopted'}
        changed = False
        for field, value in updates.items():
            if field in editable_fields and value is not None:
                setattr(animal, field, value)
                changed = True

        if not changed:
            return {'error': 'No valid fields provided to update'}, 400

        animal.updated_at = datetime.utcnow()
        animal.save()
        return {
            'message': 'Animal updated successfully',
            'animal': animal.to_dict()
        }, 200

    except Exception as e:
        return {'error': str(e)}, 500
