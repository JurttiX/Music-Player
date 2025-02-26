from sanic import Sanic, json, redirect
from sanic.response import html
from sanic_ext import render
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Sanic app
app = Sanic("SpotifyWebPlaybackSDK")
app.static("/static", "./static")  # Serve static files

# Spotify OAuth setup
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-modify-playback-state user-read-playback-state streaming",
    cache_path=".cache",
)

# Log environment variables for debugging
print("SPOTIPY_CLIENT_ID:", os.getenv("SPOTIPY_CLIENT_ID"))
print("SPOTIPY_CLIENT_SECRET:", os.getenv("SPOTIPY_CLIENT_SECRET"))
print("SPOTIPY_REDIRECT_URI:", os.getenv("SPOTIPY_REDIRECT_URI"))

# Helper function to get Spotify client
def get_spotify_client():
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        return auth_url
    return token_info["access_token"]

# Routes
@app.route("/")
async def index(request):
    return await render("index.html")

@app.route("/get_token")
async def get_token(request):
    """Return the Spotify access token."""
    try:
        token_info = sp_oauth.get_cached_token()
        if token_info:
            print("Token Info:", token_info)  # Log token info for debugging
            return json({"access_token": token_info["access_token"]})
        else:
            print("No cached token found. Redirecting to auth URL.")
            auth_url = sp_oauth.get_authorize_url()
            print("Auth URL:", auth_url)  # Log the auth URL
            return json({"auth_url": auth_url}, status=401)  # Indicate auth is required
    except Exception as e:
        print(f"Error fetching token: {e}")
        return json({"error": str(e)}, status=500)

@app.route("/callback")
async def callback(request):
    """Handle the Spotify OAuth callback."""
    try:
        code = request.args.get("code")
        if code:
            print("Received authorization code:", code)
            token_info = sp_oauth.get_access_token(code)
            print("Token Info:", token_info)
            return redirect("/")
        else:
            return json({"error": "Authorization failed: No code provided"}, status=400)
    except Exception as e:
        print(f"Error in callback: {e}")
        return json({"error": str(e)}, status=500)

@app.route("/search/<query:str>")
async def search(request, query):
    """Search for a track and return its details."""
    try:
        sp = get_spotify_client()
        if isinstance(sp, str):  # If redirection is required
            return redirect(sp)
        track_info = search_track(sp, query)
        if track_info:
            return json(track_info)
        return json({"error": "Track not found"}, status=404)
    except Exception as e:
        print(f"Error searching for track: {e}")
        return json({"error": str(e)}, status=500)

@app.route("/control_playback", methods=["POST"])
async def control_playback(request):
    """Control playback (play/pause)."""
    try:
        data = request.json
        play = data.get("play", False)
        track_uri = data.get("track_uri", None)
        device_id = data.get("device_id", None)

        sp = get_spotify_client()
        if isinstance(sp, str):  # If redirection is required
            return redirect(sp)

        # Get active devices
        devices = sp.devices()
        if not devices["devices"]:
            return json({"error": "No active device found. Please open Spotify on your device."}, status=404)

        # Use specified device ID or the first active device
        if not device_id:
            device_id = devices["devices"][0]["id"]

        if play:
            if track_uri:
                sp.start_playback(device_id=device_id, uris=[track_uri])
            else:
                sp.start_playback(device_id=device_id)
        else:
            sp.pause_playback(device_id=device_id)

        return json({"status": "success"})
    except Exception as e:
        print(f"Error controlling playback: {e}")
        return json({"error": str(e)}, status=500)

def search_track(sp, query):
    """Search for a track and return its details."""
    results = sp.search(q=query, type="track", limit=1)
    if results["tracks"]["items"]:
        track = results["tracks"]["items"][0]
        return {
            "track_name": track["name"],
            "artist": track["artists"][0]["name"],
            "image_url": track["album"]["images"][0]["url"],
            "track_length": track["duration_ms"] // 1000,
            "track_uri": track["uri"],
        }
    return None

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)