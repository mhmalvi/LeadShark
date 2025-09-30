#!/usr/bin/env python3
"""
Simple script to run live enrichment with automatic column expansion.
"""

import sys
from google_sheets_auth import authenticate_google_sheets

# Your sheet configuration
SHEET_ID = "1iop2lVOkA1LsZgrK9tmtCPx_6Mcgr0wkuElWa0wqxeU"
WORKSHEET_NAME = "Data"
TARGET_COLUMNS = 80  # Expand to 80 columns to have plenty of room

def expand_columns(sheet_id, worksheet_name="Data", target_cols=80):
    """Expand the Google Sheet to have enough columns."""
    print(f"\n🔧 Expanding sheet to {target_cols} columns...")

    # Get the service (it returns a tuple)
    result = authenticate_google_sheets(show_progress=False)
    if isinstance(result, tuple):
        service = result[0]  # First element is sheets service
    else:
        service = result

    try:
        # Get spreadsheet metadata
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()

        # Find the worksheet
        sheet = None
        for s in spreadsheet['sheets']:
            if s['properties']['title'] == worksheet_name:
                sheet = s
                break

        if not sheet:
            print(f"❌ Worksheet '{worksheet_name}' not found!")
            return False

        sheet_id_num = sheet['properties']['sheetId']
        current_columns = sheet['properties']['gridProperties']['columnCount']

        print(f"   Current columns: {current_columns}")

        if current_columns >= target_cols:
            print(f"✅ Sheet already has {current_columns} columns")
            return True

        # Expand columns
        request = {
            'requests': [{
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': sheet_id_num,
                        'gridProperties': {
                            'columnCount': target_cols
                        }
                    },
                    'fields': 'gridProperties.columnCount'
                }
            }]
        }

        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=request
        ).execute()

        print(f"✅ Expanded to {target_cols} columns!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("🦈 LeadShark - Live Enrichment Runner")
    print("=" * 70)
    print(f"\nSheet ID: {SHEET_ID}")
    print(f"Worksheet: {WORKSHEET_NAME}")

    # Step 1: Expand columns
    print("\n[Step 1] Expanding columns...")
    if not expand_columns(SHEET_ID, WORKSHEET_NAME, TARGET_COLUMNS):
        print("\n⚠️  Column expansion failed, but will try to continue...")

    # Step 2: Run enrichment
    print("\n[Step 2] Running compact enrichment...")
    print("   Mode: LIVE (will write data)")
    print("   Rows: 5 (test)")

    from compact_enricher import CompactEnricher

    enricher = CompactEnricher(
        sheet_id=SHEET_ID,
        dry_run=False  # LIVE MODE
    )

    try:
        # Authenticate first
        if not enricher.authenticate():
            print("❌ Authentication failed")
            return 1

        # Process sheet with max_rows parameter
        stats = enricher.process_sheet(max_rows=5)
        
        print("\n✅ Enrichment completed!")
        print(f"   Rows attempted: {stats.get('rows_attempted', 0)}")
        print(f"   Rows updated: {stats.get('rows_updated', 0)}")
        print(f"   Success: {stats.get('ok', 0)}")
        print(f"   Failed: {stats.get('failed', 0)}")
        
    except Exception as e:
        print(f"\n❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 70)
    print(f"📊 View results: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)