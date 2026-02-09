# AI News Digest Pipeline 📬🤖

Turns the daily AI fire-hose into a short, emoji-laced newsletter delivered to your inbox. 📰🤖

**Turn the tidal wave of tech & AI news into a bite-sized daily digest.** The project scrapes multiple sources, enriches articles with transcripts & summaries, ranks them with embeddings, then emails a beautiful newsletter-style digest—all in < 10 minutes.


## ✨ Why it's Cool
- Zero-FOMO: daily AI digest lands in your inbox before coffee ☕
- Full pipeline: scrape → summarise → rank → Gen-Z email with emoji
- Llama-3 powered, no OpenAI key needed
- One-command Docker spin-up
- Transparent relevance score for every article

---

## ⚙️ High-Level Architecture
```mermaid
flowchart LR
    subgraph Daily run
        A["Scrapers (RSS & YouTube)"] --> B[(PostgreSQL)]
        B --> C[Digest Generator 📝]
        C --> D["Relevance Ranker ⭐"]
        D --> E[Email Formatter ✉️]
        E --> F[SMTP Sender 📤]
        F --> G[Inbox 📥]
    end
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

## �️ Directory Layout (excerpt)
```text
ai-news-aggregator/
├── app/
│   ├── agents/            # HF/OpenAI powered helpers
│   ├── scrapers/          # YouTube + RSS parsers
│   ├── database/          # SQLAlchemy models & helpers
│   └── config.py          # Channel IDs etc.
├── frontend/              # React + Tailwind sign-up UI
├── docker/                # compose.yml + env templates
├── main.py                # CLI orchestrator
└── README.md
```

## 🧰 Tech Stack
| Layer | Tools |
|-------|-------|
| Language | Python 3.12 · TypeScript/JS (frontend) |
| AI / NLP | Hugging Face Inference API (Llama-3) |
| Web / API | FastAPI · Uvicorn |
| Data | PostgreSQL · SQLAlchemy ORM |
| Scraping | feedparser · youtube-transcript-api |
| Mail | Gmail SMTP via `smtplib` |
| Dev Ops | Docker Compose · GitHub Actions (optional) |

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

## 🚀 Run Locally in 3 Steps
```bash
# 1. Clone + install deps
$ git clone https://github.com/<you>/ai-news-aggregator.git
$ cd ai-news-aggregator
$ python -m venv .venv && source .venv/bin/activate
$ pip install uv && uv sync

# 2. Spin up Postgres (Docker)
$ docker compose -f docker/docker-compose.yml up -d

# 3. Configure env & fire the pipeline
$ cp app/.env.example app/.env  &&  cp docker/example.env docker/.env
$ nano app/.env   # fill SMTP & HF_API_TOKEN
$ python -m app.daily_runner --hours 24 --top 5
```

### 1. Clone & set-up
```bash
git clone https://github.com/<you>/ai-news-aggregator.git
cd ai-news-aggregator

# Create & activate virtual-env
python -m venv .venv && source .venv/bin/activate

# Install dependencies (ultra-fast)
pip install uv
uv sync                      # installs from pyproject.toml in a few seconds
```

### 2. Configure environment
```bash
# Base env for Python services
cp app/.env.example app/.env      
# If you’ll run docker-compose
cp docker/example.env docker/.env
```
Edit the new files and provide secrets:
```dotenv
# ─── PostgreSQL (local Docker) ─────────────────────
POSTGRES_USER=ainews
POSTGRES_PASSWORD=ainews_pw
POSTGRES_DB=ainews_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# ─── Email (Gmail SMTP example) ────────────────────
SMTP_USER=your@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop   # 16-char Gmail App Password
EMAIL_FROM="AI News Digest <your@gmail.com>"
EMAIL_TO="recipient@example.com"

# ─── AI APIs (choose at least one) ────────────────
HF_API_TOKEN="hf_..."          # Hugging Face Inference
OPENAI_API_KEY="sk-..."        # OpenAI (optional alternative)
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

<!-- highlights moved to top -->
- Fully automated scrape → summarise → rank → email flow
- Gen-Z styled newsletter with emoji, bullet-point digests & relevance scores
- Hugging Face LLMs only – no OpenAI key required
- Scores & sources surfaced for transparency
- 100 % Python backend + modern React sign-up frontend

## 🔮 Future Improvements
- Vector-DB caching for faster similarity ranking
- Web-based dashboard to browse past digests
- Slack / Discord delivery channels
- Kubernetes deployment manifests
- Automatic language detection + translation

### Local Docker Compose
```bash
cd Personalized-GenAI-News-Pipeline-Scrape-Rank-Deliver-/ai-news-aggregator
cp docker/example.env docker/.env   # review & edit variables
docker compose --profile all up --build
```
This spins up PostgreSQL, FastAPI API, worker processes and the React dashboard—everything wired together just like production.

### Render.com
1. Create a **Blueprint** service and point it to this repo.
2. Add env vars from `.env` / `docker/example.env` in the Render dashboard.
3. Set **Build Command**: `docker compose --profile api build`.
4. Set **Start Command**: `docker compose --profile api up -d`.

### Directory Layout (excerpt)
```text
.
├── Personalized-GenAI-News-Pipeline-Scrape-Rank-Deliver-
│   └── ai-news-aggregator
│       ├── app/            # backend Python package
│       │   ├── agents/
│       │   ├── scrapers/
│       │   └── database/
│       ├── docker/         # compose, env examples
│       ├── frontend/       # React UI
│       ├── main.py         # CLI entrypoint
│       └── pyproject.toml
├── README.md
```

---

## �📈 Extended Architecture
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

