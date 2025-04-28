
from flask import (
    Flask,
    request,
    render_template,
    send_from_directory,
    redirect,
    url_for,
    jsonify
)
import requests
import os
import moviepy.editor as mp
from pydub import AudioSegment
import zipfile

def extract_audio(video_path, output_audio_path):
    """Extract audio from a video and save it as a .wav file."""
    # pydub can sometimes directly open videos depending on format
    audio = AudioSegment.from_file(video_path)
    audio.export(output_audio_path, format="wav")
    return output_audio_path


app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

API_ENDPOINT = "http://144.24.67.16/process_video/"


@app.route("/", methods=["GET"])
def index():
    return render_template("bare_index.html")


def extract_audio(video_path, output_audio_path):
    """Extract audio from a video and save it as a .wav file."""
    video = mp.VideoFileClip(video_path)
    video.audio.write_audiofile(output_audio_path, codec="pcm_s16le")
    return output_audio_path


@app.route("/upload", methods=["POST"])
def upload():
    print("UPLOAD INITIATED")
    file = request.files["file"]
    if not file:
        return jsonify({"error": "No file provided"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    if filepath.endswith(".mp4"):
        filepath = extract_audio(filepath, filepath.replace(".mp4", ".wav"))

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