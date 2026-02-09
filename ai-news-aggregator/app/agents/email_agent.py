"""Email Agent - builds digest email with intro using Hugging Face LLM.

This agent generates a short personalised introduction and then formats the
highest-ranked digests (max 10) into a simple email-ready text block.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Optional

from huggingface_hub import InferenceClient
from pydantic import BaseModel, Field

from app.profiles.profile import DEFAULT_USER_PROFILE, UserProfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EmailIntroduction(BaseModel):
    greeting: str = Field(description="Personalized greeting with user's name and date")
    introduction: str = Field(description="2-3 sentence overview of what's in the top 10 ranked articles")


class RankedArticleDetail(BaseModel):
    digest_id: str
    rank: int
    relevance_score: float
    title: str
    summary: str
    url: str
    article_type: str
    reasoning: Optional[str] = None


class EmailDigestResponse(BaseModel):
    introduction: EmailIntroduction
    articles: List[RankedArticleDetail]
    total_ranked: int
    top_n: int

    def to_markdown(self) -> str:
        markdown = f"{self.introduction.greeting}\n\n"
        markdown += f"{self.introduction.introduction}\n\n"
        markdown += "---\n\n"

        for article in self.articles:
            markdown += f"## {article.title}\n\n"
            markdown += f"{article.summary}\n\n"
            markdown += f"[Read more →]({article.url})\n\n"
            markdown += "---\n\n"

        return markdown


class EmailDigest(BaseModel):
    introduction: EmailIntroduction
    ranked_articles: List[dict] = Field(description="Top 10 ranked articles with their details")


EMAIL_PROMPT = """You craft ✨ scroll-stopping ✨ newsletters for a Gen-Z-leaning tech crowd.
Write a punchy *2-3 sentence* opener that:
• Shouts out the reader by name
• Mentions today’s date
• Teases what’s hot in the top AI stories (no spoilers!)
• Uses an upbeat, conversational vibe (emoji allowed 👍) while *still sounding smart*
• Ends with a smooth hand-off into the list below

Keep jargon low, energy high, professionalism intact."""


class EmailAgent:
    """Creates an email from ranked digests using HuggingFace LLM."""

    def __init__(self, user_profile: UserProfile | dict | None = None):
        # Accept UserProfile or dict for flexibility
        if user_profile is None:
            self.user_profile = DEFAULT_USER_PROFILE.model_dump()
        elif isinstance(user_profile, dict):
            self.user_profile = user_profile
        else:
            self.user_profile = user_profile.model_dump()

        token = os.getenv("HUGGINGFACE_API_TOKEN")
        if not token:
            raise ValueError("HUGGINGFACE_API_TOKEN not set")

        # Remove misleading corporate proxy env that breaks HF URLs
        if os.getenv("HTTPS_PROXY", "").startswith("http://proxy_host"):
            os.environ.pop("HTTPS_PROXY", None)

        self.client = InferenceClient(token=token)
        self.model = "meta-llama/Llama-3.2-3B-Instruct"

    def generate_introduction(self, ranked_articles: List) -> EmailIntroduction:
        """Generate personalized greeting and introduction using HuggingFace LLM."""
        user_name = self.user_profile.get("name", "User")
        current_date = datetime.now().strftime("%B %d, %Y")

        if not ranked_articles:
            return EmailIntroduction(
                greeting=f"Hey {user_name}, here is your daily digest of AI news for {current_date}.",
                introduction="No articles were ranked today."
            )

        top_articles = ranked_articles[:10]
        article_summaries = "\n".join([
            f"{idx + 1}. {article.title if hasattr(article, 'title') else article.get('title', 'N/A')} "
            f"(Score: {article.relevance_score if hasattr(article, 'relevance_score') else article.get('relevance_score', 0):.1f}/10)"
            for idx, article in enumerate(top_articles)
        ])

        user_prompt = f"""{EMAIL_PROMPT}

Create an email introduction for {user_name} for {current_date}.

Top 10 ranked articles:
{article_summaries}

Generate a greeting and a 2-3 sentence introduction that previews these articles.
Format your response EXACTLY as:
GREETING: [your greeting here]
INTRODUCTION: [your introduction here]"""

        try:
            logger.info("Generating email introduction via HuggingFace LLM...")
            response = self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=200,
                temperature=0.7,
            )
            raw = response.choices[0].message.content.strip()
            logger.info(f"LLM response: {raw[:150]}...")

            # Parse the response
            greeting = f"Hey {user_name}, here is your daily digest of AI news for {current_date}."
            introduction = "Here are the top 10 AI news articles ranked by relevance to your interests."

            if "GREETING:" in raw and "INTRODUCTION:" in raw:
                parts = raw.split("INTRODUCTION:")
                greeting_part = parts[0].replace("GREETING:", "").strip()
                intro_part = parts[1].strip() if len(parts) > 1 else introduction
                if greeting_part:
                    greeting = greeting_part
                if intro_part:
                    introduction = intro_part
            elif raw:
                # Fallback: use first sentence as greeting, rest as introduction
                sentences = raw.split(". ")
                if len(sentences) >= 2:
                    greeting = sentences[0] + "."
                    introduction = ". ".join(sentences[1:])
                else:
                    introduction = raw

            # Ensure greeting includes user name
            if user_name not in greeting:
                greeting = f"Hey {user_name}, here is your daily digest of AI news for {current_date}."

            return EmailIntroduction(greeting=greeting, introduction=introduction)

        except Exception as e:
            logger.error(f"Error generating introduction: {e}")
            return EmailIntroduction(
                greeting=f"Hey {user_name}, here is your daily digest of AI news for {current_date}.",
                introduction="Here are the top 10 AI news articles ranked by relevance to your interests."
            )

    def create_email_digest(self, ranked_articles: List[dict], limit: int = 10) -> EmailDigest:
        """Create email digest with introduction and ranked articles."""
        top_articles = ranked_articles[:limit]
        introduction = self.generate_introduction(top_articles)

        return EmailDigest(
            introduction=introduction,
            ranked_articles=top_articles
        )

    def create_email_digest_response(
        self,
        ranked_articles: List[RankedArticleDetail],
        total_ranked: int,
        limit: int = 10
    ) -> EmailDigestResponse:
        """Create full email digest response with article details."""
        top_articles = ranked_articles[:limit]
        introduction = self.generate_introduction(top_articles)

        return EmailDigestResponse(
            introduction=introduction,
            articles=top_articles,
            total_ranked=total_ranked,
            top_n=limit
        )
