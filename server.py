"""
Flask server for Slack slash command integration.

Handles /summarize command to trigger newsletter analysis.
Usage in Slack: /summarize 3  (analyzes last 3 days)
"""

import os
import re
import json
import hmac
import hashlib
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Slack configuration
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")


def verify_slack_signature(request):
    """Verify that the request actually came from Slack."""
    if not SLACK_SIGNING_SECRET:
        app.logger.warning("SLACK_SIGNING_SECRET not set - skipping verification")
        return True
    
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    
    # Check timestamp to prevent replay attacks
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False
    
    # Compute expected signature
    sig_basestring = f"v0:{timestamp}:{request.get_data(as_text=True)}"
    my_signature = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(my_signature, signature)


def run_analysis_async(days: int, channel_id: str, response_url: str):
    """Run the analysis in a background thread and post results."""
    try:
        from newsletter_analyzer import analyze_newsletters
        
        # Run the analysis
        result = analyze_newsletters(days=days, channel_id=channel_id)
        
        if result.get("success"):
            message = f"✅ Newsletter analysis complete! Check the channel for the summary."
        else:
            message = f"❌ Analysis failed: {result.get('error', 'Unknown error')}"
        
        # Post follow-up message to response_url
        import requests
        requests.post(response_url, json={
            "response_type": "ephemeral",
            "text": message
        })
        
    except Exception as e:
        import requests
        requests.post(response_url, json={
            "response_type": "ephemeral",
            "text": f"❌ Error running analysis: {str(e)}"
        })


@app.route("/slack/summarize", methods=["POST"])
def handle_summarize():
    """
    Handle the /summarize slash command from Slack.
    
    Usage: /summarize 3  (analyzes last 3 days)
    Default: 3 days if no number specified
    """
    # Verify request is from Slack
    if not verify_slack_signature(request):
        return jsonify({"error": "Invalid signature"}), 403
    
    # Parse the command
    text = request.form.get("text", "").strip()
    channel_id = request.form.get("channel_id", "")
    user_id = request.form.get("user_id", "")
    response_url = request.form.get("response_url", "")
    
    # Parse number of days (default to 3)
    days = 3
    if text:
        match = re.search(r"(\d+)", text)
        if match:
            days = int(match.group(1))
            # Cap at reasonable limits
            days = max(1, min(days, 30))
    
    # Acknowledge immediately (Slack requires response within 3 seconds)
    # Then run analysis in background
    thread = threading.Thread(
        target=run_analysis_async,
        args=(days, channel_id, response_url)
    )
    thread.start()
    
    return jsonify({
        "response_type": "in_channel",
        "text": f"📰 Starting newsletter analysis for the last {days} day(s)... This may take a minute."
    })


@app.route("/slack/events", methods=["POST"])
def handle_events():
    """
    Handle Slack Events API (for message-based triggers).
    
    Listens for messages like "summarize last 5 days" in the channel.
    """
    data = request.json
    
    # Handle Slack URL verification challenge
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})
    
    # Verify request
    if not verify_slack_signature(request):
        return jsonify({"error": "Invalid signature"}), 403
    
    event = data.get("event", {})
    
    # Only process message events
    if event.get("type") != "message":
        return jsonify({"ok": True})
    
    # Ignore bot messages to prevent loops
    if event.get("bot_id") or event.get("subtype"):
        return jsonify({"ok": True})
    
    text = event.get("text", "").lower()
    channel_id = event.get("channel", "")
    
    # Check for trigger phrase
    match = re.search(r"summarize\s+(?:the\s+)?last\s+(\d+)\s+days?", text)
    if match:
        days = int(match.group(1))
        days = max(1, min(days, 30))
        
        # Post acknowledgment
        from slack_sdk import WebClient
        client = WebClient(token=SLACK_BOT_TOKEN)
        client.chat_postMessage(
            channel=channel_id,
            text=f"📰 Starting newsletter analysis for the last {days} day(s)... This may take a minute."
        )
        
        # Run analysis in background
        thread = threading.Thread(
            target=run_analysis_async,
            args=(days, channel_id, None)
        )
        thread.start()
    
    return jsonify({"ok": True})


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for deployment platforms."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


@app.route("/", methods=["GET"])
def home():
    """Home page with basic info."""
    return jsonify({
        "app": "Newsletter Intelligence Bot",
        "endpoints": {
            "/slack/summarize": "POST - Slack slash command endpoint",
            "/slack/events": "POST - Slack Events API endpoint",
            "/health": "GET - Health check"
        }
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("DEBUG", "false").lower() == "true")
