"""
Adoption controller: manage adoption requests and post-adoption tracking.
Uses SQLAlchemy models from `backend.models.sql_models`.
"""
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from backend.models.sql_models import (
    AdoptionRequest,
    Adopter,
    AdoptionCenter,
    PostAdoptionTracking,
    AdoptionStatusEnum
)
from config.py_db import engine

Session = sessionmaker(bind=engine)


def create_adoption_request(adopter_user_id, center_id, animal_mongo_id, db_session=None):
    session_created = False
    if db_session is None:
        session = Session()
        session_created = True
    else:
        session = db_session

    try:
        # Validate animal_mongo_id
        from bson import ObjectId
        try:
            ObjectId(animal_mongo_id)
        except:
            return {'error': 'Invalid animal mongo id'}, 400

        # locate adopter record (adopter_user_id may be string from JWT identity)
        try:
            adopter_user_int = int(adopter_user_id)
        except (TypeError, ValueError):
            return {'error': 'Invalid adopter user id'}, 422

        adopter = session.query(Adopter).filter(Adopter.user_id == adopter_user_int).first()
        if not adopter:
            return {'error': 'Adopter profile not found'}, 404

        # verify center exists
        center = session.query(AdoptionCenter).filter(AdoptionCenter.center_id == center_id).first()
        if not center:
            return {'error': 'Adoption center not found'}, 404

        # Check for duplicate request: same adopter and animal
        existing_request = session.query(AdoptionRequest).filter(
            AdoptionRequest.adopter_id == adopter.adopter_id,
            AdoptionRequest.animal_mongo_id == str(animal_mongo_id)
        ).first()
        if existing_request:
            return {'error': 'You have already submitted a request for this animal'}, 409

        req = AdoptionRequest(
            adopter_id=adopter.adopter_id,
            center_id=center_id,
            animal_mongo_id=str(animal_mongo_id),
            status=AdoptionStatusEnum.pending
        )
        session.add(req)
        session.commit()

        return {'message': 'Adoption request created', 'request_id': req.request_id}, 201

    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        if session_created:
            session.close()


def get_requests_by_center(center_id, db_session=None):
    session_created = False
    if db_session is None:
        session = Session()
        session_created = True
    else:
        session = db_session

    try:
        rows = session.query(AdoptionRequest).filter(AdoptionRequest.center_id == center_id).all()
        data = []

        # Import Animal model for animal details
        from database.mongodb.models.animal import Animal

        for r in rows:
            # Validate animal_mongo_id as ObjectId
            try:
                from bson import ObjectId
                ObjectId(r.animal_mongo_id)
            except:
                animal_name = 'Invalid Animal ID'
            else:
                animal = Animal.objects(id=r.animal_mongo_id).first()
                animal_name = animal.name if animal else 'Unknown Animal'

            adopter = session.query(Adopter).filter(Adopter.adopter_id == r.adopter_id).first()
            adopter_name = adopter.full_name if adopter and adopter.full_name else f'Adopter #{r.adopter_id}'

            data.append({
                'request_id': r.request_id,
                'adopter_id': r.adopter_id,
                'adopter_name': adopter_name,
                'center_id': r.center_id,
                'animal_mongo_id': r.animal_mongo_id,
                'animal_name': animal_name,
                'status': r.status.value if r.status else None,
                'request_date': r.request_date.isoformat() if r.request_date else None,
                'approval_date': r.approval_date.isoformat() if r.approval_date else None
            })
        return {'total': len(data), 'requests': data}, 200

    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        if session_created:
            session.close()


