
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Add the backend directory to the path to import database models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from config.py_db import engine
from sqlalchemy.orm import sessionmaker
from backend.models.sql_models import PostAdoptionTracking, AdoptionRequest, Adopter, AdoptionCenter
from database.mongodb.models.animal import Animal

# Configuration
RETRAIN_THRESHOLD = 100  # Retrain when we have 100+ post-adoption records
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'model', 'compatibility_model.pkl')
BACKUP_MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'model', 'compatibility_model_backup.pkl')

class CompatibilityModelRetrainer:
    def __init__(self):
        self.engine = engine
        self.Session = sessionmaker(bind=engine)

    def check_retrain_needed(self):
        """Check if retraining is needed based on data volume."""
        session = self.Session()
        try:
            count = session.query(PostAdoptionTracking).count()
            print(f"Current post-adoption tracking records: {count}")
            return count >= RETRAIN_THRESHOLD
        finally:
            session.close()

    def get_training_data(self):
        """Fetch training data from database."""
        session = self.Session()
        try:
            # Get post-adoption tracking with related data
            tracking_records = session.query(PostAdoptionTracking).all()

            training_data = []
            for record in tracking_records:
                # Get adoption request details
                adoption_request = session.query(AdoptionRequest).filter(
                    AdoptionRequest.request_id == record.request_id
                ).first()

                if not adoption_request:
                    continue

                # Get adopter details
                adopter = session.query(Adopter).filter(
                    Adopter.adopter_id == adoption_request.adopter_id
                ).first()

                if not adopter:
                    continue

                # Get center details
                center = session.query(AdoptionCenter).filter(
                    AdoptionCenter.center_id == adoption_request.center_id
                ).first()

                if not center:
                    continue

                # Get animal details from MongoDB
                try:
                    animal = Animal.objects(id=adoption_request.animal_mongo_id).first()
                    if not animal:
                        continue

                    # Get latest vet record
                    latest_vet = max(animal.vet_records, key=lambda v: v.last_updated) if animal.vet_records else None

                    # Create training record
                    training_record = {
                        # Adopter features
                        'lifestyle': adopter.lifestyle.value if adopter.lifestyle else None,
                        'home_environment': adopter.home_environment.value if adopter.home_environment else None,
                        'family_composition': adopter.family_composition.value if adopter.family_composition else None,
                        'pet_experience': adopter.pet_experience.value if adopter.pet_experience else None,
                        'preferred_pet_age_min': adopter.preferred_pet_age_min,
                        'preferred_pet_age_max': adopter.preferred_pet_age_max,

                        # Pet features
                        'species': animal.species,
                        'breed': animal.breed or '',
                        'age': animal.age,
                        'activity_level': latest_vet.stats.get('activity_level', 0) if latest_vet else 0,
                        'temperament_score': latest_vet.temperament_score if latest_vet else 0.5,

                        # Target: happiness rating (1-5 scale, convert to 0-100)
                        'compatibility_score': (record.happiness_rating / 5.0) * 100
                    }

                    training_data.append(training_record)

                except Exception as e:
                    print(f"Error processing animal {adoption_request.animal_mongo_id}: {e}")
                    continue

            return pd.DataFrame(training_data)

        finally:
            session.close()

    def create_pipeline(self):
        """Create the preprocessing and model pipeline."""
        # Define categorical and numerical features
        categorical_features = ['lifestyle', 'home_environment', 'family_composition', 'pet_experience', 'species', 'breed']
        numerical_features = ['preferred_pet_age_min', 'preferred_pet_age_max', 'age', 'activity_level', 'temperament_score']

        # Create preprocessing steps
        categorical_transformer = Pipeline(steps=[
            ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])

        numerical_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())
        ])

        # Combine preprocessing
        preprocessor = ColumnTransformer(
            transformers=[
                ('cat', categorical_transformer, categorical_features),
                ('num', numerical_transformer, numerical_features)
            ])

        # Create full pipeline
        pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            ))
        ])

        return pipeline

    def train_model(self, df):
        """Train the compatibility model."""
        print(f"Training with {len(df)} samples...")

        # Prepare features and target
        feature_cols = [col for col in df.columns if col != 'compatibility_score']
        X = df[feature_cols]
        y = df['compatibility_score']

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Create and train pipeline
        pipeline = self.create_pipeline()
        pipeline.fit(X_train, y_train)

        # Evaluate
        y_pred = pipeline.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(".2f")
        print(".3f")

        return pipeline

    def backup_current_model(self):
        """Create a backup of the current model."""
        if os.path.exists(MODEL_PATH):
            import shutil
            shutil.copy2(MODEL_PATH, BACKUP_MODEL_PATH)
            print(f"Current model backed up to {BACKUP_MODEL_PATH}")

    def save_model(self, pipeline):
        """Save the trained model."""
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(pipeline, MODEL_PATH)
        print(f"New model saved to {MODEL_PATH}")

    def retrain_model(self):
        """Main retraining workflow."""
        print("Starting compatibility model retraining...")

        # Check if retraining is needed
        if not self.check_retrain_needed():
            print(f"Retraining not needed. Need at least {RETRAIN_THRESHOLD} records.")
            return False

        # Get training data
        df = self.get_training_data()
        if len(df) < RETRAIN_THRESHOLD:
            print(f"Insufficient training data: {len(df)} records")
            return False

        # Backup current model
        self.backup_current_model()

        # Train new model
        pipeline = self.train_model(df)

        # Save new model
        self.save_model(pipeline)

        print("Model retraining completed successfully!")
        return True

def main():
    """Main function to run the retraining script."""
    try:
        retrainer = CompatibilityModelRetrainer()
        success = retrainer.retrain_model()

        if success:
            print("\n✅ Model retraining completed successfully!")
            print("The new model is now active.")
        else:
            print("\nℹ️  Model retraining was not performed.")
            print("Either retraining is not needed or insufficient data is available.")

    except Exception as e:
        print(f"\n❌ Error during model retraining: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
