#!/usr/bin/env python3
"""
LeadShark Enhanced Expanded Enrichment - CLI Runner
For users who want individual columns instead of JSON-packed data
"""

import os
import sys
import argparse
import logging

# Fix Windows Unicode issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup path
sys.path.insert(0, os.path.dirname(__file__))

from enhanced_non_destructive_enricher import EnhancedNonDestructiveEnricher


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('leadshark_expanded.log'),
            logging.StreamHandler()
        ]
    )


def print_banner():
    """Print LeadShark banner"""
    print("\n" + "="*70)
    print(" " * 10 + "🦈 LeadShark Enhanced Enrichment v3.0 (EXPANDED)")
    print(" " * 8 + "Individual Columns for Links, APIs, and Scoring")
    print("="*70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='LeadShark Enhanced Expanded Enrichment - Individual Column Format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run with 5 rows
  python run_expanded_enrichment.py --sheet-id YOUR_SHEET_ID --max-rows 5 --dry-run

  # Enrich 10 rows (live)
  python run_expanded_enrichment.py --sheet-id YOUR_SHEET_ID --max-rows 10

  # Enrich 20 rows with 3 links per row
  python run_expanded_enrichment.py --sheet-id YOUR_SHEET_ID --max-rows 20 --max-links 3

Column Structure:
  This creates 44 individual columns:
  - Link 1-5 (3 columns each): URL, Summary, JSON
  - Lead Scoring (3 columns): Score, Tags, Context
  - Gender API (3 columns)
  - Email API (3 columns)
  - GitHub API (4 columns)
  - Google Search API (3 columns)
  - LinkedIn API (3 columns)
  - Score Breakdown (6 columns): Role, Company Fit, Engagement, etc.
  - Processing Metadata (3 columns): Time, Date, Status
        """
    )

    # Required options
    parser.add_argument('--sheet-id', required=True, help='Google Sheet ID')

    # Processing options
    parser.add_argument('--max-rows', type=int, default=5, help='Max rows to process (default: 5)')
    parser.add_argument('--max-links', type=int, default=5, help='Max links per row (default: 5)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no writes)')

    # General options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    # Setup
    setup_logging(args.verbose)
    print_banner()

    print(f"📊 Configuration:")
    print(f"  Sheet ID: {args.sheet_id}")
    print(f"  Max Rows: {args.max_rows}")
    print(f"  Max Links per Row: {args.max_links}")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"  Columns to create: 44 individual columns")
    print()

    try:
        enricher = EnhancedNonDestructiveEnricher(
            sheet_id=args.sheet_id,
            dry_run=args.dry_run,
            max_links=args.max_links
        )

        # Authenticate
        print("🔐 Authenticating with Google Sheets...")
        if not enricher.authenticate():
            print("❌ Authentication failed")
            return 1

        print("✅ Authentication successful\n")

        # Process sheet
        print("🦈 Processing rows...")
        print("-" * 70)

        stats = enricher.process_sheet(max_rows=args.max_rows)

        # Results
        print("\n" + "="*70)
        print("📊 ENRICHMENT COMPLETE")
        print("="*70)
        print(f"Rows Attempted: {stats['rows_attempted']}")
        print(f"Rows Updated: {stats['rows_updated']}")
        print(f"\nLead Distribution:")
        print(f"  🔥 Hot:     {stats.get('hot', 0):>3}")
        print(f"  🟡 Warm:    {stats.get('warm', 0):>3}")
        print(f"  🔵 Cold:    {stats.get('cold', 0):>3}")
        print(f"  ⚫ Discard: {stats.get('discard', 0):>3}")
        print(f"\nProcessing Time: {stats.get('elapsed_seconds', 0):.1f}s")

        if stats['errors']:
            print(f"\n⚠️  Errors: {len(stats['errors'])}")
            for i, error in enumerate(stats['errors'][:5], 1):
                print(f"  {i}. {error}")
            if len(stats['errors']) > 5:
                print(f"  ... and {len(stats['errors']) - 5} more")

        print()

        return 0 if stats['rows_updated'] > 0 else 1

    except Exception as e:
        print(f"\n❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())