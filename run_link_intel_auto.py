#!/usr/bin/env python3
"""
Automated Link Intelligence Orchestrator Runner
Runs without requiring user input
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from link_intelligence_orchestrator import LinkIntelligenceOrchestrator

def main():
    """Run Link Intelligence Orchestrator automatically."""

    print("="*70)
    print("         LINK INTELLIGENCE ORCHESTRATOR v1.0 - AUTO RUN")
    print("="*70)

    # Configuration
    config = {
        'SHEET_ID': '1l5aAzy5bhilmB3XfEBUbnL6Le8z1t0hFlmzLA5Gwq50',
        'TAB_NAME': 'Sheet1',
        'ROW_SCOPE': '2:20',  # Starting with first 20 rows for safety
        'DAILY_LINK_LIMIT': 100,  # Conservative limit for initial run
        'MAX_LINKS_PER_ROW': 5,  # Process up to 5 links per row
        'SEARCH_ENGINE': 'Google',
        'SCRAPE_DEPTH': 'light',
        'ARP_MODE': 'on',
        'USER_AGENT_ID': 'LinkIntelBot/1.0',
        'ROBOTS_RESPECT': True,
        'DELAY_RANDOMIZATION_MS': (1000, 3000),  # Slightly higher delays for safety
        'RETRY_POLICY': {'attempts': 2, 'backoff': [2, 4]},
        'FORCE_REFRESH': False
    }

    print("\nConfiguration:")
    print("-" * 50)
    print(f"Sheet ID: {config['SHEET_ID'][:20]}...")
    print(f"Tab Name: {config['TAB_NAME']}")
    print(f"Row Scope: {config['ROW_SCOPE']}")
    print(f"Daily Link Limit: {config['DAILY_LINK_LIMIT']}")
    print(f"Max Links Per Row: {config['MAX_LINKS_PER_ROW']}")
    print(f"Search Engine: {config['SEARCH_ENGINE']}")
    print(f"Scrape Depth: {config['SCRAPE_DEPTH']}")
    print(f"ARP Mode: {config['ARP_MODE']}")
    print("-" * 50)

    print("\n[STARTING] Initializing orchestrator...")

    try:
        # Create orchestrator
        orchestrator = LinkIntelligenceOrchestrator(config)

        print("[RUNNING] Starting link intelligence processing...")
        print("\nThis will:")
        print("  1. Authenticate with Google Sheets")
        print("  2. Read rows 2-20 from your sheet")
        print("  3. Discover ALL links in every cell")
        print("  4. Search and scrape each link")
        print("  5. Calculate lead scores")
        print("  6. Write results to columns after AX")
        print("\n" + "="*70)

        # Run the orchestrator
        stats = orchestrator.run()

        # Display results
        print("\n" + "="*70)
        print("[COMPLETE] Processing finished successfully!")
        print("="*70)

        if stats['start_time'] and stats['end_time']:
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            print(f"\nProcessing Statistics:")
            print(f"  Duration: {duration:.2f} seconds")
            print(f"  Rows Processed: {stats['rows_processed']}")
            print(f"  Links Found: {stats['links_found']}")
            print(f"  Links Processed: {stats['links_processed']}")
            print(f"  Links Skipped: {stats['links_skipped']}")
            print(f"  Errors: {stats['errors']}")
            print(f"  Columns Created: {stats['columns_created']}")

        print("\n[SUCCESS] Check your Google Sheet for the enriched data!")
        print("         New columns have been added after column AX")

        # Save stats to file
        stats_file = f"link_intel_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        print(f"\n[SAVED] Statistics saved to {stats_file}")

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Processing stopped by user")
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        print("\nFull error trace:")
        traceback.print_exc()

    print("\n" + "="*70)
    print("Link Intelligence Orchestrator - Session Complete")
    print("="*70)

if __name__ == "__main__":
    main()