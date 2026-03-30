"""Run comprehensive newsletter analysis using all subscribed sources."""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

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

# Full newsletter content from Gmail (last 3 days via gworkspace MCP)
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

Referenced: Sam Altman, Sarah Friar (OpenAI CFO), Kevin Weil (CPO at OpenAI).
"""
    },
    {
        "source": "Platformer",
        "subject": "Exclusive: OpenAI disbanded its mission alignment team",
        "date": "Wed, 11 Feb 2026", 
        "url": "https://www.platformer.news/openai-mission-alignment-team-joshua-achiam/",
        "content": """
OpenAI disbanded its mission alignment team in recent weeks and transferred its seven employees to other teams. Joshua Achiam, who led the team, will take on a new title as OpenAI's "chief futurist."

The mission alignment team was created in 2024 to promote the company's stated mission to ensure that artificial general intelligence benefits all of humanity.

"The Mission Alignment function was an experiment that grew organically around a wide range of work spanning from running workshops for senior leaders within the company to studying the impacts of AI on international relations, philanthropy, and novel areas of risks," Achiam told me.

Some within the company saw the mission alignment team as a kind of spiritual successor to OpenAI's superalignment team, which was dissolved in spring 2024 after team leaders Ilya Sutskever and Jan Leike left the company.

Meanwhile, another two xAI cofounders are gone - Tony Wu and Jimmy Ba. By now, half of xAI's founding team has left. Wu wrote: "I will deeply miss the people, the warrooms, and all those battles we have fought together."

At Anthropic, senior safety researcher Mrinank Sharma left with an enigmatic departure letter saying "I've repeatedly seen how hard it is to truly let our values govern our actions," and announced plans to become a poet.

Jack Clark (Anthropic co-founder) joked: "People leaving regular companies: Time for a change! People leaving AI companies: I have gazed into the endless night and there are shapes out there."

Sen. Elizabeth Warren plans to introduce a bill to ban the sale of certain AI chips to China, following a meeting with Anthropic CEO Dario Amodei.

OpenAI is bringing ChatGPT to the Pentagon's AI platform GenAI.mil.
"""
    },
    {
        "source": "TBPN",
        "subject": "AI Is Not Covid",
        "date": "Wed, 11 Feb 2026",
        "url": "https://tbpn.substack.com/p/ai-is-not-covid",
        "content": """
The current thing in tech and business is the viral article about AI progress by Matt Shumer called "Something Big Is Happening."

Today's lineup includes:
- Shopify President Harley Finkelstein at 12:00 PM
- "Something Big Is Happening" author Matt Shumer at 12:15 PM
- Index Ventures Partner Danny Rimer at 12:30 PM
- Robinhood Co-Founder and CEO Vlad Tenev at 1:00 PM

Daily Op-Ed by John Coogan: AI Is Not Covid

I hate the Covid analogy because the number of people who caught Covid didn't follow an exponential curve, it was a logistic curve. Eventually the number of cases plateaued. 

