#!/usr/bin/env python3
"""
Google Sheets Prospect Enrichment - Smart Column Detection & Creation (Python)

Production-grade CLI that reads Google Sheets, discovers URLs, scrapes/enriches data
while respecting ToS/robots.txt, and writes results back with smart column management.

Author: LeadShark Team
License: MIT
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel

from utils.logging import setup_logging, get_logger
from utils.sheets import GoogleSheetsManager
from utils.normalize import URLExtractor
from utils.scoring import LeadScorer
from handlers.orchestrator import EnrichmentOrchestrator

# Load environment variables
load_dotenv()

# Setup console with Windows compatibility
try:
    console = Console(force_terminal=True, legacy_windows=False)
except Exception:
    console = Console()

logger = get_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Google Sheets Prospect Enrichment with Smart Column Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --sheet-id 1ABC123 --worksheet "Sheet1"
  %(prog)s --sheet-id 1ABC123 --rows "2-100" --dry-run
  %(prog)s --sheet-id 1ABC123 --only-new --max-link-summaries 3
  %(prog)s --sheet-id 1ABC123 --force-domains "twitter.com,youtube.com"
        """
    )

    # Required arguments
    parser.add_argument(
        '--sheet-id',
        required=True,
        help='Google Sheet ID (or use GOOGLE_SHEET_ID env var)'
    )

    parser.add_argument(
        '--worksheet',
        default=os.getenv('WORKSHEET_NAME', 'Sheet1'),
        help='Worksheet name (default: Sheet1)'
    )

    # Optional processing parameters
    parser.add_argument(
        '--rows',
        help='Row range to process (e.g., "2-500"). Default: all rows'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing to sheet'
    )

    parser.add_argument(
        '--only-new',
        action='store_true',
        help='Process only rows with empty COMBINED_REPORT'
    )

    parser.add_argument(
        '--force-domains',
        help='Comma-separated list of domains to restrict processing'
    )

    parser.add_argument(
        '--max-link-summaries',
        type=int,
        default=int(os.getenv('MAX_LINK_SUMMARIES', '5')),
        help='Number of per-link summary columns to create/maintain'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Bypass cache and force fresh data retrieval'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Increase verbosity (-v, -vv, -vvv)'
    )

    return parser.parse_args()


def validate_environment() -> dict:
    """Validate required environment variables and return config."""
    config = {}

    # Required environment variables
    required_vars = {
        'GOOGLE_AUTH_MODE': 'oauth',
        'HEADER_NAMESPACE': 'ENRICH_',
        'PER_DOMAIN_RPS': '0.2',
        'TIMEOUT_SECONDS': '20',
        'MAX_CELL_CHARS': '4000',
        'MAX_COMBINED_CHARS': '5000',
        'USER_AGENT': 'ProspectResearchBot/1.0 (+contact@example.com)',
        'DRY_RUN': 'false'
    }

    for var, default in required_vars.items():
        config[var] = os.getenv(var, default)

    # Convert numeric values
    try:
        config['PER_DOMAIN_RPS'] = float(config['PER_DOMAIN_RPS'])
        config['TIMEOUT_SECONDS'] = int(config['TIMEOUT_SECONDS'])
        config['MAX_CELL_CHARS'] = int(config['MAX_CELL_CHARS'])
        config['MAX_COMBINED_CHARS'] = int(config['MAX_COMBINED_CHARS'])
        config['DRY_RUN'] = config['DRY_RUN'].lower() == 'true'
    except ValueError as e:
        logger.error(f"Invalid environment variable format: {e}")
        sys.exit(1)

    # Optional API keys
    config['TWITTER_BEARER'] = os.getenv('TWITTER_BEARER', '')
    config['YOUTUBE_API_KEY'] = os.getenv('YOUTUBE_API_KEY', '')

    return config


def parse_row_range(row_range: Optional[str]) -> Optional[tuple[int, int]]:
    """Parse row range string into start, end tuple."""
    if not row_range:
        return None

    try:
        if '-' in row_range:
            start, end = row_range.split('-', 1)
            return int(start.strip()), int(end.strip())
        else:
            row_num = int(row_range.strip())
            return row_num, row_num
    except ValueError:
        logger.error(f"Invalid row range format: {row_range}")
        sys.exit(1)


