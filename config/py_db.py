"""
Python DB connection helpers for the Flask backend.
This reads the project's `config/.env` and exposes `mongo_client`, `mongo_db`, and `engine`.
"""
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo import MongoClient
from sqlalchemy import create_engine, text

# Load .env from repo config folder
env_path = Path(__file__).resolve().parent / '.env'
if not env_path.exists():
    # fallback to parent config folder (in case executed from backend)
    env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

# Mongo
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DB = os.getenv('MONGO_DB')
mongo_client = None
mongo_db = None
if MONGO_URI and MONGO_DB:
    try:
        # connect and test
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command('ping')

        # select database
        mongo_db = mongo_client[MONGO_DB]

        print(f"✓ MongoDB connected: {MONGO_URI} | DB: {MONGO_DB}")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        mongo_client = None
        mongo_db = None
else:
    print("✗ MONGO_URI or MONGO_DB not configured in .env")

# MySQL / SQLAlchemy
MYSQL_USER = os.getenv('MYSQL_USER') or os.getenv('MYSQL_USERNAME')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD') or os.getenv('MYSQL_PASS')
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE') or os.getenv('MYSQL_DB')
engine = None
if MYSQL_USER and MYSQL_PASSWORD and MYSQL_DATABASE:
    try:
        encoded_password = quote_plus(MYSQL_PASSWORD)
        connection_string = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        engine = create_engine(connection_string, pool_pre_ping=True)
        # quick test
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print(f"✓ MySQL connected: {MYSQL_HOST}:{MYSQL_PORT} | DB: {MYSQL_DATABASE}")
    except Exception as e:
        print(f"✗ MySQL connection failed: {e}")
        engine = None
else:
    print("✗ MySQL credentials not configured in .env")

# Exported names: mongo_client, mongo_db, engine
