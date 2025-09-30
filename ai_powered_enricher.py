#!/usr/bin/env python3
"""
🤖🦈 AI-Powered Lead Enricher
Integrates Anthropic Claude with LeadShark's existing enrichment pipeline
Combines rule-based scraping with AI-powered intelligence analysis
"""

import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import LeadShark core components
from google_sheets_auth import authenticate_google_sheets
from enhanced_scraping_pipeline import EnhancedScrapingPipeline
from data_enrichment import enrich_gender, enrich_email_verification
from anthropic_enrichment import AnthropicEnrichment

# Configuration
PROCESSOR_VERSION = "v3.0-AI"
SCHEMA_VERSION = "AI-1.0"
AI_ENRICHMENT_ENABLED = os.getenv('AI_ENRICHMENT_ENABLED', 'true').lower() == 'true'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('ai_enrichment.log', encoding='utf-8'),
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


class AIPoweredEnricher:
    """
    🤖🦈 LeadShark AI-Powered Enricher

    Combines traditional web scraping and API enrichment with AI-powered
    intelligence analysis using Anthropic Claude.
    """

    def __init__(self, sheet_id: str, tab_name: str = 'Sheet1'):
        """
        Initialize AI-powered enricher

        Args:
            sheet_id: Google Sheet ID
            tab_name: Worksheet name (default: Sheet1)
        """
        self.sheet_id = sheet_id
        self.tab_name = tab_name

        # Google Sheets services
        self.service = None
        self.drive_service = None

        # Core components
        self.scraper = EnhancedScrapingPipeline()

        # AI enrichment (with automatic fallback)
        self.ai_enricher = AnthropicEnrichment() if AI_ENRICHMENT_ENABLED else None

        # Statistics
        self.stats = {
            'rows_processed': 0,
            'ai_enhanced': 0,
            'rule_based_only': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

        logger.info(f"🤖 AI-Powered Enricher initialized (version: {PROCESSOR_VERSION})")
        if self.ai_enricher and self.ai_enricher.is_enabled():
            logger.info(f"✅ AI enrichment enabled (model: {self.ai_enricher.model})")
        else:
            logger.info("⚠️  AI enrichment disabled - using rule-based methods only")

    def authenticate(self) -> bool:
        """Authenticate with Google Sheets API"""
        try:
            logger.info("[AUTH] Authenticating with Google Sheets...")
            result = authenticate_google_sheets()
            if result:
                self.service, self.drive_service, _ = result
                logger.info("[OK] Authentication successful")
                return True
            logger.error("[ERROR] Authentication failed")
            return False
        except Exception as e:
            logger.error(f"[ERROR] Authentication error: {e}")
            return False

    def enrich_row(self, row_data: List[str], headers: List[str]) -> Dict[str, Any]:
        """
        🔍 Enrich a single row with both traditional and AI methods

        Args:
            row_data: List of cell values
            headers: List of column headers

        Returns:
            Dictionary with enrichment results
        """
        # Create row dictionary
        row_dict = {headers[i]: row_data[i] if i < len(row_data) else ''
                   for i in range(len(headers))}

        enrichment = {
            'timestamp': datetime.now().isoformat(),
            'processor_version': PROCESSOR_VERSION,
            'ai_enabled': self.ai_enricher is not None and self.ai_enricher.is_enabled()
        }

        # Extract key fields
        name = row_dict.get('name', row_dict.get('Name', ''))
        email = row_dict.get('email', row_dict.get('Email', ''))
        company_name = row_dict.get('organization_name', row_dict.get('Company', ''))
        website_url = row_dict.get('organization_website_url', row_dict.get('Website', ''))
        linkedin_url = row_dict.get('linkedin_url', row_dict.get('LinkedIn', ''))

        logger.info(f"[ENRICHING] {name} ({company_name})")

        # ========================================
        # Phase 1: Traditional Enrichment
        # ========================================

        # Gender detection
        if name:
            try:
                gender_data = enrich_gender(name)
                enrichment['gender'] = gender_data.get('gender', '')
                enrichment['gender_confidence'] = gender_data.get('probability', 0)
                logger.info(f"  ✓ Gender: {gender_data.get('gender', 'Unknown')}")
            except Exception as e:
                logger.warning(f"  ✗ Gender detection failed: {e}")
                enrichment['gender'] = ''

        # Email verification
        if email:
            try:
                email_data = enrich_email_verification(email)
                enrichment['email_valid'] = email_data.get('deliverable', False)
                enrichment['email_status'] = email_data.get('status', 'Unknown')
                logger.info(f"  ✓ Email: {email_data.get('status', 'Unknown')}")
            except Exception as e:
                logger.warning(f"  ✗ Email verification failed: {e}")
                enrichment['email_valid'] = None

        # Web scraping
        scraped_content = ""
        scraped_metadata = {}

        if website_url:
            try:
                logger.info(f"  → Scraping: {website_url[:50]}...")
                scrape_result = self.scraper.scrape_url_with_retry(website_url)

                if scrape_result.get('status') == 'success':
                    scraped_content = scrape_result.get('content', '')
                    scraped_metadata = scrape_result.get('metadata', {})
                    enrichment['website_scraped'] = True
                    enrichment['website_title'] = scraped_metadata.get('title', '')[:100]
                    logger.info(f"  ✓ Scraped: {len(scraped_content)} chars")
                else:
                    enrichment['website_scraped'] = False
                    enrichment['scrape_error'] = scrape_result.get('error', 'Unknown')
                    logger.warning(f"  ✗ Scraping failed: {scrape_result.get('error', '')}")
            except Exception as e:
                logger.error(f"  ✗ Scraping error: {e}")
                enrichment['website_scraped'] = False

        # ========================================
        # Phase 2: AI-Powered Analysis
        # ========================================

        if self.ai_enricher and self.ai_enricher.is_enabled():
            try:
                logger.info("  🤖 Running AI analysis...")

                # Company content analysis (if we have scraped data)
                if scraped_content and len(scraped_content) > 100:
                    ai_analysis = self.ai_enricher.analyze_company_content(
                        scraped_content,
                        company_name,
                        website_url
                    )

                    if ai_analysis.get('ai_powered'):
                        enrichment['ai_category'] = ai_analysis.get('category', '')
                        enrichment['ai_subcategories'] = ai_analysis.get('subcategories', [])
                        enrichment['ai_value_prop'] = ai_analysis.get('value_proposition', '')
                        enrichment['ai_business_model'] = ai_analysis.get('business_model', '')
                        enrichment['ai_confidence'] = ai_analysis.get('confidence_score', 0)
                        enrichment['ai_summary'] = ai_analysis.get('analysis_summary', '')

                        logger.info(f"  ✓ AI Analysis: {ai_analysis.get('category', 'N/A')} "
                                  f"({ai_analysis.get('confidence_score', 0):.0%} confidence)")
                        self.stats['ai_enhanced'] += 1
                    else:
                        logger.info("  → AI analysis fell back to rule-based")
                        self.stats['rule_based_only'] += 1

                # AI-powered lead scoring
                lead_context = {
                    'name': name,
                    'email': email,
                    'company': company_name,
                    'website': website_url,
                    'linkedin': linkedin_url,
                    'scraped_data': scraped_metadata,
                    'enrichment_data': enrichment
                }

                scoring_result = self.ai_enricher.generate_lead_score_reasoning(lead_context)

                if scoring_result.get('ai_powered'):
                    enrichment['ai_lead_score'] = scoring_result.get('lead_score', 0)
                    enrichment['ai_score_explanation'] = scoring_result.get('score_explanation', '')
                    enrichment['ai_priority'] = scoring_result.get('priority_tier', 'Medium')
                    enrichment['ai_strengths'] = scoring_result.get('strengths', [])
                    enrichment['ai_recommended_actions'] = scoring_result.get('recommended_actions', [])

                    logger.info(f"  ✓ AI Lead Score: {scoring_result.get('lead_score', 0)}/100 "
                              f"({scoring_result.get('priority_tier', 'Medium')} priority)")

                # Generate AI intelligence report
                report = self.ai_enricher.generate_intelligence_report({
                    **row_dict,
                    **enrichment
                })

                enrichment['ai_intelligence_report'] = report
                logger.info("  ✓ AI report generated")

            except Exception as e:
                logger.error(f"  ✗ AI enrichment error: {e}")
                enrichment['ai_error'] = str(e)
                self.stats['rule_based_only'] += 1
        else:
            # No AI available - use rule-based only
            logger.info("  → Rule-based enrichment only")
            enrichment['ai_enabled'] = False
            self.stats['rule_based_only'] += 1

        # ========================================
        # Phase 3: Generate Final Report
        # ========================================

        enrichment['enrichment_status'] = 'completed'
        enrichment['processing_time'] = datetime.now().isoformat()

        return enrichment

    def write_enrichment_to_sheet(self, row_index: int, enrichment_data: Dict[str, Any],
                                  headers: List[str]) -> bool:
        """
        Write enrichment data to sheet

        Args:
            row_index: Row number (0-based)
            enrichment_data: Enrichment dictionary
            headers: Current sheet headers

        Returns:
            True if successful
        """
        try:
            # Find or create enrichment columns
            # Look for existing AI enrichment columns or create after existing data

            base_col = len(headers)  # Start after existing columns

            # Define column structure
            enrichment_columns = [
                'AI: Category',
                'AI: Value Proposition',
                'AI: Business Model',
                'AI: Lead Score',
                'AI: Priority',
                'AI: Strengths',
                'AI: Recommended Actions',
                'AI: Intelligence Report',
                'Gender',
                'Gender Confidence',
                'Email Valid',
                'Website Scraped',
                'AI Confidence',
                'Processing Status',
                'Processor Version'
            ]

            # Prepare values
            values = [
                enrichment_data.get('ai_category', ''),
                enrichment_data.get('ai_value_prop', ''),
                enrichment_data.get('ai_business_model', ''),
                str(enrichment_data.get('ai_lead_score', '')),
                enrichment_data.get('ai_priority', ''),
                ' | '.join(enrichment_data.get('ai_strengths', [])),
                ' | '.join(enrichment_data.get('ai_recommended_actions', [])),
                enrichment_data.get('ai_intelligence_report', ''),
                enrichment_data.get('gender', ''),
                str(enrichment_data.get('gender_confidence', '')),
                str(enrichment_data.get('email_valid', '')),
                str(enrichment_data.get('website_scraped', '')),
                str(enrichment_data.get('ai_confidence', '')),
                enrichment_data.get('enrichment_status', ''),
                enrichment_data.get('processor_version', '')
            ]

            # Write headers if first row
            if row_index == 1:
                self._write_headers(enrichment_columns, base_col)

            # Write row data
            self._write_row_data(row_index, values, base_col)

            return True

        except Exception as e:
            logger.error(f"Failed to write enrichment: {e}")
            return False

    def _write_headers(self, headers: List[str], start_col: int):
        """Write column headers"""
        start_letter = self._index_to_column_letter(start_col)
        end_letter = self._index_to_column_letter(start_col + len(headers) - 1)

        range_name = f"{self.tab_name}!{start_letter}1:{end_letter}1"

        body = {'values': [headers]}

        self.service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        logger.info(f"[WRITE] Created {len(headers)} enrichment columns at {start_letter}")

    def _write_row_data(self, row_index: int, data: List[str], start_col: int):
        """Write row data"""
        sheet_row = row_index + 1
        start_letter = self._index_to_column_letter(start_col)
        end_letter = self._index_to_column_letter(start_col + len(data) - 1)

        range_name = f"{self.tab_name}!{start_letter}{sheet_row}:{end_letter}{sheet_row}"

        body = {'values': [data]}

        self.service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

    def _index_to_column_letter(self, index: int) -> str:
        """Convert column index to letter"""
        result = ""
        while index >= 0:
            result = chr(index % 26 + ord('A')) + result
            index = index // 26 - 1
        return result

    def process_sheet(self, max_rows: Optional[int] = None, start_row: int = 1) -> Dict[str, Any]:
        """
        Process sheet with AI-powered enrichment

        Args:
            max_rows: Maximum rows to process (None for all)
            start_row: Starting row (1-based, row 1 is headers)

        Returns:
            Statistics dictionary
        """
        self.stats['start_time'] = datetime.now()

        logger.info("="*60)
        logger.info("🤖🦈 STARTING AI-POWERED LEAD ENRICHMENT")
        logger.info("="*60)

        # Authenticate
        if not self.authenticate():
            logger.error("Failed to authenticate")
            return self.stats

        try:
            # Get sheet data
            range_name = f"{self.tab_name}!A:ZZ"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()

            sheet_data = result.get('values', [])

            if not sheet_data:
                logger.error("No data found in sheet")
                return self.stats

            headers = sheet_data[0]
            logger.info(f"Found {len(sheet_data)-1} data rows, {len(headers)} columns")

            # Determine range
            end_row = min(len(sheet_data), start_row + max_rows) if max_rows else len(sheet_data)

            logger.info(f"Processing rows {start_row + 1} to {end_row}")

            # Process each row
            for row_index in range(start_row, end_row):
                if row_index >= len(sheet_data):
                    break

                row_data = sheet_data[row_index]

                # Skip empty rows
                if not any(row_data):
                    continue

                logger.info(f"\n[ROW {row_index + 1}] Processing...")

                # Enrich row
                enrichment_data = self.enrich_row(row_data, headers)

                # Write to sheet
                self.write_enrichment_to_sheet(row_index, enrichment_data, headers)

                self.stats['rows_processed'] += 1

                # Respectful delay
                time.sleep(2.0)

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.stats['errors'] += 1

        # Final stats
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        logger.info("\n" + "="*60)
        logger.info("🤖🦈 AI-POWERED ENRICHMENT COMPLETE")
        logger.info("="*60)
        logger.info(f"Rows processed: {self.stats['rows_processed']}")
        logger.info(f"AI-enhanced: {self.stats['ai_enhanced']}")
        logger.info(f"Rule-based only: {self.stats['rule_based_only']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info("="*60)

        # Show AI stats if available
        if self.ai_enricher and self.ai_enricher.is_enabled():
            self.ai_enricher.print_stats()

        return self.stats


# Main execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='🤖🦈 AI-Powered Lead Enricher')
    parser.add_argument('--sheet-id', required=True, help='Google Sheet ID')
    parser.add_argument('--tab', default='Sheet1', help='Worksheet name')
    parser.add_argument('--max-rows', type=int, help='Maximum rows to process')
    parser.add_argument('--start-row', type=int, default=1, help='Starting row (1-based)')
    parser.add_argument('--test', action='store_true', help='Test mode (first 3 rows)')

    args = parser.parse_args()

    # Test mode overrides
    if args.test:
        args.max_rows = 3
        print("🧪 TEST MODE - Processing first 3 rows only")

    # Create enricher
    enricher = AIPoweredEnricher(
        sheet_id=args.sheet_id,
        tab_name=args.tab
    )

    # Run processing
    stats = enricher.process_sheet(
        max_rows=args.max_rows,
        start_row=args.start_row
    )

    print(f"\n✅ Processing complete! Check your Google Sheet for enriched data.")