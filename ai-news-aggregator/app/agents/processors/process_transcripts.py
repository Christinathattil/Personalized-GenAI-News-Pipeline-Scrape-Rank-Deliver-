#!/usr/bin/env python3
"""
Process YouTube transcripts for videos that don't have them yet.
Based on the reference code provided by user.
"""
from typing import Optional
import logging

from app.scrapers.youtube import YouTubeScraper
from app.database import get_session
from app.database.repository import Repository

TRANSCRIPT_UNAVAILABLE_MARKER = "__UNAVAILABLE__"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_youtube_transcripts(limit: Optional[int] = None) -> dict:
    """Process transcripts for YouTube videos without them."""
    scraper = YouTubeScraper(channels=[])  # Empty channels list since we're processing existing videos
    processed = 0
    unavailable = 0
    failed = 0
    
    with get_session() as session:
        repo = Repository(session)
        videos = repo.get_youtube_videos_without_transcript(limit=limit)
        
        logger.info(f"Found {len(videos)} videos without transcripts")
        
        for i, video in enumerate(videos, 1):
            logger.info(f"[{i}/{len(videos)}] Processing video {video.video_id}: {video.title[:50]}...")
            
            try:
                transcript_result = scraper.get_transcript(video.video_id)
                if transcript_result and transcript_result.text:
                    repo.update_youtube_video_transcript(video.video_id, transcript_result.text)
                    processed += 1
                    logger.info(f"  ✅ Transcript saved ({len(transcript_result.text)} chars)")
                else:
                    repo.update_youtube_video_transcript(video.video_id, TRANSCRIPT_UNAVAILABLE_MARKER)
                    unavailable += 1
                    logger.info(f"  ❌ No transcript available")
            except Exception as e:
                repo.update_youtube_video_transcript(video.video_id, TRANSCRIPT_UNAVAILABLE_MARKER)
                failed += 1
                logger.error(f"  💥 Error processing video {video.video_id}: {e}")
        
        # Commit all changes
        session.commit()
    
    return {
        "total": len(videos),
        "processed": processed,
        "unavailable": unavailable,
        "failed": failed
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process YouTube transcripts")
    parser.add_argument("--limit", type=int, help="Limit number of videos to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without updating")
    args = parser.parse_args()
    
    if args.dry_run:
        with get_session() as session:
            repo = Repository(session)
            videos = repo.get_youtube_videos_without_transcript(limit=args.limit)
            print(f"\nDry run: Would process {len(videos)} videos:")
            for i, video in enumerate(videos[:10], 1):  # Show first 10
                print(f"  {i}. {video.video_id} - {video.title[:60]}...")
            if len(videos) > 10:
                print(f"  ... and {len(videos) - 10} more")
    else:
        print("🎬 Starting YouTube transcript processing...")
        result = process_youtube_transcripts(limit=args.limit)
        
        print("\n📊 Processing Results:")
        print(f"  Total videos: {result['total']}")
        print(f"  ✅ Processed: {result['processed']}")
        print(f"  ❌ Unavailable: {result['unavailable']}")  
        print(f"  💥 Failed: {result['failed']}")
        
        if result['total'] > 0:
            success_rate = (result['processed'] / result['total']) * 100
            print(f"  📈 Success rate: {success_rate:.1f}%")
