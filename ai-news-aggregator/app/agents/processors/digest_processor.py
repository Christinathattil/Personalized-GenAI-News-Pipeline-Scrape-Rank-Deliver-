"""Digest processor for generating article summaries."""

import os
from typing import Dict, Any

from app.database import get_session
from app.database.repository import Repository
from app.agents.digest_generator import DigestGenerator


class DigestProcessor:
    """Processes articles and generates digests using AI summarization."""
    
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """Initialize the digest processor.
        
        Args:
            model_name: HuggingFace model name for summarization
        """
        self.model_name = model_name
        self.digest_generator = None
        
    def _init_generator(self) -> bool:
        """Initialize the digest generator if not already done."""
        if self.digest_generator is None:
            try:
                self.digest_generator = DigestGenerator(self.model_name)
                return True
            except ValueError as e:
                print(f"Failed to initialize digest generator: {e}")
                return False
        return True
    
    def process_pending_articles(self, force_regenerate: bool = False, article_type_filter: str = None) -> Dict[str, Any]:
        """Process all articles that don't have digests yet.
        
        Args:
            force_regenerate: If True, regenerate digests for articles that already have them
            article_type_filter: If provided, only process articles of this type (youtube, openai, anthropic)
            
        Returns:
            Dict with processing results and statistics
        """
        if not self._init_generator():
            return {"error": "Failed to initialize digest generator - check HUGGINGFACE_API_TOKEN"}
        
        results = {
            "processed": {"youtube": 0, "openai": 0, "anthropic": 0},
            "failed": {"youtube": 0, "openai": 0, "anthropic": 0},
            "skipped": {"youtube": 0, "openai": 0, "anthropic": 0},
            "total_processed": 0,
            "total_failed": 0,
            "total_skipped": 0
        }
        
        with get_session() as session:
            repo = Repository(session)
            
            if force_regenerate:
                # Get all articles regardless of digest status
                print("Force regenerate mode: processing all articles...")
                # TODO: Implement get_all_articles method in repository if needed
                articles = repo.get_all_articles_without_digests()
            else:
                # Get only articles without digests
                articles = repo.get_all_articles_without_digests()
            
            # Filter by article type if specified
            if article_type_filter:
                if article_type_filter in articles:
                    articles = {article_type_filter: articles[article_type_filter]}
                else:
                    return {"error": f"Invalid article type filter: {article_type_filter}"}
            
            total_articles = sum(len(article_list) for article_list in articles.values())
            print(f"Found {total_articles} articles to process")
            
            if total_articles == 0:
                return {"message": "No articles found that need digest generation"}
            
            # Process each article type
            for article_type, article_list in articles.items():
                if not article_list:
                    continue
                    
                print(f"\nProcessing {len(article_list)} {article_type} articles...")
                
                for i, article in enumerate(article_list, 1):
                    try:
                        # Check if digest already exists (for force mode)
                        article_id = article.video_id if article_type == "youtube" else article.guid
                        existing_digest = repo.get_digest_by_article(article_type, article_id)
                        
                        if existing_digest and not force_regenerate:
                            print(f"  [{i}/{len(article_list)}] Skipping {article_type} (digest exists)")
                            results["skipped"][article_type] += 1
                            continue
                        
                        print(f"  [{i}/{len(article_list)}] Generating digest for {article_type}...")
                        
                        # Generate digest
                        digest_data = self.digest_generator.generate_digest(article, article_type)
                        
                        if digest_data:
                            # Save to database
                            if existing_digest and force_regenerate:
                                # Update existing digest
                                existing_digest.title = digest_data["title"]
                                existing_digest.summary = digest_data["summary"]
                                print(f"    Updated digest: {digest_data['title']}")
                            else:
                                # Add new digest
                                repo.add_digest(digest_data)
                                print(f"    Created digest: {digest_data['title']}")
                            
                            results["processed"][article_type] += 1
                            session.commit()  # Commit after each successful digest
                            
                        else:
                            print(f"    Failed to generate digest")
                            results["failed"][article_type] += 1
                            
                    except Exception as e:
                        print(f"    Error processing article: {e}")
                        results["failed"][article_type] += 1
                        continue
            
            # Calculate totals
            for category in ["processed", "failed", "skipped"]:
                results[f"total_{category}"] = sum(results[category].values())
        
        return results
    
    def get_digest_stats(self) -> Dict[str, Any]:
        """Get statistics about existing digests."""
        with get_session() as session:
            repo = Repository(session)
            
            # Get all digests
            digests = repo.get_all_digests()
            
            stats = {
                "total_digests": len(digests),
                "by_type": {"youtube": 0, "openai": 0, "anthropic": 0},
                "recent_digests": []
            }
            
            for digest in digests:
                stats["by_type"][digest.article_type] += 1
            
            # Get 5 most recent digests
            recent = sorted(digests, key=lambda d: d.created_at, reverse=True)[:5]
            for digest in recent:
                stats["recent_digests"].append({
                    "type": digest.article_type,
                    "title": digest.title,
                    "created_at": digest.created_at.isoformat()
                })
            
            return stats


def main():
    """CLI entry point for digest processing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process articles and generate digests")
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Regenerate digests for articles that already have them"
    )
    parser.add_argument(
        "--type", 
        choices=["youtube", "openai", "anthropic"],
        help="Only process articles of this type"
    )
    parser.add_argument(
        "--stats", 
        action="store_true",
        help="Show digest statistics"
    )
    parser.add_argument(
        "--model",
        default="facebook/bart-large-cnn",
        help="HuggingFace model name for summarization"
    )
    
    args = parser.parse_args()
    
    processor = DigestProcessor(model_name=args.model)
    
    if args.stats:
        stats = processor.get_digest_stats()
        print("\nDigest Statistics:")
        print(f"Total digests: {stats['total_digests']}")
        print("By type:")
        for article_type, count in stats["by_type"].items():
            print(f"  {article_type}: {count}")
        
        if stats["recent_digests"]:
            print("\nRecent digests:")
            for digest in stats["recent_digests"]:
                print(f"  [{digest['type']}] {digest['title']} ({digest['created_at']})")
    else:
        results = processor.process_pending_articles(
            force_regenerate=args.force,
            article_type_filter=args.type
        )
        
        if "error" in results:
            print(f"Error: {results['error']}")
            return
        
        if "message" in results:
            print(results["message"])
            return
        
        print(f"\nDigest Processing Complete!")
        print(f"Processed: {results['total_processed']}")
        print(f"Failed: {results['total_failed']}")
        print(f"Skipped: {results['total_skipped']}")
        
        print("\nBreakdown by type:")
        for article_type in ["youtube", "openai", "anthropic"]:
            processed = results["processed"][article_type]
            failed = results["failed"][article_type]
            skipped = results["skipped"][article_type]
            total = processed + failed + skipped
            if total > 0:
                print(f"  {article_type}: {processed} processed, {failed} failed, {skipped} skipped")


if __name__ == "__main__":
    main()
