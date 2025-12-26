
"""
Compatibility Prediction Module for Pet Adoption System

This module predicts a Compatibility Score (0-100) indicating how suitable a pet is for a specific adopter.
It uses a pre-trained Random Forest Regressor with a defined preprocessing pipeline.
"""

import pandas as pd
import numpy as np
import joblib

# Load the pre-trained model
full_pipeline = joblib.load('ml_model/model/compatibility_model.pkl')

"""
    Predict compatibility score using the provided input data.

    Args:
        input_data (dict): Dictionary containing all required fields for the model.

    Returns:
        dict: A dictionary with 'compatibility_score' (float, 0-100) and 'match_label' ("High", "Medium", or "Low").
    """

def predict_compatibility(input_data):

    # Prepare DataFrame for prediction
    df = pd.DataFrame([input_data])

    # Predict score (pipeline handles preprocessing)
    score = full_pipeline.predict(df)[0]  # Scale to 0-100
    score = np.clip(score, 0, 100)  # Ensure within bounds

    # Determine match label
    if score >= 70:
        match_label = "High"
    elif score >= 40:
        match_label = "Medium"
    else:
        match_label = "Low"

    return {
        'compatibility_score': round(score, 2),
        'match_label': match_label
    }


