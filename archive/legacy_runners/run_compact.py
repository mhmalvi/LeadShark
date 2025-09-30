#!/usr/bin/env python3
"""
Quick Compact Enricher Runner
Handles sheets with too many columns by using only 5 enrichment columns
"""

import sys
import os
from cli_interface import CLIInterface

sys.path.append(os.path.dirname(__file__))

from compact_enricher import CompactEnricher
from google_sheets_auth import (
    authenticate_google_sheets,
    parse_sheet_id_from_url,
    get_sheet_metadata,
    preview_sheet_data,
    validate_sheet_access
)

def main():
    """Main function for compact enrichment"""
    cli = CLIInterface()

    # Show banner
    cli.print_banner()
    cli.print_info("🎯 Compact Enrichment Mode - Uses only 5 columns!")

    try:
        # Step 1: Authentication
        cli.print_info("🔐 Connecting to Google...")
        auth_result = authenticate_google_sheets(show_progress=True)

        if not auth_result:
            cli.print_error("Google authentication failed")
            return 1

        sheets_service, drive_service, creds = auth_result

        # Step 2: Get sheet from user or use the one from error
        sheet_input = cli.prompt_sheet_input()
        if not sheet_input:
            # Use the sheet ID from the error for quick testing
            sheet_input = "1l5aAzy5bhilmB3XfEBUbnL6Le8z1t0hFlmzLA5Gwq50"
            cli.print_info(f"Using sheet from previous error: {sheet_input}")

        sheet_id = parse_sheet_id_from_url(sheet_input)
        if not sheet_id:
            cli.print_error("Invalid sheet ID or URL")
            return 1

        # Step 3: Validate and get metadata
        cli.print_info("Validating sheet access...")
        valid, metadata = validate_sheet_access(sheets_service, drive_service, sheet_id)
        if not valid:
            return 1

        cli.print_success(f"Connected to: {metadata['title']}")

        # Step 4: Select worksheet (use first one for speed)
        sheet_name = metadata['sheets'][0]['title']
        cli.print_info(f"Using worksheet: {sheet_name}")

        # Step 5: Quick preview
        preview_data = preview_sheet_data(sheets_service, sheet_id, sheet_name, max_rows=2)
        if not preview_data:
            cli.print_error("Cannot load preview")
            return 1

        total_columns = len(preview_data.get('headers', []))
        cli.print_info(f"Sheet has {total_columns} columns")

        if total_columns > 55:
            cli.print_warning("Sheet is near column limit - compact mode is perfect!")
        else:
            cli.print_info("Compact mode will use only 5 columns regardless")

        # Step 6: Initialize compact enricher
        cli.print_info("🚀 Initializing compact enricher...")

        enricher = CompactEnricher(sheet_id, dry_run=True)  # Start with dry run
        enricher.service = sheets_service
        enricher.drive_service = drive_service
        enricher.cli = cli  # For progress updates

        # Step 7: Process with progress
        rows_to_process = 3  # Small test
        cli.print_info(f"Processing {rows_to_process} rows (DRY RUN)...")

        if cli.use_rich:
            progress = cli.create_progress_display(
                rows_to_process,
                f"{rows_to_process} rows",
                sheet_name,
                dry_run=True
            )

            with progress:
                stats = enricher.process_sheet(max_rows=rows_to_process)
        else:
            stats = enricher.process_sheet(max_rows=rows_to_process)

        # Step 8: Show results
        cli.show_final_summary(stats, stats.get('elapsed_seconds', 0))

        if stats.get('rows_attempted', 0) > 0:
            cli.print_success("🎉 Compact enrichment test successful!")
            cli.print_info("💡 To run live: modify the script to set dry_run=False")
            cli.print_info("📊 Compact enrichment uses only 5 columns:")
            cli.print_info("   1. Enrich::Row Key")
            cli.print_info("   2. Enrich::Summary Report (Markdown)")
            cli.print_info("   3. Enrich::Key Data (JSON)")
            cli.print_info("   4. Enrich::Status & Meta (JSON)")
            cli.print_info("   5. Enrich::URLs & Sources (JSON)")

        return 0 if stats.get('rows_attempted', 0) > 0 else 1

    except KeyboardInterrupt:
        cli.print_warning("Process interrupted")
        return 1
    except Exception as e:
        cli.print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())