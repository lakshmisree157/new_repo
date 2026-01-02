import numpy as np
import re
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer

# -------------------------------
# 1. KEYWORD DICTIONARY (DOMAIN-BASED)
# -------------------------------

BEHAVIOR_KEYWORDS = {
    # Negative/High Risk
    "aggressive": -0.8,
    "fearful": -0.5,
    "anxious": -0.4,
    "skittish": -0.4,
    "timid": -0.3,
    "destructive": -0.6,
    
    # Positive
    "calm": 0.4,
    "friendly": 0.6,
    "gentle": 0.5,
    "docile": 0.4,
    "playful": 0.5,
    "social": 0.4,
    "obedient": 0.5,
    
    # Neutral/Situational
    "active": 0.2,
    "alert": 0.2,
    "protective": 0.1
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
    words = text.split()
    
    score = 0.0
    count = 0
    
    negations = {"not", "no", "never", "none", "without"}
    intensifiers = {"very", "extremely", "highly", "really", "so"}
    
    for i, word in enumerate(words):
        if word in BEHAVIOR_KEYWORDS:
            weight = BEHAVIOR_KEYWORDS[word]
            
            # Check for negation (look back 2 words)
            is_negated = False
            for j in range(max(0, i-2), i):
                if words[j] in negations:
                    is_negated = True
                    break
            
            if is_negated:
                weight = -weight * 0.8 # Invert and dampen
            
            # Check for intensifiers
            for j in range(max(0, i-1), i):
                if words[j] in intensifiers:
                    weight *= 1.5
                    break
            
            score += weight
            count += 1

    if count == 0:
        return 0.5  # neutral behavior

    # normalize to [0,1]
    # score/count will be roughly between -1 and 1
    normalized_score = (score / count + 1) / 2
    return np.clip(normalized_score, 0, 1)

# -------------------------------
# 4. PHYSIOLOGICAL SCORE
# -------------------------------

def compute_physio_score(weight, heart_rate, activity_level, medical_flags):
    """
    Evaluates physiological stability using ideal ranges.
    Ideal HR: 70-110 bpm
    Ideal Activity: 5-8 (Moderate-High)
    """
    
    # 1. Heart Rate Score
    hr_score = 1.0
    if heart_rate < 60 or heart_rate > 140:
        hr_score = 0.3 # High distress
    elif heart_rate < 70 or heart_rate > 120:
        hr_score = 0.6 # Slight distress/Excitement
    
    # 2. Activity Level Score
    act_score = 1.0
    if activity_level <= 2 or activity_level >= 9:
        act_score = 0.5 # Hyper-active or Lethargic
    elif activity_level <= 4:
        act_score = 0.8 # Calm/Low energy
        
    # 3. Medical Penalty
    medical_penalty = 0.15 * len(medical_flags)
    
    # Combine (Heart rate is a stronger indicator of current stress)
    physio_score = (0.6 * hr_score + 0.4 * act_score) - medical_penalty
    return np.clip(physio_score, 0, 1)

# -------------------------------
# 5. BEHAVIORAL SCORE
# -------------------------------

def compute_behavioral_score(aggression_level, anxiety_level, sociability, obedience):
    """
    Compute behavioral score with safety factors (aggression/anxiety) weighted higher.
    Inputs are 0-5 scales.
    """
    # Weights for each behavior category
    weights = {
        "aggression": 1.5,
        "anxiety": 1.2,
        "sociability": 1.0,
        "obedience": 0.8
    }
    
    # Normalize each to 0-1 (low is better for aggression/anxiety)
    agg_val = (1 - (aggression_level / 5.0)) * weights["aggression"]
    anx_val = (1 - (anxiety_level / 5.0)) * weights["anxiety"]
    soc_val = (sociability / 5.0) * weights["sociability"]
    obe_val = (obedience / 5.0) * weights["obedience"]
    
    total_weight = sum(weights.values())
    behavioral_score = (agg_val + anx_val + soc_val + obe_val) / total_weight
    
    return np.clip(behavioral_score, 0, 1)

# -------------------------------
# 5. FINAL TEMPERAMENT SCORE
# -------------------------------

def calculate_temperament_score(pet_data: dict) -> dict:
    """
    Combines three dimensions into a final temperament score.
    Now weighted towards behavioral stability (50%).
    """

    physio_score = compute_physio_score(
        pet_data.get("weight", 15),
        pet_data.get("heart_rate_bpm", 80),
        pet_data.get("activity_level", 5),
        pet_data.get("medical_flags", [])
    )

    text_score = compute_text_score(pet_data.get("vet_notes", ""))

    behavioral_score = compute_behavioral_score(
        pet_data.get("aggression_level", 0),
        pet_data.get("anxiety_level", 0),
        pet_data.get("sociability", 0),
        pet_data.get("obedience", 0)
    )

    # FINAL WEIGHTED MIX
    # Behavioral (50%) + Text (30%) + Physio (20%)
    temperament_score = (
        0.50 * behavioral_score + 
        0.30 * text_score + 
        0.20 * physio_score
    )

    return {
        "temperament_score": round(temperament_score, 2),
        "details": {
            "behavioral": round(behavioral_score, 2),
            "textual": round(text_score, 2),
            "physiological": round(physio_score, 2)
        }
    }

# -------------------------------
# 6. ENHANCED SAMPLE USAGE / TESTING
# -------------------------------

if __name__ == "__main__":
    test_cases = [
        {
            "name": "Standard Positive",
            "data": {
                "weight": 18, "heart_rate_bpm": 90, "activity_level": 6,
                "vet_notes": "Dog is friendly and very obedient.",
                "aggression_level": 0, "anxiety_level": 1, "sociability": 5, "obedience": 5
            }
        },
        {
            "name": "Handling Negation (Not Aggressive)",
            "data": {
                "weight": 20, "heart_rate_bpm": 85, "activity_level": 5,
                "vet_notes": "Dog is not aggressive and very calm.",
                "aggression_level": 0, "anxiety_level": 0, "sociability": 4, "obedience": 4
            }
        },
        {
            "name": "Handling Intensifiers (Extremely Aggressive)",
            "data": {
                "weight": 25, "heart_rate_bpm": 130, "activity_level": 9,
                "vet_notes": "Dog is extremely aggressive and fearful.",
                "aggression_level": 5, "anxiety_level": 4, "sociability": 1, "obedience": 1
            }
        },
        {
            "name": "High Stress Physio",
            "data": {
                "weight": 12, "heart_rate_bpm": 150, "activity_level": 10,
                "vet_notes": "Dog is alert but skittish.",
                "aggression_level": 1, "anxiety_level": 3, "sociability": 3, "obedience": 2
            }
        }
    ]

    for case in test_cases:
        print(f"\n--- Testing: {case['name']} ---")
        result = calculate_temperament_score(case['data'])
        print(f"Final Score: {result['temperament_score']}")
        print(f"Details: {result['details']}")
