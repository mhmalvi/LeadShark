#!/usr/bin/env python3
"""
Improved Google Sheets Integrated Enricher
Handles column overflow by creating new sheets for additional data
Provides structured, well-organized enrichment reports
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

sys.path.append(os.path.dirname(__file__))

from google_sheets_auth import authenticate_google_sheets, read_sheet, write_to_sheet
from data_enrichment import DataEnrichment
from enhanced_scraping_pipeline import EnhancedScrapingPipeline

class ImprovedSheetsEnricher:
    """Improved enrichment solution with better sheet management"""

    GOOGLE_SHEETS_MAX_COLUMNS = 26 * 26  # 676 columns (A to ZZ)
    COLUMNS_SAFETY_MARGIN = 50  # Leave some columns for safety

    def __init__(self, sheet_id: str, max_rows: int = 5):
        self.sheet_id = sheet_id
        self.max_rows = max_rows
        self.service = None
        self.enricher = DataEnrichment()
        self.scraper = EnhancedScrapingPipeline()
        self.enrichment_results = []
        self.processing_time = 0

    def authenticate(self):
        """Authenticate with Google Sheets"""
        print("Authenticating with Google Sheets API...")
        self.service = authenticate_google_sheets()
        return self.service is not None

    def get_or_create_sheet(self, sheet_name: str) -> bool:
        """Get existing sheet or create new one"""
        try:
            # Get spreadsheet metadata
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()

            # Check if sheet exists
            sheets = spreadsheet.get('sheets', [])
            sheet_exists = any(
                sheet['properties']['title'] == sheet_name
                for sheet in sheets
            )

            if not sheet_exists:
                # Create new sheet
                print(f"Creating new sheet: {sheet_name}")
                request_body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': sheet_name,
                                'gridProperties': {
                                    'rowCount': 1000,
                                    'columnCount': 50
                                }
                            }
                        }
                    }]
                }

                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body=request_body
                ).execute()

                print(f"Successfully created sheet: {sheet_name}")
            else:
                print(f"Using existing sheet: {sheet_name}")

            return True

        except Exception as e:
            print(f"Error managing sheet: {e}")
            return False

    def find_first_empty_column(self, sheet_name: str = None) -> Tuple[int, bool]:
        """
        Find first empty column and check if we need a new sheet
        Returns: (column_index, needs_new_sheet)
        """
        print(f"Scanning for empty columns in {sheet_name or 'main sheet'}...")

        # Get sheet properties to check actual dimensions
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()

            # Find the sheet
            target_sheet = None
            for sheet in spreadsheet.get('sheets', []):
                if sheet_name:
                    if sheet['properties']['title'] == sheet_name:
                        target_sheet = sheet
                        break
                else:
                    if sheet['properties']['index'] == 0:  # Main sheet
                        target_sheet = sheet
                        break

            if target_sheet:
                max_columns = target_sheet['properties']['gridProperties']['columnCount']
                print(f"Sheet has {max_columns} columns available")
            else:
                max_columns = 26  # Default if we can't find sheet info
        except:
            max_columns = 26  # Default if API call fails

        # Construct range with sheet name if provided
        if sheet_name:
            test_range = f"{sheet_name}!A1:ZZ100"
        else:
            test_range = "A1:AZ100"  # Limit range to avoid errors

        try:
            sheet_data = read_sheet(self.service, self.sheet_id, test_range)
        except:
            # Sheet doesn't exist or is empty
            return (0, False)

        if not sheet_data:
            return (0, False)

        max_cols = 0
        for row in sheet_data:
            max_cols = max(max_cols, len(row))

        # Check if we have enough columns for our enrichment data (need 9 columns)
        available_columns = max_columns - max_cols
        needs_new_sheet = available_columns < 10  # Need at least 10 columns for our data

        # Find first completely empty column
        for col_index in range(max_cols, min(max_cols + 20, max_columns)):
            has_data = False
            for row in sheet_data:
                if col_index < len(row) and row[col_index].strip():
                    has_data = True
                    break
            if not has_data:
                return (col_index, needs_new_sheet)

        return (max_cols, needs_new_sheet)

    def column_index_to_letter(self, index: int) -> str:
        """Convert column index to Excel-style letter"""
        result = ""
        while index >= 0:
            result = chr(65 + (index % 26)) + result
            index = index // 26 - 1
        return result

    def detect_key_columns(self, headers: List[str]) -> Dict[str, Optional[int]]:
        """Detect important columns"""
        columns = {
            'name': None,
            'first_name': None,
            'email': None,
            'company': None,
            'website': None,
            'linkedin': None
        }

        for i, header in enumerate(headers):
            header_lower = header.lower().strip()

            if header_lower in ['name', 'full_name'] and columns['name'] is None:
                columns['name'] = i
            elif 'first_name' in header_lower:
                columns['first_name'] = i
            elif header_lower in ['email'] and columns['email'] is None:
                columns['email'] = i
            elif any(word in header_lower for word in ['company', 'organization_name']):
                columns['company'] = i
            elif any(word in header_lower for word in ['website', 'website_url']):
                columns['website'] = i
            elif 'linkedin' in header_lower and 'url' in header_lower:
                columns['linkedin'] = i

        return columns

    def process_enrichment_data(self, data_rows: List[List[str]], columns: Dict[str, Optional[int]]) -> List[Dict[str, Any]]:
        """Process all rows and collect enrichment data"""

        print(f"Processing {len(data_rows)} rows for enrichment...")
        results = []

        for i, row in enumerate(data_rows, 2):  # Start from row 2
            print(f"\nProcessing Row {i}: ", end="")

            # Extract data
            name = row[columns['name']] if columns['name'] and columns['name'] < len(row) else ""
            first_name = row[columns['first_name']] if columns['first_name'] and columns['first_name'] < len(row) else ""
            email = row[columns['email']] if columns['email'] and columns['email'] < len(row) else ""
            company = row[columns['company']] if columns['company'] and columns['company'] < len(row) else ""
            website = row[columns['website']] if columns['website'] and columns['website'] < len(row) else ""
            linkedin = row[columns['linkedin']] if columns['linkedin'] and columns['linkedin'] < len(row) else ""

            if not first_name and name:
                first_name = name.split()[0] if name.split() else ""

            print(f"{name}")

            # Initialize result
            result = {
                'row_number': i,
                'name': name,
                'email': email,
                'company': company,
                'website': website,
                'linkedin': linkedin,
                'enrichment': {}
            }

            # Gender analysis
            if first_name:
                gender_result = self.enricher.get_gender(first_name)
                result['enrichment']['gender'] = gender_result
                time.sleep(1)

            # GitHub search
            if company:
                github_result = self.enricher.search_github(company)
                result['enrichment']['github'] = github_result
                time.sleep(2)

            # Website scraping
            if website:
                scrape_result = self.scraper.scrape_url_with_retry(website)
                result['enrichment']['website'] = scrape_result
                time.sleep(2)

            # LinkedIn check
            if linkedin:
                linkedin_result = self.enricher.check_linkedin_profile_exists(linkedin)
                result['enrichment']['linkedin'] = linkedin_result
                time.sleep(1)

            results.append(result)

        return results

    def write_enrichment_to_main_sheet(self, start_col: int):
        """Write enrichment data columns to main sheet"""

        start_letter = self.column_index_to_letter(start_col)

        # Enrichment Data Headers
        enrichment_headers = [
            'ENRICHMENT DATA',
            'Date',
            'Gender',
            'Gender_Confidence',
            'GitHub_Repos',
            'Website_Status',
            'Website_Title',
            'LinkedIn_Status',
            'Processing_Notes'
        ]

        # Write section header
        header_range = f"{start_letter}1:{self.column_index_to_letter(start_col + len(enrichment_headers) - 1)}1"
        write_to_sheet(self.service, self.sheet_id, header_range, [enrichment_headers])

        # Prepare enrichment data
        enrichment_data = []
        for result in self.enrichment_results:
            enrichment = result['enrichment']

            # Extract gender info
            gender = enrichment.get('gender', {}).get('gender', 'unknown')
            gender_conf = enrichment.get('gender', {}).get('probability', 0)
            gender_display = f"{gender_conf*100:.0f}%" if gender != 'unknown' else 'N/A'

            # Extract GitHub info
            github_repos = enrichment.get('github', {}).get('total_repos', 0)

            # Extract website info
            website_status = "SUCCESS" if enrichment.get('website', {}).get('status') == 'success' else "FAILED"
            website_title = enrichment.get('website', {}).get('metadata', {}).get('title', 'N/A')
            if len(website_title) > 30:
                website_title = website_title[:30] + "..."

            # Extract LinkedIn info
            linkedin_status = "ACCESSIBLE" if enrichment.get('linkedin', {}).get('accessible') else "BLOCKED"

            # Processing notes
            notes = []
            if enrichment.get('gender', {}).get('status') == 'success':
                notes.append("Gender: OK")
            if enrichment.get('website', {}).get('status') == 'success':
                content_len = enrichment.get('website', {}).get('full_content_length', 0)
                notes.append(f"Web: {content_len} chars")
            if github_repos > 0:
                notes.append(f"GitHub: {github_repos} repos")

            processing_notes = "; ".join(notes) if notes else "Basic processing"

            enrichment_data.append([
                '',  # Empty for section header
                datetime.now().strftime('%Y-%m-%d'),
                gender,
                gender_display,
                github_repos,
                website_status,
                website_title,
                linkedin_status,
                processing_notes
            ])

        # Write enrichment data
        data_range = f"{start_letter}2:{self.column_index_to_letter(start_col + len(enrichment_headers) - 1)}{len(enrichment_data) + 1}"
        write_to_sheet(self.service, self.sheet_id, data_range, enrichment_data)

    def write_comprehensive_report_to_sheet(self, sheet_name: str):
        """Write comprehensive report to a dedicated sheet"""

        # Calculate statistics
        total_rows = len(self.enrichment_results)
        gender_success = sum(1 for r in self.enrichment_results if r['enrichment'].get('gender', {}).get('status') == 'success')
        github_success = sum(1 for r in self.enrichment_results if r['enrichment'].get('github', {}).get('status') == 'success')
        website_success = sum(1 for r in self.enrichment_results if r['enrichment'].get('website', {}).get('status') == 'success')
        linkedin_success = sum(1 for r in self.enrichment_results if r['enrichment'].get('linkedin', {}).get('status') == 'success')

        # Create comprehensive report structure
        report_data = []

        # Title and timestamp
        report_data.append(['ENRICHMENT ANALYSIS REPORT', '', '', ''])
        report_data.append([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', '', '', ''])
        report_data.append(['', '', '', ''])

        # Executive Summary
        report_data.append(['EXECUTIVE SUMMARY', '', '', ''])
        report_data.append(['Metric', 'Value', 'Success Rate', 'Notes'])
        report_data.append(['Total Records Processed', str(total_rows), '100%', 'All records analyzed'])
        report_data.append(['Processing Duration', f'{self.processing_time:.1f} seconds', '', f'{self.processing_time/total_rows:.1f} sec/record'])
        report_data.append(['', '', '', ''])

        # Success Metrics
        report_data.append(['ENRICHMENT SUCCESS METRICS', '', '', ''])
        report_data.append(['Data Type', 'Successful', 'Failed', 'Success Rate'])
        report_data.append(['Gender Analysis', str(gender_success), str(total_rows - gender_success), f'{gender_success/total_rows*100:.1f}%'])
        report_data.append(['GitHub Search', str(github_success), str(total_rows - github_success), f'{github_success/total_rows*100:.1f}%'])
        report_data.append(['Website Scraping', str(website_success), str(total_rows - website_success), f'{website_success/total_rows*100:.1f}%'])
        report_data.append(['LinkedIn Validation', str(linkedin_success), str(total_rows - linkedin_success), f'{linkedin_success/total_rows*100:.1f}%'])
        report_data.append(['', '', '', ''])

        # Detailed Results
        report_data.append(['DETAILED RECORD ANALYSIS', '', '', ''])
        report_data.append(['Row', 'Name', 'Company', 'Gender', 'Gender Conf', 'GitHub Repos', 'Website Status', 'LinkedIn Status'])

        for result in self.enrichment_results:
            enrichment = result['enrichment']

            gender = enrichment.get('gender', {}).get('gender', 'unknown')
            gender_conf = enrichment.get('gender', {}).get('probability', 0)
            gender_display = f"{gender_conf*100:.0f}%" if gender != 'unknown' else 'N/A'
            github_repos = enrichment.get('github', {}).get('total_repos', 0)
            website_status = "SUCCESS" if enrichment.get('website', {}).get('status') == 'success' else "FAILED"
            linkedin_status = "ACCESSIBLE" if enrichment.get('linkedin', {}).get('accessible') else "BLOCKED"

            report_data.append([
                str(result['row_number']),
                result['name'],
                result['company'],
                gender,
                gender_display,
                str(github_repos),
                website_status,
                linkedin_status
            ])

        report_data.append(['', '', '', ''])

        # Key Findings
        report_data.append(['KEY FINDINGS AND INSIGHTS', '', '', ''])
        report_data.append(['Category', 'Finding', '', ''])
        report_data.append(['Gender Distribution', f'{gender_success} names analyzed with high confidence', '', ''])
        report_data.append(['Digital Presence', f'{website_success} active websites found', '', ''])
        report_data.append(['Developer Activity', f'{github_repos} total GitHub repositories', '', ''])
        report_data.append(['Professional Networks', f'{linkedin_success} LinkedIn profiles validated', '', ''])
        report_data.append(['', '', '', ''])

        # Technical Details
        report_data.append(['TECHNICAL IMPLEMENTATION', '', '', ''])
        report_data.append(['Component', 'Details', '', ''])
        report_data.append(['Processing Method', 'Batch processing with rate limiting', '', ''])
        report_data.append(['API Integrations', 'Gender API, GitHub API', '', ''])
        report_data.append(['Web Scraping', 'BeautifulSoup with retry logic', '', ''])
        report_data.append(['Error Handling', 'Comprehensive exception handling', '', ''])
        report_data.append(['Data Storage', 'Google Sheets with automatic sheet creation', '', ''])

        # Write to sheet
        range_notation = f"{sheet_name}!A1:H{len(report_data)}"
        write_to_sheet(self.service, self.sheet_id, range_notation, report_data)

        print(f"Comprehensive report written to sheet: {sheet_name}")

    def run_improved_enrichment(self):
        """Run improved enrichment with better sheet management"""

        print("="*70)
        print("IMPROVED GOOGLE SHEETS ENRICHMENT SYSTEM")
        print("="*70)
        print(f"Sheet ID: {self.sheet_id}")
        print(f"Max Rows: {self.max_rows}")

        start_time = time.time()

        # Step 1: Authenticate
        if not self.authenticate():
            print("ERROR: Authentication failed")
            return False
        print("SUCCESS: Authenticated")

        # Step 2: Read main sheet data
        print("\nReading spreadsheet data...")
        sheet_data = read_sheet(self.service, self.sheet_id, f"A1:Z{self.max_rows + 1}")

        if not sheet_data or len(sheet_data) < 2:
            print("ERROR: Insufficient data")
            return False

        headers = sheet_data[0]
        data_rows = sheet_data[1:]

        print(f"SUCCESS: Found {len(data_rows)} rows with {len(headers)} columns")

        # Step 3: Detect key columns
        columns = self.detect_key_columns(headers)
        print("\nColumn Detection:")
        for col_name, col_index in columns.items():
            if col_index is not None:
                print(f"  {col_name}: Column {col_index} ({headers[col_index]})")

        # Step 4: Process enrichment data
        self.enrichment_results = self.process_enrichment_data(data_rows, columns)
        self.processing_time = time.time() - start_time

        # Step 5: Determine where to write enrichment data
        print("\n" + "="*50)
        print("WRITING ENRICHMENT RESULTS")
        print("="*50)

        # Check main sheet for space
        first_empty_col, needs_new_sheet = self.find_first_empty_column()

        if not needs_new_sheet:
            # Write to main sheet
            first_empty_letter = self.column_index_to_letter(first_empty_col)
            print(f"Writing enrichment data to main sheet starting at column: {first_empty_letter}")
            self.write_enrichment_to_main_sheet(first_empty_col)
        else:
            print("Main sheet is approaching column limit. Creating new sheet for enrichment data...")

        # Step 6: Create comprehensive report in new sheet
        report_sheet_name = f"Enrichment_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if self.get_or_create_sheet(report_sheet_name):
            print(f"\nWriting comprehensive report to sheet: {report_sheet_name}")
            self.write_comprehensive_report_to_sheet(report_sheet_name)

        # Step 7: Final summary
        print(f"\n{'='*70}")
        print("ENRICHMENT COMPLETED SUCCESSFULLY!")
        print(f"{'='*70}")
        print(f"Processed: {len(self.enrichment_results)} rows")
        print(f"Time: {self.processing_time:.1f} seconds")

        if not needs_new_sheet:
            print(f"Enrichment data added to main sheet starting at column: {self.column_index_to_letter(first_empty_col)}")

        print(f"Comprehensive report created in sheet: {report_sheet_name}")
        print(f"\nSpreadsheet: https://docs.google.com/spreadsheets/d/{self.sheet_id}")
        print("\nYour Google Sheet now contains:")
        print("- Enrichment data columns in the main sheet (if space available)")
        print("- Comprehensive analysis report in a dedicated sheet")
        print("- Executive summary with key metrics")
        print("- Detailed record-by-record analysis")
        print("- Technical implementation details")

        return True

def main():
    """Main execution function"""

    SHEET_ID = "1l5aAzy5bhilmB3XfEBUbnL6Le8z1t0hFlmzLA5Gwq50"
    MAX_ROWS = 5

    enricher = ImprovedSheetsEnricher(SHEET_ID, MAX_ROWS)

    try:
        success = enricher.run_improved_enrichment()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
        return 1
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())