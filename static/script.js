let isPlaying = false;

// Fetch the access token from the backend
async function getAccessToken() {
    const response = await fetch('/get_token');
    if (response.status === 401) {
        // Handle redirect to Spotify auth page
        const data = await response.json();
        if (data.auth_url) {
            window.location.href = data.auth_url;  // Redirect to Spotify auth page
        } else {
            throw new Error('Unable to fetch access token: No auth URL provided');
        }
    } else if (response.ok) {
        const data = await response.json();
        return data.access_token;
    } else {
        throw new Error('Unable to fetch access token');
    }
}

// Initialize the Web Playback SDK
async function initializePlayer() {
    try {
        const token = await getAccessToken();
        const player = new Spotify.Player({
            name: 'IAMMUSIC Player',
            getOAuthToken: cb => { cb(token); },
            volume: 0.5
        });

        // Event listeners
        player.addListener('ready', ({ device_id }) => {
            console.log('Ready with Device ID', device_id);
        });

        player.addListener('not_ready', ({ device_id }) => {
            console.log('Device ID has gone offline', device_id);
        });

        player.addListener('initialization_error', ({ message }) => {
            console.error('Initialization Error:', message);
        });

        player.addListener('authentication_error', ({ message }) => {
            console.error('Authentication Error:', message);
        });

        player.addListener('account_error', ({ message }) => {
            console.error('Account Error:', message);
        });

        // Connect to the player
        player.connect().then(success => {
            if (success) {
                console.log('Connected to Spotify!');
            }
        });

        // Play/Pause button functionality
        const startPauseButton = document.getElementById('StartPause_image');
        startPauseButton.addEventListener('click', () => {
            isPlaying = !isPlaying;
            startPauseButton.src = isPlaying ? 'static/images/pause.png' : 'static/images/play.png';

            fetch('/control_playback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ play: isPlaying })
            }).then(response => response.json())
              .then(data => console.log(data))
              .catch(error => console.error('Error:', error));
        });
    } catch (error) {
        console.error('Error initializing player:', error);
    }
}

// Initialize the player when the SDK is ready
window.onSpotifyWebPlaybackSDKReady = () => {
    console.log('Spotify Web Playback SDK is ready!');
    initializePlayer();
};