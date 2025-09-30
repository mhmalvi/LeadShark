#!/usr/bin/env python3
"""
Runner Script for Non-Destructive Google Sheets Enricher
Demonstrates append-only, row-aligned enrichment
"""

import os
import sys
import json
import argparse
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from non_destructive_enricher import NonDestructiveEnricher


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║        Non-Destructive Google Sheets Enricher v2.0          ║
║                                                              ║
║  • Append-only enrichment (preserves all original data)     ║
║  • Namespaced columns with Enrich:: prefix                  ║
║  • Row key matching for idempotent updates                  ║
║  • Smart column management (stays under 60 columns)         ║
║  • Comprehensive error handling and retry logic             ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def validate_environment():
    """Validate environment and dependencies"""
    issues = []

    # Check for credentials file
    if not os.path.exists('credentials.json'):
        issues.append("❌ credentials.json not found - run authentication setup first")

    # Check for required modules
    try:
        import google.auth
    except ImportError:
        issues.append("❌ Google auth packages not installed - run: pip install -r requirements.txt")

    if issues:
        print("\n⚠️  Setup Issues Detected:")
        for issue in issues:
            print(f"  {issue}")
        return False

    print("✅ Environment validated successfully")
    return True


def main():
    """Main execution function"""
    print_banner()

    parser = argparse.ArgumentParser(
        description='Non-Destructive Google Sheets Enricher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run on first 5 rows
  python run_non_destructive.py --sheet-id YOUR_SHEET_ID --dry-run

  # Process first 10 rows
  python run_non_destructive.py --sheet-id YOUR_SHEET_ID --max-rows 10

  # Process all rows (production)
  python run_non_destructive.py --sheet-id YOUR_SHEET_ID --all

  # Run tests
  python run_non_destructive.py --test
        """
    )

    parser.add_argument(
        '--sheet-id',
        help='Google Sheet ID from the URL'
    )
    parser.add_argument(
        '--max-rows',
        type=int,
        default=5,
        help='Maximum rows to process (default: 5)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all rows in the sheet'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - preview changes without writing'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run test suite'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Batch size for updates (default: 50)'
    )

    args = parser.parse_args()

    # Run tests if requested
    if args.test:
        print("\n🧪 Running Test Suite...")
        print("="*60)
        from test_non_destructive import run_tests
        success = run_tests()
        return 0 if success else 1

    # Validate sheet ID
    if not args.sheet_id:
        print("\n❌ Error: --sheet-id is required")
        print("   Get this from your Google Sheets URL:")
        print("   https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit")
        parser.print_help()
        return 1

    # Validate environment
    if not validate_environment():
        return 1

    # Initialize enricher
    print(f"\n📊 Initializing enricher for sheet: {args.sheet_id}")
    print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"   Max rows: {'ALL' if args.all else args.max_rows}")

    enricher = NonDestructiveEnricher(
        sheet_id=args.sheet_id,
        dry_run=args.dry_run
    )

    # Authenticate
    print("\n🔐 Authenticating with Google Sheets API...")
    if not enricher.authenticate():
        print("❌ Authentication failed!")
        print("\nTroubleshooting:")
        print("1. Ensure credentials.json exists")
        print("2. Check that the service account has access to your sheet")
        print("3. Run: python google_sheets_auth.py to test authentication")
        return 1

    print("✅ Authentication successful")

    # Process the sheet
    print("\n🚀 Starting enrichment process...")
    print("="*60)

    try:
        max_rows = None if args.all else args.max_rows
        stats = enricher.process_sheet(max_rows=max_rows)

        # Print results
        print("\n" + "="*60)
        print("📈 ENRICHMENT COMPLETE")
        print("="*60)

        print(f"\n📊 Statistics:")
        print(f"   • Rows attempted: {stats['rows_attempted']}")
        print(f"   • Rows updated: {stats['rows_updated']}")
        print(f"   • Rows skipped: {stats['rows_skipped']}")
        print(f"   • Processing time: {stats['elapsed_seconds']:.1f} seconds")

        if stats['rows_updated'] > 0:
            print(f"\n✅ Success Rate: {(stats['rows_updated']/stats['rows_attempted']*100):.1f}%")

        if stats['errors']:
            print(f"\n⚠️  Errors encountered: {len(stats['errors'])}")
            for error in stats['errors'][:3]:  # Show first 3 errors
                print(f"   - {error}")

        if args.dry_run:
            print("\n🔍 DRY RUN COMPLETE - No actual changes were made")
            print("   Remove --dry-run flag to apply changes")
        else:
            print(f"\n✅ Sheet updated successfully!")
            print(f"   View your sheet: https://docs.google.com/spreadsheets/d/{args.sheet_id}")

        # Summary of what was done
        print("\n📝 What was done:")
        print("   ✓ Read existing headers (preserved all original columns)")
        print("   ✓ Added Enrich:: namespaced columns at the far right")
        print("   ✓ Generated/retrieved stable row keys for matching")
        print("   ✓ Enriched data from web scraping and APIs")
        print("   ✓ Wrote results to Enrich:: columns only")
        print("   ✓ Original data remains completely unchanged")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())