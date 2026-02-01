 """YouTube URL parsing utilities to extract channel IDs."""
from __future__ import annotations

import re
import os
import requests
from typing import Optional, Tuple


def extract_channel_id_from_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract YouTube channel ID from various URL formats.
    
    Supported formats:
    - https://www.youtube.com/channel/UC...
    - https://www.youtube.com/@username
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/playlist?list=PL...
    
    Returns:
        Tuple of (channel_id, channel_name) or (None, None) if extraction fails.
    """
    url = url.strip()
    
    # Direct channel URL: /channel/UC...
    channel_match = re.search(r"youtube\.com/channel/([a-zA-Z0-9_-]{24})", url)
    if channel_match:
        return channel_match.group(1), None
    
    # Handle URL: /@username
    handle_match = re.search(r"youtube\.com/@([a-zA-Z0-9_-]+)", url)
    if handle_match:
        handle = handle_match.group(1)
        channel_id = resolve_handle_to_channel_id(handle)
        return channel_id, f"@{handle}"
    
    # Video URL: /watch?v=VIDEO_ID or youtu.be/VIDEO_ID
    video_match = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    if video_match:
        video_id = video_match.group(1)
        return get_channel_id_from_video(video_id)
    
    # Playlist URL: /playlist?list=PL...
    playlist_match = re.search(r"youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)", url)
    if playlist_match:
        playlist_id = playlist_match.group(1)
        return get_channel_id_from_playlist(playlist_id)
    
    return None, None


def resolve_handle_to_channel_id(handle: str) -> Optional[str]:
    """
    Resolve a YouTube handle (@username) to a channel ID.
    Uses oembed endpoint which doesn't require API key.
    """
    try:
        # Try to get channel page and extract channel ID from meta tags
        response = requests.get(
            f"https://www.youtube.com/@{handle}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        if response.status_code == 200:
            # Look for channel ID in the page content
            match = re.search(r'"channelId":"([a-zA-Z0-9_-]{24})"', response.text)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


def get_channel_id_from_video(video_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Get channel ID from a video ID.

    If env var YOUTUBE_API_KEY is set, use YouTube Data API v3 which is faster and
    more reliable than scraping. Falls back to the oEmbed + scraping approach
    when no key is configured.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if api_key:
        try:
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"part": "snippet", "id": video_id, "key": api_key},
                timeout=5,
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    snippet = items[0]["snippet"]
                    return snippet.get("channelId"), snippet.get("channelTitle")
        except Exception:
            pass  # fall through to oEmbed method below
    try:
        # Use oembed to get video info
        response = requests.get(
            f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            author_url = data.get("author_url", "")
            channel_name = data.get("author_name")
            
            # Extract channel ID from author_url
            if "/channel/" in author_url:
                match = re.search(r"/channel/([a-zA-Z0-9_-]{24})", author_url)
                if match:
                    return match.group(1), channel_name
            
            # If author_url uses handle format, resolve it
            if "/@" in author_url:
                handle_match = re.search(r"/@([a-zA-Z0-9_-]+)", author_url)
                if handle_match:
                    channel_id = resolve_handle_to_channel_id(handle_match.group(1))
                    return channel_id, channel_name
    except Exception:
        pass
    
    # Fallback: scrape video page
    try:
        response = requests.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        if response.status_code == 200:
            match = re.search(r'"channelId":"([a-zA-Z0-9_-]{24})"', response.text)
            if match:
                return match.group(1), None
    except Exception:
        pass
    
    return None, None


def get_channel_id_from_playlist(playlist_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Get channel ID from a playlist ID.
    """
    try:
        response = requests.get(
            f"https://www.youtube.com/playlist?list={playlist_id}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        if response.status_code == 200:
            match = re.search(r'"channelId":"([a-zA-Z0-9_-]{24})"', response.text)
            if match:
                return match.group(1), None
    except Exception:
        pass
    return None, None


def validate_and_extract_channels(urls: list[str]) -> list[dict]:
    """
    Validate a list of YouTube URLs and extract channel information.
    
    Returns:
        List of dicts with keys: channel_id, channel_name, original_url
    """
    results = []
    seen_channel_ids = set()
    
    for url in urls:
        channel_id, channel_name = extract_channel_id_from_url(url)
        if channel_id and channel_id not in seen_channel_ids:
            seen_channel_ids.add(channel_id)
            results.append({
                "channel_id": channel_id,
                "channel_name": channel_name,
                "original_url": url
            })
    
    return results
