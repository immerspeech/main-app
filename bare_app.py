
from flask import (
    Flask,
    request,
    render_template,
    send_from_directory,
    redirect,
    url_for,
    jsonify,
    session,
    send_file
)
import requests
import hashlib
import zipfile
import bcrypt
import os
import io

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

API_ENDPOINT = "http://144.24.67.16/process_video/"

# Supabase config
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_API_KEY = os.environ.get("SUPABASE_API_KEY")

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def get_user(username):
    """Fetch user by username from Supabase."""
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}"
    }
    params = {
        "select": "*",
        "username": f"eq.{username}"
    }
    response = requests.get(f"{SUPABASE_URL}/rest/v1/users", headers=headers, params=params)
    if response.status_code == 200 and response.json():
        return response.json()[0]
    return None

def update_terms_agreed(user_id):
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "terms_agreed": True
    }
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
        headers=headers,
        json=data
    )
    return response.status_code == 204  # Supabase returns 204 on successful update

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'username' in session: 
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        promocode = request.form['promocode']
        terms_agreed = request.form.get('terms') == 'on'

        if not terms_agreed:
            return render_template("signup.html", error="You must agree to the Terms of Service.")

        hashed_pw = hash_password(password)

        # Check promocode
        promo_check = requests.get(
            f"{SUPABASE_URL}/rest/v1/promocodes?promocode=eq.{promocode}",
            headers={
                "apikey": SUPABASE_API_KEY,
                "Authorization": f"Bearer {SUPABASE_API_KEY}"
            }
        )

        print(promo_check.json())
        print(promo_check)
        print(promocode)
        
        if promo_check.status_code != 200:
            return render_template("signup.html", error="Invalid promocode.")

        payload = {
            "username": username,
            "password": hashed_pw,
            "email": email,
            "terms_agreed": True,
            "promocode_used": promocode
        }

        print(payload)

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/users",
            headers={
                "apikey": SUPABASE_API_KEY,
                "Authorization": f"Bearer {SUPABASE_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        if response.status_code == 201:
            return redirect(url_for('login'))
        else:
            return render_template("signup.html", error="Signup failed. Try again.")

    return render_template("signup.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session: 
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user(username)

        if user and verify_password(password, user['password']):
            session['username'] = user['username']
            session['user_id'] = user['id']
            session['counter'] = user.get('counter', 0)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password.")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/", methods=["GET"])
def index():
    if 'username' in session:
        return render_template("bare_index.html")
    else:
        return redirect(url_for('login'))

@app.route("/upload", methods=["POST"])
def upload():
    print("UPLOAD INITIATED")

    file = request.files.get("file")
    target_language = request.form.get("target_language")
    user_prompt = request.form.get("user_prompt")

    if not file:
        return jsonify({"error": "No file provided"}), 400
    if not target_language:
        return jsonify({"error": "No target language provided"}), 400

    try:
        # Read file into buffer and reset cursor
        file_buffer = io.BytesIO()
        file.save(file_buffer)
        file_buffer.seek(0)  # VERY IMPORTANT

        print(file, target_language)

        # Send request to external API
        response = requests.post(
            API_ENDPOINT,
            files={"file": ("filename.mp4", file_buffer)},
            data={"target_language": target_language,
                  "user_prompt": user_prompt}
        )

        if response.status_code != 200:
            print("Processing failed:", response.text)
            return jsonify({"error": f"Processing failed: {response.text}"}), 500

        # Process ZIP response
        processed_zip = io.BytesIO(response.content)
        zip_id = str(hash(file.filename))

        extract_folder = f"/tmp/{zip_id}_extracted"
        dubbed_filename = "dubbed.wav"
        dubbed_path = os.path.join(extract_folder, dubbed_filename)
        zip_temp_path = f"/tmp/{zip_id}_processed.zip"

        os.makedirs(extract_folder, exist_ok=True)

        with zipfile.ZipFile(processed_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)

        with open(zip_temp_path, "wb") as f:
            f.write(response.content)

        return_data = {
            "message": "Processing complete",
            "dubbed_url": url_for("serve_dubbed_audio", zip_id=zip_id, _external=True),
            "zip_url": url_for("serve_zip_file", zip_id=zip_id, _external=True)
        }

        return jsonify(return_data)

    except Exception as e:
        print("Server error:", e)
        return jsonify({"error": "Internal server error"}), 500



@app.route("/serve_audio/<zip_id>")
def serve_dubbed_audio(zip_id):
    print("SERVING AUDIO for zip_id:", zip_id)
    dubbed_path = f"/tmp/{zip_id}_extracted/translated_audio.wav"

    if not os.path.exists(dubbed_path):
        print("File not found:", dubbed_path)
        return "File not found", 404

    return send_file(dubbed_path, mimetype="audio/wav", as_attachment=False)

@app.route("/download_zip/<zip_id>")
def serve_zip_file(zip_id):
    zip_temp_path = f"/tmp/{zip_id}_processed.zip"

    if not os.path.exists(zip_temp_path):
        print("ZIP file not found:", zip_temp_path)
        return "File not found", 404

    return send_file(zip_temp_path, as_attachment=True)


@app.route("/processed/<filename>")
def processed_file(filename):
    print("SERVING PROCESSED FILE")
    return send_from_directory(PROCESSED_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)