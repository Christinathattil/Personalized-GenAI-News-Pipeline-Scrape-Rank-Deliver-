"""Email digest processor - generates and sends daily AI news digest emails."""
from __future__ import annotations

import logging

from app.agents.email_agent import EmailAgent, RankedArticleDetail, EmailDigestResponse
from app.agents.news_curator import CuratorAgent
from app.profiles.profile import DEFAULT_USER_PROFILE
from app.database import get_session
from app.database.repository import Repository
from app.agents.email_sender import EmailSender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def generate_email_digest(hours: int = 24, top_n: int = 10) -> EmailDigestResponse:
    """Generate email digest from recent digests.

    Args:
        hours: Look back window for digests
        top_n: Number of top articles to include

    Returns:
        EmailDigestResponse with introduction and ranked articles
    """
    user_profile = DEFAULT_USER_PROFILE
    curator = CuratorAgent(user_profile)
    email_agent = EmailAgent(user_profile)

    with get_session() as session:
        repo = Repository(session)
        digest_rows = repo.get_recent_digests(hours=hours)

        # Convert ORM objects to dicts
        digests = [
            {
                "id": d.id,
                "title": d.title,
                "summary": d.summary,
                "url": d.url,
                "article_type": d.article_type,
            }
            for d in digest_rows
        ]

    total = len(digests)

    if total == 0:
        logger.warning(f"No digests found from the last {hours} hours")
        raise ValueError("No digests available")

    logger.info(f"Ranking {total} digests for email generation")
    ranked_articles = curator.rank_digests(digests)

    if not ranked_articles:
        logger.error("Failed to rank digests")
        raise ValueError("Failed to rank articles")

    logger.info(f"Generating email digest with top {top_n} articles")

    # Build RankedArticleDetail list by matching ranked articles with digest data
    article_details = []
    for a in ranked_articles:
        digest = next((d for d in digests if d["id"] == a.digest_id), None)
        if digest:
            article_details.append(
                RankedArticleDetail(
                    digest_id=a.digest_id,
                    rank=a.rank,
                    relevance_score=a.relevance_score,
                    reasoning=a.reasoning,
                    title=digest.get("title", ""),
                    summary=digest.get("summary", ""),
                    url=digest.get("url", ""),
                    article_type=digest.get("article_type", ""),
                )
            )

    email_digest = email_agent.create_email_digest_response(
        ranked_articles=article_details,
        total_ranked=len(ranked_articles),
        limit=top_n
    )

    logger.info("Email digest generated successfully")
    logger.info(f"\n=== Email Introduction ===")
    logger.info(email_digest.introduction.greeting)
    logger.info(f"\n{email_digest.introduction.introduction}")

    return email_digest


def digest_to_html(digest: EmailDigestResponse) -> str:
    """Generate modern, attention-grabbing HTML newsletter without altering content."""
    style_block = """
    <style>
      @media (prefers-color-scheme: dark) {
        body { background:#121212;color:#e0e0e0; }
        .card { background:#1e1e1e; }
        a { color:#4dabf7; }
      }
      body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; margin:0 auto; max-width:700px; padding:40px 20px; line-height:1.65; background:#fafafa; }
      h1 { font-size:2rem; margin:0 0 28px; text-align:center; background:linear-gradient(90deg,#007cf0,#00dfd8); -webkit-background-clip:text; color:transparent; }
      .card { border:1px solid #e1e1e1; border-radius:10px; padding:24px; margin-bottom:28px; box-shadow:0 2px 6px rgba(0,0,0,.05); transition:transform .2s ease; background:#ffffff; }
      .card:hover { transform:translateY(-4px); box-shadow:0 6px 14px rgba(0,0,0,.08); }
      .title { font-size:1.25rem; margin:0 0 14px; color:#111; font-weight:600; }
      .summary { margin:0 0 16px; color:#444; }
      a.read-more { display:inline-block; text-decoration:none; color:#007cf0; font-weight:600; }
      a.read-more:hover { text-decoration:underline; }
      .greeting { font-size:1.2rem; margin-bottom:10px; }
      .intro { color:#333; margin-bottom:30px; }
      hr.separator { border:none; border-top:2px dashed #ddd; margin:48px 0; }
    </style>
    """.strip()

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\">",
        "  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
        "  <title>Daily AI News Digest</title>",
        style_block,
        "</head>",
        "<body>",
        "  <h1>📰 Daily AI News Digest</h1>",
        f"  <p class=\"greeting\">{digest.introduction.greeting}</p>",
        f"  <p class=\"intro\">{digest.introduction.introduction}</p>",
        "  <hr class=\"separator\">",
    ]

    for art in digest.articles:
        html_parts.extend([
            "  <div class=\"card\">",
            f"    <div class=\"title\">👉 {art.title}</div>",
            f"    <p class=\"summary\">{art.summary}</p>",
            f"    <a class=\"read-more\" href=\"{art.url}\">Read more →</a>",
            "  </div>",
        ])

    html_parts.extend(["</body>", "</html>"])
    return "\n".join(html_parts)

def send_digest_email(hours: int = 24, top_n: int = 10) -> dict:
    """Generate and display email digest (email sending not implemented).

    Args:
        hours: Look back window for digests
        top_n: Number of top articles to include

    Returns:
        dict with success status and details
    """
    try:
        result = generate_email_digest(hours=hours, top_n=top_n)
        markdown_content = result.to_markdown()
        html_content = digest_to_html(result)

        subject = f"Daily AI News Digest - {result.introduction.greeting.split('for ')[-1] if 'for ' in result.introduction.greeting else 'Today'}"

        logger.info(f"Email subject: {subject}")
        logger.info(f"\n=== Markdown Content ===\n{markdown_content}")

        email_sent = False
        try:
            sender = EmailSender()
            sender.send_email(subject=subject, html_body=html_content, text_body=markdown_content)
            email_sent = True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

        return {
            "success": True,
            "subject": subject,
            "articles_count": len(result.articles),
            "markdown": markdown_content,
            "html": html_content,
            "digest": result,
            "email_sent": email_sent,
        }
    except ValueError as e:
        logger.error(f"Error generating email digest: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    result = send_digest_email(hours=24, top_n=10)
    if result["success"]:
        print("\n=== Email Digest Generated ===")
        print(f"Subject: {result['subject']}")
        print(f"Articles: {result['articles_count']}")
        print("\n=== Markdown Preview ===")
        print(result["markdown"])
    else:
        print(f"Error: {result['error']}")
