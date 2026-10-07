"""
Crop Recommendation Model Training (Random Forest)

Loads dataset/Crop_recommendation.csv, preprocesses, trains RandomForestClassifier
with 80-20 train-test split. Computes Accuracy, Confusion Matrix, Classification Report,
F1 Score. Saves: crop_model.pkl, crop_encoder.pkl, scaler.pkl, accuracy.pkl

Run from project root: python train_model.py
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    classification_report,
    f1_score,
)

# =============================================================================
# 1. LOAD DATASET
# =============================================================================
# Features: N, P, K, temperature, humidity, ph, rainfall (7 columns)
# Target: label (crop name)

crop = pd.read_csv("dataset/Crop_recommendation.csv")

# Map crop names to integer labels (required for sklearn)
crop_dict = {
    "rice": 0,
    "maize": 1,
    "chickpea": 2,
    "kidneybeans": 3,
    "pigeonpeas": 4,
    "mothbeans": 5,
    "mungbean": 6,
    "blackgram": 7,
    "lentil": 8,
    "pomegranate": 9,
    "banana": 10,
    "mango": 11,
    "grapes": 12,
    "watermelon": 13,
    "muskmelon": 14,
    "apple": 15,
    "orange": 16,
    "papaya": 17,
    "coconut": 18,
    "cotton": 19,
    "jute": 20,
    "coffee": 21,
}

# Reverse mapping: integer -> crop name (saved as crop_encoder.pkl for App.py to decode)
crop_encoder = {v: k for k, v in crop_dict.items()}

crop["crop_no"] = crop["label"].map(crop_dict)
X = crop.drop(["label", "crop_no"], axis=1)
y = crop["crop_no"]

# =============================================================================
# 2. TRAIN-TEST SPLIT (80-20)
# =============================================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# =============================================================================
# 3. PREPROCESSING (StandardScaler - same used at prediction time in App.py)
# =============================================================================

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# =============================================================================
# 4. MODEL TRAINING (Random Forest)
# =============================================================================

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)
y_pred = model.predict(X_test_scaled)

# =============================================================================
# 5. EVALUATION: Accuracy, Confusion Matrix, Classification Report, F1 Score
# =============================================================================

accuracy = accuracy_score(y_test, y_pred) * 100
f1 = f1_score(y_test, y_pred, average="weighted")
cm = confusion_matrix(y_test, y_pred)

print("=" * 50)
print("Crop Model (Random Forest) - Evaluation")
print("=" * 50)
print(f"Accuracy: {accuracy:.2f}%")
print(f"F1 Score (weighted): {f1:.4f}")
print()
print("Confusion Matrix:")
print(cm)
print()
print("Classification Report:")
print(classification_report(y_test, y_pred, zero_division=0))
print("=" * 50)

# =============================================================================
# 6. SAVE ARTIFACTS (loaded by App.py for prediction)
# =============================================================================
# - crop_model.pkl: Random Forest classifier
# - crop_encoder.pkl: dict mapping predicted class index -> crop name (decode label)
# - scaler.pkl: StandardScaler fitted on training data
# - accuracy.pkl: float accuracy for display on result page

joblib.dump(model, "crop_model.pkl")
joblib.dump(crop_encoder, "crop_encoder.pkl")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(accuracy, "accuracy.pkl")

print("Saved: crop_model.pkl, crop_encoder.pkl, scaler.pkl, accuracy.pkl")
print("Crop model training complete.")
