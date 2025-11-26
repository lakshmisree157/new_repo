"""
Authentication controller: handles user registration, login, and profile retrieval.
Uses bcrypt for password hashing and JWT for token generation.
Column names match schema.sql exactly.
"""
from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_

from backend.models.sql_models import User, AdoptionCenter, Adopter, RoleEnum,LifestyleEnum, HomeEnvironmentEnum
from config.py_db import engine

bcrypt = Bcrypt()
Session = sessionmaker(bind=engine)


def register_user(username, email, password, role, db_session=None, **kwargs):
    """
    Register a new user with bcrypt-hashed password.
    
    Args:
        username (str): Unique username
        email (str): Unique email address
        password (str): Plain text password (will be hashed with bcrypt)
        role (str): 'admin', 'center', or 'adopter'
        **kwargs: Additional data (center_name, location, contact_number for centers;
                 full_name, address, phone_number, lifestyle, home_environment for adopters)
    
    Returns:
        tuple: (response_dict, status_code)
    """
    session_created = False
    if db_session is None:
        session = Session()
        session_created = True
    else:
        session = db_session
    try:
        # Check if user already exists
        existing_user = session.query(User).filter(
            or_(User.email == email, User.username == username)
        ).first()
        
        if existing_user:
            return {'error': 'Email or username already registered'}, 409
        
        if role not in {r.value for r in RoleEnum}:
            return {'error': f"Invalid role. allowed: {[r.value for r in RoleEnum]}"}, 400

    # Validate adopter enums if provided
        lifestyle = kwargs.get('lifestyle')
        home_environment = kwargs.get('home_environment')

        allowed_lifestyles = [e.value for e in LifestyleEnum]
        allowed_envs = [e.value for e in HomeEnvironmentEnum]

        if lifestyle is not None and lifestyle not in allowed_lifestyles:
            return {'error': f"Invalid lifestyle. allowed: {allowed_lifestyles}"}, 400

        if home_environment is not None and home_environment not in allowed_envs:
            return {'error': f"Invalid home_environment. allowed: {allowed_envs}"}, 400
        
        # Hash password using bcrypt
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create user with password_hash column (matches schema)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_pw,  # MATCHES SCHEMA COLUMN NAME
            role=RoleEnum[role]
        )
        session.add(new_user)
        session.flush()  # Get user_id before commit
        
        # If center role, create adoption center record
        if role == 'center':
            center_name = kwargs.get('center_name', 'Unnamed Center')
            location = kwargs.get('location', '')
            contact_number = kwargs.get('contact_number', '')
            
            new_center = AdoptionCenter(
                user_id=new_user.user_id,
                center_name=center_name,  # MATCHES SCHEMA
                location=location,
                contact_number=contact_number
            )
            session.add(new_center)
        
        # If adopter role, create adopter record
        if role == 'adopter':
            full_name = kwargs.get('full_name', '')
            address = kwargs.get('address', '')
            phone_number = kwargs.get('phone_number', '')
            lifestyle_val = kwargs.get('lifestyle')
            home_environment_val = kwargs.get('home_environment')

            # convert to enum objects if provided
            lifestyle_enum = None
            home_env_enum = None
            if lifestyle_val:
                try:
                    lifestyle_enum = LifestyleEnum(lifestyle_val)
                except Exception:
                    return {'error': f'Invalid lifestyle. allowed: {[e.value for e in LifestyleEnum]}'}, 400
            if home_environment_val:
                try:
                    home_env_enum = HomeEnvironmentEnum(home_environment_val)
                except Exception:
                    return {'error': f'Invalid home_environment. allowed: {[e.value for e in HomeEnvironmentEnum]}'}, 400

            new_adopter = Adopter(
                user_id=new_user.user_id,
                full_name=full_name,
                address=address,
                phone_number=phone_number,
                lifestyle=lifestyle_enum,
                home_environment=home_env_enum
            )
            session.add(new_adopter)
        
        session.commit()
        
        return {
            'message': 'User registered successfully',
            'user': {
                'user_id': new_user.user_id,
                'username': new_user.username,
                'email': new_user.email,
                'role': new_user.role.value
            }
        }, 201
    
    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        if session_created:
            session.close()


