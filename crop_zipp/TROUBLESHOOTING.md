# 🔧 Troubleshooting Guide

## Common Issues and Solutions

---

## ❌ Error: "The session is unavailable because no secret key was set"

### ✅ Solution:

This error means Flask can't manage user sessions. Here's how to fix it:

### **Method 1: Restart the Application (Recommended)**

1. **Stop the current Flask app:**
   - Press `Ctrl + C` in the terminal where Flask is running

2. **Start it again:**
   ```bash
   python App.py
   ```

3. **Or use the restart script:**
   ```bash
   restart_app.bat
   ```

### **Method 2: Verify Secret Key**

1. **Open `App.py`**

2. **Check lines 17-24** - You should see:
   ```python
   app = Flask(__name__)
   
   # Secret key for session management
   app.secret_key = 'c3c6f5c2e813049deff8af859479d592a1b2c3d4e5f6g7h8'
   app.config['SESSION_TYPE'] = 'filesystem'
   ```

3. **If missing, add it** right after `app = Flask(__name__)`

4. **Save and restart** the app

---

## ❌ Error: "Connection refused" or "MongoDB not running"

### ✅ Solution:

1. **Check if MongoDB is running:**
   ```bash
   # Windows
   net start MongoDB
   
   # Or check services
   services.msc
   ```

2. **Start MongoDB if stopped:**
   - Open Services (Win + R, type `services.msc`)
   - Find "MongoDB"
   - Right-click → Start

3. **Or run setup again:**
   ```bash
   python setup_mongodb.py
   ```

---

## ❌ Error: "ModuleNotFoundError: No module named 'flask_login'"

### ✅ Solution:

Install missing dependencies:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install flask-login pymongo bcrypt
```

---

## ❌ Error: "Port 5000 is already in use"

### ✅ Solution:

### **Method 1: Kill the process**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F
```

### **Method 2: Use a different port**

Edit `App.py` at the bottom:
```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Changed from 5000 to 5001
```

Then access: http://127.0.0.1:5001

---

## ❌ Error: "Invalid username or password"

### ✅ Solution:

1. **Make sure you registered first:**
   - Go to: http://127.0.0.1:5000/register
   - Create an account

2. **Check username spelling:**
   - Usernames are case-sensitive
   - No extra spaces

3. **Try registering a new account:**
   - Use a different username
   - Use a different email

---

## ❌ Weather data not showing / "Demo Location"

### ✅ Solution:

1. **Get OpenWeatherMap API key:**
   - See `WEATHER_API_SETUP.md` for instructions
   - Sign up at: https://openweathermap.org/api

2. **Add API key to App.py:**
   - Find line ~195
   - Replace `'YOUR_API_KEY'` with your actual key

3. **Wait 10-15 minutes:**
   - New API keys need time to activate

4. **Restart the app:**
   ```bash
   python App.py
   ```

---

## ❌ Error: "Template not found"

### ✅ Solution:

1. **Check folder structure:**
   ```
   crop-advisor/
   ├── App.py
   ├── templates/
   │   ├── index.html
   │   ├── result.html
   │   ├── login.html
   │   ├── register.html
   │   ├── about.html
   │   ├── contact.html
   │   └── account.html
   ```

2. **Make sure all HTML files are in `templates/` folder**

3. **Restart the app**

---

## ❌ Models not loading / "FileNotFoundError"

### ✅ Solution:

1. **Check if model files exist:**
   - `crop_model.pkl`
   - `fertilizer_model.pkl`
   - `scaler.pkl`
   - `soil_encoder.pkl`
   - `crop_encoder.pkl`
   - `fertilizer_encoder.pkl`

2. **If missing, train the models:**
   ```bash
   python train_model.py
   python train_fertilizer_model.py
   ```

3. **Make sure files are in the same directory as App.py**

---

## ❌ Page not loading / Blank screen

### ✅ Solution:

1. **Check browser console:**
   - Press F12
   - Look for errors in Console tab

2. **Clear browser cache:**
   - Press Ctrl + Shift + Delete
   - Clear cached images and files

3. **Try a different browser:**
   - Chrome, Firefox, Edge

4. **Check Flask terminal for errors:**
   - Look at the terminal where Flask is running
   - Check for error messages

---

## ❌ "Access Denied" or "Login Required"

### ✅ Solution:

1. **You need to login first:**
   - Go to: http://127.0.0.1:5000/login
   - Or register: http://127.0.0.1:5000/register

2. **Session expired:**
   - Login again
   - Check if cookies are enabled

3. **Clear cookies:**
   - Browser settings → Clear cookies
   - Login again

---

## ❌ History not saving

### ✅ Solution:

1. **Check MongoDB connection:**
   ```bash
   python setup_mongodb.py
   ```

2. **Make sure you're logged in:**
   - History is user-specific
   - Login required

3. **Check MongoDB is running:**
   - See MongoDB troubleshooting above

---

## ❌ Mobile menu not working

### ✅ Solution:

1. **Clear browser cache**

2. **Check JavaScript errors:**
   - Press F12 on mobile browser
   - Look for errors

3. **Try desktop view:**
   - Menu should work on desktop

---

## 🔄 General Troubleshooting Steps

### When something doesn't work:

1. **Restart the Flask app:**
   ```bash
   Ctrl + C
   python App.py
   ```

2. **Clear browser cache:**
   - Ctrl + Shift + Delete

3. **Check terminal for errors:**
   - Look at Flask output
   - Read error messages

4. **Verify all files exist:**
   - Check file structure
   - Make sure nothing is missing

5. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Check MongoDB is running:**
   ```bash
   python setup_mongodb.py
   ```

---

## 📞 Still Having Issues?

### Check these files for more help:
- `AUTH_SETUP.md` - Authentication issues
- `WEATHER_API_SETUP.md` - Weather data issues
- `FEATURES_SUMMARY.md` - Feature documentation
- `README` files - General information

### Common Fixes Checklist:
- [ ] Restart Flask app
- [ ] Clear browser cache
- [ ] Check MongoDB is running
- [ ] Verify all files exist
- [ ] Check for typos in code
- [ ] Look at terminal errors
- [ ] Try different browser
- [ ] Reinstall dependencies

---

## 💡 Pro Tips

1. **Always check the terminal** where Flask is running for error messages

2. **Use browser developer tools** (F12) to see JavaScript errors

3. **Keep MongoDB running** in the background

4. **Restart after making changes** to Python files

5. **Clear cache** after updating HTML/CSS

6. **Check file paths** - make sure files are in correct folders

7. **Read error messages carefully** - they usually tell you what's wrong!

---

## ✅ Quick Fix Commands

```bash
# Restart Flask
Ctrl + C
python App.py

# Setup MongoDB
python setup_mongodb.py

# Reinstall dependencies
pip install -r requirements.txt

# Train models
python train_model.py
python train_fertilizer_model.py

# Check if MongoDB is running
net start MongoDB
```

---

**Most issues are fixed by simply restarting the Flask app!** 🔄