def get_requests_by_adopter(adopter_user_id, db_session=None):
    """
    Get adoption requests by adopter user_id (from JWT identity).
    Always expects user_id, finds adopter by user_id to avoid ID clashes.
    """
    session_created = False
    if db_session is None:
        session = Session()
        session_created = True
    else:
        session = db_session

    try:
        try:
            user_id = int(adopter_user_id)
        except (TypeError, ValueError):
            return {'error': 'Invalid user id'}, 422

        # Find adopter by user_id (standardized approach)
        adopter = session.query(Adopter).filter(Adopter.user_id == user_id).first()

        if not adopter:
            return {'error': 'Adopter profile not found'}, 404

        rows = session.query(AdoptionRequest).filter(AdoptionRequest.adopter_id == adopter.adopter_id).all()
        data = []

        # Import Animal model for animal details
        from database.mongodb.models.animal import Animal

        for r in rows:
            # Validate animal_mongo_id as ObjectId
            try:
                from bson import ObjectId
                ObjectId(r.animal_mongo_id)
            except:
                animal_name = 'Invalid Animal ID'
            else:
                animal = Animal.objects(id=r.animal_mongo_id).first()
                animal_name = animal.name if animal else 'Unknown Animal'

            # Get center details
            center = session.query(AdoptionCenter).filter(AdoptionCenter.center_id == r.center_id).first()
            center_name = center.center_name if center else 'Unknown Center'

            data.append({
                'request_id': r.request_id,
                'adopter_id': r.adopter_id,
                'center_id': r.center_id,
                'center_name': center_name,
                'animal_mongo_id': r.animal_mongo_id,
                'animal_name': animal_name,
                'status': r.status.value if r.status else None,
                'request_date': r.request_date.isoformat() if r.request_date else None,
                'approval_date': r.approval_date.isoformat() if r.approval_date else None
            })
        return {'total': len(data), 'requests': data}, 200

    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        if session_created:
            session.close()


def update_request_status(request_id, new_status, db_session=None):
    session_created = False
    if db_session is None:
        session = Session()
        session_created = True
    else:
        session = db_session

    try:
        req = session.query(AdoptionRequest).filter(AdoptionRequest.request_id == request_id).first()
        if not req:
            return {'error': 'Adoption request not found'}, 404

        # validate status
        allowed = [s.value for s in AdoptionStatusEnum]
        if new_status not in allowed:
            return {'error': f'Invalid status, allowed: {allowed}'}, 400

        req.status = AdoptionStatusEnum(new_status)
        if new_status == 'approved':
            req.approval_date = datetime.utcnow()
        session.add(req)
        session.commit()

        return {'message': 'Request status updated', 'request_id': req.request_id, 'status': req.status.value}, 200

    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        if session_created:
            session.close()


def add_post_adoption_tracking(request_id, followup_date=None, notes=None, health_status=None, db_session=None):
    session_created = False
    if db_session is None:
        session = Session()
        session_created = True
    else:
        session = db_session

    try:
        req = session.query(AdoptionRequest).filter(AdoptionRequest.request_id == request_id).first()
        if not req:
            return {'error': 'Adoption request not found'}, 404

        track = PostAdoptionTracking(
            request_id=request_id,
            followup_date=followup_date,
            notes=notes,
            health_status=health_status
        )
        session.add(track)
        session.commit()

        return {'message': 'Post-adoption tracking added', 'track_id': track.track_id}, 201

    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        if session_created:
            session.close()


def get_feedback_for_center(center_id, db_session=None):
    """
    Fetch post-adoption feedback entries scoped to a specific center.
    """
    session_created = False
    if db_session is None:
        session = Session()
        session_created = True
    else:
        session = db_session

    try:
        rows = session.query(PostAdoptionTracking, AdoptionRequest, Adopter).join(
            AdoptionRequest, PostAdoptionTracking.request_id == AdoptionRequest.request_id
        ).join(
            Adopter, AdoptionRequest.adopter_id == Adopter.adopter_id
        ).filter(
            AdoptionRequest.center_id == center_id
        ).all()

        from database.mongodb.models.animal import Animal
        feedback_items = []
        for track, request, adopter in rows:
            animal_name = 'Unknown Animal'
            try:
                from bson import ObjectId
                ObjectId(request.animal_mongo_id)
            except Exception:
                pass
            else:
                animal = Animal.objects(id=request.animal_mongo_id).first()
                if animal:
                    animal_name = animal.name

            feedback_items.append({
                'track_id': track.track_id,
                'request_id': request.request_id,
                'animal_mongo_id': request.animal_mongo_id,
                'dog_name': animal_name,
                'adopter_name': adopter.full_name if adopter else f'Adopter #{request.adopter_id}',
                'notes': track.notes,
                'health_status': track.health_status.value if track.health_status else None,
                'followup_date': track.followup_date.isoformat() if track.followup_date else None
            })

        return {'total': len(feedback_items), 'feedback': feedback_items}, 200

    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        if session_created:
            session.close()


