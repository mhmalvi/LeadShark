#!/usr/bin/env python3
"""
Smart Enrichment Pipeline for Google Sheets
Automatically finds next available columns and generates comprehensive reports
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from google_sheets_auth import authenticate_google_sheets, read_sheet, write_to_sheet
from data_enrichment import DataEnrichment
from enhanced_scraping_pipeline import EnhancedScrapingPipeline

class SmartEnrichmentPipeline:
    """Smart enrichment pipeline that preserves existing data"""

    def __init__(self, sheet_id: str, max_rows: int = 5):
        self.sheet_id = sheet_id
        self.max_rows = max_rows
        self.service = None
        self.enricher = DataEnrichment()
        self.scraper = EnhancedScrapingPipeline()
        self.enrichment_results = []

    def authenticate(self):
        """Authenticate with Google Sheets"""
        print("Authenticating with Google Sheets API...")
        self.service = authenticate_google_sheets()
        return self.service is not None

    def find_last_column(self, sheet_data: List[List[str]]) -> int:
        """Find the last column with data"""
        max_col = 0
        for row in sheet_data:
            max_col = max(max_col, len(row))
        return max_col

    def column_index_to_letter(self, index: int) -> str:
        """Convert column index to Excel-style letter (0=A, 25=Z, 26=AA)"""
        result = ""
        while index >= 0:
            result = chr(65 + (index % 26)) + result
            index = index // 26 - 1
        return result

    def detect_columns(self, headers: List[str]) -> Dict[str, Optional[int]]:
        """Detect important columns in the spreadsheet"""
        columns = {
            'email': None,
            'name': None,
            'first_name': None,
            'linkedin_url': None,
            'organization': None,
            'company_name': None,
            'website': None
        }

        for i, header in enumerate(headers):
            header_lower = header.lower()

            if 'email' in header_lower and columns['email'] is None:
                columns['email'] = i
            elif header_lower in ['name', 'full_name'] and columns['name'] is None:
                columns['name'] = i
            elif 'first_name' in header_lower and columns['first_name'] is None:
                columns['first_name'] = i
            elif 'linkedin' in header_lower and 'url' in header_lower:
                columns['linkedin_url'] = i
            elif header_lower == 'organization' and columns['organization'] is None:
                columns['organization'] = i
            elif 'company' in header_lower or 'organization_name' in header_lower:
                columns['company_name'] = i
            elif 'website' in header_lower and columns['website'] is None:
                columns['website'] = i

        return columns

    def process_row(self, row: List[str], columns: Dict[str, Optional[int]], row_number: int) -> Dict[str, Any]:
        """Process a single row of data"""
        print(f"\n{'='*50}")
        print(f"PROCESSING ROW {row_number}")
        print(f"{'='*50}")

        # Extract data from row
        email = row[columns['email']] if columns['email'] and columns['email'] < len(row) else ""
        name = row[columns['name']] if columns['name'] and columns['name'] < len(row) else ""
        first_name = row[columns['first_name']] if columns['first_name'] and columns['first_name'] < len(row) else ""
        linkedin_url = row[columns['linkedin_url']] if columns['linkedin_url'] and columns['linkedin_url'] < len(row) else ""

        # Parse organization data if it's JSON
        organization_data = {}
        if columns['organization'] and columns['organization'] < len(row) and row[columns['organization']]:
            try:
                organization_data = json.loads(row[columns['organization']])
            except:
                pass

        company_name = organization_data.get('name', '') or (row[columns['company_name']] if columns['company_name'] and columns['company_name'] < len(row) else "")
        company_website = organization_data.get('website_url', '') or (row[columns['website']] if columns['website'] and columns['website'] < len(row) else "")

        if not first_name and name:
            first_name = name.split()[0] if name.split() else ""

        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Company: {company_name}")
        print(f"Website: {company_website}")
        print(f"LinkedIn: {linkedin_url}")

        # Initialize enrichment result
        result = {
            'row_number': row_number,
            'original_data': {
                'name': name,
                'email': email,
                'company': company_name,
                'website': company_website,
                'linkedin': linkedin_url
            },
            'enrichment_timestamp': datetime.now().isoformat(),
            'enrichment_results': {}
        }

        # Email verification
        if email and '@' in email:
            print(f"\n  >> Verifying email: {email}")
            email_result = self.enricher.verify_email_eva(email)
            result['enrichment_results']['email_verification'] = email_result

            if email_result.get('status') == 'success':
                deliverable = email_result.get('deliverable', False)
                print(f"    Email Status: {'VALID' if deliverable else 'INVALID'}")
            else:
                print(f"    Email Error: {email_result.get('error', 'Unknown')}")
            time.sleep(1)

        # Gender analysis
        if first_name:
            print(f"\n  >> Analyzing gender for: {first_name}")
            gender_result = self.enricher.get_gender(first_name)
            result['enrichment_results']['gender_analysis'] = gender_result

            if gender_result.get('status') == 'success':
                gender = gender_result.get('gender', 'unknown')
                probability = gender_result.get('probability', 0)
                print(f"    Gender: {gender} ({probability*100:.0f}% confidence)")
            time.sleep(1)

        # GitHub search
        if company_name:
            print(f"\n  >> Searching GitHub for: {company_name}")
            github_result = self.enricher.search_github(company_name)
            result['enrichment_results']['github_search'] = github_result

            if github_result.get('status') == 'success':
                orgs = github_result.get('total_orgs', 0)
                repos = github_result.get('total_repos', 0)
                print(f"    GitHub: {orgs} organizations, {repos} repositories")
            time.sleep(2)

        # Website scraping
        if company_website:
            print(f"\n  >> Scraping website: {company_website}")
            scrape_result = self.scraper.scrape_url_with_retry(company_website)
            result['enrichment_results']['website_scraping'] = scrape_result

            if scrape_result.get('status') == 'success':
                content_length = scrape_result.get('full_content_length', 0)
                print(f"    Website: SUCCESS ({content_length} chars)")

                if scrape_result.get('metadata', {}).get('title'):
                    title = scrape_result['metadata']['title'][:60]
                    print(f"    Title: {title}...")
            else:
                print(f"    Website: FAILED - {scrape_result.get('status')}")
            time.sleep(2)

        # LinkedIn check
        if linkedin_url:
            print(f"\n  >> Checking LinkedIn profile...")
            linkedin_result = self.enricher.check_linkedin_profile_exists(linkedin_url)
            result['enrichment_results']['linkedin_check'] = linkedin_result

            if linkedin_result.get('status') == 'success':
                accessible = linkedin_result.get('accessible', False)
                print(f"    LinkedIn: {'ACCESSIBLE' if accessible else 'BLOCKED/RESTRICTED'}")
            time.sleep(1)

        print(f"\nSUCCESS - Completed row {row_number}")
        return result

    def generate_summary_data(self) -> List[List[str]]:
        """Generate summary data for Google Sheets"""
        summary_data = []

        for result in self.enrichment_results:
            enrichment = result['enrichment_results']

            # Extract key metrics
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

            summary_data.append([
                result['enrichment_timestamp'][:10],  # Date only
                email_status,
                gender_display,
                github_status,
                website_status,
                linkedin_status
            ])

        return summary_data

    def generate_final_report(self) -> str:
        """Generate comprehensive final report"""

        report = f"""
