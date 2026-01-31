"""Predefined interests with hierarchical tagging."""
from __future__ import annotations

# 20 AI-related interests organized by category
# Format: (tag, display_name, parent_tag or None)
INTERESTS = [
    # Core AI/ML
    ("machine_learning", "Machine Learning", None),
    ("deep_learning", "Deep Learning", "machine_learning"),
    ("neural_networks", "Neural Networks", "machine_learning"),
    
    # Generative AI
    ("generative_ai", "Generative AI", None),
    ("large_language_models", "Large Language Models (LLMs)", "generative_ai"),
    ("text_to_image", "Text-to-Image Models", "generative_ai"),
    ("ai_agents", "AI Agents & Assistants", "generative_ai"),
    
    # Applications
    ("nlp", "Natural Language Processing", None),
    ("computer_vision", "Computer Vision", None),
    ("robotics", "Robotics & Automation", None),
    ("autonomous_vehicles", "Autonomous Vehicles", "robotics"),
    
    # Industry & Business
    ("ai_startups", "AI Startups & Funding", None),
    ("enterprise_ai", "Enterprise AI Solutions", None),
    ("ai_tools", "AI Tools & Productivity", None),
    
    # Research & Ethics
    ("ai_research", "AI Research Papers", None),
    ("ai_safety", "AI Safety & Alignment", None),
    ("ai_ethics", "AI Ethics & Regulation", None),
    
    # Platforms & Infrastructure
    ("cloud_ai", "Cloud AI Services", None),
    ("open_source_ai", "Open Source AI", None),
    ("ai_hardware", "AI Hardware & Chips", None),
]


def get_interests_for_seeding() -> list[dict]:
    """
    Get interests formatted for database seeding.
    
    Returns list of dicts with: tag, display_name, parent_tag
    """
    return [
        {"tag": tag, "display_name": display_name, "parent_tag": parent_tag}
        for tag, display_name, parent_tag in INTERESTS
    ]


def get_interest_display_list() -> list[dict]:
    """
    Get interests formatted for frontend display.
    
    Returns list of dicts with: tag, display_name, category
    """
    result = []
    for tag, display_name, parent_tag in INTERESTS:
        result.append({
            "tag": tag,
            "display_name": display_name,
            "is_subcategory": parent_tag is not None,
            "parent_tag": parent_tag,
        })
    return result
