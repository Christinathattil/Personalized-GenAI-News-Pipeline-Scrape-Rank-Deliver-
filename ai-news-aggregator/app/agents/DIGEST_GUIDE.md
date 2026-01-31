# Digest Generation Guide

This guide explains how to use the newly implemented Digest Generation Agent to automatically create summaries for all your scraped articles.

## Setup

### 1. Get a Hugging Face Token
1. Visit [Hugging Face](https://huggingface.co/) and create an account
2. Go to [Settings > Access Tokens](https://huggingface.co/settings/tokens)
3. Create a new token with "Read" permissions
4. Copy the token (starts with `hf_...`)

### 2. Configure Environment
Create a `.env` file in the project root:
```bash
HUGGINGFACE_API_TOKEN=hf_your_token_here
```

### 3. Create Database Tables
Run the migration to create the digest table:
```bash
uv run python -m app.database.migrate create
```

## Usage

### Basic Usage - Scrape + Generate Digests
```bash
# Scrape articles and generate digests in one command
uv run python main.py --generate-digests --hours 24
```

### Digest-Only Mode
```bash
# Only generate digests for existing articles
uv run python main.py --digest-only
```

### Force Regeneration
```bash
# Regenerate all digests (even for articles that already have them)
uv run python main.py --digest-only --force-digests
```

### Using the Standalone Digest Processor
```bash
# Process all pending articles
uv run python -m app.processors.digest_processor

# Show digest statistics
uv run python -m app.processors.digest_processor --stats

# Process only YouTube articles
uv run python -m app.processors.digest_processor --type youtube

# Force regenerate all digests
uv run python -m app.processors.digest_processor --force
```

## Features

### What Gets Processed
- **YouTube Videos**: Title, description, and transcript (if available)
- **OpenAI Articles**: Title, description, and markdown content
- **Anthropic Articles**: Title, description, and markdown content

### Digest Output
Each digest contains:
- **Title**: Clean, informative title (non-clickbait)
- **Summary**: 2-3 sentence concise summary
- **Metadata**: Links back to original article, creation timestamps

### AI Model
- Uses Facebook's BART-Large-CNN model via Hugging Face API
- Optimized for technical/AI content summarization
- Handles content truncation for long articles
- Includes retry logic for API reliability

## Database Schema

The `digests` table stores:
```sql
id (string, primary key)
article_type (string) -- 'youtube', 'openai', 'anthropic'
article_id (string)   -- FK to original article
url (string)          -- Article URL
title (string)        -- Generated title
summary (text)        -- Generated summary
created_at (datetime)
updated_at (datetime)
```

## Troubleshooting

### Common Issues

1. **"HUGGINGFACE_API_TOKEN not set"**
   - Ensure your .env file contains the token
   - Token must start with `hf_`

2. **"Model loading" errors**
   - The HuggingFace model may be cold-starting
   - The system includes automatic retry logic
   - Wait 10-20 seconds and try again

3. **"No articles found"**
   - Run scraping first: `uv run python main.py --hours 24`
   - Check if articles already have digests: use `--force-digests` to regenerate

4. **Database errors**
   - Run migration: `uv run python -m app.database.migrate create`
   - Ensure database is accessible

### Performance Tips
- Process articles in smaller batches for better reliability
- The system commits after each successful digest to prevent data loss
- Use `--type` filter for specific article types when testing

## Architecture

- **DigestGenerator**: Core AI agent using HuggingFace API
- **DigestProcessor**: Orchestrates processing of multiple articles
- **Repository**: Database operations for digests
- **Integration**: Seamlessly works with existing scraping pipeline
