#!/usr/bin/env python3
"""
Newsletter Summarizer - Variable Days

Run from Cursor when someone asks in Slack.

Usage:
    python summarize_days.py 3    # Last 3 days
    python summarize_days.py 5    # Last 5 days  
    python summarize_days.py 7    # Last 7 days

The script will:
1. Show you the Gmail query to run via gworkspace MCP
2. You paste the newsletter content
3. It analyzes and posts to Slack
"""

import sys

def main():
    days = 3
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("Usage: python summarize_days.py [days]")
            sys.exit(1)
    
    # Build the Gmail query
    query = f"""from:(lenny+how-i-ai@substack.com OR ai.plus@axios.com OR bigtechnology@substack.com OR tbpn+run-of-show@substack.com OR superhuman@mail.joinsuperhuman.ai OR lenny@substack.com OR email@stratechery.com OR noahpinion@substack.com OR newsletter@techmeme.com OR casey@platformer.news OR list@ben-evans.com OR dan@tldrnewsletter.com OR thecode@mail.joinsuperhuman.ai OR notboring@substack.com OR emilysundberg@substack.com) newer_than:{days}d"""
    
    print("=" * 60)
    print(f"📰 Newsletter Summary - Last {days} Days")
    print("=" * 60)
    print()
    print("Step 1: Run this MCP command to fetch emails:")
    print()
    print(f'gworkspace-mcp read_mail with query="{query}" max_results=25 include_body=true')
    print()
    print("Step 2: Once you have the content, run:")
    print("    python run_full_analysis.py")
    print()
    print("The analysis will be posted to #comms-newsletter-intel")
    print()
    print("-" * 60)
    print("Or just ask me to 'summarize the last X days' and I'll do it!")
    print("-" * 60)


if __name__ == "__main__":
    main()
