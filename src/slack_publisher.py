"""Slack publisher for posting newsletter summaries."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackPublisher:
    """Publishes newsletter analysis summaries to Slack."""

    def __init__(self, config: dict):
        """
        Initialize the Slack publisher.

        Args:
            config: Configuration dict with slack settings
        """
        self.config = config
        self.slack_config = config.get("slack", {})
        
        # Get channel from environment
        self.channel = os.environ.get("SLACK_CHANNEL_ID")
        if not self.channel:
            raise ValueError("SLACK_CHANNEL_ID environment variable not set")
        
        # Get token - try multiple sources
        self.token = self._get_slack_token()
        self.cookie = self._get_slack_cookie()
        
        if not self.token:
            raise ValueError(
                "No Slack token found. Set SLACK_BOT_TOKEN or SLACK_TOKEN env var, "
                "or run Slack MCP authentication."
            )
        
        # Initialize client with token (and cookie if using user token)
        if self.cookie:
            # Using xoxc user token with cookie
            self.client = WebClient(token=self.token)
            self.client.headers["Cookie"] = f"d={self.cookie}"
        else:
            # Using xoxb bot token
            self.client = WebClient(token=self.token)
        
        # Unfurl settings from config
        self.unfurl_links = self.slack_config.get("unfurl_links", False)
        self.unfurl_media = self.slack_config.get("unfurl_media", False)
    
    def _get_slack_token(self) -> Optional[str]:
        """Get Slack token from environment or MCP config."""
        # Try environment variables first
        token = os.environ.get("SLACK_BOT_TOKEN") or os.environ.get("SLACK_TOKEN")
        if token:
            return token
        
        # Try Slack MCP credentials file
        mcp_creds_path = Path.home() / ".config" / "slack-mcp" / "credentials.json"
        if mcp_creds_path.exists():
            try:
                with open(mcp_creds_path) as f:
                    creds = json.load(f)
                    return creds.get("token")
            except Exception:
                pass
        
        return None
    
    def _get_slack_cookie(self) -> Optional[str]:
        """Get Slack cookie for xoxc tokens."""
        cookie = os.environ.get("SLACK_COOKIE")
        if cookie:
            return cookie
        
        # Try Slack MCP credentials file
        mcp_creds_path = Path.home() / ".config" / "slack-mcp" / "credentials.json"
        if mcp_creds_path.exists():
            try:
                with open(mcp_creds_path) as f:
                    creds = json.load(f)
                    return creds.get("cookie")
            except Exception:
                pass
        
        return None

    def publish(self, analysis: dict) -> bool:
        """
        Publish analysis results to Slack.

        Args:
            analysis: Analysis dict from ThemeAnalyzer

        Returns:
            True if successful, False otherwise
        """
        try:
            blocks = self._build_blocks(analysis)
            
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=self._build_fallback_text(analysis),
                unfurl_links=self.unfurl_links,
                unfurl_media=self.unfurl_media,
            )
            
            print(f"Posted to Slack: {response['ts']}")
            return True
            
        except SlackApiError as e:
            print(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            print(f"Slack publish error: {e}")
            return False

    def _build_blocks(self, analysis: dict) -> list[dict]:
        """
        Build Slack blocks for the analysis.

        Args:
            analysis: Analysis dict

        Returns:
            List of Slack block dicts
        """
        blocks = []
        
        # Header
        date_range = analysis.get("date_range", {})
        start = self._format_date(date_range.get("start", ""))
        end = self._format_date(date_range.get("end", ""))
        
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Newsletter Intel | {start} - {end}",
                "emoji": False
            }
        })
        
        blocks.append({"type": "divider"})
        
        # Trending Themes
        themes = analysis.get("themes", [])
        if themes:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*TRENDING THEMES*"
                }
            })
            
            for i, theme in enumerate(themes[:5], 1):
                blocks.extend(self._build_theme_block(i, theme))
            
            blocks.append({"type": "divider"})
        
        # Shopify Mentions
        shopify_mentions = analysis.get("shopify_mentions", [])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*SHOPIFY MENTIONS*"
            }
        })
        
        if shopify_mentions:
            for mention in shopify_mentions:
                blocks.append(self._build_shopify_mention_block(mention))
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_No Shopify mentions in this batch_"
                }
            })
        
        blocks.append({"type": "divider"})
        
        # Notable Quotes
        quotes = analysis.get("notable_quotes", [])
        if quotes:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*NOTABLE QUOTES*"
                }
            })
            
            for quote in quotes[:3]:
                blocks.append(self._build_quote_block(quote))
            
            blocks.append({"type": "divider"})
        
        # Trend-Jack Opportunities
        opportunities = analysis.get("trend_jack_opportunities", [])
        if opportunities:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*TREND-JACK OPPORTUNITIES*"
                }
            })
            
            for i, opp in enumerate(opportunities[:3], 1):
                blocks.append(self._build_opportunity_block(i, opp))
            
            blocks.append({"type": "divider"})
        
        # Sources Processed
        sources = analysis.get("sources_processed", [])
        if sources:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*SOURCES PROCESSED ({len(sources)} newsletters)*"
                }
            })
            
            source_links = self._build_source_links(sources)
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": source_links
                }
            })
        
        return blocks

    def _build_theme_block(self, index: int, theme: dict) -> list[dict]:
        """Build blocks for a single theme."""
        blocks = []
        
        title = theme.get("title", "Untitled Theme")
        mention_count = theme.get("mention_count", 0)
        summary = theme.get("summary", "")
        sources = theme.get("sources", [])
        
        # Theme title and summary
        text = f"*{index}. {title}* ({mention_count} mentions)\n{summary}"
        
        # Add source links
        if sources:
            source_links = []
            for source in sources:
                name = source.get("name", "")
                url = source.get("url", "")
                if url:
                    source_links.append(f"<{url}|{name}>")
                else:
                    source_links.append(name)
            text += f"\n→ {' | '.join(source_links)}"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        })
        
        return blocks

    def _build_shopify_mention_block(self, mention: dict) -> dict:
        """Build block for a Shopify mention."""
        source_name = mention.get("source_name", "Unknown")
        source_url = mention.get("source_url", "")
        context = mention.get("context", "")
        quote = mention.get("quote")
        
        # Build source link
        if source_url:
            source_ref = f"<{source_url}|{source_name}>"
        else:
            source_ref = source_name
        
        text = f"• *{source_ref}*: {context}"
        
        if quote:
            text += f'\n  _"{quote}"_'
        
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }

    def _build_quote_block(self, quote: dict) -> dict:
        """Build block for a notable quote."""
        quote_text = quote.get("quote", "")
        author = quote.get("author", "")
        source_name = quote.get("source_name", "")
        source_url = quote.get("source_url", "")
        
        # Build source reference
        if source_url:
            source_ref = f"<{source_url}|{source_name}>"
        else:
            source_ref = source_name
        
        text = f'_"{quote_text}"_\n— {author}, {source_ref}'
        
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }

    def _build_opportunity_block(self, index: int, opp: dict) -> dict:
        """Build block for a trend-jack opportunity."""
        theme = opp.get("theme", "")
        opportunity = opp.get("opportunity", "")
        angle = opp.get("angle", "")
        best_outlet = opp.get("best_outlet", "")
        outlet_rationale = opp.get("outlet_rationale", "")
        
        text = f"*{index}. {theme}*\n"
        text += f"*Opportunity:* {opportunity}\n"
        text += f"*Angle:* {angle}\n"
        text += f"*Best outlet:* {best_outlet}"
        
        if outlet_rationale:
            text += f" ({outlet_rationale})"
        
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }

    def _build_source_links(self, sources: list[dict]) -> str:
        """Build compact list of source links."""
        links = []
        
        for source in sources:
            name = source.get("name", "Unknown")
            url = source.get("url", "")
            
            if url:
                links.append(f"<{url}|{name}>")
            else:
                links.append(name)
        
        # Join with bullet separator
        return " • ".join(links)

    def _build_fallback_text(self, analysis: dict) -> str:
        """Build plain text fallback for notifications."""
        themes = analysis.get("themes", [])
        source_count = len(analysis.get("sources_processed", []))
        
        theme_summary = ""
        if themes:
            theme_names = [t.get("title", "") for t in themes[:3]]
            theme_summary = f"Top themes: {', '.join(theme_names)}"
        
        return f"Newsletter Intel: {source_count} newsletters processed. {theme_summary}"

    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        if not date_str:
            return datetime.now().strftime("%b %d")
        
        try:
            # Try parsing ISO format
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%b %d")
        except ValueError:
            # Try common email date format
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(date_str)
                return dt.strftime("%b %d")
            except Exception:
                return date_str[:10]


def publish_to_slack(analysis: dict, config: dict) -> bool:
    """
    Publish analysis to Slack.

    Args:
        analysis: Analysis dict from ThemeAnalyzer
        config: Configuration dict

    Returns:
        True if successful, False otherwise
    """
    publisher = SlackPublisher(config)
    return publisher.publish(analysis)
