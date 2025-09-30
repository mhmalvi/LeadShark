#!/usr/bin/env python3
"""
🦈 LeadShark - Unified Entry Point
Advanced Lead Enrichment & Intelligence System

Consolidates all enrichment modes into a single, powerful CLI
"""

import os
import sys
import argparse
from typing import Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import core modules
from google_sheets_auth import authenticate_google_sheets, parse_sheet_id_from_url
from cli_interface import CLIInterface

# Version info
__version__ = "3.0.0"
__build__ = "Consolidated"

def print_help():
    """Display comprehensive help information"""
    help_text = """
LeadShark v{version} - Unified Lead Enrichment System

USAGE:
    python leadshark.py [MODE] [OPTIONS]

ENRICHMENT MODES:
    hybrid          🔥 HYBRID AI + Enhanced (59 columns: AI + multi-link scraping)
    compact         Space-efficient enrichment (5 columns: AX-BB)
    full            Comprehensive enrichment (27 columns with full metadata)
    ai              AI-powered enrichment with GPT/Claude (15+ columns)
    link-intel      Advanced link intelligence with scoring (dynamic columns)
    smart           Auto-detect best mode based on sheet capacity

PROVIDER OPTIONS (for AI mode):
    --provider      Choose AI provider: openai (default) or anthropic
    --model         Specify model (e.g., gpt-4o-mini, claude-3-5-sonnet-20241022)

DATA SOURCE OPTIONS:
    --sheet-id ID   Google Sheet ID or URL
    --tab NAME      Worksheet/tab name (default: Sheet1)

PROCESSING OPTIONS:
    --test          Process first 5 rows only (for testing)
    --limit N       Process first N rows
    --all           Process all rows in sheet
    --dry-run       Preview changes without writing to sheet
    --resume        Resume from last processed row

PERFORMANCE OPTIONS:
    --rate slow     Use slower, more respectful rate limiting
    --rate fast     Use faster processing (use carefully)
    --batch N       Batch size for updates (default: 50)
    --workers N     Number of concurrent workers (default: 1)

OUTPUT OPTIONS:
    --verbose       Show detailed processing information
    --quiet         Minimal output (errors only)
    --log FILE      Log file path (default: leadshark.log)

EXAMPLES:

1. AI-powered enrichment with OpenAI (test mode):
   python leadshark.py ai --sheet-id YOUR_ID --test

2. Compact enrichment (production run):
   python leadshark.py compact --sheet-id YOUR_ID --all

3. Link intelligence with scoring:
   python leadshark.py link-intel --sheet-id YOUR_ID --limit 100

4. Smart mode (auto-select best enrichment type):
   python leadshark.py smart --sheet-id YOUR_ID --all

5. AI with specific provider and model:
   python leadshark.py ai --provider anthropic --model claude-3-5-sonnet-20241022 --sheet-id YOUR_ID

6. Interactive mode (guided workflow):
   python leadshark.py

For detailed documentation: https://github.com/yourusername/leadshark
""".format(version=__version__)

    print(help_text)


def get_enricher(mode: str, **kwargs):
    """Factory function to get appropriate enricher based on mode"""

    if mode == 'hybrid':
        from hybrid_ai_enhanced_enricher import HybridAIEnhancedEnricher
        return HybridAIEnhancedEnricher(**kwargs)

    elif mode == 'compact':
        from compact_enricher import CompactEnricher
        return CompactEnricher(**kwargs)

    elif mode == 'full':
        from non_destructive_enricher import NonDestructiveEnricher
        return NonDestructiveEnricher(**kwargs)

    elif mode == 'ai':
        from ai_powered_enricher import AIPoweredEnricher
        return AIPoweredEnricher(**kwargs)

    elif mode == 'link-intel':
        from link_intelligence_orchestrator import LinkIntelligenceOrchestrator
        return LinkIntelligenceOrchestrator(**kwargs)

    elif mode == 'smart':
        # Smart mode: auto-detect best enrichment type based on sheet
        from smart_enricher import SmartEnricher
        return SmartEnricher(**kwargs)

    else:
        raise ValueError(f"Unknown enrichment mode: {mode}")


