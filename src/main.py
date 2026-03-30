"""Main orchestration script for the newsletter intelligence pipeline."""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .gmail_fetcher import GmailFetcher
from .content_parser import ContentParser, parse_emails
from .theme_analyzer import ThemeAnalyzer
from .slack_publisher import SlackPublisher

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
SOURCES_PATH = PROJECT_ROOT / "config" / "sources.yaml"
PROMPTS_PATH = PROJECT_ROOT / "config" / "prompts"
STATE_PATH = PROJECT_ROOT / "state.json"
OUTPUT_PATH = PROJECT_ROOT / "output" / "summaries"


def load_config() -> dict:
    """Load configuration from YAML file."""
    if not CONFIG_PATH.exists():
        print(f"Error: Configuration file not found: {CONFIG_PATH}")
        sys.exit(1)
    
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_state() -> dict:
    """Load pipeline state (last run timestamp, etc.)."""
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    """Save pipeline state."""
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, default=str)


def save_markdown_summary(analysis: dict, config: dict):
    """Save analysis as markdown file."""
    if not config.get("output", {}).get("archive_summaries", True):
        return
    
    # Ensure output directory exists
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = OUTPUT_PATH / f"summary_{timestamp}.md"
    
    # Build markdown content
    md_content = build_markdown(analysis)
    
    with open(filename, "w") as f:
        f.write(md_content)
    
    print(f"Saved markdown summary: {filename}")


def build_markdown(analysis: dict) -> str:
    """Build markdown summary from analysis."""
    lines = []
    
    # Header
    date_range = analysis.get("date_range", {})
    start = date_range.get("start", "")[:10]
    end = date_range.get("end", "")[:10]
    
    lines.append(f"# Newsletter Intel | {start} to {end}")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")
    
    # Themes
    themes = analysis.get("themes", [])
    if themes:
        lines.append("## Trending Themes")
        lines.append("")
        
        for i, theme in enumerate(themes, 1):
            title = theme.get("title", "")
            count = theme.get("mention_count", 0)
            summary = theme.get("summary", "")
            sources = theme.get("sources", [])
            
            lines.append(f"### {i}. {title} ({count} mentions)")
            lines.append("")
            lines.append(summary)
            lines.append("")
            
            if sources:
                source_links = []
                for s in sources:
                    name = s.get("name", "")
                    url = s.get("url", "")
                    if url:
                        source_links.append(f"[{name}]({url})")
                    else:
                        source_links.append(name)
                lines.append(f"Sources: {', '.join(source_links)}")
                lines.append("")
    
    # Shopify Mentions
    lines.append("## Shopify Mentions")
    lines.append("")
    
    shopify_mentions = analysis.get("shopify_mentions", [])
    if shopify_mentions:
        for mention in shopify_mentions:
            source_name = mention.get("source_name", "")
            source_url = mention.get("source_url", "")
            context = mention.get("context", "")
            quote = mention.get("quote")
            
            if source_url:
                lines.append(f"- **[{source_name}]({source_url})**: {context}")
            else:
                lines.append(f"- **{source_name}**: {context}")
            
            if quote:
                lines.append(f'  > "{quote}"')
            lines.append("")
    else:
        lines.append("_No Shopify mentions in this batch._")
        lines.append("")
    
    # Notable Quotes
    quotes = analysis.get("notable_quotes", [])
    if quotes:
        lines.append("## Notable Quotes")
        lines.append("")
        
        for quote in quotes:
            text = quote.get("quote", "")
            author = quote.get("author", "")
            source_name = quote.get("source_name", "")
            source_url = quote.get("source_url", "")
            
            lines.append(f'> "{text}"')
            if source_url:
                lines.append(f"> — {author}, [{source_name}]({source_url})")
            else:
                lines.append(f"> — {author}, {source_name}")
            lines.append("")
    
    # Trend-Jack Opportunities
    opportunities = analysis.get("trend_jack_opportunities", [])
    if opportunities:
        lines.append("## Trend-Jack Opportunities")
        lines.append("")
        
        for i, opp in enumerate(opportunities, 1):
            theme = opp.get("theme", "")
            opportunity = opp.get("opportunity", "")
            angle = opp.get("angle", "")
            outlet = opp.get("best_outlet", "")
            rationale = opp.get("outlet_rationale", "")
            
            lines.append(f"### {i}. {theme}")
            lines.append("")
            lines.append(f"**Opportunity:** {opportunity}")
            lines.append("")
            lines.append(f"**Angle:** {angle}")
            lines.append("")
            lines.append(f"**Best Outlet:** {outlet}")
            if rationale:
                lines.append(f"({rationale})")
            lines.append("")
    
    # Sources Processed
    sources = analysis.get("sources_processed", [])
    if sources:
        lines.append("## Sources Processed")
        lines.append("")
        
        for source in sources:
            name = source.get("name", "")
            url = source.get("url", "")
            subject = source.get("subject", "")
            date = source.get("date", "")[:10] if source.get("date") else ""
            
            if url:
                lines.append(f"- [{name}]({url}): {subject} ({date})")
            else:
                lines.append(f"- {name}: {subject} ({date})")
        lines.append("")
    
    return "\n".join(lines)


