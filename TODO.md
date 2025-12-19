# TODO for Compatibility Prediction Module

## 1. Update ml_model/scripts/compatibility.py
- [x] Import necessary libraries (pandas, sklearn, joblib, numpy)
- [x] Define preprocessing pipeline:
  - [x] OneHotEncoder for categorical features: lifestyle, home_environment, family_composition, pet_experience, species, breed
  - [x] MinMaxScaler for numeric features: preferred_pet_age_min, preferred_pet_age_max, age, activity_level, temperament_score
  - [x] Create derived feature: age_match
- [x] Define RandomForestRegressor model with specified parameters
- [x] Implement predict_compatibility(adopter_data, pet_data) function:
  - [x] Preprocess adopter and pet data
  - [x] Combine into feature vector
  - [x] Predict score (0-100)
  - [x] Determine match_label based on thresholds
  - [x] Return dict with compatibility_score and match_label
- [x] Define placeholder train_model function for future training
- [x] Add clear documentation explaining deferred training

## 2. Verify requirements.txt has necessary dependencies
- [x] Ensure pandas, scikit-learn, joblib, numpy are present

## 3. Test the module (placeholder, since no training data)
- [x] Run the script to ensure no errors in definitions

## 4. Add API endpoint for compatibility prediction
- [x] Add /api/adoptions/compatibility route in adoption_routes.py
- [x] Fetch adopter and pet data from DB
- [x] Call predict_compatibility and return result

## 5. Update database schema
- [x] Add compatibility_score column to post_adoption_tracking table

## 6. Integrate compatibility prediction into adoption request creation
- [x] Modify create_adoption_request to calculate and store compatibility_score
- [x] Update get_requests_by_center and get_requests_by_adopter to include compatibility_score in responses
- [x] Update database schema and models for compatibility_score in adoption_requests

## 7. Update TODO.md
- [x] Mark completed tasks