If you model the power of artificial intelligence as a function of energy, we do have plenty of room for exponential growth. Humanity is 13 orders of magnitude away from Kardashev Type 2 (aka Dyson Sphere capturing 100% of the sun's energy).

I do like Matt's framing of "It's time to talk to your friends outside the tech world about AI."

New coding models are remarkable, and they will clearly reshuffle the economics of the tech industry and permanently change the role of software engineers in most companies.

Special thanks to sponsors: Shopify, Graphite, ElevenLabs, CrowdStrike, MongoDB, and more.
"""
    },
    {
        "source": "Techmeme",
        "subject": "xAI reorganizes, Z.ai launches GLM-5",
        "date": "Thu, 12 Feb 2026",
        "url": "https://www.techmeme.com",
        "content": """
TOP NEWS:

Elon Musk announces an xAI reorganization that "required parting ways with some people", after two xAI co-founders announced they were leaving this week.

xAI will be organized into four core areas: Grok's chatbot and voice products, coding, Imagine, and Macrohard, which will build digital agents to run companies.

xAI All-Hands Meeting: Elon Musk told employees that xAI needs a factory on the moon to build AI satellites and a massive catapult to launch them into space.

Z.AI launches GLM-5, its flagship open-weight model, saying it has best-in-class performance among open-source models in reasoning, coding, and agentic tasks.

GLM-5 pricing is absurd: $0.80 per million input tokens, $2.56 per million output tokens. For context: Claude Opus 4.6: $5/$25, GPT 5.3 Codex: $1.75/$14. China isn't just competing - they're undercutting everyone while shipping frontier-level models.

GPT-5.3-Codex and Claude Opus 4.6 can meaningfully contribute to the improvement of AI models, a sign of what's coming for most knowledge work within five years (Matt Shumer article).

EARNINGS:
SHOPIFY reports Q4 revenue up 31% YoY to $3.7B, vs. $3.59B est., net income down 43% YoY to $743M, and forecasts Q1 revenue growth above est; SHOP drops 10%+

Cisco reports Q2 revenue up 10% YoY to $15.35B, vs. $15.12B est.

AppLovin reports Q4 revenue up 66% YoY to $1.66B.

AI NEWS:
Anthropic CCO Paul Smith says the startup is focused on "growing revenue" rather than "flashy headlines", calls the software stock selloff "hyperbole".

Source: To catch leakers, OpenAI security staff use a custom ChatGPT with access to Slack, email, and docs that cross-references news articles with access logs.

OpenAI announced that the US military will get access to ChatGPT via GenAI.mil.

Google told advertisers it is integrating shopping features into Search's AI Mode and Gemini.

Anthropic says Claude users on the free plan can now create files, connect to external services, use skills, and more.
"""
    },
    {
        "source": "Superhuman AI",
        "subject": "New Chinese model outpaces rivals",
        "date": "Thu, 12 Feb 2026",
        "url": "https://www.superhuman.ai",
        "content": """
An AI-generated essay (that ironically warns everyone about the dangers of AI) is going mega viral. The post has generated over 70 million views.

1. New Chinese model rivals OpenAI and Google across multiple benchmarks: Chinese startup Zhipu AI just dropped GLM-5, an open-source model that's giving proprietary rivals like Google, OpenAI, and Anthropic a run for their money on multiple benchmarks. The MIT-licensed model features a native "Agent Mode" that turns prompts into ready-to-use documents.

2. xAI unveils interplanetary roadmap in rare public all-hands: The company just posted a full 45-minute all-hands video, laying out CEO Elon Musk's vision for the AI lab — including moon-based factories and space data centers.

3. Anthropic beefs up Claude's free tier: The company just opened up file creation, Connectors, and Skills to all free Claude users — features previously reserved for paid subscribers.

FROM THE FRONTIER: Matt Shumer's viral essay "Something Big Is Happening"

"The future is already here. It just hasn't knocked on your door yet." Matt Shumer claims his AI tools now build complete apps from simple English prompts, then autonomously test and refine them without human intervention. He projects that AI will likely disrupt 50% of entry-level, white-collar jobs in one to five years.

But some skeptics are pushing back. For Wharton professor Ethan Mollick, it's important to note that AI is still "quite jagged", creating bottlenecks for users. Even Sam Altman has cautioned against overhyping current capabilities, suggesting AI might be a "bubble".
"""
    },
    {
        "source": "The Code (Superhuman)",
        "subject": "Alibaba drops new imaging model",
        "date": "Wed, 11 Feb 2026",
        "url": "https://codenewsletter.ai",
        "content": """
Every AI lab and IDE company is making the same bet: the future of engineering is managing AI agents.

Warp debuts Oz to help dev teams run coding agents in the cloud. Each agent gets its own Docker environment to build, test, and write PRs autonomously. Warp says Oz is already writing 60% of its internal PRs.

Alibaba's new image model merges generation and editing into one: Qwen-Image-2.0, a single model that generates and edits images with prompts up to 1K tokens.

Prime Intellect wants to turn every dev team into an AI lab with their new Lab environment for post-training agentic models using reinforcement learning.

How context graphs became enterprise AI's trillion-dollar idea:
- Foundation Capital refers to context graphs as a "trillion-dollar opportunity"
- AI agents fail at roughly 70% of enterprise tasks
- MIT found that 95% of AI pilots deliver zero P&L impact

Glean CEO Arvind Jain: "You can't reliably capture the why; you can capture the how."

This hack fixes Claude Code's memory problem: A /handover command that generates a HANDOVER.md file before ending sessions, preserving context for the next session.
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
        "source": "Axios AI+",
        "subject": "The infinite workday",
        "date": "Wed, 11 Feb 2026",
        "url": "https://www.axios.com/newsletters/axios-ai-plus",
        "content": """
Anthropic flags risks as AI development accelerates.

The concept of the "infinite workday" - AI enables work to continue 24/7.

Companies grappling with how to manage AI-augmented productivity expectations.
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

AI continues to transform industries across the board.

OpenAI released new agent frameworks including Responses API, Agents SDK, and AgentKit.
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
    },
    {
        "source": "TLDR AI",
        "subject": "xAI co-founders leave, OpenAI device delayed, agent skills guide",
        "date": "Wed, 11 Feb 2026",
        "url": "https://tldr.tech/ai",
        "content": """
xAI co-founder Tony Wu announced his exit from the company, then fellow co-founder Jimmy Ba followed.

OpenAI device has been delayed - the anticipated hardware device won't be named "io."

Guide to building agent skills and capabilities.
"""
    },
    {
        "source": "Noahpinion",
        "subject": "Roundup #77: The Fix-Everything Button",
        "date": "Wed, 11 Feb 2026",
        "url": "https://www.noahpinion.blog/p/roundup-77-the-fix-everything-button",
        "content": """
Is AI taking our jobs yet?

As agentic coding apps wow the world, it's time for yet another round of "Is AI taking our jobs yet?". Most of the attention has been focused on young college grads. The story is that AI primarily automates knowledge work — software engineering, legal services — and impacts white-collar entry-level hiring more than other types.

But Adam Ozimek points out that if you look at employment rates instead of unemployment rates, the picture looks very different. Recent college grads have shown pretty constant labor force participation.

Zanna Iscenko points out that jobs typically reckoned to be more "AI exposed" also tend to be more sensitive to macroeconomic swings.

It still looks to me as if the slowdown in new-grad hiring is not a great example of AI taking jobs. Perhaps this year will be the year.

On H-1B visas:
Trump has implemented a huge fee for hiring H-1Bs. Proponents of skilled immigration have warned that if companies can't get talent to come to America, they'll simply set up overseas offices.

Alphabet Inc. is plotting to dramatically expand its presence in India, with the possibility of taking millions of square feet in new office space in Bangalore. Trump's visa restrictions have made it harder to bring foreign talent to America.

Google rivals including OpenAI and Anthropic have recently set up shop in India.
"""
    },
    {
        "source": "Emily Sundberg / Feed Me",
        "subject": "Balthazar has turned into a Billboard",
        "date": "Thu, 12 Feb 2026",
        "url": "https://www.readfeedme.com/p/balthazar-has-turned-into-a-billboard",
        "content": """
Fashion Week observations and NYC culture.

The Ankler Team has a bold new black and white logo redesign.

After a delayed multibillion-dollar renovation of the Midtown Waldorf Astoria, the hotel's Chinese owners are looking to sell.

Playboy's editor told me why the magazine joined Substack.
"""
    }
]

def run_analysis():
    """Run the full analysis pipeline."""
    print("=" * 60)
    print("Newsletter Intelligence - Full Analysis")
    print(f"Analyzing {len(NEWSLETTERS)} newsletters from 13 sources")
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
    prompt = PROMPT_TEMPLATE.replace("{content}", full_content)
    
    print("Sending to Claude for analysis...")
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
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        print("Claude analysis complete!")
        print()
        
        # Debug: show first 500 chars of response
        print("Response preview:")
        print(response_text[:500])
        print("...")
        print()
        
        # Parse JSON from response - find the JSON object directly
        text = response_text.strip()
        
        # Find the first { and extract the complete JSON object
        start = text.find("{")
        if start >= 0:
            # Find matching closing brace by tracking depth
            depth = 0
            end_pos = start
            for i, char in enumerate(text[start:], start):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        end_pos = i + 1
                        break
            text = text[start:end_pos]
        
        # Debug: show extracted JSON preview
        print("Extracted JSON preview:")
        print(text[:300] if text else "(empty)")
        print()
        
        if not text or not text.startswith("{"):
            print("ERROR: Could not extract JSON from response")
            print("Full response:")
            print(response_text)
            return None
        
        analysis = json.loads(text)
        
        # Add metadata
        analysis["date_range"] = {
            "start": "2026-02-10",
            "end": "2026-02-12"
        }
        
        return analysis
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def post_to_slack(analysis):
    """Post analysis to Slack."""
    from slack_publisher import SlackPublisher
    
    print("Posting to Slack channel #comms-newsletter-intel...")
    publisher = SlackPublisher(config)
    success = publisher.publish(analysis)
    
    if success:
        print("✓ Posted successfully!")
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
            if theme.get('summary'):
                print(f"    {theme.get('summary')[:100]}...")
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
            print(f"    Angle: {opp.get('angle', '')[:80]}...")
        print()
        
        # Post to Slack
        print("=" * 60)
        post_to_slack(analysis)
