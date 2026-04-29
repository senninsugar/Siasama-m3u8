import subprocess
import json
import os
import shutil
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_m3u8(url):
    YT_DLP_PATH = "yt-dlp"
    PROXY_URL = "http://other.siatube.com:3007"
    
    command = [
        YT_DLP_PATH,
        "--js-runtimes", "node",
        "--proxy", PROXY_URL,
        "-J",
        "--skip-download",
        "--no-check-certificate",
        "--youtube-include-hls-manifest",
        "--no-check-formats",
        "--no-warnings",
        "--extractor-args", "youtube:player_client=ios",
        url
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            timeout=25
        )

        if result.returncode != 0:
            return {"error": "yt-dlp failed", "stderr": result.stderr}, 500

        data = json.loads(result.stdout)
        m3u8_urls = []

        formats = data.get("formats", [])
        for f in formats:
            f_url = f.get('url', '')
            if 'index.m3u8' in f_url or '/hls_playlist/' in f_url:
                m3u8_urls.append({
                    "format_id": f.get("format_id"),
                    "res": f.get("resolution"),
                    "url": f_url
                })

        if not m3u8_urls:
            hls_url = data.get('url')
            if hls_url and ('m3u8' in hls_url or 'manifest' in hls_url):
                m3u8_urls.append({"format_id": "direct", "url": hls_url})

        return {
            "title": data.get("title"),
            "m3u8_urls": m3u8_urls
        }, 200

    except subprocess.TimeoutExpired:
        return {"error": "yt-dlp timeout (25s)"}, 504
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