def update_adopter_profile(user_id, full_name=None, address=None, phone_number=None, lifestyle=None, home_environment=None):
    session_created = False
    if not user_id:
        return {'error': 'User ID is required'}, 400

    session = None
    try:
        session = Session()
        user_id_int = int(user_id)
        adopter = session.query(Adopter).filter(Adopter.user_id == user_id_int).first()
        if not adopter:
            return {'error': 'Adopter profile not found'}, 404

        if full_name is not None:
            adopter.full_name = full_name
        if address is not None:
            adopter.address = address
        if phone_number is not None:
            adopter.phone_number = phone_number
        if lifestyle is not None:
            adopter.lifestyle = lifestyle  # Assumes validated enum passed from route
        if home_environment is not None:
            adopter.home_environment = home_environment

        session.add(adopter)
        session.commit()

        return {'message': 'Adopter profile updated successfully'}, 200
    except Exception as e:
        if session:
            session.rollback()
        return {'error': str(e)}, 500
    finally:
        if session:
            session.close()


def update_center_profile(user_id, center_name=None, location=None, contact_number=None):
    session_created = False
    if not user_id:
        return {'error': 'User ID is required'}, 400

    session = None
    try:
        session = Session()
        user_id_int = int(user_id)
        center = session.query(AdoptionCenter).filter(AdoptionCenter.user_id == user_id_int).first()
        if not center:
            return {'error': 'Center profile not found'}, 404

        if center_name is not None:
            center.center_name = center_name
        if location is not None:
            center.location = location
        if contact_number is not None:
            center.contact_number = contact_number

        session.add(center)
        session.commit()

        return {'message': 'Center profile updated successfully'}, 200
    except Exception as e:
        if session:
            session.rollback()
        return {'error': str(e)}, 500
    finally:
        if session:
            session.close()


def login_user(email, password, db_session=None):
    """
    Authenticate user and return JWT token.
    
    Args:
        email (str): User email
        password (str): Plain text password to verify against password_hash
    
    Returns:
        tuple: (response_dict, status_code)
    """
    session_created = False
    if db_session is None:
        session = Session()
        session_created = True
    else:
        session = db_session

    try:
        # Find user by email
        user = session.query(User).filter(User.email == email).first()

        
        
        if not user:
            return {'error': 'Invalid email or password'}, 401
        
        # Verify password against password_hash (matches schema)
        if not bcrypt.check_password_hash(user.password_hash, password):  # MATCHES SCHEMA COLUMN
            return {'error': 'Invalid email or password'}, 401
        
        user_id_str = str(user.user_id)
        
        # Generate JWT token
        access_token = create_access_token(
            identity=user_id_str,
            additional_claims={'role': user.role.value}
        )

        print(f'[login_user] Token created for user_id={user_id_str}, role={user.role.value}')
        
        return {
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'role': user.role.value
            }
        }, 200
    
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        if session_created:
            session.close()


def get_user_profile(user_id, db_session=None):
    """
    Retrieve user profile by user_id (from JWT token).
    
    Args:
        user_id (int): User ID from JWT identity
    
    Returns:
        tuple: (response_dict, status_code)
    """
    session_created = False
    if db_session is None:
        session = Session()
        session_created = True
    else:
        session = db_session

    try:
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            print(f'[get_user_profile] Invalid user_id type: {type(user_id)} = {user_id}')
            return {'error': f'Invalid user_id: {user_id}'}, 422
        
        print(f'[get_user_profile] Fetching profile for user_id={user_id_int}')
        
        user = session.query(User).filter(User.user_id == user_id_int).first()
        
        if not user:
            return {'error': 'User not found'}, 404
        
        profile = {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value,
            'created_at': user.created_at.isoformat()
        }
        
        # Add role-specific data
        if user.role == RoleEnum.center:
            center = session.query(AdoptionCenter).filter(AdoptionCenter.user_id == user_id_int).first()
            if center:
                profile['center'] = {
                    'center_id': center.center_id,
                    'center_name': center.center_name,  # MATCHES SCHEMA
                    'location': center.location,
                    'contact_number': center.contact_number
                }
        
        if user.role == RoleEnum.adopter:
            adopter = session.query(Adopter).filter(Adopter.user_id == user_id_int).first()
            if adopter:
                profile['adopter'] = {
                    'adopter_id': adopter.adopter_id,
                    'full_name': adopter.full_name,
                    'address': adopter.address,
                    'phone_number': adopter.phone_number,
                    'lifestyle': adopter.lifestyle.value if adopter.lifestyle else None,
                    'home_environment': adopter.home_environment.value if adopter.home_environment else None
                }
        
        # if user.role == RoleEnum.center:
        #     center = session.query(center).filter(center.user_id == user_id_int).first()
        #     if adopter:
        #         profile['center'] = {
        #             'center_id': adopter.center_id,
        #             'center_name': adopter.center_name,
        #             'location': adopter.location,
        #             'contact_number': adopter.contact_number
                    
        #         }
        
        return {'message': 'Profile retrieved', 'user': profile}, 200
    
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        if session_created:
            session.close()