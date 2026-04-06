import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ensure project root is in sys.path for absolute imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sqlalchemy.orm import sessionmaker
from backend.models.sql_models import AdoptionRequest, PostAdoptionTracking, Adopter, User, AdoptionStatusEnum
from config.py_db import engine
from dotenv import load_dotenv
from pathlib import Path

# Load env
env_path = Path(__file__).resolve().parent.parent.parent / 'config' / '.env'
load_dotenv(dotenv_path=env_path)

GRID_API = os.getenv('GRID_API')
FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL')

Session = sessionmaker(bind=engine)

def send_reminder_email(adopter_email, adopter_name, dog_name):
    if not GRID_API or not FROM_EMAIL:
        print("[FAIL] SendGrid not configured. Skipping email.")
        return

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=adopter_email,
        subject='We want to hear from you and your new friend! 🐾',
        plain_text_content=f'Hi {adopter_name},\n\nIt has been a few days since you adopted {dog_name}. We would love to get an update on how things are going! Please log in to your dashboard and share some feedback.\n\nBest,\nPetConnect Team'
    )
    try:
        sg = SendGridAPIClient(GRID_API)
        response = sg.send(message)
        print(f"[OK] Reminder sent to {adopter_email} for {dog_name}. Status: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Failed to send email to {adopter_email}: {e}")

def run_reminder_service():
    session = Session()
    try:
        # Find approved adoptions
        approved_requests = session.query(AdoptionRequest).filter(
            AdoptionRequest.status.in_([AdoptionStatusEnum.approved, AdoptionStatusEnum.completed])
        ).all()

        now = datetime.utcnow()
        for req in approved_requests:
            # Join to get adopter info
            adopter_user = session.query(User).join(Adopter, User.user_id == Adopter.user_id).filter(
                Adopter.adopter_id == req.adopter_id
            ).first()
            
            if not adopter_user:
                continue

            adopter_name = adopter_user.adopter.full_name or adopter_user.username
            adopter_email = adopter_user.email
            
            # Find latest animal name from mongo if possible, but for service we might just need ID or cached name
            # For simplicity, we'll just say "your dog" or similar if name is not easily available in SQL
            # AdoptionRequest doesn't have animal_name in SQL, only animal_mongo_id.
            # To avoid dependencying on MongoDB in a background service if possible, 
            # we could fetch it once.
            dog_name = "your new friend" # Default

            # Check latest feedback
            latest_feedback = session.query(PostAdoptionTracking).filter(
                PostAdoptionTracking.request_id == req.request_id
            ).order_by(PostAdoptionTracking.created_at.desc()).first()

            should_remind = False
            if not latest_feedback:
                # No feedback yet. Check approval date.
                if req.approval_date and (now - req.approval_date).days >= 5:
                    should_remind = True
            else:
                # Feedback exists. Check last feedback date.
                if (now - latest_feedback.created_at).days >= 5:
                    should_remind = True

            if should_remind:
                send_reminder_email(adopter_email, adopter_name, dog_name)

    finally:
        session.close()

if __name__ == '__main__':
    print("Starting Post-Adoption Feedback Reminder Service...")
    run_reminder_service()
    print("Reminder service execution completed.")
