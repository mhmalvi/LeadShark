#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Smart Column Enricher on your Google Sheet
"""

import sys
import os

# Fix Windows Unicode issues
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

from smart_column_enricher import SmartColumnEnricher

# Your sheet configuration
SHEET_ID = "1iop2lVOkA1LsZgrK9tmtCPx_6Mcgr0wkuElWa0wqxeU"

def main():
    print("=" * 70)
    print("LeadShark - Smart Column Enricher Test")
    print("=" * 70)
    print(f"\nSheet ID: {SHEET_ID}")
    print("Mode: TEST (analyzing data, not writing yet)")
    print("Rows: 5 (test)\n")
    
    # Initialize enricher
    enricher = SmartColumnEnricher(sheet_id=SHEET_ID, dry_run=True)
    
    # Authenticate
    print("[Step 1] Authenticating...")
    if not enricher.authenticate():
        print("[FAIL] Authentication failed")
        return 1
    print("[OK] Authenticated\n")
    
    # Process sheet
    print("[Step 2] Processing sheet...")
    try:
        stats = enricher.process_sheet(max_rows=5)
        
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"Rows attempted: {stats['rows_attempted']}")
        print(f"Rows updated: {stats['rows_updated']}")
        print(f"Success: {stats['ok']}")
        print(f"Partial: {stats['partial']}")
        print(f"Failed: {stats['failed']}")
        print(f"Time: {stats.get('elapsed_seconds', 0):.1f}s")
        
        if stats.get('errors'):
            print(f"\nErrors:")
            for error in stats['errors'][:5]:
                print(f"  - {error}")
        
        print("\n" + "=" * 70)
        print("[OK] Test completed! Check the log file for detailed output.")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\n[FAIL] Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[WARN] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)