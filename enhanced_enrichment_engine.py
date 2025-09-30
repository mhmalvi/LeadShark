#!/usr/bin/env python3
"""
Enhanced Enrichment Engine
Orchestrates multi-link scraping + API enrichment + lead scoring + context generation
"""

import sys
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import logging

# Fix Windows Unicode issues for logging
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass  # Already wrapped or not needed

from multi_link_scraper import MultiLinkScraper
from link_type_classifier import LinkTypeClassifier
from data_enrichment import DataEnrichment
from lead_scoring_engine import LeadScoringEngine
from context_generator import ContextGenerator
from api_rate_limiter import APIRateLimiter


class EnhancedEnrichmentEngine:
    """
    Complete enrichment engine that:
    1. Scrapes multiple links per row (Link 1-5 with Summary + JSON)
    2. Performs API enrichment (Gender, Email, GitHub, Company, LinkedIn)
    3. Calculates lead scores (0-100) with weighted factors
    4. Generates complete context paragraphs
    5. Tracks API sources for transparency
    """

    def __init__(self):
        self.multi_scraper = MultiLinkScraper()
        self.classifier = LinkTypeClassifier()
        self.enricher = DataEnrichment()
        self.scorer = LeadScoringEngine()
        self.context_gen = ContextGenerator()
        self.rate_limiter = APIRateLimiter()

        self.logger = logging.getLogger(__name__)

    def enrich_row(
        self,
        row_data: Dict[str, str],
        max_links: int = 5
    ) -> Dict[str, any]:
        """
        Enrich a single row with all data

        Returns dict with:
        - link_data: {1: {summary, json}, 2: {...}, ...}
        - api_enrichment: {gender, email, github, company, linkedin}
        - lead_score: int (0-100)
        - lead_tags: str ("Hot 🔥", etc.)
        - complete_context: str
        - last_scraped: timestamp
        """
        start_time = time.time()

        enrichment_result = {
            'link_data': {},
            'api_enrichment': {},
            'lead_score': 0,
            'lead_tags': 'Discard ⚫',
            'complete_context': '',
            'last_scraped': datetime.now(timezone.utc).isoformat(),
            'processing_time_ms': 0,
            'errors': []
        }

        try:
            # Step 1: Extract all links from row
            links = self._extract_links_from_row(row_data)
            self.logger.info(f"Found {len(links)} links to scrape")

            # Step 2: Scrape all links
            if links:
                enrichment_result['link_data'] = self.multi_scraper.scrape_multiple_links(
                    links,
                    max_links=max_links
                )
                self.logger.info(f"Scraped {len(enrichment_result['link_data'])} links")

            # Step 3: API enrichment with rate limiting
            enrichment_result['api_enrichment'] = self._perform_api_enrichment(row_data)

            # Step 4: Prepare data for scoring
            scoring_data = self._prepare_scoring_data(
                row_data,
                enrichment_result['link_data'],
                enrichment_result['api_enrichment']
            )

            # Step 5: Calculate lead score
            score, tags, breakdown = self.scorer.calculate_score(scoring_data)
            enrichment_result['lead_score'] = score
            enrichment_result['lead_tags'] = tags
            enrichment_result['score_breakdown'] = breakdown

            self.logger.info(f"Lead score: {score} - {tags}")

            # Step 6: Generate complete context
            person_name = self._extract_person_name(row_data)
            enrichment_result['complete_context'] = self.context_gen.generate_complete_context(
                scoring_data,
                person_name
            )

            self.logger.info("Context generated successfully")

        except Exception as e:
            self.logger.error(f"Enrichment failed: {e}")
            enrichment_result['errors'].append(str(e))

        # Calculate processing time
        enrichment_result['processing_time_ms'] = int((time.time() - start_time) * 1000)

        return enrichment_result

    def _extract_links_from_row(self, row_data: Dict[str, str]) -> List[str]:
        """Extract all links from row data"""
        links = []

        # Comprehensive link field names (order matters - priority order)
        link_fields = [
            # Personal/Individual links first
            'linkedin_url', 'LinkedIn URL', 'linkedin',
            # Organization website
            'organization_website_url', 'company_website', 'website', 'Website', 'url', 'URL',
            # Organization social profiles
            'organization_linkedin_url', 'organization_twitter_url', 'organization_facebook_url',
            # Personal social profiles
            'twitter_url', 'Twitter URL', 'twitter',
            'facebook_url', 'Facebook URL', 'facebook',
            'github_url', 'GitHub URL', 'github',
            'instagram_url', 'Instagram URL', 'instagram',
            # Other organization links
            'organization_primary_domain'
        ]

        for field in link_fields:
            if field in row_data and row_data[field]:
                url = row_data[field].strip()
                if url and url.startswith(('http://', 'https://')) and url not in links:
                    links.append(url)

        return links

    def _perform_api_enrichment(self, row_data: Dict[str, str]) -> Dict[str, Dict]:
        """Perform API enrichment with rate limiting and caching"""
        api_results = {}

        # 1. Gender detection
        first_name = self._extract_first_name(row_data)
        if first_name:
            gender_result = self.rate_limiter.make_cached_request(
                'genderize',
                first_name.lower(),
                self.enricher.get_gender,
                first_name
            )

            if gender_result:
                api_results['gender'] = {
                    'data': gender_result,
                    'source': 'Genderize.io',
                    'confidence': gender_result.get('probability', 0) * 100 if gender_result.get('status') == 'success' else 0
                }

        # 2. Email verification
        email = self._extract_email(row_data)
        if email:
            email_result = self.rate_limiter.make_cached_request(
                'eva_email',
                email.lower(),
                self.enricher.verify_email_eva,
                email
            )

            if email_result:
                api_results['email_verification'] = {
                    'data': email_result,
                    'source': 'EVA API',
                    'deliverable': email_result.get('deliverable', False) if email_result.get('status') == 'success' else False
                }

        # 3. GitHub search
        company = self._extract_company_name(row_data)
        if company:
            github_result = self.rate_limiter.make_cached_request(
                'github',
                company.lower(),
                self.enricher.search_github,
                company
            )

            if github_result:
                api_results['github'] = {
                    'data': github_result,
                    'source': 'GitHub REST API v3',
                    'total_repos': github_result.get('total_repos', 0) if github_result.get('status') == 'success' else 0
                }

        # 4. Google company search
        if company:
            location = row_data.get('location', row_data.get('Location', ''))
            google_result = self.rate_limiter.make_cached_request(
                'google_search',
                f"{company}_{location}".lower(),
                self.enricher.google_company_search,
                company,
                location
            )

            if google_result:
                api_results['google_search'] = {
                    'data': google_result,
                    'source': 'Google Custom Search API',
                    'industry_mentions': google_result.get('industry_mentions', []) if google_result.get('status') == 'success' else []
                }

        # 5. LinkedIn verification (from scraped data, not separate API)
        linkedin_url = row_data.get('linkedin_url', row_data.get('LinkedIn URL', ''))
        if linkedin_url:
            api_results['linkedin'] = {
                'data': {'url': linkedin_url},
                'source': 'Web scraping (platform-optimized)',
                'verified': True  # Will be updated from scraping results
            }

        return api_results

    def _prepare_scoring_data(
        self,
        row_data: Dict,
        link_data: Dict,
        api_enrichment: Dict
    ) -> Dict:
        """Prepare data structure for lead scoring"""
        scoring_data = {
            'scraped_content': {},
            'api_results': {}
        }

        # Map link data to scoring structure
        for link_idx, link_info in link_data.items():
            link_type = link_info.get('link_type', '')

            if 'linkedin' in link_type:
                scoring_data['scraped_content']['linkedin'] = {
                    'url': link_info['url'],
                    'extracted': link_info.get('extracted', {})
                }
            elif 'twitter' in link_type or link_type == 'twitter':
                scoring_data['scraped_content']['twitter'] = {
                    'url': link_info['url'],
                    'extracted': link_info.get('extracted', {})
                }
            elif 'github' in link_type:
                scoring_data['scraped_content']['github'] = {
                    'url': link_info['url'],
                    'extracted': link_info.get('extracted', {})
                }
            elif link_type == 'website':
                scoring_data['scraped_content']['website'] = {
                    'url': link_info['url'],
                    'extracted': link_info.get('extracted', {})
                }

        # Map API enrichment to scoring structure
        for api_name, api_data in api_enrichment.items():
            scoring_data['api_results'][api_name] = api_data.get('data', {})

        return scoring_data

    def _extract_person_name(self, row_data: Dict) -> str:
        """Extract person name from row"""
        name_fields = ['name', 'Name', 'full_name', 'Full Name', 'first_name', 'last_name']
        for field in name_fields:
            if field in row_data and row_data[field]:
                return row_data[field].strip()
        return ""

    def _extract_first_name(self, row_data: Dict) -> str:
        """Extract first name from row"""
        if 'first_name' in row_data or 'First Name' in row_data:
            return row_data.get('first_name', row_data.get('First Name', '')).strip()

        # Extract from full name
        full_name = self._extract_person_name(row_data)
        if full_name:
            parts = full_name.split()
            return parts[0] if parts else ""

        return ""

    def _extract_email(self, row_data: Dict) -> str:
        """Extract email from row"""
        email_fields = ['email', 'Email', 'email_address', 'Email Address']
        for field in email_fields:
            if field in row_data and row_data[field]:
                return row_data[field].strip()
        return ""

    def _extract_company_name(self, row_data: Dict) -> str:
        """Extract company name from row"""
        company_fields = [
            'company', 'Company', 'organization', 'Organization',
            'organization_name', 'company_name', 'Company Name'
        ]
        for field in company_fields:
            if field in row_data and row_data[field]:
                return row_data[field].strip()
        return ""

    def get_api_quota_status(self) -> Dict:
        """Get current API quota status"""
        return self.rate_limiter.get_all_quota_status()


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    engine = EnhancedEnrichmentEngine()

    test_row = {
        'name': 'John Doe',
        'first_name': 'John',
        'email': 'john@example.com',
        'company': 'ExampleCorp',
        'location': 'New York',
        'linkedin_url': 'https://linkedin.com/in/johndoe',
        'website': 'https://example.com',
        'twitter_url': 'https://twitter.com/johndoe'
    }

    print("Enhanced Enrichment Engine Test\n")
    print("=" * 60)

    # Show quota status
    print("\nAPI Quota Status:")
    for api, status in engine.get_api_quota_status().items():
        print(f"  {api}: {status.get('remaining', 'N/A')} remaining")

    print("\n" + "=" * 60)
    print("Starting enrichment...\n")

    result = engine.enrich_row(test_row, max_links=2)

    print(f"\nProcessing time: {result['processing_time_ms']}ms")
    print(f"Links scraped: {len(result['link_data'])}")
    print(f"API enrichments: {len(result['api_enrichment'])}")
    print(f"Lead Score: {result['lead_score']} - {result['lead_tags']}")
    print(f"\nComplete Context:\n{result['complete_context']}")

    if result['errors']:
        print(f"\nErrors: {result['errors']}")