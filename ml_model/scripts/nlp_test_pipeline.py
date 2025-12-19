import numpy as np
import re
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer

# -------------------------------
# 1. KEYWORD DICTIONARY (DOMAIN-BASED)
# -------------------------------

BEHAVIOR_KEYWORDS = {
    "aggressive": -0.6,
    "anxious": -0.3,
    "calm": 0.4,
    "friendly": 0.5,
    "active": 0.2,
    "fearful": -0.4,
    "alert": 0.2
}

# -------------------------------
# 2. TEXT PREPROCESSING
# -------------------------------

def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    return text

# -------------------------------
# 3. NLP TEXT SCORE
# -------------------------------

def compute_text_score(vet_notes: str) -> float:
    text = preprocess_text(vet_notes)
    score = 0.0
    count = 0

    for word, weight in BEHAVIOR_KEYWORDS.items():
        if word in text:
            score += weight
            count += 1

    if count == 0:
        return 0.5  # neutral behavior

    # normalize to [0,1]
    normalized_score = (score / count + 1) / 2
    return np.clip(normalized_score, 0, 1)

# -------------------------------
# 4. PHYSIOLOGICAL SCORE
# -------------------------------

def compute_physio_score(weight, heart_rate, activity_level, medical_flags):
    """
    Assumptions:
    - Normal dog BPM ≈ 60–120
    - activity_level: 1–10
    """

    scaler = MinMaxScaler()

    numeric_features = np.array([
        weight,
        heart_rate,
        activity_level
    ]).reshape(-1, 1)

    normalized = scaler.fit_transform(numeric_features).flatten()

    # medical penalty
    medical_penalty = 0.1 * len(medical_flags)

    physio_score = np.mean(normalized) - medical_penalty
    return np.clip(physio_score, 0, 1)

# -------------------------------
# 5. FINAL TEMPERAMENT SCORE
# -------------------------------

def calculate_temperament_score(pet_data: dict) -> dict:
    """
    pet_data keys:
    weight, heart_rate_bpm, activity_level,
    medical_flags, vet_notes
    """

    physio_score = compute_physio_score(
        pet_data["weight"],
        pet_data["heart_rate_bpm"],
        pet_data["activity_level"],
        pet_data["medical_flags"]
    )

    text_score = compute_text_score(pet_data["vet_notes"])

    alpha = 0.5  # equal importance
    temperament_score = alpha * physio_score + (1 - alpha) * text_score

    return {
        "temperament_score": round(temperament_score, 2),
        "physio_score": round(physio_score, 2),
        "text_score": round(text_score, 2)
    }

# -------------------------------
# 6. SAMPLE USAGE
# -------------------------------

sample_pet = {
    "weight": 18,
    "heart_rate_bpm": 110,
    "activity_level": 8,
    "medical_flags": [],
    "vet_notes": "Dog is alert, slightly anxious around strangers, very active and friendly."
}

result = calculate_temperament_score(sample_pet)
print(result)
