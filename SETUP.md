# Newsletter Intelligence Bot - Setup Guide

This guide walks you through setting up the `/summarize` Slack command that lets anyone in the channel trigger newsletter analysis.

## Overview

When someone types `/summarize 5` in Slack, the bot will:
1. Fetch newsletters from the last 5 days from your Gmail
2. Analyze them with Claude to extract themes, mentions, and opportunities
3. Post a formatted summary back to the channel

## Prerequisites

- A Shopify email account (for Gmail access)
- Access to create a Slack app in your workspace
- A hosting platform account (Railway, Render, or Heroku)

---

## Step 1: Gmail OAuth Setup (~5 minutes)

The bot needs read-only access to your Gmail to fetch newsletters.

### 1.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it `newsletter-intel` and create it

### 1.2 Enable Gmail API

1. In your project, go to **APIs & Services** → **Library**
2. Search for "Gmail API" and click it
3. Click **Enable**

### 1.3 Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **Internal** (for Shopify workspace) or **External**
3. Fill in:
   - App name: `Newsletter Intelligence`
   - User support email: your email
   - Developer contact: your email
4. Click **Save and Continue**
5. On Scopes page, click **Add or Remove Scopes**
6. Find and select `https://www.googleapis.com/auth/gmail.readonly`
7. Save and continue through the rest

### 1.4 Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `Newsletter Intel Bot`
5. Click **Create**
6. Click **Download JSON**
7. Rename the file to `client_secret.json`
8. Place it in the `credentials/` folder of this repo

### 1.5 Authorize the App (One-time)

Run this locally to authorize:

```bash
cd newsletter-intel
python -c "from newsletter_analyzer import get_gmail_service; get_gmail_service()"
```

This opens a browser window - sign in with your Shopify Google account and authorize.
A `token.json` file will be created in `credentials/`.

---

## Step 2: Create Slack App (~5 minutes)

### 2.1 Create the App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. Name: `Newsletter Intel Bot`
4. Workspace: Select your Shopify workspace
5. Click **Create App**

### 2.2 Configure Slash Command

1. In your app settings, go to **Slash Commands**
2. Click **Create New Command**
3. Fill in:
   - Command: `/summarize`
   - Request URL: `https://YOUR-DEPLOYED-URL/slack/summarize` (fill in after deployment)
   - Short Description: `Summarize newsletters from the last X days`
   - Usage Hint: `[days]` (e.g., `/summarize 3`)
4. Click **Save**

### 2.3 Add Bot Permissions

1. Go to **OAuth & Permissions**
2. Under **Scopes** → **Bot Token Scopes**, add:
   - `chat:write` - Post messages
   - `commands` - Handle slash commands
3. Click **Install to Workspace** at the top
4. Authorize the app

### 2.4 Get Credentials

From your Slack app settings, copy:

1. **Bot User OAuth Token** (starts with `xoxb-`)
   - Found in **OAuth & Permissions** → **Bot User OAuth Token**
   
2. **Signing Secret**
   - Found in **Basic Information** → **App Credentials** → **Signing Secret**

---

## Step 3: Deploy to Railway (~5 minutes)

Railway offers a free tier and easy deployment.

### 3.1 Create Railway Account

1. Go to [railway.app](https://railway.app/)
2. Sign up with GitHub

### 3.2 Deploy from GitHub

1. Push this repo to your GitHub (if not already)
2. In Railway, click **New Project** → **Deploy from GitHub repo**
3. Select your `newsletter-intel` repository
4. Railway will auto-detect the Python app

### 3.3 Set Environment Variables

In Railway, go to your service → **Variables** and add:

```
ANTHROPIC_API_KEY=shopify-eyJ...  (your Shopify AI Proxy token)
ANTHROPIC_BASE_URL=https://proxy.shopify.ai/apis/anthropic
SLACK_BOT_TOKEN=xoxb-...  (from Step 2.4)
SLACK_SIGNING_SECRET=...  (from Step 2.4)
SLACK_CHANNEL_ID=C0AEH7J3T0B  (your #comms-newsletter-intel channel)
```

### 3.4 Upload Gmail Credentials

You'll need to include the Gmail credentials. Two options:

**Option A: Add as environment variables (recommended for production)**
```
GOOGLE_TOKEN_JSON=<contents of credentials/token.json as one line>
GOOGLE_CLIENT_SECRET_JSON=<contents of credentials/client_secret.json as one line>
```

Then update `newsletter_analyzer.py` to read from env vars if files don't exist.

**Option B: Include in repo (simpler but less secure)**
Add `credentials/token.json` to your repo (remove from .gitignore temporarily).
Note: This contains your OAuth tokens - only do this for private repos.

### 3.5 Get Your Deployment URL

Once deployed, Railway provides a URL like:
`https://newsletter-intel-production.up.railway.app`

### 3.6 Update Slack Slash Command URL

Go back to your Slack app → **Slash Commands** → Edit `/summarize`
Update the Request URL to:
`https://YOUR-RAILWAY-URL/slack/summarize`

---

## Step 4: Test It!

1. Go to `#comms-newsletter-intel` in Slack
2. Type `/summarize 3`
3. You should see:
   - Immediate response: "📰 Starting newsletter analysis for the last 3 day(s)..."
   - After ~1-2 minutes: Full analysis posted to the channel

---

## Troubleshooting

### "Gmail OAuth not configured"
- Make sure `credentials/client_secret.json` exists
- Run the authorization step locally first

### "Invalid signature" error
- Check that `SLACK_SIGNING_SECRET` is set correctly
- Make sure you're using the Signing Secret, not the Client Secret

### "No newsletters found"
- Check that your Gmail filter query matches your newsletter senders
- Verify the date range has emails

### Analysis takes too long / times out
- Slack requires response within 3 seconds (handled by async processing)
- The full analysis can take 1-2 minutes
- Check Railway logs for errors

---

## Configuration

### Customize Newsletter Sources

Edit `config/config.yaml` to add/remove newsletter senders:

```yaml
gmail:
  sender_query: >-
    from:lenny@substack.com OR
    from:bigtechnology@substack.com OR
    from:your-new-newsletter@example.com
  label: newsletters
```

### Customize Analysis Prompt

Edit `config/prompts/summarize.txt` to change what the analysis focuses on.

---

## Alternative: Message-Based Trigger

If you prefer users to type "summarize last 5 days" instead of a slash command:

1. In your Slack app, go to **Event Subscriptions**
2. Enable Events and set Request URL to: `https://YOUR-URL/slack/events`
3. Under **Subscribe to bot events**, add: `message.channels`
4. Reinstall the app to your workspace

Now users can type naturally: "summarize last 5 days" and the bot will respond.

---

## Support

If you run into issues, check:
1. Railway logs for server errors
2. Slack app event logs for delivery issues
3. Google Cloud Console for OAuth errors
