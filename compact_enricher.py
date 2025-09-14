#!/usr/bin/env python3
"""
Compact Google Sheets Enricher
Uses only 4-5 enrichment columns to handle column limit constraints
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import logging

sys.path.append(os.path.dirname(__file__))

from google_sheets_auth import authenticate_google_sheets
from data_enrichment import DataEnrichment
from enhanced_scraping_pipeline import EnhancedScrapingPipeline

# Constants
PROCESSOR_VERSION = "v2.0-Compact"
SCHEMA_VERSION = "S-Compact-1.0"
ENRICH_PREFIX = "Enrich::"

# Compact enrichment headers (only 5 columns!)
COMPACT_ENRICH_HEADERS = [
    f"{ENRICH_PREFIX}Row Key",           # Stable identifier
    f"{ENRICH_PREFIX}Summary Report",    # Main intelligence (JSON/Markdown)
    f"{ENRICH_PREFIX}Key Data",          # Essential data (JSON)
    f"{ENRICH_PREFIX}Status & Meta",     # Status, confidence, timestamps (JSON)
    f"{ENRICH_PREFIX}URLs & Sources"     # All URLs and source count (JSON)
]


class CompactEnricher:
    """Compact enricher using only 5 columns for all enrichment data"""

    def __init__(self, sheet_id: str, dry_run: bool = False):
        self.sheet_id = sheet_id
        self.dry_run = dry_run
        self.service = None
        self.drive_service = None
        self.enricher = DataEnrichment()
        self.scraper = EnhancedScrapingPipeline()
        self.cli = None

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('compact_enricher.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def authenticate(self) -> bool:
        """Authenticate with Google Sheets"""
        try:
            self.logger.info("Authenticating with Google Sheets API...")
            result = authenticate_google_sheets()
            if result:
                self.service, self.drive_service, creds = result
                return True
            return False
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False

    def check_column_capacity(self, existing_headers: List[str]) -> Tuple[bool, int]:
        """Check if we have space for compact enrichment columns"""
        current_count = len(existing_headers)
        needed_columns = len(COMPACT_ENRICH_HEADERS)

        # Check existing enrichment columns
        existing_enrich = [h for h in existing_headers if h.startswith(ENRICH_PREFIX)]
        if existing_enrich:
            # We already have enrichment columns, just use them
            return True, current_count

        # Check if we can add new columns
        max_columns = 60  # Conservative Google Sheets limit
        available_space = max_columns - current_count

        if available_space >= needed_columns:
            return True, current_count + needed_columns
        else:
            return False, current_count

    def ensure_compact_headers(self, existing_headers: List[str]) -> Dict[str, int]:
        """Ensure compact enrichment headers exist"""
        enrich_columns = {}

        # Force use of specific columns AX through BB (0-indexed: 49-53) for compact enrichment
        # AX=49, AY=50, AZ=51, BA=52, BB=53
        target_columns = list(range(49, 54))  # Use exactly 5 columns for 5 headers

        # Map each header to its target column (ignore any existing headers elsewhere)
        for i, header in enumerate(COMPACT_ENRICH_HEADERS):
            if i < len(target_columns):
                enrich_columns[header] = target_columns[i]

        # Always set headers to ensure they're in the right place
        headers_to_set = COMPACT_ENRICH_HEADERS[:len(target_columns)]

        self.logger.info(f"Using columns AX-BB (indices {target_columns}) for compact enrichment")

        # Set headers in target columns AX-BB
        if headers_to_set:
            if not self.dry_run:
                # Set headers to specific columns
                for i, header in enumerate(headers_to_set):
                    col_idx = target_columns[i]
                    range_name = f"{self._col_to_letter(col_idx)}1"

                    try:
                        self.service.spreadsheets().values().update(
                            spreadsheetId=self.sheet_id,
                            range=range_name,
                            valueInputOption='RAW',
                            body={'values': [[header]]}
                        ).execute()

                        self.logger.info(f"Set column {self._col_to_letter(col_idx)} header to '{header}'")

                    except Exception as e:
                        self.logger.error(f"Failed to set header in column {self._col_to_letter(col_idx)}: {e}")
                        return {}

            else:
                # Dry run mode
                self.logger.info(f"[DRY RUN] Would set headers in columns AX-BB")

        return enrich_columns

    def process_row_compact(self, row_data: Dict[str, str], row_index: int) -> Dict[str, str]:
        """Process row and return compact enrichment data"""
        start_time = time.time()

        # Get display name
        person_name = self._get_display_name(row_data)

        if self.cli:
            self.cli.update_progress(row_index, person_name, "processing", "Extracting data...")

        # Generate row key
        row_key = self._get_row_key(row_data, row_index)

        # Extract URLs
        urls = self._extract_urls(row_data)
        primary_url = urls[0] if urls else ""

        # Initialize results
        enrichment_data = {
            'urls': urls,
            'scraped_content': {},
            'api_results': {},
            'confidence': 0,
            'source_count': 0,
            'status': 'FAILED'
        }

        try:
            # Scrape primary URL
            if primary_url:
                if self.cli:
                    self.cli.update_progress(row_index, person_name, "processing", f"Scraping {primary_url[:30]}...")

                scraped = self.scraper.scrape_url(primary_url)
                if scraped and scraped.get('status') == 'success':
                    enrichment_data['scraped_content'] = {
                        'title': scraped.get('title', ''),
                        'description': scraped.get('meta_description', ''),
                        'content_summary': scraped.get('content', '')[:500],
                        'emails': scraped.get('emails', [])[:5],
                        'phones': scraped.get('phones', [])[:3],
                        'social_links': scraped.get('social_links', [])[:5]
                    }
                    enrichment_data['source_count'] += 1

            # API enrichment
            if self.cli:
                self.cli.update_progress(row_index, person_name, "processing", "API enrichment...")

            # Email verification
            if 'email' in row_data and row_data['email']:
                email_result = self.enricher.verify_email_eva(row_data['email'])
                if email_result.get('status') == 'success':
                    enrichment_data['api_results']['email_verification'] = email_result
                    enrichment_data['source_count'] += 1

            # Gender detection
            first_name = self._extract_first_name(row_data)
            if first_name:
                gender_result = self.enricher.get_gender(first_name)
                if gender_result.get('status') == 'success':
                    enrichment_data['api_results']['gender'] = gender_result
                    enrichment_data['source_count'] += 1

            # Company search
            company = self._extract_company_name(row_data)
            if company:
                github_result = self.enricher.search_github(company)
                if github_result.get('status') == 'success':
                    enrichment_data['api_results']['github'] = {
                        'organizations': github_result.get('organizations', [])[:3],
                        'repositories': github_result.get('repositories', [])[:5],
                        'total_repos': github_result.get('total_repos', 0)
                    }
                    enrichment_data['source_count'] += 1

            # Calculate confidence and status
            if enrichment_data['source_count'] > 0:
                enrichment_data['confidence'] = min(100, 20 + (enrichment_data['source_count'] * 25))
                enrichment_data['status'] = 'OK' if enrichment_data['source_count'] >= 2 else 'PARTIAL'

        except Exception as e:
            self.logger.error(f"Row {row_index} processing error: {e}")
            enrichment_data['error'] = str(e)[:200]

        # Processing time
        runtime_ms = int((time.time() - start_time) * 1000)

        # Update progress
        if self.cli:
            status = enrichment_data['status'].lower()
            details = f"{enrichment_data['source_count']} sources, {enrichment_data['confidence']}% confidence"
            self.cli.update_progress(row_index, person_name, status, details)

        # Generate compact column data
        compact_data = self._generate_compact_data(row_key, enrichment_data, runtime_ms)

        return compact_data

    def _generate_compact_data(self, row_key: str, enrichment_data: Dict, runtime_ms: int) -> Dict[str, str]:
        """Generate compact enrichment data for 5 columns"""

        # Column 1: Row Key
        compact_data = {
            f"{ENRICH_PREFIX}Row Key": row_key
        }

        # Column 2: Summary Report (Markdown)
        summary_parts = []

        # Add title
        summary_parts.append("# Enrichment Summary")

        # Add scraped content summary
        if enrichment_data['scraped_content']:
            content = enrichment_data['scraped_content']
            if content.get('title'):
                summary_parts.append(f"**Title:** {content['title']}")
            if content.get('description'):
                summary_parts.append(f"**Description:** {content['description'][:200]}...")
            if content.get('content_summary'):
                summary_parts.append(f"**Summary:** {content['content_summary']}")

        # Add key findings
        findings = []
        api_results = enrichment_data.get('api_results', {})

        if 'email_verification' in api_results:
            status = "✅ Deliverable" if api_results['email_verification'].get('deliverable') else "❌ Not deliverable"
            findings.append(f"Email: {status}")

        if 'gender' in api_results:
            gender_data = api_results['gender']
            gender = gender_data.get('gender', 'unknown')
            prob = int((gender_data.get('probability', 0) * 100))
            findings.append(f"Gender: {gender} ({prob}% confidence)")

        if 'github' in api_results:
            github_data = api_results['github']
            repo_count = github_data.get('total_repos', 0)
            findings.append(f"GitHub: {repo_count} repositories found")

        if findings:
            summary_parts.append("## Key Findings")
            for finding in findings:
                summary_parts.append(f"- {finding}")

        # Add confidence and status
        summary_parts.append(f"\n**Confidence:** {enrichment_data['confidence']}%")
        summary_parts.append(f"**Status:** {enrichment_data['status']}")

        compact_data[f"{ENRICH_PREFIX}Summary Report"] = "\n".join(summary_parts)

        # Column 3: Key Data (JSON)
        key_data = {
            'scraped_content': enrichment_data['scraped_content'],
            'api_results': enrichment_data['api_results']
        }
        compact_data[f"{ENRICH_PREFIX}Key Data"] = json.dumps(key_data, separators=(',', ':'))

        # Column 4: Status & Meta (JSON)
        status_meta = {
            'status': enrichment_data['status'],
            'confidence': enrichment_data['confidence'],
            'source_count': enrichment_data['source_count'],
            'last_enriched': datetime.now(timezone.utc).isoformat(),
            'processor_version': PROCESSOR_VERSION,
            'schema_version': SCHEMA_VERSION,
            'runtime_ms': runtime_ms,
            'error': enrichment_data.get('error', '')
        }
        compact_data[f"{ENRICH_PREFIX}Status & Meta"] = json.dumps(status_meta, separators=(',', ':'))

        # Column 5: URLs & Sources (JSON)
        urls_sources = {
            'primary_url': enrichment_data['urls'][0] if enrichment_data['urls'] else '',
            'all_urls': enrichment_data['urls'],
            'source_count': enrichment_data['source_count']
        }
        compact_data[f"{ENRICH_PREFIX}URLs & Sources"] = json.dumps(urls_sources, separators=(',', ':'))

        return compact_data

    def process_sheet(self, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """Process sheet with compact enrichment"""
        start_time = time.time()
        stats = {
            'rows_attempted': 0,
            'rows_updated': 0,
            'ok': 0,
            'partial': 0,
            'failed': 0,
            'errors': []
        }

        try:
            # Read headers
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="1:1"
            ).execute()

            headers = result.get('values', [[]])[0] if result.get('values') else []
            self.logger.info(f"Found {len(headers)} existing columns")

            # Check capacity and ensure headers
            can_add, total_cols = self.check_column_capacity(headers)
            if not can_add:
                error_msg = f"Cannot add enrichment columns - sheet has {len(headers)} columns (limit ~60)"
                self.logger.error(error_msg)
                stats['errors'].append(error_msg)
                return stats

            enrich_columns = self.ensure_compact_headers(headers)
            if not enrich_columns:
                error_msg = "Failed to create enrichment columns"
                stats['errors'].append(error_msg)
                return stats

            self.logger.info(f"Using compact enrichment: {len(enrich_columns)} columns")

            # Read data
            range_name = "A:ZZ" if not max_rows else f"A1:ZZ{max_rows + 1}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()

            sheet_data = result.get('values', [])
            if len(sheet_data) <= 1:
                self.logger.warning("No data rows found")
                return stats

            headers = sheet_data[0]
            data_rows = sheet_data[1:max_rows + 1 if max_rows else len(sheet_data)]

            # Process rows
            for idx, row in enumerate(data_rows, start=1):
                stats['rows_attempted'] += 1

                # Convert to dict
                row_dict = {}
                for col_idx, value in enumerate(row):
                    if col_idx < len(headers):
                        row_dict[headers[col_idx]] = value

                # Process row
                try:
                    compact_data = self.process_row_compact(row_dict, idx)

                    # Write to sheet
                    if self._write_compact_data(idx, compact_data, enrich_columns):
                        stats['rows_updated'] += 1

                        # Update stats based on status
                        status_json = compact_data.get(f"{ENRICH_PREFIX}Status & Meta", '{}')
                        try:
                            status_data = json.loads(status_json)
                            status = status_data.get('status', 'FAILED').lower()
                            stats[status] = stats.get(status, 0) + 1
                        except:
                            stats['failed'] += 1

                    # Rate limiting
                    time.sleep(1)

                except Exception as e:
                    self.logger.error(f"Row {idx} failed: {e}")
                    stats['errors'].append(f"Row {idx}: {str(e)}")
                    stats['failed'] += 1

        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            stats['errors'].append(str(e))

        stats['elapsed_seconds'] = time.time() - start_time
        return stats

    def _write_compact_data(self, row_index: int, compact_data: Dict[str, str], enrich_columns: Dict[str, int]) -> bool:
        """Write compact data to sheet"""
        try:
            requests = []

            for header, value in compact_data.items():
                if header in enrich_columns:
                    col_idx = enrich_columns[header]
                    range_name = f"{self._col_to_letter(col_idx)}{row_index + 1}"
                    requests.append({
                        'range': range_name,
                        'values': [[value]]
                    })

            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would write to row {row_index + 1}: {len(requests)} columns")
                return True

            if requests:
                body = {
                    'valueInputOption': 'RAW',
                    'data': requests
                }

                self.service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body=body
                ).execute()

                return True

        except Exception as e:
            self.logger.error(f"Write failed for row {row_index}: {e}")
            return False

        return True

    def _extract_urls(self, row_data: Dict[str, str]) -> List[str]:
        """Extract URLs from row data"""
        urls = []
        url_fields = [
            'website', 'Website', 'url', 'URL', 'company_website',
            'organization_website_url', 'linkedin_url', 'LinkedIn URL',
            'twitter_url', 'facebook_url'
        ]

        for field in url_fields:
            if field in row_data and row_data[field]:
                url = row_data[field].strip()
                if url.startswith(('http://', 'https://')) and url not in urls:
                    urls.append(url)

        return urls

    def _extract_first_name(self, row_data: Dict[str, str]) -> str:
        """Extract first name from row data"""
        name_fields = ['first_name', 'First Name', 'name', 'Name']
        for field in name_fields:
            if field in row_data and row_data[field]:
                name = row_data[field].strip()
                if field in ['name', 'Name']:
                    # Extract first name from full name
                    return name.split()[0] if name.split() else ""
                return name
        return ""

    def _extract_company_name(self, row_data: Dict[str, str]) -> str:
        """Extract company name from row data"""
        company_fields = [
            'company', 'Company', 'organization', 'Organization',
            'organization_name', 'company_name'
        ]
        for field in company_fields:
            if field in row_data and row_data[field]:
                return row_data[field].strip()
        return ""

    def _get_display_name(self, row_data: Dict[str, str]) -> str:
        """Get display name for progress"""
        name_fields = ['name', 'Name', 'first_name', 'last_name']
        for field in name_fields:
            if field in row_data and row_data[field]:
                return row_data[field][:30]

        company_fields = ['company', 'organization']
        for field in company_fields:
            if field in row_data and row_data[field]:
                return f"({row_data[field][:25]})"

        return "Row data"

    def _get_row_key(self, row_data: Dict[str, str], row_index: int) -> str:
        """Generate row key"""
        # Priority: LinkedIn > Email > Company+Name > Row index

        for field in ['linkedin_url', 'LinkedIn URL']:
            if field in row_data and row_data[field]:
                return f"linkedin:{row_data[field]}"

        for field in ['email', 'Email']:
            if field in row_data and row_data[field]:
                return f"email:{row_data[field]}"

        company = self._extract_company_name(row_data)
        name = row_data.get('name', row_data.get('Name', ''))
        if company and name:
            return f"compound:{company}:{name}"

        return f"row:{row_index}"

    def _col_to_letter(self, col_index: int) -> str:
        """Convert column index to letter"""
        result = ""
        while col_index >= 0:
            result = chr(65 + (col_index % 26)) + result
            col_index = col_index // 26 - 1
        return result


# CLI integration
def main():
    """Main function for testing"""
    import argparse

    parser = argparse.ArgumentParser(description='Compact Google Sheets Enricher')
    parser.add_argument('--sheet-id', required=True, help='Google Sheet ID')
    parser.add_argument('--max-rows', type=int, default=5, help='Max rows to process')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    args = parser.parse_args()

    enricher = CompactEnricher(args.sheet_id, dry_run=args.dry_run)

    if not enricher.authenticate():
        print("Authentication failed")
        return 1

    print(f"🚀 Starting compact enrichment...")
    print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"   Max rows: {args.max_rows}")
    print(f"   Using only 5 enrichment columns")

    stats = enricher.process_sheet(max_rows=args.max_rows)

    print("\n📊 Results:")
    print(f"   Rows processed: {stats['rows_attempted']}")
    print(f"   Rows updated: {stats['rows_updated']}")
    print(f"   Success: {stats.get('ok', 0)} | Partial: {stats.get('partial', 0)} | Failed: {stats.get('failed', 0)}")
    print(f"   Time: {stats.get('elapsed_seconds', 0):.1f}s")

    if stats['errors']:
        print(f"   Errors: {len(stats['errors'])}")

    return 0 if stats['rows_updated'] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())