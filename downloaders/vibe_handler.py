"""
Vibe-based playlist generation using Ollama
"""
import logging
import requests
import json
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class VibePlaylistGenerator:
    """Generate playlists from vibe descriptions using Ollama"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "ministral-3"):
        self.ollama_url = ollama_url
        self.model = model
        logger.info(f"VibePlaylistGenerator initialized with model: {model}")
    
    def generate_playlist(self, vibe: str, num_tracks: int = 30) -> Optional[List[Dict[str, str]]]:
        """
        Generate a playlist from a vibe description
        
        Args:
            vibe: Natural language description of desired music
            num_tracks: Number of tracks to generate
            
        Returns:
            List of {'artist': ..., 'title': ...} dicts, or None if failed
        """
        prompt = f'''You are a music supervisor creating playlists. Generate a playlist of exactly {num_tracks} songs based on this description: "{vibe}"

Output ONLY valid CSV format with exactly two columns: artist,title
No headers, no explanations, no numbering, no extra text.
Each line should be: Artist Name,Song Title

Example format:
MGMT,Kids
Passion Pit,Sleepyhead

Now generate the playlist:'''
        
        try:
            logger.info(f"Generating playlist for vibe: {vibe}")
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120  # 2 minute timeout for generation
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code}")
                return None
            
            result = response.json()
            playlist_text = result.get('response', '')
            
            if not playlist_text:
                logger.error("Ollama returned empty response")
                return None
            
            logger.debug(f"Ollama response: {playlist_text[:200]}...")
            
            # Parse the response
            tracks = self._parse_playlist_response(playlist_text)
            
            if not tracks:
                logger.error("Failed to parse any tracks from Ollama response")
                return None
            
            logger.info(f"Successfully generated {len(tracks)} tracks")
            return tracks
            
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to Ollama - is it running?")
            return None
        except Exception as e:
            logger.error(f"Error generating playlist: {e}", exc_info=True)
            return None
    
    def _parse_playlist_response(self, response_text: str) -> List[Dict[str, str]]:
        """Parse Ollama's response into track list"""
        tracks = []
        
        # Split into lines
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip headers, explanations, markdown
            if any(skip in line.lower() for skip in ['artist,title', 'here', 'based on', 'playlist', '---', '```']):
                continue
            
            # Look for lines with commas (CSV format)
            if ',' in line:
                # Remove any leading numbers or bullets
                line = line.lstrip('0123456789.- ')
                
                # Split on first comma
                parts = line.split(',', 1)
                if len(parts) == 2:
                    artist = parts[0].strip()
                    title = parts[1].strip()
                    
                    # Basic validation
                    if artist and title and len(artist) > 0 and len(title) > 0:
                        tracks.append({
                            'artist': artist,
                            'title': title
                        })
        
        return tracks
    
    def test_connection(self) -> bool:
        """Test if Ollama is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False