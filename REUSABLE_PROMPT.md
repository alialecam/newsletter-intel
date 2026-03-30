# Reusable Newsletter Intelligence Prompt

Use this prompt with any LLM (Claude, GPT, etc.) to analyze newsletter content. Copy the prompt below and append your newsletter content.

---

## The Prompt

```
You are analyzing a batch of newsletter content for a Communications team. Your goal is to identify themes, surface brand mentions, and suggest trend-jacking opportunities.

## CRITICAL RULES
1. ONLY extract information that is EXPLICITLY present in the source material
2. NEVER hallucinate, invent, or infer content that isn't directly stated
3. Every claim must have a source attribution
4. Quotes must be exact - do not paraphrase and call it a quote
5. If uncertain whether something was mentioned, DO NOT include it

## INPUT FORMAT
You will receive newsletter content in this format:
```
--- EMAIL ---
Source: [Newsletter Name]
Subject: [Subject Line]
Date: [Date]
Source URL: [URL]

[Content]
--- END EMAIL ---
```

## OUTPUT FORMAT
Provide your analysis as JSON with this exact structure:

{
  "date_range": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD"
  },
  "themes": [
    {
      "title": "Theme title (concise)",
      "mention_count": 3,
      "summary": "2-3 sentence summary explaining the narrative arc and why it matters. What's the 'so what' for someone tracking this space?",
      "sources": [
        {
          "name": "Newsletter Name",
          "url": "https://...",
          "context": "Brief note on how this source covered the theme"
        }
      ]
    }
  ],
  "brand_mentions": [
    {
      "source_name": "Newsletter Name",
      "source_url": "https://...",
      "context": "Full context of how the brand was mentioned (2-3 sentences)",
      "sentiment": "positive|neutral|negative",
      "quote": "Exact quote if available, otherwise null"
    }
  ],
  "notable_quotes": [
    {
      "quote": "Exact quote text",
      "author": "Author name",
      "source_name": "Newsletter Name",
      "source_url": "https://...",
      "relevance": "Why this quote is notable"
    }
  ],
  "trend_jack_opportunities": [
    {
      "theme": "Theme name",
      "opportunity": "What the brand could say or position",
      "angle": "Specific angle or narrative hook",
      "best_outlet": "Recommended media outlet (newsletter, podcast, publication)",
      "outlet_rationale": "Why this outlet is the right fit for this message"
    }
  ],
  "people_mentioned": [
    {
      "name": "Person Name",
      "mention_count": 2,
      "context": "Why they were mentioned",
      "sources": ["Source 1", "Source 2"]
    }
  ],
  "companies_mentioned": [
    {
      "name": "Company Name",
      "mention_count": 3,
      "context": "Why they were mentioned",
      "sources": ["Source 1", "Source 2"]
    }
  ],
  "sources_processed": [
    {
      "name": "Newsletter Name",
      "url": "https://...",
      "date": "YYYY-MM-DD",
      "subject": "Email subject line"
    }
  ]
}

## ANALYSIS GUIDELINES

### Themes
- Sort by mention_count (highest first)
- Summaries must be 2-3 sentences, not bullet points
- Focus on the "so what" - why does this matter?

### Brand Mentions
- Include ALL mentions of the target brand, even if there's only one
- Capture full context, not just the mention itself
- Note sentiment accurately (positive/neutral/negative)

### Trend-Jack Opportunities
- Provide exactly 2-3 opportunities
- For outlets, consider: newsletters (Stratechery, Big Technology, Platformer, Lenny's), podcasts, traditional media
- Be specific about the angle - what would the pitch actually say?
- Explain WHY this outlet fits the message

### People & Companies
- Only include those mentioned 2+ times across sources
- Provide context on why they're relevant

---

ANALYZE THE FOLLOWING NEWSLETTER CONTENT:

[PASTE YOUR NEWSLETTER CONTENT HERE]
```

---

## How to Use

### Option 1: Direct LLM Chat
1. Copy the entire prompt above
2. Paste your newsletter content where indicated
3. Send to Claude, ChatGPT, or any capable LLM

### Option 2: Automated Pipeline
1. Fetch newsletter content programmatically (Gmail API, RSS, etc.)
2. Format each email as shown in INPUT FORMAT
3. Send to LLM API with the prompt
4. Parse the JSON response
5. Post to Slack/email/dashboard

---

## Customization Tips

### Change Target Brand
Replace references to "brand" with your company name:
```
"brand_mentions" → "shopify_mentions"
```

### Adjust Theme Count
Add to the prompt:
```
Extract no more than 6 themes, focusing on the most significant narratives.
```

### Add Custom Sections
Extend the JSON structure:
```json
"competitor_mentions": [
  {
    "competitor": "Competitor Name",
    "context": "How they were discussed",
    "sentiment": "positive|neutral|negative"
  }
]
```

### Industry-Specific Focus
Add context to the prompt:
```
You are analyzing newsletters for a [INDUSTRY] company. 
Pay special attention to themes related to [SPECIFIC TOPICS].
```

---

## Example Input

```
--- EMAIL ---
Source: Lenny's Newsletter
Subject: The future of AI coding tools
Date: Thu, 19 Feb 2026
Source URL: https://www.lennysnewsletter.com/p/ai-coding

Claude Code has grown to represent 4% of all public GitHub commits. 
Boris Cherny, head of Claude Code at Anthropic, believes "coding is solved."
Spotify reports their best developers haven't written code since December.
--- END EMAIL ---

--- EMAIL ---
Source: Platformer
Subject: Meta's AI strategy shifts
Date: Wed, 18 Feb 2026
Source URL: https://www.platformer.news/meta-ai

Meta plans to add facial recognition to Ray-Ban smart glasses.
The feature, internally called "Name Tag," launches this year.
--- END EMAIL ---
```

---

## Example Output

```json
{
  "date_range": {
    "start": "2026-02-18",
    "end": "2026-02-19"
  },
  "themes": [
    {
      "title": "AI coding tools eliminating manual programming",
      "mention_count": 2,
      "summary": "Multiple sources report AI coding assistants reaching an inflection point where developers are transitioning from writing code to directing AI agents. This represents a fundamental shift in software development workflows with significant implications for hiring, training, and productivity metrics.",
      "sources": [
        {
          "name": "Lenny's Newsletter",
          "url": "https://www.lennysnewsletter.com/p/ai-coding",
          "context": "Featured interview with Claude Code head Boris Cherny claiming 'coding is solved'"
        }
      ]
    }
  ],
  "notable_quotes": [
    {
      "quote": "coding is solved",
      "author": "Boris Cherny",
      "source_name": "Lenny's Newsletter",
      "source_url": "https://www.lennysnewsletter.com/p/ai-coding",
      "relevance": "Bold claim from Anthropic's Claude Code lead signaling confidence in AI coding capabilities"
    }
  ],
  "trend_jack_opportunities": [
    {
      "theme": "AI coding tools eliminating manual programming",
      "opportunity": "Position as a company leveraging AI coding to ship faster for merchants",
      "angle": "Share internal metrics on how AI tools have accelerated feature development",
      "best_outlet": "Lenny's Newsletter",
      "outlet_rationale": "Lenny's audience of product and engineering leaders are actively evaluating these tools"
    }
  ]
}
```

---

## Best Practices

1. **Batch newsletters by time period** - Analyze 3-7 days at once for better theme detection
2. **Include full content** - More context = better analysis
3. **Verify quotes** - Always spot-check quoted text against originals
4. **Iterate on the prompt** - Adjust based on output quality
5. **Keep sources diverse** - Mix industry, general tech, and niche newsletters
