# Newsletter Intelligence Aggregator

A tool that automatically aggregates newsletters, extracts key themes, identifies brand mentions, and suggests trend-jacking opportunities—then posts formatted summaries to Slack.

## What It Does

When triggered, this tool:
1. **Fetches newsletters** from Gmail (configurable sources)
2. **Analyzes content** with Claude AI to extract:
   - Key themes with narrative summaries
   - Brand/company mentions with sentiment
   - Notable quotes with attribution
   - Trend-jacking opportunities with recommended media outlets
   - People and companies mentioned
3. **Posts a formatted summary** to a Slack channel

## Example Output

The tool produces Slack messages with:
- 📊 **Themes** - Top narratives across all newsletters with mention counts
- 🏷️ **Brand Mentions** - Every mention of your company with context and sentiment
- 💬 **Notable Quotes** - Key quotes with attribution
- 🎯 **Trend-Jack Opportunities** - Suggested angles + best outlets to pitch

---

## Quick Start (Using Cursor + MCP)

If you have Cursor IDE with Google Workspace MCP configured, you can run summaries immediately:

### 1. Clone the Repository
```bash
git clone <repo-url>
cd newsletter-intel
```

### 2. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Anthropic API (or Shopify AI Proxy)
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_BASE_URL=https://api.anthropic.com  # or proxy URL

# Slack
SLACK_CHANNEL_ID=C0XXXXXXX  # Your channel ID
```

### 4. Configure Newsletter Sources
Edit `config/config.yaml` to add your newsletter senders:
```yaml
gmail:
  sender_query: >-
    from:newsletter1@example.com OR
    from:newsletter2@example.com OR
    from:your-newsletters@substack.com
  label: newsletters
```

### 5. Run a Summary
From Cursor, ask the AI assistant:
> "summarize the last 3 days"

The assistant will fetch emails via MCP, analyze them, and post to Slack.

---

## Full Setup (Automated Slack Commands)

For self-service `/summarize` commands in Slack, complete these additional steps:

### Step 1: Gmail OAuth Setup (~5 min)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project called `newsletter-intel`
3. Enable the **Gmail API**
4. Configure OAuth consent screen (Internal for workspace)
5. Create OAuth credentials (Desktop app)
6. Download `client_secret.json` to `credentials/` folder
7. Run authorization:
   ```bash
   python -c "from newsletter_analyzer import get_gmail_service; get_gmail_service()"
   ```

### Step 2: Create Slack App (~5 min)

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create New App → From scratch
3. Name: `Newsletter Intel Bot`
4. Add Bot Token Scopes: `chat:write`, `commands`
5. Install to Workspace
6. Copy **Bot User OAuth Token** and **Signing Secret**

### Step 3: Deploy Server (~5 min)

Deploy to Railway, Render, or Heroku:

```bash
# Railway example
railway login
railway init
railway up
```

Set environment variables:
```
ANTHROPIC_API_KEY=...
ANTHROPIC_BASE_URL=...
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_CHANNEL_ID=C0XXXXXXX
```

### Step 4: Configure Slash Command

1. In your Slack app settings, go to **Slash Commands**
2. Create New Command:
   - Command: `/summarize`
   - Request URL: `https://YOUR-DEPLOYED-URL/slack/summarize`
   - Description: `Summarize newsletters from the last X days`
   - Usage Hint: `[days]`

### Step 5: Test It!

In your Slack channel, type:
```
/summarize 5
```

---

## Configuration

### Newsletter Sources (`config/config.yaml`)

```yaml
schedule:
  cadence_days: 3

gmail:
  sender_query: >-
    from:lenny@substack.com OR
    from:newsletter@techmeme.com OR
    from:dan@tldrnewsletter.com
  label: newsletters

claude:
  model: claude-sonnet-4-20250514
  max_tokens: 8192

slack:
  unfurl_links: false
  unfurl_media: false

brands_to_highlight:
  - "Your Company"
  - "Your Product"
```

### Analysis Prompt (`config/prompts/summarize.txt`)

The prompt template controls what Claude extracts. Key sections:
- Themes with narrative summaries
- Brand mentions with sentiment
- Notable quotes
- Trend-jack opportunities with outlet recommendations

---

## Project Structure

```
newsletter-intel/
├── config/
│   ├── config.yaml          # Main configuration
│   ├── sources.yaml         # Newsletter metadata
│   └── prompts/
│       └── summarize.txt    # Claude prompt template
├── credentials/             # Gmail OAuth (gitignored)
├── src/
│   ├── gmail_fetcher.py     # Gmail API integration
│   ├── content_parser.py    # Email parsing
│   ├── theme_analyzer.py    # Claude analysis
│   └── slack_publisher.py   # Slack posting
├── server.py                # Flask server for slash commands
├── newsletter_analyzer.py   # Main analysis module
├── requirements.txt
├── .env.example
├── Procfile                 # For deployment
└── SETUP.md                 # Detailed setup guide
```

---

## Customization

### Add New Newsletter Sources

1. Find the sender email (check email headers)
2. Add to `config/config.yaml`:
   ```yaml
   gmail:
     sender_query: >-
       from:existing@example.com OR
       from:new-newsletter@substack.com
   ```

### Change Target Brand

Edit `config/config.yaml`:
```yaml
brands_to_highlight:
  - "Your Company Name"
```

And update `config/prompts/summarize.txt` to reference your brand.

### Adjust Output Format

Edit `config/prompts/summarize.txt` to change:
- Number of themes extracted
- Quote selection criteria
- Trend-jack opportunity format
- Any custom sections

### Change Slack Formatting

Edit `src/slack_publisher.py` to modify the Slack Blocks layout.

---

## Prompt Template

Here's the core prompt used for analysis (from `config/prompts/summarize.txt`):

```
You are analyzing a batch of newsletter content for a Communications team. 
Your goal is to identify themes, surface brand mentions, and suggest trend-jacking opportunities.

CRITICAL RULES:
1. ONLY extract information that is EXPLICITLY present in the source material
2. NEVER hallucinate, invent, or infer content that isn't directly stated
3. Every claim must have a source attribution
4. Quotes must be exact - do not paraphrase and call it a quote
5. If uncertain whether something was mentioned, DO NOT include it

[... see full template in config/prompts/summarize.txt]
```

---

## Anti-Hallucination Safeguards

The tool includes strict guardrails to prevent AI hallucination:

1. **Explicit source attribution** - Every theme/quote must cite its source
2. **Exact quote matching** - Quotes must be verbatim, not paraphrased
3. **Uncertainty handling** - If unsure, omit rather than guess
4. **URL verification** - Only use URLs explicitly provided in content

---

## Troubleshooting

### "No newsletters found"
- Check your Gmail query in `config/config.yaml`
- Verify the sender emails are correct
- Ensure the date range has emails

### "Authentication error"
- Gmail: Re-run OAuth authorization
- Slack: Verify bot token is correct
- Anthropic: Check API key is valid

### "Analysis timeout"
- Reduce the number of newsletters analyzed
- Increase `max_tokens` if responses are truncated

### Slack message not posting
- Verify channel ID is correct (starts with `C`)
- Ensure bot is invited to the channel
- Check bot has `chat:write` permission

---

## Requirements

- Python 3.10+
- Gmail account with newsletters
- Anthropic API key (or compatible proxy)
- Slack workspace with bot permissions

---

## License

Internal use only. Adapt as needed for your organization.
