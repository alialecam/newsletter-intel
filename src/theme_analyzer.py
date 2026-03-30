"""Theme analyzer using Claude API for newsletter summarization."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic

from .content_parser import ParsedEmail


class ThemeAnalyzer:
    """Analyzes newsletter content using Claude to extract themes and insights."""

    def __init__(self, config: dict, prompts_path: Optional[Path] = None):
        """
        Initialize the theme analyzer.

        Args:
            config: Configuration dict with claude settings
            prompts_path: Path to prompts directory
        """
        self.config = config
        self.claude_config = config.get("claude", {})
        self.model = self.claude_config.get("model", "claude-sonnet-4-20250514")
        self.max_tokens = self.claude_config.get("max_tokens", 4096)
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template(prompts_path)
        
        # Brands to highlight
        self.highlight_brands = config.get("highlight_brands", ["Shopify"])
        
        # Initialize Anthropic client
        # Support both Shopify AI Proxy and direct Anthropic API
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        # Check for Shopify AI Proxy base URL
        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        if base_url:
            self.client = anthropic.Anthropic(
                api_key=api_key,
                base_url=base_url
            )
        else:
            self.client = anthropic.Anthropic(api_key=api_key)

    def _load_prompt_template(self, prompts_path: Optional[Path]) -> str:
        """Load the summarization prompt template."""
        if prompts_path is None:
            prompts_path = Path(__file__).parent.parent / "config" / "prompts"
        
        template_path = prompts_path / "summarize.txt"
        
        if template_path.exists():
            return template_path.read_text()
        
        # Fallback template
        return """Analyze the following newsletter content and extract:
1. Key themes with 2-3 sentence summaries
2. All mentions of Shopify (regardless of frequency)
3. Notable quotes with attribution
4. 2-3 trend-jacking opportunities with recommended outlets

Content:
{content}

Respond with valid JSON."""

    def analyze(self, emails: list[ParsedEmail]) -> dict:
        """
        Analyze a batch of newsletter emails.

        Args:
            emails: List of parsed emails to analyze

        Returns:
            Analysis results as a dict
        """
        if not emails:
            return self._empty_analysis()

        # Prepare content for analysis
        content = self._prepare_content(emails)
        
        # Build the prompt
        prompt = self.prompt_template.format(content=content)
        
        # Call Claude API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract response text
            response_text = response.content[0].text
            
            # Parse JSON from response
            analysis = self._parse_response(response_text)
            
            # Ensure all required fields are present
            analysis = self._validate_analysis(analysis, emails)
            
            return analysis
            
        except anthropic.APIError as e:
            print(f"Claude API error: {e}")
            return self._empty_analysis(error=str(e))
        except Exception as e:
            print(f"Analysis error: {e}")
            return self._empty_analysis(error=str(e))

    def _prepare_content(self, emails: list[ParsedEmail]) -> str:
        """
        Prepare email content for analysis.

        Args:
            emails: List of parsed emails

        Returns:
            Formatted content string
        """
        content_parts = []
        
        for email in emails:
            # Build source URL reference
            source_ref = ""
            if email.source_url:
                source_ref = f"\nSource URL: {email.source_url}"
            
            # Format each email
            part = f"""
--- EMAIL ---
Source: {email.source_name or email.from_name}
Subject: {email.subject}
Date: {email.date}{source_ref}

{email.clean_text[:8000]}  # Limit per-email content

Links:
{self._format_links(email.links[:20])}
--- END EMAIL ---
"""
            content_parts.append(part)
        
        return "\n\n".join(content_parts)

    def _format_links(self, links: list[dict]) -> str:
        """Format links for inclusion in prompt."""
        if not links:
            return "(no links extracted)"
        
        formatted = []
        for link in links:
            text = link.get("text", "")[:50]
            url = link.get("url", "")
            formatted.append(f"- [{text}]({url})")
        
        return "\n".join(formatted)

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse JSON from Claude's response.

        Args:
            response_text: Raw response text

        Returns:
            Parsed dict
        """
        # Try to find JSON in the response
        text = response_text.strip()
        
        # If response starts with ```json, extract the JSON block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()
        
        # Try to find JSON object boundaries
        if not text.startswith("{"):
            start = text.find("{")
            if start >= 0:
                # Find matching closing brace
                depth = 0
                for i, char in enumerate(text[start:], start):
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            text = text[start:i+1]
                            break
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response text: {text[:500]}...")
            return {}

    def _validate_analysis(self, analysis: dict, emails: list[ParsedEmail]) -> dict:
        """
        Validate and fill in missing fields in analysis.

        Args:
            analysis: Raw analysis dict
            emails: Original emails for metadata

        Returns:
            Validated analysis dict
        """
        # Ensure date range
        if "date_range" not in analysis:
            dates = [email.date for email in emails if email.date]
            analysis["date_range"] = {
                "start": min(dates) if dates else datetime.now().isoformat(),
                "end": max(dates) if dates else datetime.now().isoformat(),
            }
        
        # Ensure required lists exist
        analysis.setdefault("themes", [])
        analysis.setdefault("shopify_mentions", [])
        analysis.setdefault("notable_quotes", [])
        analysis.setdefault("trend_jack_opportunities", [])
        analysis.setdefault("people_mentioned", [])
        analysis.setdefault("companies_mentioned", [])
        
        # Build sources_processed from emails if not present
        if "sources_processed" not in analysis:
            analysis["sources_processed"] = [
                {
                    "name": email.source_name or email.from_name,
                    "url": email.source_url or "",
                    "date": email.date,
                    "subject": email.subject,
                }
                for email in emails
            ]
        
        return analysis

    def _empty_analysis(self, error: Optional[str] = None) -> dict:
        """Return an empty analysis structure."""
        result = {
            "date_range": {
                "start": datetime.now().isoformat(),
                "end": datetime.now().isoformat(),
            },
            "themes": [],
            "shopify_mentions": [],
            "notable_quotes": [],
            "trend_jack_opportunities": [],
            "people_mentioned": [],
            "companies_mentioned": [],
            "sources_processed": [],
        }
        
        if error:
            result["error"] = error
        
        return result


def analyze_newsletters(
    emails: list[ParsedEmail],
    config: dict,
    prompts_path: Optional[Path] = None,
) -> dict:
    """
    Analyze a list of parsed newsletter emails.

    Args:
        emails: List of ParsedEmail objects
        config: Configuration dict
        prompts_path: Path to prompts directory

    Returns:
        Analysis results dict
    """
    analyzer = ThemeAnalyzer(config, prompts_path)
    return analyzer.analyze(emails)
