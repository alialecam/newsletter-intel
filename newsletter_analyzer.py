"""
Newsletter analysis module that can be triggered by Slack commands.

This module:
1. Fetches emails from Gmail via OAuth
2. Analyzes content with Claude
3. Posts results to Slack
"""

import os
import json
import base64
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import yaml
import anthropic
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Google API imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Load config
CONFIG_PATH = Path(__file__).parent / "config" / "config.yaml"
PROMPT_PATH = Path(__file__).parent / "config" / "prompts" / "summarize.txt"
CREDENTIALS_PATH = Path(__file__).parent / "credentials"

with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

with open(PROMPT_PATH) as f:
    PROMPT_TEMPLATE = f.read()


def get_gmail_service():
    """Get authenticated Gmail API service."""
    creds = None
    token_path = CREDENTIALS_PATH / "token.json"
    client_secret_path = CREDENTIALS_PATH / "client_secret.json"
    
    # Load existing credentials
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secret_path.exists():
                raise FileNotFoundError(
                    f"Gmail OAuth not configured. Please place client_secret.json in {CREDENTIALS_PATH}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    
    return build("gmail", "v1", credentials=creds)


def fetch_newsletters(days: int) -> list:
    """Fetch newsletters from Gmail for the specified number of days."""
    service = get_gmail_service()
    
    # Build date query
    after_date = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    
    # Get sender query from config
    sender_query = CONFIG.get("gmail", {}).get("sender_query", "")
    label = CONFIG.get("gmail", {}).get("label", "newsletters")
    
    # Build Gmail search query
    query_parts = []
    if sender_query:
        query_parts.append(f"({sender_query})")
    if label:
        query_parts.append(f"label:{label}")
    
    if query_parts:
        query = f"({' OR '.join(query_parts)}) after:{after_date}"
    else:
        query = f"after:{after_date}"
    
    print(f"Gmail query: {query}")
    
    # Fetch message IDs
    results = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=50
    ).execute()
    
    messages = results.get("messages", [])
    print(f"Found {len(messages)} messages")
    
    newsletters = []
    for msg in messages:
        try:
            # Get full message
            full_msg = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full"
            ).execute()
            
            # Extract headers
            headers = {h["name"]: h["value"] for h in full_msg["payload"]["headers"]}
            
            # Extract body
            body = extract_body(full_msg["payload"])
            
            newsletters.append({
                "source": extract_sender_name(headers.get("From", "")),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "url": f"https://mail.google.com/mail/u/0/#inbox/{msg['id']}",
                "content": body[:8000]  # Limit content length
            })
        except Exception as e:
            print(f"Error fetching message {msg['id']}: {e}")
    
    return newsletters


def extract_sender_name(from_header: str) -> str:
    """Extract display name from From header."""
    if "<" in from_header:
        return from_header.split("<")[0].strip().strip('"')
    return from_header


def extract_body(payload: dict) -> str:
    """Extract text body from Gmail message payload."""
    body = ""
    
    if "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    
    if "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            
            if mime_type == "text/plain":
                if part["body"].get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    break
            elif mime_type == "text/html" and not body:
                if part["body"].get("data"):
                    html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    # Basic HTML to text conversion
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, "lxml")
                    body = soup.get_text(separator="\n", strip=True)
            elif mime_type.startswith("multipart"):
                body = extract_body(part)
                if body:
                    break
    
    return body


def analyze_with_claude(newsletters: list) -> dict:
    """Analyze newsletters with Claude."""
    if not newsletters:
        return {"error": "No newsletters to analyze"}
    
    # Prepare content
    content_parts = []
    for nl in newsletters:
        part = f"""
--- EMAIL ---
Source: {nl['source']}
Subject: {nl['subject']}
Date: {nl['date']}
Source URL: {nl['url']}

{nl['content']}
--- END EMAIL ---
"""
        content_parts.append(part)
    
    full_content = "\n\n".join(content_parts)
    prompt = PROMPT_TEMPLATE.replace("{content}", full_content)
    
    # Initialize Anthropic client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set"}
    
    client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
    
    # Call Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = response.content[0].text
    
    # Parse JSON
    start = response_text.find("{")
    if start >= 0:
        depth = 0
        end_pos = start
        for i, char in enumerate(response_text[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end_pos = i + 1
                    break
        json_text = response_text[start:end_pos]
        return json.loads(json_text)
    
    return {"error": "Could not parse Claude response"}


def post_to_slack(analysis: dict, channel_id: str) -> bool:
    """Post analysis results to Slack."""
    # Import the existing SlackPublisher
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    from slack_publisher import SlackPublisher
    
    # Override channel if specified
    config = CONFIG.copy()
    if channel_id:
        config["slack"] = config.get("slack", {})
        config["slack"]["channel_id"] = channel_id
    
    publisher = SlackPublisher(config)
    return publisher.publish(analysis)


def analyze_newsletters(days: int = 3, channel_id: str = None) -> dict:
    """
    Main entry point for newsletter analysis.
    
    Args:
        days: Number of days to analyze
        channel_id: Slack channel to post to (uses config default if not specified)
    
    Returns:
        dict with success status and any error messages
    """
    try:
        print(f"Fetching newsletters from last {days} days...")
        newsletters = fetch_newsletters(days)
        
        if not newsletters:
            return {"success": False, "error": "No newsletters found in the specified time range"}
        
        print(f"Analyzing {len(newsletters)} newsletters with Claude...")
        analysis = analyze_with_claude(newsletters)
        
        if "error" in analysis:
            return {"success": False, "error": analysis["error"]}
        
        # Add metadata
        analysis["date_range"] = {
            "start": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            "end": datetime.now().strftime("%Y-%m-%d")
        }
        
        print("Posting to Slack...")
        target_channel = channel_id or os.environ.get("SLACK_CHANNEL_ID")
        success = post_to_slack(analysis, target_channel)
        
        if success:
            return {"success": True, "newsletters_analyzed": len(newsletters)}
        else:
            return {"success": False, "error": "Failed to post to Slack"}
        
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze newsletters")
    parser.add_argument("--days", type=int, default=3, help="Number of days to analyze")
    parser.add_argument("--channel", type=str, help="Slack channel ID to post to")
    args = parser.parse_args()
    
    result = analyze_newsletters(days=args.days, channel_id=args.channel)
    print(json.dumps(result, indent=2))