def interactive_mode():
    """
    Interactive guided workflow for users who prefer step-by-step process
    """
    cli = CLIInterface()
    cli.print_banner()

    print("\nWelcome to LeadShark Interactive Mode\n")

    # Step 1: Select enrichment mode
    print("SELECT ENRICHMENT MODE:\n")
    print("  1. 🔥 Hybrid AI + Enhanced - MOST POWERFUL (59 columns: AI + multi-link)")
    print("  2. AI-Powered (GPT/Claude) - Intelligent analysis (15 columns)")
    print("  3. Link Intelligence - Advanced link discovery with scoring")
    print("  4. Compact - Space-efficient (5 columns)")
    print("  5. Full - Comprehensive (27 columns)")
    print("  6. Smart - Auto-detect best mode")

    mode_choice = input("\nEnter your choice (1-6) [1]: ").strip() or "1"

    mode_map = {
        "1": "hybrid",
        "2": "ai",
        "3": "link-intel",
        "4": "compact",
        "5": "full",
        "6": "smart"
    }

    mode = mode_map.get(mode_choice, "ai")

    # Step 2: AI provider selection (if AI mode)
    provider = None
    if mode == "ai":
        print("\nSELECT AI PROVIDER:\n")
        print("  1. OpenAI (GPT) - Fast and cost-effective")
        print("  2. Anthropic (Claude) - Advanced reasoning")

        provider_choice = input("\nEnter your choice (1-2) [1]: ").strip() or "1"
        provider = "openai" if provider_choice == "1" else "anthropic"

    # Step 3: Get Google Sheet
    sheet_input = cli.prompt_sheet_input()
    if not sheet_input:
        cli.print_error("No sheet ID provided")
        return

    # Parse sheet ID from URL if needed
    sheet_id = parse_sheet_id_from_url(sheet_input)
    if not sheet_id:
        cli.print_error("Invalid sheet URL or ID")
        return

    # Step 4: Authenticate
    cli.print_info("Authenticating with Google Sheets...")
    auth_result = authenticate_google_sheets()

    # Handle tuple return (sheets_service, drive_service, creds)
    if isinstance(auth_result, tuple):
        sheets_service = auth_result[0]
        drive_service = auth_result[1]
    else:
        sheets_service = auth_result
        drive_service = None

    # Step 5: Select worksheet
    from google_sheets_auth import get_sheet_metadata
    metadata = get_sheet_metadata(sheets_service, drive_service, sheet_id)
    tab_name = cli.select_worksheet(metadata)

    if not tab_name:
        cli.print_error("No worksheet selected")
        return

    # Step 6: Preview data
    from google_sheets_auth import preview_sheet_data
    preview = preview_sheet_data(sheets_service, sheet_id, tab_name)
    if not cli.show_sheet_preview(preview):
        cli.print_warning("Operation cancelled by user")
        return

    # Step 7: Processing mode
    mode_options = cli.prompt_processing_mode()
    limit = mode_options.get('limit')

    # Step 8: Execute enrichment - build kwargs based on mode
    if mode == 'hybrid':
        enricher_kwargs = {
            'sheet_id': sheet_id,
            'dry_run': False,
            'max_links': 5
        }
    elif mode == 'link-intel':
        enricher_kwargs = {
            'config': {
                'SHEET_ID': sheet_id,
                'TAB_NAME': tab_name,
                'ROW_SCOPE': 'all rows',
                'DAILY_LINK_LIMIT': 500,
                'MAX_LINKS_PER_ROW': 10
            }
        }
    elif mode == 'ai':
        enricher_kwargs = {
            'sheet_id': sheet_id,
            'tab_name': tab_name
        }
        if provider:
            enricher_kwargs['provider'] = provider
    elif mode in ['compact', 'full', 'smart', 'hybrid']:
        enricher_kwargs = {
            'sheet_id': sheet_id,
            'dry_run': False
        }
        if mode == 'hybrid':
            enricher_kwargs['max_links'] = 5
    else:
        enricher_kwargs = {
            'sheet_id': sheet_id
        }

    enricher = get_enricher(mode, **enricher_kwargs)

    cli.print_info(f"Starting {mode} enrichment...")

    # Set service on enricher
    enricher.service = sheets_service
    if hasattr(enricher, 'drive_service'):
        enricher.drive_service = drive_service

    # Call appropriate method based on enricher type
    if hasattr(enricher, 'process_sheet'):
        enricher.process_sheet(max_rows=limit)
    elif hasattr(enricher, 'enrich'):
        enricher.enrich(service=(sheets_service, drive_service), limit=limit)
    else:
        raise AttributeError(f"Enricher {type(enricher).__name__} has no process_sheet or enrich method")

    cli.print_success("Enrichment complete!")


