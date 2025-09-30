#!/usr/bin/env python3
"""
🤖🦈 Hybrid AI + Enhanced Multi-Link Enricher (v4.0)
Combines AI-powered intelligence with comprehensive multi-link scraping

Features:
- AI-powered analysis (Anthropic Claude + OpenAI GPT)
- Multi-link scraping (5 links × 3 columns each)
- Comprehensive API enrichment (5 APIs)
- Advanced lead scoring (6-factor breakdown + AI score)
- 59 total enrichment columns (44 enhanced + 15 AI)
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

sys.path.append(os.path.dirname(__file__))

from google_sheets_auth import authenticate_google_sheets
from enhanced_enrichment_engine import EnhancedEnrichmentEngine
from anthropic_enrichment import AnthropicEnrichment
from data_enrichment import enrich_gender, enrich_email_verification

# Constants
PROCESSOR_VERSION = "v4.0-Hybrid-AI-Enhanced"
SCHEMA_VERSION = "S-Hybrid-4.0"
ENRICH_PREFIX = "Enrich::"

# Hybrid enrichment headers (59 columns total)
HYBRID_ENRICHMENT_HEADERS = [
    # Row identification (1)
    f"{ENRICH_PREFIX}Row Key",

    # === MULTI-LINK SCRAPING (15 columns) ===
    # Link 1-5 (3 columns each)
    f"{ENRICH_PREFIX}Link 1", f"{ENRICH_PREFIX}Link 1 - Summary", f"{ENRICH_PREFIX}Link 1 - JSON",
    f"{ENRICH_PREFIX}Link 2", f"{ENRICH_PREFIX}Link 2 - Summary", f"{ENRICH_PREFIX}Link 2 - JSON",
    f"{ENRICH_PREFIX}Link 3", f"{ENRICH_PREFIX}Link 3 - Summary", f"{ENRICH_PREFIX}Link 3 - JSON",
    f"{ENRICH_PREFIX}Link 4", f"{ENRICH_PREFIX}Link 4 - Summary", f"{ENRICH_PREFIX}Link 4 - JSON",
    f"{ENRICH_PREFIX}Link 5", f"{ENRICH_PREFIX}Link 5 - Summary", f"{ENRICH_PREFIX}Link 5 - JSON",

    # === AI INTELLIGENCE (8 columns) ===
    f"{ENRICH_PREFIX}AI: Category",
    f"{ENRICH_PREFIX}AI: Value Proposition",
    f"{ENRICH_PREFIX}AI: Business Model",
    f"{ENRICH_PREFIX}AI: Lead Score",
    f"{ENRICH_PREFIX}AI: Priority",
    f"{ENRICH_PREFIX}AI: Strengths",
    f"{ENRICH_PREFIX}AI: Actions",
    f"{ENRICH_PREFIX}AI: Report",

    # === TRADITIONAL LEAD SCORING (3 columns) ===
    f"{ENRICH_PREFIX}Lead Score",
    f"{ENRICH_PREFIX}Lead Tags",
    f"{ENRICH_PREFIX}Complete Context",

    # === API ENRICHMENT (15 columns) ===
    # Gender API (3)
    f"{ENRICH_PREFIX}Gender", f"{ENRICH_PREFIX}Gender Confidence", f"{ENRICH_PREFIX}Gender API Source",
    # Email API (3)
    f"{ENRICH_PREFIX}Email Status", f"{ENRICH_PREFIX}Email Deliverability", f"{ENRICH_PREFIX}Email API Source",
    # GitHub API (4)
    f"{ENRICH_PREFIX}GitHub Profile", f"{ENRICH_PREFIX}GitHub Repos Count",
    f"{ENRICH_PREFIX}GitHub Activity", f"{ENRICH_PREFIX}GitHub API Source",
    # Google Search API (3)
    f"{ENRICH_PREFIX}Company Info", f"{ENRICH_PREFIX}Company Industry", f"{ENRICH_PREFIX}Google Search API Source",
    # LinkedIn API (3)
    f"{ENRICH_PREFIX}LinkedIn Verified", f"{ENRICH_PREFIX}LinkedIn Status", f"{ENRICH_PREFIX}LinkedIn API Source",

    # === SCORE BREAKDOWN (6 columns) ===
    f"{ENRICH_PREFIX}Role Score",
    f"{ENRICH_PREFIX}Company Fit Score",
    f"{ENRICH_PREFIX}Engagement Score",
    f"{ENRICH_PREFIX}Contactability Score",
    f"{ENRICH_PREFIX}Tech Fit Score",
    f"{ENRICH_PREFIX}Recency Score",

    # === PROCESSING METADATA (4 columns) ===
    f"{ENRICH_PREFIX}AI Confidence",
    f"{ENRICH_PREFIX}Processing Time (ms)",
    f"{ENRICH_PREFIX}Last Enriched",
    f"{ENRICH_PREFIX}Status",
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('hybrid_enricher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure stdout encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass


class HybridAIEnhancedEnricher:
    """
    Hybrid enricher combining AI intelligence with comprehensive multi-link scraping.

    Features:
    - AI-powered company analysis (Anthropic Claude + OpenAI GPT)
    - Multi-link scraping (5 links with summaries and JSON)
    - 5 API integrations (Gender, Email, GitHub, Google, LinkedIn)
    - Advanced lead scoring (traditional + AI)
    - 59 total enrichment columns
    """

    def __init__(self, sheet_id: str, dry_run: bool = False, max_links: int = 5, auto_create_sheet: bool = False):
        self.sheet_id = sheet_id
        self.original_sheet_id = sheet_id
        self.dry_run = dry_run
        self.max_links = max_links
        self.auto_create_sheet = auto_create_sheet  # Now defaults to False - work on main tab
        self.service = None
        self.drive_service = None
        self.tab_name = "Data"  # Main tab name

        # New sheet tracking
        self.new_sheet_created = False
        self.new_sheet_url = None

        # Initialize engines
        self.enrichment_engine = EnhancedEnrichmentEngine()
        self.ai_enricher = AnthropicEnrichment()

        self.logger = logger

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

    def add_enrichment_columns_to_tab(self, tab_name: str, original_headers: List[str]) -> bool:
        """
        Add enrichment columns to existing tab (expands columns programmatically)
        Returns True if successful, False otherwise
        """
        try:
            self.logger.info("="*60)
            self.logger.info("📊 ADDING ENRICHMENT COLUMNS TO MAIN TAB")
            self.logger.info("="*60)

            # Check if enrichment columns already exist
            existing_headers = original_headers
            enrichment_exists = any(header.startswith(ENRICH_PREFIX) for header in existing_headers)

            if enrichment_exists:
                self.logger.info("⚠️  Enrichment columns already exist, will update existing data")
                return True

            # Get current sheet metadata
            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])

            target_sheet = None
            for sheet in sheets:
                if sheet['properties']['title'] == tab_name:
                    target_sheet = sheet
                    break

            if not target_sheet:
                self.logger.error(f"Tab '{tab_name}' not found")
                return False

            sheet_id = target_sheet['properties']['sheetId']
            current_cols = target_sheet['properties']['gridProperties']['columnCount']
            current_rows = target_sheet['properties']['gridProperties']['rowCount']

            # Calculate required columns
            required_cols = len(original_headers) + len(HYBRID_ENRICHMENT_HEADERS)

            self.logger.info(f"Current columns: {current_cols}")
            self.logger.info(f"Required columns: {required_cols} ({len(original_headers)} existing + {len(HYBRID_ENRICHMENT_HEADERS)} enrichment)")

            # Expand columns if needed
            if required_cols > current_cols:
                self.logger.info(f"Expanding from {current_cols} to {required_cols} columns...")

                request = {
                    'requests': [{
                        'appendDimension': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'length': required_cols - current_cols
                        }
                    }]
                }

                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body=request
                ).execute()

                self.logger.info(f"✅ Expanded to {required_cols} columns")

            # Append enrichment headers to row 1
            start_col = self._col_to_letter(len(original_headers) + 1)
            end_col = self._col_to_letter(len(original_headers) + len(HYBRID_ENRICHMENT_HEADERS))

            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=f"'{tab_name}'!{start_col}1:{end_col}1",
                valueInputOption='RAW',
                body={'values': [HYBRID_ENRICHMENT_HEADERS]}
            ).execute()

            self.logger.info(f"✅ Added {len(HYBRID_ENRICHMENT_HEADERS)} enrichment column headers at {start_col}1:{end_col}1")
            self.logger.info("="*60)

            return True

        except Exception as e:
            self.logger.error(f"Failed to add enrichment columns: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_new_tab_with_essential_data(self, original_headers: List[str]) -> Optional[str]:
        """
        Create a new TAB within the existing sheet with essential data columns + 59 enrichment columns
        Returns new tab name if successful, None otherwise
        """
        try:
            self.logger.info("="*60)
            self.logger.info("📑 CREATING NEW TAB FOR HYBRID ENRICHMENT")
            self.logger.info("="*60)

            # Identify essential columns (common lead data fields)
            essential_fields = [
                'name', 'Name', 'full_name', 'Full Name',
                'first_name', 'First Name', 'last_name', 'Last Name',
                'email', 'Email', 'email_address', 'Email Address', 'personal_email',
                'company', 'Company', 'organization', 'Organization', 'organization_name',
                'title', 'Title', 'job_title', 'Job Title',
                'location', 'Location', 'city', 'state', 'country',
                'linkedin_url', 'LinkedIn URL', 'linkedin',
                'website', 'Website', 'url', 'URL', 'company_website', 'organization_website_url',
                'twitter_url', 'Twitter URL', 'twitter',
                'facebook_url', 'Facebook URL',
                'github_url', 'GitHub URL',
                'phone', 'Phone', 'phone_number',
                'industry', 'Industry',
                'headline', 'Headline',
                'seniority', 'Seniority'
            ]

            # Find which essential columns exist in original sheet
            essential_columns = []
            essential_indices = []
            for idx, header in enumerate(original_headers):
                if header in essential_fields and header not in essential_columns:
                    essential_columns.append(header)
                    essential_indices.append(idx)

            self.logger.info(f"Found {len(essential_columns)} essential columns to copy:")
            self.logger.info(f"  {', '.join(essential_columns[:10])}{'...' if len(essential_columns) > 10 else ''}")

            # Create new tab with timestamp name
            new_tab_name = f'Enriched {datetime.now().strftime("%Y-%m-%d %H-%M-%S")}'

            # Add new sheet/tab to existing spreadsheet
            request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': new_tab_name,
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': len(essential_columns) + len(HYBRID_ENRICHMENT_HEADERS)
                            }
                        }
                    }
                }]
            }

            response = self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body=request_body
            ).execute()

            self.logger.info(f"✅ Created new tab: {new_tab_name}")
            self.logger.info(f"🔗 URL: https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit#gid={response['replies'][0]['addSheet']['properties']['sheetId']}")

            # Create combined headers
            new_headers = essential_columns + HYBRID_ENRICHMENT_HEADERS

            # Write headers to new tab
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=f"'{new_tab_name}'!1:1",
                valueInputOption='RAW',
                body={'values': [new_headers]}
            ).execute()

            self.logger.info(f"📋 Wrote {len(new_headers)} headers ({len(essential_columns)} essential + {len(HYBRID_ENRICHMENT_HEADERS)} enrichment)")

            # Copy data from original sheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="Data!A:ZZ"
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
                    new_row.extend([''] * len(HYBRID_ENRICHMENT_HEADERS))
                    rows_to_copy.append(new_row)

                # Write data to new tab
                if rows_to_copy:
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.sheet_id,
                        range=f"'{new_tab_name}'!A2:ZZ{len(rows_to_copy) + 1}",
                        valueInputOption='RAW',
                        body={'values': rows_to_copy}
                    ).execute()

                    self.logger.info(f"📊 Copied {len(rows_to_copy)} rows to new tab")

            # Store new tab info
            self.new_sheet_created = True
            self.new_tab_name = new_tab_name
            new_tab_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit#gid={response['replies'][0]['addSheet']['properties']['sheetId']}"
            self.new_sheet_url = new_tab_url

            self.logger.info("="*60)
            self.logger.info(f"✅ NEW TAB READY: {new_tab_url}")
            self.logger.info("="*60)

            return new_tab_name

        except Exception as e:
            self.logger.error(f"Failed to create new tab: {e}")
            import traceback
            traceback.print_exc()
            return None

    def process_row_hybrid(self, row_data: Dict[str, str], row_index: int) -> Dict[str, str]:
        """
        Process a single row with hybrid AI + enhanced enrichment
        Returns expanded column data for all 59 columns
        """
        self.logger.info(f"Processing row {row_index}: {self._get_display_name(row_data)}")

        start_time = time.time()
        expanded_data = {}

        # === PHASE 1: Traditional Multi-Link Enrichment ===
        self.logger.info(f"[Phase 1] Multi-link scraping and API enrichment...")
        enrichment_result = self.enrichment_engine.enrich_row(row_data, max_links=self.max_links)

        # === PHASE 2: AI Intelligence Analysis ===
        self.logger.info(f"[Phase 2] AI-powered intelligence analysis...")
        ai_result = None
        try:
            # Combine all scraped content for AI analysis
            combined_content = ""
            for link_num in range(1, 6):
                # link_data uses integer keys
                if link_num in enrichment_result['link_data']:
                    link_info = enrichment_result['link_data'][link_num]
                    combined_content += f"\n\n=== {link_info['url']} ===\n{link_info['summary']}"

            # Run AI analysis
            if combined_content.strip():
                ai_result = self.ai_enricher.analyze_company_content(
                    content=combined_content[:10000],  # Limit to 10k chars
                    company_name=row_data.get('organization_name', row_data.get('company', 'Unknown'))
                )
        except Exception as e:
            self.logger.warning(f"AI analysis failed: {e}")
            ai_result = None

        # === BUILD 59-COLUMN OUTPUT ===

        # Column 1: Row Key
        expanded_data[f"{ENRICH_PREFIX}Row Key"] = self._get_row_key(row_data, row_index)

        # Columns 2-16: Link 1-5 (3 columns each)
        for link_num in range(1, 6):
            prefix = f"{ENRICH_PREFIX}Link {link_num}"

            # link_data uses integer keys, not string keys
            if link_num in enrichment_result['link_data']:
                link_info = enrichment_result['link_data'][link_num]
                expanded_data[prefix] = link_info['url']
                expanded_data[f"{prefix} - Summary"] = link_info['summary']
                expanded_data[f"{prefix} - JSON"] = json.dumps(link_info.get('extracted_data', {}), indent=2)
            else:
                expanded_data[prefix] = ""
                expanded_data[f"{prefix} - Summary"] = ""
                expanded_data[f"{prefix} - JSON"] = ""

        # Columns 17-24: AI Intelligence (8 columns)
        if ai_result and ai_result.get('ai_powered'):
            # AI enricher returns flat dictionary with keys: category, business_model, value_proposition, etc.
            expanded_data[f"{ENRICH_PREFIX}AI: Category"] = ai_result.get('category', '')
            expanded_data[f"{ENRICH_PREFIX}AI: Value Proposition"] = ai_result.get('value_proposition', '')
            expanded_data[f"{ENRICH_PREFIX}AI: Business Model"] = ai_result.get('business_model', '')

            # AI Lead Score - use confidence_score if available
            confidence = ai_result.get('confidence_score', 0)
            expanded_data[f"{ENRICH_PREFIX}AI: Lead Score"] = str(int(confidence * 100)) if confidence else '0'

            # Priority based on commercial readiness
            commercial = ai_result.get('commercial_readiness', '').lower()
            if 'high' in commercial or 'strong' in commercial:
                priority = 'High'
            elif 'low' in commercial or 'weak' in commercial:
                priority = 'Low'
            else:
                priority = 'Medium'
            expanded_data[f"{ENRICH_PREFIX}AI: Priority"] = priority

            # Strengths = differentiators
            differentiators = ai_result.get('differentiators', [])
            expanded_data[f"{ENRICH_PREFIX}AI: Strengths"] = ', '.join(differentiators) if differentiators else ''

            # Actions = suggested next steps based on target market
            target_market = ai_result.get('target_market', '')
            expanded_data[f"{ENRICH_PREFIX}AI: Actions"] = f"Target: {target_market}" if target_market else ''

            # Report = analysis summary
            expanded_data[f"{ENRICH_PREFIX}AI: Report"] = ai_result.get('analysis_summary', '')

            # Set AI confidence
            expanded_data[f"{ENRICH_PREFIX}AI Confidence"] = f"{int(confidence * 100)}%" if confidence else '0%'
        else:
            # Empty AI columns if AI failed
            for col in ['AI: Category', 'AI: Value Proposition', 'AI: Business Model',
                       'AI: Lead Score', 'AI: Priority', 'AI: Strengths', 'AI: Actions', 'AI: Report']:
                expanded_data[f"{ENRICH_PREFIX}{col}"] = ""

        # Columns 25-27: Traditional Lead Scoring
        expanded_data[f"{ENRICH_PREFIX}Lead Score"] = str(enrichment_result['lead_score'])
        expanded_data[f"{ENRICH_PREFIX}Lead Tags"] = enrichment_result['lead_tags']
        expanded_data[f"{ENRICH_PREFIX}Complete Context"] = enrichment_result['complete_context']

        # Columns 28-42: API Enrichment (15 columns)

        # Gender API (3 columns)
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

        # Email API (3 columns)
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

        # GitHub API (4 columns)
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

        # Google Search API (3 columns)
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

        # LinkedIn API (3 columns)
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

        # Columns 43-48: Score Breakdown (6 columns)
        score_breakdown = enrichment_result.get('score_breakdown', {})
        expanded_data[f"{ENRICH_PREFIX}Role Score"] = f"{score_breakdown.get('role_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}Company Fit Score"] = f"{score_breakdown.get('company_fit_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}Engagement Score"] = f"{score_breakdown.get('engagement_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}Contactability Score"] = f"{score_breakdown.get('contactability_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}Tech Fit Score"] = f"{score_breakdown.get('tech_fit_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}Recency Score"] = f"{score_breakdown.get('recency_score', 0):.1f}"

        # Columns 49-52: Processing Metadata (4 columns)
        # AI Confidence already set above in AI section

        processing_time_ms = int((time.time() - start_time) * 1000)
        expanded_data[f"{ENRICH_PREFIX}Processing Time (ms)"] = str(processing_time_ms)
        expanded_data[f"{ENRICH_PREFIX}Last Enriched"] = datetime.now(timezone.utc).isoformat()

        # Status: OK if AI worked and lead score >= 30
        ai_success = ai_result and ai_result.get('ai_powered')
        score_ok = enrichment_result['lead_score'] >= 30
        expanded_data[f"{ENRICH_PREFIX}Status"] = 'OK' if (ai_success and score_ok) else 'PARTIAL'

        return expanded_data

    def process_sheet(self, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """Process sheet with hybrid enrichment and auto sheet creation"""
        if not self.service:
            if not self.authenticate():
                raise Exception("Authentication failed")

        self.logger.info("="*60)
        self.logger.info("🤖🦈 HYBRID AI + ENHANCED ENRICHMENT STARTING")
        self.logger.info("="*60)

        # Read original sheet data
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.original_sheet_id,
            range=f'{self.tab_name}!A:ZZ'
        ).execute()

        values = result.get('values', [])
        if not values:
            self.logger.error("No data found in sheet")
            return {}

        headers = values[0]
        rows = values[1:]

        if max_rows:
            rows = rows[:max_rows]

        # Add enrichment columns to main tab (or create new tab if auto_create_sheet is True)
        if self.auto_create_sheet:
            # Create new tab mode
            new_tab_name = self.create_new_tab_with_essential_data(headers)
            if not new_tab_name:
                self.logger.error("Failed to create new tab, aborting")
                return {}

            # Get essential column count from new tab
            new_sheet_result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f"'{new_tab_name}'!1:1"
            ).execute()
            new_headers = new_sheet_result.get('values', [[]])[0]
            essential_col_count = len(new_headers) - len(HYBRID_ENRICHMENT_HEADERS)
            self.logger.info(f"Essential columns in new tab: {essential_col_count}")
            target_tab = new_tab_name
        else:
            # Main tab mode - add enrichment columns to existing tab
            if not self.add_enrichment_columns_to_tab(self.tab_name, headers):
                self.logger.error("Failed to add enrichment columns, aborting")
                return {}

            # Count only non-enrichment columns (original data columns)
            essential_col_count = len([h for h in headers if not h.startswith(ENRICH_PREFIX)])
            self.logger.info(f"Original data columns: {essential_col_count}")
            self.logger.info(f"Total columns (with enrichment): {len(headers)}")
            target_tab = self.tab_name

        stats = {'processed': 0, 'success': 0, 'partial': 0, 'failed': 0}
        enriched_rows = []

        # Process each row
        for idx, row in enumerate(rows, start=1):
            try:
                # Convert row to dict
                row_data = dict(zip(headers, row + [''] * (len(headers) - len(row))))

                # Process with hybrid enrichment
                expanded_data = self.process_row_hybrid(row_data, idx)

                # Convert dict to list for writing
                enriched_values = [expanded_data.get(header, '') for header in HYBRID_ENRICHMENT_HEADERS]
                enriched_rows.append(enriched_values)

                stats['processed'] += 1
                if expanded_data[f"{ENRICH_PREFIX}Status"] == 'OK':
                    stats['success'] += 1
                else:
                    stats['partial'] += 1

            except Exception as e:
                self.logger.error(f"Error processing row {idx}: {e}")
                stats['failed'] += 1
                # Add empty row to maintain alignment
                enriched_rows.append([''] * len(HYBRID_ENRICHMENT_HEADERS))

        # Write enriched data to target tab
        if not self.dry_run and enriched_rows:
            try:
                # Calculate start column (after existing columns)
                start_col = self._col_to_letter(essential_col_count + 1)
                end_col = self._col_to_letter(essential_col_count + len(HYBRID_ENRICHMENT_HEADERS))

                self.logger.info(f"Writing {len(enriched_rows)} enriched rows to columns {start_col}-{end_col}...")

                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=f"'{target_tab}'!{start_col}2:{end_col}{len(enriched_rows) + 1}",
                    valueInputOption='RAW',
                    body={'values': enriched_rows}
                ).execute()

                self.logger.info(f"✅ Wrote enrichment data to tab '{target_tab}'")

            except Exception as e:
                self.logger.error(f"Failed to write enriched data: {e}")

        self.logger.info("="*60)
        self.logger.info("🤖🦈 HYBRID ENRICHMENT COMPLETE")
        self.logger.info(f"Processed: {stats['processed']}, Success: {stats['success']}, Partial: {stats['partial']}, Failed: {stats['failed']}")
        if self.auto_create_sheet and self.new_sheet_created:
            self.logger.info(f"📊 New tab: {self.new_sheet_url}")
        else:
            self.logger.info(f"📊 Updated main tab: '{self.tab_name}'")
        self.logger.info("="*60)

        return stats

    def _get_display_name(self, row_data: Dict[str, str]) -> str:
        """Get display name for logging"""
        name = row_data.get('name', row_data.get('first_name', ''))
        company = row_data.get('organization_name', row_data.get('company', ''))
        return f"{name} @ {company}" if name and company else name or company or "Unknown"

    def _get_row_key(self, row_data: Dict[str, str], row_index: int) -> str:
        """Generate stable row key"""
        # Try LinkedIn URL first
        linkedin = row_data.get('linkedin_url', '')
        if linkedin:
            return f"linkedin:{linkedin}"

        # Try email
        email = row_data.get('email', '')
        if email:
            return f"email:{email}"

        # Fallback to index
        return f"row:{row_index}"

    def _col_to_letter(self, col_index: int) -> str:
        """Convert column index (1-based) to letter(s)"""
        result = ""
        while col_index > 0:
            col_index -= 1
            result = chr(col_index % 26 + 65) + result
            col_index //= 26
        return result


def main():
    """Main entry point for testing"""
    import argparse

    parser = argparse.ArgumentParser(description='Hybrid AI + Enhanced Enricher')
    parser.add_argument('--sheet-id', required=True, help='Google Sheet ID')
    parser.add_argument('--max-rows', type=int, help='Max rows to process')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    args = parser.parse_args()

    enricher = HybridAIEnhancedEnricher(
        sheet_id=args.sheet_id,
        dry_run=args.dry_run,
        max_links=5
    )

    enricher.process_sheet(max_rows=args.max_rows)


if __name__ == "__main__":
    main()
