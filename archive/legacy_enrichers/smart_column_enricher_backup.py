#!/usr/bin/env python3
"""
Smart Column Enricher - Enhanced Data Collection Strategy
Processes multiple links per row with individual columns + combined context + lead scoring
"""

import os
import sys
import json
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import logging

sys.path.append(os.path.dirname(__file__))

from google_sheets_auth import authenticate_google_sheets
from data_enrichment import DataEnrichment
from enhanced_scraping_pipeline import EnhancedScrapingPipeline

# Constants
PROCESSOR_VERSION = "v3.0-SmartColumn"
SCHEMA_VERSION = "S-Smart-1.0"


class LinkTypeClassifier:
    """Classify links by type (LinkedIn, website, Twitter, GitHub, etc.)"""
    
    @staticmethod
    def classify(url: str) -> str:
        """Classify link type by domain/path heuristics"""
        if not url:
            return "unknown"
        
        url_lower = url.lower()
        domain = urlparse(url).netloc.lower()
        
        # Social media platforms
        if "linkedin.com" in domain:
            return "linkedin"
        elif "twitter.com" in domain or "x.com" in domain:
            return "twitter"
        elif "github.com" in domain:
            return "github"
        elif "facebook.com" in domain:
            return "facebook"
        elif "instagram.com" in domain:
            return "instagram"
        elif "tiktok.com" in domain:
            return "tiktok"
        elif "youtube.com" in domain:
            return "youtube"
        
        # Business platforms
        elif "crunchbase.com" in domain:
            return "crunchbase"
        elif "angel.co" in domain or "angellist.com" in domain:
            return "angellist"
        elif "pitchbook.com" in domain:
            return "pitchbook"
        
        # Job platforms
        elif "/jobs" in url_lower or "/careers" in url_lower:
            return "job"
        elif "/contact" in url_lower:
            return "contact"
        
        # Default to generic website
        else:
            return "website"


