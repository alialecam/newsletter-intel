#!/usr/bin/env python3
"""
Newsletter Summarizer - Run when someone asks in Slack

Usage:
    python summarize.py          # Last 3 days (default)
    python summarize.py 5        # Last 5 days
    python summarize.py 7        # Last 7 days

This script:
1. Fetches newsletters via gworkspace MCP (run from Cursor)
2. Analyzes with Claude
3. Posts to #comms-newsletter-intel
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "src"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import yaml
import anthropic

# Load config
with open(Path(__file__).parent / "config" / "config.yaml") as f:
    config = yaml.safe_load(f)

with open(Path(__file__).parent / "config" / "prompts" / "summarize.txt") as f:
    PROMPT_TEMPLATE = f.read()


def fetch_newsletters_mcp(days: int):
    """
    Placeholder for MCP-fetched newsletters.
    
    When running in Cursor, the newsletters are fetched via gworkspace MCP
    and passed to this script. For standalone use, this would need Gmail OAuth.
    """
    print(f"⚠️  To fetch newsletters, run this from Cursor with gworkspace MCP")
    print(f"   Or set up Gmail OAuth (see SETUP.md)")
    return []


def analyze_with_claude(newsletters: list) -> dict:
    """Analyze newsletters with Claude."""
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
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    
    client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
    
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
        return json.loads(response_text[start:end_pos])
    
    return {}


def post_to_slack(analysis: dict):
    """Post to Slack."""
    from slack_publisher import SlackPublisher
    publisher = SlackPublisher(config)
    return publisher.publish(analysis)


def main():
    # Parse days argument
    days = 3
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
            days = max(1, min(days, 30))
        except ValueError:
            print(f"Usage: python summarize.py [days]")
            print(f"  Example: python summarize.py 5")
            sys.exit(1)
    
    print("=" * 60)
    print(f"📰 Newsletter Intelligence - Last {days} Days")
    print("=" * 60)
    print()
    print("To run a full analysis:")
    print("  1. Use the gworkspace MCP to fetch emails (already connected)")
    print("  2. Run: python run_full_analysis.py")
    print()
    print("Or for automated Slack commands, complete SETUP.md")


if __name__ == "__main__":
    main()
