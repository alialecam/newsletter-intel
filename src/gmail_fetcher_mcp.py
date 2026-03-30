"""Gmail fetcher that works with pre-fetched email data.

This module is designed to work with emails fetched via the Google Workspace MCP
or any other source that provides email data in a compatible format.

For MCP-based fetching, emails should be fetched externally and passed to the
parse functions here.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import re


@dataclass
class RawEmail:
    """Raw email data structure."""
    id: str
    subject: str
    from_addr: str
    date: str
    body_html: str = ""
    body_text: str = ""
    snippet: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject": self.subject,
            "from": self.from_addr,
            "date": self.date,
            "body_html": self.body_html,
            "body_text": self.body_text,
            "snippet": self.snippet,
        }


def parse_mcp_email(mcp_email: dict) -> RawEmail:
    """
    Parse email data from MCP format to RawEmail.
    
    Args:
        mcp_email: Email dict from gworkspace-mcp read_mail tool
        
    Returns:
        RawEmail instance
    """
    return RawEmail(
        id=mcp_email.get("id", ""),
        subject=mcp_email.get("subject", ""),
        from_addr=mcp_email.get("from", ""),
        date=mcp_email.get("date", ""),
        body_html=mcp_email.get("body_html", ""),
        body_text=mcp_email.get("body_text", mcp_email.get("body", "")),
        snippet=mcp_email.get("snippet", mcp_email.get("preview", "")),
    )


def build_newsletter_query(config: dict) -> str:
    """
    Build Gmail search query from config.
    
    Args:
        config: Configuration dict with gmail settings
        
    Returns:
        Gmail search query string
    """
    gmail_config = config.get("gmail", {})
    
    # Get sender query
    sender_query = gmail_config.get("sender_query", "")
    
    # Clean up the query (remove newlines, extra spaces)
    sender_query = " ".join(sender_query.split())
    
    # Get label
    label = gmail_config.get("label", "newsletters")
    
    # Build combined query
    # Either matches sender filter OR is in the newsletters label
    if sender_query and label:
        return f"({sender_query}) OR label:{label}"
    elif sender_query:
        return sender_query
    elif label:
        return f"label:{label}"
    else:
        return "label:newsletters"


# Default newsletter senders for reference
DEFAULT_NEWSLETTER_SENDERS = [
    "lenny@substack.com",
    "lenny+how-i-ai@substack.com",
    "bigtechnology@substack.com",
    "email@stratechery.com",
    "casey@platformer.news",
    "noahpinion@substack.com",
    "list@ben-evans.com",
    "notboring@substack.com",
    "dan@tldrnewsletter.com",
    "newsletter@techmeme.com",
    "ai.plus@axios.com",
    "superhuman@mail.joinsuperhuman.ai",
    "thecode@mail.joinsuperhuman.ai",
    "tbpn+run-of-show@substack.com",
]


def get_sender_query() -> str:
    """Get the default sender query for newsletters."""
    senders = " OR ".join([f"from:{s}" for s in DEFAULT_NEWSLETTER_SENDERS])
    return f"({senders})"
