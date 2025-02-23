let isPlaying = false;
let currentTrackUri = null;
let audioContext;
let analyser;
let source;
let dataArray;
let bufferLength;

// Add event listener to the search button
document.getElementById('search_button').addEventListener('click', async () => {
    const query = document.getElementById('search_bar').value;
    if (!query) {
        alert('Please enter a search query.');
        return;
    }

    try {
        // Send the search query to the backend
        const response = await fetch(`/search/${query}`);
        const text = await response.text();  // Get the response as text
        console.log('Response text:', text);  // Log the response text

        const data = JSON.parse(text);  // Parse the response as JSON

        if (data.error) {
            alert(data.error);
            return;
        }

        // Update the UI with the track details
        document.getElementById('song').textContent = data.track_name;
        document.getElementById('artist').textContent = data.artist;
        document.getElementById('image').src = data.image_url;
        document.getElementById('track_length').textContent = `Length: ${formatTime(data.track_length)}`;

        // Store the track URI
        currentTrackUri = data.track_uri;
    } catch (error) {
        console.error('Error fetching track data:', error);
        alert('An error occurred while fetching track data.');
    }
});

// Helper function to format track length (seconds to mm:ss)
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

// Play/Pause button functionality
const startPauseButton = document.getElementById('StartPause_image');

startPauseButton.addEventListener('click', () => {
    isPlaying = !isPlaying; // Toggle play/pause state
    startPauseButton.src = isPlaying ? 'static/images/pause.png' : 'static/images/play.png';

    // Call the backend to play/pause the track
    controlPlayback(isPlaying, currentTrackUri);
});

// Function to control playback (play/pause)
async function controlPlayback(play, trackUri) {
    try {
        const response = await fetch('/control_playback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ play: play, track_uri: trackUri }),
        });
        const data = await response.json();

        if (data.error) {
            alert(`Error: ${data.error}`);
            console.error(`Error: ${data.error}`);
            return;
        }

        console.log('Playback control successful:', data);

        if (play) {
            // Initialize the audio context and analyser
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioContext.createAnalyser();
                analyser.fftSize = 256;
                bufferLength = analyser.frequencyBinCount;
                dataArray = new Uint8Array(bufferLength);

                // Connect the audio context to the audio source
                const audioElement = new Audio();
                audioElement.src = `https://open.spotify.com/track/${trackUri.split(':').pop()}`;
                audioElement.crossOrigin = "anonymous";
                source = audioContext.createMediaElementSource(audioElement);
                source.connect(analyser);
                analyser.connect(audioContext.destination);

                audioElement.play();
                drawVisualizer();
            }
        }
    } catch (error) {
        console.error('Error controlling playback:', error);
        alert('An error occurred while controlling playback.');
    }
}

// Music Sync Visualizer
const visualiser = document.getElementById('visualiser');
const canvasCtx = visualiser.getContext('2d');

function drawVisualizer() {
    requestAnimationFrame(drawVisualizer);
    analyser.getByteFrequencyData(dataArray);

    canvasCtx.fillStyle = 'rgb(190, 190, 190)';
    canvasCtx.fillRect(0, 0, visualiser.width, visualiser.height);

    const barWidth = (visualiser.width / bufferLength) * 2.5;
    let barHeight;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
        barHeight = dataArray[i];
        canvasCtx.fillStyle = `rgb(${barHeight + 100}, 50, 50)`;
        canvasCtx.fillRect(x, visualiser.height - barHeight / 2, barWidth, barHeight / 2);
        x += barWidth + 1;
    }
}

// Initialize visualizer
visualiser.width = 300;
visualiser.height = 40;