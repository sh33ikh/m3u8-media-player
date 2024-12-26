import os
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

VIDEO_FOLDER = './playlists'
ALLOWED_EXTENSIONS = {'m3u8'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def scan_playlists():
    playlists = []
    for root, _, files in os.walk(VIDEO_FOLDER):
        for file in files:
            if allowed_file(file):
                playlists.append({
                    'name': file,
                    'url': f"/playlists/{secure_filename(file)}"
                })
    return playlists

@app.route('/')
def index():
    playlists = scan_playlists()
    return render_template('index.html', playlists=playlists)

@app.route('/playlists/<filename>')
def serve_playlist(filename):
    file_path = os.path.join(VIDEO_FOLDER, filename)
    if os.path.exists(file_path):
        return send_from_directory(VIDEO_FOLDER, filename)
    else:
        return "Playlist not found", 404

if __name__ == '__main__':
    app.run(debug=True)
