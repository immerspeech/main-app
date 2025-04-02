import os
import time
import json
import shutil
import moviepy.editor as mp
from flask import Flask, request, jsonify, Response, stream_with_context

app = Flask(__name__)

UPLOAD_FOLDER = "ai_uploads"
OUTPUT_FOLDER = "static/audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def extract_audio(video_path, output_audio_path):
    """Extract audio from a video and save it as a .wav file."""
    video = mp.VideoFileClip(video_path)
    video.audio.write_audiofile(output_audio_path, codec="pcm_s16le")
    return output_audio_path


@app.route("/process_video", methods=["POST"])
def process_video():
    """Simulate AI model processing: receive video, extract audio, and stream results."""
    if "video" not in request.files or "language" not in request.form:
        return jsonify({"error": "Missing video file or language"}), 400

    video_file = request.files["video"]
    language = request.form["language"]
    
    if video_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not video_file.filename.endswith(".mp4"):
        return jsonify({"error": "Invalid file format"}), 400

    # Save the uploaded video
    video_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
    video_file.save(video_path)

    # Extract audio from video
    audio_filename = f"{os.path.splitext(video_file.filename)[0]}.wav"
    audio_path = os.path.join(OUTPUT_FOLDER, audio_filename)
    extract_audio(video_path, audio_path)

    # Store the processed audio path for later retrieval
    shutil.move(audio_path, os.path.join(OUTPUT_FOLDER, audio_filename))

    return jsonify({"message": "Processing started", "audio_file": audio_filename})


@app.route("/results", methods=["GET"])
def stream_results():
    """Simulate AI response streaming text and then returning audio."""
    def generate():
        # Send English text after 5 seconds
        time.sleep(5)
        yield f"data: {json.dumps({'type': 'text_en', 'content': 'This is a sample English output.'})}\n\n"

        # Send Korean text after 5 more seconds
        time.sleep(5)
        yield f"data: {json.dumps({'type': 'text_kr', 'content': '이것은 샘플 한국어 출력입니다.'})}\n\n"

        # Retrieve processed audio file
        audio_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith(".wav")]
        for audio_file in audio_files:
            yield f"data: {json.dumps({'type': 'audio', 'url': f'/audio/{audio_file}'})}\n\n"

    return Response(stream_with_context(generate()), content_type="text/event-stream")


@app.route("/audio/<filename>", methods=["GET"])
def serve_audio(filename):
    """Serve generated audio files."""
    audio_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(audio_path):
        return jsonify({"error": "File not found"}), 404

    return Response(open(audio_path, "rb"), mimetype="audio/wav")


if __name__ == "__main__":
    app.run(port=5001, debug=True)
