from flask import Flask, request, send_file, jsonify
from pytube import YouTube
import os
import instaloader
import re
import tempfile

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# -------- YouTube Download --------
@app.route("/download/youtube", methods=["POST"])
def download_youtube():
    data = request.json
    url = data.get("url")
    download_type = data.get("type", "video")
    quality = data.get("quality", "1080p")

    if not url:
        return jsonify({"error": "URL missing"}), 400

    try:
        yt = YouTube(url)
        if download_type == "video":
            stream = yt.streams.filter(progressive=True, file_extension="mp4", res=quality).first()
        else:
            stream = yt.streams.filter(only_audio=True).first()

        if not stream:
            return jsonify({"error": "Quality not available"}), 400

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        stream.download(output_path=os.path.dirname(temp_file.name), filename=os.path.basename(temp_file.name))
        return send_file(temp_file.name, as_attachment=True, download_name=stream.default_filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------- Instagram Download --------
@app.route("/download/instagram", methods=["POST"])
def download_instagram():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL missing"}), 400

    try:
        L = instaloader.Instaloader(download_videos=True, download_comments=False)
        shortcode_match = re.search(r"instagram\.com/p/([A-Za-z0-9_-]+)/?", url)
        if not shortcode_match:
            return jsonify({"error": "Invalid Instagram URL"}), 400

        shortcode = shortcode_match.group(1)
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        temp_dir = tempfile.mkdtemp()
        L.download_post(post, target=temp_dir)
        files = [f for f in os.listdir(temp_dir) if f.endswith((".mp4", ".jpg"))]
        if not files:
            return jsonify({"error": "Download failed"}), 500

        file_path = os.path.join(temp_dir, files[0])
        return send_file(file_path, as_attachment=True, download_name=files[0])

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
