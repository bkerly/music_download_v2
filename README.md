# Music Downloader - Phase 1

A local music download manager using yt-dlp (no Spotify API required).

## Directory Structure

```
music_downloader/
├── downloaders/
│   ├── __init__.py
│   └── spotify_handler.py    # yt-dlp wrapper
├── utils/
│   ├── __init__.py
│   ├── input_parser.py        # Input type detection
│   ├── job_manager.py         # Job tracking
│   └── logger.py              # Logging setup
├── downloads/                 # Output directory
├── logs/                      # Log files
├── requirements.txt
├── test_phase1.py            # Unit tests
├── cli_test.py               # Interactive CLI
└── README.md
```

## Setup

1. **Create the directory structure:**
```bash
mkdir -p music_downloader/downloaders
mkdir -p music_downloader/utils
mkdir -p music_downloader/downloads
mkdir -p music_downloader/logs
cd music_downloader
```

2. **Create empty `__init__.py` files:**
```bash
touch downloaders/__init__.py
touch utils/__init__.py
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Make sure you have ffmpeg installed:**
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Usage

### Interactive CLI
```bash
python cli_test.py
```

Then enter:
- YouTube URLs (videos or playlists)
- Search queries like "Miles Davis - So What"
- Type 'quit' to exit

**Note:** Spotify URLs won't work without API credentials (Spotify now requires Premium). Use search queries or YouTube URLs instead.

### Run Tests
```bash
python test_phase1.py
```

## Features (Phase 1)

✅ Download from YouTube URLs (videos, playlists)  
✅ Search and download by query  
✅ Organize as artist/album/tracks or playlist/tracks  
✅ Job tracking and history  
✅ Failed tracks saved to CSV  
✅ Comprehensive error logging  
✅ 320kbps MP3 with proper metadata  
❌ Spotify URLs (requires Premium - use search instead)

## Output Organization

- **Albums**: `downloads/Artist/Album/Artist - Track.mp3`
- **Playlists**: `downloads/PlaylistName/Artist - Track.mp3`

## Coming in Future Phases

- Phase 2: Web interface (Flask)
- Phase 3: Ollama vibe-based playlist generation
- Phase 4: Real-time progress updates
- Phase 5: Advanced error recovery and retry logic