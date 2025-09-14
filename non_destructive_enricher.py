#!/usr/bin/env python3
"""
Non-Destructive, Append-Only Google Sheets Enricher
Implements namespaced enrichment columns with row key matching
Version: 2.0
Schema: S-Append-1.0
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
import logging

sys.path.append(os.path.dirname(__file__))

from google_sheets_auth import authenticate_google_sheets
from data_enrichment import DataEnrichment
from enhanced_scraping_pipeline import EnhancedScrapingPipeline

# Constants
PROCESSOR_VERSION = "v2.0"
SCHEMA_VERSION = "S-Append-1.0"
ENRICH_PREFIX = "Enrich::"
MAX_COLUMNS = 60
COLUMN_SAFETY_MARGIN = 5
MAX_FIELD_LENGTH = 1000
MAX_REPORT_LENGTH = 20000
BATCH_SIZE = 50

# Required enrichment headers in order
REQUIRED_ENRICH_HEADERS = [
    f"{ENRICH_PREFIX}Row Key",  # Special: for row identification
    f"{ENRICH_PREFIX}Primary URL",
    f"{ENRICH_PREFIX}All URLs (|)",
    f"{ENRICH_PREFIX}Page Title",
    f"{ENRICH_PREFIX}Meta Description",
    f"{ENRICH_PREFIX}About / Summary",
    f"{ENRICH_PREFIX}Contacts (emails|phones)",
    f"{ENRICH_PREFIX}Social Profiles (|)",
    f"{ENRICH_PREFIX}Tech / Stack (|)",
    f"{ENRICH_PREFIX}Locations (|)",
    f"{ENRICH_PREFIX}Employees (approx.)",
    f"{ENRICH_PREFIX}Revenue (approx.)",
    f"{ENRICH_PREFIX}Industry / Tags (|)",
    f"{ENRICH_PREFIX}Key Findings (| bullets)",
    f"{ENRICH_PREFIX}Risks (|)",
    f"{ENRICH_PREFIX}Opportunities (|)",
    f"{ENRICH_PREFIX}Confidence (0-100)",
    f"{ENRICH_PREFIX}Final Report (Markdown)",
    f"{ENRICH_PREFIX}Source Count",
    f"{ENRICH_PREFIX}Scrape Status",
    f"{ENRICH_PREFIX}Enrichment Status",
    f"{ENRICH_PREFIX}Last Enriched At (UTC)",
    f"{ENRICH_PREFIX}Processor Version",
    f"{ENRICH_PREFIX}Schema Version",
    f"{ENRICH_PREFIX}Error (last run)",
    f"{ENRICH_PREFIX}Retry Count",
    f"{ENRICH_PREFIX}Runtime (ms)"
]

# Optional headers (can be skipped if space is tight)
OPTIONAL_ENRICH_HEADERS = [
    f"{ENRICH_PREFIX}Employees (approx.)",
    f"{ENRICH_PREFIX}Revenue (approx.)",
    f"{ENRICH_PREFIX}Locations (|)",
    f"{ENRICH_PREFIX}Industry / Tags (|)",
    f"{ENRICH_PREFIX}Tech / Stack (|)"
]

@dataclass
class EnrichmentResult:
    """Structured enrichment result"""
    primary_url: str = ""
    all_urls: List[str] = field(default_factory=list)
    page_title: str = ""
    meta_description: str = ""
    about_summary: str = ""
    contacts: Dict[str, List[str]] = field(default_factory=dict)
    social_profiles: List[str] = field(default_factory=list)
    tech_stack: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    employees_approx: str = ""
    revenue_approx: str = ""
    industry_tags: List[str] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    confidence: int = 0
    final_report: str = ""
    source_count: int = 0
    scrape_status: str = "EMPTY"
    enrichment_status: str = "FAILED"
    error: str = ""
    retry_count: int = 0
    runtime_ms: int = 0

class NonDestructiveEnricher:
    """Non-destructive, append-only Google Sheets enricher"""

    def __init__(self, sheet_id: str, dry_run: bool = False):
        self.sheet_id = sheet_id
        self.dry_run = dry_run
        self.service = None
        self.drive_service = None
        self.enricher = DataEnrichment()
        self.scraper = EnhancedScrapingPipeline()

        # Header mapping cache
        self.header_map = {}
        self.enrich_columns = {}
        self.total_columns = 0

        # CLI integration for progress tracking
        self.cli = None

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('non_destructive_enricher.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def authenticate(self) -> bool:
        """Authenticate with Google Sheets"""
        try:
            self.logger.info("Authenticating with Google Sheets API...")
            self.service = authenticate_google_sheets()
            return self.service is not None
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False

    def read_headers(self) -> Tuple[List[str], Dict[str, int]]:
        """Read existing headers and build mapping"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="1:1"
            ).execute()

            headers = result.get('values', [[]])[0] if result.get('values') else []
            header_map = {header: idx for idx, header in enumerate(headers)}

            self.logger.info(f"Found {len(headers)} existing headers")
            return headers, header_map

        except Exception as e:
            self.logger.error(f"Failed to read headers: {e}")
            return [], {}

    def ensure_enrichment_headers(self, existing_headers: List[str]) -> Dict[str, int]:
        """Ensure all enrichment headers exist, append missing ones"""
        current_headers = existing_headers.copy()
        enrich_columns = {}

        # Check total column count
        self.total_columns = len(current_headers)

        # Identify existing enrichment columns
        for idx, header in enumerate(current_headers):
            if header.startswith(ENRICH_PREFIX):
                enrich_columns[header] = idx

        # Determine which headers to add
        headers_to_add = []
        for header in REQUIRED_ENRICH_HEADERS:
            if header not in enrich_columns:
                # Check if we have space
                if self.total_columns + len(headers_to_add) >= MAX_COLUMNS - COLUMN_SAFETY_MARGIN:
                    if header in OPTIONAL_ENRICH_HEADERS:
                        self.logger.warning(f"Skipping optional header due to column limit: {header}")
                        continue
                    else:
                        self.logger.warning(f"Approaching column limit, adding required header: {header}")

                headers_to_add.append(header)

        if headers_to_add and not self.dry_run:
            # Append new headers to the sheet
            start_col = len(current_headers)
            end_col = start_col + len(headers_to_add) - 1

            range_name = f"{self._col_to_letter(start_col)}1:{self._col_to_letter(end_col)}1"

            self.logger.info(f"Adding {len(headers_to_add)} enrichment headers at {range_name}")

            body = {'values': [headers_to_add]}
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()

            # Update our mapping
            for idx, header in enumerate(headers_to_add):
                enrich_columns[header] = start_col + idx

        elif self.dry_run and headers_to_add:
            self.logger.info(f"[DRY RUN] Would add {len(headers_to_add)} headers: {headers_to_add}")
            # Simulate the mapping
            start_col = len(current_headers)
            for idx, header in enumerate(headers_to_add):
                enrich_columns[header] = start_col + idx

        self.enrich_columns = enrich_columns
        self.total_columns = len(current_headers) + len(headers_to_add)

        return enrich_columns

    def get_row_key(self, row_data: Dict[str, str], row_index: int) -> Optional[str]:
        """Generate or retrieve stable row key"""
        # Check if row key already exists
        if f"{ENRICH_PREFIX}Row Key" in row_data:
            existing_key = row_data[f"{ENRICH_PREFIX}Row Key"]
            if existing_key:
                return existing_key

        # Generate row key based on priority
        # 1. LinkedIn Profile URL
        for key in ['linkedin_url', 'LinkedIn URL', 'linkedin', 'LinkedIn Profile']:
            if key in row_data and row_data[key]:
                return f"linkedin:{row_data[key]}"

        # 2. Email
        for key in ['email', 'Email', 'email_address', 'Email Address']:
            if key in row_data and row_data[key]:
                return f"email:{row_data[key]}"

        # 3. Company Domain + Person Name
        company = None
        person = None

        for key in ['company', 'Company', 'organization', 'Organization', 'company_name']:
            if key in row_data and row_data[key]:
                company = row_data[key]
                break

        for key in ['name', 'Name', 'full_name', 'Full Name']:
            if key in row_data and row_data[key]:
                person = row_data[key]
                break

        if company and person:
            return f"compound:{company}:{person}"

        # 4. Fallback to row index (not ideal but necessary)
        self.logger.warning(f"No stable key found for row {row_index}, using index")
        return f"row:{row_index}"

    def find_row_by_key(self, row_key: str, sheet_data: List[List[str]],
                        headers: List[str]) -> Optional[int]:
        """Find row index by row key"""
        if f"{ENRICH_PREFIX}Row Key" not in headers:
            return None

        key_col_idx = headers.index(f"{ENRICH_PREFIX}Row Key")

        for idx, row in enumerate(sheet_data):
            if idx == 0:  # Skip header row
                continue
            if len(row) > key_col_idx and row[key_col_idx] == row_key:
                return idx

        return None

    def process_row(self, row_data: Dict[str, str], row_index: int) -> EnrichmentResult:
        """Process a single row and generate enrichment data"""
        start_time = time.time()
        result = EnrichmentResult()

        try:
            # Extract URLs from row
            urls = []
            url_fields = ['website', 'Website', 'url', 'URL', 'company_website',
                         'organization_website_url', 'linkedin_url', 'LinkedIn URL']

            for field in url_fields:
                if field in row_data and row_data[field]:
                    url = row_data[field].strip()
                    if url.startswith(('http://', 'https://')):
                        urls.append(url)

            result.all_urls = list(set(urls))  # Deduplicate
            result.primary_url = urls[0] if urls else ""

            # Scrape primary URL if available
            if result.primary_url:
                self.logger.info(f"Scraping {result.primary_url}")
                scraped = self.scraper.scrape_url(result.primary_url)

                if scraped and scraped.get('status') == 'success':
                    result.scrape_status = "OK"
                    result.page_title = self._truncate(scraped.get('title', ''), MAX_FIELD_LENGTH)
                    result.meta_description = self._truncate(scraped.get('meta_description', ''), MAX_FIELD_LENGTH)

                    # Extract content summary
                    content = scraped.get('content', '')
                    result.about_summary = self._truncate(self._extract_summary(content), MAX_FIELD_LENGTH)

                    # Extract contacts
                    emails = scraped.get('emails', [])
                    phones = scraped.get('phones', [])
                    result.contacts = {'emails': emails[:10], 'phones': phones[:10]}

                    # Social profiles
                    result.social_profiles = scraped.get('social_links', [])[:20]

                    result.source_count += 1
                else:
                    result.scrape_status = "PARTIAL"

            # API Enrichment
            if 'email' in row_data and row_data['email']:
                email_result = self.enricher.verify_email_eva(row_data['email'])
                if email_result.get('status') == 'success':
                    result.key_findings.append(f"Email deliverable: {email_result.get('deliverable', 'unknown')}")
                    result.source_count += 1

            if 'name' in row_data and row_data['name']:
                first_name = row_data['name'].split()[0] if row_data['name'] else ""
                if first_name:
                    gender_result = self.enricher.get_gender(first_name)
                    if gender_result.get('status') == 'success':
                        gender = gender_result.get('gender', 'unknown')
                        probability = gender_result.get('probability', 0)
                        result.key_findings.append(f"Gender: {gender} ({int(probability*100)}% confidence)")
                        result.source_count += 1

            # Calculate confidence
            if result.source_count > 0:
                result.confidence = min(100, 30 + (result.source_count * 20))
                result.enrichment_status = "OK" if result.source_count >= 2 else "PARTIAL"
            else:
                result.enrichment_status = "FAILED"

            # Generate final report
            result.final_report = self._generate_report(row_data, result)

        except Exception as e:
            self.logger.error(f"Error processing row {row_index}: {e}")
            result.error = str(e)[:500]
            result.enrichment_status = "FAILED"

        # Calculate runtime
        result.runtime_ms = int((time.time() - start_time) * 1000)

        return result

    def map_result_to_columns(self, result: EnrichmentResult) -> Dict[str, str]:
        """Map enrichment result to column values"""

        # Format contacts
        contacts_str = ""
        if result.contacts:
            emails = "|".join(result.contacts.get('emails', []))
            phones = "|".join(result.contacts.get('phones', []))
            contacts_str = f"{emails}|{phones}" if emails or phones else ""

        mapped = {
            f"{ENRICH_PREFIX}Primary URL": result.primary_url,
            f"{ENRICH_PREFIX}All URLs (|)": "|".join(result.all_urls),
            f"{ENRICH_PREFIX}Page Title": result.page_title,
            f"{ENRICH_PREFIX}Meta Description": result.meta_description,
            f"{ENRICH_PREFIX}About / Summary": result.about_summary,
            f"{ENRICH_PREFIX}Contacts (emails|phones)": contacts_str,
            f"{ENRICH_PREFIX}Social Profiles (|)": "|".join(result.social_profiles),
            f"{ENRICH_PREFIX}Tech / Stack (|)": "|".join(result.tech_stack),
            f"{ENRICH_PREFIX}Locations (|)": "|".join(result.locations),
            f"{ENRICH_PREFIX}Employees (approx.)": result.employees_approx,
            f"{ENRICH_PREFIX}Revenue (approx.)": result.revenue_approx,
            f"{ENRICH_PREFIX}Industry / Tags (|)": "|".join(result.industry_tags),
            f"{ENRICH_PREFIX}Key Findings (| bullets)": "|".join(result.key_findings),
            f"{ENRICH_PREFIX}Risks (|)": "|".join(result.risks),
            f"{ENRICH_PREFIX}Opportunities (|)": "|".join(result.opportunities),
            f"{ENRICH_PREFIX}Confidence (0-100)": str(result.confidence),
            f"{ENRICH_PREFIX}Final Report (Markdown)": self._truncate(result.final_report, MAX_REPORT_LENGTH),
            f"{ENRICH_PREFIX}Source Count": str(result.source_count),
            f"{ENRICH_PREFIX}Scrape Status": result.scrape_status,
            f"{ENRICH_PREFIX}Enrichment Status": result.enrichment_status,
            f"{ENRICH_PREFIX}Last Enriched At (UTC)": datetime.now(timezone.utc).isoformat(),
            f"{ENRICH_PREFIX}Processor Version": PROCESSOR_VERSION,
            f"{ENRICH_PREFIX}Schema Version": SCHEMA_VERSION,
            f"{ENRICH_PREFIX}Error (last run)": result.error,
            f"{ENRICH_PREFIX}Retry Count": str(result.retry_count),
            f"{ENRICH_PREFIX}Runtime (ms)": str(result.runtime_ms)
        }

        # Normalize whitespace
        for key, value in mapped.items():
            if value:
                mapped[key] = " ".join(value.split())

        return mapped

    def write_enrichment_data(self, row_index: int, row_key: str,
                              enrichment_data: Dict[str, str]) -> bool:
        """Write enrichment data to specific row"""
        try:
            # Build batch update request
            requests = []

            # First, ensure row key is written
            if f"{ENRICH_PREFIX}Row Key" in self.enrich_columns:
                key_col = self.enrich_columns[f"{ENRICH_PREFIX}Row Key"]
                range_name = f"{self._col_to_letter(key_col)}{row_index + 1}"

                requests.append({
                    'range': range_name,
                    'values': [[row_key]]
                })

            # Write all enrichment data
            for header, value in enrichment_data.items():
                if header in self.enrich_columns:
                    col_idx = self.enrich_columns[header]
                    range_name = f"{self._col_to_letter(col_idx)}{row_index + 1}"

                    requests.append({
                        'range': range_name,
                        'values': [[value]]
                    })

            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would write to row {row_index + 1}:")
                for req in requests[:5]:  # Show first 5 for brevity
                    self.logger.info(f"  {req['range']}: {req['values'][0][0][:100]}")
                return True

            # Execute batch update
            if requests:
                body = {
                    'valueInputOption': 'RAW',
                    'data': requests
                }

                result = self.service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body=body
                ).execute()

                self.logger.info(f"Updated {result.get('totalUpdatedCells', 0)} cells in row {row_index + 1}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to write enrichment data: {e}")
            return False

        return True

    def process_sheet(self, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """Process entire sheet with enrichment and progress tracking"""
        start_time = time.time()
        stats = {
            'rows_attempted': 0,
            'rows_updated': 0,
            'rows_skipped': 0,
            'ok': 0,
            'partial': 0,
            'failed': 0,
            'errors': [],
            'elapsed_seconds': 0
        }

        try:
            # Read existing headers
            headers, header_map = self.read_headers()
            if not headers:
                raise ValueError("Failed to read sheet headers")

            # Ensure enrichment headers exist
            self.ensure_enrichment_headers(headers)

            # Read all data
            range_name = "A:ZZ" if not max_rows else f"A1:ZZ{max_rows + 1}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()

            sheet_data = result.get('values', [])
            if len(sheet_data) <= 1:
                self.logger.warning("No data rows found")
                return stats

            # Update headers with enrichment columns
            if self.enrich_columns:
                headers = sheet_data[0]

            # Process each data row
            for idx in range(1, min(len(sheet_data), max_rows + 1 if max_rows else len(sheet_data))):
                row = sheet_data[idx]
                stats['rows_attempted'] += 1

                # Convert row to dict
                row_dict = {}
                for col_idx, value in enumerate(row):
                    if col_idx < len(headers):
                        row_dict[headers[col_idx]] = value

                # Get person/company name for progress display
                person_name = self._get_display_name(row_dict)

                # Update CLI progress - processing state
                if self.cli:
                    self.cli.update_progress(
                        idx, person_name, "processing",
                        f"Extracting URLs and data..."
                    )

                # Get or generate row key
                row_key = self.get_row_key(row_dict, idx)

                self.logger.info(f"Processing row {idx} ({person_name}) with key: {row_key}")

                try:
                    # Process the row
                    enrichment_result = self.process_row(row_dict, idx)

                    # Map to columns
                    column_data = self.map_result_to_columns(enrichment_result)

                    # Write enrichment data
                    if self.write_enrichment_data(idx, row_key, column_data):
                        stats['rows_updated'] += 1
                        status = enrichment_result.enrichment_status.lower()
                        stats[status] = stats.get(status, 0) + 1

                        # Update CLI progress - success
                        if self.cli:
                            details = f"{enrichment_result.source_count} sources, {enrichment_result.confidence}% confidence"
                            self.cli.update_progress(idx, person_name, status, details)

                    else:
                        stats['rows_skipped'] += 1
                        stats['failed'] += 1

                        # Update CLI progress - failed
                        if self.cli:
                            self.cli.update_progress(idx, person_name, "failed", "Write failed")

                except Exception as row_error:
                    self.logger.error(f"Row {idx} processing failed: {row_error}")
                    stats['rows_skipped'] += 1
                    stats['failed'] += 1
                    stats['errors'].append(f"Row {idx}: {str(row_error)}")

                    # Update CLI progress - error
                    if self.cli:
                        self.cli.update_progress(idx, person_name, "failed", f"Error: {str(row_error)[:50]}")

                # Rate limiting
                if not self.dry_run:
                    time.sleep(self.scraper.get_request_delay("default"))

        except Exception as e:
            self.logger.error(f"Sheet processing failed: {e}")
            stats['errors'].append(str(e))

        stats['elapsed_seconds'] = time.time() - start_time

        # Print summary to logger
        self.logger.info("="*60)
        self.logger.info("PROCESSING SUMMARY")
        self.logger.info(f"Rows attempted: {stats['rows_attempted']}")
        self.logger.info(f"Rows updated: {stats['rows_updated']}")
        self.logger.info(f"Rows skipped: {stats['rows_skipped']}")
        self.logger.info(f"Success rate: OK={stats.get('ok', 0)}, Partial={stats.get('partial', 0)}, Failed={stats.get('failed', 0)}")
        self.logger.info(f"Elapsed time: {stats['elapsed_seconds']:.1f} seconds")
        if stats['errors']:
            self.logger.info(f"Errors: {len(stats['errors'])}")

        return stats

    def _get_display_name(self, row_dict: Dict[str, str]) -> str:
        """Extract display name from row for progress tracking"""
        # Try various name fields
        name_fields = ['name', 'Name', 'full_name', 'Full Name', 'first_name', 'First Name']
        for field in name_fields:
            if field in row_dict and row_dict[field]:
                return row_dict[field][:30]  # Truncate for display

        # Try company/organization
        org_fields = ['company', 'Company', 'organization', 'Organization', 'organization_name']
        for field in org_fields:
            if field in row_dict and row_dict[field]:
                return f"({row_dict[field][:25]})"  # Parentheses for company

        return f"Row data"

    def _col_to_letter(self, col_index: int) -> str:
        """Convert column index to letter (0=A, 25=Z, 26=AA)"""
        result = ""
        while col_index >= 0:
            result = chr(65 + (col_index % 26)) + result
            col_index = col_index // 26 - 1
        return result

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis"""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length - 12] + "... [truncated]"

    def _extract_summary(self, content: str) -> str:
        """Extract summary from content"""
        if not content:
            return ""

        # Take first 500 chars of actual content
        lines = content.split('\n')
        summary_lines = []
        total_length = 0

        for line in lines:
            line = line.strip()
            if line and not line.startswith(('<', '{')):  # Skip HTML/JSON
                if total_length + len(line) > 500:
                    break
                summary_lines.append(line)
                total_length += len(line)

        return " ".join(summary_lines)

    def _generate_report(self, row_data: Dict[str, str], result: EnrichmentResult) -> str:
        """Generate markdown report"""
        report = []

        # Header
        name = row_data.get('name', row_data.get('Name', 'Unknown'))
        company = row_data.get('company', row_data.get('organization', 'Unknown'))

        report.append(f"# Intelligence Report: {name}")
        report.append(f"**Organization:** {company}")
        report.append("")

        # Key Information
        if result.page_title:
            report.append(f"**Page Title:** {result.page_title}")

        if result.about_summary:
            report.append(f"**Summary:** {result.about_summary}")

        # Findings
        if result.key_findings:
            report.append("\n## Key Findings")
            for finding in result.key_findings:
                report.append(f"- {finding}")

        # Confidence
        report.append(f"\n**Confidence Score:** {result.confidence}/100")
        report.append(f"**Sources Merged:** {result.source_count}")
        report.append(f"**Status:** {result.enrichment_status}")

        return "\n".join(report)


def main():
    """Main execution for testing"""
    import argparse

    parser = argparse.ArgumentParser(description='Non-Destructive Google Sheets Enricher')
    parser.add_argument('--sheet-id', required=True, help='Google Sheet ID')
    parser.add_argument('--max-rows', type=int, default=5, help='Maximum rows to process')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    args = parser.parse_args()

    enricher = NonDestructiveEnricher(args.sheet_id, dry_run=args.dry_run)

    if not enricher.authenticate():
        print("Authentication failed")
        return

    stats = enricher.process_sheet(max_rows=args.max_rows)
    print(f"\nProcessing complete: {stats}")


if __name__ == "__main__":
    main()