def cli_mode(args):
    """
    Command-line mode for direct processing
    """
    # Determine mode
    mode = args.mode or 'ai'  # Default to AI mode

    # Get sheet ID
    sheet_id = args.sheet_id
    if not sheet_id:
        print("ERROR: --sheet-id required for CLI mode")
        print("Use: python leadshark.py --help")
        sys.exit(1)

    # Parse sheet ID if URL provided
    sheet_id = parse_sheet_id_from_url(sheet_id)

    # Authenticate
    print("Authenticating with Google Sheets...")
    auth_result = authenticate_google_sheets()

    # Handle tuple return (sheets_service, drive_service, creds)
    if isinstance(auth_result, tuple):
        sheets_service = auth_result[0]
        drive_service = auth_result[1]
    else:
        sheets_service = auth_result
        drive_service = None

    # Get enricher - build kwargs based on mode
    enricher_kwargs = {}

    if mode == 'hybrid':
        # Hybrid enricher expects sheet_id and optional dry_run
        enricher_kwargs = {
            'sheet_id': sheet_id,
            'dry_run': args.dry_run,
            'max_links': 5
        }
    elif mode == 'link-intel':
        # LinkIntelligenceOrchestrator expects a config dict
        enricher_kwargs = {
            'config': {
                'SHEET_ID': sheet_id,
                'TAB_NAME': args.tab or 'Sheet1',
                'ROW_SCOPE': 'all rows',
                'DAILY_LINK_LIMIT': 500,
                'MAX_LINKS_PER_ROW': 10
            }
        }
    elif mode == 'ai':
        # AIPoweredEnricher expects sheet_id and tab_name (no verbose)
        enricher_kwargs = {
            'sheet_id': sheet_id,
            'tab_name': args.tab or 'Sheet1'
        }
        if args.provider:
            enricher_kwargs['provider'] = args.provider
        if args.model:
            enricher_kwargs['model'] = args.model
    elif mode in ['compact', 'full', 'smart', 'hybrid']:
        # These enrichers expect sheet_id and optional dry_run
        enricher_kwargs = {
            'sheet_id': sheet_id,
            'dry_run': args.dry_run
        }
        if mode == 'hybrid':
            enricher_kwargs['max_links'] = 5
    else:
        # Default fallback
        enricher_kwargs = {
            'sheet_id': sheet_id
        }

    enricher = get_enricher(mode, **enricher_kwargs)

    # Determine limit
    limit = None
    if args.test:
        limit = 5
    elif args.limit:
        limit = args.limit

    # Execute
    if args.dry_run:
        print("\nDRY RUN MODE - No changes will be written")

    print(f"\nStarting {mode} enrichment...")
    print(f"   Sheet: {sheet_id}")
    print(f"   Tab: {args.tab or 'Sheet1'}")
    if limit:
        print(f"   Limit: {limit} rows")
    else:
        print(f"   Mode: All rows")

    # Set service on enricher
    enricher.service = sheets_service
    if hasattr(enricher, 'drive_service'):
        enricher.drive_service = drive_service

    # Call appropriate method based on enricher type
    if hasattr(enricher, 'process_sheet'):
        enricher.process_sheet(max_rows=limit)
    elif hasattr(enricher, 'enrich'):
        enricher.enrich(
            service=(sheets_service, drive_service),
            limit=limit,
            dry_run=args.dry_run,
            batch_size=args.batch,
            rate_profile=args.rate
        )
    else:
        raise AttributeError(f"Enricher {type(enricher).__name__} has no process_sheet or enrich method")

    print("\nEnrichment complete!")


def main():
    """Main entry point"""

    # Create argument parser
    parser = argparse.ArgumentParser(
        description='🦈 LeadShark - Advanced Lead Enrichment System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )

    # Mode selection (positional)
    parser.add_argument(
        'mode',
        nargs='?',
        choices=['hybrid', 'ai', 'compact', 'full', 'link-intel', 'smart'],
        help='Enrichment mode'
    )

    # Help
    parser.add_argument('-h', '--help', action='store_true', help='Show help message')

    # Data source
    parser.add_argument('--sheet-id', help='Google Sheet ID or URL')
    parser.add_argument('--tab', default='Sheet1', help='Worksheet/tab name')

    # AI options
    parser.add_argument('--provider', choices=['openai', 'anthropic'], help='AI provider')
    parser.add_argument('--model', help='AI model to use')

    # Processing options
    parser.add_argument('--test', action='store_true', help='Process first 5 rows only')
    parser.add_argument('--limit', type=int, help='Process first N rows')
    parser.add_argument('--all', action='store_true', help='Process all rows')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    parser.add_argument('--resume', action='store_true', help='Resume from last row')

    # Performance
    parser.add_argument('--rate', choices=['slow', 'fast'], default='normal', help='Rate limiting profile')
    parser.add_argument('--batch', type=int, default=50, help='Batch size for updates')
    parser.add_argument('--workers', type=int, default=1, help='Concurrent workers')

    # Output
    parser.add_argument('--verbose', action='store_true', help='Detailed output')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    parser.add_argument('--log', default='leadshark.log', help='Log file path')

    # Parse args
    args = parser.parse_args()

    # Show help if requested
    if args.help:
        print_help()
        return

    try:
        # Interactive mode if no arguments
        if not args.mode and not args.sheet_id:
            interactive_mode()
        else:
            # CLI mode
            cli_mode(args)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)

    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()