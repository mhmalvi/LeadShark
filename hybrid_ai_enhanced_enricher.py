#!/usr/bin/env python3
"""
🤖🦈 Hybrid AI + Enhanced Multi-Link Enricher (v5.1 - Sequential Email Sequences!)
Combines AI-powered intelligence with comprehensive multi-link scraping + cold outreach + email sequences

Features:
- AI-powered analysis (Anthropic Claude + OpenAI GPT for both intelligence & email sequences)
- Multi-link scraping (5 links × 3 columns each)
- Comprehensive API enrichment (5 APIs)
- Advanced lead scoring (6-factor breakdown + AI score + owner/founder boost)
- Enhanced email finding (pattern generation + multi-service verification)
- Cold outreach personalization (recent activity, pain points, trigger events)
- Email component generation (subject lines, opening lines, value props, CTAs)
- AI Email Sequences (5-email cadence with GPT-4o-mini personalized content) **NEW v5.1**
- 85 total enrichment columns (UPGRADED from 70)
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
from data_enrichment import enrich_gender, enrich_email_verification, DataEnrichment
from cold_outreach_engine import ColdOutreachEngine
from ai_email_sequence_generator import AIEmailSequenceGenerator

# Constants
PROCESSOR_VERSION = "v5.1-Sequential-Email-Sequences"
SCHEMA_VERSION = "S-EmailSequences-5.1"
ENRICH_PREFIX = "Enrich::"

# Hybrid enrichment headers (85 columns total - UPGRADED from 70 with Email Sequences!)
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
    f"{ENRICH_PREFIX}🤖 AI Category",
    f"{ENRICH_PREFIX}🤖 AI Value Proposition",
    f"{ENRICH_PREFIX}🤖 AI Business Model",
    f"{ENRICH_PREFIX}🤖 AI Lead Score",
    f"{ENRICH_PREFIX}🤖 AI Priority Level",
    f"{ENRICH_PREFIX}🤖 AI Key Strengths",
    f"{ENRICH_PREFIX}🤖 AI Recommended Actions",
    f"{ENRICH_PREFIX}🤖 AI Full Report",

    # === LEAD SCORING (3 columns) ===
    f"{ENRICH_PREFIX}🎯 Lead Score (0-100)",
    f"{ENRICH_PREFIX}🎯 Lead Tag (Hot/Warm/Cold)",
    f"{ENRICH_PREFIX}📋 Complete Context",

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

    # === ENHANCED EMAIL ENRICHMENT (4 columns) === NEW v5.0!
    f"{ENRICH_PREFIX}📧 Email Variants (Generated)",
    f"{ENRICH_PREFIX}📧 Best Email Found",
    f"{ENRICH_PREFIX}📧 Email Confidence (0-100)",
    f"{ENRICH_PREFIX}📧 Email Source",

    # === COLD OUTREACH PERSONALIZATION (5 columns) === NEW v5.0!
    f"{ENRICH_PREFIX}📰 Recent Activity/News",
    f"{ENRICH_PREFIX}🎯 Pain Points (AI-Detected)",
    f"{ENRICH_PREFIX}💬 Personalization Hook",
    f"{ENRICH_PREFIX}⭐ Social Proof",
    f"{ENRICH_PREFIX}🚀 Trigger Event",

    # === COLD EMAIL COMPONENTS (6 columns) === NEW v5.0!
    f"{ENRICH_PREFIX}✉️ Subject Line #1 (Question)",
    f"{ENRICH_PREFIX}✉️ Subject Line #2 (Activity)",
    f"{ENRICH_PREFIX}✉️ Subject Line #3 (Value)",
    f"{ENRICH_PREFIX}✉️ Opening Line",
    f"{ENRICH_PREFIX}✉️ Value Proposition",
    f"{ENRICH_PREFIX}✉️ Call-to-Action",

    # === AI EMAIL SEQUENCE (15 columns) === NEW v5.1!
    # Email 1: Initial Outreach (Day 1)
    f"{ENRICH_PREFIX}📨 Email 1 - Subject",
    f"{ENRICH_PREFIX}📨 Email 1 - Body",
    f"{ENRICH_PREFIX}📨 Email 1 - Timing",
    # Email 2: Value Add (Day 3)
    f"{ENRICH_PREFIX}📨 Email 2 - Subject",
    f"{ENRICH_PREFIX}📨 Email 2 - Body",
    f"{ENRICH_PREFIX}📨 Email 2 - Timing",
    # Email 3: Social Proof (Day 7)
    f"{ENRICH_PREFIX}📨 Email 3 - Subject",
    f"{ENRICH_PREFIX}📨 Email 3 - Body",
    f"{ENRICH_PREFIX}📨 Email 3 - Timing",
    # Email 4: Direct Ask (Day 10)
    f"{ENRICH_PREFIX}📨 Email 4 - Subject",
    f"{ENRICH_PREFIX}📨 Email 4 - Body",
    f"{ENRICH_PREFIX}📨 Email 4 - Timing",
    # Email 5: Break-up (Day 14)
    f"{ENRICH_PREFIX}📨 Email 5 - Subject",
    f"{ENRICH_PREFIX}📨 Email 5 - Body",
    f"{ENRICH_PREFIX}📨 Email 5 - Timing",

    # === SCORE BREAKDOWN (6 columns) ===
    f"{ENRICH_PREFIX}📊 Role Score (30%)",
    f"{ENRICH_PREFIX}📊 Company Fit Score (25%)",
    f"{ENRICH_PREFIX}📊 Engagement Score (15%)",
    f"{ENRICH_PREFIX}📊 Contactability Score (10%)",
    f"{ENRICH_PREFIX}📊 Tech Fit Score (10%)",
    f"{ENRICH_PREFIX}📊 Recency Score (10%)",

    # === PROCESSING METADATA (6 columns) === UPDATED v5.1!
    f"{ENRICH_PREFIX}⚙️ AI Confidence Level",
    f"{ENRICH_PREFIX}⚙️ Processing Time (seconds)",
    f"{ENRICH_PREFIX}⚙️ Last Enriched",
    f"{ENRICH_PREFIX}⚙️ Email Sequence Status",
    f"{ENRICH_PREFIX}⚙️ Email Sequence Generated At",
    f"{ENRICH_PREFIX}⚙️ Status",
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

    Features (v5.1 - Sequential Email Sequences):
    - AI-powered company analysis (Anthropic Claude + OpenAI GPT)
    - Multi-link scraping (5 links with summaries and JSON)
    - 5 API integrations (Gender, Email, GitHub, Google, LinkedIn)
    - Advanced lead scoring (traditional + AI) with owner/partner detection
    - Enhanced email finding (pattern generation + multi-service verification)
    - Cold outreach personalization (recent activity, pain points, trigger events)
    - Email component generation (subject lines, opening lines, CTAs)
    - AI Email Sequences (5-email personalized cadence) **NEW v5.1**
    - 85 total enrichment columns (UPGRADED from 70)
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
        self.data_enrichment = DataEnrichment()  # NEW: For enhanced email finding
        self.cold_outreach = ColdOutreachEngine()  # NEW: For cold outreach components
        self.email_sequence_generator = AIEmailSequenceGenerator()  # NEW v5.1: For AI email sequences

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
                self.logger.info("⚠️  Enrichment columns already exist, checking if headers need update...")

                # Check if we have the new v5.0 headers (with emojis)
                has_v5_headers = any('📧' in header or '🤖' in header or '🎯' in header for header in existing_headers)

                if not has_v5_headers:
                    self.logger.info("🔄 Updating to v5.0 headers (53 → 80 columns)...")

                    # Get sheet metadata to expand columns if needed
                    sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
                    sheets = sheet_metadata.get('sheets', [])

                    target_sheet = None
                    for sheet in sheets:
                        if sheet['properties']['title'] == tab_name:
                            target_sheet = sheet
                            break

                    if target_sheet:
                        sheet_id = target_sheet['properties']['sheetId']
                        current_cols = target_sheet['properties']['gridProperties']['columnCount']
                        required_cols = len(existing_headers) - len([h for h in existing_headers if h.startswith(ENRICH_PREFIX)]) + len(HYBRID_ENRICHMENT_HEADERS)

                        # Expand columns if needed (80 new vs 53 old = 27 more columns)
                        if required_cols > current_cols:
                            self.logger.info(f"📏 Expanding sheet from {current_cols} to {required_cols} columns...")
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

                    # Find where enrichment columns start
                    enrich_start_idx = next((i for i, h in enumerate(existing_headers) if h.startswith(ENRICH_PREFIX)), len(existing_headers))

                    # Update the headers
                    start_col = self._col_to_letter(enrich_start_idx + 1)
                    end_col = self._col_to_letter(enrich_start_idx + len(HYBRID_ENRICHMENT_HEADERS))

                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.sheet_id,
                        range=f"'{tab_name}'!{start_col}1:{end_col}1",
                        valueInputOption='RAW',
                        body={'values': [HYBRID_ENRICHMENT_HEADERS]}
                    ).execute()

                    self.logger.info(f"✅ Updated {len(HYBRID_ENRICHMENT_HEADERS)} column headers to v5.0 format")
                    self.logger.info(f"📊 New headers include: Email enrichment (4), Personalization (5), Email components (6)")
                else:
                    self.logger.info("✅ Already has v5.0 headers")

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
        Create a new TAB within the existing sheet with essential data columns + 80 enrichment columns (v5.0)
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
        Process a single row with hybrid AI + enhanced enrichment + cold outreach + email sequences
        Returns expanded column data for all 85 columns (UPGRADED from 70)
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

            # Run AI analysis (with timeout protection)
            if combined_content.strip():
                self.logger.info(f"[Phase 2] Calling AI enricher with {len(combined_content)} chars of content...")
                ai_result = self.ai_enricher.analyze_company_content(
                    content=combined_content[:10000],  # Limit to 10k chars
                    company_name=row_data.get('organization_name', row_data.get('company', 'Unknown'))
                )
                self.logger.info(f"[Phase 2] AI analysis complete")
            else:
                self.logger.warning(f"[Phase 2] No content available for AI analysis, skipping...")
        except Exception as e:
            self.logger.warning(f"[Phase 2] AI analysis failed: {e}")
            ai_result = None

        # === PHASE 3: Enhanced Email Finding (NEW!) ===
        self.logger.info(f"[Phase 3] Enhanced email finding and verification...")
        email_result = None
        try:
            # Extract domain from company website
            domain = self._extract_domain(row_data)
            first_name = row_data.get('first_name', row_data.get('First Name', ''))
            last_name = row_data.get('last_name', row_data.get('Last Name', ''))

            # Extract from full name if first/last not available
            if not first_name or not last_name:
                full_name = row_data.get('name', row_data.get('Name', ''))
                if full_name:
                    parts = full_name.split()
                    if len(parts) >= 2:
                        first_name = parts[0]
                        last_name = parts[-1]

            if first_name and last_name and domain:
                self.logger.info(f"[Phase 3] Finding emails for {first_name} {last_name} @ {domain}")
                email_result = self.data_enrichment.find_and_verify_emails(
                    first_name=first_name,
                    last_name=last_name,
                    domain=domain,
                    scraped_content=combined_content,
                    provided_email=row_data.get('email', row_data.get('Email', ''))
                )
                self.logger.info(f"[Phase 3] Email finding complete: {email_result.get('best_email', 'none found')}")
            else:
                self.logger.warning(f"[Phase 3] Missing required data (first:{first_name}, last:{last_name}, domain:{domain}), skipping...")
        except Exception as e:
            self.logger.warning(f"[Phase 3] Enhanced email finding failed: {e}")
            email_result = None

        # === PHASE 4: Cold Outreach Components (NEW!) ===
        self.logger.info(f"[Phase 4] Cold outreach personalization and email components...")
        outreach_result = None
        try:
            person_name = row_data.get('name', row_data.get('Name', ''))
            company_name = row_data.get('organization_name', row_data.get('company', row_data.get('Company', '')))
            industry = row_data.get('industry', row_data.get('Industry', ''))

            # Get title from enrichment or row data
            title = row_data.get('title', row_data.get('Title', ''))

            if person_name and company_name and combined_content:
                self.logger.info(f"[Phase 4] Generating cold outreach for {person_name} @ {company_name}")
                outreach_result = self.cold_outreach.generate_complete_email_components(
                    person_name=person_name,
                    company_name=company_name,
                    industry=industry or 'company',
                    scraped_content=combined_content,
                    product_category="solution"
                )
                self.logger.info(f"[Phase 4] Cold outreach generation complete")
            else:
                self.logger.warning(f"[Phase 4] Missing required data, skipping cold outreach generation...")
        except Exception as e:
            self.logger.warning(f"[Phase 4] Cold outreach generation failed: {e}")
            outreach_result = None

        # === PHASE 5: AI Email Sequence Generation (NEW v5.1!) ===
        self.logger.info(f"[Phase 5] AI-powered email sequence generation...")
        email_sequence = None
        try:
            person_name = row_data.get('name', row_data.get('Name', ''))
            company_name = row_data.get('organization_name', row_data.get('company', row_data.get('Company', '')))
            title = row_data.get('title', row_data.get('Title', ''))
            industry = row_data.get('industry', row_data.get('Industry', ''))

            # Extract linkedin_data before using it
            linkedin_data = enrichment_result['api_enrichment'].get('linkedin', {})

            # Only generate if we have AI client and minimum required data
            if self.email_sequence_generator.client and person_name and company_name:
                # Build comprehensive lead data from all phases
                lead_data = {
                    'name': person_name,
                    'company': company_name,
                    'title': title,
                    'industry': industry,
                    'linkedin_headline': linkedin_data.get('data', {}).get('headline', '') if linkedin_data else '',
                    'linkedin_company': linkedin_data.get('data', {}).get('current_company', '') if linkedin_data else '',
                    'linkedin_experience': str(linkedin_data.get('data', {}).get('experience', [])) if linkedin_data else '',
                    'recent_activity': outreach_result.get('recent_activity', '') if outreach_result else '',
                    'pain_points': outreach_result.get('pain_points', '') if outreach_result else '',
                    'trigger_events': outreach_result.get('trigger_event', '') if outreach_result else '',
                    'social_proof': outreach_result.get('social_proof', '') if outreach_result else '',
                    'lead_score': enrichment_result['lead_score'],
                    'ai_category': ai_result.get('category', '') if ai_result else '',
                    'ai_value_proposition': ai_result.get('value_proposition', '') if ai_result else '',
                    # Add scraped content for hook extraction
                    'scraped_content': enrichment_result.get('scraped_content', ''),
                    'website_summary': enrichment_result.get('website_summary', '')
                }

                # Default sender info (can be configured)
                sender_info = {
                    'name': 'Your Name',
                    'company': 'Your Company',
                    'title': 'Your Title',
                    'value_proposition': 'We help companies grow'
                }

                # Default product info (can be configured)
                product_info = {
                    'name': 'Our Solution',
                    'category': 'software',
                    'key_benefit': 'efficiency and growth',
                    'target_industries': [industry] if industry else []
                }

                self.logger.info(f"[Phase 5] Generating 5-email sequence for {person_name} @ {company_name}")
                email_sequence = self.email_sequence_generator.generate_complete_sequence(
                    lead_data=lead_data,
                    sender_info=sender_info,
                    product_info=product_info
                )
                self.logger.info(f"[Phase 5] Email sequence generation complete")
            else:
                if not self.email_sequence_generator.client:
                    self.logger.warning(f"[Phase 5] OpenAI API key not set (OPENAI_API_KEY), skipping email sequence generation")
                else:
                    self.logger.warning(f"[Phase 5] Missing required data (name:{person_name}, company:{company_name}), skipping...")
        except Exception as e:
            self.logger.warning(f"[Phase 5] Email sequence generation failed: {e}")
            email_sequence = None

        # === BUILD 97-COLUMN OUTPUT ===

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
            expanded_data[f"{ENRICH_PREFIX}🤖 AI Category"] = ai_result.get('category', '')
            expanded_data[f"{ENRICH_PREFIX}🤖 AI Value Proposition"] = ai_result.get('value_proposition', '')
            expanded_data[f"{ENRICH_PREFIX}🤖 AI Business Model"] = ai_result.get('business_model', '')

            # AI Lead Score - use confidence_score if available
            confidence = ai_result.get('confidence_score', 0)
            expanded_data[f"{ENRICH_PREFIX}🤖 AI Lead Score"] = str(int(confidence * 100)) if confidence else '0'

            # Priority based on commercial readiness
            commercial = ai_result.get('commercial_readiness', '').lower()
            if 'high' in commercial or 'strong' in commercial:
                priority = 'High'
            elif 'low' in commercial or 'weak' in commercial:
                priority = 'Low'
            else:
                priority = 'Medium'
            expanded_data[f"{ENRICH_PREFIX}🤖 AI Priority Level"] = priority

            # Strengths = differentiators
            differentiators = ai_result.get('differentiators', [])
            expanded_data[f"{ENRICH_PREFIX}🤖 AI Key Strengths"] = ', '.join(differentiators) if differentiators else ''

            # Actions = suggested next steps based on target market
            target_market = ai_result.get('target_market', '')
            expanded_data[f"{ENRICH_PREFIX}🤖 AI Recommended Actions"] = f"Target: {target_market}" if target_market else ''

            # Report = analysis summary
            expanded_data[f"{ENRICH_PREFIX}🤖 AI Full Report"] = ai_result.get('analysis_summary', '')

            # Set AI confidence
            expanded_data[f"{ENRICH_PREFIX}⚙️ AI Confidence Level"] = f"{int(confidence * 100)}%" if confidence else '0%'
        else:
            # Empty AI columns if AI failed
            for col in ['🤖 AI Category', '🤖 AI Value Proposition', '🤖 AI Business Model',
                       '🤖 AI Lead Score', '🤖 AI Priority Level', '🤖 AI Key Strengths',
                       '🤖 AI Recommended Actions', '🤖 AI Full Report']:
                expanded_data[f"{ENRICH_PREFIX}{col}"] = ""
            expanded_data[f"{ENRICH_PREFIX}⚙️ AI Confidence Level"] = "0%"

        # Columns 25-27: Lead Scoring (3 columns)
        expanded_data[f"{ENRICH_PREFIX}🎯 Lead Score (0-100)"] = str(enrichment_result['lead_score'])
        expanded_data[f"{ENRICH_PREFIX}🎯 Lead Tag (Hot/Warm/Cold)"] = enrichment_result['lead_tags']
        expanded_data[f"{ENRICH_PREFIX}📋 Complete Context"] = enrichment_result['complete_context']

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
            verified = data.get('verified', False)
            status = linkedin_data.get('status', 'Unknown')

            # Build LinkedIn status with enriched data
            status_parts = []
            if verified and status == 'success':
                if data.get('headline'):
                    status_parts.append(data['headline'][:100])
                if data.get('current_company'):
                    status_parts.append(f"@ {data['current_company']}")
                if data.get('connections'):
                    status_parts.append(f"({data['connections']} connections)")

            expanded_data[f"{ENRICH_PREFIX}LinkedIn Verified"] = "Yes" if verified else "No"
            expanded_data[f"{ENRICH_PREFIX}LinkedIn Status"] = " | ".join(status_parts) if status_parts else status.capitalize()
            expanded_data[f"{ENRICH_PREFIX}LinkedIn API Source"] = linkedin_data.get('source', 'Web scraping')
        else:
            expanded_data[f"{ENRICH_PREFIX}LinkedIn Verified"] = ""
            expanded_data[f"{ENRICH_PREFIX}LinkedIn Status"] = ""
            expanded_data[f"{ENRICH_PREFIX}LinkedIn API Source"] = ""

        # === ENHANCED EMAIL ENRICHMENT (4 columns) === NEW v5.0!
        if email_result:
            email_variants = email_result.get('email_variants', [])
            expanded_data[f"{ENRICH_PREFIX}📧 Email Variants (Generated)"] = " | ".join(email_variants[:5]) if email_variants else ""
            expanded_data[f"{ENRICH_PREFIX}📧 Best Email Found"] = email_result.get('best_email', '')
            expanded_data[f"{ENRICH_PREFIX}📧 Email Confidence (0-100)"] = str(email_result.get('confidence_score', 0))
            expanded_data[f"{ENRICH_PREFIX}📧 Email Source"] = email_result.get('source', 'none')
        else:
            expanded_data[f"{ENRICH_PREFIX}📧 Email Variants (Generated)"] = ""
            expanded_data[f"{ENRICH_PREFIX}📧 Best Email Found"] = ""
            expanded_data[f"{ENRICH_PREFIX}📧 Email Confidence (0-100)"] = "0"
            expanded_data[f"{ENRICH_PREFIX}📧 Email Source"] = ""

        # === COLD OUTREACH PERSONALIZATION (5 columns) === NEW v5.0!
        if outreach_result:
            expanded_data[f"{ENRICH_PREFIX}📰 Recent Activity/News"] = outreach_result.get('recent_activity', '')
            expanded_data[f"{ENRICH_PREFIX}🎯 Pain Points (AI-Detected)"] = outreach_result.get('pain_points', '')
            expanded_data[f"{ENRICH_PREFIX}💬 Personalization Hook"] = outreach_result.get('personalization_hook', '')
            expanded_data[f"{ENRICH_PREFIX}⭐ Social Proof"] = outreach_result.get('social_proof', '')
            expanded_data[f"{ENRICH_PREFIX}🚀 Trigger Event"] = outreach_result.get('trigger_event', '')
        else:
            expanded_data[f"{ENRICH_PREFIX}📰 Recent Activity/News"] = ""
            expanded_data[f"{ENRICH_PREFIX}🎯 Pain Points (AI-Detected)"] = ""
            expanded_data[f"{ENRICH_PREFIX}💬 Personalization Hook"] = ""
            expanded_data[f"{ENRICH_PREFIX}⭐ Social Proof"] = ""
            expanded_data[f"{ENRICH_PREFIX}🚀 Trigger Event"] = ""

        # === COLD EMAIL COMPONENTS (6 columns) === NEW v5.0!
        if outreach_result:
            expanded_data[f"{ENRICH_PREFIX}✉️ Subject Line #1 (Question)"] = outreach_result.get('subject_line_1', '')
            expanded_data[f"{ENRICH_PREFIX}✉️ Subject Line #2 (Activity)"] = outreach_result.get('subject_line_2', '')
            expanded_data[f"{ENRICH_PREFIX}✉️ Subject Line #3 (Value)"] = outreach_result.get('subject_line_3', '')
            expanded_data[f"{ENRICH_PREFIX}✉️ Opening Line"] = outreach_result.get('opening_line', '')
            expanded_data[f"{ENRICH_PREFIX}✉️ Value Proposition"] = outreach_result.get('value_prop_match', '')
            expanded_data[f"{ENRICH_PREFIX}✉️ Call-to-Action"] = outreach_result.get('suggested_cta', '')
        else:
            expanded_data[f"{ENRICH_PREFIX}✉️ Subject Line #1 (Question)"] = ""
            expanded_data[f"{ENRICH_PREFIX}✉️ Subject Line #2 (Activity)"] = ""
            expanded_data[f"{ENRICH_PREFIX}✉️ Subject Line #3 (Value)"] = ""
            expanded_data[f"{ENRICH_PREFIX}✉️ Opening Line"] = ""
            expanded_data[f"{ENRICH_PREFIX}✉️ Value Proposition"] = ""
            expanded_data[f"{ENRICH_PREFIX}✉️ Call-to-Action"] = ""

        # === AI EMAIL SEQUENCE (15 columns) === NEW v5.1!
        if email_sequence:
            # Email 1
            email_1 = email_sequence.get('email_1', {})
            expanded_data[f"{ENRICH_PREFIX}📨 Email 1 - Subject"] = email_1.get('subject', '')
            expanded_data[f"{ENRICH_PREFIX}📨 Email 1 - Body"] = email_1.get('body', '')
            expanded_data[f"{ENRICH_PREFIX}📨 Email 1 - Timing"] = email_1.get('timing', '')

            # Email 2
            email_2 = email_sequence.get('email_2', {})
            expanded_data[f"{ENRICH_PREFIX}📨 Email 2 - Subject"] = email_2.get('subject', '')
            expanded_data[f"{ENRICH_PREFIX}📨 Email 2 - Body"] = email_2.get('body', '')
            expanded_data[f"{ENRICH_PREFIX}📨 Email 2 - Timing"] = email_2.get('timing', '')

            # Email 3
            email_3 = email_sequence.get('email_3', {})
            expanded_data[f"{ENRICH_PREFIX}📨 Email 3 - Subject"] = email_3.get('subject', '')
            expanded_data[f"{ENRICH_PREFIX}📨 Email 3 - Body"] = email_3.get('body', '')
            expanded_data[f"{ENRICH_PREFIX}📨 Email 3 - Timing"] = email_3.get('timing', '')

            # Email 4
            email_4 = email_sequence.get('email_4', {})
            expanded_data[f"{ENRICH_PREFIX}📨 Email 4 - Subject"] = email_4.get('subject', '')
            expanded_data[f"{ENRICH_PREFIX}📨 Email 4 - Body"] = email_4.get('body', '')
            expanded_data[f"{ENRICH_PREFIX}📨 Email 4 - Timing"] = email_4.get('timing', '')

            # Email 5
            email_5 = email_sequence.get('email_5', {})
            expanded_data[f"{ENRICH_PREFIX}📨 Email 5 - Subject"] = email_5.get('subject', '')
            expanded_data[f"{ENRICH_PREFIX}📨 Email 5 - Body"] = email_5.get('body', '')
            expanded_data[f"{ENRICH_PREFIX}📨 Email 5 - Timing"] = email_5.get('timing', '')
        else:
            # Empty email sequence columns
            for i in range(1, 6):
                expanded_data[f"{ENRICH_PREFIX}📨 Email {i} - Subject"] = ""
                expanded_data[f"{ENRICH_PREFIX}📨 Email {i} - Body"] = ""
                expanded_data[f"{ENRICH_PREFIX}📨 Email {i} - Timing"] = ""

        # === SCORE BREAKDOWN (6 columns) ===
        score_breakdown = enrichment_result.get('score_breakdown', {})
        expanded_data[f"{ENRICH_PREFIX}📊 Role Score (30%)"] = f"{score_breakdown.get('role_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}📊 Company Fit Score (25%)"] = f"{score_breakdown.get('company_fit_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}📊 Engagement Score (15%)"] = f"{score_breakdown.get('engagement_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}📊 Contactability Score (10%)"] = f"{score_breakdown.get('contactability_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}📊 Tech Fit Score (10%)"] = f"{score_breakdown.get('tech_fit_score', 0):.1f}"
        expanded_data[f"{ENRICH_PREFIX}📊 Recency Score (10%)"] = f"{score_breakdown.get('recency_score', 0):.1f}"

        # === PROCESSING METADATA (6 columns) === UPDATED v5.1!
        # AI Confidence already set above in AI section

        processing_time_sec = round((time.time() - start_time), 2)
        expanded_data[f"{ENRICH_PREFIX}⚙️ Processing Time (seconds)"] = str(processing_time_sec)
        expanded_data[f"{ENRICH_PREFIX}⚙️ Last Enriched"] = datetime.now(timezone.utc).isoformat()

        # Email sequence metadata
        if email_sequence:
            expanded_data[f"{ENRICH_PREFIX}⚙️ Email Sequence Status"] = "Generated"
            expanded_data[f"{ENRICH_PREFIX}⚙️ Email Sequence Generated At"] = datetime.now(timezone.utc).isoformat()
        else:
            expanded_data[f"{ENRICH_PREFIX}⚙️ Email Sequence Status"] = "Not Generated"
            expanded_data[f"{ENRICH_PREFIX}⚙️ Email Sequence Generated At"] = ""

        # Status: OK if AI worked and lead score >= 30
        ai_success = ai_result and ai_result.get('ai_powered')
        score_ok = enrichment_result['lead_score'] >= 30
        expanded_data[f"{ENRICH_PREFIX}⚙️ Status"] = 'OK' if (ai_success and score_ok) else 'PARTIAL'

        return expanded_data

    def process_sheet(self, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """Process sheet with hybrid enrichment and auto sheet creation"""
        if not self.service:
            if not self.authenticate():
                raise Exception("Authentication failed")

        self.logger.info("="*60)
        self.logger.info("🤖🦈 v5.1 SEQUENTIAL EMAIL SEQUENCES ENRICHMENT STARTING")
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

        # Calculate column range for enrichment data (once)
        start_col = self._col_to_letter(essential_col_count + 1)
        end_col = self._col_to_letter(essential_col_count + len(HYBRID_ENRICHMENT_HEADERS))

        # Process each row and write immediately
        for idx, row in enumerate(rows, start=1):
            try:
                # Convert row to dict
                row_data = dict(zip(headers, row + [''] * (len(headers) - len(row))))

                # Process with hybrid enrichment
                expanded_data = self.process_row_hybrid(row_data, idx)

                # Convert dict to list for writing
                enriched_values = [expanded_data.get(header, '') for header in HYBRID_ENRICHMENT_HEADERS]

                # Log completion status
                self.logger.info(f"[Complete] Row {idx} enrichment finished - {len([v for v in enriched_values if v])} columns populated")

                # Write this row immediately (unless dry run)
                if not self.dry_run:
                    row_number = idx + 1  # +1 because row 1 is headers
                    self.logger.info(f"[Writing] Writing row {idx} to sheet range {target_tab}!{start_col}{row_number}:{end_col}{row_number}")
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.sheet_id,
                        range=f"'{target_tab}'!{start_col}{row_number}:{end_col}{row_number}",
                        valueInputOption='RAW',
                        body={'values': [enriched_values]}
                    ).execute()
                    self.logger.info(f"✅ Row {idx} written to sheet successfully!")
                else:
                    self.logger.info(f"[Dry Run] Would write row {idx} to sheet")

                stats['processed'] += 1
                if expanded_data.get(f"{ENRICH_PREFIX}⚙️ Status") == 'OK':
                    stats['success'] += 1
                else:
                    stats['partial'] += 1

            except Exception as e:
                self.logger.error(f"Error processing row {idx}: {e}")
                stats['failed'] += 1
                # Write empty row to maintain alignment
                if not self.dry_run:
                    row_number = idx + 1
                    empty_values = [''] * len(HYBRID_ENRICHMENT_HEADERS)
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.sheet_id,
                        range=f"'{target_tab}'!{start_col}{row_number}:{end_col}{row_number}",
                        valueInputOption='RAW',
                        body={'values': [empty_values]}
                    ).execute()

        self.logger.info("="*60)
        self.logger.info("🤖🦈 v5.0 COLD OUTREACH ENRICHMENT COMPLETE")
        self.logger.info(f"Processed: {stats['processed']}, Success: {stats['success']}, Partial: {stats['partial']}, Failed: {stats['failed']}")
        self.logger.info(f"✅ 80 columns enriched (email finding + cold outreach + AI + scoring)")
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

    def _extract_domain(self, row_data: Dict[str, str]) -> str:
        """Extract domain from website URL"""
        import re

        # Try various website field names
        website_fields = [
            'organization_website_url', 'company_website', 'website',
            'Website', 'url', 'URL', 'organization_primary_domain'
        ]

        website = ""
        for field in website_fields:
            if field in row_data and row_data[field]:
                website = row_data[field]
                break

        if not website:
            return ""

        # Clean domain
        domain = website.lower().strip()
        domain = domain.replace('www.', '')
        domain = re.sub(r'^https?://', '', domain)

        # Extract domain only (remove paths)
        if '/' in domain:
            domain = domain.split('/')[0]

        return domain

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
