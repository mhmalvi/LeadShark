#!/usr/bin/env python3
"""
Fix column limit issue and run enrichment
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from compact_enricher import CompactEnricher
from google_sheets_auth import authenticate_google_sheets
from googleapiclient.discovery import build

def expand_sheet_columns(service, sheet_id, target_columns=60):
    """Expand the sheet to have more columns"""
    try:
        # Get sheet metadata
        sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])

        if not sheets:
            print("   No sheets found in the spreadsheet")
            return False

        sheet = sheets[0]  # Use first sheet
        sheet_name = sheet['properties']['title']
        current_cols = sheet['properties']['gridProperties']['columnCount']

        print(f"   Current columns: {current_cols}")
        print(f"   Target columns: {target_columns}")

        if current_cols >= target_columns:
            print("   Sheet already has enough columns")
            return True

        # Expand the sheet
        requests = [{
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet['properties']['sheetId'],
                    'gridProperties': {
                        'columnCount': target_columns
                    }
                },
                'fields': 'gridProperties.columnCount'
            }
        }]

        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={'requests': requests}
        ).execute()

        print(f"   SUCCESS: Expanded sheet to {target_columns} columns")
        return True

    except Exception as e:
        print(f"   FAILED: Could not expand sheet: {e}")
        return False

def main():
    """Fix columns and run enrichment"""

    print("=" * 60)
    print("LEADSHARK - COLUMN FIX AND ENRICHMENT")
    print("=" * 60)

    sheet_id = "1iop2lVOkA1LsZgrK9tmtCPx_6Mcgr0wkuElWa0wqxeU"
    print(f"Processing sheet: {sheet_id}")

    # Authenticate first
    print("\n1. Authenticating...")
    service = authenticate_google_sheets()
    if not service:
        print("   FAILED: Authentication failed")
        return 1
    print("   SUCCESS: Authenticated with Google Sheets")

    # Try to expand columns
    print("\n2. Checking and expanding columns...")
    if not expand_sheet_columns(service, sheet_id, 60):
        print("   WARNING: Could not expand columns, trying with existing columns")

    # Initialize enricher
    enricher = CompactEnricher(sheet_id, dry_run=False)

    if not enricher.authenticate():
        print("   FAILED: Enricher authentication failed")
        return 1

    # Run enrichment
    print("\n3. Starting enrichment...")
    stats = enricher.process_sheet(max_rows=5)

    print("\n4. Results:")
    print(f"   Rows attempted: {stats.get('rows_attempted', 0)}")
    print(f"   Rows updated: {stats.get('rows_updated', 0)}")
    print(f"   Success: {stats.get('ok', 0)}")
    print(f"   Partial: {stats.get('partial', 0)}")
    print(f"   Failed: {stats.get('failed', 0)}")
    print(f"   Processing time: {stats.get('elapsed_seconds', 0):.1f}s")

    if stats.get('errors'):
        print(f"\n   Errors ({len(stats['errors'])}):")
        for error in stats['errors'][:5]:
            print(f"     - {error}")

    # Summary
    print("\n" + "=" * 60)
    if stats.get('rows_updated', 0) > 0:
        print("SUCCESS: Data has been written to your Google Sheet!")
        print("Check the enrichment columns for the new data.")
        return 0
    else:
        print("No rows were updated. Check errors above.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nEnrichment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)