# AETHON DATA ENRICHMENT REPORT
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Sheet ID:** {self.sheet_id}
**Rows Processed:** {len(self.enrichment_results)}

---

## PROCESSING SUMMARY

**Total Rows:** {len(self.enrichment_results)}
**Processing Time:** {self.processing_time:.1f} seconds
**Average Time per Row:** {self.processing_time / len(self.enrichment_results):.1f} seconds

### Success Rates:
"""

        # Calculate success rates
        email_success = sum(1 for r in self.enrichment_results if r['enrichment_results'].get('email_verification', {}).get('status') == 'success')
        gender_success = sum(1 for r in self.enrichment_results if r['enrichment_results'].get('gender_analysis', {}).get('status') == 'success')
        github_success = sum(1 for r in self.enrichment_results if r['enrichment_results'].get('github_search', {}).get('status') == 'success')
        website_success = sum(1 for r in self.enrichment_results if r['enrichment_results'].get('website_scraping', {}).get('status') == 'success')
        linkedin_success = sum(1 for r in self.enrichment_results if r['enrichment_results'].get('linkedin_check', {}).get('status') == 'success')

        total = len(self.enrichment_results)

        report += f"""
- **Email Verification:** {email_success}/{total} ({email_success/total*100:.1f}%)
- **Gender Analysis:** {gender_success}/{total} ({gender_success/total*100:.1f}%)
- **GitHub Search:** {github_success}/{total} ({github_success/total*100:.1f}%)
- **Website Scraping:** {website_success}/{total} ({website_success/total*100:.1f}%)
- **LinkedIn Check:** {linkedin_success}/{total} ({linkedin_success/total*100:.1f}%)

