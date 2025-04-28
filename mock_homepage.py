import os
import time
import shutil
import moviepy.editor as mp
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_from_directory
import requests

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
<<<<<<< HEAD
AI_MODEL_API = "http://144.24.67.16"  # Mock AI model API
AI_MODEL_API_ENDPOINT = "http://144.24.67.16/process_video/"
=======
AI_MODEL_API = "http://127.0.0.1:5001"  # Mock AI model API
AI_MODEL_API_ENDPOINT = "http://127.0.0.1:5001/process_video"
>>>>>>> upstream/main

# Ensure necessary folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs("static/audio", exist_ok=True)


def trim_video(input_path, output_path, max_duration=60):
    """Trim video if it's longer than 1 minute."""
    clip = mp.VideoFileClip(input_path)
    if clip.duration > max_duration:
        clip = clip.subclip(0, max_duration)
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path


@app.route("/")
def homepage():
    """Render the homepage."""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_video():
    """Handle video upload and send to AI model."""
    if "video" not in request.files or "language" not in request.form:
        return jsonify({"error": "Missing video file or language"}), 400

    video_file = request.files["video"]
    language = request.form["language"]

    if video_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not video_file.filename.endswith(".mp4"):
        return jsonify({"error": "Invalid file format"}), 400

    # Save uploaded file
    video_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
    video_file.save(video_path)

    # Trim if necessary
    trimmed_path = os.path.join(PROCESSED_FOLDER, f"trimmed_{video_file.filename}")
    trimmed_video = trim_video(video_path, trimmed_path)

    # Send video to AI model
    with open(trimmed_video, "rb") as f:
        files = {"video": f}
        data = {"language": language}
        response = requests.post(AI_MODEL_API_ENDPOINT, files=files, data=data, stream=True)

    return Response(response.iter_content(chunk_size=1024), content_type=response.headers["Content-Type"])


@app.route("/results", methods=["GET"])
def stream_results():
    """Stream AI model's text and audio results."""
    def event_stream():
        response = requests.get(f"{AI_MODEL_API}/results", stream=True)
        for line in response.iter_lines():
            if line:
                yield f"data: {line.decode()}\n\n"

    return Response(stream_with_context(event_stream()), content_type="text/event-stream")


@app.route("/audio/<filename>")
def get_audio(filename):
    return send_from_directory("static/audio", filename)

if __name__ == "__main__":
    app.run(debug=True)