def display_config_summary(config: dict, args: argparse.Namespace):
    """Display configuration summary in a nice table."""
    table = Table(title="LeadShark Enrichment Configuration", show_header=True)
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Core settings
    table.add_row("Sheet ID", args.sheet_id[:20] + "..." if len(args.sheet_id) > 20 else args.sheet_id)
    table.add_row("Worksheet", args.worksheet)
    table.add_row("Max Link Summaries", str(args.max_link_summaries))
    table.add_row("Dry Run", "Yes" if args.dry_run else "No")
    table.add_row("Only New Rows", "Yes" if args.only_new else "No")

    # Processing settings
    if args.rows:
        table.add_row("Row Range", args.rows)
    if args.force_domains:
        table.add_row("Force Domains", args.force_domains)

    # API availability
    api_status = []
    if config.get('TWITTER_BEARER'):
        api_status.append("Twitter OK")
    if config.get('YOUTUBE_API_KEY'):
        api_status.append("YouTube OK")

    table.add_row("Available APIs", ", ".join(api_status) if api_status else "None (scraping only)")
    table.add_row("Rate Limit", f"{config['PER_DOMAIN_RPS']} RPS")
    table.add_row("Cache", "Disabled" if args.no_cache else "Enabled")

    console.print(table)
    console.print()


async def main():
    """Main application entry point."""
    args = parse_arguments()

    # Setup logging
    log_level = logging.WARNING
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG

    setup_logging(level=log_level)

    # Welcome message
    console.print(Panel.fit(
        "[bold cyan]LeadShark Prospect Enrichment[/bold cyan]\n"
        "Smart Column Detection & ToS-Compliant Data Collection",
        border_style="cyan"
    ))

    try:
        # Validate environment and configuration
        config = validate_environment()

        # Override dry run if specified in args
        if args.dry_run:
            config['DRY_RUN'] = True

        # Display configuration
        display_config_summary(config, args)

        # Parse row range
        row_range = parse_row_range(args.rows)

        # Force domains list
        force_domains = []
        if args.force_domains:
            force_domains = [d.strip() for d in args.force_domains.split(',')]

        # Initialize Google Sheets manager
        logger.info("Initializing Google Sheets connection...")
        sheets_manager = GoogleSheetsManager(
            sheet_id=args.sheet_id,
            auth_mode=config['GOOGLE_AUTH_MODE']
        )

        # Initialize URL extractor
        url_extractor = URLExtractor()

        # Initialize lead scorer
        lead_scorer = LeadScorer()

        # Initialize enrichment orchestrator
        orchestrator = EnrichmentOrchestrator(
            sheets_manager=sheets_manager,
            url_extractor=url_extractor,
            lead_scorer=lead_scorer,
            config=config
        )

        # Setup managed columns (smart column detection)
        logger.info("Setting up managed column headers...")
        await orchestrator.setup_managed_columns(
            worksheet_name=args.worksheet,
            max_link_summaries=args.max_link_summaries
        )

        # Process the sheet
        logger.info("Starting enrichment process...")
        results = await orchestrator.process_sheet(
            worksheet_name=args.worksheet,
            row_range=row_range,
            only_new=args.only_new,
            force_domains=force_domains,
            use_cache=not args.no_cache,
            dry_run=config['DRY_RUN']
        )

        # Display results summary
        if config['DRY_RUN']:
            console.print("\n[yellow]DRY RUN COMPLETED - No changes written to sheet[/yellow]")
        else:
            console.print(f"\n[green]Enrichment completed successfully![/green]")

        # Results table
        results_table = Table(title="Processing Results", show_header=True)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Count", style="white", justify="right")

        results_table.add_row("Total Rows Processed", str(results.get('total_processed', 0)))
        results_table.add_row("Successful Enrichments", str(results.get('successful', 0)))
        results_table.add_row("Skipped (ToS/Robots)", str(results.get('skipped_tos', 0)))
        results_table.add_row("No URLs Found", str(results.get('no_urls', 0)))
        results_table.add_row("Errors", str(results.get('errors', 0)))

        console.print(results_table)

        if results.get('errors', 0) > 0:
            console.print(f"\n[yellow]Check logs for error details[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        console.print(f"\n[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())