def get_feedback_for_adopter(adopter_user_id, db_session=None):
    """
    Fetch post-adoption feedback entries for a specific adopter.
    """
    session_created = False
    if db_session is None:
        session = Session()
        session_created = True
    else:
        session = db_session

    try:
        try:
            user_id = int(adopter_user_id)
        except (TypeError, ValueError):
            return {'error': 'Invalid user id'}, 422

        # Find adopter by user_id
        adopter = session.query(Adopter).filter(Adopter.user_id == user_id).first()
        if not adopter:
            return {'error': 'Adopter profile not found'}, 404

        rows = session.query(PostAdoptionTracking, AdoptionRequest, AdoptionCenter).join(
            AdoptionRequest, PostAdoptionTracking.request_id == AdoptionRequest.request_id
        ).join(
            AdoptionCenter, AdoptionRequest.center_id == AdoptionCenter.center_id
        ).filter(
            AdoptionRequest.adopter_id == adopter.adopter_id
        ).all()

        from database.mongodb.models.animal import Animal
        feedback_items = []
        for track, request, center in rows:
            animal_name = 'Unknown Animal'
            try:
                from bson import ObjectId
                ObjectId(request.animal_mongo_id)
            except Exception:
                pass
            else:
                animal = Animal.objects(id=request.animal_mongo_id).first()
                if animal:
                    animal_name = animal.name

            feedback_items.append({
                'track_id': track.track_id,
                'request_id': request.request_id,
                'animal_mongo_id': request.animal_mongo_id,
                'dog_name': animal_name,
                'center_name': center.center_name if center else 'Unknown Center',
                'notes': track.notes,
                'health_status': track.health_status.value if track.health_status else None,
                'followup_date': track.followup_date.isoformat() if track.followup_date else None
            })

        return {'total': len(feedback_items), 'feedback': feedback_items}, 200

    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        if session_created:
            session.close()


def delete_adoption_request(request_id, adopter_user_id, db_session=None):
    """
    Delete a pending adoption request. Only the adopter who created it can delete it.
    """
    session_created = False
    if db_session is None:
        session = Session()
        session_created = True
    else:
        session = db_session

    try:
        # Find the adopter record
        try:
            adopter_user_int = int(adopter_user_id)
        except (TypeError, ValueError):
            return {'error': 'Invalid adopter user id'}, 422

        adopter = session.query(Adopter).filter(Adopter.user_id == adopter_user_int).first()
        if not adopter:
            return {'error': 'Adopter profile not found'}, 404

        # Find the request
        req = session.query(AdoptionRequest).filter(
            AdoptionRequest.request_id == request_id,
            AdoptionRequest.adopter_id == adopter.adopter_id
        ).first()

        if not req:
            return {'error': 'Adoption request not found or you do not have permission to delete it'}, 404

        # Only allow deletion of pending requests
        if req.status != AdoptionStatusEnum.pending:
            return {'error': 'Only pending requests can be deleted'}, 400

        session.delete(req)
        session.commit()

        return {'message': 'Adoption request deleted successfully', 'request_id': request_id}, 200

    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        if session_created:
            session.close()
