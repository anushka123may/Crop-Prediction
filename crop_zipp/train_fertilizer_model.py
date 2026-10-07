"""
Fertilizer Recommendation Model Training (Random Forest)

Loads dataset/Fertilizer Prediction.csv, encodes categorical variables (Soil Type, Crop Type),
trains RandomForestClassifier. Saves: fertilizer_model.pkl, fertilizer_encoder.pkl,
soil_encoder.pkl, fertilizer_crop_encoder.pkl (required by App.py to build feature vector).

Run from project root: python train_fertilizer_model.py
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

# =============================================================================
# 1. LOAD DATASET
# =============================================================================

df = pd.read_csv("dataset/Fertilizer Prediction.csv")
df.columns = df.columns.str.strip()

# =============================================================================
# 2. ENCODE CATEGORICAL VARIABLES
# =============================================================================

le_soil = LabelEncoder()
le_crop = LabelEncoder()
le_fertilizer = LabelEncoder()

df["Soil Type Encoded"] = le_soil.fit_transform(df["Soil Type"])
df["Crop Type Encoded"] = le_crop.fit_transform(df["Crop Type"])
df["Fertilizer Encoded"] = le_fertilizer.fit_transform(df["Fertilizer Name"])

# =============================================================================
# 3. FEATURES AND TARGET
# =============================================================================
# Feature order: Temperature, Humidity, Moisture, Soil Encoded, Crop Type Encoded, N, K, P

X = df[
    [
        "Temparature",
        "Humidity",
        "Moisture",
        "Soil Type Encoded",
        "Crop Type Encoded",
        "Nitrogen",
        "Potassium",
        "Phosphorous",
    ]
]
y = df["Fertilizer Encoded"]

# =============================================================================
# 4. TRAIN-TEST SPLIT (80-20)
# =============================================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# =============================================================================
# 5. MODEL TRAINING (Random Forest)
# =============================================================================

rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# =============================================================================
# 6. EVALUATION
# =============================================================================

acc = rf_model.score(X_test, y_test) * 100
print("=" * 50)
print("Fertilizer Model (Random Forest)")
print("=" * 50)
print(f"Accuracy: {acc:.2f}%")
print(f"Soil Types: {list(le_soil.classes_)}")
print(f"Crop Types: {list(le_crop.classes_)}")
print(f"Fertilizers: {list(le_fertilizer.classes_)}")
print("=" * 50)

# =============================================================================
# 7. SAVE ARTIFACTS
# =============================================================================
# fertilizer_model.pkl, fertilizer_encoder.pkl (and encoders needed for App.py input)

joblib.dump(rf_model, "fertilizer_model.pkl")
joblib.dump(le_fertilizer, "fertilizer_encoder.pkl")
joblib.dump(le_soil, "soil_encoder.pkl")
joblib.dump(le_crop, "fertilizer_crop_encoder.pkl")

print("Saved: fertilizer_model.pkl, fertilizer_encoder.pkl, soil_encoder.pkl, fertilizer_crop_encoder.pkl")
print("Fertilizer model training complete.")
