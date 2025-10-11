#!/usr/bin/env python3
"""Check row data to see what's missing"""

import os
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from google_sheets_auth import authenticate_google_sheets

os.environ['GOOGLE_SHEET_ID'] = '1iop2lVOkA1LsZgrK9tmtCPx_6Mcgr0wkuElWa0wqxeU'

sheets_service, drive_service, creds = authenticate_google_sheets()

print("Reading sheet data...")
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=os.environ['GOOGLE_SHEET_ID'],
    range='A1:CZ100'  # Get first 100 rows, all columns
).execute()
rows = result.get('values', [])

print(f"\nTotal rows: {len(rows)}")
print(f"Total columns: {len(rows[0]) if rows else 0}")

headers = rows[0]

# Find enrichment columns
enrich_cols = [(i, h) for i, h in enumerate(headers) if h.startswith('Enrich::')]
print(f"\nEnrichment columns found: {len(enrich_cols)}")

# Check rows 1-5
for row_num in range(1, min(6, len(rows))):
    print(f"\n{'='*80}")
    print(f"ROW {row_num} DATA:")
    print('='*80)

    row = rows[row_num]

    # Basic info
    print(f"Name: {row[0] if len(row) > 0 else 'N/A'}")
    print(f"Company: {row[1] if len(row) > 1 else 'N/A'}")
    print(f"Email: {row[2] if len(row) > 2 else 'N/A'}")

    # Check enrichment columns
    print("\nEnrichment Status:")
    empty_count = 0
    filled_count = 0

    for col_idx, col_name in enrich_cols[:20]:  # Show first 20 enrichment columns
        value = row[col_idx] if col_idx < len(row) else ''
        status = "✅" if value.strip() else "❌"
        if value.strip():
            filled_count += 1
        else:
            empty_count += 1

        # Only show name for brevity
        short_name = col_name.replace('Enrich::', '').replace('🤖 ', '').replace('📨 ', '').replace('🎯 ', '')
        print(f"  {status} {short_name[:40]}: {'[filled]' if value.strip() else '[empty]'}")

    print(f"\nSummary: {filled_count} filled, {empty_count} empty (out of first 20)")

print("\n" + "="*80)
