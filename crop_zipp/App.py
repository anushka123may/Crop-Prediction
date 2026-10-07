"""
Crop and Fertilizer Advisor - Flask Web Application

Serves the web UI; loads ML models and artifacts. Prediction flow:
  User Input -> Scale (scaler) -> Crop Model -> Decode (crop_encoder) -> Crop name
  -> Map to fertilizer Crop Type -> Encode soil/crop -> Fertilizer Model -> Decode -> Fertilizer name

Required .pkl (run train_model.py and train_fertilizer_model.py first):
  crop_model.pkl, scaler.pkl, crop_encoder.pkl, accuracy.pkl
  fertilizer_model.pkl, soil_encoder.pkl, fertilizer_crop_encoder.pkl, fertilizer_encoder.pkl

Run: python App.py
"""

import os
import json
from datetime import datetime
from bson.objectid import ObjectId

import numpy as np
import joblib
import requests
import bcrypt
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from pymongo import MongoClient

# =============================================================================
# FLASK APP & CONFIG
# =============================================================================

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

# =============================================================================
# MONGODB (optional – fallback to in-memory if MongoDB not running)
# =============================================================================

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGODB_AVAILABLE = False
client = None
db = None
users_collection = None
history_collection = None

# In-memory fallback when MongoDB is not available
IN_MEMORY_USERS = {}
IN_MEMORY_HISTORY = []
_IN_MEMORY_HISTORY_ID = 0

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    db = client["crop_advisor_db"]
    users_collection = db["users"]
    history_collection = db["recommendations"]
    MONGODB_AVAILABLE = True
    print("MongoDB connected.")
except Exception as e:
    print(f"MongoDB not available ({e}). Using in-memory storage (demo login: admin / admin).")
    # Demo user for running without MongoDB: username=admin, password=admin
    _demo_password = bcrypt.hashpw(b"admin", bcrypt.gensalt())
    IN_MEMORY_USERS = {
        "1": {"_id": "1", "id": "1", "username": "admin", "email": "admin@local", "password": _demo_password},
    }

# =============================================================================
# FLASK-LOGIN
# =============================================================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get("_id", user_data.get("id", "")))
        self.username = user_data.get("username", "")
        self.email = user_data.get("email", "")


@login_manager.user_loader
def load_user(user_id):
    if MONGODB_AVAILABLE:
        try:
            user_data = users_collection.find_one({"_id": ObjectId(user_id)})
            return User(user_data) if user_data else None
        except Exception:
            return None
    return User(IN_MEMORY_USERS[user_id]) if user_id in IN_MEMORY_USERS else None


