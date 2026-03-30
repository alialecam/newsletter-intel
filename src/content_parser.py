"""Content parser for extracting clean text and links from newsletter emails."""

import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup, NavigableString
import yaml
from pathlib import Path


@dataclass
class ParsedEmail:
    """Structured representation of a parsed newsletter email."""

    id: str
    subject: str
    from_addr: str
    from_name: str
    date: str
    clean_text: str
    links: list[dict] = field(default_factory=list)
    source_name: Optional[str] = None
    source_url: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "subject": self.subject,
            "from_addr": self.from_addr,
            "from_name": self.from_name,
            "date": self.date,
            "clean_text": self.clean_text,
            "links": self.links,
            "source_name": self.source_name,
            "source_url": self.source_url,
        }


class ContentParser:
    """Parser for extracting clean content from newsletter emails."""

    # Common tracking/unsubscribe URL patterns to filter out
    TRACKING_PATTERNS = [
        r"unsubscribe",
        r"manage.preferences",
        r"email-preferences",
        r"optout",
        r"tracking",
        r"click\.",
        r"trk\.",
        r"substack\.com/action",
        r"list-manage\.com",
        r"mailchimp",
        r"sendgrid",
        r"beehiiv\.com/v\d/",
    ]

    def __init__(self, sources_path: Optional[Path] = None):
        """
        Initialize the content parser.

        Args:
            sources_path: Path to sources.yaml for name lookups
        """
        self.sources = {}
        if sources_path and sources_path.exists():
            with open(sources_path) as f:
                data = yaml.safe_load(f)
                for source in data.get("sources", []):
                    email = source.get("email", "").lower()
                    self.sources[email] = {
                        "name": source.get("name"),
                        "url": source.get("url"),
                        "category": source.get("category"),
                    }

    def parse_email(self, email: dict) -> ParsedEmail:
        """
        Parse a raw email dict into structured content.

        Args:
            email: Raw email dict from GmailFetcher

        Returns:
            ParsedEmail with clean text and extracted links
        """
        # Extract sender info
        from_addr = email.get("from", "")
        from_name = self._extract_sender_name(from_addr)
        email_addr = self._extract_email_address(from_addr)

        # Look up source info
        source_info = self.sources.get(email_addr.lower(), {})
        source_name = source_info.get("name") or from_name
        source_url = source_info.get("url")

        # Parse body content
        body_html = email.get("body_html", "")
        body_text = email.get("body_text", "")

        if body_html:
            clean_text, links = self._parse_html(body_html)
        elif body_text:
            clean_text = self._clean_text(body_text)
            links = self._extract_links_from_text(body_text)
        else:
            clean_text = email.get("snippet", "")
            links = []

        # If we found a primary article link, use it as source_url
        if not source_url and links:
            primary_link = self._find_primary_link(links, source_name)
            if primary_link:
                source_url = primary_link

        return ParsedEmail(
            id=email.get("id", ""),
            subject=email.get("subject", ""),
            from_addr=from_addr,
            from_name=from_name,
            date=email.get("date", ""),
            clean_text=clean_text,
            links=links,
            source_name=source_name,
            source_url=source_url,
        )

    def _extract_sender_name(self, from_header: str) -> str:
        """Extract display name from From header."""
        # Format: "Name <email@example.com>" or just "email@example.com"
        match = re.match(r'^"?([^"<]+)"?\s*<', from_header)
        if match:
            return match.group(1).strip()
        
        # Try to extract name from email address
        email = self._extract_email_address(from_header)
        if email:
            local_part = email.split("@")[0]
            # Convert "john.doe" or "john_doe" to "John Doe"
            name = re.sub(r"[._]", " ", local_part)
            return name.title()
        
        return from_header

    def _extract_email_address(self, from_header: str) -> str:
        """Extract email address from From header."""
        match = re.search(r"<([^>]+)>", from_header)
        if match:
            return match.group(1)
        
        # Check if it's just an email address
        if "@" in from_header and " " not in from_header.strip():
            return from_header.strip()
        
        return ""

    def _parse_html(self, html: str) -> tuple[str, list[dict]]:
        """
        Parse HTML content to extract clean text and links.

        Args:
            html: Raw HTML content

        Returns:
            Tuple of (clean_text, links_list)
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove unwanted elements
        for tag in soup.find_all(["script", "style", "head", "meta", "noscript"]):
            tag.decompose()

        # Remove common footer/unsubscribe sections
        for tag in soup.find_all(class_=re.compile(r"footer|unsubscribe|manage", re.I)):
            tag.decompose()

        # Extract links before cleaning
        links = self._extract_links_from_soup(soup)

        # Get clean text
        text = soup.get_text(separator="\n")
        clean_text = self._clean_text(text)

        return clean_text, links

    def _extract_links_from_soup(self, soup: BeautifulSoup) -> list[dict]:
        """
        Extract meaningful links from parsed HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of link dicts with url and text
        """
        links = []
        seen_urls = set()

        for a_tag in soup.find_all("a", href=True):
            url = a_tag.get("href", "").strip()
            
            # Skip empty, mailto, and anchor links
            if not url or url.startswith(("#", "mailto:", "tel:")):
                continue

            # Skip tracking/unsubscribe links
            if self._is_tracking_url(url):
                continue

            # Get link text
            text = a_tag.get_text(strip=True)
            if not text:
                # Try to get alt text from images
                img = a_tag.find("img")
                if img:
                    text = img.get("alt", "")

            # Skip if no meaningful text
            if not text or len(text) < 2:
                continue

            # Normalize URL
            parsed = urlparse(url)
            normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Skip duplicates
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)

            links.append({
                "url": url,
                "text": text[:200],  # Limit text length
                "domain": parsed.netloc,
            })

        return links

    def _extract_links_from_text(self, text: str) -> list[dict]:
        """Extract URLs from plain text content."""
        links = []
        seen_urls = set()

        # Simple URL regex
        url_pattern = r'https?://[^\s<>"\')\]]+(?:\([^\s<>"\')\]]*\))?[^\s<>"\')\]]+'
        
        for match in re.finditer(url_pattern, text):
            url = match.group(0).rstrip(".,;:!?")
            
            if self._is_tracking_url(url):
                continue

            parsed = urlparse(url)
            normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)

            links.append({
                "url": url,
                "text": parsed.netloc,
                "domain": parsed.netloc,
            })

        return links

    def _is_tracking_url(self, url: str) -> bool:
        """Check if URL is likely a tracking/unsubscribe link."""
        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in self.TRACKING_PATTERNS)

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.

        Args:
            text: Raw text content

        Returns:
            Cleaned text
        """
        # Replace multiple newlines with double newline
        text = re.sub(r"\n\s*\n", "\n\n", text)
        
        # Replace multiple spaces with single space
        text = re.sub(r"[ \t]+", " ", text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        
        # Remove excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        return text.strip()

    def _find_primary_link(self, links: list[dict], source_name: str) -> Optional[str]:
        """
        Find the most likely primary article link.

        Args:
            links: List of extracted links
            source_name: Newsletter source name

        Returns:
            Primary link URL or None
        """
        # Priority: Look for links to the source's own domain
        source_words = source_name.lower().split()
        
        for link in links:
            domain = link.get("domain", "").lower()
            # Check if domain contains source name words
            if any(word in domain for word in source_words if len(word) > 3):
                return link.get("url")

        # Fall back to first non-social link
        social_domains = ["twitter.com", "x.com", "linkedin.com", "facebook.com"]
        for link in links:
            domain = link.get("domain", "").lower()
            if not any(social in domain for social in social_domains):
                return link.get("url")

        return links[0].get("url") if links else None


def parse_emails(emails: list[dict], sources_path: Optional[Path] = None) -> list[ParsedEmail]:
    """
    Parse a list of raw emails into structured content.

    Args:
        emails: List of raw email dicts from GmailFetcher
        sources_path: Path to sources.yaml

    Returns:
        List of ParsedEmail objects
    """
    parser = ContentParser(sources_path)
    return [parser.parse_email(email) for email in emails]
