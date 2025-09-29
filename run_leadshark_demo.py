#!/usr/bin/env python3
"""
LeadShark Demo Runner
Demonstrates the core capabilities of the LeadShark lead enrichment system
"""

import os
import sys
import time
from datetime import datetime

# Add the current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from google_sheets_auth import authenticate_google_sheets, get_sheet_metadata, preview_sheet_data
from data_enrichment import DataEnrichment
from enhanced_scraping_pipeline import EnhancedScrapingPipeline

def main():
    print("=" * 60)
    print("LEADSHARK - PREDATORY LEAD ENRICHMENT SYSTEM")
    print("=" * 60)
    print()

    # 1. Authentication Test
    print("1. GOOGLE SHEETS AUTHENTICATION")
    print("-" * 30)
    result = authenticate_google_sheets()
    if not result:
        print("[FAILED] Google authentication failed")
        return

    sheets_service, drive_service, creds = result
    print("[SUCCESS] Google Sheets API connected")
    print()

    # 2. Sheet Analysis
    print("2. SHEET ANALYSIS & METADATA")
    print("-" * 30)
    sheet_id = os.getenv('GOOGLE_SHEET_ID', '1iop2lVOkA1LsZgrK9tmtCPx_6Mcgr0wkuElWa0wqxeU')

    metadata = get_sheet_metadata(sheets_service, drive_service, sheet_id)
    if metadata:
        print(f"Sheet Title: {metadata['title']}")
        print(f"Sheet ID: {metadata['id']}")
        print(f"Worksheets: {len(metadata['sheets'])}")
        for sheet in metadata['sheets']:
            print(f"  - {sheet['title']}: {sheet['rowCount']} rows x {sheet['columnCount']} cols")
        print(f"URL: {metadata['url']}")
    else:
        print("[FAILED] Could not access sheet")
        return
    print()

    # 3. Data Preview
    print("3. DATA PREVIEW")
    print("-" * 30)
    preview = preview_sheet_data(sheets_service, sheet_id, max_rows=5)
    if preview:
        print(f"Headers ({len(preview['headers'])}): {', '.join(preview['headers'][:5])}...")
        print(f"Data rows available: {preview['total_rows']}")
        print("Sample data (first 3 rows):")
        for i, row in enumerate(preview['preview_rows'][:3]):
            row_data = ', '.join(str(cell) for cell in row[:3]) + "..."
            print(f"  Row {i+2}: {row_data}")
    else:
        print("[WARNING] Could not preview data")
    print()

    # 4. Enrichment Engine Demo
    print("4. ENRICHMENT ENGINES")
    print("-" * 30)

    # Data enricher
    enricher = DataEnrichment()
    print(f"[READY] Data Enrichment API - Email verification & data APIs")

    # Web scraper
    scraper = EnhancedScrapingPipeline()
    print(f"[READY] Enhanced Scraping Pipeline - Multi-platform support")

    # Demo enrichment (safe test)
    print("\nTesting enrichment on sample email:")
    test_email = 'john.smith@techcorp.com'

    start_time = time.time()
    result = enricher.verify_email_eva(test_email)
    elapsed = time.time() - start_time

    print(f"Email verification completed in {elapsed:.2f}s")
    print(f"Service: {result.get('service', 'Unknown')}")
    print(f"Status: {result.get('status', 'Unknown')}")
    if result.get('deliverable') is not None:
        print(f"Deliverable: {result['deliverable']}")
    print()

    # 5. System Capabilities Summary
    print("5. SYSTEM CAPABILITIES")
    print("-" * 30)
    capabilities = [
        "+ Non-destructive lead enrichment",
        "+ Google Sheets API integration",
        "+ Multi-platform web scraping (LinkedIn, Facebook, Twitter/X)",
        "+ API-based data enhancement (Genderize, GitHub, Email verification)",
        "+ Smart column management (60-column limit handling)",
        "+ Compact vs Full enrichment strategies",
        "+ Real-time progress tracking",
        "+ Rate limiting and respectful scraping",
        "+ JSON-structured enrichment data",
        "+ Comprehensive error handling and logging"
    ]

    for capability in capabilities:
        print(f"  {capability}")
    print()

    # 6. Ready Status
    print("6. SYSTEM STATUS")
    print("-" * 30)
    print("[READY] LeadShark is fully operational and ready for lead enrichment")
    print(f"[CONFIG] Target sheet: {metadata['title']}")
    print(f"[CONFIG] Available data: {preview['total_rows'] if preview else 'Unknown'} prospect rows")
    print()
    print("To run live enrichment:")
    print("  python compact_enricher.py  # For 5-column compact mode")
    print("  python run_pipeline.py      # For full interactive mode")
    print()

if __name__ == "__main__":
    # Set environment
    os.environ['GOOGLE_SHEET_ID'] = '1iop2lVOkA1LsZgrK9tmtCPx_6Mcgr0wkuElWa0wqxeU'

    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[STOPPED] Demo interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()