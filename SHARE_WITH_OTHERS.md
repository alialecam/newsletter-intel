# Newsletter Intelligence Tool - Share Guide

## What This Tool Does

Automatically aggregates newsletters, extracts themes, identifies brand mentions, and posts formatted summaries to Slack.

**Input:** Your Gmail newsletters
**Output:** Slack summary with themes, quotes, and trend-jacking opportunities

---

## Files to Share

Share this entire `newsletter-intel/` folder. Key files:

| File | What It Does |
|------|--------------|
| `QUICK_START_GUIDE.md` | 10-minute setup for Cursor + MCP users |
| `README.md` | Full documentation |
| `SETUP.md` | Detailed setup for Slack slash commands |
| `REUSABLE_PROMPT.md` | Standalone prompt for any LLM |
| `config/config.yaml` | Newsletter sources configuration |
| `config/prompts/summarize.txt` | The analysis prompt template |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

---

## Three Ways to Use This

### 1. Quick Mode (Cursor + MCP)
**Best for:** Individual use, no server needed

Setup: 10 minutes
- Clone repo, install dependencies
- Add API keys to `.env`
- Ask Cursor: "summarize the last 3 days"

See: `QUICK_START_GUIDE.md`

### 2. Slash Command Mode
**Best for:** Team use, anyone can trigger from Slack

Setup: 20 minutes
- Complete Quick Mode setup
- Create Slack app
- Deploy server to Railway/Render
- Users type `/summarize 5` in Slack

See: `SETUP.md`

### 3. Prompt-Only Mode
**Best for:** Using with any LLM, no code needed

Setup: 2 minutes
- Copy prompt from `REUSABLE_PROMPT.md`
- Paste newsletter content
- Send to Claude/ChatGPT

See: `REUSABLE_PROMPT.md`

---

## Customization Checklist

When setting up for a new team:

- [ ] Update `brands_to_highlight` in `config/config.yaml`
- [ ] Add your newsletter sources to `gmail.sender_query`
- [ ] Set your Slack channel ID in `.env`
- [ ] Get Anthropic API key (or internal proxy token)
- [ ] (Optional) Customize prompt in `config/prompts/summarize.txt`

---

## Required Credentials

| Credential | Where to Get It |
|------------|-----------------|
| Anthropic API Key | anthropic.com or internal proxy |
| Slack Channel ID | Right-click channel → View details |
| Slack Bot Token | api.slack.com/apps (for slash commands) |
| Gmail OAuth | Google Cloud Console (for automated mode) |

---

## Example Output

The tool produces Slack messages like:

```
📰 Newsletter Intelligence | Feb 16-19, 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 KEY THEMES

🔹 AI coding tools transforming development (7 mentions)
   Claude Code now represents 4% of GitHub commits. Boris Cherny 
   claims "coding is solved." This signals a fundamental shift...
   Sources: Lenny's Newsletter, TLDR, Platformer

🔹 AI monetization strategies diverging (4 mentions)
   Perplexity abandons ads, OpenAI tests them, Anthropic stays 
   ad-free. The industry is splitting on how to monetize...
   Sources: Superhuman, Techmeme, TBPN

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ YOUR COMPANY MENTIONS

• TBPN: Listed as sponsor alongside MongoDB, CrowdStrike...
  Sentiment: Positive

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 TREND-JACK OPPORTUNITIES

1. AI Coding Transformation
   Angle: Share how your team uses AI coding tools
   Best Outlet: Lenny's Newsletter
   Why: Audience actively evaluating these tools
```

---

## Common Newsletter Sources

Add these to your config (or customize):

```yaml
gmail:
  sender_query: >-
    from:lenny@substack.com OR
    from:dan@tldrnewsletter.com OR
    from:casey@platformer.news OR
    from:newsletter@techmeme.com OR
    from:bigtechnology@substack.com OR
    from:notboring@substack.com OR
    from:ai.plus@axios.com OR
    from:email@stratechery.com OR
    from:noahpinion@substack.com
```

---

## Questions?

1. Check `README.md` for full documentation
2. Check `SETUP.md` for deployment details
3. Check `REUSABLE_PROMPT.md` for prompt-only usage
