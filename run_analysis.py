"""Run real newsletter analysis using gworkspace MCP data and Claude."""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / "src"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import yaml
import anthropic

# Load config
with open(Path(__file__).parent / "config" / "config.yaml") as f:
    config = yaml.safe_load(f)

# Load prompt template
with open(Path(__file__).parent / "config" / "prompts" / "summarize.txt") as f:
    PROMPT_TEMPLATE = f.read()

# Real newsletter content from your Gmail (fetched via gworkspace MCP)
NEWSLETTERS = [
    {
        "source": "Lenny's Newsletter",
        "subject": '"Engineers are becoming sorcerers" | The future of software development with OpenAI\'s Sherwin Wu',
        "date": "Thu, 12 Feb 2026",
        "url": "https://www.lennysnewsletter.com/p/engineers-are-becoming-sorcerers",
        "content": """
Sherwin Wu leads engineering for OpenAI's API platform, where roughly 95% of engineers use Codex, often working with fleets of 10 to 20 parallel AI agents.

We discuss:
- What OpenAI did to cut code review times from 10-15 minutes to 2-3 minutes
- How AI is changing the role of managers
- Why the productivity gap between AI power users and everyone else is widening
- Why "models will eat your scaffolding for breakfast"
- Why the next 12 to 24 months are a rare window where engineers can leap ahead before the role fully transforms

Key quote from Nicolas Bustamante: "LLMs Eat Scaffolding for Breakfast"

The Bitter Lesson applies - bet on compute and general methods, not clever engineering.

Sam Altman mentioned regarding the pace of AI development.
Sarah Friar (OpenAI CFO) referenced on AI's business impact.
"""
    },
    {
        "source": "Platformer",
        "subject": "Exclusive: OpenAI disbanded its mission alignment team",
        "date": "Wed, 11 Feb 2026", 
        "url": "https://www.platformer.news/openai-mission-alignment-team",
        "content": """
OpenAI disbanded its mission alignment team in recent weeks and transferred its seven employees to other teams. Joshua Achiam, who led the team, will take on a new title as OpenAI's "chief futurist."

The mission alignment team was created in 2024 to promote the company's stated mission to ensure that artificial general intelligence benefits all of humanity.

"The Mission Alignment function was an experiment that grew organically around a wide range of work spanning from running workshops for senior leaders within the company to studying the impacts of AI on international relations, philanthropy, and novel areas of risks," Achiam told me.

Some within the company saw the mission alignment team as a kind of spiritual successor to OpenAI's superalignment team, which was dissolved in spring 2024 after team leaders Ilya Sutskever and Jan Leike left the company.

Meanwhile, another two xAI cofounders are gone - Tony Wu and Jimmy Ba. By now, half of xAI's founding team has left. Wu wrote: "I will deeply miss the people, the warrooms, and all those battles we have fought together."

At Anthropic, senior safety researcher Mrinank Sharma left with an enigmatic departure letter saying "I've repeatedly seen how hard it is to truly let our values govern our actions," and announced plans to become a poet.

Jack Clark (Anthropic co-founder) joked in September 2025: "People leaving regular companies: Time for a change! People leaving AI companies: I have gazed into the endless night and there are shapes out there."

Sen. Elizabeth Warren plans to introduce a bill to ban the sale of certain AI chips to China, following a meeting with Anthropic CEO Dario Amodei.

OpenAI is bringing ChatGPT to the Pentagon's AI platform GenAI.mil.
"""
    },
    {
        "source": "TLDR",
        "subject": "xAI public all hands, inside Siri revamp, AI changing everything",
        "date": "Thu, 12 Feb 2026",
        "url": "https://tldr.tech/",
        "content": """
Elon Musk has restructured xAI following the exit of two of its co-founders earlier this week.

Apple's Siri team is undergoing major changes as the company races to catch up in AI.

AI continues to transform industries across the board - from healthcare to finance to manufacturing.

GLM-5 is a new MIT-licensed model with 754 billion parameters delivering significant performance improvements.

ChatGPT skills allow developers to submit apps directly to ChatGPT.

OpenAI released new agent frameworks including Responses API, Agents SDK, and AgentKit.
"""
    },
    {
        "source": "Axios AI+",
        "subject": "Scared as hell",
        "date": "Thu, 12 Feb 2026",
        "url": "https://www.axios.com/newsletters/axios-ai-plus",
        "content": """
Anthropic subscriptions are rising significantly.

The AI industry is moving at breakneck speed, leaving many feeling overwhelmed.

Discussion of AI safety concerns and the rapid pace of capability improvements.

Anthropic's Dario Amodei continues to advocate for responsible AI development.

Major tech companies racing to deploy AI agents in enterprise settings.
"""
    },
    {
        "source": "TLDR AI",
        "subject": "GLM-5, ChatGPT skills, harness engineering",
        "date": "Thu, 12 Feb 2026",
        "url": "https://tldr.tech/ai",
        "content": """
GLM-5 is a new MIT-licensed model with 754 billion parameters. It delivers significant performance improvements over previous open models.

ChatGPT skills allow developers to build and submit apps directly to ChatGPT's ecosystem.

OpenAI's new harness engineering approach is changing how developers build AI applications.

Agent development continues to accelerate with new frameworks and tools.
"""
    }
]

