# Quick Start Guide: Newsletter Intelligence in 10 Minutes

This guide gets you a working newsletter summarizer that posts to Slack—without deploying any servers.

---

## Prerequisites

- **Cursor IDE** with Google Workspace MCP enabled
- **Slack workspace** access
- **Anthropic API key** (or Shopify AI Proxy token)

---

## Step 1: Clone & Setup (2 min)

```bash
# Clone the repo
git clone <repo-url>
cd newsletter-intel

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

---

## Step 2: Configure Credentials (3 min)

Edit `.env` with your settings:

```env
# Anthropic API
# Option A: Direct Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_BASE_URL=https://api.anthropic.com

# Option B: Shopify AI Proxy
ANTHROPIC_API_KEY=shopify-eyJ...
ANTHROPIC_BASE_URL=https://proxy.shopify.ai/apis/anthropic

# Slack Channel ID
# Find it: Right-click channel → View channel details → scroll to bottom
SLACK_CHANNEL_ID=C0XXXXXXX
```

---

## Step 3: Configure Newsletter Sources (2 min)

Edit `config/config.yaml`:

```yaml
gmail:
  sender_query: >-
    from:lenny@substack.com OR
    from:dan@tldrnewsletter.com OR
    from:casey@platformer.news OR
    from:newsletter@techmeme.com OR
    from:your-favorite-newsletter@example.com
  label: newsletters

brands_to_highlight:
  - "Your Company Name"
```

---

## Step 4: Run Your First Summary (3 min)

Open Cursor and ask the AI assistant:

> "Summarize the last 3 days of newsletters and post to Slack"

Or be more specific:

> "Fetch newsletters from the last 5 days using gworkspace MCP, analyze them with Claude, and post the summary to my Slack channel"

The assistant will:
1. Fetch emails via Google Workspace MCP
2. Analyze content with Claude
3. Post formatted summary to your Slack channel

---

## That's It!

You now have a working newsletter intelligence tool. 

### To run future summaries:
Just ask in Cursor: "summarize the last X days"

### To add more newsletters:
Add sender emails to `config/config.yaml`

### To change the target brand:
Update `brands_to_highlight` in config

---

## What's in the Summary?

Each Slack post includes:

📊 **Themes** (sorted by frequency)
- Theme title with mention count
- 2-3 sentence narrative summary
- Source links

🏷️ **Brand Mentions**
- Every mention of your company
- Full context + sentiment
- Direct quotes when available

💬 **Notable Quotes**
- Key quotes with attribution
- Why each quote matters

🎯 **Trend-Jack Opportunities**
- Suggested angles
- Best outlet to pitch
- Why the outlet fits

---

## Next Steps

### Want automated Slack commands?
See `SETUP.md` for deploying the `/summarize` slash command.

### Want to customize the analysis?
Edit `config/prompts/summarize.txt` to change what Claude extracts.

### Want to use this prompt elsewhere?
See `REUSABLE_PROMPT.md` for a standalone prompt template.

---

## Troubleshooting

**"No newsletters found"**
- Check sender emails in config match your actual newsletter senders
- Verify the date range has emails in your inbox

**"Slack posting failed"**
- Verify channel ID is correct (starts with `C`)
- Ensure Slack MCP is authenticated

**"Claude analysis failed"**
- Check API key is valid
- Verify base URL is correct for your setup

---

## File Reference

| File | Purpose |
|------|---------|
| `.env` | Your credentials (gitignored) |
| `config/config.yaml` | Newsletter sources, settings |
| `config/prompts/summarize.txt` | Claude prompt template |
| `src/slack_publisher.py` | Slack message formatting |

---

## Support

Questions? Check the full `README.md` or `SETUP.md` for detailed documentation.
