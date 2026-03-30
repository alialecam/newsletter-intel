# Newsletter Intelligence Aggregator - Cursor Rules

This document provides guidance for AI assistants working on this codebase. It covers architecture decisions, coding patterns, and domain knowledge.

## Project Purpose

This tool aggregates tech/media newsletters for Shopify Communications, extracting themes, surfacing Shopify mentions, and identifying trend-jacking opportunities. The audience is non-technical Communications staff who need to stay informed about the ecosystem.

## Architecture Decisions

### Email Fetching Strategy
- **Dual-source approach**: Fetch by sender filter AND by Gmail label
- Rationale: Allows adding new sources without code changes (just move to "newsletters" folder)
- Deduplication by message ID prevents duplicates

### AI Summarization
- **Model**: Claude (Anthropic) - chosen for structured output quality
- **Anti-hallucination**: Strict prompting that requires source citations for every claim
- All quotes must be exact, all links must be real

### Output Format
- **Primary**: Slack with Blocks API for rich formatting
- **Secondary**: Markdown archive for historical reference
- Link unfurling disabled to keep summaries clean

## Adding New Newsletter Sources

### Method 1: Gmail Label (Recommended)
Simply add emails to the "newsletters" label in Gmail. They'll be picked up automatically.

### Method 2: Sender Filter
Edit `config/config.yaml` and add to the `sender_query`:

```yaml
gmail:
  sender_query: >
    from:(existing@source.com OR 
    new@source.com)
```

### Method 3: Source Metadata
For display names and categories, add to `config/sources.yaml`:

```yaml
sources:
  - name: "Display Name"
    email: "email@source.com"
    category: "tech-business"
    url: "https://source.com/"
```

## Prompt Engineering Guidelines

### Summarization Prompts

When modifying `config/prompts/summarize.txt`:

1. **Always require source citations** - Every claim must link to source material
2. **Explicit over implicit** - Tell Claude exactly what format you want
3. **Negative instructions matter** - "Do NOT hallucinate" is important
4. **Use JSON output** - Structured output is more reliable than freeform

### Anti-Hallucination Patterns

Good:
```
ONLY extract information that is EXPLICITLY present in the source material.
Every claim must have a source attribution.
If uncertain whether something was mentioned, DO NOT include it.
```

Bad:
```
Summarize the key points.  # Too vague, allows inference
```

### Theme Extraction

- Require 2-3 sentence summaries (not bullet points)
- Ask for the "so what" - why does this theme matter?
- Sort by mention count for relevance

### Shopify Mentions

- Always surface ALL mentions, even single occurrences
- Include full context (2-3 sentences)
- Capture exact quotes when available
- Note sentiment (positive/neutral/negative)

### Trend-Jack Opportunities

- Request specific angles, not vague suggestions
- Include recommended outlet with rationale
- Consider audience fit (Stratechery = strategy, Lenny = product, etc.)

## Code Style Guidelines

### Python Style
- Type hints for all function signatures
- Docstrings for public methods
- `dataclass` for structured data
- Path objects over string paths

### Error Handling
- Graceful degradation - if one email fails, continue with others
- Log errors but don't crash the pipeline
- Return empty/default structures on failure

### Configuration
- Environment variables for secrets (API keys, tokens)
- YAML files for non-sensitive config
- Sensible defaults for all optional settings

## Common Tasks

### Testing Locally

```bash
# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Run Gmail OAuth setup
python -m src.gmail_fetcher

# Run full pipeline
python -m src.main
```

### Debugging Email Parsing

```python
from src.gmail_fetcher import GmailFetcher
from src.content_parser import ContentParser
import yaml

# Load config
with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

# Fetch emails
fetcher = GmailFetcher(config)
fetcher.authenticate()
emails = fetcher.fetch_emails(max_results=5)

# Parse one email
parser = ContentParser()
parsed = parser.parse_email(emails[0])
print(parsed.clean_text[:500])
```

### Testing Slack Output

```python
from src.slack_publisher import SlackPublisher

# Test with mock analysis
mock_analysis = {
    "themes": [{"title": "Test", "mention_count": 1, "summary": "Test summary", "sources": []}],
    "shopify_mentions": [],
    "sources_processed": []
}

publisher = SlackPublisher(config)
publisher.publish(mock_analysis)
```

## Memory: Past Decisions

### 2026-02-12: Initial Implementation
- Chose Claude over GPT-4 for better structured output
- Dual Gmail fetch strategy for flexibility
- Slack Blocks API for rich formatting without unfurls
- 3-day cadence as default (configurable)

### Newsletter Source Selection
Current sources focus on:
- Tech strategy (Stratechery, Benedict Evans)
- Tech business (Big Technology, Not Boring)
- AI developments (Axios AI+, Superhuman, TLDR)
- Product/UX (Lenny's Newsletter)
- Policy/platforms (Platformer)

## File Reference

| File | Purpose |
|------|---------|
| `src/gmail_fetcher.py` | Gmail API OAuth + email fetching |
| `src/content_parser.py` | HTML/text extraction, link preservation |
| `src/theme_analyzer.py` | Claude API integration, theme extraction |
| `src/slack_publisher.py` | Slack Blocks formatting + posting |
| `src/main.py` | Pipeline orchestration, state management |
| `config/config.yaml` | Main configuration |
| `config/sources.yaml` | Newsletter source metadata |
| `config/prompts/summarize.txt` | Claude prompt template |
