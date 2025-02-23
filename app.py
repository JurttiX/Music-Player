from flask import Flask, jsonify, render_template, request
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

# Log the environment variables to ensure they are loaded correctly
print("SPOTIPY_CLIENT_ID:", os.getenv('SPOTIPY_CLIENT_ID'))
print("SPOTIPY_CLIENT_SECRET:", os.getenv('SPOTIPY_CLIENT_SECRET'))
print("SPOTIPY_REDIRECT_URI:", os.getenv('SPOTIPY_REDIRECT_URI'))

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
    scope="user-modify-playback-state user-read-playback-state"
))

def search_track(query):
    """Search for a track and return its details."""
    results = sp.search(q=query, type='track', limit=1)
    if results['tracks']['items']:
        track = results['tracks']['items'][0]
        track_name = track['name']
        artist = track['artists'][0]['name']
        image_url = track['album']['images'][0]['url']  # Largest image
        track_length = track['duration_ms'] // 1000  # Convert to seconds
        track_uri = track['uri']  # Get the track URI
        return {
            'track_name': track_name,
            'artist': artist,
            'image_url': image_url,
            'track_length': track_length,
            'track_uri': track_uri
        }
    return None

@app.route('/')
def index():
    """Render the main HTML page."""
    return render_template('index.html')

@app.route('/search/<query>')
def search(query):
    """API endpoint to search for a track and return its details."""
    try:
        track_info = search_track(query)
        if track_info:
            return jsonify(track_info)
        return jsonify({'error': 'Track not found'}), 404
    except Exception as e:
        print(f"Error searching for track: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/control_playback', methods=['POST'])
def control_playback():
    """API endpoint to control playback (play/pause)."""
    data = request.json
    play = data.get('play', False)
    track_uri = data.get('track_uri', None)
    device_id = data.get('device_id', None)  # Optional: Allow specifying a device ID

    try:
        # Get the list of active devices
        devices = sp.devices()
        if not devices['devices']:
            return jsonify({'error': 'No active device found. Please open Spotify on your device.'}), 404

        # Use the specified device ID or the first active device
        if not device_id:
            device_id = devices['devices'][0]['id']

        if play:
            if track_uri:
                response = sp.start_playback(device_id=device_id, uris=[track_uri])  # Start playback of the specified track
            else:
                response = sp.start_playback(device_id=device_id)  # Start playback on the specified device
        else:
            response = sp.pause_playback(device_id=device_id)  # Pause playback on the specified device

        print(f"Spotify API response: {response}")  # Log the response
        return jsonify({'status': 'success'})
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API error: {e}")  # Log the error
        return jsonify({'error': e.msg}), e.http_status
    except Exception as e:
        print(f"Error controlling playback: {e}")  # Log the error
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)