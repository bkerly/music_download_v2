"""
Test Phase 1 components
"""
import os
import sys
from utils.logger import setup_logger
from utils.input_parser import detect_input_type
from utils.job_manager import JobManager
from downloaders.spotify_handler import MusicDownloader

# Setup logging
logger = setup_logger()

def test_input_parser():
    """Test input type detection"""
    print("\n=== Testing Input Parser ===")
    
    test_cases = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/playlist?list=PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG",
        "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp",
        "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
        "https://open.spotify.com/album/2noRn2Aes5aoNVsU6iWThc",
        "Miles Davis - So What",
        "bohemian rhapsody",
        "music for sunset beach party in Ibiza",
        "upbeat workout playlist"
    ]
    
    for test in test_cases:
        input_type, cleaned = detect_input_type(test)
        print(f"Input: {test[:50]}")
        print(f"  Type: {input_type}")
        print()

def test_job_manager():
    """Test job management"""
    print("\n=== Testing Job Manager ===")
    
    manager = JobManager(jobs_file="test_jobs.json")
    
    # Create a test job
    job = manager.create_job("spotify_track", "https://open.spotify.com/track/test")
    print(f"Created job: {job.job_id}")
    print(f"Status: {job.status}")
    
    # Update job with mock result
    mock_result = {
        'success': True,
        'total': 10,
        'completed': 8,
        'failed': 2,
        'failed_tracks': [
            {'artist': 'Test Artist', 'title': 'Test Song 1', 'error': 'Not found'},
            {'artist': 'Test Artist', 'title': 'Test Song 2', 'error': 'Download failed'}
        ],
        'output_dir': 'downloads/test'
    }
    
    job.update_from_result(mock_result)
    manager.update_job(job)
    print(f"Updated status: {job.status}")
    print(f"Completed: {job.completed_tracks}/{job.total_tracks}")
    
    # Save failed tracks CSV
    manager.save_failed_tracks_csv(job)
    
    # Clean up test file
    if os.path.exists("test_jobs.json"):
        os.remove("test_jobs.json")

def test_downloader():
    """Test actual downloads"""
    print("\n=== Testing SpotifyDownloader ===")
    print("NOTE: This will attempt real downloads!")
    
    response = input("Run download tests? (y/n): ")
    if response.lower() != 'y':
        print("Skipping download tests")
        return
    
    try:
        downloader = MusicDownloader(output_dir="test_downloads")
        
        # Test 1: Single track search
        print("\nTest 1: Search query")
        result = downloader.download_search_query("Never Gonna Give You Up Rick Astley")
        print(f"Result: {result}")
        
        # Test 2: Spotify URL (if you have one)
        # print("\nTest 2: Spotify URL")
        # result = downloader.download_url("https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT")
        # print(f"Result: {result}")
        
        # Test 3: Track list
        print("\nTest 3: Track list")
        tracks = [
            {'artist': 'Miles Davis', 'title': 'So What'},
            {'artist': 'MGMT', 'title': 'Kids'}
        ]
        result = downloader.download_track_list(tracks, "test_playlist")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"Error in download tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Phase 1: Core Download Engine Tests")
    print("=" * 50)
    
    test_input_parser()
    test_job_manager()
    test_downloader()
    
    print("\n" + "=" * 50)
    print("Tests complete!")