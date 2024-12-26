import os
from flask import Flask, render_template, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
VIDEO_FOLDER = 'playlists'  # Remove './' to avoid path issues
ALLOWED_EXTENSIONS = {'m3u8', 'm3u'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def scan_playlists():
    """Scan for playlist files and return their information."""
    playlists = []
    try:
        # Ensure video folder exists
        if not os.path.exists(VIDEO_FOLDER):
            os.makedirs(VIDEO_FOLDER)
            
        # Scan for playlist files
        for file in os.listdir(VIDEO_FOLDER):
            if allowed_file(file):
                secure_name = secure_filename(file)
                playlists.append({
                    'name': os.path.splitext(secure_name)[0].replace('_', ' ').title(),
                    'url': f"/playlists/{secure_name}",
                    'filename': secure_name
                })
        
        # If no playlists found, add a default entry
        if not playlists:
            playlists.append({
                'name': 'Default Playlist',
                'url': '/playlists/play.m3u8',
                'filename': 'play.m3u8'
            })
            
    except Exception as e:
        print(f"Error scanning playlists: {e}")
        # Return default playlist if there's an error
        return [{
            'name': 'Default Playlist',
            'url': '/playlists/play.m3u8',
            'filename': 'play.m3u8'
        }]
    
    return playlists

@app.route('/')
def index():
    """Render the main page with playlist information."""
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
        return send_from_directory(VIDEO_FOLDER, secure_name)
    except Exception as e:
        print(f"Error serving playlist {filename}: {e}")
        return "Playlist not found", 404

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    app.run(debug=True)
