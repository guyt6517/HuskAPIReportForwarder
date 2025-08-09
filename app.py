import os
import requests
from flask import Flask, request, jsonify, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    raise RuntimeError("Environment variable DISCORD_WEBHOOK_URL not set")

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv', 'mpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/report", methods=["POST"])
def report():
    # Check required text fields
    reported_user_id = request.form.get("reportedUserId", "").strip()
    description = request.form.get("description", "").strip()

    if not reported_user_id:
        return jsonify({"error": "'reportedUserId' is required"}), 400
    if not description:
        return jsonify({"error": "'description' is required"}), 400

    # Check file upload
    if 'videoEvidence' not in request.files:
        return jsonify({"error": "'videoEvidence' file is required"}), 400

    video_file = request.files['videoEvidence']
    if video_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(video_file.filename):
        return jsonify({"error": f"File extension not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    # Secure filename (though we won't save it permanently)
    filename = secure_filename(video_file.filename)

    # Prepare payload for Discord webhook
    content = (
        f"**New Report**\n"
        f"User ID: {reported_user_id}\n"
        f"Description: {description}"
    )

    # Discord expects a multipart/form-data POST for file uploads
    files = {
        "file": (filename, video_file.stream, video_file.mimetype)
    }
    data = {
        "content": content
    }

    # Send POST request to Discord webhook
    resp = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files)

    if resp.status_code in (200, 204):
        return jsonify({"message": "Report sent successfully"}), 200
    else:
        return jsonify({"error": "Failed to send to Discord webhook"}), 500


if __name__ == "__main__":
    app.run(debug=True)
