#!/usr/bin/env python3
"""
Add enrichment data to the next available columns in Google Sheets
This script safely finds available space and adds enrichment results
"""

import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from google_sheets_auth import authenticate_google_sheets, read_sheet, write_to_sheet

def add_enrichment_to_sheet():
    """Add enrichment data to the Google Sheet in available columns"""

    SHEET_ID = "1l5aAzy5bhilmB3XfEBUbnL6Le8z1t0hFlmzLA5Gwq50"

    print("="*60)
    print("ADDING ENRICHMENT DATA TO GOOGLE SHEETS")
    print("="*60)

    # Authenticate
    service = authenticate_google_sheets()
    if not service:
        print("ERROR: Authentication failed")
        return False

    # Read the latest results file
    results_file = "enrichment_results_20250913_200703.json"
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        print(f"Loaded {len(results)} enrichment results")
    except FileNotFoundError:
        print("ERROR: Results file not found")
        return False

    # Read current sheet to find available columns
    print("Reading current sheet structure...")
    sheet_data = read_sheet(service, SHEET_ID, "A1:Z1")  # Read first row to see current headers

    if not sheet_data:
        print("ERROR: Could not read sheet")
        return False

    current_headers = sheet_data[0]
    print(f"Current sheet has {len(current_headers)} columns")

    # Find the first empty column after existing data
    # Let's use columns starting from a safe position
    next_available_col = len(current_headers) + 2  # Add buffer

    # Convert to column letters
    def col_index_to_letter(index):
        result = ""
        while index >= 0:
            result = chr(65 + (index % 26)) + result
            index = index // 26 - 1
        return result

    start_col_letter = col_index_to_letter(next_available_col)

    print(f"Adding enrichment data starting from column {start_col_letter}")

    # Create enrichment headers
    enrichment_headers = [
        'Enrichment_Date',
        'Email_Status',
        'Gender_Prediction',
        'GitHub_Status',
        'Website_Status',
        'LinkedIn_Status'
    ]

    end_col_letter = col_index_to_letter(next_available_col + len(enrichment_headers) - 1)

    # Write headers
    header_range = f"{start_col_letter}1:{end_col_letter}1"
    print(f"Writing headers to range: {header_range}")

    try:
        write_to_sheet(service, SHEET_ID, header_range, [enrichment_headers])
        print("SUCCESS: Headers written")
    except Exception as e:
        print(f"ERROR writing headers: {e}")
        return False

    # Prepare enrichment data
    enrichment_data = []
    for result in results:
        enrichment = result['enrichment_results']

        # Extract summary data
        email_status = "N/A"
        if 'email_verification' in enrichment:
            email_result = enrichment['email_verification']
            if email_result.get('status') == 'success':
                email_status = "VALID" if email_result.get('deliverable') else "INVALID"
            elif email_result.get('status') == 'error':
                email_status = "ERROR"

        gender = enrichment.get('gender_analysis', {}).get('gender', 'unknown')
        gender_conf = enrichment.get('gender_analysis', {}).get('probability', 0)
        gender_display = f"{gender} ({gender_conf*100:.0f}%)" if gender != 'unknown' else 'unknown'

        github_repos = enrichment.get('github_search', {}).get('total_repos', 0)
        github_status = "FOUND" if github_repos > 0 else "NONE"

        website_status = "SUCCESS" if enrichment.get('website_scraping', {}).get('status') == 'success' else "FAILED"

        linkedin_status = "ACCESSIBLE" if enrichment.get('linkedin_check', {}).get('accessible') else "BLOCKED"

        enrichment_data.append([
            result['enrichment_timestamp'][:10],  # Date only
            email_status,
            gender_display,
            github_status,
            website_status,
            linkedin_status
        ])

    # Write enrichment data
    data_range = f"{start_col_letter}2:{end_col_letter}{len(enrichment_data) + 1}"
    print(f"Writing data to range: {data_range}")

    try:
        write_to_sheet(service, SHEET_ID, data_range, enrichment_data)
        print("SUCCESS: Enrichment data written")
    except Exception as e:
        print(f"ERROR writing data: {e}")
        return False

    print(f"\n{'='*60}")
    print("ENRICHMENT DATA SUCCESSFULLY ADDED!")
    print(f"{'='*60}")
    print(f"Columns: {start_col_letter} to {end_col_letter}")
    print(f"Rows: {len(enrichment_data)} data rows")
    print(f"Spreadsheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")

    return True

if __name__ == "__main__":
    try:
        success = add_enrichment_to_sheet()
        if success:
            print("\nSUCCESS: Enrichment data added to Google Sheets!")
        else:
            print("\nFAILED: Check errors above")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()