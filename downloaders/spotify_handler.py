"""
YouTube download handler using yt-dlp directly (no Spotify API needed)
Supports parsing pasted Spotify playlist text
"""
import os
import logging
import yt_dlp
import requests
import re
from typing import List, Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class MusicDownloader:
    """Music downloader using yt-dlp (no Spotify API required)"""
    
    def __init__(self, output_dir: str = "downloads", threads: int = 4):
        self.output_dir = output_dir
        self.threads = threads
        
        # Base yt-dlp options
        self.ydl_opts_base = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'outtmpl': os.path.join(output_dir, '%(artist)s/%(album)s/%(artist)s - %(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'extract_flat': False,
        }
        
        logger.info("MusicDownloader initialized successfully")
    
    def parse_playlist_text(self, playlist_text: str) -> List[Dict[str, str]]:
        """
        Parse pasted Spotify playlist text from embed view
        
        Expected format:
        1. Song Title
        Artist Name
        03:28
        
        Returns list of {'artist': ..., 'title': ...}
        """
        tracks = []
        lines = playlist_text.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Look for numbered track entries (e.g., "1. Song Title")
            # Remove track number if present
            title_line = re.sub(r'^\d+\.\s*', '', line)
            
            # Check if this could be a track title (not a time duration)
            if not re.match(r'^\d{1,2}:\d{2}$', title_line):
                # Next line should be artist (unless it's a duration)
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    
                    # Check if next line is artist (not a duration)
                    if not re.match(r'^\d{1,2}:\d{2}$', next_line):
                        artist = next_line
                        title = title_line
                        
                        # Clean up common suffixes
                        title = re.sub(r'\s*-\s*Remastered.*$', '', title, flags=re.IGNORECASE)
                        
                        tracks.append({
                            'artist': artist,
                            'title': title
                        })
                        
                        # Skip to duration line or next track
                        i += 2
                        
                        # Skip duration if present
                        if i < len(lines) and re.match(r'^\d{1,2}:\d{2}$', lines[i].strip()):
                            i += 1
                        continue
            
            i += 1
        
        logger.info(f"Parsed {len(tracks)} tracks from pasted text")
        return tracks
    
    def download_url(self, url: str, custom_output: Optional[str] = None) -> Dict:
        """
        Download from YouTube URL
        """
        result = {
            'success': False,
            'total': 0,
            'completed': 0,
            'failed': 0,
            'failed_tracks': [],
            'output_dir': self.output_dir,
            'errors': []
        }
        
        try:
            # Set up yt-dlp options
            ydl_opts = self.ydl_opts_base.copy()
            
            if custom_output:
                ydl_opts['outtmpl'] = os.path.join(self.output_dir, custom_output)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Extracting info from: {url}")
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    result['errors'].append(f"Could not extract info from URL: {url}")
                    return result
                
                # Check if it's a playlist
                if 'entries' in info:
                    entries = [e for e in info['entries'] if e is not None]
                    result['total'] = len(entries)
                    logger.info(f"Found playlist with {len(entries)} tracks")
                else:
                    result['total'] = 1
                    logger.info(f"Found single track")
                
                # Download
                logger.info("Starting download...")
                ydl.download([url])
                
                # Since yt-dlp doesn't give us detailed per-track results easily,
                # we'll assume success if we got here without exceptions
                result['completed'] = result['total']
                result['success'] = True
                
        except Exception as e:
            error_msg = str(e)
            result['errors'].append(f"Download error: {error_msg}")
            result['failed'] = result['total'] - result['completed']
            logger.error(f"Error downloading from URL: {e}", exc_info=True)
        
        return result
    
    def download_search_query(self, query: str, custom_output: Optional[str] = None) -> Dict:
        """
        Search YouTube and download first result
        """
        result = {
            'success': False,
            'total': 1,
            'completed': 0,
            'failed': 0,
            'failed_tracks': [],
            'output_dir': self.output_dir,
            'errors': []
        }
        
        try:
            # Set up yt-dlp options for search
            ydl_opts = self.ydl_opts_base.copy()
            
            if custom_output:
                ydl_opts['outtmpl'] = os.path.join(self.output_dir, custom_output)
            
            # Use ytsearch to find and download first result
            search_query = f"ytsearch1:{query} official audio"
            
            logger.info(f"Searching for: {query}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                
                if not info or 'entries' not in info or not info['entries']:
                    result['failed'] = 1
                    result['failed_tracks'].append({
                        'artist': 'Unknown',
                        'title': query,
                        'error': 'No search results found'
                    })
                    result['errors'].append(f"No results found for: {query}")
                    logger.warning(f"No results for: {query}")
                    return result
                
                # Get first result
                video = info['entries'][0]
                if video:
                    logger.info(f"Found: {video.get('title', 'Unknown')}")
                    ydl.download([video['webpage_url']])
                    result['completed'] = 1
                    result['success'] = True
                    logger.info(f"✓ Downloaded: {query}")
                else:
                    result['failed'] = 1
                    result['failed_tracks'].append({
                        'artist': 'Unknown',
                        'title': query,
                        'error': 'No valid result found'
                    })
                    logger.warning(f"✗ No valid result for: {query}")
                    
        except Exception as e:
            result['failed'] = 1
            result['failed_tracks'].append({
                'artist': 'Unknown',
                'title': query,
                'error': str(e)
            })
            result['errors'].append(f"Search error: {str(e)}")
            logger.error(f"Error searching for {query}: {e}", exc_info=True)
        
        return result
    
    def download_track_list(self, tracks: List[Dict[str, str]], playlist_name: str) -> Dict:
        """
        Download a list of tracks from CSV (artist, title)
        Organizes as playlist_name/tracks
        """
        result = {
            'success': False,
            'total': len(tracks),
            'completed': 0,
            'failed': 0,
            'failed_tracks': [],
            'output_dir': os.path.join(self.output_dir, playlist_name),
            'errors': []
        }
        
        # Custom output for playlist organization
        custom_output = f"{playlist_name}/%(artist)s - %(title)s.%(ext)s"
        
        logger.info(f"Downloading {len(tracks)} tracks for playlist: {playlist_name}")
        
        for idx, track in enumerate(tracks, 1):
            artist = track.get('artist', '')
            title = track.get('title', '')
            
            if not artist or not title:
                result['failed'] += 1
                result['failed_tracks'].append({
                    'artist': artist,
                    'title': title,
                    'error': 'Missing artist or title'
                })
                continue
            
            query = f"{artist} {title}"
            logger.info(f"[{idx}/{len(tracks)}] Searching for: {query}")
            
            track_result = self.download_search_query(query, custom_output)
            
            result['completed'] += track_result['completed']
            result['failed'] += track_result['failed']
            result['failed_tracks'].extend(track_result['failed_tracks'])
        
        result['success'] = result['completed'] > 0
        
        logger.info(f"Playlist download complete: {result['completed']}/{result['total']} succeeded")
        
        return result