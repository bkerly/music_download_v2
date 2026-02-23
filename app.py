"""
Flask web interface for music downloader
"""
from flask import Flask, render_template, request, jsonify
import os
import logging
from utils.logger import setup_logger
from utils.input_parser import detect_input_type
from utils.job_manager import JobManager
from downloaders.spotify_handler import MusicDownloader
from downloaders.vibe_handler import VibePlaylistGenerator

# Setup
logger = setup_logger()
app = Flask(__name__)

# Initialize components
job_manager = JobManager()
downloader = MusicDownloader(output_dir="downloads")
vibe_generator = VibePlaylistGenerator()

# Create necessary directories
os.makedirs("downloads", exist_ok=True)
os.makedirs("logs", exist_ok=True)


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/submit', methods=['POST'])
def submit_download():
    """Submit a download job"""
    data = request.json
    user_input = data.get('input', '').strip()
    
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400
    
    # Check if it's pasted playlist text
    if '\n' in user_input and any(char.isdigit() for char in user_input.split('\n')[0][:3]):
        # Looks like pasted Spotify playlist
        tracks = downloader.parse_playlist_text(user_input)
        
        if not tracks:
            return jsonify({'error': 'Could not parse playlist text'}), 400
        
        playlist_name = data.get('playlist_name', 'pasted_playlist').strip() or 'pasted_playlist'
        
        # Create job
        job = job_manager.create_job('pasted_playlist', f"{len(tracks)} tracks")
        job.status = 'queued'
        job_manager.update_job(job)
        
        # Start download in background
        import threading
        thread = threading.Thread(
            target=process_track_list,
            args=(job.job_id, tracks, playlist_name)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job.job_id,
            'message': f'Downloading {len(tracks)} tracks...'
        })
    
    # Detect input type
    input_type, cleaned_input = detect_input_type(user_input)
    
    # Handle vibe descriptions
    if input_type == 'vibe_description':
        # Check if Ollama is available
        if not vibe_generator.test_connection():
            return jsonify({
                'error': 'Ollama is not running. Start it with: ollama serve'
            }), 503
        
        num_tracks = data.get('num_tracks', 30)
        
        # Create job
        job = job_manager.create_job('vibe_description', user_input)
        job.status = 'generating'
        job_manager.update_job(job)
        
        # Generate and download in background
        import threading
        thread = threading.Thread(
            target=process_vibe,
            args=(job.job_id, user_input, num_tracks)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job.job_id,
            'message': 'Generating playlist from vibe...'
        })
    
    # Create job for URL or search
    job = job_manager.create_job(input_type, cleaned_input)
    job.status = 'queued'
    job_manager.update_job(job)
    
    # Start download in background
    import threading
    thread = threading.Thread(
        target=process_download,
        args=(job.job_id, input_type, cleaned_input)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job.job_id,
        'message': 'Download started...'
    })


@app.route('/api/jobs')
def get_jobs():
    """Get all jobs"""
    jobs = job_manager.get_all_jobs()
    return jsonify([job.to_dict() for job in jobs])


@app.route('/api/jobs/<job_id>')
def get_job(job_id):
    """Get specific job status"""
    job = job_manager.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job.to_dict())


def process_download(job_id: str, input_type: str, cleaned_input: str):
    """Process download in background thread"""
    job = job_manager.get_job(job_id)
    if not job:
        return
    
    try:
        job.status = 'downloading'
        job_manager.update_job(job)
        
        if input_type in ['youtube_video', 'youtube_playlist']:
            result = downloader.download_url(cleaned_input)
        elif input_type == 'search_query':
            result = downloader.download_search_query(cleaned_input)
        else:
            result = {
                'success': False,
                'errors': [f'Input type {input_type} not supported yet']
            }
        
        job.update_from_result(result)
        job_manager.update_job(job)
        
        if job.failed_tracks > 0:
            job_manager.save_failed_tracks_csv(job)
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
        job.status = 'failed'
        job.error_messages.append(str(e))
        job_manager.update_job(job)


def process_vibe(job_id: str, vibe: str, num_tracks: int):
    """Process vibe-based playlist in background thread"""
    job = job_manager.get_job(job_id)
    if not job:
        return
    
    try:
        # Generate playlist
        job.status = 'generating'
        job_manager.update_job(job)
        
        tracks = vibe_generator.generate_playlist(vibe, num_tracks)
        
        if not tracks:
            job.status = 'failed'
            job.error_messages.append('Failed to generate playlist from vibe')
            job_manager.update_job(job)
            return
        
        # Download tracks
        job.status = 'downloading'
        job_manager.update_job(job)
        
        # Create sanitized playlist name from vibe
        import re
        playlist_name = re.sub(r'[^a-zA-Z0-9_-]', '_', vibe[:50])
        
        result = downloader.download_track_list(tracks, playlist_name)
        
        job.update_from_result(result)
        job_manager.update_job(job)
        
        if job.failed_tracks > 0:
            job_manager.save_failed_tracks_csv(job)
        
    except Exception as e:
        logger.error(f"Error processing vibe job {job_id}: {e}", exc_info=True)
        job.status = 'failed'
        job.error_messages.append(str(e))
        job_manager.update_job(job)


def process_track_list(job_id: str, tracks: list, playlist_name: str):
    """Process track list download in background thread"""
    job = job_manager.get_job(job_id)
    if not job:
        return
    
    try:
        job.status = 'downloading'
        job_manager.update_job(job)
        
        result = downloader.download_track_list(tracks, playlist_name)
        
        job.update_from_result(result)
        job_manager.update_job(job)
        
        if job.failed_tracks > 0:
            job_manager.save_failed_tracks_csv(job)
        
    except Exception as e:
        logger.error(f"Error processing track list job {job_id}: {e}", exc_info=True)
        job.status = 'failed'
        job.error_messages.append(str(e))
        job_manager.update_job(job)


if __name__ == '__main__':
    print("\n" + "="*50)
    print("Music Downloader - Web Interface")
    print("="*50)
    print("\nStarting server at http://localhost:5000")
    print("\nMake sure Ollama is running for vibe-based playlists:")
    print("  ollama serve")
    print("\n" + "="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)