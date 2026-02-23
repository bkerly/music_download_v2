"""
Simple CLI to test Phase 1
"""
import os
import re
from utils.logger import setup_logger
from utils.input_parser import detect_input_type
from utils.job_manager import JobManager
from downloaders.spotify_handler import MusicDownloader

# Setup
logger = setup_logger()
job_manager = JobManager()
downloader = MusicDownloader(output_dir="downloads")

def main():
    print("Music Downloader - Phase 1 Test")
    print("=" * 50)
    print("\nOptions:")
    print("  - Paste a URL (YouTube or Spotify playlist)")
    print("  - Enter a search query (e.g., 'Artist - Song')")
    print("  - Paste Spotify playlist text (from embed view)")
    print("  - Type 'quit' to exit")
    
    while True:
        print("\nEnter URL, search query, playlist text, or 'quit':")
        
        # Check if input looks like multi-line paste
        first_line = input("> ").strip()
        
        if first_line.lower() in ['quit', 'exit', 'q']:
            break
        
        if not first_line:
            continue
        
        user_input = first_line
        
        # Check if this might be pasted playlist text (starts with number or has multiple lines coming)
        # If user pastes multiple lines, Python will only get first line, so we need to prompt for more
        if re.match(r'^\d+\.\s+', first_line) or 'Jason' in first_line or 'Playlist' in first_line:
            print("(Paste rest of playlist, then press Ctrl+D or Ctrl+Z on a new line when done)")
            print("Or just press Enter if that was the complete input")
            
            additional_lines = []
            try:
                while True:
                    line = input()
                    if not line:  # Empty line = done
                        break
                    additional_lines.append(line)
            except EOFError:
                pass  # Ctrl+D pressed
            
            if additional_lines:
                user_input = first_line + '\n' + '\n'.join(additional_lines)
        
        # Check if this is pasted playlist text
        if '\n' in user_input and re.search(r'\d{1,2}:\d{2}', user_input):
            # This looks like pasted Spotify playlist text
            print("\nDetected pasted Spotify playlist text")
            
            tracks = downloader.parse_playlist_text(user_input)
            
            if not tracks:
                print("Could not parse any tracks from pasted text")
                continue
            
            print(f"Found {len(tracks)} tracks")
            
            # Ask for playlist name
            playlist_name = input("Enter playlist name (or press Enter for 'pasted_playlist'): ").strip()
            if not playlist_name:
                playlist_name = "pasted_playlist"
            
            # Create job
            job = job_manager.create_job('pasted_playlist', f"{len(tracks)} tracks")
            print(f"Job ID: {job.job_id}")
            
            job.status = 'downloading'
            job_manager.update_job(job)
            
            try:
                result = downloader.download_track_list(tracks, playlist_name)
                
                job.update_from_result(result)
                job_manager.update_job(job)
                
                print(f"\nStatus: {job.status}")
                print(f"Completed: {job.completed_tracks}/{job.total_tracks}")
                if job.failed_tracks > 0:
                    print(f"Failed: {job.failed_tracks}")
                    job_manager.save_failed_tracks_csv(job)
                
            except Exception as e:
                print(f"\nError: {e}")
                job.status = 'failed'
                job.error_messages.append(str(e))
                job_manager.update_job(job)
                logger.error(f"Download failed for job {job.job_id}", exc_info=True)
            
            continue
        
        # Regular URL/search processing
        input_type, cleaned_input = detect_input_type(user_input)
        print(f"\nDetected type: {input_type}")
        
        job = job_manager.create_job(input_type, cleaned_input)
        print(f"Job ID: {job.job_id}")
        
        job.status = 'downloading'
        job_manager.update_job(job)
        
        try:
            if input_type in ['youtube_video', 'youtube_playlist', 'spotify_track', 
                              'spotify_playlist', 'spotify_album']:
                print("Downloading from URL...")
                result = downloader.download_url(cleaned_input)
            elif input_type == 'search_query':
                print("Searching and downloading...")
                result = downloader.download_search_query(cleaned_input)
            else:
                print(f"Type '{input_type}' not yet supported in Phase 1")
                print("(Vibe descriptions will be added in Phase 3)")
                job.status = 'failed'
                job.error_messages.append("Input type not yet supported")
                job_manager.update_job(job)
                continue
            
            job.update_from_result(result)
            job_manager.update_job(job)
            
            print(f"\nStatus: {job.status}")
            print(f"Completed: {job.completed_tracks}/{job.total_tracks}")
            if job.failed_tracks > 0:
                print(f"Failed: {job.failed_tracks}")
                job_manager.save_failed_tracks_csv(job)
            
            if job.error_messages:
                print("\nErrors:")
                for error in job.error_messages:
                    print(f"  - {error}")
            
        except Exception as e:
            print(f"\nError: {e}")
            job.status = 'failed'
            job.error_messages.append(str(e))
            job_manager.update_job(job)
            logger.error(f"Download failed for job {job.job_id}", exc_info=True)
    
    print("\nGoodbye!")

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    main()