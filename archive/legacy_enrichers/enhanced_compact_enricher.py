#!/usr/bin/env python3
"""
Enhanced Compact Google Sheets Enricher
Integrates new multi-link scraping + API enrichment + lead scoring
Uses optimized column structure for Google Sheets
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
PROCESSOR_VERSION = "v3.0-Enhanced-Compact"
SCHEMA_VERSION = "S-Enhanced-1.0"
ENRICH_PREFIX = "Enrich::"

# Enhanced compact enrichment headers
ENHANCED_COMPACT_HEADERS = [
    f"{ENRICH_PREFIX}Row Key",              # Stable identifier
    f"{ENRICH_PREFIX}Lead Score",           # 0-100 score
    f"{ENRICH_PREFIX}Lead Tags",            # Hot/Warm/Cold/Discard
    f"{ENRICH_PREFIX}Complete Context",     # Synthesized paragraph
    f"{ENRICH_PREFIX}Link Data",            # All link summaries (JSON)
    f"{ENRICH_PREFIX}API Enrichment",       # All API results (JSON)
    f"{ENRICH_PREFIX}Score Breakdown",      # Scoring details (JSON)
    f"{ENRICH_PREFIX}Status & Meta",        # Status, timestamps (JSON)
]


class EnhancedCompactEnricher:
    """
    Enhanced compact enricher using 8 columns for comprehensive enrichment:
    - Row Key
    - Lead Score & Tags
    - Complete Context (human-readable)
    - Link Data (multi-link scraping results)
    - API Enrichment (all API results with sources)
    - Score Breakdown (detailed scoring)
    - Status & Meta (processing info)
    """

    def __init__(self, sheet_id: str, dry_run: bool = False, max_links: int = 5):
        self.sheet_id = sheet_id
        self.dry_run = dry_run
        self.max_links = max_links
        self.service = None
        self.drive_service = None
        self.enrichment_engine = EnhancedEnrichmentEngine()
        self.cli = None

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enhanced_compact_enricher.log'),
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
        """Check if we have space for enhanced enrichment columns"""
        current_count = len(existing_headers)
        needed_columns = len(ENHANCED_COMPACT_HEADERS)

        # Check existing enrichment columns
        existing_enrich = [h for h in existing_headers if h.startswith(ENRICH_PREFIX)]
        if existing_enrich:
            return True, current_count

        # Check if we can add new columns
        max_columns = 60  # Conservative Google Sheets limit
        available_space = max_columns - current_count

        if available_space >= needed_columns:
            return True, current_count + needed_columns
        else:
            return False, current_count

    def ensure_enhanced_headers(self, existing_headers: List[str]) -> Dict[str, int]:
        """Ensure enhanced enrichment headers exist"""
        enrich_columns = {}

        # Use columns starting after existing data
        start_col = len(existing_headers)
        target_columns = list(range(start_col, start_col + len(ENHANCED_COMPACT_HEADERS)))

        # Map each header to its target column
        for i, header in enumerate(ENHANCED_COMPACT_HEADERS):
            if i < len(target_columns):
                enrich_columns[header] = target_columns[i]

        self.logger.info(f"Using columns {self._col_to_letter(start_col)}-{self._col_to_letter(start_col + len(ENHANCED_COMPACT_HEADERS) - 1)} for enhanced enrichment")

        # Set headers
        if not self.dry_run:
            for i, header in enumerate(ENHANCED_COMPACT_HEADERS):
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
            self.logger.info(f"[DRY RUN] Would set headers in columns {self._col_to_letter(start_col)}+")

        return enrich_columns

    def process_row_enhanced(self, row_data: Dict[str, str], row_index: int) -> Dict[str, str]:
        """Process row with enhanced enrichment engine"""
        start_time = time.time()

        # Get display name
        person_name = self._get_display_name(row_data)

        if self.cli:
            self.cli.update_progress(row_index, person_name, "processing", "Starting enhanced enrichment...")

        # Generate row key
        row_key = self._get_row_key(row_data, row_index)

        try:
            # Run enhanced enrichment
            if self.cli:
                self.cli.update_progress(row_index, person_name, "processing", "Scraping links...")

            enrichment_result = self.enrichment_engine.enrich_row(row_data, max_links=self.max_links)

            # Update progress
            if self.cli:
                status = "ok" if enrichment_result['lead_score'] >= 60 else "partial"
                details = f"Score: {enrichment_result['lead_score']} - {enrichment_result['lead_tags']}"
                self.cli.update_progress(row_index, person_name, status, details)

            # Generate compact column data
            compact_data = self._generate_enhanced_compact_data(row_key, enrichment_result)

            return compact_data

        except Exception as e:
            self.logger.error(f"Row {row_index} enhanced enrichment error: {e}")

            # Return error data
            return {
                f"{ENRICH_PREFIX}Row Key": row_key,
                f"{ENRICH_PREFIX}Lead Score": "0",
                f"{ENRICH_PREFIX}Lead Tags": "Error ❌",
                f"{ENRICH_PREFIX}Complete Context": f"Error during enrichment: {str(e)[:200]}",
                f"{ENRICH_PREFIX}Link Data": "{}",
                f"{ENRICH_PREFIX}API Enrichment": "{}",
                f"{ENRICH_PREFIX}Score Breakdown": "{}",
                f"{ENRICH_PREFIX}Status & Meta": json.dumps({
                    'status': 'FAILED',
                    'error': str(e)[:200],
                    'last_enriched': datetime.now(timezone.utc).isoformat(),
                    'processor_version': PROCESSOR_VERSION
                }, separators=(',', ':'))
            }

    def _generate_enhanced_compact_data(self, row_key: str, enrichment_result: Dict) -> Dict[str, str]:
        """Generate enhanced compact enrichment data for 8 columns"""

        compact_data = {}

        # Column 1: Row Key
        compact_data[f"{ENRICH_PREFIX}Row Key"] = row_key

        # Column 2: Lead Score
        compact_data[f"{ENRICH_PREFIX}Lead Score"] = str(enrichment_result['lead_score'])

        # Column 3: Lead Tags
        compact_data[f"{ENRICH_PREFIX}Lead Tags"] = enrichment_result['lead_tags']

        # Column 4: Complete Context (human-readable paragraph)
        compact_data[f"{ENRICH_PREFIX}Complete Context"] = enrichment_result['complete_context']

        # Column 5: Link Data (JSON with all link summaries)
        link_data_summary = {}
        for link_idx, link_info in enrichment_result['link_data'].items():
            link_data_summary[f"link_{link_idx}"] = {
                'url': link_info['url'],
                'type': link_info['link_display'],
                'summary': link_info['summary'][:200],  # Truncate for space
                'status': link_info['scrape_status']
            }
        compact_data[f"{ENRICH_PREFIX}Link Data"] = json.dumps(link_data_summary, indent=2)

        # Column 6: API Enrichment (JSON with all API results + sources)
        api_summary = {}
        for api_name, api_data in enrichment_result['api_enrichment'].items():
            api_summary[api_name] = {
                'source': api_data.get('source', 'Unknown'),
                'status': api_data.get('data', {}).get('status', 'unknown'),
                'key_data': self._extract_api_key_data(api_name, api_data)
            }
        compact_data[f"{ENRICH_PREFIX}API Enrichment"] = json.dumps(api_summary, indent=2)

        # Column 7: Score Breakdown (JSON with detailed scoring)
        score_breakdown = enrichment_result.get('score_breakdown', {})
        compact_data[f"{ENRICH_PREFIX}Score Breakdown"] = json.dumps(score_breakdown, indent=2)

        # Column 8: Status & Meta (JSON with processing metadata)
        status_meta = {
            'status': 'OK' if enrichment_result['lead_score'] >= 30 else 'LOW_SCORE',
            'processing_time_ms': enrichment_result['processing_time_ms'],
            'last_enriched': enrichment_result['last_scraped'],
            'processor_version': PROCESSOR_VERSION,
            'schema_version': SCHEMA_VERSION,
            'links_scraped': len(enrichment_result['link_data']),
            'apis_called': len(enrichment_result['api_enrichment']),
            'errors': enrichment_result.get('errors', [])
        }
        compact_data[f"{ENRICH_PREFIX}Status & Meta"] = json.dumps(status_meta, indent=2)

        return compact_data

    def _extract_api_key_data(self, api_name: str, api_data: Dict) -> Dict:
        """Extract key data from API response for compact storage"""
        data = api_data.get('data', {})

        if api_name == 'gender':
            return {
                'gender': data.get('gender', ''),
                'probability': data.get('probability', 0)
            }
        elif api_name == 'email_verification':
            return {
                'deliverable': data.get('deliverable', False)
            }
        elif api_name == 'github':
            return {
                'total_repos': data.get('total_repos', 0),
                'total_orgs': data.get('total_orgs', 0)
            }
        elif api_name == 'google_search':
            return {
                'industries': data.get('industry_mentions', [])[:3]
            }
        elif api_name == 'linkedin':
            return {
                'verified': data.get('verified', False)
            }
        else:
            return {}

    def process_sheet(self, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """Process sheet with enhanced enrichment"""
        start_time = time.time()
        stats = {
            'rows_attempted': 0,
            'rows_updated': 0,
            'hot': 0,
            'warm': 0,
            'cold': 0,
            'discard': 0,
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

            enrich_columns = self.ensure_enhanced_headers(headers)
            if not enrich_columns:
                error_msg = "Failed to create enrichment columns"
                stats['errors'].append(error_msg)
                return stats

            self.logger.info(f"Using enhanced compact enrichment: {len(enrich_columns)} columns")

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
            # Fix: Process all rows up to max_rows (not just 1 row)
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
                    compact_data = self.process_row_enhanced(row_dict, idx)

                    # Write to sheet
                    if self._write_compact_data(idx, compact_data, enrich_columns):
                        stats['rows_updated'] += 1

                        # Update stats based on tags
                        tags = compact_data.get(f"{ENRICH_PREFIX}Lead Tags", '').lower()
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


# CLI integration
def main():
    """Main function for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced Compact Google Sheets Enricher')
    parser.add_argument('--sheet-id', required=True, help='Google Sheet ID')
    parser.add_argument('--max-rows', type=int, default=5, help='Max rows to process')
    parser.add_argument('--max-links', type=int, default=5, help='Max links per row')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    args = parser.parse_args()

    enricher = EnhancedCompactEnricher(
        args.sheet_id,
        dry_run=args.dry_run,
        max_links=args.max_links
    )

    if not enricher.authenticate():
        print("❌ Authentication failed")
        return 1

    print(f"🚀 Starting enhanced compact enrichment...")
    print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"   Max rows: {args.max_rows}")
    print(f"   Max links per row: {args.max_links}")
    print(f"   Using 8 enrichment columns")

    stats = enricher.process_sheet(max_rows=args.max_rows)

    print("\n📊 Results:")
    print(f"   Rows processed: {stats['rows_attempted']}")
    print(f"   Rows updated: {stats['rows_updated']}")
    print(f"   🔥 Hot: {stats.get('hot', 0)} | 🟡 Warm: {stats.get('warm', 0)} | 🔵 Cold: {stats.get('cold', 0)} | ⚫ Discard: {stats.get('discard', 0)}")
    print(f"   Time: {stats.get('elapsed_seconds', 0):.1f}s")

    if stats['errors']:
        print(f"   Errors: {len(stats['errors'])}")

    return 0 if stats['rows_updated'] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())