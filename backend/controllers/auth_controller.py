"""
Authentication controller: handles user registration, login, and profile retrieval.
Uses bcrypt for password hashing and JWT for token generation.
Column names match schema.sql exactly.
"""
from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_
import uuid

from firebase_admin import auth as firebase_auth
from backend.models.sql_models import User, AdoptionCenter, Adopter, RoleEnum, LifestyleEnum, HomeEnvironmentEnum, CenterStatusEnum, PetExperienceEnum, FamilyCompositionEnum
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
        pet_experience = kwargs.get('pet_experience')
        family_composition = kwargs.get('family_composition')

        allowed_lifestyles = [e.value for e in LifestyleEnum]
        allowed_envs = [e.value for e in HomeEnvironmentEnum]
        allowed_pet_exp = [e.value for e in PetExperienceEnum]
        allowed_families = [e.value for e in FamilyCompositionEnum]

        if lifestyle is not None and lifestyle not in allowed_lifestyles:
            return {'error': f"Invalid lifestyle. allowed: {allowed_lifestyles}"}, 400

        if home_environment is not None and home_environment not in allowed_envs:
            return {'error': f"Invalid home_environment. allowed: {allowed_envs}"}, 400

        if pet_experience is not None and pet_experience not in allowed_pet_exp:
            return {'error': f"Invalid pet_experience. allowed: {allowed_pet_exp}"}, 400

        if family_composition is not None and family_composition not in allowed_families:
            return {'error': f"Invalid family_composition. allowed: {allowed_families}"}, 400
        
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
            family_composition_val = kwargs.get('family_composition')
            pet_experience_val = kwargs.get('pet_experience')
            preferred_pet_age_min_val = kwargs.get('preferred_pet_age_min')
            preferred_pet_age_max_val = kwargs.get('preferred_pet_age_max')

            # Normalize family_composition to replace underscores with spaces
            if family_composition_val:
                family_composition_val = family_composition_val.replace('_', ' ')

            # convert to enum objects if provided
            lifestyle_enum = None
            home_env_enum = None
            family_comp_enum = None
            pet_exp_enum = None
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
            if family_composition_val:
                try:
                    family_comp_enum = FamilyCompositionEnum(family_composition_val)
                except Exception:
                    return {'error': f'Invalid family_composition. allowed: {[e.value for e in FamilyCompositionEnum]}'}, 400
            if pet_experience_val:
                try:
                    pet_exp_enum = PetExperienceEnum(pet_experience_val)
                except Exception:
                    return {'error': f'Invalid pet_experience. allowed: {[e.value for e in PetExperienceEnum]}'}, 400

            new_adopter = Adopter(
                user_id=new_user.user_id,
                full_name=full_name,
                address=address,
                phone_number=phone_number,
                lifestyle=lifestyle_enum,
                home_environment=home_env_enum,
                family_composition=family_comp_enum,
                pet_experience=pet_exp_enum,
                preferred_pet_age_min=preferred_pet_age_min_val,
                preferred_pet_age_max=preferred_pet_age_max_val
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


def update_adopter_profile(user_id, full_name=None, address=None, phone_number=None, lifestyle=None, home_environment=None, family_composition=None, pet_experience=None, allergies=None, preferred_pet_age_min=None, preferred_pet_age_max=None):
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
        if family_composition is not None:
            adopter.family_composition = family_composition
        if pet_experience is not None:
            adopter.pet_experience = pet_experience
        if preferred_pet_age_min is not None:
            adopter.preferred_pet_age_min = preferred_pet_age_min
        if preferred_pet_age_max is not None:
            adopter.preferred_pet_age_max = preferred_pet_age_max

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

        # Check if center is approved before allowing login
        if user.role == RoleEnum.center:
            center = session.query(AdoptionCenter).filter(AdoptionCenter.user_id == user.user_id).first()
            if not center:
                return {'error': 'Center profile not found'}, 401
            if center.status != CenterStatusEnum.approved:
                return {'error': 'Your center registration is still pending approval. Please wait for admin approval.'}, 403
        
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


def verify_firebase_token(id_token):
    """
    Verify Firebase ID token and return user info.
    """
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"[verify_firebase_token] Error: {e}")
        return None


def firebase_login(id_token):
    """
    Login user via Firebase ID Token.
    Returns JWT if user exists in SQL, otherwise prompts for registration.
    """
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return {'error': 'Invalid or expired Firebase token'}, 401

    email = decoded_token.get('email')
    if not email:
        return {'error': 'Email not provided by Firebase'}, 400

    session = Session()
    try:
        user = session.query(User).filter(User.email == email).first()

        if not user:
            # User doesn't exist in SQL, Frontend should redirect to complete profile
            return {
                'message': 'Registration required',
                'needs_registration': True,
                'email': email,
                'username_suggestion': email.split('@')[0]
            }, 200

        # User exists, generate JWT
        user_id_str = str(user.user_id)
        access_token = create_access_token(
            identity=user_id_str,
            additional_claims={'role': user.role.value}
        )

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
        session.close()


def firebase_register(id_token, role, username=None, **kwargs):
    """
    Complete registration for a Firebase user.
    """
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return {'error': 'Invalid or expired Firebase token'}, 401

    email = decoded_token.get('email')
    if not email:
        return {'error': 'Email not provided by Firebase'}, 400

    if not username:
        username = email.split('@')[0] + "_" + str(uuid.uuid4())[:4]

    # Use a random password since they login via Firebase
    dummy_password = str(uuid.uuid4())
    
    # Delegate to regular register_user logic
    return register_user(
        username=username,
        email=email,
        password=dummy_password,
        role=role,
        **kwargs
    )


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
                    'contact_number': center.contact_number,
                    'status': center.status.value if center.status else None,
                    'reviewed_by': center.reviewed_by,
                    'reviewed_at': center.reviewed_at.isoformat() if center.reviewed_at else None
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
                    'home_environment': adopter.home_environment.value if adopter.home_environment else None,
                    'family_composition': adopter.family_composition.value if adopter.family_composition else None,
                    'pet_experience': adopter.pet_experience.value if adopter.pet_experience else None,

                    'preferred_pet_age_min': adopter.preferred_pet_age_min,
                    'preferred_pet_age_max': adopter.preferred_pet_age_max
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