"""
Simple CLI to test Phase 1
"""
import os
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
    
    while True:
        print("\nEnter a URL, search query, or 'quit' to exit:")
        user_input = input("> ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if not user_input:
            continue
        
        # Detect input type
        input_type, cleaned_input = detect_input_type(user_input)
        print(f"\nDetected type: {input_type}")
        
        # Create job
        job = job_manager.create_job(input_type, cleaned_input)
        print(f"Job ID: {job.job_id}")
        
        # Start download
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
            
            # Update job with result
            job.update_from_result(result)
            job_manager.update_job(job)
            
            # Print results
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