#!/usr/bin/env python3
"""
Simple Compact Enricher Test - No Rich formatting
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from compact_enricher import CompactEnricher
from google_sheets_auth import authenticate_google_sheets

def main():
    """Simple test without rich formatting"""

    print("=" * 60)
    print("COMPACT ENRICHER TEST")
    print("=" * 60)

    # Your sheet ID
    sheet_id = "1l5aAzy5bhilmB3XfEBUbnL6Le8z1t0hFlmzLA5Gwq50"
    print(f"Testing with sheet: {sheet_id}")

    # Initialize enricher
    enricher = CompactEnricher(sheet_id, dry_run=False)

    # Authenticate
    print("\n1. Authenticating...")
    if not enricher.authenticate():
        print("   FAILED: Authentication failed")
        return 1

    print("   SUCCESS: Authenticated with Google Sheets")

    # Test processing
    print("\n2. Processing 2 rows (dry run)...")
    stats = enricher.process_sheet(max_rows=2)

    print("\n3. Results:")
    print(f"   Rows attempted: {stats.get('rows_attempted', 0)}")
    print(f"   Rows updated: {stats.get('rows_updated', 0)}")
    print(f"   Success: {stats.get('ok', 0)}")
    print(f"   Partial: {stats.get('partial', 0)}")
    print(f"   Failed: {stats.get('failed', 0)}")
    print(f"   Processing time: {stats.get('elapsed_seconds', 0):.1f}s")

    if stats.get('errors'):
        print(f"   Errors ({len(stats['errors'])}):")
        for error in stats['errors'][:3]:
            print(f"     - {error}")

    # Summary
    print("\n" + "=" * 60)
    if stats.get('rows_attempted', 0) > 0:
        print("SUCCESS: Compact enricher working!")
        print("The compact enricher uses only 5 columns:")
        print("  1. Enrich::Row Key")
        print("  2. Enrich::Summary Report")
        print("  3. Enrich::Key Data")
        print("  4. Enrich::Status & Meta")
        print("  5. Enrich::URLs & Sources")
        print("\nTo run live: Change dry_run=False in the script")
        return 0
    else:
        print("FAILED: No rows were processed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)