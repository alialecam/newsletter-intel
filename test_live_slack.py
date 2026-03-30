"""Test posting mock analysis to Slack with live credentials."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import yaml

# Load config
with open(Path(__file__).parent / "config" / "config.yaml") as f:
    config = yaml.safe_load(f)

# Mock analysis (simulating what Claude would return)
MOCK_ANALYSIS = {
    "date_range": {
        "start": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "end": datetime.now().strftime("%Y-%m-%d")
    },
    "themes": [
        {
            "title": "AI Agents in Enterprise",
            "mention_count": 4,
            "summary": "Enterprise software is rapidly shifting toward autonomous AI agents that can execute multi-step workflows without human intervention. The consensus across multiple newsletters is that 2026 will be the 'year of deployment' as pilot programs mature into production systems.",
            "sources": [
                {"name": "Big Technology", "url": "https://www.bigtechnology.com/", "context": "Deep dive on enterprise adoption"},
                {"name": "TLDR", "url": "https://tldr.tech/", "context": "News roundup"},
                {"name": "Stratechery", "url": "https://stratechery.com/", "context": "Platform economics angle"}
            ]
        },
        {
            "title": "OpenAI Pricing Changes",
            "mention_count": 3,
            "summary": "OpenAI's new tiered pricing model is forcing startups to reconsider their AI cost structures. Several newsletters noted this could accelerate the shift toward open-source alternatives.",
            "sources": [
                {"name": "TLDR", "url": "https://tldr.tech/", "context": "Pricing coverage"},
                {"name": "Platformer", "url": "https://www.platformer.news/", "context": "Regulatory angle"}
            ]
        }
    ],
    "shopify_mentions": [
        {
            "source_name": "Big Technology",
            "source_url": "https://www.bigtechnology.com/",
            "context": "Referenced Shopify's approach to AI agents—embedding AI into checkout flows where it improves conversion rates without users noticing.",
            "sentiment": "positive",
            "quote": None
        },
        {
            "source_name": "Lenny's Newsletter",
            "source_url": "https://www.lennysnewsletter.com/",
            "context": "Highlighted Shopify as a 'great example' of invisible AI—their AI-powered checkout improves conversion without users knowing.",
            "sentiment": "positive",
            "quote": "We're not building AI products. We're building better products that happen to use AI."
        }
    ],
    "notable_quotes": [
        {
            "quote": "The agent era is here, and it's messier than anyone predicted.",
            "author": "Alex Kantrowitz",
            "source_name": "Big Technology",
            "source_url": "https://www.bigtechnology.com/"
        }
    ],
    "trend_jack_opportunities": [
        {
            "theme": "AI Agents + Commerce",
            "opportunity": "Position Shopify as enabling 'agent-ready storefronts'",
            "angle": "Merchants need to prepare for AI agents as customers",
            "best_outlet": "Big Technology",
            "outlet_rationale": "Tech + business crossover audience"
        },
        {
            "theme": "Invisible AI UX",
            "opportunity": "Shopify's AI that 'just works' vs. chatbot-forward competitors",
            "angle": "Counter-narrative to the chatbot hype cycle",
            "best_outlet": "Lenny's Newsletter",
            "outlet_rationale": "Product/UX focused audience"
        }
    ],
    "sources_processed": [
        {"name": "Big Technology", "url": "https://www.bigtechnology.com/", "date": datetime.now().strftime("%Y-%m-%d"), "subject": "The Age of AI Agents"},
        {"name": "Stratechery", "url": "https://stratechery.com/", "date": datetime.now().strftime("%Y-%m-%d"), "subject": "Platform Economics"},
        {"name": "TLDR", "url": "https://tldr.tech/", "date": datetime.now().strftime("%Y-%m-%d"), "subject": "AI News Roundup"},
        {"name": "Lenny's Newsletter", "url": "https://www.lennysnewsletter.com/", "date": datetime.now().strftime("%Y-%m-%d"), "subject": "Invisible AI"},
        {"name": "Platformer", "url": "https://www.platformer.news/", "date": datetime.now().strftime("%Y-%m-%d"), "subject": "AI Policy"}
    ]
}

if __name__ == "__main__":
    print("Testing Slack integration with mock analysis...")
    print()
    
    from slack_publisher import SlackPublisher
    
    try:
        publisher = SlackPublisher(config)
        print(f"✓ Slack credentials loaded")
        print(f"  Channel: {publisher.channel}")
        print()
        
        print("Posting mock analysis to Slack...")
        success = publisher.publish(MOCK_ANALYSIS)
        
        if success:
            print("✓ Posted successfully! Check your Slack DM.")
        else:
            print("✗ Failed to post")
            
    except Exception as e:
        print(f"✗ Error: {e}")
