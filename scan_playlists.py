import os
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Initialize Flask app
app = Flask(__name__)

# Configuration
VIDEO_FOLDER = './playlists'
ALLOWED_EXTENSIONS = {'m3u8', 'm3u'}
SCAN_INTERVAL = 300  # Scan directory every 5 minutes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure video folder exists
os.makedirs(VIDEO_FOLDER, exist_ok=True)

class PlaylistScanner:
    def __init__(self):
        self.playlists = []
        self.last_scan = 0

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def scan_playlists(self, force=False):
        current_time = time.time()
        
        # Only scan if forced or enough time has passed since last scan
        if not force and current_time - self.last_scan < SCAN_INTERVAL:
            return self.playlists

        logger.info("Scanning playlists directory...")
        new_playlists = []
        
        try:
            for root, _, files in os.walk(VIDEO_FOLDER):
                for file in files:
                    if self.allowed_file(file):
                        relative_path = os.path.relpath(root, VIDEO_FOLDER)
                        url_path = os.path.join(relative_path, file).replace('\\', '/')
                        
                        # Read first line of playlist file for title (if it's a comment)
                        title = file
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                first_line = f.readline().strip()
                                if first_line.startswith('#EXTINF:'):
                                    title = first_line.split(',', 1)[1]
                        except Exception as e:
                            logger.warning(f"Could not read playlist title from {file}: {e}")

                        new_playlists.append({
                            'name': title,
                            'filename': file,
                            'url': f"/playlists/{url_path}",
                            'last_modified': os.path.getmtime(file_path)
                        })

            # Sort playlists by last modified time (newest first)
            new_playlists.sort(key=lambda x: x['last_modified'], reverse=True)
            self.playlists = new_playlists
            self.last_scan = current_time
            logger.info(f"Found {len(new_playlists)} playlists")
            
        except Exception as e:
            logger.error(f"Error scanning playlists: {e}")
            if not self.playlists:  # Only raise error if we have no existing playlists
                raise

        return self.playlists

class PlaylistEventHandler(FileSystemEventHandler):
    def __init__(self, scanner):
        self.scanner = scanner

    def on_any_event(self, event):
        if event.is_directory:
            return
        if any(event.src_path.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            logger.info(f"Playlist change detected: {event.src_path}")
            self.scanner.scan_playlists(force=True)

# Initialize scanner
playlist_scanner = PlaylistScanner()

# Setup watchdog observer
observer = Observer()
event_handler = PlaylistEventHandler(playlist_scanner)
observer.schedule(event_handler, VIDEO_FOLDER, recursive=True)
observer.start()

@app.route('/')
def index():
    try:
        playlists = playlist_scanner.scan_playlists()
        return render_template('index.html', playlists=playlists)
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/playlists/<path:filename>')
def serve_playlist(filename):
    try:
        # Ensure the requested file is within VIDEO_FOLDER
        requested_path = os.path.join(VIDEO_FOLDER, filename)
        if not os.path.commonpath([requested_path, VIDEO_FOLDER]) == VIDEO_FOLDER:
            abort(403)  # Forbidden - attempt to access file outside VIDEO_FOLDER
            
        if os.path.exists(requested_path):
            directory = os.path.dirname(requested_path)
            filename = os.path.basename(requested_path)
            return send_from_directory(directory, filename)
        else:
            abort(404)  # Not Found
    except Exception as e:
        logger.error(f"Error serving playlist {filename}: {e}")
        abort(500)  # Internal Server Error

@app.route('/api/playlists')
def get_playlists():
    try:
        playlists = playlist_scanner.scan_playlists()
        return jsonify(playlists)
    except Exception as e:
        logger.error(f"Error getting playlists: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Playlist not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    try:
        # Initial scan
        playlist_scanner.scan_playlists(force=True)
        app.run(debug=True)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        observer.stop()
