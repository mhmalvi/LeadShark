#!/usr/bin/env python3
"""
Demo script for Link Intelligence Orchestrator
Shows how the system processes links from Google Sheets
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from link_intelligence_orchestrator import LinkIntelligenceOrchestrator

def demo_link_discovery():
    """Demonstrate link discovery capabilities."""
    print("\n" + "="*60)
    print("LINK DISCOVERY DEMO")
    print("="*60)

    # Sample row data that might be in a Google Sheet
    sample_row = [
        "John Doe",
        "CEO",
        "john@techstartup.com",
        "TechStartup Inc",
        "https://techstartup.com",
        "Check out our LinkedIn at https://linkedin.com/company/techstartup",
        "www.techstartup.com/blog",
        "Follow us on https://twitter.com/techstartup",
        "+1-555-123-4567",
        "San Francisco, CA",
        "Series B funded, see crunchbase.com/organization/techstartup",
        "Our Facebook page: facebook.com/techstartupinc"
    ]

    # Create orchestrator with test config
    config = {
        'SHEET_ID': 'demo-sheet',
        'TAB_NAME': 'Sheet1',
        'ROW_SCOPE': 'all rows',
        'DAILY_LINK_LIMIT': 500,
        'MAX_LINKS_PER_ROW': 10,
        'SEARCH_ENGINE': 'Google',
        'SCRAPE_DEPTH': 'light',
        'ARP_MODE': 'on',
        'USER_AGENT_ID': 'LinkIntelBot/1.0',
        'ROBOTS_RESPECT': True,
        'DELAY_RANDOMIZATION_MS': (800, 2500),
        'RETRY_POLICY': {'attempts': 3, 'backoff': [2, 4, 8]},
        'FORCE_REFRESH': False
    }

    orchestrator = LinkIntelligenceOrchestrator(config)

    print("\nSample Row Data:")
    print("-" * 40)
    for i, cell in enumerate(sample_row):
        print(f"Cell {i+1}: {cell}")

    print("\n" + "="*60)
    print("DISCOVERED LINKS:")
    print("="*60)

    # Discover links in the row
    links = orchestrator.discover_links_in_row(sample_row)

    for i, link in enumerate(links, 1):
        print(f"L{i}: {link}")

    print(f"\nTotal Links Found: {len(links)}")

    print("\n" + "="*60)
    print("WHAT WOULD HAPPEN NEXT:")
    print("="*60)

    print("""
For each discovered link, the orchestrator would:

1. SEARCH INTELLIGENCE:
   - Google/Bing search for company info
   - Look for LinkedIn, Crunchbase presence
   - Identify industry/category
   - Find size signals (employees, revenue)
   - Check for recent news/activity

2. SCRAPE INTELLIGENCE:
   - Extract title, meta description, H1
   - Find value proposition
   - Detect pricing/CTA presence
   - Extract contact methods (email, phone, forms)
   - Identify tech stack (CMS, analytics, etc.)
   - Check freshness (recent dates)
   - Find social media links

3. GENERATE OUTPUTS:
   - Individual link summaries
   - Comprehensive final report
   - Lead score (0-100) with rationale
   - ARP enrichment fields

4. WRITE TO SHEET:
   - Create columns after AX dynamically
   - Never overwrite existing data
   - Mark as processed (idempotent)
    """)

    print("\n" + "="*60)
    print("SAMPLE OUTPUT COLUMNS (Created after AX):")
    print("="*60)

    sample_columns = [
        "L1 URL: https://techstartup.com",
        "L1 Search Summary: SaaS company | 50+ employees | LinkedIn verified | Series B",
        "L1 Scrape Summary: B2B platform | Pricing page found | Contact form | Tech: React, AWS",
        "L2 URL: https://linkedin.com/company/techstartup",
        "L2 Search Summary: Active LinkedIn | 500+ followers | Regular posts",
        "L2 Scrape Summary: Company profile | Team size: 51-200 | Founded 2019",
        "...",
        "Final Report (All Links): • Analyzed 5 links • Industry: SaaS/Technology • Size: 50+ employees • Tech: Modern stack • Commercial: Pricing visible • Social: Active presence",
        "Lead Score (0-100): 78 (ICP match; pricing visible; LinkedIn active; tech: React)",
        "ARP: Primary Domain: techstartup.com",
        "ARP: Company Name: TechStartup Inc",
        "ARP: Category/Industry: SaaS, Technology",
        "ARP: Tech Stack Highlights: React, AWS, Google Analytics",
        "ARP: LinkedIn Presence: Y + https://linkedin.com/company/techstartup"
    ]

    for col in sample_columns:
        print(f"  {col}")

    print("\n" + "="*60)
    print("KEY ADVANTAGES OVER CURRENT SYSTEM:")
    print("="*60)

    print("""
CURRENT compact_enricher.py:
  ❌ Only scrapes FIRST URL found
  ❌ Only checks predefined URL columns
  ❌ No search intelligence
  ❌ No lead scoring
  ❌ Fixed column placement
  ❌ Limited to 5 compact columns

LINK INTELLIGENCE ORCHESTRATOR:
  ✅ Discovers ALL links in EVERY cell
  ✅ Processes multiple links per row
  ✅ Web search + scraping intelligence
  ✅ Lead scoring with weighted rubric
  ✅ Dynamic columns after AX
  ✅ ARP mode for standardized enrichment
  ✅ Idempotent with resume capability
  ✅ Production-ready with rate limiting
    """)

if __name__ == "__main__":
    demo_link_discovery()