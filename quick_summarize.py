#!/usr/bin/env python3
"""
Quick Newsletter Summarizer

Run this script when someone in #comms-newsletter-intel asks for a summary.
Just change the DAYS variable below and run!

Usage:
    python quick_summarize.py
"""

# ============================================
# CHANGE THIS NUMBER TO MATCH THE REQUEST
# ============================================
DAYS = 3  # Change to 5, 7, etc. as requested
# ============================================

import subprocess
import sys

print(f"📰 Running newsletter analysis for the last {DAYS} days...")
print(f"   Posting to #comms-newsletter-intel")
print()

# Run the full analysis
result = subprocess.run(
    [sys.executable, "run_full_analysis.py"],
    cwd="/Users/alialecam/Cursor Projects/newsletter-intel"
)

if result.returncode == 0:
    print()
    print("✅ Done! Check #comms-newsletter-intel for the summary.")
else:
    print()
    print("❌ Something went wrong. Check the output above.")
