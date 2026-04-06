# 🐾 Pet Adoption Platform

A full-stack pet adoption system with multi-role authentication (Admin, Adopter, Adoption Centers), MySQL/MongoDB databases, Firebase auth, and ML-powered compatibility matching.

## ✨ Features
- **Multi-Role System**: Admins manage system, Adopters request pets, Centers list animals
- **Databases**: MySQL (users/requests), MongoDB (animals with rich docs)
- **Auth**: JWT + Firebase Admin SDK
- **Frontend**: Responsive HTML/JS dashboards served by Flask
- **ML**: Scikit-learn compatibility model (`ml_model/model/compatibility_model.pkl`)
- **API-First**: REST endpoints under `/api/*`

## 📋 Prerequisites
- Python 3.8+
- MySQL 8.0+ server
- MongoDB 4.0+ server
- Firebase project (for auth)
- Git

## 🚀 Quick Start

### 1. Clone & Navigate
```cmd
cd /d d:\com_Code\dbms_el
git clone <your-repo> .  REM if not already cloned
```

### 2. Setup `.env` (Critical!)
Copy `config/.env.example` to `config/.env` (create if missing) and fill:

```env
# MySQL
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_pass
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=dbms_db

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=pet_adoption

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-prod

# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=config/firebase-service-account.json
```

**Firebase Setup**:
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create project → Project Settings → Service Accounts → Generate new key (JSON)
3. Save as `config/firebase-service-account.json`

### 3. Database Setup
**MySQL**:
```cmd
mysql -u root -p < database/mysql/schema.sql
```

**MongoDB**: Auto-creates DB/collections on first connect. Define animal models in `database/mongodb/models/animal.py`.

### 4. Install Dependencies
```cmd
REM Backend
pip install -r backend/requirements.txt

REM ML (optional, for retraining)
pip install -r ml_model/requirements.txt
```

### 5. Run Backend (Serves API + Frontend!)
```cmd
cd backend
set FLASK_ENV=development
python app.py
```
- Backend: `http://localhost:4000`
- Frontend pages: `http://localhost:4000/home.html`, `/adopter-login`, `/admin-dashboard.html`, etc.
- API Health: `http://localhost:4000/health`
- API Docs: Check routes in `backend/routes/*.py`

**Expected Output**:
```
✓ MongoEngine connected to pet_adoption
✓ MySQL connected: localhost:3306 | DB: dbms_db
✓ Firebase Admin initialized
 * Running on http://0.0.0.0:4000
```

## 🛠️ Development

### Backend Only
```cmd
cd backend
python app.py
```

### Frontend Development
- Edit `frontend/pages/*.html` and `frontend/assets/*`
- Auto-reloads via Flask static serving
- For production: Build SPA (e.g., React) and serve via nginx/CDN

### ML Model Usage/Retraining
1. Predict compatibility:
   ```python
   # In backend or script
   import joblib
   model = joblib.load('ml_model/model/compatibility_model.pkl')
   score = model.predict(adopter_features, pet_features)
   ```
2. Retrain:
   ```cmd
   cd ml_model/scripts
   python retrain_compatibility_model.py
   ```

### Testing DB Connections
```
GET http://localhost:4000/api/mysql/test  → MySQL status
GET http://localhost:4000/api/mongo/test → MongoDB status
```

## 📁 File Structure
```
d:/com_Code/dbms_el/
├── backend/              # Flask API + static frontend serving
│   ├── app.py           # Main app
│   ├── requirements.txt
│   ├── routes/          # API blueprints (auth, pets, adoptions)
│   └── controllers/     # Business logic
├── frontend/            # Static HTML/JS
│   ├── pages/           # Dashboards (admin/adopter/center)
│   └── assets/          # JS/CSS (firebase-auth-helper.js, api.js)
├── config/              # .env, DB connections, Firebase
├── database/
│   ├── mysql/schema.sql  # Users/adopters/requests
│   └── mongodb/models/   # Animal schemas
├── ml_model/            # Compatibility model
└── README.md            # This file!
```

## 🔌 API Endpoints Summary
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Create user (admin/adopter/center) |
| `/api/auth/login` | POST | JWT token |
| `/api/pets/` | GET/POST | List/add animals (MongoDB) |
| `/api/adoptions/` | POST | Request adoption w/ ML score |
| `/admin-dashboard.html` | GET | Admin UI |

**Full routes**: See `backend/routes/*.py`

## 🐛 Troubleshooting
| Issue | Solution |
|-------|----------|
| `DB connection failed` | Check `.env`, start MySQL/MongoDB services |
| `Firebase not found` | Add service account JSON |
| `CORS error` | Allowed for localhost:* |
| `Module not found` | `pip install -r backend/requirements.txt` |
| Port 4000 busy | `set PORT=5000 && python app.py` |

## 🚀 Production Deployment
1. Use Gunicorn + Nginx: `gunicorn -w 4 -b 0.0.0.0:4000 app:app`
2. Dockerize (Dockerfile needed)
3. Cloud: Heroku/Railway (DB addons), Firebase Hosting for frontend

## 🤝 Contributing
1. Fork & PR
2. Follow PEP8
3. Update tests in `backend/services/manual_test.py`

**Questions?** Open an issue!

---

*Built with ❤️ for pet lovers*

