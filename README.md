# Music Downloader - Phase 2

A local music download manager with web interface and AI-powered playlist generation.

## Features

✅ **Web Interface** - Clean, modern UI  
✅ **YouTube Downloads** - Videos and playlists  
✅ **Spotify Playlist Import** - Copy/paste from Spotify  
✅ **Search Queries** - Find and download tracks  
✅ **Vibe-Based Playlists** - AI generates playlists from descriptions  
✅ **Job Tracking** - Real-time progress updates  
✅ **320kbps MP3** - High quality with metadata  

## Directory Structure

```
music_downloader/
├── downloaders/
│   ├── __init__.py
│   ├── spotify_handler.py    # yt-dlp wrapper
│   └── vibe_handler.py        # Ollama integration
├── utils/
│   ├── __init__.py
│   ├── input_parser.py        # Input type detection
│   ├── job_manager.py         # Job tracking
│   └── logger.py              # Logging setup
├── templates/
│   └── index.html             # Web UI
├── downloads/                 # Output directory
├── logs/                      # Log files
├── requirements.txt
├── app.py                     # Flask app
└── README.md
```

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Make sure you have ffmpeg installed:**
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

3. **Start Ollama (for vibe-based playlists):**
```bash
ollama serve
ollama pull ministral-3
```

## Usage

### Start the Web Server

```bash
python app.py
```

Then open http://localhost:5000 in your browser

### What You Can Do:

1. **YouTube URLs** - Paste any YouTube video or playlist URL
2. **Spotify Playlists** - Copy the track list from Spotify (right-click → Copy), paste it in
3. **Search Queries** - Type "Artist - Song Name"
4. **Vibe Descriptions** - Type something like "upbeat indie rock for summer road trips"

The app will:
- Detect what you entered automatically
- Download tracks as 320kbps MP3s
- Organize files as `downloads/PlaylistName/Artist - Song.mp3`
- Show real-time progress

## Output Organization

- **Playlists**: `downloads/PlaylistName/Artist - Track.mp3`
- **Albums**: `downloads/Artist/Album/Artist - Track.mp3`

## Examples

**Vibe descriptions:**
- "chill lo-fi beats for studying"
- "energetic workout music"  
- "90s euro dance party"
- "moody indie rock for rainy days"

**Spotify playlists:**
Just copy the entire track list from Spotify's embed player or web view and paste it in.

## Coming Soon

- Phase 3: Advanced error recovery
- Phase 4: Batch operations
- Phase 5: Music library management