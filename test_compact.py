#!/usr/bin/env python3
"""
Quick test for compact enricher
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from compact_enricher import CompactEnricher

def test_compact_enricher():
    """Test the compact enricher with your sheet"""

    # Your sheet ID from the error
    sheet_id = "1l5aAzy5bhilmB3XfEBUbnL6Le8z1t0hFlmzLA5Gwq50"

    print("🧪 Testing Compact Enricher")
    print(f"Sheet ID: {sheet_id}")
    print("=" * 50)

    # Initialize enricher
    enricher = CompactEnricher(sheet_id, dry_run=True)  # Start with dry run

    # Authenticate
    print("🔐 Authenticating...")
    if not enricher.authenticate():
        print("❌ Authentication failed")
        return 1

    print("✅ Authentication successful")

    # Test processing 2 rows
    print("🚀 Processing 2 rows (dry run)...")
    stats = enricher.process_sheet(max_rows=2)

    print("\n📊 Results:")
    print(f"   Rows attempted: {stats.get('rows_attempted', 0)}")
    print(f"   Rows updated: {stats.get('rows_updated', 0)}")
    print(f"   Success: {stats.get('ok', 0)}")
    print(f"   Partial: {stats.get('partial', 0)}")
    print(f"   Failed: {stats.get('failed', 0)}")
    print(f"   Time: {stats.get('elapsed_seconds', 0):.1f}s")

    if stats.get('errors'):
        print(f"   Errors: {len(stats['errors'])}")
        for error in stats['errors']:
            print(f"     - {error}")

    if stats.get('rows_attempted', 0) > 0:
        print("✅ Compact enricher test successful!")
        print("💡 To run live: remove --dry-run flag")
        return 0
    else:
        print("❌ No rows were processed")
        return 1

if __name__ == "__main__":
    sys.exit(test_compact_enricher())