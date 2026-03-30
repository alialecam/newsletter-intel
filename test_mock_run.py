"""Mock test to demonstrate pipeline output with sample data."""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Sample mock emails simulating real newsletter content
MOCK_EMAILS = [
    {
        "id": "msg001",
        "subject": "The Age of AI Agents is Here",
        "from": "Alex Kantrowitz <bigtechnology@substack.com>",
        "date": (datetime.now() - timedelta(days=1)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
        "body_html": """
        <html><body>
        <h1>The Age of AI Agents is Here</h1>
        <p>Enterprise software is undergoing its biggest transformation since the cloud. AI agents—autonomous systems that can execute multi-step workflows—are moving from demos to production deployments.</p>
        <p>Companies like Salesforce, ServiceNow, and <strong>Shopify</strong> are racing to build agent capabilities into their platforms. Shopify's approach is particularly interesting: rather than building flashy chatbots, they're embedding AI into checkout flows where it improves conversion rates without users even noticing.</p>
        <p>"The agent era is here, and it's messier than anyone predicted," one enterprise CTO told me. "But the companies that figure it out will have a massive advantage."</p>
        <p>OpenAI's new pricing tiers are forcing startups to rethink their cost structures. Some are turning to open-source alternatives like Llama and Mistral.</p>
        <a href="https://www.bigtechnology.com/p/ai-agents-enterprise">Read more</a>
        </body></html>
        """,
        "body_text": "",
        "snippet": "Enterprise software is undergoing its biggest transformation..."
    },
    {
        "id": "msg002", 
        "subject": "Stratechery: Platform Economics in the AI Era",
        "from": "Ben Thompson <email@stratechery.com>",
        "date": (datetime.now() - timedelta(days=2)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
        "body_html": """
        <html><body>
        <h1>Platform Economics in the AI Era</h1>
        <p>The platform dynamics that defined the last decade of tech are shifting. AI changes the calculus of build vs. buy, and that has implications for every platform company.</p>
        <p>Consider Shopify: their platform model depends on third-party developers building apps. But if AI can generate custom integrations on demand, what happens to the app ecosystem?</p>
        <p>The answer isn't obvious. Platforms that embrace AI tooling may actually strengthen their ecosystems by lowering the barrier to entry for developers.</p>
        <p>Sam Altman spoke at a conference this week about "the next phase" of AI deployment. Meanwhile, Google announced new Gemini capabilities targeting enterprise workflows.</p>
        <a href="https://stratechery.com/2026/platform-economics-ai">Read the full analysis</a>
        </body></html>
        """,
        "body_text": "",
        "snippet": "The platform dynamics that defined the last decade..."
    },
    {
        "id": "msg003",
        "subject": "TLDR AI: OpenAI Pricing Changes, Agent Frameworks, and More",
        "from": "Dan <dan@tldrnewsletter.com>",
        "date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
        "body_html": """
        <html><body>
        <h1>TLDR AI</h1>
        <h2>Big News</h2>
        <p><strong>OpenAI announces new pricing tiers</strong> - The new structure includes a "pro" tier at $200/month with higher rate limits and priority access to new models.</p>
        <p><strong>AI Agents going mainstream</strong> - Enterprise adoption of AI agents accelerated in Q1, with Gartner predicting 30% of enterprises will have production agent deployments by year end.</p>
        <h2>Tools & Launches</h2>
        <p>Microsoft released new Azure AI Agent Service. Anthropic updated Claude with improved tool use.</p>
        <p>Sam Altman hinted at GPT-5 capabilities in a podcast interview.</p>
        <a href="https://tldr.tech/ai">Read more at TLDR</a>
        </body></html>
        """,
        "body_text": "",
        "snippet": "OpenAI announces new pricing tiers..."
    },
    {
        "id": "msg004",
        "subject": "Lenny's Newsletter: The Rise of Invisible AI",
        "from": "Lenny Rachitsky <lenny@substack.com>",
        "date": (datetime.now() - timedelta(days=1)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
        "body_html": """
        <html><body>
        <h1>The Rise of Invisible AI</h1>
        <p>The best AI products are ones you don't notice. I've been tracking a trend I call "invisible AI"—AI that improves products without requiring users to change their behavior.</p>
        <p>Shopify is a great example. Their AI-powered checkout doesn't ask users to chat with a bot. It just... works better. Conversion rates go up, and users don't even know AI is involved.</p>
        <p>This is the opposite of the chatbot hype cycle. Instead of making AI the interface, the best PMs are making AI the infrastructure.</p>
        <p>"We're not building AI products. We're building better products that happen to use AI," a Shopify PM told me.</p>
        <a href="https://www.lennysnewsletter.com/p/invisible-ai">Full post</a>
        </body></html>
        """,
        "body_text": "",
        "snippet": "The best AI products are ones you don't notice..."
    },
    {
        "id": "msg005",
        "subject": "Platformer: The Policy Implications of AI Agents",
        "from": "Casey Newton <casey@platformer.news>",
        "date": (datetime.now() - timedelta(days=2)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
        "body_html": """
        <html><body>
        <h1>The Policy Implications of AI Agents</h1>
        <p>As AI agents become more autonomous, regulators are scrambling to catch up. The EU is already considering extensions to the AI Act that would cover autonomous agent systems.</p>
        <p>The core question: when an AI agent makes a decision that harms someone, who's liable? The user who deployed it? The company that built it? The platform it runs on?</p>
        <p>OpenAI's pricing changes are also drawing regulatory attention, with some arguing the tiered access creates unfair advantages for well-funded companies.</p>
        <a href="https://www.platformer.news/ai-agents-policy">Read more</a>
        </body></html>
        """,
        "body_text": "",
        "snippet": "As AI agents become more autonomous..."
    }
]

# Mock analysis result (what Claude would return)
MOCK_ANALYSIS = {
    "date_range": {
        "start": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "end": datetime.now().strftime("%Y-%m-%d")
    },
    "themes": [
        {
            "title": "AI Agents in Enterprise",
            "mention_count": 4,
            "summary": "Enterprise software is rapidly shifting toward autonomous AI agents that can execute multi-step workflows without human intervention. The consensus across multiple newsletters is that 2026 will be the 'year of deployment' as pilot programs mature into production systems. Gartner predicts 30% of enterprises will have production agent deployments by year end.",
            "sources": [
                {"name": "Big Technology", "url": "https://www.bigtechnology.com/p/ai-agents-enterprise", "context": "Deep dive on enterprise adoption"},
                {"name": "TLDR", "url": "https://tldr.tech/ai", "context": "News roundup on agent frameworks"},
                {"name": "Platformer", "url": "https://www.platformer.news/ai-agents-policy", "context": "Policy implications"},
                {"name": "Stratechery", "url": "https://stratechery.com/2026/platform-economics-ai", "context": "Platform economics angle"}
            ]
        },
        {
            "title": "OpenAI Pricing Restructure",
            "mention_count": 3,
            "summary": "OpenAI's new tiered pricing model is forcing startups to reconsider their AI cost structures. The new 'pro' tier at $200/month offers higher rate limits and priority access, but some argue this creates unfair advantages for well-funded companies. Several newsletters noted this could accelerate the shift toward open-source alternatives like Llama and Mistral.",
            "sources": [
                {"name": "TLDR", "url": "https://tldr.tech/ai", "context": "Pricing announcement coverage"},
                {"name": "Big Technology", "url": "https://www.bigtechnology.com/p/ai-agents-enterprise", "context": "Cost structure implications"},
                {"name": "Platformer", "url": "https://www.platformer.news/ai-agents-policy", "context": "Regulatory attention"}
            ]
        },
        {
            "title": "Invisible AI UX Pattern",
            "mention_count": 2,
            "summary": "A counter-narrative to the chatbot hype is emerging: the best AI products are ones users don't notice. Rather than making AI the interface, leading companies are making AI the infrastructure—improving products without changing user behavior. This 'invisible AI' approach is gaining traction among product leaders.",
            "sources": [
                {"name": "Lenny's Newsletter", "url": "https://www.lennysnewsletter.com/p/invisible-ai", "context": "Product strategy perspective"},
                {"name": "Big Technology", "url": "https://www.bigtechnology.com/p/ai-agents-enterprise", "context": "Shopify example"}
            ]
        }
    ],
    "shopify_mentions": [
        {
            "source_name": "Big Technology",
            "source_url": "https://www.bigtechnology.com/p/ai-agents-enterprise",
            "context": "Referenced Shopify's approach to AI agents as 'particularly interesting'—embedding AI into checkout flows where it improves conversion rates without users noticing, rather than building flashy chatbots.",
            "sentiment": "positive",
            "quote": None
        },
        {
            "source_name": "Stratechery",
            "source_url": "https://stratechery.com/2026/platform-economics-ai",
            "context": "Discussed Shopify's platform model in the context of AI's impact on app ecosystems. Raised the question of what happens to third-party developers if AI can generate custom integrations on demand.",
            "sentiment": "neutral",
            "quote": None
        },
        {
            "source_name": "Lenny's Newsletter",
            "source_url": "https://www.lennysnewsletter.com/p/invisible-ai",
            "context": "Highlighted Shopify as a 'great example' of invisible AI—their AI-powered checkout improves conversion rates without users even knowing AI is involved.",
            "sentiment": "positive",
            "quote": "We're not building AI products. We're building better products that happen to use AI."
        }
    ],
    "notable_quotes": [
        {
            "quote": "The agent era is here, and it's messier than anyone predicted.",
            "author": "Enterprise CTO (anonymous)",
            "source_name": "Big Technology",
            "source_url": "https://www.bigtechnology.com/p/ai-agents-enterprise",
            "relevance": "Captures the current state of enterprise AI adoption"
        },
        {
            "quote": "We're not building AI products. We're building better products that happen to use AI.",
            "author": "Shopify PM",
            "source_name": "Lenny's Newsletter",
            "source_url": "https://www.lennysnewsletter.com/p/invisible-ai",
            "relevance": "Defines the 'invisible AI' product philosophy"
        }
    ],
    "trend_jack_opportunities": [
        {
            "theme": "AI Agents + Commerce",
            "opportunity": "Position Shopify as enabling 'agent-ready storefronts'—merchants need to prepare for AI agents as customers",
            "angle": "While competitors focus on chatbots, Shopify is building infrastructure for the next generation of AI-powered commerce where agents browse, compare, and purchase on behalf of users",
            "best_outlet": "Big Technology",
            "outlet_rationale": "Alex Kantrowitz covers the intersection of tech and business; his audience includes enterprise decision-makers interested in practical AI applications"
        },
        {
            "theme": "Invisible AI as Product Philosophy",
            "opportunity": "Shopify's approach to AI that 'just works' vs. chatbot-forward competitors",
            "angle": "Counter-narrative to the chatbot hype cycle—the best AI is AI users never see. Shopify's checkout improvements are proof that invisible AI drives better outcomes than conversational interfaces",
            "best_outlet": "Lenny's Newsletter",
            "outlet_rationale": "Lenny's audience is product managers and builders who care about UX philosophy; this angle would resonate with his 'invisible AI' thesis"
        },
        {
            "theme": "Platform Economics in the AI Era",
            "opportunity": "How Shopify's platform model adapts to AI tooling—ecosystem play vs. vertically integrated competitors",
            "angle": "AI doesn't weaken platforms, it strengthens them. Shopify's bet is that AI lowers the barrier to entry for developers, growing the app ecosystem rather than replacing it",
            "best_outlet": "Stratechery",
            "outlet_rationale": "Ben Thompson's strategy-focused analysis reaches influential tech executives and investors; platform economics is his core expertise"
        }
    ],
    "people_mentioned": [
        {
            "name": "Sam Altman",
            "mention_count": 2,
            "context": "OpenAI CEO; mentioned in context of GPT-5 hints and conference remarks about 'next phase' of AI",
            "sources": ["TLDR", "Stratechery"]
        }
    ],
    "companies_mentioned": [
        {
            "name": "OpenAI",
            "mention_count": 4,
            "context": "Pricing changes, new model announcements, regulatory attention",
            "sources": ["TLDR", "Big Technology", "Platformer", "Stratechery"]
        },
        {
            "name": "Google",
            "mention_count": 2,
            "context": "Gemini capabilities for enterprise workflows",
            "sources": ["Stratechery", "TLDR"]
        }
    ],
    "sources_processed": [
        {"name": "Big Technology", "url": "https://www.bigtechnology.com/p/ai-agents-enterprise", "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), "subject": "The Age of AI Agents is Here"},
        {"name": "Stratechery", "url": "https://stratechery.com/2026/platform-economics-ai", "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"), "subject": "Platform Economics in the AI Era"},
        {"name": "TLDR", "url": "https://tldr.tech/ai", "date": datetime.now().strftime("%Y-%m-%d"), "subject": "TLDR AI: OpenAI Pricing Changes, Agent Frameworks, and More"},
        {"name": "Lenny's Newsletter", "url": "https://www.lennysnewsletter.com/p/invisible-ai", "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), "subject": "The Rise of Invisible AI"},
        {"name": "Platformer", "url": "https://www.platformer.news/ai-agents-policy", "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"), "subject": "The Policy Implications of AI Agents"}
    ]
}


def build_slack_preview(analysis: dict) -> str:
    """Build a text preview of what the Slack message would look like."""
    lines = []
    
    date_range = analysis.get("date_range", {})
    start = date_range.get("start", "")
    end = date_range.get("end", "")
    
    lines.append("=" * 70)
    lines.append(f"  NEWSLETTER INTEL | {start} to {end}")
    lines.append("=" * 70)
    lines.append("")
    
    # Themes
    lines.append("━" * 70)
    lines.append("TRENDING THEMES")
    lines.append("━" * 70)
    lines.append("")
    
    for i, theme in enumerate(analysis.get("themes", []), 1):
        title = theme.get("title", "")
        count = theme.get("mention_count", 0)
        summary = theme.get("summary", "")
        sources = theme.get("sources", [])
        
        lines.append(f"{i}. {title} ({count} mentions)")
        lines.append("")
        # Wrap summary
        words = summary.split()
        current_line = "   "
        for word in words:
            if len(current_line) + len(word) + 1 > 70:
                lines.append(current_line)
                current_line = "   " + word
            else:
                current_line += " " + word if current_line.strip() else "   " + word
        if current_line.strip():
            lines.append(current_line)
        lines.append("")
        
        source_names = [s.get("name", "") for s in sources]
        lines.append(f"   → {' | '.join(source_names)}")
        lines.append("")
    
    # Shopify Mentions
    lines.append("━" * 70)
    lines.append("SHOPIFY MENTIONS")
    lines.append("━" * 70)
    lines.append("")
    
    for mention in analysis.get("shopify_mentions", []):
        source = mention.get("source_name", "")
        context = mention.get("context", "")
        quote = mention.get("quote")
        
        lines.append(f"• {source}:")
        # Wrap context
        words = context.split()
        current_line = "  "
        for word in words:
            if len(current_line) + len(word) + 1 > 68:
                lines.append(current_line)
                current_line = "  " + word
            else:
                current_line += " " + word if current_line.strip() else "  " + word
        if current_line.strip():
            lines.append(current_line)
        
        if quote:
            lines.append(f'  → "{quote}"')
        lines.append("")
    
    # Notable Quotes
    lines.append("━" * 70)
    lines.append("NOTABLE QUOTES")
    lines.append("━" * 70)
    lines.append("")
    
    for quote in analysis.get("notable_quotes", []):
        text = quote.get("quote", "")
        author = quote.get("author", "")
        source = quote.get("source_name", "")
        
        lines.append(f'"{text}"')
        lines.append(f"— {author}, {source}")
        lines.append("")
    
    # Trend-Jack Opportunities
    lines.append("━" * 70)
    lines.append("TREND-JACK OPPORTUNITIES")
    lines.append("━" * 70)
    lines.append("")
    
    for i, opp in enumerate(analysis.get("trend_jack_opportunities", []), 1):
        theme = opp.get("theme", "")
        opportunity = opp.get("opportunity", "")
        angle = opp.get("angle", "")
        outlet = opp.get("best_outlet", "")
        rationale = opp.get("outlet_rationale", "")
        
        lines.append(f"{i}. {theme}")
        lines.append(f"   Opportunity: {opportunity}")
        lines.append(f"   Angle: {angle[:80]}..." if len(angle) > 80 else f"   Angle: {angle}")
        lines.append(f"   Best outlet: {outlet} ({rationale[:50]}...)" if len(rationale) > 50 else f"   Best outlet: {outlet} ({rationale})")
        lines.append("")
    
    # Sources
    lines.append("━" * 70)
    sources = analysis.get("sources_processed", [])
    lines.append(f"SOURCES PROCESSED ({len(sources)} newsletters)")
    lines.append("━" * 70)
    source_names = [s.get("name", "") for s in sources]
    lines.append(" • ".join(source_names))
    lines.append("")
    lines.append("=" * 70)
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  MOCK TEST: Newsletter Intelligence Pipeline")
    print("  (Using sample data to demonstrate output format)")
    print("=" * 70 + "\n")
    
    print(f"Processing {len(MOCK_EMAILS)} mock newsletter emails...\n")
    
    # Show what Slack output would look like
    slack_preview = build_slack_preview(MOCK_ANALYSIS)
    print(slack_preview)
    
    # Also save the JSON analysis
    print("\n" + "=" * 70)
    print("  RAW ANALYSIS JSON (truncated)")
    print("=" * 70 + "\n")
    print(json.dumps(MOCK_ANALYSIS, indent=2)[:3000])
    print("\n... (truncated)")
