from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from backend.models.sql_models import AdoptionCenter, AdminLog, CenterStatusEnum
from config.py_db import engine

Session = sessionmaker(bind=engine)

def list_pending_centers():
    session = Session()
    try:
        centers = session.query(AdoptionCenter).filter(AdoptionCenter.status == CenterStatusEnum.pending).all()
        data = [{
            'center_id': c.center_id,
            'center_name': c.center_name,
            'location': c.location,
            'contact_number': c.contact_number,
            'status': c.status.value,
            'created_at': c.created_at.isoformat() if c.created_at else None
        } for c in centers]
        return {'total': len(data), 'centers': data}, 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500
    finally:
        session.close()

def review_center(center_id, admin_user_id, action):
    session = Session()
    try:
        center = session.query(AdoptionCenter).filter(AdoptionCenter.center_id == center_id).first()
        if not center:
            return {'error': 'Center not found'}, 404
        if center.status != CenterStatusEnum.pending:
            return {'message': f'Center already reviewed: {center.status.value}'}, 200

        if action == 'approve':
            center.status = CenterStatusEnum.approved
            action_type = 'approve_center'
            message = 'Center approved successfully'
        elif action == 'reject':
            center.status = CenterStatusEnum.rejected
            action_type = 'reject_center'
            message = 'Center rejected successfully'
        else:
            return {'error': 'Invalid action. Use "approve" or "reject"'}, 400

        center.reviewed_by = admin_user_id
        center.reviewed_at = datetime.utcnow()
        session.add(center)

        # Log this admin action
        log = AdminLog(
            admin_id=admin_user_id,
            action_type=action_type,
            details=f'{action.capitalize()}d adoption center: {center.center_name} (ID: {center.center_id})',
            timestamp=datetime.utcnow()
        )
        session.add(log)
        session.commit()

        return {'message': message}, 200
    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        session.close()
