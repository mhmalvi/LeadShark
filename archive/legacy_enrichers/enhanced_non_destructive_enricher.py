#!/usr/bin/env python3
"""
Enhanced Non-Destructive Google Sheets Enricher (v3.0)
Expands enrichment data into individual columns for maximum readability
Creates 35-40 individual columns instead of JSON-packed data
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
from enhanced_enrichment_engine import EnhancedEnrichmentEngine

# Constants
PROCESSOR_VERSION = "v3.0-Enhanced-Expanded"
SCHEMA_VERSION = "S-Enhanced-Expanded-1.0"
ENRICH_PREFIX = "Enrich::"

# Enhanced expanded enrichment headers (35-40 columns)
ENHANCED_EXPANDED_HEADERS = [
    # Row identification
    f"{ENRICH_PREFIX}Row Key",

    # Link 1 (3 columns)
    f"{ENRICH_PREFIX}Link 1",
    f"{ENRICH_PREFIX}Link 1 - Summary",
    f"{ENRICH_PREFIX}Link 1 - JSON",

    # Link 2 (3 columns)
    f"{ENRICH_PREFIX}Link 2",
    f"{ENRICH_PREFIX}Link 2 - Summary",
    f"{ENRICH_PREFIX}Link 2 - JSON",

    # Link 3 (3 columns)
    f"{ENRICH_PREFIX}Link 3",
    f"{ENRICH_PREFIX}Link 3 - Summary",
    f"{ENRICH_PREFIX}Link 3 - JSON",

    # Link 4 (3 columns)
    f"{ENRICH_PREFIX}Link 4",
    f"{ENRICH_PREFIX}Link 4 - Summary",
    f"{ENRICH_PREFIX}Link 4 - JSON",

    # Link 5 (3 columns)
    f"{ENRICH_PREFIX}Link 5",
    f"{ENRICH_PREFIX}Link 5 - Summary",
    f"{ENRICH_PREFIX}Link 5 - JSON",

    # Lead Scoring (3 columns)
    f"{ENRICH_PREFIX}Lead Score",
    f"{ENRICH_PREFIX}Lead Tags",
    f"{ENRICH_PREFIX}Complete Context",

    # Gender API (3 columns)
    f"{ENRICH_PREFIX}Gender",
    f"{ENRICH_PREFIX}Gender Confidence",
    f"{ENRICH_PREFIX}Gender API Source",

    # Email API (3 columns)
    f"{ENRICH_PREFIX}Email Status",
    f"{ENRICH_PREFIX}Email Deliverability",
    f"{ENRICH_PREFIX}Email API Source",

    # GitHub API (4 columns)
    f"{ENRICH_PREFIX}GitHub Profile",
    f"{ENRICH_PREFIX}GitHub Repos Count",
    f"{ENRICH_PREFIX}GitHub Activity",
    f"{ENRICH_PREFIX}GitHub API Source",

    # Google Search API (3 columns)
    f"{ENRICH_PREFIX}Company Info",
    f"{ENRICH_PREFIX}Company Industry",
    f"{ENRICH_PREFIX}Google Search API Source",

    # LinkedIn API (3 columns)
    f"{ENRICH_PREFIX}LinkedIn Verified",
    f"{ENRICH_PREFIX}LinkedIn Status",
    f"{ENRICH_PREFIX}LinkedIn API Source",

    # Score Breakdown (6 columns)
    f"{ENRICH_PREFIX}Role Score",
    f"{ENRICH_PREFIX}Company Fit Score",
    f"{ENRICH_PREFIX}Engagement Score",
    f"{ENRICH_PREFIX}Contactability Score",
    f"{ENRICH_PREFIX}Tech Fit Score",
    f"{ENRICH_PREFIX}Recency Score",

    # Processing Metadata (3 columns)
    f"{ENRICH_PREFIX}Processing Time (ms)",
    f"{ENRICH_PREFIX}Last Enriched",
    f"{ENRICH_PREFIX}Status",
]


class EnhancedNonDestructiveEnricher:
    """
    Enhanced non-destructive enricher using 35-40 individual columns:
    - 5 links × 3 columns each (URL, Summary, JSON)
    - Lead scoring (score, tags, context)
    - Gender API (3 columns)
    - Email API (3 columns)
    - GitHub API (4 columns)
    - Google Search API (3 columns)
    - LinkedIn API (3 columns)
    - Score breakdown (6 columns)
    - Processing metadata (3 columns)
    """

    def __init__(self, sheet_id: str, dry_run: bool = False, max_links: int = 5, auto_create_sheet: bool = True):
        self.sheet_id = sheet_id
        self.original_sheet_id = sheet_id
        self.dry_run = dry_run
        self.max_links = max_links
        self.auto_create_sheet = auto_create_sheet
        self.service = None
        self.drive_service = None
        self.enrichment_engine = EnhancedEnrichmentEngine()
        self.new_sheet_created = False
        self.new_sheet_url = None

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enhanced_non_destructive_enricher.log'),
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
        """Check if we have space for expanded enrichment columns"""
        current_count = len(existing_headers)
        needed_columns = len(ENHANCED_EXPANDED_HEADERS)

        # Check existing enrichment columns
        existing_enrich = [h for h in existing_headers if h.startswith(ENRICH_PREFIX)]

        # Check if we have expanded format already
        has_expanded = any('Link 1' in h for h in existing_enrich)
        if has_expanded and len(existing_enrich) >= 40:
            self.logger.info(f"Found {len(existing_enrich)} existing EXPANDED enrichment columns")
            return True, current_count

        # Check if we can add new columns
        max_columns = 60  # Conservative Google Sheets limit
        available_space = max_columns - current_count

        if available_space >= needed_columns:
            return True, current_count + needed_columns
        else:
            # Not enough space - will need to create new sheet
            self.logger.warning(f"Insufficient space: need {needed_columns}, have {available_space}")
            self.logger.info("Will automatically create a new sheet with essential data...")
            return False, current_count

    def ensure_expanded_headers(self, existing_headers: List[str]) -> Optional[Dict[str, int]]:
        """Ensure expanded enrichment headers exist in sheet"""
        try:
            # Check if EXPANDED headers already exist (not compact headers)
            existing_enrich = [h for h in existing_headers if h.startswith(ENRICH_PREFIX)]

            # Check if we have expanded format (Link 1, Link 2, etc.) or compact format (Link Data JSON)
            has_expanded = any('Link 1' in h for h in existing_enrich)

            if has_expanded and len(existing_enrich) >= 40:
                # We already have expanded format, reuse it
                self.logger.info(f"Found {len(existing_enrich)} existing EXPANDED enrichment columns")
                header_map = {}
                for idx, header in enumerate(existing_headers):
                    if header.startswith(ENRICH_PREFIX):
                        header_map[header] = idx
                return header_map

            # If we have compact format (8 columns), we need to add expanded format alongside
            if existing_enrich and not has_expanded:
                self.logger.info(f"Found {len(existing_enrich)} COMPACT columns, will add EXPANDED columns alongside")

            # Add new headers
            start_col = len(existing_headers)
            new_headers = existing_headers + ENHANCED_EXPANDED_HEADERS

            if not self.dry_run:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range="1:1",
                    valueInputOption='RAW',
                    body={'values': [new_headers]}
                ).execute()

            # Create header map
            header_map = {}
            for idx, header in enumerate(ENHANCED_EXPANDED_HEADERS, start=start_col):
                header_map[header] = idx

            self.logger.info(f"Created {len(ENHANCED_EXPANDED_HEADERS)} enrichment columns starting at column {start_col}")
            return header_map

        except Exception as e:
            self.logger.error(f"Failed to ensure headers: {e}")
            return None

    def process_row_expanded(self, row_data: Dict[str, str], row_index: int) -> Dict[str, str]:
        """Process a single row and return expanded column data"""
        self.logger.info(f"Processing row {row_index}: {self._get_display_name(row_data)}")

        # Run enrichment engine
        enrichment_result = self.enrichment_engine.enrich_row(row_data, max_links=self.max_links)

        # Map to expanded columns
        expanded_data = {}

        # Column 1: Row Key
        expanded_data[f"{ENRICH_PREFIX}Row Key"] = self._get_row_key(row_data, row_index)

        # Columns 2-16: Link 1-5 (3 columns each)
        for link_num in range(1, 6):
            link_key = f"link_{link_num}"
            prefix = f"{ENRICH_PREFIX}Link {link_num}"

            if link_key in enrichment_result['link_data']:
                link_info = enrichment_result['link_data'][link_key]
                expanded_data[prefix] = link_info['url']
                expanded_data[f"{prefix} - Summary"] = link_info['summary']
                expanded_data[f"{prefix} - JSON"] = json.dumps(link_info.get('extracted_data', {}), indent=2)
            else:
                expanded_data[prefix] = ""
                expanded_data[f"{prefix} - Summary"] = ""
                expanded_data[f"{prefix} - JSON"] = ""

        # Columns 17-19: Lead Scoring
        expanded_data[f"{ENRICH_PREFIX}Lead Score"] = str(enrichment_result['lead_score'])
        expanded_data[f"{ENRICH_PREFIX}Lead Tags"] = enrichment_result['lead_tags']
        expanded_data[f"{ENRICH_PREFIX}Complete Context"] = enrichment_result['complete_context']

        # Columns 20-22: Gender API
        gender_data = enrichment_result['api_enrichment'].get('gender', {})
        if gender_data:
            data = gender_data.get('data', {})
            expanded_data[f"{ENRICH_PREFIX}Gender"] = data.get('gender', '').capitalize()
            expanded_data[f"{ENRICH_PREFIX}Gender Confidence"] = f"{data.get('probability', 0) * 100:.0f}%"
            expanded_data[f"{ENRICH_PREFIX}Gender API Source"] = gender_data.get('source', 'Genderize.io')
        else:
            expanded_data[f"{ENRICH_PREFIX}Gender"] = ""
            expanded_data[f"{ENRICH_PREFIX}Gender Confidence"] = ""
            expanded_data[f"{ENRICH_PREFIX}Gender API Source"] = ""

        # Columns 23-25: Email API
        email_data = enrichment_result['api_enrichment'].get('email_verification', {})
        if email_data:
            data = email_data.get('data', {})
            expanded_data[f"{ENRICH_PREFIX}Email Status"] = "Valid" if data.get('deliverable') else "Invalid"
            expanded_data[f"{ENRICH_PREFIX}Email Deliverability"] = "Deliverable" if data.get('deliverable') else "Undeliverable"
            expanded_data[f"{ENRICH_PREFIX}Email API Source"] = email_data.get('source', 'EVA API')
        else:
            expanded_data[f"{ENRICH_PREFIX}Email Status"] = ""
            expanded_data[f"{ENRICH_PREFIX}Email Deliverability"] = ""
            expanded_data[f"{ENRICH_PREFIX}Email API Source"] = ""

        # Columns 26-29: GitHub API
        github_data = enrichment_result['api_enrichment'].get('github', {})
        if github_data:
            data = github_data.get('data', {})
            expanded_data[f"{ENRICH_PREFIX}GitHub Profile"] = f"github.com/{data.get('username', '')}" if data.get('username') else ""
            expanded_data[f"{ENRICH_PREFIX}GitHub Repos Count"] = str(data.get('total_repos', 0))
            expanded_data[f"{ENRICH_PREFIX}GitHub Activity"] = "Active" if data.get('total_repos', 0) > 0 else "Inactive"
            expanded_data[f"{ENRICH_PREFIX}GitHub API Source"] = github_data.get('source', 'GitHub REST API v3')
        else:
            expanded_data[f"{ENRICH_PREFIX}GitHub Profile"] = ""
            expanded_data[f"{ENRICH_PREFIX}GitHub Repos Count"] = ""
            expanded_data[f"{ENRICH_PREFIX}GitHub Activity"] = ""
            expanded_data[f"{ENRICH_PREFIX}GitHub API Source"] = ""

        # Columns 30-32: Google Search API
        google_data = enrichment_result['api_enrichment'].get('google_search', {})
        if google_data:
            data = google_data.get('data', {})
            expanded_data[f"{ENRICH_PREFIX}Company Info"] = data.get('company_info', '')[:200]
            industries = data.get('industry_mentions', [])
            expanded_data[f"{ENRICH_PREFIX}Company Industry"] = ", ".join(industries[:5])
            expanded_data[f"{ENRICH_PREFIX}Google Search API Source"] = google_data.get('source', 'Google Custom Search API')
        else:
            expanded_data[f"{ENRICH_PREFIX}Company Info"] = ""
            expanded_data[f"{ENRICH_PREFIX}Company Industry"] = ""
            expanded_data[f"{ENRICH_PREFIX}Google Search API Source"] = ""

        # Columns 33-35: LinkedIn API
        linkedin_data = enrichment_result['api_enrichment'].get('linkedin', {})
        if linkedin_data:
            data = linkedin_data.get('data', {})
            expanded_data[f"{ENRICH_PREFIX}LinkedIn Verified"] = "Yes" if data.get('verified') else "No"
            expanded_data[f"{ENRICH_PREFIX}LinkedIn Status"] = data.get('status', 'Unknown')
            expanded_data[f"{ENRICH_PREFIX}LinkedIn API Source"] = linkedin_data.get('source', 'Web scraping')
        else:
            expanded_data[f"{ENRICH_PREFIX}LinkedIn Verified"] = ""
            expanded_data[f"{ENRICH_PREFIX}LinkedIn Status"] = ""
            expanded_data[f"{ENRICH_PREFIX}LinkedIn API Source"] = ""

        # Columns 36-41: Score Breakdown
        score_breakdown = enrichment_result.get('score_breakdown', {})
        expanded_data[f"{ENRICH_PREFIX}Role Score"] = f"{score_breakdown.get('role_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}Company Fit Score"] = f"{score_breakdown.get('company_fit_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}Engagement Score"] = f"{score_breakdown.get('engagement_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}Contactability Score"] = f"{score_breakdown.get('contactability_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}Tech Fit Score"] = f"{score_breakdown.get('tech_fit_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}Recency Score"] = f"{score_breakdown.get('recency_score', 0):.1f}"

        # Columns 42-44: Processing Metadata
        expanded_data[f"{ENRICH_PREFIX}Processing Time (ms)"] = str(enrichment_result['processing_time_ms'])
        expanded_data[f"{ENRICH_PREFIX}Last Enriched"] = enrichment_result['last_scraped']
        expanded_data[f"{ENRICH_PREFIX}Status"] = 'OK' if enrichment_result['lead_score'] >= 30 else 'LOW_SCORE'

        return expanded_data

    def create_new_sheet_with_essential_data(self, original_headers: List[str]) -> Optional[str]:
        """
        Create a new Google Sheet with essential data columns + enrichment columns
        Returns new sheet ID if successful, None otherwise
        """
        try:
            self.logger.info("Creating new sheet with essential data...")

            # Identify essential columns (common lead data fields)
            essential_fields = [
                'name', 'Name', 'full_name', 'Full Name',
                'first_name', 'First Name', 'last_name', 'Last Name',
                'email', 'Email', 'email_address', 'Email Address',
                'company', 'Company', 'organization', 'Organization',
                'title', 'Title', 'job_title', 'Job Title',
                'location', 'Location',
                'linkedin_url', 'LinkedIn URL', 'linkedin',
                'website', 'Website', 'url', 'URL', 'company_website',
                'twitter_url', 'Twitter URL', 'twitter',
                'facebook_url', 'Facebook URL',
                'github_url', 'GitHub URL',
                'phone', 'Phone', 'phone_number'
            ]

            # Find which essential columns exist in original sheet
            essential_columns = []
            essential_indices = []
            for idx, header in enumerate(original_headers):
                if header in essential_fields and header not in essential_columns:
                    essential_columns.append(header)
                    essential_indices.append(idx)

            self.logger.info(f"Found {len(essential_columns)} essential columns to copy")

            # Create new spreadsheet
            spreadsheet = {
                'properties': {
                    'title': f'LeadShark Enriched - {datetime.now().strftime("%Y-%m-%d %H-%M")}'
                },
                'sheets': [{
                    'properties': {
                        'title': 'Enriched Data',
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': len(essential_columns) + len(ENHANCED_EXPANDED_HEADERS)
                        }
                    }
                }]
            }

            response = self.service.spreadsheets().create(body=spreadsheet).execute()
            new_sheet_id = response['spreadsheetId']
            new_sheet_url = response['spreadsheetUrl']

            self.logger.info(f"Created new sheet: {new_sheet_id}")
            self.logger.info(f"URL: {new_sheet_url}")

            # Create combined headers
            new_headers = essential_columns + ENHANCED_EXPANDED_HEADERS

            # Write headers to new sheet
            self.service.spreadsheets().values().update(
                spreadsheetId=new_sheet_id,
                range="1:1",
                valueInputOption='RAW',
                body={'values': [new_headers]}
            ).execute()

            self.logger.info("Wrote headers to new sheet")

            # Copy data from original sheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.original_sheet_id,
                range="A:ZZ"
            ).execute()

            original_data = result.get('values', [])
            if len(original_data) > 1:
                # Extract essential data from each row
                rows_to_copy = []
                for row in original_data[1:]:  # Skip header
                    new_row = []
                    for idx in essential_indices:
                        if idx < len(row):
                            new_row.append(row[idx])
                        else:
                            new_row.append('')

                    # Pad with empty cells for enrichment columns
                    new_row.extend([''] * len(ENHANCED_EXPANDED_HEADERS))
                    rows_to_copy.append(new_row)

                # Write data to new sheet
                if rows_to_copy:
                    self.service.spreadsheets().values().update(
                        spreadsheetId=new_sheet_id,
                        range=f"A2:ZZ{len(rows_to_copy) + 1}",
                        valueInputOption='RAW',
                        body={'values': rows_to_copy}
                    ).execute()

                    self.logger.info(f"Copied {len(rows_to_copy)} rows to new sheet")

            # Store new sheet info
            self.new_sheet_created = True
            self.new_sheet_url = new_sheet_url
            self.sheet_id = new_sheet_id

            self.logger.info(f"✅ New sheet ready: {new_sheet_url}")

            return new_sheet_id

        except Exception as e:
            self.logger.error(f"Failed to create new sheet: {e}")
            import traceback
            traceback.print_exc()
            return None

    def process_sheet(self, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """Process sheet with expanded enrichment"""
        start_time = time.time()
        stats = {
            'rows_attempted': 0,
            'rows_updated': 0,
            'hot': 0,
            'warm': 0,
            'cold': 0,
            'discard': 0,
            'errors': [],
            'new_sheet_created': False,
            'new_sheet_url': None
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
                # Try to create new sheet automatically
                if self.auto_create_sheet:
                    self.logger.info("🔄 Creating new sheet with essential data...")
                    new_sheet_id = self.create_new_sheet_with_essential_data(headers)

                    if not new_sheet_id:
                        error_msg = "Failed to create new sheet automatically"
                        self.logger.error(error_msg)
                        stats['errors'].append(error_msg)
                        return stats

                    # Update stats
                    stats['new_sheet_created'] = True
                    stats['new_sheet_url'] = self.new_sheet_url

                    # Re-read headers from new sheet
                    result = self.service.spreadsheets().values().get(
                        spreadsheetId=self.sheet_id,
                        range="1:1"
                    ).execute()
                    headers = result.get('values', [[]])[0] if result.get('values') else []
                else:
                    error_msg = f"Cannot add enrichment columns - sheet has {len(headers)} columns (limit ~60)"
                    self.logger.error(error_msg)
                    stats['errors'].append(error_msg)
                    return stats

            enrich_columns = self.ensure_expanded_headers(headers)
            if not enrich_columns:
                error_msg = "Failed to create enrichment columns"
                stats['errors'].append(error_msg)
                return stats

            self.logger.info(f"Using enhanced expanded enrichment: {len(enrich_columns)} columns")

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
            # Fix: Process all rows up to max_rows
            if max_rows:
                data_rows = sheet_data[1:max_rows + 1]
            else:
                data_rows = sheet_data[1:]

            self.logger.info(f"Processing {len(data_rows)} data rows...")

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
                    expanded_data = self.process_row_expanded(row_dict, idx)

                    # Write to sheet
                    if self._write_expanded_data(idx, expanded_data, enrich_columns):
                        stats['rows_updated'] += 1

                        # Update stats based on tags
                        tags = expanded_data.get(f"{ENRICH_PREFIX}Lead Tags", '').lower()
                        if 'hot' in tags or '🔥' in tags:
                            stats['hot'] += 1
                        elif 'warm' in tags or '🟡' in tags:
                            stats['warm'] += 1
                        elif 'cold' in tags or '🔵' in tags:
                            stats['cold'] += 1
                        else:
                            stats['discard'] += 1

                    # Rate limiting
                    time.sleep(1)

                except Exception as e:
                    self.logger.error(f"Row {idx} failed: {e}")
                    stats['errors'].append(f"Row {idx}: {str(e)}")
                    stats['discard'] += 1

        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            stats['errors'].append(str(e))

        stats['elapsed_seconds'] = time.time() - start_time
        return stats

    def _write_expanded_data(self, row_index: int, expanded_data: Dict[str, str], enrich_columns: Dict[str, int]) -> bool:
        """Write expanded data to sheet"""
        try:
            requests = []

            for header, value in expanded_data.items():
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
        for field in ['linkedin_url', 'LinkedIn URL']:
            if field in row_data and row_data[field]:
                return f"linkedin:{row_data[field]}"

        for field in ['email', 'Email']:
            if field in row_data and row_data[field]:
                return f"email:{row_data[field]}"

        company = row_data.get('company', row_data.get('Company', ''))
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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced Non-Destructive Enricher v3.0')
    parser.add_argument('--sheet-id', required=True, help='Google Sheet ID')
    parser.add_argument('--max-rows', type=int, help='Max rows to process')
    parser.add_argument('--max-links', type=int, default=5, help='Max links per row')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    args = parser.parse_args()

    enricher = EnhancedNonDestructiveEnricher(
        sheet_id=args.sheet_id,
        dry_run=args.dry_run,
        max_links=args.max_links
    )

    if enricher.authenticate():
        stats = enricher.process_sheet(max_rows=args.max_rows)
        print(f"\n✅ Processing complete!")
        print(f"Rows attempted: {stats['rows_attempted']}")
        print(f"Rows updated: {stats['rows_updated']}")
        print(f"Hot: {stats['hot']}, Warm: {stats['warm']}, Cold: {stats['cold']}, Discard: {stats['discard']}")