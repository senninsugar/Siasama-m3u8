import subprocess
import json
import os
import shutil
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_m3u8(url):
    YT_DLP_PATH = "yt-dlp"
    PROXY_URL = "http://other.siatube.com:3007"
    
    node_path = shutil.which("node")
    
    command = [
        YT_DLP_PATH,
        "--js-runtimes", "node",
        "--proxy", PROXY_URL,
        "-J",
        "--skip-download",
        "--no-progress",
        url
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        if result.returncode != 0:
            return {"error": f"yt-dlp failed: {result.stderr}"}, 500

        data = json.loads(result.stdout)
        formats = data.get("formats", [])
        
        m3u8_list = []
        for f in formats:
            if 'm3u8' in f.get('protocol', '') or f.get('ext') == 'm3u8' or '.m3u8' in f.get('url', ''):
                m3u8_list.append({
                    "format_id": f.get("format_id"),
                    "resolution": f.get("resolution"),
                    "url": f.get("url"),
                    "vcodec": f.get("vcodec"),
                    "acodec": f.get("acodec")
                })

        return {
            "title": data.get("title"),
            "m3u8_urls": m3u8_list
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/extract', methods=['GET'])
def extract():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    result, status_code = get_m3u8(video_url)
    return jsonify(result), status_code

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
