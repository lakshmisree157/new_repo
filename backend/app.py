import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask import send_from_directory
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from sqlalchemy import text
from mongoengine import connect

# Import connections from config package
from config.py_db import mongo_client, mongo_db, engine

# Import blueprints
from backend.routes.auth_routes import auth_bp
from backend.routes.pet_routes import pet_bp
from backend.routes.adoption_routes import adopt_bp

app = Flask(__name__)

# Enable CORS for all routes (allow frontend to call backend)
CORS(app, resources={
    r"/api/*": {
        "origins": ["*", "http://localhost:8000", "http://127.0.0.1:8000", "file://"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 604800  # 7 days in seconds

# Initialize extensions
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# MongoEngine configuration (uses MONGO_URI from config/.env)
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DB_NAME = os.getenv('MONGO_DB') or os.getenv('MONGO_DATABASE') or 'pet_Adoptio'
if MONGO_URI:
    try:
        connect(db=MONGO_DB_NAME, host=MONGO_URI, uuidRepresentation='standard')
        print(f"✓ MongoEngine connected to {MONGO_DB_NAME}")
    except Exception as e:
        print(f"✗ MongoEngine connection failed: {e}")

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(pet_bp)
app.register_blueprint(adopt_bp)

# Serve minimal frontend pages and assets for local testing
FRONTEND_ROOT = project_root.joinpath('frontend')
FRONTEND_PAGES = FRONTEND_ROOT.joinpath('pages')
FRONTEND_ASSETS = FRONTEND_ROOT.joinpath('assets')


@app.route('/')
def serve_home():
    return send_from_directory(str(FRONTEND_PAGES), 'home.html')



@app.route('/adopter-login')
def serve_adopter_login():
    return send_from_directory(str(FRONTEND_PAGES), 'adopter-login.html')


@app.route('/center-login')
def serve_center_login():
    return send_from_directory(str(FRONTEND_PAGES), 'center-login.html')


@app.route('/adopter-register')
def serve_adopter_register():
    return send_from_directory(str(FRONTEND_PAGES), 'adopter-register.html')


@app.route('/center-register')
def serve_center_register():
    return send_from_directory(str(FRONTEND_PAGES), 'center-register.html')


@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory(str(FRONTEND_PAGES), 'dashboard.html')


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(str(FRONTEND_ASSETS), filename)


@app.route('/health')
def health():
    return jsonify(status='ok')


@app.route('/api/mongo/test')
def mongo_test():
    if not mongo_client:
        return jsonify(ok=False, error='MongoDB not configured'), 500
    try:
        db = mongo_db or mongo_client.get_database()
        collections = db.list_collection_names()
        return jsonify(ok=True, db=str(db.name), collections_count=len(collections), collections=collections)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.route('/api/mysql/test')
def mysql_test():
    if not engine:
        return jsonify(ok=False, error='MySQL not configured'), 500
    try:
        with engine.connect() as conn:
            r = conn.execute(text('SELECT 1 AS ok')).fetchone()
            return jsonify(ok=bool(r and r[0] == 1))
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.route('/api/auth/register', methods=['POST'])
def register_stub():
    """Deprecated: use POST /api/auth/register instead (via auth_routes blueprint)"""
    return jsonify(error='Use the new auth endpoint at /api/auth/register'), 410


@app.route('/api/auth/login', methods=['POST'])
def login_stub():
    """Deprecated: use POST /api/auth/login instead (via auth_routes blueprint)"""
    return jsonify(error='Use the new auth endpoint at /api/auth/login'), 410


if __name__ == '__main__':
    # Run with Flask for local development
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 4000)), debug=True)