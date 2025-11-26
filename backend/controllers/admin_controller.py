from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from backend.models.sql_models import AdoptionCenter, AdminLog
from config.py_db import engine

Session = sessionmaker(bind=engine)

def list_unverified_centers():
    session = Session()
    try:
        centers = session.query(AdoptionCenter).filter(AdoptionCenter.verified == False).all()
        data = [{
            'center_id': c.center_id,
            'center_name': c.center_name,
            'location': c.location,
            'contact_number': c.contact_number,
            'verified': c.verified
        } for c in centers]
        return {'total': len(data), 'centers': data}, 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500
    finally:
        session.close()

def verify_center(center_id, admin_user_id):
    session = Session()
    try:
        center = session.query(AdoptionCenter).filter(AdoptionCenter.center_id == center_id).first()
        if not center:
            return {'error': 'Center not found'}, 404
        if center.verified:
            return {'message': 'Center already verified'}, 200

        center.verified = True
        session.add(center)

        # Log this admin action
        log = AdminLog(
            admin_id=admin_user_id,
            action_type='verify_center',
            details=f'Verified adoption center: {center.center_name} (ID: {center.center_id})',
            timestamp=datetime.utcnow()
        )
        session.add(log)
        session.commit()

        return {'message': 'Center verified successfully'}, 200
    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        session.close()
