"""
SQLAlchemy ORM models for MySQL tables.
All column names and types match schema.sql exactly.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean, Date, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class RoleEnum(enum.Enum):
    """Enum for user roles - matches schema ENUM"""
    admin = 'admin'
    center = 'center'
    adopter = 'adopter'


class LifestyleEnum(enum.Enum):
    """Enum for adopter lifestyle"""
    active = 'active'
    moderate = 'moderate'
    quiet = 'quiet'


class HomeEnvironmentEnum(enum.Enum):
    """Enum for home environment"""
    apartment = 'apartment'
    house = 'house'
    farm = 'farm'


class HealthStatusEnum(enum.Enum):
    """Enum for health status"""
    good = 'good'
    average = 'average'
    poor = 'poor'


class AdoptionStatusEnum(enum.Enum):
    """Enum for adoption request status"""
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'
    completed = 'completed'


class CenterStatusEnum(enum.Enum):
    """Enum for adoption center status"""
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'


class AdoptionOutcomeEnum(enum.Enum):
    """Enum for adoption outcome"""
    successful = 'successful'
    returned = 'returned'
    cancelled = 'cancelled'


class PetExperienceEnum(enum.Enum):
    """Enum for pet experience level"""
    beginner = 'beginner'
    intermediate = 'intermediate'
    expert = 'expert'


class FamilyCompositionEnum(enum.Enum):
    """Enum for family composition"""
    alone = 'alone'
    with_family = 'with family'
    with_children = 'with children'
    with_other_pets = 'with other pets'


class User(Base):
    """
    User table: user_id, username, email, password_hash, role, created_at
    Matches schema.sql columns exactly
    """
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # MATCHES SCHEMA
    role = Column(Enum(RoleEnum), nullable=False)  # admin, adopter, center
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    adoption_center = relationship('AdoptionCenter', back_populates='user', uselist=False, foreign_keys='AdoptionCenter.user_id')
    adopter = relationship('Adopter', back_populates='user', uselist=False)
    admin_logs = relationship('AdminLog', back_populates='admin')

    def __repr__(self):
        return f'<User {self.username} ({self.role.value})>'


class AdoptionCenter(Base):
    """
    Adoption centers table: center_id, user_id, center_name, location, contact_number, created_at, status, reviewed_by, reviewed_at
    Matches schema.sql columns exactly
    """
    __tablename__ = 'adoption_centers'

    center_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    center_name = Column(String(100), nullable=False)  # MATCHES SCHEMA
    location = Column(String(150))
    contact_number = Column(String(15))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(CenterStatusEnum), default=CenterStatusEnum.pending)  # pending, approved, rejected
    reviewed_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship('User', back_populates='adoption_center', foreign_keys=[user_id])
    adoption_requests = relationship('AdoptionRequest', back_populates='center')
    reviewer = relationship('User', foreign_keys=[reviewed_by])

    def __repr__(self):
        return f'<AdoptionCenter {self.center_name} - {self.status.value}>'


class Adopter(Base):
    """
    Adopters table: adopter_id, user_id, full_name, address, phone_number, lifestyle, home_environment, family_composition, pet_experience, preferred_pet_age_min, preferred_pet_age_max
    Matches schema.sql columns exactly
    """
    __tablename__ = 'adopters'

    adopter_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    full_name = Column(String(100))
    address = Column(String(255))
    phone_number = Column(String(15))
    lifestyle = Column(Enum(LifestyleEnum))  # active, moderate, quiet
    home_environment = Column(Enum(HomeEnvironmentEnum))  # apartment, house, farm
    family_composition = Column(Enum(FamilyCompositionEnum))  # alone, with family, with children, with other pets
    pet_experience = Column(Enum(PetExperienceEnum), default=PetExperienceEnum.beginner)  # beginner, intermediate, expert
    preferred_pet_age_min = Column(Integer)
    preferred_pet_age_max = Column(Integer)

    # Relationships
    user = relationship('User', back_populates='adopter')
    adoption_requests = relationship('AdoptionRequest', back_populates='adopter')

    def __repr__(self):
        return f'<Adopter {self.full_name}>'


class AdoptionRequest(Base):
    """
    Adoption requests table: request_id, adopter_id, center_id, animal_mongo_id, status, request_date, approval_date, compatibility_score, adoption_outcome
    Matches schema.sql columns exactly
    """
    __tablename__ = 'adoption_requests'

    request_id = Column(Integer, primary_key=True, autoincrement=True)
    adopter_id = Column(Integer, ForeignKey('adopters.adopter_id', ondelete='CASCADE'), nullable=False)
    center_id = Column(Integer, ForeignKey('adoption_centers.center_id', ondelete='CASCADE'), nullable=False)
    animal_mongo_id = Column(String(50), nullable=False)  # MongoDB ObjectId reference
    status = Column(Enum(AdoptionStatusEnum), default=AdoptionStatusEnum.pending)  # pending, approved, rejected, completed
    request_date = Column(DateTime, default=datetime.utcnow)
    approval_date = Column(DateTime, nullable=True)
    compatibility_score = Column(DECIMAL(5,2), default=0.0)  # Compatibility score
    adoption_outcome = Column(Enum(AdoptionOutcomeEnum), nullable=True)  # successful, returned, cancelled

    # Relationships
    adopter = relationship('Adopter', back_populates='adoption_requests')
    center = relationship('AdoptionCenter', back_populates='adoption_requests')
    tracking = relationship('PostAdoptionTracking', back_populates='adoption_request')

    def __repr__(self):
        return f'<AdoptionRequest {self.request_id} - {self.status.value}>'


class PostAdoptionTracking(Base):
    """
    Post-adoption tracking table: track_id, request_id, followup_date, notes, health_status
    Matches schema.sql columns exactly
    """
    __tablename__ = 'post_adoption_tracking'

    track_id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey('adoption_requests.request_id', ondelete='CASCADE'), nullable=False)
    followup_date = Column(Date)
    notes = Column(Text)
    health_status = Column(Enum(HealthStatusEnum))  # good, average, poor
    happiness_rating = Column(Integer, nullable=True)  # 1-5 rating
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    adoption_request = relationship('AdoptionRequest', back_populates='tracking')

    def __repr__(self):
        return f'<PostAdoptionTracking {self.track_id}>'


class AdminLog(Base):
    """
    Admin logs table: log_id, admin_id, action_type, details, timestamp
    Matches schema.sql columns exactly
    """
    __tablename__ = 'admin_logs'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    action_type = Column(String(50))
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    admin = relationship('User', back_populates='admin_logs')

    def __repr__(self):
        return f'<AdminLog {self.log_id}>'