import os
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify
import requests
from werkzeug.utils import secure_filename

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Config for the folder containing m3u8 files
VIDEO_FOLDER = './playlists'
ALLOWED_EXTENSIONS = {'m3u8'}

# Function to check if file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to scan and list all m3u8 files
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

# Route to serve the homepage with available playlists
@app.route('/')
def index():
    playlists = scan_playlists()
    return render_template('index.html', playlists=playlists)

# Route to serve m3u8 files
@app.route('/playlists/<filename>')
def serve_playlist(filename):
    file_path = os.path.join(VIDEO_FOLDER, filename)
    if os.path.exists(file_path):
        return app.send_static_file(file_path)
    else:
        return "Playlist not found", 404

if __name__ == '__main__':
    app.run(debug=True)
