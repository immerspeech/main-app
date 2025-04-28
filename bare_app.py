
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
import hashlib
import requests
import zipfile
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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = hash_password(password)

        user = get_user(username)
        print(user)

        if user and user['password'] == password:
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

    file = request.files["file"]
    if not file:
        return jsonify({"error": "No file provided"}), 400

    file_buffer = io.BytesIO(file.read())

    response = requests.post(API_ENDPOINT, files={"file": ("filename.mp4", file_buffer)})

    if response.status_code != 200:
        print(response.text)
        return jsonify({"error": f"Processing failed: {response.text}"}), 500

    # Process response ZIP
    processed_zip = io.BytesIO(response.content)

    zip_id = str(hash(file.filename))  # Unique identifier

    # Setup folders and paths
    extract_folder = f"/tmp/{zip_id}_extracted"
    dubbed_filename = "dubbed.wav"
    dubbed_path = os.path.join(extract_folder, dubbed_filename)
    zip_temp_path = f"/tmp/{zip_id}_processed.zip"

    os.makedirs(extract_folder, exist_ok=True)

    with zipfile.ZipFile(processed_zip, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)

    # Save original zip
    with open(zip_temp_path, "wb") as f:
        f.write(response.content)

    print("ZIP TEMP PATH:", zip_temp_path)
    print("DUBBED PATH:", dubbed_path)

    # Return JSON response with only IDs (no full /tmp path leaks)
    return_data = {
        "message": "Processing complete",
        "dubbed_url": url_for("serve_dubbed_audio", zip_id=zip_id, _external=True),
        "zip_url": url_for("serve_zip_file", zip_id=zip_id, _external=True),
    }

    print("RETURNING JSON:", return_data)

    return jsonify(return_data)


@app.route("/serve_audio/<zip_id>")
def serve_dubbed_audio(zip_id):
    print("SERVING AUDIO for zip_id:", zip_id)
    dubbed_path = f"/tmp/{zip_id}_extracted/dubbed.wav"

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