"""
Parse and classify user input
"""
import re
from typing import Tuple
from urllib.parse import urlparse


def detect_input_type(user_input: str) -> Tuple[str, str]:
    """
    Detect what type of input the user provided
    
    Returns:
        (input_type, cleaned_input)
        
    Types:
        - youtube_video
        - youtube_playlist
        - spotify_track
        - spotify_playlist
        - spotify_album
        - search_query (looks like "Artist - Song")
        - vibe_description (natural language)
    """
    user_input = user_input.strip()
    
    # Check for URLs
    if is_url(user_input):
        parsed = urlparse(user_input)
        domain = parsed.netloc.lower()
        
        # YouTube
        if 'youtube.com' in domain or 'youtu.be' in domain:
            if 'playlist' in user_input or 'list=' in user_input:
                return ('youtube_playlist', user_input)
            return ('youtube_video', user_input)
        
        # Spotify
        elif 'spotify.com' in domain:
            if '/playlist/' in user_input:
                return ('spotify_playlist', user_input)
            elif '/album/' in user_input:
                return ('spotify_album', user_input)
            elif '/track/' in user_input:
                return ('spotify_track', user_input)
            else:
                return ('spotify_track', user_input)  # Default for Spotify URLs
    
    # Check for search query format (Artist - Song)
    if ' - ' in user_input and len(user_input.split(' - ')) == 2:
        return ('search_query', user_input)
    
    # Check for obvious search patterns
    if looks_like_search_query(user_input):
        return ('search_query', user_input)
    
    # Everything else is a vibe description
    return ('vibe_description', user_input)


def is_url(text: str) -> bool:
    """Check if text is a URL"""
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except:
        return False


def looks_like_search_query(text: str) -> bool:
    """
    Heuristic to detect if text looks like a search query
    vs a vibe description
    
    Search query: "bohemian rhapsody queen"
    Vibe: "upbeat summer party music"
    """
    # If it has common vibe words, probably a vibe
    vibe_keywords = [
        'music for', 'playlist', 'vibe', 'mood', 'feeling',
        'upbeat', 'chill', 'relaxing', 'energetic', 'party',
        'workout', 'study', 'focus', 'sleep', 'background'
    ]
    
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in vibe_keywords):
        return False
    
    # If it's short and doesn't have vibe words, probably a search
    if len(text.split()) <= 5:
        return True
    
    # Otherwise assume vibe
    return False


def clean_search_query(query: str) -> str:
    """Clean up a search query"""
    # Remove extra whitespace
    query = ' '.join(query.split())
    return query