class EnhancedFieldExtractor:
    """Extract platform-specific fields from scraped content"""
    
    @staticmethod
    def extract_fields(link_type: str, scraped_data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Extract fields based on link type"""
        
        extracted = {
            "source": link_type,
            "url": url,
            "extracted": {
                "title": None,
                "name": None,
                "company": None,
                "location": None,
                "description": None,
                "key_fields": {},
                "contacts": {
                    "emails": [],
                    "phones": []
                },
                "metrics": {
                    "followers": None,
                    "stars": None,
                    "subscribers": None
                },
                "top_items": [],
                "raw_text_snippet": None
            },
            "confidence": 0.0,
            "scrape_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if not scraped_data or scraped_data.get('status') != 'success':
            extracted['confidence'] = 0.0
            return extracted
        
        content = scraped_data.get('content', '')
        meta = scraped_data.get('meta', {})
        
        # Extract title
        extracted['extracted']['title'] = meta.get('title') or scraped_data.get('title')
        
        # Extract description
        extracted['extracted']['description'] = (
            meta.get('description') or 
            meta.get('og:description') or
            content[:300] if content else None
        )
        
        # Extract contacts
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        extracted['extracted']['contacts']['emails'] = list(set(emails))[:5]
        
        phones = re.findall(r'\+?[\d\s\-\(\)]{10,}', content)
        extracted['extracted']['contacts']['phones'] = list(set(phones))[:3]
        
        # Store snippet
        extracted['extracted']['raw_text_snippet'] = content[:500] if content else None
        
        # Confidence based on data richness
        confidence_score = 0.3  # Base score
        if extracted['extracted']['title']: confidence_score += 0.2
        if extracted['extracted']['description']: confidence_score += 0.2
        if extracted['extracted']['contacts']['emails']: confidence_score += 0.2
        if len(content) > 500: confidence_score += 0.1
        
        extracted['confidence'] = min(confidence_score, 1.0)
        
        return extracted


class LeadScorer:
    """Calculate lead score based on weighted factors"""
    
    WEIGHTS = {
        'role_power': 30,        # Role / Decision Power
        'company_fit': 25,       # Company Fit
        'engagement': 15,        # Engagement / Visibility
        'contactability': 15,    # Contactability
        'tech_fit': 10,          # Tech / Product Fit
        'recency': 5             # Recency / Signal Strength
    }
    
    @staticmethod
    def calculate_score(row_data: Dict[str, Any], enriched_links: List[Dict[str, Any]]) -> Tuple[int, str]:
        """Calculate lead score (0-100) and tag (Hot/Warm/Cold/Discard)"""
        
        scores = {
            'role_power': 0.0,
            'company_fit': 0.0,
            'engagement': 0.0,
            'contactability': 0.0,
            'tech_fit': 0.0,
            'recency': 0.0
        }
        
        # Analyze role from LinkedIn data
        linkedin_data = next((link for link in enriched_links if link.get('source') == 'linkedin'), None)
        if linkedin_data:
            title = (linkedin_data.get('extracted', {}).get('title') or '').lower()
            if any(term in title for term in ['ceo', 'cto', 'cfo', 'founder', 'president', 'vp']):
                scores['role_power'] = 1.0
            elif any(term in title for term in ['director', 'head of', 'lead']):
                scores['role_power'] = 0.7
            elif any(term in title for term in ['manager', 'senior']):
                scores['role_power'] = 0.5
        
        # Check contactability
        has_email = any(link.get('extracted', {}).get('contacts', {}).get('emails') for link in enriched_links)
        if has_email:
            scores['contactability'] = 1.0
        
        # Check engagement (social presence)
        social_links = [link for link in enriched_links if link.get('source') in ['twitter', 'linkedin', 'github']]
        if len(social_links) >= 2:
            scores['engagement'] = 0.8
        elif len(social_links) == 1:
            scores['engagement'] = 0.5
        
        # Company fit (has company website)
        has_website = any(link.get('source') == 'website' for link in enriched_links)
        if has_website:
            scores['company_fit'] = 0.7
        
        # Tech fit (has GitHub)
        has_github = any(link.get('source') == 'github' for link in enriched_links)
        if has_github:
            scores['tech_fit'] = 0.8
        
        # Calculate weighted total
        total_score = sum(scores[key] * LeadScorer.WEIGHTS[key] for key in scores)
        total_score = int(round(total_score))
        
        # Determine tag
        if total_score >= 80:
            tag = "🔥 Hot"
        elif total_score >= 60:
            tag = "🟡 Warm"
        elif total_score >= 30:
            tag = "🔵 Cold"
        else:
            tag = "⚫ Discard"
        
        return total_score, tag


class ContextSynthesizer:
    """Synthesize complete context from all link summaries"""
    
    @staticmethod
    def synthesize(row_data: Dict[str, Any], enriched_links: List[Dict[str, Any]]) -> str:
        """Create 3-6 sentence summary from all enriched data"""
        
        sentences = []
        
        # Start with name and role (from LinkedIn)
        linkedin_data = next((link for link in enriched_links if link.get('source') == 'linkedin'), None)
        if linkedin_data:
            name = row_data.get('name', row_data.get('first_name', ''))
            title = linkedin_data.get('extracted', {}).get('title')
            location = linkedin_data.get('extracted', {}).get('location')
            
            intro = f"{name}"
            if title:
                intro += f" is {title}"
            if location:
                intro += f", based in {location}"
            sentences.append(intro + ".")
        
        # Add company info (from website)
        website_data = next((link for link in enriched_links if link.get('source') == 'website'), None)
        if website_data:
            company = row_data.get('organization_name', '')
            description = website_data.get('extracted', {}).get('description', '')
            if company and description:
                sentences.append(f"{company}: {description[:150]}.")
        
        # Add contact info
        all_emails = []
        for link in enriched_links:
            emails = link.get('extracted', {}).get('contacts', {}).get('emails', [])
            all_emails.extend(emails)
        
        if all_emails:
            sentences.append(f"Contact: {all_emails[0]}.")
        
        # Add social presence
        twitter_data = next((link for link in enriched_links if link.get('source') == 'twitter'), None)
        if twitter_data:
            sentences.append("Active on social media.")
        
        # Combine
        if sentences:
            return " ".join(sentences)
        else:
            return "Limited data available."


class SmartColumnEnricher:
    """Enhanced enricher that creates individual columns per link + combined context"""
    
    def __init__(self, sheet_id: str, dry_run: bool = False):
        self.sheet_id = sheet_id
        self.dry_run = dry_run
        self.service = None
        self.drive_service = None
        self.scraper = EnhancedScrapingPipeline()
        self.classifier = LinkTypeClassifier()
        self.extractor = EnhancedFieldExtractor()
        self.scorer = LeadScorer()
        self.synthesizer = ContextSynthesizer()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('smart_column_enricher.log'),
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
    
    def find_link_columns(self, headers: List[str]) -> List[int]:
        """Find columns that contain URLs"""
        link_columns = []
        url_keywords = ['url', 'link', 'website', 'linkedin', 'twitter', 'github', 'facebook']
        
        for idx, header in enumerate(headers):
            header_lower = header.lower()
            if any(keyword in header_lower for keyword in url_keywords):
                link_columns.append(idx)
        
        return link_columns
    
    def extract_links_from_row(self, row: List[str], link_columns: List[int]) -> List[Tuple[str, int]]:
        """Extract URLs from specific columns in a row"""
        links = []
        for col_idx in link_columns:
            if col_idx < len(row):
                cell_value = row[col_idx]
                if cell_value and ('http://' in cell_value or 'https://' in cell_value):
                    links.append((cell_value, col_idx))
        return links
    
    def _ensure_enrichment_columns(self, headers: List[str]) -> Tuple[int, int, int, int]:
        """Ensure enrichment columns exist and return their indices"""
        # Column names
        col_lead_score = "Enrich:LeadScore"
        col_lead_tag = "Enrich:LeadTag"
        col_context = "Enrich:Context"
        col_enriched_data = "Enrich:EnrichedData_JSON"

        # Find or add columns
        score_idx = headers.index(col_lead_score) if col_lead_score in headers else len(headers)
        tag_idx = headers.index(col_lead_tag) if col_lead_tag in headers else len(headers) + 1
        context_idx = headers.index(col_context) if col_context in headers else len(headers) + 2
        data_idx = headers.index(col_enriched_data) if col_enriched_data in headers else len(headers) + 3

        # Add headers if needed
        if col_lead_score not in headers:
            headers.extend([col_lead_score, col_lead_tag, col_context, col_enriched_data])
            if not self.dry_run:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range='A1',
                    valueInputOption='RAW',
                    body={'values': [headers]}
                ).execute()
                self.logger.info("Added enrichment columns to sheet")

        return score_idx, tag_idx, context_idx, data_idx

    def _clean_context(self, context: str) -> str:
        """Remove binary/garbage characters from context"""
        # Replace common binary characters with empty string
        import re
        cleaned = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f\ufffd]', '', context)
        # Remove multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    def process_sheet(self, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """Process sheet with smart column enrichment"""
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
            # Read sheet data
            sheet_data = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='A1:Z10000'
            ).execute()

            values = sheet_data.get('values', [])
            if not values:
                self.logger.error("No data found in sheet")
                return stats

            headers = values[0][:]  # Make a copy
            link_columns = self.find_link_columns(headers)

            if not link_columns:
                self.logger.error("No link columns found in sheet")
                return stats

            self.logger.info(f"Found {len(link_columns)} link columns: {[headers[i] for i in link_columns]}")

            # Ensure enrichment columns exist
            score_idx, tag_idx, context_idx, data_idx = self._ensure_enrichment_columns(headers)

            # Process rows
            rows_to_process = values[1:max_rows+1] if max_rows else values[1:]
            updates = []  # Batch updates

            for row_idx, row in enumerate(rows_to_process, start=2):
                stats['rows_attempted'] += 1

                # Ensure row has enough columns
                while len(row) < len(headers):
                    row.append('')

                # Extract links
                links = self.extract_links_from_row(row, link_columns)

                if not links:
                    self.logger.info(f"Row {row_idx}: No links found, skipping")
                    continue

                # Enrich each link
                enriched_links = []
                for url, col_idx in links:
                    link_type = self.classifier.classify(url)
                    self.logger.info(f"Row {row_idx}: Processing {link_type} link: {url}")

                    # Scrape
                    scraped_data = self.scraper.scrape_url(url)

                    # Extract fields
                    enriched_data = self.extractor.extract_fields(link_type, scraped_data, url)
                    enriched_links.append(enriched_data)

                # Build row data dict
                row_data = {headers[i]: row[i] if i < len(row) else '' for i in range(len(headers))}

                # Calculate lead score
                score, tag = self.scorer.calculate_score(row_data, enriched_links)

                # Synthesize context
                context = self.synthesizer.synthesize(row_data, enriched_links)
                context = self._clean_context(context)

                # Create JSON data
                enriched_json = json.dumps({
                    'lead_score': score,
                    'lead_tag': tag,
                    'links_processed': len(enriched_links),
                    'enriched_links': enriched_links,
                    'processor_version': PROCESSOR_VERSION,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }, ensure_ascii=False)

                # Update row
                row[score_idx] = str(score)
                row[tag_idx] = tag.replace('🔥', '').replace('🟡', '').replace('🔵', '').replace('⚫', '').strip()
                row[context_idx] = context
                row[data_idx] = enriched_json

                # Add to batch updates
                cell_range = f'A{row_idx}:{chr(65 + len(row) - 1)}{row_idx}'
                updates.append({
                    'range': cell_range,
                    'values': [row]
                })

                self.logger.info(f"Row {row_idx}: Enriched {len(enriched_links)} links, Score: {score}, Tag: {tag}")
                self.logger.info(f"Row {row_idx}: Context: {context[:100]}...")

                stats['rows_updated'] += 1
                stats['ok'] += 1

            # Write all updates to sheet
            if updates and not self.dry_run:
                self.service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body={'data': updates, 'valueInputOption': 'RAW'}
                ).execute()
                self.logger.info(f"Wrote {len(updates)} rows to sheet")
            elif self.dry_run:
                self.logger.info(f"DRY RUN: Would have written {len(updates)} rows")

            stats['elapsed_seconds'] = time.time() - start_time
            return stats

        except Exception as e:
            self.logger.error(f"Sheet processing failed: {e}")
            import traceback
            traceback.print_exc()
            stats['errors'].append(str(e))
            return stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Smart Column Enricher")
    parser.add_argument('--sheet-id', required=True, help='Google Sheet ID')
    parser.add_argument('--max-rows', type=int, default=5, help='Max rows to process')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    enricher = SmartColumnEnricher(args.sheet_id, dry_run=args.dry_run)
    
    if not enricher.authenticate():
        print("Authentication failed")
        sys.exit(1)
    
    stats = enricher.process_sheet(max_rows=args.max_rows)
    
    print("\n" + "="*60)
    print("ENRICHMENT COMPLETE")
    print(f"Rows attempted: {stats['rows_attempted']}")
    print(f"Rows updated: {stats['rows_updated']}")
    print(f"Success: {stats['ok']}")
    print(f"Failed: {stats['failed']}")
    print(f"Time: {stats.get('elapsed_seconds', 0):.1f}s")
    print("="*60)