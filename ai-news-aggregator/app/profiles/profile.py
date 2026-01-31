from pydantic import BaseModel
from typing import List, Dict

class UserPreferences(BaseModel):
    """User preferences for content filtering."""
    prefer_practical: bool = True
    prefer_technical_depth: bool = True
    prefer_research_breakthroughs: bool = True
    prefer_production_focus: bool = True
    avoid_marketing_hype: bool = True

class UserProfile(BaseModel):
    """Represents the end-user interests used for curation."""

    name: str = "Christina"
    title: str = "AI Engineer & Researcher"
    background: str = (
        "Experienced AI engineer with deep interest in practical AI applications, "
        "research breakthroughs, and production-ready systems."
    )
    expertise_level: str = "Advanced"
    interests: List[str] = [
        "Large Language Models (LLMs) and their applications",
        "Retrieval-Augmented Generation (RAG) systems",
        "AI agent architectures and frameworks",
        "Multimodal AI and vision-language models",
        "AI safety and alignment research",
        "Production AI systems and MLOps",
        "Real-world AI applications and case studies",
        "Technical tutorials and implementation guides",
        "Research papers with practical implications",
        "AI infrastructure and scaling challenges",
    ]
    preferences: UserPreferences = UserPreferences()

DEFAULT_USER_PROFILE = UserProfile()
