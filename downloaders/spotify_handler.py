"""
YouTube download handler using yt-dlp directly (no Spotify API needed)
Supports extracting Spotify playlist metadata without authentication
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
    
    def _extract_spotify_id(self, url: str) -> Optional[str]:
        """Extract Spotify ID from URL"""
        # Spotify URLs: https://open.spotify.com/track/ID or /playlist/ID or /album/ID
        match = re.search(r'spotify\.com/(track|playlist|album)/([a-zA-Z0-9]+)', url)
        if match:
            return match.group(2)
        return None
    
    def _is_spotify_url(self, url: str) -> bool:
        """Check if URL is a Spotify URL"""
        return 'spotify.com' in url.lower()
    
    def _get_spotify_playlist_tracks(self, playlist_url: str) -> Optional[List[Dict[str, str]]]:
        """
        Extract track list from Spotify playlist using web scraping
        No API credentials needed - uses public embed API
        """
        try:
            # Extract playlist ID from URL
            match = re.search(r'spotify\.com/playlist/([a-zA-Z0-9]+)', playlist_url)
            if not match:
                logger.error("Could not extract playlist ID from URL")
                return None
            
            playlist_id = match.group(1)
            
            # Use Spotify's public embed API (no auth required)
            embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
            
            logger.info(f"Fetching Spotify playlist metadata for ID: {playlist_id}")
            
            # Get the embed page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(embed_url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch playlist: HTTP {response.status_code}")
                return None
            
            # Try to extract data from the page
            # Spotify embeds have a data-uri attribute with track info
            html = response.text
            
            # Look for the embedded data
            # This is a simplified approach - we'll use yt-dlp's spotify extractor instead
            # which can handle this better
            
            logger.info("Using yt-dlp to extract Spotify playlist metadata...")
            
            # yt-dlp can extract Spotify metadata without downloading
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,  # Don't download, just get metadata
                'skip_download': True,
            }
            
            tracks = []
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(playlist_url, download=False)
                    
                    if info and 'entries' in info:
                        for entry in info['entries']:
                            if entry:
                                artist = entry.get('artist') or entry.get('uploader') or 'Unknown'
                                title = entry.get('track') or entry.get('title') or 'Unknown'
                                
                                tracks.append({
                                    'artist': artist,
                                    'title': title
                                })
                        
                        logger.info(f"Extracted {len(tracks)} tracks from Spotify playlist")
                        return tracks
                    
                except Exception as e:
                    logger.warning(f"yt-dlp Spotify extraction failed: {e}")
                    # Fall back to web scraping
                    pass
            
            # Fallback: try to parse from HTML
            # Look for track data in script tags
            import json
            
            # Find the embedded data
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
            if match:
                try:
                    data = json.loads(match.group(1))
                    
                    # Navigate through the nested structure to find tracks
                    # This structure may change, so it's fragile
                    playlist_data = data.get('props', {}).get('pageProps', {}).get('state', {})
                    
                    # Try to find tracks in various possible locations
                    # This is highly dependent on Spotify's current page structure
                    logger.warning("HTML parsing method - structure may have changed")
                    
                except Exception as e:
                    logger.error(f"Failed to parse Spotify embed data: {e}")
            
            logger.error("Could not extract tracks from Spotify playlist")
            logger.info("Try using a public Spotify playlist or search for tracks manually")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Spotify playlist: {e}", exc_info=True)
            return None
    
    def download_url(self, url: str, custom_output: Optional[str] = None) -> Dict:
        """
        Download from YouTube or Spotify URL
        For Spotify playlists, extracts track list and searches YouTube for each
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
            # Check if it's a Spotify playlist
            if self._is_spotify_url(url) and '/playlist/' in url:
                logger.info("Detected Spotify playlist - extracting tracks...")
                
                tracks = self._get_spotify_playlist_tracks(url)
                
                if not tracks:
                    result['errors'].append("Could not extract tracks from Spotify playlist")
                    result['errors'].append("Make sure the playlist is public, or try a YouTube playlist instead")
                    return result
                
                # Extract playlist name from URL or use generic name
                playlist_match = re.search(r'/playlist/([a-zA-Z0-9]+)', url)
                playlist_name = f"spotify_playlist_{playlist_match.group(1)}" if playlist_match else "spotify_playlist"
                
                # Download tracks as a playlist
                logger.info(f"Downloading {len(tracks)} tracks from Spotify playlist...")
                return self.download_track_list(tracks, playlist_name)
            
            # Check if it's any other Spotify URL (track, album)
            if self._is_spotify_url(url):
                result['errors'].append("Spotify track/album URLs require API credentials (Premium account)")
                result['errors'].append("Try searching for the track instead: 'Artist - Song Name'")
                return result
            
            # For YouTube URLs, proceed normally
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