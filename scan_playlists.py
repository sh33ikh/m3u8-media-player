from flask import Flask, render_template, send_from_directory, jsonify
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# Configuration
PLAYLIST_FOLDER = 'playlists'
ALLOWED_EXTENSIONS = {'m3u8', 'm3u'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_playlist_info(filename):
    """Get detailed information about a playlist file."""
    try:
        file_path = os.path.join(PLAYLIST_FOLDER, filename)
        stats = os.stat(file_path)
        return {
            'name': os.path.splitext(filename)[0].replace('_', ' ').title(),
            'url': f"/playlists/{secure_filename(filename)}",
            'filename': filename,
            'size': stats.st_size,
            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'created': datetime.fromtimestamp(stats.st_ctime).isoformat()
        }
    except Exception as e:
        print(f"Error getting playlist info for {filename}: {e}")
        return None

def scan_playlists():
    """Scan for playlist files and return their information."""
    playlists = []
    
    try:
        # Ensure playlist folder exists
        os.makedirs(PLAYLIST_FOLDER, exist_ok=True)
        
        # Scan for playlist files
        for filename in os.listdir(PLAYLIST_FOLDER):
            if allowed_file(filename):
                playlist_info = get_playlist_info(filename)
                if playlist_info:
                    playlists.append(playlist_info)
        
        # Add default playlist if no playlists found
        if not playlists and os.path.exists(os.path.join(PLAYLIST_FOLDER, 'play.m3u8')):
            default_info = get_playlist_info('play.m3u8')
            if default_info:
                playlists.append(default_info)
        
    except Exception as e:
        print(f"Error scanning playlists: {e}")
        # Return default playlist on error
        return [{
            'name': 'Default Playlist',
            'url': '/playlists/play.m3u8',
            'filename': 'play.m3u8',
            'size': 0,
            'modified': datetime.now().isoformat(),
            'created': datetime.now().isoformat()
        }]
    
    return sorted(playlists, key=lambda x: x['modified'], reverse=True)

@app.route('/')
def index():
    """Render the main player page."""
    try:
        playlists = scan_playlists()
        return render_template('index.html', playlists=playlists)
    except Exception as e:
        print(f"Error rendering index: {e}")
        return render_template('error.html', error="Could not load playlists"), 500

@app.route('/playlists/<filename>')
def serve_playlist(filename):
    """Serve playlist files securely."""
    try:
        secure_name = secure_filename(filename)
        if os.path.exists(os.path.join(PLAYLIST_FOLDER, secure_name)):
            return send_from_directory(PLAYLIST_FOLDER, secure_name)
        return "Playlist not found", 404
    except Exception as e:
        print(f"Error serving playlist {filename}: {e}")
        return "Error accessing playlist", 500

@app.route('/api/playlists')
def get_playlists():
    """API endpoint to get playlist information."""
    try:
        playlists = scan_playlists()
        return jsonify({
            'status': 'success',
            'playlists': playlists
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

# Required for Vercel
app.debug = False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
