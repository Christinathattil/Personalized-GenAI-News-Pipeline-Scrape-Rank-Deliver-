"""Digest Generation Agent using Hugging Face models."""

import json
import os
import uuid
from typing import Dict, Any, Optional

from huggingface_hub import InferenceClient


class DigestGenerator:
    """Agent that generates digests using Hugging Face summarization models."""
    
    def __init__(self, model_name: str = "sshleifer/distilbart-cnn-12-6"): 
        """Initialize the digest generator.
        
        Args:
            model_name: HuggingFace model name for summarization
        """
        self.model_name = model_name
        self.token = os.getenv("HUGGINGFACE_API_TOKEN")
        if not self.token:
            raise ValueError("HUGGINGFACE_API_TOKEN environment variable is required")

        # HF Inference client (serverless provider)
        self.client = InferenceClient(provider="hf-inference", api_key=self.token)

    def _prepare_content(self, article: Any, article_type: str) -> str:
        """Extract and prepare content from article for summarization."""
        content_parts = []
        
        if article_type == "youtube":
            # Exclude videos with no usable transcript
            if not getattr(article, "transcript", None) or getattr(article, "transcript") == "TRANSCRIPT IS NOT AVAILABLE":
                # Return empty string so caller can skip digest generation
                return ""

            # YouTube video content (transcript available)
            if hasattr(article, 'title') and article.title:
                content_parts.append(f"Title: {article.title}")
            if hasattr(article, 'description') and article.description:
                content_parts.append(f"Description: {article.description}")
            # Truncate transcript if too long (BART has ~1024 token limit)
            transcript = article.transcript[:2000] if len(article.transcript) > 2000 else article.transcript
            content_parts.append(f"Transcript: {transcript}")
        
        elif article_type in ["openai", "anthropic"]:
            # Article content
            if hasattr(article, 'title') and article.title:
                content_parts.append(f"Title: {article.title}")
            if hasattr(article, 'description') and article.description:
                content_parts.append(f"Description: {article.description}")
            if hasattr(article, 'markdown') and article.markdown and article.markdown != "MARKDOWN CONVERSION IS NOT AVAILABLE":
                # Truncate markdown if too long
                markdown = article.markdown[:2000] if len(article.markdown) > 2000 else article.markdown
                content_parts.append(f"Content: {markdown}")
        
        return " | ".join(content_parts)

    def _call_hf_api(self, text: str, max_retries: int = 5) -> Optional[str]:
        """Call Hugging Face Inference API for summarization with exponential back-off."""
        backoff_seconds = 4  # initial back-off
        for attempt in range(max_retries):
            try:
                # InferenceClient exposes a per-request timeout via keyword arg
                result = self.client.summarization(text, model=self.model_name)
                if not result:
                    raise ValueError("Empty response from HF API")
                # --- Normalize output to string ---
                if isinstance(result, str):
                    return result.strip()
                if hasattr(result, "summary_text"):
                    return str(result.summary_text).strip()
                if isinstance(result, (list, tuple)):
                    first = result[0]
                    if isinstance(first, str):
                        return first.strip()
                    if hasattr(first, "summary_text"):
                        return str(first.summary_text).strip()
                return str(result).strip()

            except Exception as e:
                err_msg = str(e)
                print(f"Error calling HuggingFace API (attempt {attempt + 1}/{max_retries}): {err_msg}")
                if attempt == max_retries - 1:
                    break  # give up
                import time
                # If it's a gateway timeout, wait longer
                if "504" in err_msg:
                    sleep_secs = backoff_seconds * (attempt + 1)
                else:
                    sleep_secs = 3 * (attempt + 1)
                print(f"Waiting {sleep_secs}s before retry…")
                time.sleep(sleep_secs)
        return None

    def _generate_title(self, content: str, summary: str) -> str:
        """Generate a title from content and summary."""
        # Extract original title if available
        if content.startswith("Title: "):
            original_title = content.split("Title: ")[1].split(" | ")[0]
            # If original title is good, use it, otherwise generate from summary
            if len(original_title) > 10 and len(original_title) < 100:
                return original_title
        
        # Generate title from first sentence of summary
        sentences = summary.split('. ')
        if sentences:
            title = sentences[0].strip()
            # Remove trailing period if present
            if title.endswith('.'):
                title = title[:-1]
            # Ensure reasonable length
            if len(title) > 80:
                title = title[:77] + "..."
            return title
        
        return "AI News Digest"

    def generate_digest(self, article: Any, article_type: str) -> Optional[Dict[str, Any]]:
        """Generate digest for an article.
        
        Args:
            article: Article ORM object
            article_type: Type of article (youtube, openai, anthropic)
            
        Returns:
            Dict containing digest data or None if generation failed
        """
        try:
            # Prepare content
            content = self._prepare_content(article, article_type)
            if not content.strip():
                print(f"No content available for {article_type} article")
                return None
            
            # Generate summary
            summary = self._call_hf_api(content)
            if not summary:
                print(f"Failed to generate summary for {article_type} article")
                return None
            
            # Generate title
            title = self._generate_title(content, summary)
            
            # Get article ID and URL
            if article_type == "youtube":
                article_id = article.video_id
                url = article.url
            else:  # openai or anthropic
                article_id = article.guid
                url = article.url
            
            # Create digest data
            digest_data = {
                "id": str(uuid.uuid4()),
                "article_type": article_type,
                "article_id": article_id,
                "url": url,
                "title": title,
                "summary": summary
            }
            
            return digest_data
            
        except Exception as e:
            print(f"Error generating digest: {e}")
            return None

    def process_articles(self, articles_by_type: Dict[str, list]) -> Dict[str, int]:
        """Process multiple articles and generate digests.
        
        Args:
            articles_by_type: Dict with article type as key and list of articles as value
            
        Returns:
            Dict with counts of successfully processed articles by type
        """
        results = {"youtube": 0, "openai": 0, "anthropic": 0}
        
        for article_type, articles in articles_by_type.items():
            print(f"Processing {len(articles)} {article_type} articles...")
            
            for article in articles:
                digest_data = self.generate_digest(article, article_type)
                if digest_data:
                    results[article_type] += 1
                    print(f"Generated digest for {article_type}: {digest_data['title']}")
                else:
                    print(f"Failed to generate digest for {article_type} article")
        
        return results
