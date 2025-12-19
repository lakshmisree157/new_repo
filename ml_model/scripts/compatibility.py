
"""
Compatibility Prediction Module for Pet Adoption System

This module predicts a Compatibility Score (0-100) indicating how suitable a pet is for a specific adopter.
It uses a Random Forest Regressor with a defined preprocessing pipeline.

Data-First Lifecycle:
1. Pipeline definition (current)
2. Data collection (future)
3. Supervised training (future)
4. Model improvement (future)

No training is performed now due to lack of labeled data.
Training will use adoption_outcome: 'successful' -> high compatibility, 'returned'/'cancelled' -> low compatibility.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

# Define feature lists
CATEGORICAL_FEATURES = [
    'lifestyle', 'home_environment', 'family_composition', 'pet_experience',  # adopter
    'species', 'breed'  # pet
]

NUMERIC_FEATURES = [
    'preferred_pet_age_min', 'preferred_pet_age_max',  # adopter
    'age', 'activity_level', 'temperament_score'  # pet
]

# Preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES),
        ('num', MinMaxScaler(), NUMERIC_FEATURES)
    ]
)

# Random Forest Regressor model (not trained yet)
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    random_state=42
)

# Full pipeline: preprocessing + model
full_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('regressor', model)
])

def predict_compatibility(adopter_data, pet_data):
    """
    Predict compatibility score between an adopter and a pet.

    Args:
        adopter_data (dict): Adopter profile with keys matching CATEGORICAL_FEATURES and NUMERIC_FEATURES
        pet_data (dict): Pet profile with keys matching CATEGORICAL_FEATURES and NUMERIC_FEATURES

    Returns:
        dict: {
            "compatibility_score": float (0-100),
            "match_label": str ("High" | "Medium" | "Low")
        }
    """
    # Combine adopter and pet data
    combined_data = {**adopter_data, **pet_data}

    # Create derived feature: age_match
    pet_age = combined_data.get('age', 0)
    min_age = combined_data.get('preferred_pet_age_min', 0)
    max_age = combined_data.get('preferred_pet_age_max', 100)
    age_match = 1 if min_age <= pet_age <= max_age else 0
    combined_data['age_match'] = age_match

    # Prepare DataFrame for prediction
    df = pd.DataFrame([combined_data])

    # Predict score (pipeline will handle preprocessing)
    # Note: Since model is not trained, this will raise an error if called
    # For now, return a placeholder score
    try:
        score = full_pipeline.predict(df)[0] * 100  # Scale to 0-100
        score = np.clip(score, 0, 100)  # Ensure within bounds
    except:
        # Placeholder until model is trained
        score = 50.0  # Neutral score

    # Determine label
    if score >= 75:
        label = "High"
    elif score >= 50:
        label = "Medium"
    else:
        label = "Low"

    return {
        "compatibility_score": round(score, 2),
        "match_label": label
    }

def train_model(X_train, y_train):
    """
    Placeholder function for training the model.
    To be called when labeled data becomes available.

    Args:
        X_train (pd.DataFrame): Feature matrix
        y_train (pd.Series): Target labels (0-1 scale for compatibility)

    Future training data will come from adoption_outcome:
    - 'successful' -> high compatibility (e.g., 0.8-1.0)
    - 'returned'/'cancelled' -> low compatibility (e.g., 0.0-0.3)
    """
    # Fit the full pipeline
    full_pipeline.fit(X_train, y_train)

    # Save the trained model
    joblib.dump(full_pipeline, '../models/compatibility_model.joblib')
    print("Model trained and saved to ../models/compatibility_model.joblib")

def load_model():
    """
    Load a trained model for predictions.
    """
    return joblib.load('../models/compatibility_model.joblib')

if __name__ == '__main__':
    # Example usage (placeholder data)
    adopter_example = {
        'lifestyle': 'active',
        'home_environment': 'house',
        'family_composition': 'with family',
        'pet_experience': 'intermediate',
        'preferred_pet_age_min': 1,
        'preferred_pet_age_max': 5
    }

    pet_example = {
        'species': 'dog',
        'breed': 'german shepherd',
        'age': 3,
        'activity_level': 3,
        'temperament_score': 0.7
    }

    result = predict_compatibility(adopter_example, pet_example)
    print("Compatibility Prediction:", result)
