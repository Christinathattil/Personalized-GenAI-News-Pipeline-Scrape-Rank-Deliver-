Set an environment variable before running the scraper:
bash
export HTTPS_PROXY="http://username:password@proxy_host:proxy_port"
The scraper automatically passes that proxy dict to YouTubeTranscriptApi.fetch() and .list() calls, so all transcript requests go through the proxy.


# DIGEST AGENT

uv run python main.py --generate-digests --hours 24                

### NEWS CURATOR AND RANKING AGENT

uv run python -m app.agents.news_curator

### EMAIL AGENT

uv run python -m app.agents.processors.process_email

# Last 12 hours, top 5 articles
uv run python -m app.agents.processors.process_email --hours 12 --top_n 5





# 1 – activate the project’s venv (skip if your prompt already shows “(.venv)”)
source .venv/bin/activate

# 2 – install the package **inside that same venv**
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy   # clears bad proxy vars
pip install -e .

# 3 – generate + send the digest
python -m app.agents.processors.process_email --hours 24 --top_n 10





# from project root (ai-news-aggregator/)
python -m main                 # one-off           
python -m main --schedule      # repeats every 24h 
python -m main --interval 6    # one-off, 6-hour window 

# Custom frequency: every 6 h, stop after 3 cycles
python -m main --interval 6 --stop-after 3


# 🤖 AI News Aggregator

> **Intelligent AI News Pipeline** that scrapes, ranks, and delivers personalized AI news digests straight to your inbox.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://postgresql.org)

## What It Does

The AI News Aggregator is a sophisticated pipeline that:

1. **Scrapes** AI news from multiple sources (OpenAI blog, Anthropic updates, YouTube transcripts)
2. **Ranks** content using AI-powered relevance scoring
3. **Generates** concise summaries using HuggingFace models
4. **Delivers** personalized email digests
5. **Serves** content via a modern web interface

---

## How It Works

### System Architecture

```mermaid
graph TD
    A[News Sources] --> B[Scrapers]
    B --> C[Database]
    C --> D[AI Ranking Engine]
    D --> E[Summary Generator]
    E --> F[Email Service]
    E --> G[Web API]
    F --> H[User Inbox]
    G --> I[React Frontend]
    
    subgraph "Data Sources"
        A1[OpenAI Blog]
        A2[Anthropic News]
        A3[YouTube Channels]
    end
    
    subgraph "Processing Pipeline"
        B1[Content Scraping]
        D1[Relevance Scoring]
        E1[Text Summarization]
    end
    
    subgraph "Delivery Channels"
        F1[SMTP Email]
        G1[REST API]
    end
    
    A --> A1
    A --> A2
    A --> A3
    B --> B1
    D --> D1
    E --> E1
    F --> F1
    G --> G1
```

### Data Flow

```mermaid
flowchart LR
    S[Sources] --> SC[Scraping]
    SC --> DB[(PostgreSQL)]
    DB --> RK[AI Ranking]
    RK --> SG[Summarization]
    SG --> OUT[Output]
    
    OUT --> E[ Email]
    OUT --> W[ Web]
    OUT --> API[ API]
```

### Core Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Scrapers** | BeautifulSoup4, YouTube API | Extract content from sources |
| **Database** | PostgreSQL + SQLAlchemy | Store articles and metadata |
| **AI Engine** | OpenAI API, HuggingFace | Rank and summarize content |
| **Email Service** | SMTP | Send personalized digests |
| **Web API** | FastAPI | RESTful backend service |
| **Frontend** | React + TypeScript | Modern web interface |

---

## Quick Start

### Prerequisites

- **Python 3.12+** 
- **PostgreSQL 13+**
- **Node.js 18+** (for frontend)
- **SMTP credentials** (for email delivery)
- **HuggingFace token** (for summarization models)

### 1. Clone & Setup

```bash
# Clone the repository
git clone <repository-url>
cd ai-news-aggregator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Environment Configuration

```bash
# Copy environment template
cp app/example.env app/.env

# Edit with your credentials
nano app/.env
```

**Required Environment Variables:**

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_news

# HuggingFace (for summarization)
HF_AUTH_TOKEN=your_hf_token_here

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL="AI News Digest <no-reply@yourdomain.com>"

# OpenAI (for ranking)
OPENAI_API_KEY=your_openai_key_here

# Web service
BASE_URL=http://localhost:8000
```

### 3. Database Setup

```bash
# Create database
createdb ai_news

# Run migrations (if using Alembic)
# alembic upgrade head
```

### 4. Run the Pipeline

```bash
# One-time run (last 24 hours, top 10 articles)
python -m main

# Custom time window
python -m main --hours 12 --top 5

# Schedule every 6 hours
python -m main --schedule --interval 6

# Run 3 times then stop
python -m main --schedule --interval 6 --stop-after 3
```

---

## Development Setup

### Backend Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run individual components
uv run python -m app.agents.news_curator          # News ranking
uv run python -m app.agents.digest_generator      # Generate digests
uv run python -m app.agents.processors.process_email  # Email processing
```

### Frontend Development

```bash
cd frontend
npm install
npm start  # Development server
npm run build  # Production build
```

### Using UV (Recommended)

```bash
# Install uv (if not already installed)
pip install uv

