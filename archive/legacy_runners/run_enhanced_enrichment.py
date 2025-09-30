#!/usr/bin/env python3
"""
LeadShark Enhanced Enrichment - Simple Runner
Quick entry point for enhanced multi-link enrichment
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Fix Windows Unicode issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup path
sys.path.insert(0, os.path.dirname(__file__))

from enhanced_compact_enricher import EnhancedCompactEnricher
from enhanced_enrichment_engine import EnhancedEnrichmentEngine


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('leadshark_enhanced.log'),
            logging.StreamHandler()
        ]
    )


def print_banner():
    """Print LeadShark banner"""
    print("\n" + "="*70)
    print(" " * 15 + "🦈 LeadShark Enhanced Enrichment v3.0")
    print(" " * 10 + "Multi-Link Scraping + API Enrichment + Lead Scoring")
    print("="*70 + "\n")


def show_api_quotas():
    """Show current API quota status"""
    print("📊 API Quota Status:")
    print("-" * 70)

    engine = EnhancedEnrichmentEngine()
    quotas = engine.get_api_quota_status()

    for api_name, status in quotas.items():
        quota = status.get('quota', 'unlimited')
        remaining = status.get('remaining', 'unlimited')
        period = status.get('period', 'N/A')

        if quota == 'unlimited':
            print(f"  ✅ {api_name:20s} Unlimited")
        else:
            percent = (remaining / quota * 100) if remaining != 'unlimited' else 100
            status_icon = "✅" if percent > 50 else "⚠️" if percent > 20 else "❌"
            print(f"  {status_icon} {api_name:20s} {remaining:>4}/{quota:<4} ({percent:.0f}%) - {period}")

    print()


def test_single_row():
    """Test enrichment on a single row"""
    print("🧪 Testing Single Row Enrichment")
    print("-" * 70)

    test_row = {
        'name': 'Test User',
        'first_name': 'Test',
        'email': 'test@example.com',
        'company': 'TestCorp',
        'location': 'San Francisco',
        'linkedin_url': 'https://linkedin.com/in/test',
        'website': 'https://example.com'
    }

    print("\nInput:")
    for key, value in test_row.items():
        print(f"  {key}: {value}")

    print("\nEnriching...")

    try:
        engine = EnhancedEnrichmentEngine()
        result = engine.enrich_row(test_row, max_links=2)

        print("\n✅ Enrichment Complete!")
        print("-" * 70)
        print(f"Processing Time: {result['processing_time_ms']}ms")
        print(f"Lead Score: {result['lead_score']}/100")
        print(f"Lead Tags: {result['lead_tags']}")
        print(f"Links Scraped: {len(result['link_data'])}")
        print(f"APIs Called: {len(result['api_enrichment'])}")

        print(f"\nComplete Context:")
        print(f"  {result['complete_context']}")

        if result['errors']:
            print(f"\nErrors: {result['errors']}")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_sheet_enrichment(sheet_id: str, max_rows: int, max_links: int, dry_run: bool):
    """Run enrichment on Google Sheet"""
    print(f"📊 Starting Sheet Enrichment")
    print("-" * 70)
    print(f"Sheet ID: {sheet_id}")
    print(f"Max Rows: {max_rows}")
    print(f"Max Links per Row: {max_links}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    try:
        enricher = EnhancedCompactEnricher(
            sheet_id=sheet_id,
            dry_run=dry_run,
            max_links=max_links
        )

        # Authenticate
        print("🔐 Authenticating with Google Sheets...")
        if not enricher.authenticate():
            print("❌ Authentication failed")
            return False

        print("✅ Authentication successful\n")

        # Show quotas before processing
        show_api_quotas()

        # Process sheet
        print("🦈 Processing rows...")
        print("-" * 70)

        stats = enricher.process_sheet(max_rows=max_rows)

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

        return stats['rows_updated'] > 0

    except Exception as e:
        print(f"\n❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='LeadShark Enhanced Enrichment - Multi-Link Scraping + API Enrichment + Lead Scoring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test single row
  python run_enhanced_enrichment.py --test

  # Show API quotas
  python run_enhanced_enrichment.py --quotas

  # Enrich 5 rows (dry run)
  python run_enhanced_enrichment.py --sheet-id YOUR_SHEET_ID --max-rows 5 --dry-run

  # Enrich 10 rows (live)
  python run_enhanced_enrichment.py --sheet-id YOUR_SHEET_ID --max-rows 10

  # Full enrichment with 3 links per row
  python run_enhanced_enrichment.py --sheet-id YOUR_SHEET_ID --max-rows 100 --max-links 3
        """
    )

    # Mode selection
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--test', action='store_true', help='Test single row enrichment')
    mode.add_argument('--quotas', action='store_true', help='Show API quota status')

    # Sheet enrichment options
    parser.add_argument('--sheet-id', help='Google Sheet ID')
    parser.add_argument('--max-rows', type=int, default=5, help='Max rows to process (default: 5)')
    parser.add_argument('--max-links', type=int, default=5, help='Max links per row (default: 5)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no writes)')

    # General options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    # Setup
    setup_logging(args.verbose)
    print_banner()

    # Run requested mode
    if args.test:
        success = test_single_row()
        return 0 if success else 1

    elif args.quotas:
        show_api_quotas()
        return 0

    elif args.sheet_id:
        success = run_sheet_enrichment(
            sheet_id=args.sheet_id,
            max_rows=args.max_rows,
            max_links=args.max_links,
            dry_run=args.dry_run
        )
        return 0 if success else 1

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())