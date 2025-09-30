#!/usr/bin/env python3
"""
Multi-Link Scraper with Platform-Specific Extraction
Scrapes multiple links per row with Summary + JSON output
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import logging

from link_type_classifier import LinkTypeClassifier, LinkType
from enhanced_scraping_pipeline import EnhancedScrapingPipeline


class MultiLinkScraper:
    """
    Scrapes multiple links per row and generates:
    - Short Summary (human-readable)
    - JSON data (machine-readable)
    - Complete Context paragraph
    """

    def __init__(self):
        self.classifier = LinkTypeClassifier()
        self.scraper = EnhancedScrapingPipeline()
        self.logger = logging.getLogger(__name__)

    def scrape_multiple_links(
        self,
        links: List[str],
        max_links: int = 5
    ) -> Dict[int, Dict[str, any]]:
        """
        Scrape up to max_links URLs
        Returns: {link_index: {summary, json, link_type}}
        """
        results = {}

        for idx, url in enumerate(links[:max_links], start=1):
            if not url or not url.strip():
                continue

            self.logger.info(f"Scraping Link {idx}: {url}")

            try:
                # Classify link type
                link_type = self.classifier.classify_url(url)
                link_display = self.classifier.get_display_name(link_type)

                # Scrape URL
                scraped = self.scraper.scrape_url_with_retry(url)

                # Extract structured data based on link type
                extracted_data = self._extract_by_type(scraped, link_type)

                # Generate summary
                summary = self._generate_summary(extracted_data, link_type, url)

                # Generate JSON
                json_data = self._generate_json(extracted_data, link_type, url)

                results[idx] = {
                    'url': url,
                    'link_type': link_type.value,
                    'link_display': link_display,
                    'summary': summary,
                    'json': json_data,
                    'extracted': extracted_data,
                    'scrape_status': scraped.get('status', 'unknown')
                }

                # Respectful delay
                time.sleep(self.scraper.get_request_delay(url))

            except Exception as e:
                self.logger.error(f"Link {idx} scraping failed: {e}")
                results[idx] = {
                    'url': url,
                    'link_type': 'error',
                    'link_display': 'Error',
                    'summary': f"ERROR: {str(e)[:100]}",
                    'json': json.dumps({'error': str(e)}),
                    'extracted': {},
                    'scrape_status': 'failed'
                }

        return results

    def _extract_by_type(self, scraped_data: Dict, link_type: LinkType) -> Dict:
        """Extract structured data based on link type"""
        if scraped_data.get('status') != 'success':
            return {
                'error': scraped_data.get('error', 'Scraping failed'),
                'status': scraped_data.get('status', 'failed')
            }

        content = scraped_data.get('content', '')
        metadata = scraped_data.get('metadata', {})

        # Get extraction template
        template = self.classifier.get_extraction_template(link_type)

        # Base extracted data
        extracted = {
            'title': metadata.get('title', ''),
            'description': metadata.get('description', ''),
            'url': scraped_data.get('url', ''),
        }

        # Platform-specific extraction
        if link_type == LinkType.LINKEDIN_PROFILE:
            extracted.update(self._extract_linkedin_profile(content, metadata))

        elif link_type == LinkType.LINKEDIN_COMPANY:
            extracted.update(self._extract_linkedin_company(content, metadata))

        elif link_type == LinkType.WEBSITE:
            extracted.update(self._extract_website(content, metadata, scraped_data))

        elif link_type == LinkType.TWITTER:
            extracted.update(self._extract_twitter(content, metadata))

        elif link_type == LinkType.GITHUB:
            extracted.update(self._extract_github(content, metadata))

        elif link_type == LinkType.CONTACT_PAGE:
            extracted.update(self._extract_contact_page(content, metadata, scraped_data))

        else:
            # Generic extraction
            extracted.update(self._extract_generic(content, metadata))

        return extracted

    def _extract_linkedin_profile(self, content: str, metadata: Dict) -> Dict:
        """Extract LinkedIn profile fields"""
        # Try to parse HTML
        try:
            soup = BeautifulSoup(content, 'html.parser')

            data = {}

            # Extract headline/title
            headline_selectors = ['.pv-top-card-section__headline', '.text-body-medium']
            for selector in headline_selectors:
                element = soup.select_one(selector)
                if element:
                    data['headline'] = element.get_text(strip=True)
                    break

            # Extract location
            location_selectors = ['.pv-top-card-section__location', '.pb2.t-black--light']
            for selector in location_selectors:
                element = soup.select_one(selector)
                if element:
                    data['location'] = element.get_text(strip=True)
                    break

            # Extract summary/about (first 300 chars)
            about_text = content[:300] if len(content) > 300 else content
            data['about'] = about_text.strip()

            return data

        except Exception as e:
            self.logger.warning(f"LinkedIn profile extraction failed: {e}")
            return {}

    def _extract_linkedin_company(self, content: str, metadata: Dict) -> Dict:
        """Extract LinkedIn company fields"""
        try:
            soup = BeautifulSoup(content, 'html.parser')

            data = {}

            # Company name
            name_el = soup.select_one('.org-top-card-summary__title')
            if name_el:
                data['company_name'] = name_el.get_text(strip=True)

            # Tagline
            tagline_el = soup.select_one('.org-top-card-summary__tagline')
            if tagline_el:
                data['tagline'] = tagline_el.get_text(strip=True)

            # Industry
            industry_el = soup.select_one('.org-top-card-summary__info-item')
            if industry_el:
                data['industry'] = industry_el.get_text(strip=True)

            return data

        except Exception as e:
            self.logger.warning(f"LinkedIn company extraction failed: {e}")
            return {}

    def _extract_website(self, content: str, metadata: Dict, scraped_data: Dict) -> Dict:
        """Extract company website fields"""
        data = {
            'description': metadata.get('description', ''),
            'emails': scraped_data.get('emails', [])[:5],
            'phones': scraped_data.get('phones', [])[:3],
            'social_links': scraped_data.get('social_links', [])[:5],
        }

        # Extract services/products mentions
        services_keywords = ['services', 'products', 'solutions', 'offerings']
        services_found = [kw for kw in services_keywords if kw in content.lower()]
        if services_found:
            data['services_mentioned'] = services_found

        return data

    def _extract_twitter(self, content: str, metadata: Dict) -> Dict:
        """Extract Twitter/X profile fields"""
        try:
            soup = BeautifulSoup(content, 'html.parser')

            data = {}

            # Bio
            bio_el = soup.select_one('[data-testid="UserDescription"]')
            if bio_el:
                data['bio'] = bio_el.get_text(strip=True)

            # Try to extract follower count from content
            if 'followers' in content.lower():
                # Simple heuristic extraction
                import re
                follower_match = re.search(r'(\d+[\d,]*)\s+followers?', content.lower())
                if follower_match:
                    data['followers_text'] = follower_match.group(1)

            return data

        except Exception as e:
            self.logger.warning(f"Twitter extraction failed: {e}")
            return {}

    def _extract_github(self, content: str, metadata: Dict) -> Dict:
        """Extract GitHub profile fields"""
        try:
            soup = BeautifulSoup(content, 'html.parser')

            data = {}

            # Bio
            bio_el = soup.select_one('.p-note')
            if bio_el:
                data['bio'] = bio_el.get_text(strip=True)

            # Try to count repos
            if 'repositories' in content.lower():
                import re
                repo_match = re.search(r'(\d+)\s+repositories?', content.lower())
                if repo_match:
                    data['repo_count_text'] = repo_match.group(1)

            return data

        except Exception as e:
            self.logger.warning(f"GitHub extraction failed: {e}")
            return {}

    def _extract_contact_page(self, content: str, metadata: Dict, scraped_data: Dict) -> Dict:
        """Extract contact page fields"""
        return {
            'emails': scraped_data.get('emails', []),
            'phones': scraped_data.get('phones', []),
            'has_contact_form': 'form' in content.lower() and 'submit' in content.lower()
        }

    def _extract_generic(self, content: str, metadata: Dict) -> Dict:
        """Generic extraction"""
        return {
            'title': metadata.get('title', ''),
            'description': metadata.get('description', ''),
            'content_preview': content[:200] if content else ''
        }

    def _generate_summary(self, extracted: Dict, link_type: LinkType, url: str) -> str:
        """Generate human-readable summary"""
        link_display = self.classifier.get_display_name(link_type)

        if extracted.get('error'):
            return f"**Link:** {url}\n**Status:** Error - {extracted['error']}"

        lines = [f"**Link:** {url}", f"**Type:** {link_display}"]

        # Add key fields based on type
        if link_type == LinkType.LINKEDIN_PROFILE:
            if extracted.get('headline'):
                lines.append(f"**Headline:** {extracted['headline']}")
            if extracted.get('location'):
                lines.append(f"**Location:** {extracted['location']}")

        elif link_type == LinkType.LINKEDIN_COMPANY:
            if extracted.get('company_name'):
                lines.append(f"**Company:** {extracted['company_name']}")
            if extracted.get('tagline'):
                lines.append(f"**Tagline:** {extracted['tagline']}")

        elif link_type == LinkType.WEBSITE:
            if extracted.get('description'):
                lines.append(f"**About:** {extracted['description'][:150]}")
            if extracted.get('emails'):
                lines.append(f"**Contact:** {', '.join(extracted['emails'][:2])}")

        elif link_type == LinkType.TWITTER:
            if extracted.get('bio'):
                lines.append(f"**Bio:** {extracted['bio'][:100]}")
            if extracted.get('followers_text'):
                lines.append(f"**Followers:** {extracted['followers_text']}")

        elif link_type == LinkType.GITHUB:
            if extracted.get('bio'):
                lines.append(f"**Bio:** {extracted['bio'][:100]}")
            if extracted.get('repo_count_text'):
                lines.append(f"**Repos:** {extracted['repo_count_text']}")

        else:
            if extracted.get('title'):
                lines.append(f"**Title:** {extracted['title'][:100]}")
            if extracted.get('description'):
                lines.append(f"**Description:** {extracted['description'][:100]}")

        return "\n".join(lines)

    def _generate_json(self, extracted: Dict, link_type: LinkType, url: str) -> str:
        """Generate machine-readable JSON"""
        schema = self.classifier.get_json_schema(link_type)

        schema['url'] = url
        schema['scrape_timestamp'] = datetime.now(timezone.utc).isoformat()

        # Map extracted data to schema
        schema['extracted'].update(extracted)

        # Calculate confidence (simple heuristic)
        field_count = sum(1 for v in extracted.values() if v)
        schema['confidence'] = min(1.0, field_count / 5.0)

        return json.dumps(schema, separators=(',', ':'))


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = MultiLinkScraper()

    test_links = [
        "https://linkedin.com/in/johndoe",
        "https://example.com",
        "https://twitter.com/johndoe"
    ]

    print("Multi-Link Scraper Test\n")
    print("=" * 60)

    results = scraper.scrape_multiple_links(test_links, max_links=2)

    for idx, data in results.items():
        print(f"\nLink {idx}:")
        print(f"URL: {data['url']}")
        print(f"Type: {data['link_display']}")
        print(f"Status: {data['scrape_status']}")
        print(f"\nSummary:\n{data['summary']}")
        print(f"\nJSON (first 200 chars):\n{data['json'][:200]}...")
        print("=" * 60)