# Use uv for faster dependency management
uv run python -m main
uv run python -m app.agents.news_curator
```

---

## Manual Agent Execution

### News Curator & Ranking Agent
```bash
uv run python -m app.agents.news_curator
```

### Digest Generation Agent
```bash
# Generate digests for last 24 hours
uv run python main.py --generate-digests --hours 24
```

### Email Agent
```bash
# Send digest for last 12 hours, top 5 articles
uv run python -m app.agents.processors.process_email --hours 12 --top_n 5
```

---

## Configuration

### YouTube Channels

Edit `app/config.py` to add/remove YouTube channels:

```python
YOUTUBE_CHANNELS = [
    "UC_x5XG1OV2P6uZZ5FSM9Ttw",  # Dave Ebbelaar
    "UCZ50rYSkYQG31YDEJm9Di_g",  # Coursera
    # Add your channels here
]
```

### Proxy Support

For environments requiring proxy access:

```bash
# Set proxy environment variables
export HTTPS_PROXY="http://username:password@proxy_host:proxy_port"
export HTTP_PROXY="http://username:password@proxy_host:proxy_port"

# The scraper automatically uses these for YouTube API calls
```

---

## Docker Deployment

### Development

```bash
# Build and run all services
docker-compose up --build

# Individual services
docker-compose up api    # Backend only
docker-compose up frontend  # Frontend only
docker-compose up db     # Database only
```

### Production

```bash
# Production build
docker-compose -f docker-compose.prod.yml up -d
```

---

## Cloud Deployment (Render)

The project includes `render.yaml` for easy deployment on Render.com:

1. **Connect repository** to Render
2. **Add environment variables** in Render dashboard
3. **Deploy** - Render will automatically:
   - Build and deploy FastAPI backend
   - Build and deploy React frontend
   - Provision PostgreSQL database
   - Configure networking and health checks

---

## Project Structure

```
ai-news-aggregator/
├── app/                          # Core application
│   ├── agents/                   # AI agents for processing
│   │   ├── digest_generator.py   # Content summarization
│   │   ├── email_agent.py        # Email handling
│   │   └── news_curator.py       # News ranking
│   ├── scrapers/                 # Data collection
│   │   ├── anthropic_news.py     # Anthropic scraper
│   │   ├── openai_news.py        # OpenAI scraper
│   │   └── youtube.py            # YouTube transcript scraper
│   ├── database/                 # Database models & migrations
│   ├── services/                 # Business logic
│   └── config.py                 # Configuration
├── api/                          # FastAPI web service
│   ├── models.py                 # API models
│   ├── schemas.py                # Pydantic schemas
│   └── email_service.py          # Email endpoints
├── frontend/                     # React web interface
├── docker/                       # Docker configurations
├── main.py                       # CLI entry point
├── pyproject.toml                # Python dependencies
└── render.yaml                   # Render deployment config
```

---

## API Endpoints

### Health & Status
- `GET /api/health` - Service health check

### Email Management
- `POST /api/email/subscribe` - Subscribe to digests
- `POST /api/email/unsubscribe` - Unsubscribe
- `GET /api/email/confirm/{token}` - Confirm subscription

### Articles
- `GET /api/articles` - List articles
- `GET /api/articles/{id}` - Get article details

### Digests
- `GET /api/digests` - List digests
- `GET /api/digests/latest` - Latest digest

---

## Testing

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_scrapers.py
pytest tests/test_agents.py

# Run with coverage
pytest --cov=app tests/
```

---

## Monitoring & Logging

### Logging Configuration

The application uses structured logging with multiple levels:

```python
# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
logging.basicConfig(level=logging.INFO,
                   format="%(asctime)s · %(levelname)s · %(message)s")
```

### Monitoring Endpoints

- **Health checks**: `/api/health`
- **Metrics**: Available via logging output
- **Database status**: Check connection logs

---

## Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Guidelines

- Follow **PEP 8** for Python code
- Use **type hints** for all functions
- Write **tests** for new features
- Update **documentation** as needed

---

## Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check PostgreSQL is running
pg_ctl status

# Verify connection string
psql postgresql://user:password@localhost:5432/ai_news
```

**Email Sending Failures**
```bash
# Test SMTP credentials
python -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587).starttls()"
```

**YouTube API Issues**
```bash
# Set proxy if needed
export HTTPS_PROXY="http://proxy:port"
```

**HuggingFace Model Errors**
```bash
# Verify token has access to models
python -c "from huggingface_hub import HfApi; HfApi().whoami()"
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m main --hours 1
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **OpenAI** for GPT models and API
- **HuggingFace** for summarization models
- **BeautifulSoup** for web scraping
- **FastAPI** for the web framework
- **React** for the frontend interface

---

## Support

For issues and questions:

1. **Check** the troubleshooting section above
2. **Search** existing GitHub issues
3. **Create** a new issue with detailed information
4. **Join** our community discussions

---

*Built with for the AI community*
