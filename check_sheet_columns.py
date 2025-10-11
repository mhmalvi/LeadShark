#!/usr/bin/env python3
"""Check Google Sheet column headers"""

from google_sheets_auth import authenticate_google_sheets

# Authenticate
auth_result = authenticate_google_sheets()
if isinstance(auth_result, tuple):
    service = auth_result[0]
else:
    service = auth_result

sheet_id = '1iop2lVOkA1LsZgrK9tmtCPx_6Mcgr0wkuElWa0wqxeU'

# Read headers (row 1)
print("Reading sheet headers...")
headers_result = service.spreadsheets().values().get(
    spreadsheetId=sheet_id,
    range='Data!1:1'
).execute()
headers = headers_result.get('values', [[]])[0]

print(f'\n{"="*70}')
print(f'GOOGLE SHEET COLUMN ANALYSIS')
print(f'{"="*70}')
print(f'Total columns in sheet: {len(headers)}')

# Find Enrich:: columns
enrich_cols = [(i+1, h) for i, h in enumerate(headers) if 'Enrich::' in h]
print(f'\nTotal Enrich:: columns found: {len(enrich_cols)}')
print(f'Expected Enrich:: columns: 80 (v5.0)')

print(f'\n{"="*70}')
print(f'ALL ENRICHMENT COLUMNS IN SHEET:')
print(f'{"="*70}')
for idx, header in enrich_cols:
    print(f'{idx:3d}. {header}')

# Read row 2 data (first data row)
print(f'\n{"="*70}')
print(f'SAMPLE DATA - ROW 2 (Lorenzo Nuti):')
print(f'{"="*70}')
row_result = service.spreadsheets().values().get(
    spreadsheetId=sheet_id,
    range='Data!2:2'
).execute()
row_data = row_result.get('values', [[]])[0] if row_result.get('values') else []

# Show enrichment column data
enrich_start = min([idx-1 for idx, _ in enrich_cols]) if enrich_cols else 0
for idx, header in enrich_cols[:20]:  # Show first 20 enrichment columns
    value = row_data[idx-1] if idx-1 < len(row_data) else '(empty)'
    print(f'{header}: {value[:80] if len(str(value)) > 80 else value}')

print(f'\n{"="*70}')
print(f'MISSING v5.0 COLUMNS CHECK:')
print(f'{"="*70}')

# Expected v5.0 columns
expected_v5_columns = [
    'Enrich::📧 Email Variants (Generated)',
    'Enrich::📧 Best Email Found',
    'Enrich::📧 Email Confidence (0-100)',
    'Enrich::📧 Email Source',
    'Enrich::📰 Recent Activity/News',
    'Enrich::🎯 Pain Points (AI-Detected)',
    'Enrich::💬 Personalization Hook',
    'Enrich::⭐ Social Proof',
    'Enrich::🚀 Trigger Event',
    'Enrich::✉️ Subject Line #1 (Question)',
    'Enrich::✉️ Subject Line #2 (Activity)',
    'Enrich::✉️ Subject Line #3 (Value)',
    'Enrich::✉️ Opening Line',
    'Enrich::✉️ Value Proposition',
    'Enrich::✉️ Call-to-Action',
]

existing_headers = [h for _, h in enrich_cols]
missing = [col for col in expected_v5_columns if col not in existing_headers]

if missing:
    print(f'❌ MISSING {len(missing)} v5.0 columns:')
    for col in missing:
        print(f'   - {col}')
else:
    print('✅ All v5.0 columns are present!')

print(f'\n{"="*70}')
