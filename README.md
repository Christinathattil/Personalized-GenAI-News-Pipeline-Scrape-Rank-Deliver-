# AI News Aggregator 📰🤖

**Turn the tidal wave of tech & AI news into a bite-sized daily digest.** The project scrapes multiple sources, enriches articles with transcripts & summaries, ranks them with embeddings, then emails a beautiful newsletter-style digest—all in < 10 minutes.

---

## 🚦 How It Works

```mermaid
flowchart TB
    S([Scheduler]) --> A[RSS & HTML Scraper]
    S --> A2[YouTube Captions Fetcher]
    A --> DB[(PostgreSQL – raw)]
    A2 --> B2[Transcript Cleaner]
    B2 --> DB
    DB --> C[NLP Summariser (OpenAI)]
    C --> E[Embeddings Generator]
    E --> R[Ranker]
    R --> F[Digest Formatter]
    F --> M[SMTP Email Sender]
```

*Repository mapping*
- `main.py` – orchestrates scheduler & CLI entry
- `app/scrapers/` – site-specific scrapers (`openai_news.py`, `anthropic_news.py`, `youtube.py`)
- `app/agents/news_curator.py` – enrichment & ranking
- `app/agents/digest_generator.py` – digest builder
- `app/agents/email_sender.py` – SMTP dispatch
- `app/database/models.py` – SQLAlchemy tables & relationships
- `app/database/` – connection, migrations, reset scripts


1. **Ingestion** ‑ RSS feeds, regular web pages and YouTube captions are fetched.
2. **Enrichment** ‑ Content is cleaned, summarised and embedded.
3. **Ranking** ‑ Cosine-similarity + recency scoring selects the *N* most relevant items.
4. **Digest** ‑ Markdown/HTML newsletter is generated.
5. **Delivery** ‑ `process_email` agent fires the email via SMTP.

---

## 🛠️  Tech Stack

| Layer            | Tooling                                                    |
|------------------|------------------------------------------------------------|
| Language         | Python 3.12                                               |
| Web / API        | FastAPI ＋ Uvicorn                                         |
| Data store       | PostgreSQL ＋ SQLAlchemy ORM                               |
| NLP / AI         | HuggingFace Token(Used here)/OpenAI API, Tiktoken, HuggingFace Embeddings               |
| Scraping         | BeautifulSoup4, Feedparser, YouTube-Transcript-API         |
| Async tricks     | `asyncio`, `asyncio-throttle`, `httpx`                     |
| Packaging        | PEP-621 (`pyproject.toml`) + `uv` for ultra-fast installs  |

---

## ⚡ Quick-Start (Local)

### 1. Clone & setup
```bash
# Clone
git clone https://github.com/<you>/ai-news-aggregator.git
cd ai-news-aggregator

# Python venv
python -m venv .venv && source .venv/bin/activate

# Faster pip (optional but recommended)
pip install uv
uv pip install -e .          # ≤10 s – installs deps in editable mode
```

### 2. Configure ENV
Copy the template and fill in the blanks:
```bash
cp .env.example .env  # then edit .env
# ──────────────────────────────
OPENAI_API_KEY="sk-..."
POSTGRES_URL="postgresql+psycopg2://user:pass@localhost:5432/news"
EMAIL_FROM="digest@your-domain.com"
EMAIL_TO="you@your-inbox.com"
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
HF_API_TOKEN="hf_..."
```

> **Note**: The pipeline defaults to using Hugging Face models via `HF_API_TOKEN`. If you prefer OpenAI models (e.g. GPT-4), simply leave `HF_API_TOKEN` blank and supply `OPENAI_API_KEY` instead.

Optional proxy for YouTube captions:
```bash
export HTTPS_PROXY="http://username:password@proxy_host:proxy_port"
```

### 3. Initialise database
```bash
python -m app.db.init
```

### 4. Run some agents!
```bash
# One-off 24-hour digest (default top-10)
uv run python main.py --generate-digests --hours 24

# Curate + rank but don’t email
uv run python -m app.agents.news_curator

# Send last 12 h, top-5 articles
uv run python -m app.agents.processors.process_email --hours 12 --top_n 5
```

### 5. Schedule it
```bash
# Every 24 h (crontab-free) – persists until interrupted
python -m main --schedule

# Custom – every 6 h, stop after 3 cycles
python -m main --interval 6 --stop-after 3
```

---

## 🌐 Running the API Server (optional)
```bash
uvicorn app.main:app --reload --port 8000
# Swagger UI ⇒ http://localhost:8000/docs
```

---

## 📈 Extended Architecture
```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Scheduler
  participant Scraper
  participant Curator
  participant Ranker
  participant Emailer
  User->>Scheduler: starts `main.py --schedule`
  Scheduler->>Scraper: fetch feeds
  Scraper->>Curator: cleaned articles
  Curator->>Ranker: summarised + embedded
  Ranker->>Emailer: top-N digest payload
  Emailer-->>User: glossy newsletter ✉️
```

---

## 🤝 Contributing
1. Fork ➡️ branch ➡️ PR.
2. Run `pre-commit install` for black, isort & flake8.
3. Write tests under `tests/` (pytest).

---

## 📄 License
MIT © 2026 Christina Thattil

