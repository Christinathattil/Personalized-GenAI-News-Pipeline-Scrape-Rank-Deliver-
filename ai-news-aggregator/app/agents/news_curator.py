"""News Curator Agent - ranks digests using HuggingFace LLM."""
from __future__ import annotations

import os
import json
import re
import logging
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field
from huggingface_hub import InferenceClient

from app.database import get_session
from app.database.repository import Repository
from app.profiles.profile import DEFAULT_USER_PROFILE, UserProfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CURATOR_PROMPT = """You rank AI news for a user. Score each article 0-10 based on relevance to user interests.

Output ONLY a JSON array. No other text. Format:
[{"digest_id":"ID","relevance_score":8.5,"rank":1,"reasoning":"why"}]"""


class RankedArticle(BaseModel):
    digest_id: str = Field(description="The digest ID")
    relevance_score: float = Field(ge=0.0, le=10.0)
    rank: int = Field(ge=1)
    reasoning: str = Field(description="Brief explanation")


class RankedDigestList(BaseModel):
    articles: List[RankedArticle]


class CuratorAgent:
    """Ranks digests using HuggingFace text-generation model."""

    def __init__(self, user_profile: UserProfile | None = None):
        self.profile = user_profile or DEFAULT_USER_PROFILE
        token = os.getenv("HUGGINGFACE_API_TOKEN")
        # Disable placeholder proxy that causes URL parse errors
        proxy = os.getenv("HTTPS_PROXY")
        if proxy and "proxy_host" in proxy:
            os.environ.pop("HTTPS_PROXY", None)
        if not token:
            raise ValueError("HUGGINGFACE_API_TOKEN not set")
        self.client = InferenceClient(token=token)
        self.model = "meta-llama/Llama-3.2-3B-Instruct"

    def _build_system_prompt(self) -> str:
        interests = "\n".join(f"- {i}" for i in self.profile.interests)
        prefs = self.profile.preferences.model_dump()
        pref_text = "\n".join(f"- {k}: {v}" for k, v in prefs.items())
        return f"""{CURATOR_PROMPT}

User Profile:
Name: {self.profile.name}
Title: {self.profile.title}
Background: {self.profile.background}
Expertise: {self.profile.expertise_level}

Interests:
{interests}

Preferences:
{pref_text}"""

    def rank_digests(self, digests: List[dict]) -> List[RankedArticle]:
        if not digests:
            return []

        # Score each digest individually for reliability
        scored = []
        for d in digests:
            score, reason = self._score_single(d)
            scored.append((d, score, reason))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return [
            RankedArticle(
                digest_id=item[0]["id"],
                relevance_score=item[1],
                rank=i + 1,
                reasoning=item[2]
            )
            for i, item in enumerate(scored)
        ]

    def _score_single(self, digest: dict) -> tuple[float, str]:
        """Score a single digest using LLM."""
        prompt = f"""Score this article for relevance to the user (0-10). Reply with ONLY: score|reason

User interests: {', '.join(self.profile.interests[:5])}

Article: {digest['title']}
Summary: {digest['summary'][:200]}"""

        try:
            logger.info(f"Calling LLM for: {digest['title'][:40]}...")
            response = self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1,
            )
            raw = response.choices[0].message.content.strip()
            logger.info(f"LLM response: {raw[:80]}")
            # Parse "score|reason" format
            if "|" in raw:
                parts = raw.split("|", 1)
                score = float(re.search(r"[\d.]+", parts[0]).group())
                reason = parts[1].strip()[:100]
                return min(10.0, max(0.0, score)), reason
            # Try to extract just a number
            match = re.search(r"(\d+\.?\d*)", raw)
            if match:
                return min(10.0, max(0.0, float(match.group(1)))), "LLM scored"
            logger.warning(f"Could not parse LLM response: {raw}")
        except Exception as e:
            logger.error(f"LLM score failed for {digest['id']}: {e}")

        # Fallback to keyword scoring
        return self._keyword_score(digest)

    def _keyword_score(self, digest: dict) -> tuple[float, str]:
        """Keyword-based scoring fallback."""
        interests = [kw.lower() for kw in self.profile.interests]
        text = f"{digest['title']} {digest['summary']}".lower()
        hits = sum(1 for kw in interests if kw in text)
        score = min(10.0, max(1.0, hits * 1.5))
        return score, "Keyword match"

    def _fallback_rank(self, digests: List[dict]) -> List[RankedArticle]:
        """Keyword-based fallback when LLM fails."""
        interests = [kw.lower() for kw in self.profile.interests]
        scored = []
        for d in digests:
            text = f"{d['title']} {d['summary']}".lower()
            hits = sum(1 for kw in interests if kw in text)
            score = min(10.0, max(1.0, hits * 1.5))
            scored.append((d, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            RankedArticle(
                digest_id=d["id"],
                relevance_score=s,
                rank=i + 1,
                reasoning="Keyword match fallback"
            )
            for i, (d, s) in enumerate(scored)
        ]


def curate_digests(hours: int = 24) -> dict:
    """Main entry point for curation."""
    curator = CuratorAgent()

    with get_session() as session:
        repo = Repository(session)
        digest_rows = repo.get_recent_digests(hours)

    digests = [
        {"id": d.id, "title": d.title, "summary": d.summary, "article_type": d.article_type, "url": d.url}
        for d in digest_rows
    ]
    total = len(digests)

    if total == 0:
        logger.warning(f"No digests found from the last {hours} hours")
        return {"total": 0, "ranked": 0}

    logger.info(f"Curating {total} digests for {curator.profile.name}")
    ranked = curator.rank_digests(digests)

    if not ranked:
        logger.error("Failed to rank digests")
        return {"total": total, "ranked": 0}

    logger.info(f"Ranked {len(ranked)} articles")
    print("\n=== Top Ranked Articles ===")
    for article in ranked[:10]:
        digest = next((d for d in digests if d["id"] == article.digest_id), None)
        if digest:
            print(f"\nRank {article.rank} | Score: {article.relevance_score:.1f}/10")
            print(f"Title: {digest['title']}")
            print(f"Type: {digest['article_type']}")
            print(f"Link: {digest.get('url', 'N/A')}")
            print(f"Reasoning: {article.reasoning}")

    return {
        "total": total,
        "ranked": len(ranked),
        "articles": [a.model_dump() for a in ranked],
    }


if __name__ == "__main__":
    result = curate_digests(hours=24)
    print(f"\n=== Curation Results ===")
    print(f"Total digests: {result['total']}")
    print(f"Ranked: {result['ranked']}")