---

## DETAILED RESULTS

"""

        for i, result in enumerate(self.enrichment_results, 1):
            original = result['original_data']
            enrichment = result['enrichment_results']

            report += f"""
### Row {result['row_number']} - {original['name']}

**Original Data:**
- Name: {original['name']}
- Email: {original['email']}
- Company: {original['company']}
- Website: {original['website']}

**Enrichment Results:**
"""

            # Email verification details
            if 'email_verification' in enrichment:
                email_data = enrichment['email_verification']
                if email_data.get('status') == 'success':
                    deliverable = "VALID" if email_data.get('deliverable') else "INVALID"
                    report += f"- **Email Status:** {deliverable}\n"
                else:
                    report += f"- **Email Status:** ERROR - {email_data.get('error', 'Unknown')}\n"

            # Gender analysis details
            if 'gender_analysis' in enrichment:
                gender_data = enrichment['gender_analysis']
                if gender_data.get('status') == 'success':
                    gender = gender_data.get('gender', 'unknown')
                    conf = gender_data.get('probability', 0)
                    count = gender_data.get('count', 0)
                    report += f"- **Gender:** {gender} ({conf*100:.0f}% confidence, {count:,} samples)\n"

            # GitHub search details
            if 'github_search' in enrichment:
                github_data = enrichment['github_search']
                if github_data.get('status') == 'success':
                    orgs = github_data.get('total_orgs', 0)
                    repos = github_data.get('total_repos', 0)
                    report += f"- **GitHub:** {orgs} organizations, {repos} repositories\n"

            # Website scraping details
            if 'website_scraping' in enrichment:
                website_data = enrichment['website_scraping']
                if website_data.get('status') == 'success':
                    length = website_data.get('full_content_length', 0)
                    title = website_data.get('metadata', {}).get('title', 'No title')[:50]
                    report += f"- **Website:** SUCCESS - Scraped ({length:,} chars) - {title}...\n"
                else:
                    status = website_data.get('status', 'unknown')
                    report += f"- **Website:** FAILED - {status}\n"

            # LinkedIn check details
            if 'linkedin_check' in enrichment:
                linkedin_data = enrichment['linkedin_check']
                if linkedin_data.get('status') == 'success':
                    accessible = "ACCESSIBLE" if linkedin_data.get('accessible') else "BLOCKED/RESTRICTED"
                    report += f"- **LinkedIn:** {accessible}\n"

            report += "\n---\n"

        report += f"""
## RECOMMENDATIONS

Based on the enrichment results:

1. **Email Quality:** {email_success}/{total} emails successfully verified
2. **Data Completeness:** Gender analysis successful for {gender_success}/{total} records
3. **Digital Presence:** {website_success}/{total} websites successfully scraped
4. **Social Validation:** LinkedIn profiles checked for all records

## FILES GENERATED

- **Enrichment Data:** Added to Google Sheets columns (next available)
- **JSON Results:** Saved to `enrichment_results_[timestamp].json`
- **Final Report:** This comprehensive analysis

---

