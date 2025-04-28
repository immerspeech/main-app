
from flask import (
    Flask,
    request,
    render_template,
    send_from_directory,
    redirect,
    url_for,
    jsonify,
    session
)
import hashlib
import requests
import zipfile
import os


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
            return redirect(url_for('dashboard'))
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

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    # Send file to remote API
    with open(filepath, "rb") as f:
        response = requests.post(API_ENDPOINT, files={"file": f})

    if response.status_code != 200:
        print(response.text)
        return jsonify({"error": f"Processing failed: {response.text}"}), 500

    # Save processed result
    processed_filename = "processed_" + file.filename[:-4] + ".zip"
    processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
    with open(processed_path, "wb") as out_file:
        out_file.write(response.content)
    
    with zipfile.ZipFile(processed_path, 'r') as zip_ref:
        zip_ref.extractall(processed_path[:-4])
    dubbed_filename = os.path.join(processed_path[:-4], 'dubbed.wav')
    concat_filename = os.path.join(processed_path[:-4], 'concat.wav')


    print("UPLOAD COMPLETED")
    print(processed_filename)

    # Return JSON with the processed file URL
    return jsonify({
        "processed_url": url_for("processed_file", filename=processed_filename, _external=True),
        "message": "Processing complete"
    })

@app.route("/processed/<filename>")
def processed_file(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)