def run_pipeline(
    config: dict,
    dry_run: bool = False,
    skip_slack: bool = False,
    since_days: int = None,
):
    """
    Run the full newsletter intelligence pipeline.

    Args:
        config: Configuration dict
        dry_run: If True, don't post to Slack
        skip_slack: If True, skip Slack posting
        since_days: Override days to look back for emails
    """
    print("=" * 60)
    print("Newsletter Intelligence Pipeline")
    print("=" * 60)
    print()
    
    # Step 1: Fetch emails from Gmail
    print("Step 1: Fetching emails from Gmail...")
    fetcher = GmailFetcher(config)
    
    if not fetcher.authenticate():
        print("Gmail authentication failed. Run: python -m src.gmail_fetcher")
        return False
    
    # Determine date range
    if since_days is not None:
        from datetime import timedelta
        since_date = datetime.now() - timedelta(days=since_days)
    else:
        since_date = None  # Uses config default
    
    emails = fetcher.fetch_emails(since_date=since_date)
    print(f"Fetched {len(emails)} emails")
    
    if not emails:
        print("No emails found. Nothing to process.")
        return True
    
    # Step 2: Parse email content
    print("\nStep 2: Parsing email content...")
    parsed_emails = parse_emails(emails, SOURCES_PATH)
    print(f"Parsed {len(parsed_emails)} emails")
    
    # Step 3: Analyze with Claude
    print("\nStep 3: Analyzing content with Claude...")
    analyzer = ThemeAnalyzer(config, PROMPTS_PATH)
    analysis = analyzer.analyze(parsed_emails)
    
    if "error" in analysis:
        print(f"Analysis error: {analysis['error']}")
        return False
    
    theme_count = len(analysis.get("themes", []))
    shopify_count = len(analysis.get("shopify_mentions", []))
    print(f"Found {theme_count} themes, {shopify_count} Shopify mentions")
    
    # Step 4: Save markdown summary
    print("\nStep 4: Saving markdown summary...")
    save_markdown_summary(analysis, config)
    
    # Step 5: Post to Slack
    if dry_run:
        print("\nStep 5: Skipping Slack (dry run mode)")
        print("\nAnalysis preview:")
        print(json.dumps(analysis, indent=2, default=str)[:2000])
    elif skip_slack:
        print("\nStep 5: Skipping Slack (--skip-slack flag)")
    else:
        print("\nStep 5: Posting to Slack...")
        publisher = SlackPublisher(config)
        if publisher.publish(analysis):
            print("Posted to Slack successfully")
        else:
            print("Failed to post to Slack")
            return False
    
    # Update state
    state = load_state()
    state["last_run"] = datetime.now().isoformat()
    state["emails_processed"] = len(emails)
    state["themes_found"] = theme_count
    save_state(state)
    
    print("\n" + "=" * 60)
    print("Pipeline completed successfully!")
    print("=" * 60)
    
    return True


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Newsletter Intelligence Aggregator for Shopify Communications"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline but don't post to Slack",
    )
    parser.add_argument(
        "--skip-slack",
        action="store_true",
        help="Skip Slack posting (still saves markdown)",
    )
    parser.add_argument(
        "--since-days",
        type=int,
        help="Override: fetch emails from last N days",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run interactive setup (Gmail OAuth)",
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(PROJECT_ROOT / ".env")
    
    # Load configuration
    config = load_config()
    
    # Run setup if requested
    if args.setup:
        from .gmail_fetcher import setup_gmail_oauth
        setup_gmail_oauth()
        return
    
    # Run pipeline
    success = run_pipeline(
        config=config,
        dry_run=args.dry_run,
        skip_slack=args.skip_slack,
        since_days=args.since_days,
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