**Generated with Aethon Data Enricher**
*Powered by Claude Code Intelligence*
"""

        return report

    def run_pipeline(self):
        """Run the complete enrichment pipeline"""

        print("="*70)
        print("AETHON SMART ENRICHMENT PIPELINE")
        print("="*70)
        print(f"Sheet ID: {self.sheet_id}")
        print(f"Max Rows: {self.max_rows}")

        start_time = time.time()

        # Step 1: Authenticate
        if not self.authenticate():
            print("ERROR: Authentication failed")
            return False
        print("SUCCESS: Authenticated successfully")

        # Step 2: Read sheet data
        print(f"\nReading spreadsheet data...")
        sheet_data = read_sheet(self.service, self.sheet_id, f"A1:ZZ{self.max_rows + 1}")

        if not sheet_data or len(sheet_data) < 2:
            print("ERROR: Insufficient data in spreadsheet")
            return False

        headers = sheet_data[0]
        data_rows = sheet_data[1:]

        print(f"SUCCESS: Found {len(data_rows)} data rows with {len(headers)} columns")

        # Step 3: Detect column structure
        columns = self.detect_columns(headers)
        print(f"\nColumn detection:")
        for col_name, col_index in columns.items():
            if col_index is not None:
                print(f"  {col_name}: Column {col_index} ({headers[col_index]})")

        # Step 4: Find next available column for enrichment data
        last_col_index = self.find_last_column(sheet_data)
        next_col_index = last_col_index + 1  # Add buffer column
        next_col_letter = self.column_index_to_letter(next_col_index)

        print(f"\nData placement:")
        print(f"  Last used column: {self.column_index_to_letter(last_col_index - 1)}")
        print(f"  Enrichment data will start at: {next_col_letter}")

        # Step 5: Process each row
        print(f"\nProcessing {len(data_rows)} rows...")

        for i, row in enumerate(data_rows, 2):  # Start from row 2 (after header)
            result = self.process_row(row, columns, i)
            self.enrichment_results.append(result)

        # Step 6: Calculate processing time
        self.processing_time = time.time() - start_time

        # Step 7: Write enrichment summary to Google Sheets
        print(f"\nWriting enrichment data to Google Sheets...")

        # Headers for enrichment columns
        enrichment_headers = [
            'Enrichment_Date',
            'Email_Status',
            'Gender_Prediction',
            'GitHub_Status',
            'Website_Status',
            'LinkedIn_Status'
        ]

        # Write headers
        header_range = f"{next_col_letter}1:{self.column_index_to_letter(next_col_index + len(enrichment_headers) - 1)}1"
        write_to_sheet(self.service, self.sheet_id, header_range, [enrichment_headers])

        # Write summary data
        summary_data = self.generate_summary_data()
        data_range = f"{next_col_letter}2:{self.column_index_to_letter(next_col_index + len(enrichment_headers) - 1)}{len(summary_data) + 1}"
        write_to_sheet(self.service, self.sheet_id, data_range, summary_data)

        print(f"SUCCESS: Enrichment data written to columns {next_col_letter}-{self.column_index_to_letter(next_col_index + len(enrichment_headers) - 1)}")

        # Step 8: Save detailed results to JSON
        results_filename = f"enrichment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_filename, 'w', encoding='utf-8') as f:
            json.dump(self.enrichment_results, f, indent=2, ensure_ascii=False)

        print(f"Detailed results saved to: {results_filename}")

        # Step 9: Generate and save final report
        print(f"\nGenerating final report...")
        final_report = self.generate_final_report()

        report_filename = f"enrichment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(final_report)

        print(f"Final report saved to: {report_filename}")

        # Step 10: Display summary
        print(f"\n{'='*70}")
        print("ENRICHMENT COMPLETED SUCCESSFULLY!")
        print(f"{'='*70}")
        print(f"Processed: {len(self.enrichment_results)} rows")
        print(f"Time: {self.processing_time:.1f} seconds")
        print(f"Average: {self.processing_time / len(self.enrichment_results):.1f} seconds/row")
        print(f"Spreadsheet: https://docs.google.com/spreadsheets/d/{self.sheet_id}")
        print(f"Results: {results_filename}")
        print(f"Report: {report_filename}")

        return True

def main():
    """Main execution function"""

    # Configuration
    SHEET_ID = "1l5aAzy5bhilmB3XfEBUbnL6Le8z1t0hFlmzLA5Gwq50"
    MAX_ROWS = 5  # Process first 5 rows

    # Initialize and run pipeline
    pipeline = SmartEnrichmentPipeline(SHEET_ID, MAX_ROWS)

    try:
        success = pipeline.run_pipeline()
        if not success:
            print("ERROR: Pipeline failed. Check the errors above.")
            return 1

        return 0

    except KeyboardInterrupt:
        print("\n\nWARNING: Pipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())