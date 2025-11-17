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


def add_vet_record(animal_id, file_url=None, summary=None, stats=None, temperament_score=None):
    """
    Add a veterinary record to an animal.
    
    Args:
        animal_id: MongoDB ObjectId as string
        file_url: link to vet report
        summary: visit summary
        stats: dict with health metrics (weight, heart_rate, etc.)
        temperament_score: 0-10 behavioral score (for ML)
    
    Returns:
        dict with updated animal or error dict
    """
    try:
        animal = Animal.objects(id=animal_id).first()
        if not animal:
            return {'error': 'Animal not found'}, 404
        
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
        return {
            'center_id': center_id,
            'total': animals.count(),
            'animals': [a.to_dict() for a in animals]
        }, 200

    except Exception as e:
        return {'error': str(e)}, 500
