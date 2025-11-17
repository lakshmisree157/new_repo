# Pet Adoption Authentication - Test Guide

## Prerequisites

1. **Start MySQL**: Ensure MySQL is running with the `dbms_db` database.
2. **Create tables**: Run the schema:
   ```sql
   mysql -u root -p dbms_db < database/mysql/auth_schema.sql
   ```
3. **Install backend dependencies**:
   ```powershell
   cd backend
   pip install -r requirements.txt
   ```
4. **Start Flask app**:
   ```powershell
   python app.py
   ```
   Expected output:
   ```
   ✓ MySQL connected: localhost:3306 | DB: dbms_db
   ✓ MongoDB connected: ...
   * Running on http://127.0.0.1:4000
   ```

---

## API Endpoints

### 1. Health Check
```bash
GET /health
```

**curl**:
```bash
curl http://localhost:4000/health
```

**Expected Response** (200 OK):
```json
{
  "status": "ok"
}
```

---

### 2. Register User

**POST /api/auth/register**

**Request Body** (application/json):
```json
{
  "username": "john_adopter",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "role": "adopter"
}
```

**curl**:
```bash
curl -X POST http://localhost:4000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_adopter",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "role": "adopter"
  }'
```

**Expected Response** (201 Created):
```json
{
  "message": "User registered successfully",
  "user_id": 1,
  "username": "john_adopter",
  "email": "john@example.com",
  "role": "adopter"
}
```

---

### 3. Register Adoption Center

**POST /api/auth/register** (with role='adoption_center')

**Request Body**:
```json
{
  "username": "shelter_paws",
  "email": "paws@shelter.com",
  "password": "SecurePass123!",
  "role": "adoption_center",
  "center_name": "Pawsome Shelter",
  "location": "123 Main St, Anytown",
  "contact_number": "555-1234"
}
```

**curl**:
```bash
curl -X POST http://localhost:4000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "shelter_paws",
    "email": "paws@shelter.com",
    "password": "SecurePass123!",
    "role": "adoption_center",
    "center_name": "Pawsome Shelter",
    "location": "123 Main St, Anytown",
    "contact_number": "555-1234"
  }'
```

**Expected Response** (201 Created):
```json
{
  "message": "User registered successfully",
  "user_id": 2,
  "username": "shelter_paws",
  "email": "paws@shelter.com",
  "role": "adoption_center"
}
```

---

### 4. Login

**POST /api/auth/login**

**Request Body**:
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**curl**:
```bash
curl -X POST http://localhost:4000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response** (200 OK):
```json
{
  "message": "Login successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": 1,
  "username": "john_adopter",
  "email": "john@example.com",
  "role": "adopter"
}
```

**Save the access_token for protected endpoints.**

---

### 5. Get User Profile (Protected)

**GET /api/auth/profile**

**Headers**: `Authorization: Bearer <access_token>`

**curl** (using token from login response):
```bash
curl -X GET http://localhost:4000/api/auth/profile \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Expected Response** (200 OK):
```json
{
  "user": {
    "user_id": 1,
    "username": "john_adopter",
    "email": "john@example.com",
    "role": "adopter",
    "is_active": true,
    "created_at": "2025-11-14T10:30:00"
  }
}
```

**If adoption_center role, also includes**:
```json
{
  "user": {
    "user_id": 2,
    "username": "shelter_paws",
    "email": "paws@shelter.com",
    "role": "adoption_center",
    "is_active": true,
    "created_at": "2025-11-14T10:35:00",
    "adoption_center": {
      "center_id": 1,
      "name": "Pawsome Shelter",
      "location": "123 Main St, Anytown",
      "contact_number": "555-1234"
    }
  }
}
```

---

### 6. Admin-Only Route (Protected)

**GET /api/auth/admin/only**

Accessible **only by users with role='admin'**.

**curl**:
```bash
curl -X GET http://localhost:4000/api/auth/admin/only \
  -H "Authorization: Bearer <admin-token>"
```

**Response if authorized** (200 OK):
```json
{
  "message": "Admin access granted",
  "user_id": 3
}
```

**Response if not authorized** (403 Forbidden):
```json
{
  "error": "Forbidden: insufficient permissions"
}
```

---

### 7. Center Info Route (Protected)

**GET /api/auth/center/info**

Accessible by users with role='adoption_center' **or** 'admin'.

**curl**:
```bash
curl -X GET http://localhost:4000/api/auth/center/info \
  -H "Authorization: Bearer <center-or-admin-token>"
```

**Response if authorized** (200 OK):
```json
{
  "message": "Center info access granted",
  "user_id": 2,
  "role": "adoption_center"
}
```

---

## Postman Collection (JSON)

Save as `postman_collection.json` and import into Postman:

```json
{
  "info": {
    "name": "Pet Adoption Auth",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Register Adopter",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"username\": \"adopter1\", \"email\": \"adopter@example.com\", \"password\": \"SecurePass123!\", \"role\": \"adopter\"}"
        },
        "url": {
          "raw": "http://localhost:4000/api/auth/register",
          "protocol": "http",
          "host": ["localhost"],
          "port": "4000",
          "path": ["api", "auth", "register"]
        }
      }
    },
    {
      "name": "Login",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"email\": \"adopter@example.com\", \"password\": \"SecurePass123!\"}"
        },
        "url": {
          "raw": "http://localhost:4000/api/auth/login",
          "protocol": "http",
          "host": ["localhost"],
          "port": "4000",
          "path": ["api", "auth", "login"]
        }
      }
    },
    {
      "name": "Get Profile",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ],
        "url": {
          "raw": "http://localhost:4000/api/auth/profile",
          "protocol": "http",
          "host": ["localhost"],
          "port": "4000",
          "path": ["api", "auth", "profile"]
        }
      }
    }
  ]
}
```

**In Postman**:
1. After login, copy the `access_token`.
2. Set it as Postman environment variable: `{{access_token}}`.
3. Use in `Authorization` header for protected routes.

---

## Running Tests

```powershell
cd backend
pip install pytest
python -m pytest tests/test_auth.py -v
```

Expected output (all tests pass):
```
test_auth.py::test_health PASSED
test_auth.py::test_register_adopter PASSED
test_auth.py::test_register_adoption_center PASSED
test_auth.py::test_login_success PASSED
test_auth.py::test_profile_with_token PASSED
test_auth.py::test_admin_only_route PASSED
...
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'config'` | Python path issue | Run from project root; ensure `sys.path` includes project root |
| `No such table: users` | Schema not created | Run `mysql ... < database/mysql/auth_schema.sql` |
| `401 Unauthorized` | Missing or invalid token | Ensure token is in `Authorization: Bearer <token>` header |
| `403 Forbidden` | Insufficient role permissions | Use appropriate user role for endpoint |
| `MySQL connection failed` | DB not running or wrong credentials | Check `config/.env` and MySQL service status |

---

## Architecture

- **backend/models/sql_models.py**: SQLAlchemy ORM models (`User`, `AdoptionCenter`)
- **backend/controllers/auth_controller.py**: Business logic (register, login, profile)
- **backend/routes/auth_routes.py**: Flask routes and role-based decorator
- **config/py_db.py**: DB connection (MySQL via SQLAlchemy)
- **database/mysql/auth_schema.sql**: SQL schema for users and adoption_centers tables

Role-based access is enforced via the `@role_required(...)` decorator.