def run_analysis():
    """Run the full analysis pipeline."""
    print("=" * 60)
    print("Newsletter Intelligence - Live Analysis")
    print("=" * 60)
    print()
    
    # Prepare content for Claude
    content_parts = []
    for nl in NEWSLETTERS:
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
    # Use replace instead of format to avoid issues with JSON braces in template
    prompt = PROMPT_TEMPLATE.replace("{content}", full_content)
    
    print(f"Analyzing {len(NEWSLETTERS)} newsletters with Claude...")
    print()
    
    # Initialize Anthropic client with Shopify proxy
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return None
    
    client = anthropic.Anthropic(
        api_key=api_key,
        base_url=base_url
    )
    
    # Call Claude
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        print("Claude analysis complete!")
        print()
        
        # Parse JSON from response
        text = response_text.strip()
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
        
        if not text.startswith("{"):
            start = text.find("{")
            if start >= 0:
                depth = 0
                for i, char in enumerate(text[start:], start):
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            text = text[start:i+1]
                            break
        
        analysis = json.loads(text)
        
        # Add metadata
        analysis["date_range"] = {
            "start": "2026-02-11",
            "end": "2026-02-12"
        }
        
        # Ensure sources_processed exists
        if "sources_processed" not in analysis:
            analysis["sources_processed"] = [
                {"name": nl["source"], "url": nl["url"], "date": nl["date"], "subject": nl["subject"]}
                for nl in NEWSLETTERS
            ]
        
        return analysis
        
    except Exception as e:
        print(f"Error: {e}")
        return None


def post_to_slack(analysis):
    """Post analysis to Slack."""
    from slack_publisher import SlackPublisher
    
    print("Posting to Slack...")
    publisher = SlackPublisher(config)
    success = publisher.publish(analysis)
    
    if success:
        print("✓ Posted successfully! Check your Slack.")
    else:
        print("✗ Failed to post to Slack")
    
    return success


if __name__ == "__main__":
    analysis = run_analysis()
    
    if analysis:
        print("=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60)
        print()
        
        # Show themes
        print("THEMES:")
        for theme in analysis.get("themes", []):
            print(f"  • {theme.get('title')} ({theme.get('mention_count')} mentions)")
        print()
        
        # Show Shopify mentions
        print("SHOPIFY MENTIONS:")
        mentions = analysis.get("shopify_mentions", [])
        if mentions:
            for m in mentions:
                print(f"  • {m.get('source_name')}: {m.get('context', '')[:100]}...")
        else:
            print("  (none found)")
        print()
        
        # Show trend-jack opportunities
        print("TREND-JACK OPPORTUNITIES:")
        for opp in analysis.get("trend_jack_opportunities", []):
            print(f"  • {opp.get('theme')}")
            print(f"    Outlet: {opp.get('best_outlet')}")
        print()
        
        # Post to Slack
        print("=" * 60)
        post_to_slack(analysis)
