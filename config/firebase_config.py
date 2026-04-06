import os
import firebase_admin
from firebase_admin import credentials, auth
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo config folder
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

firebase_app = None

def initialize_firebase():
    global firebase_app
    if firebase_app:
        return firebase_app

    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
    
    if not service_account_path:
        # Default fallback
        service_account_path = Path(__file__).resolve().parent / 'firebase-service-account.json'
    else:
        service_account_path = Path(service_account_path)

    if service_account_path.exists():
        try:
            cred = credentials.Certificate(str(service_account_path))
            firebase_app = firebase_admin.initialize_app(cred)
            print(f"[OK] Firebase Admin initialized using {service_account_path}")
        except Exception as e:
            print(f"[FAIL] Firebase Admin initialization failed: {e}")
    else:
        print(f"[WARN] Firebase service account file not found at {service_account_path}. Firebase auth will not work.")
    
    return firebase_app

# Auto-initialize
initialize_firebase()