# =============================================================================
# LOAD ML MODELS AND ARTIFACTS (with error handling)
# =============================================================================
# Crop: Random Forest. Input (7): N, P, K, temperature, humidity, ph, rainfall.
# Fertilizer: Random Forest. Input (8): temp, hum, moisture, soil_enc, crop_type_enc, N, K, P.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_pkl(name):
    path = os.path.join(BASE_DIR, name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing {name}. Run train_model.py and train_fertilizer_model.py first.")
    return joblib.load(path)


try:
    crop_model = _load_pkl("crop_model.pkl")
    scaler = _load_pkl("scaler.pkl")
    crop_encoder = _load_pkl("crop_encoder.pkl")  # dict: int -> crop name (decode label)
    accuracy_value = _load_pkl("accuracy.pkl")
    fertilizer_model = _load_pkl("fertilizer_model.pkl")
    soil_encoder = _load_pkl("soil_encoder.pkl")
    fertilizer_crop_encoder = _load_pkl("fertilizer_crop_encoder.pkl")
    fertilizer_encoder = _load_pkl("fertilizer_encoder.pkl")
except FileNotFoundError as e:
    print(str(e))
    raise
except Exception as e:
    print(f"Error loading .pkl files: {e}")
    raise

# Map crop model output (e.g. 'rice') to fertilizer dataset Crop Type (e.g. 'Paddy')
# Used to build fertilizer feature vector. Fallback: 'Millets' if unknown.
CROP_TO_FERTILIZER_CROP_TYPE = {
    "rice": "Paddy",
    "maize": "Maize",
    "cotton": "Cotton",
    "chickpea": "Pulses",
    "kidneybeans": "Pulses",
    "pigeonpeas": "Pulses",
    "mothbeans": "Pulses",
    "mungbean": "Pulses",
    "blackgram": "Pulses",
    "lentil": "Pulses",
    "pomegranate": "Oil seeds",
    "banana": "Millets",
    "mango": "Oil seeds",
    "grapes": "Oil seeds",
    "watermelon": "Millets",
    "muskmelon": "Millets",
    "apple": "Oil seeds",
    "orange": "Oil seeds",
    "papaya": "Millets",
    "coconut": "Oil seeds",
    "jute": "Millets",
    "coffee": "Oil seeds",
}

# =============================================================================
# SOIL DATA (for chatbot / area-based soil)
# =============================================================================

def _load_soil_data():
    path = os.path.join(BASE_DIR, "soil_data.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"Default": {"Nitrogen": 45, "Phosphorus": 42, "Potassium": 40, "pH": 6.5}}


SOIL_DATA = _load_soil_data()
OPENWEATHER_API_KEY = os.environ.get(
    "OPENWEATHER_API_KEY", "c3c6f5c2e813049deff8af859479d592"
)


# =============================================================================
# ROUTES - AUTH
# =============================================================================

@app.route("/")
def index():
    if current_user.is_authenticated:
        return render_template("index.html", user=current_user)
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user_data = None
        if MONGODB_AVAILABLE:
            user_data = users_collection.find_one({"username": username})
        else:
            for u in IN_MEMORY_USERS.values():
                if u.get("username") == username:
                    user_data = u
                    break
        if user_data and bcrypt.checkpw(
            password.encode("utf-8"), user_data["password"]
        ):
            login_user(User(user_data))
            return redirect(url_for("index"))
        flash("Invalid username or password", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        if MONGODB_AVAILABLE:
            if users_collection.find_one(
                {"$or": [{"username": username}, {"email": email}]}
            ):
                flash("Username or email already exists.", "error")
                return render_template("register.html")
            result = users_collection.insert_one({
                "username": username,
                "email": email,
                "password": hashed,
                "created_at": datetime.now(),
            })
            user_data = users_collection.find_one({"_id": result.inserted_id})
            login_user(User(user_data))
            flash("Registration successful!", "success")
            return redirect(url_for("index"))
        else:
            for u in IN_MEMORY_USERS.values():
                if u.get("username") == username or u.get("email") == email:
                    flash("Username or email already exists.", "error")
                    return render_template("register.html")
            new_id = str(len(IN_MEMORY_USERS) + 1)
            IN_MEMORY_USERS[new_id] = {
                "_id": new_id,
                "id": new_id,
                "username": username,
                "email": email,
                "password": hashed,
            }
            login_user(User(IN_MEMORY_USERS[new_id]))
            flash("Registration successful!", "success")
            return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/about")
@login_required
def about():
    return render_template("about.html", user=current_user)


@app.route("/contact")
@login_required
def contact():
    return render_template("contact.html", user=current_user)


@app.route("/account")
@login_required
def account():
    if MONGODB_AVAILABLE:
        total = history_collection.count_documents({"user_id": current_user.id})
        user_data = users_collection.find_one({"_id": ObjectId(current_user.id)})
    else:
        total = len([h for h in IN_MEMORY_HISTORY if h.get("user_id") == current_user.id])
        user_data = IN_MEMORY_USERS.get(current_user.id, {"username": current_user.username, "email": getattr(current_user, "email", "")})
    return render_template(
        "account.html",
        user=current_user,
        total_recommendations=total,
        user_data=user_data,
    )


# =============================================================================
# ROUTES - WEATHER & SOIL (for UI and chatbot)
# =============================================================================

@app.route("/get_weather", methods=["POST"])
def get_weather():
    """Returns temperature (°C), humidity (%), rainfall (mm) by city or lat/lon."""
    try:
        data = request.get_json() or {}
        city = data.get("city", "").strip()
        lat, lon = data.get("lat"), data.get("lon")
        if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "YOUR_API_KEY":
            return jsonify({"error": "OpenWeatherMap API key not set"}), 400
        if city:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        elif lat is not None and lon is not None:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        else:
            return jsonify({"error": "Provide city or lat/lon"}), 400
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        d = resp.json()
        temp = round(float(d["main"]["temp"]), 1)
        humidity = round(float(d["main"]["humidity"]), 1)
        rain_1h = d.get("rain", {}).get("1h", 0) or 0
        rain_3h = d.get("rain", {}).get("3h", 0) or 0
        rainfall = (
            round(float(rain_1h or rain_3h) * 24, 1) if (rain_1h or rain_3h) else 0.0
        )
        return jsonify({
            "temperature": temp,
            "humidity": humidity,
            "rainfall": rainfall,
            "location": d.get("name", "Your Location"),
            "description": (d.get("weather") or [{}])[0].get("description", "").title(),
            "wind_speed": round(float((d.get("wind") or {}).get("speed", 0)), 1),
            "pressure": (d.get("main") or {}).get("pressure", 0),
        })
    except requests.RequestException as e:
        return jsonify({"error": f"Weather API failed: {str(e)}"}), 500
    except (KeyError, TypeError) as e:
        return jsonify({"error": f"Invalid response: {str(e)}"}), 500


@app.route("/get_location_ip", methods=["GET"])
def get_location_ip():
    """Approximate lat/lon from client IP when browser geolocation is denied."""
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()
        if ip in ("127.0.0.1", "::1", "localhost", ""):
            url = "http://ip-api.com/json/?fields=status,lat,lon,city,message"
        else:
            url = f"http://ip-api.com/json/{ip}?fields=status,lat,lon,city,message"
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "success":
            return jsonify({"error": data.get("message", "Could not detect location")}), 400
        return jsonify({
            "lat": data["lat"],
            "lon": data["lon"],
            "city": data.get("city", ""),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_soil")
def get_soil():
    """Returns average N, P, K, pH for a state/area from soil_data.json."""
    area = (
        request.args.get("state")
        or request.args.get("area")
        or request.args.get("district")
        or ""
    ).strip()
    if not area:
        return jsonify(SOIL_DATA.get("Default", SOIL_DATA["Default"]))
    for key in SOIL_DATA:
        if key.lower() == area.lower():
            return jsonify(SOIL_DATA[key])
    return jsonify(SOIL_DATA.get("Default", SOIL_DATA["Default"]))


# =============================================================================
# ROUTES - CHATBOT CROP PREDICTION (no fertilizer; uses weather if provided)
# =============================================================================

@app.route("/chat_predict", methods=["POST"])
@login_required
def chat_predict():
    """Predict crop from N, P, K, ph and optional city/lat/lon for weather."""
    try:
        data = request.get_json() or {}
        N = int(data.get("N", 0))
        P = int(data.get("P", 0))
        K = int(data.get("K", 0))
        ph = float(data.get("ph", 6.5))
        city = (data.get("city") or "").strip()
        lat, lon = data.get("lat"), data.get("lon")

        temp, hum, rain = 25.0, 65.0, 100.0
        if (city or (lat is not None and lon is not None)) and OPENWEATHER_API_KEY and OPENWEATHER_API_KEY != "YOUR_API_KEY":
            try:
                if city:
                    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
                else:
                    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                d = r.json()
                temp = round(float(d["main"]["temp"]), 1)
                hum = round(float(d["main"]["humidity"]), 1)
                r1 = (d.get("rain") or {}).get("1h", 0) or 0
                r3 = (d.get("rain") or {}).get("3h", 0) or 0
                rain = round(float(r1 or r3) * 24, 1) if (r1 or r3) else 0.0
            except Exception:
                pass

        features = np.array([[N, P, K, temp, hum, ph, rain]])
        transformed = scaler.transform(features)
        pred = crop_model.predict(transformed)
        crop_name = crop_encoder.get(int(pred[0]), "unknown")

        entry = {
            "user_id": current_user.id,
            "timestamp": datetime.now(),
            "crop": crop_name,
            "fertilizer": "N/A",
            "inputs": {
                "N": N, "P": P, "K": K,
                "temperature": temp, "humidity": hum, "ph": ph,
                "rainfall": rain, "soil_type": "N/A",
            },
        }
        if MONGODB_AVAILABLE:
            history_collection.insert_one(entry)
        else:
            global _IN_MEMORY_HISTORY_ID, IN_MEMORY_HISTORY
            _IN_MEMORY_HISTORY_ID += 1
            entry["_id"] = str(_IN_MEMORY_HISTORY_ID)
            IN_MEMORY_HISTORY.append(entry)
        return jsonify({
            "crop": crop_name,
            "temperature": temp,
            "humidity": hum,
            "rainfall": rain,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# ROUTES - HISTORY
# =============================================================================

@app.route("/get_history", methods=["GET"])
@login_required
def get_history():
    try:
        if MONGODB_AVAILABLE:
            items = list(
                history_collection.find({"user_id": current_user.id})
                .sort("timestamp", -1)
                .limit(20)
            )
            for item in items:
                item["id"] = str(item["_id"])
                del item["_id"]
                item.pop("user_id", None)
        else:
            items = [h.copy() for h in IN_MEMORY_HISTORY if h.get("user_id") == current_user.id]
            items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            items = items[:20]
            for item in items:
                item["id"] = item.get("_id", "")
                item.pop("user_id", None)
        for item in items:
            if "inputs" not in item:
                item["inputs"] = {
                    "N": "-", "P": "-", "K": "-",
                    "temperature": "-", "humidity": "-", "soil_type": "-",
                }
            if isinstance(item.get("timestamp"), datetime):
                item["timestamp"] = item["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete_history/<history_id>", methods=["DELETE"])
@login_required
def delete_history(history_id):
    try:
        if MONGODB_AVAILABLE:
            history_collection.delete_one(
                {"_id": ObjectId(history_id), "user_id": current_user.id}
            )
        else:
            global IN_MEMORY_HISTORY
            IN_MEMORY_HISTORY = [h for h in IN_MEMORY_HISTORY if not (h.get("user_id") == current_user.id and str(h.get("_id")) == str(history_id))]
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/clear_history", methods=["DELETE"])
@login_required
def clear_history():
    try:
        if MONGODB_AVAILABLE:
            history_collection.delete_many({"user_id": current_user.id})
        else:
            global IN_MEMORY_HISTORY
            IN_MEMORY_HISTORY = [h for h in IN_MEMORY_HISTORY if h.get("user_id") != current_user.id]
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# ROUTES - MAIN CROP + FERTILIZER PREDICTION
# =============================================================================
# Flow: Form input -> Scale crop features -> Crop model -> Decode to crop name
#       -> Map crop name to fertilizer Crop Type -> Encode soil + crop type
#       -> Fertilizer model -> Decode to fertilizer name -> Save history -> Result page

@app.route("/crop", methods=["POST"])
@login_required
def crop():
    try:
        N = int(request.form.get("N", 0))
        P = int(request.form.get("P", 0))
        K = int(request.form.get("K", 0))
        temp = float(request.form.get("temp", 0))
        hum = float(request.form.get("hum", 0))
        ph = float(request.form.get("ph", 0))
        rain = float(request.form.get("rain", 0))
        moisture = float(request.form.get("moisture", 0))
        soil_type = request.form.get("soil_type", "Loamy")
    except (ValueError, TypeError) as e:
        flash(f"Invalid form input: {e}")
        return redirect(url_for("index"))

    # --- Crop prediction: User input -> Scale -> Model -> Decode label -> Crop name
    try:
        crop_features = np.array([[N, P, K, temp, hum, ph, rain]])
        crop_scaled = scaler.transform(crop_features)
        crop_pred = crop_model.predict(crop_scaled)
        crop_name = crop_encoder.get(int(crop_pred[0]), "unknown")
    except Exception as e:
        flash(f"Crop prediction failed: {e}")
        return redirect(url_for("index"))

    # --- Fertilizer prediction: map crop to Crop Type -> Encode -> Model -> Decode
    fertilizer_name = "Not Available"
    try:
        fert_crop_type = CROP_TO_FERTILIZER_CROP_TYPE.get(
            crop_name.lower(), "Millets"
        )
        if fert_crop_type not in fertilizer_crop_encoder.classes_:
            fert_crop_type = "Millets"
        soil_enc = soil_encoder.transform([soil_type])[0]
        crop_enc = fertilizer_crop_encoder.transform([fert_crop_type])[0]
        fert_features = np.array(
            [[temp, hum, moisture, soil_enc, crop_enc, N, K, P]]
        )
        fert_pred = fertilizer_model.predict(fert_features)
        fertilizer_name = fertilizer_encoder.inverse_transform(fert_pred)[0]
    except Exception:
        fertilizer_name = "Unable to determine"

    try:
        entry = {
            "user_id": current_user.id,
            "timestamp": datetime.now(),
            "crop": crop_name,
            "fertilizer": fertilizer_name,
            "inputs": {
                "N": N, "P": P, "K": K,
                "temperature": temp, "humidity": hum, "ph": ph,
                "rainfall": rain, "moisture": moisture, "soil_type": soil_type,
            },
        }
        if MONGODB_AVAILABLE:
            history_collection.insert_one(entry)
        else:
            global _IN_MEMORY_HISTORY_ID, IN_MEMORY_HISTORY
            _IN_MEMORY_HISTORY_ID += 1
            entry["_id"] = str(_IN_MEMORY_HISTORY_ID)
            IN_MEMORY_HISTORY.append(entry)
    except Exception:
        pass

    return render_template(
        "result.html",
        crop=crop_name,
        fertilizer=fertilizer_name,
        accuracy=round(accuracy_value, 2),
        soil_type=soil_type,
        n_value=N,
        p_value=P,
        k_value=K,
        temp=temp,
        hum=hum,
        rain=rain,
        moisture=moisture,
    )


# =============================================================================
# COMMON URL ALIASES & 404 HANDLER
# =============================================================================

@app.route("/index")
@app.route("/home")
def home_redirect():
    return redirect(url_for("index"))


@app.errorhandler(404)
def page_not_found(e):
    if current_user.is_authenticated:
        flash("Page not found.", "error")
        return redirect(url_for("index"))
    return redirect(url_for("login"))


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
