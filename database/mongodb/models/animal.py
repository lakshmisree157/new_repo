"""
MongoEngine models for animal and veterinary records.
Database: pet_Adoptio (MongoDB)
Collections: animals (main collection with embedded vet_records)
"""
from mongoengine import Document, EmbeddedDocument, fields, errors
from datetime import datetime


class VetRecord(EmbeddedDocument):
    """
    Embedded document: veterinary record within an Animal document.
    Stores report info, health metrics, and behavioral assessment.
    Used for ML compatibility matching (temperament_score).
    """
    file_url = fields.StringField(max_length=500)  # Link to vet report (PDF, image, etc.)
    summary = fields.StringField(max_length=1000)  # Brief summary of visit
    stats = fields.DictField()  # {weight: kg, heart_rate: bpm, activity_level: %, ...}
    temperament_score = fields.FloatField(min_value=0.0, max_value=10.0)  # 0-10 scale for ML
    last_updated = fields.DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f"VetRecord ({self.last_updated.strftime('%Y-%m-%d')})"


class Animal(Document):
    """
    Main document: pet/animal in an adoption center.
    References MySQL adoption_centers.center_id for cross-db integrity.
    Embeds multiple VetRecord documents for health history.
    """
    name = fields.StringField(required=True, max_length=100)
    species = fields.StringField(required=True, max_length=50)  # dog, cat, rabbit, etc.
    breed = fields.StringField(max_length=100)
    age = fields.IntField(min_value=0)  # age in months
    gender = fields.StringField(choices=['male', 'female', 'unknown'])
    description = fields.StringField(max_length=1000)  # behavior, personality notes
    center_id = fields.IntField(required=True)  # FK to MySQL adoption_centers.center_id
    vet_records = fields.EmbeddedDocumentListField(VetRecord, default=list)
    
    # Metadata
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    is_adopted = fields.BooleanField(default=False)
    
    meta = {
        'collection': 'animals',
        'indexes': [
            'center_id',
            'species',
            'is_adopted',
            'created_at'
        ]
    }

    def __str__(self):
        return f"<Animal {self.name} ({self.species}) - Center {self.center_id}>"

    def to_dict(self):
        """Convert to dict for JSON serialization."""
        return {
            'id': str(self.id),
            'name': self.name,
            'species': self.species,
            'breed': self.breed,
            'age': self.age,
            'gender': self.gender,
            'description': self.description,
            'center_id': self.center_id,
            'vet_records': [
                {
                    'file_url': vr.file_url,
                    'summary': vr.summary,
                    'stats': vr.stats,
                    'temperament_score': vr.temperament_score,
                    'last_updated': vr.last_updated.isoformat() if vr.last_updated else None
                }
                for vr in self.vet_records
            ],
            'is_adopted': self.is_adopted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
