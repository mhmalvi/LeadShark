#!/usr/bin/env python3
"""
LeadShark - Predatory Lead Enrichment System

Features:
- Interactive Google OAuth sign-in with scope verification
- Smart lead sheet selection with worksheet picker
- Real-time hunt progress tracking with rich UX
- Non-destructive lead enrichment and intelligence gathering
- Comprehensive error handling and recovery for maximum efficiency
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from cli_interface import CLIInterface, install_rich_hint
    from google_sheets_auth import (
        authenticate_google_sheets,
        parse_sheet_id_from_url,
        get_sheet_metadata,
        preview_sheet_data,
        validate_sheet_access
    )
    from non_destructive_enricher import NonDestructiveEnricher
    from compact_enricher import CompactEnricher
    from enhanced_scraping_pipeline import EnhancedScrapingPipeline
    from data_enrichment import DataEnrichment
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required files are in the current directory")
    sys.exit(1)

def load_config():
    """Load configuration from environment or defaults"""
    return {
        'max_rows_per_batch': int(os.getenv('MAX_ROWS_PER_BATCH', '50')),
        'processing_delay': float(os.getenv('PROCESSING_DELAY', '2.0')),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'rate_profile_multiplier': {
            'default': 1.0,
            'slow': 2.5
        }
    }

def interactive_sheet_selection(cli: CLIInterface, sheets_service, drive_service) -> Optional[Dict]:
    """Interactive sheet selection flow"""
    while True:
        # Get sheet input from user
        sheet_input = cli.prompt_sheet_input()
        if not sheet_input:
            cli.print_error("Sheet input is required")
            continue

        # Parse sheet ID
        sheet_id = parse_sheet_id_from_url(sheet_input)
        if not sheet_id:
            cli.print_error("Invalid Google Sheet URL or ID")
            continue

        cli.print_info(f"Validating sheet access...")

        # Validate access and get metadata
        valid, metadata = validate_sheet_access(sheets_service, drive_service, sheet_id)
        if not valid:
            cli.print_error("Cannot access sheet. Please check permissions and try again.")
            continue

        cli.print_success(f">> LeadShark connected to hunting ground: {metadata['title']}")

        # Select worksheet
        sheet_name = cli.select_worksheet(metadata)
        if not sheet_name:
            continue

        # Get preview
        cli.print_info("Loading sheet preview...")
        preview_data = preview_sheet_data(sheets_service, sheet_id, sheet_name)
        if not preview_data:
            cli.print_error("Cannot load sheet preview")
            continue

        # Show preview and get confirmation
        if cli.show_sheet_preview(preview_data):
            return {
                'sheet_id': sheet_id,
                'sheet_name': sheet_name,
                'metadata': metadata,
                'preview': preview_data
            }
        else:
            cli.print_info("Sheet selection cancelled. Please choose another sheet.")

def process_with_live_progress(enricher: NonDestructiveEnricher, cli: CLIInterface,
                              sheet_info: Dict, options: Dict) -> Dict[str, Any]:
    """Process sheet with live progress display"""
    sheet_id = sheet_info['sheet_id']
    sheet_name = sheet_info['sheet_name']
    total_rows = sheet_info['preview']['total_rows']
    dry_run = options.get('dry_run', False)

    # Determine actual rows to process
    if options.get('all_rows'):
        max_rows = None
        rows_to_process = total_rows
    else:
        max_rows = options.get('max_rows', 5)
        rows_to_process = min(max_rows, total_rows)

    # Create progress display
    mode = f"{rows_to_process} rows" if max_rows else "all rows"
    progress = cli.create_progress_display(rows_to_process, mode, sheet_name, dry_run)

    stats = {
        'rows_attempted': 0,
        'rows_updated': 0,
        'ok': 0,
        'partial': 0,
        'failed': 0,
        'skipped': 0,
        'errors': [],
        'start_time': time.time()
    }

    try:
        with progress:
            # Setup enricher for progress tracking
            enricher.cli = cli  # Inject CLI for progress updates

            # Process the sheet
            result_stats = enricher.process_sheet(max_rows=max_rows)

            # Merge stats
            stats.update(result_stats)

    except KeyboardInterrupt:
        cli.print_warning("Processing interrupted by user")
        stats['errors'].append("User interruption")
    except Exception as e:
        cli.print_error(f"Processing failed: {e}")
        stats['errors'].append(str(e))

    stats['elapsed_time'] = time.time() - stats['start_time']
    return stats

def main():
    """Main execution function with interactive flow"""
    # Initialize CLI interface
    cli = CLIInterface()

    # Check if rich is available
    try:
        import rich
    except ImportError:
        install_rich_hint()

    # Show banner
    cli.print_banner()

    # Parse command line arguments (for override options)
    parser = argparse.ArgumentParser(
        description='LeadShark - Predatory Lead Enrichment System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py                          # Interactive mode
  python run_pipeline.py --sheet SHEET_ID --test  # Quick test run
  python run_pipeline.py --dry-run               # Preview mode
  python run_pipeline.py --sheet SHEET_ID --all  # Process all rows
        """
    )

    parser.add_argument('--sheet', help='Google Sheet ID or URL (skips interactive selection)')
    parser.add_argument('--tab', help='Specific worksheet name (skips tab selection)')
    parser.add_argument('--test', action='store_true', help='Test mode - process first 5 rows')
    parser.add_argument('--all', action='store_true', help='Process all rows')
    parser.add_argument('--rows', type=int, help='Number of rows to process')
    parser.add_argument('--start', type=int, help='Start from row number', default=2)
    parser.add_argument('--dry-run', action='store_true', help='Preview mode - no actual writes')
    parser.add_argument('--rate-profile', choices=['default', 'slow'], default='default',
                       help='Rate limiting profile')
    parser.add_argument('--force-auth', action='store_true', help='Force re-authentication')

    args = parser.parse_args()

    try:
        # Step 1: Google OAuth Authentication
        cli.print_info("[*] Connecting to Google...")

        auth_result = authenticate_google_sheets(
            force_consent=args.force_auth,
            show_progress=True
        )

        if not auth_result:
            cli.print_error("Google authentication failed")
            return 1

        sheets_service, drive_service, creds = auth_result
        cli.print_success("Google services connected successfully")

        # Step 2: Sheet Selection
        if args.sheet:
            # Non-interactive mode with provided sheet
            sheet_id = parse_sheet_id_from_url(args.sheet)
            if not sheet_id:
                cli.print_error("Invalid sheet ID or URL provided")
                return 1

            cli.print_info(f"Validating provided sheet...")
            valid, metadata = validate_sheet_access(sheets_service, drive_service, sheet_id)
            if not valid:
                return 1

            # Select worksheet
            if args.tab:
                # Use provided tab name
                sheet_name = args.tab
                # Validate tab exists
                tab_exists = any(sheet['title'] == args.tab for sheet in metadata['sheets'])
                if not tab_exists:
                    cli.print_error(f"Worksheet '{args.tab}' not found in sheet")
                    available_tabs = [sheet['title'] for sheet in metadata['sheets']]
                    cli.print_info(f"Available worksheets: {', '.join(available_tabs)}")
                    return 1
            else:
                # Use first sheet
                sheet_name = metadata['sheets'][0]['title'] if metadata['sheets'] else 'Sheet1'

            # Get preview
            preview_data = preview_sheet_data(sheets_service, sheet_id, sheet_name)
            if not preview_data:
                cli.print_error("Cannot load sheet preview")
                return 1

            sheet_info = {
                'sheet_id': sheet_id,
                'sheet_name': sheet_name,
                'metadata': metadata,
                'preview': preview_data
            }
        else:
            # Interactive sheet selection
            sheet_info = interactive_sheet_selection(cli, sheets_service, drive_service)
            if not sheet_info:
                cli.print_info("No sheet selected. Exiting.")
                return 0

        # Step 3: Processing Options
        if any([args.test, args.all, args.rows, args.dry_run]):
            # Use command line options
            options = {
                'dry_run': args.dry_run,
                'all_rows': args.all,
                'start_row': args.start,
                'rate_profile': args.rate_profile
            }

            if args.test:
                options['max_rows'] = 5
            elif args.rows:
                options['max_rows'] = args.rows
            elif not args.all:
                options['max_rows'] = 5  # Default
        else:
            # Interactive mode selection
            options = cli.prompt_processing_mode()
            options['start_row'] = args.start
            options['rate_profile'] = args.rate_profile

        # Step 4: Choose Enrichment Strategy
        cli.print_info("[~] Analyzing sheet capacity...")

        # Check column count to determine enrichment strategy
        total_columns = len(sheet_info['preview']['headers'])
        available_space = 60 - total_columns  # Conservative Google Sheets lead capacity limit

        use_compact = False
        if available_space < 20:  # Need 22+ columns for full enrichment
            cli.print_warning(f"Sheet has {total_columns} columns. Using compact enrichment (5 columns).")
            use_compact = True
        else:
            cli.print_info(f"Sheet has {total_columns} columns. Using full enrichment.")

        # Initialize appropriate enricher
        cli.print_info("[>] Initializing enrichment engine...")

        if use_compact:
            enricher = CompactEnricher(
                sheet_id=sheet_info['sheet_id'],
                dry_run=options.get('dry_run', False)
            )
        else:
            enricher = NonDestructiveEnricher(
                sheet_id=sheet_info['sheet_id'],
                dry_run=options.get('dry_run', False)
            )

        # Authenticate enricher (reuse existing services)
        enricher.service = sheets_service
        enricher.drive_service = drive_service

        # Apply rate profile
        config = load_config()
        rate_multiplier = config['rate_profile_multiplier'].get(options['rate_profile'], 1.0)
        enricher.scraper.apply_rate_multiplier(rate_multiplier)

        # Step 5: Process with Live Progress
        cli.print_info(f"[~] Processing {sheet_info['sheet_name']}...")

        stats = process_with_live_progress(enricher, cli, sheet_info, options)

        # Step 6: Show Final Summary
        cli.show_final_summary(stats, stats['elapsed_time'])

        # Save processing log
        log_file = f"sheets_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(log_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'sheet_info': {
                    'id': sheet_info['sheet_id'],
                    'name': sheet_info['sheet_name'],
                    'title': sheet_info['metadata']['title']
                },
                'options': options,
                'stats': stats
            }, f, indent=2)

        if options.get('dry_run'):
            cli.print_info("[~] Dry run completed - no changes were made to your sheet")
            cli.print_info("Remove --dry-run flag to apply changes")
        else:
            cli.print_success(f"✅ Enrichment completed!")
            cli.print_info(f"📊 View your sheet: {sheet_info['metadata']['url']}")

        return 0 if stats['rows_updated'] > 0 or options.get('dry_run') else 1

    except KeyboardInterrupt:
        cli.print_warning("Process interrupted by user")
        return 1
    except Exception as e:
        cli.print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())