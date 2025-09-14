#!/usr/bin/env python3
"""
Link Intelligence Orchestrator
A meticulous system for scanning, searching, scraping, and scoring every link in Google Sheets rows.
"""

import os
import sys
import json
import time
import re
import random
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Set
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs
import logging
from collections import defaultdict
import requests
from bs4 import BeautifulSoup
import traceback

sys.path.append(os.path.dirname(__file__))

from google_sheets_auth import authenticate_google_sheets
from enhanced_scraping_pipeline import EnhancedScrapingPipeline

# Constants
ORCHESTRATOR_VERSION = "v1.0-LinkIntel"
SCHEMA_VERSION = "LIO-1.0"
AX_COLUMN_INDEX = 49  # Column AX is index 49 (0-based)

class LinkIntelligenceOrchestrator:
    """
    Comprehensive link intelligence system with search, scrape, and scoring capabilities.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the orchestrator with configuration.

        Args:
            config: Configuration dictionary with all parameters
        """
        # Core configuration
        self.sheet_id = config.get('SHEET_ID', '')
        self.tab_name = config.get('TAB_NAME', 'Sheet1')
        self.row_scope = config.get('ROW_SCOPE', 'all rows')
        self.daily_link_limit = config.get('DAILY_LINK_LIMIT', 500)
        self.max_links_per_row = config.get('MAX_LINKS_PER_ROW', 10)
        self.search_engine = config.get('SEARCH_ENGINE', 'Google')
        self.scrape_depth = config.get('SCRAPE_DEPTH', 'light')
        self.arp_mode = config.get('ARP_MODE', 'on').lower() == 'on'
        self.user_agent_id = config.get('USER_AGENT_ID', 'LinkIntelBot/1.0')
        self.robots_respect = config.get('ROBOTS_RESPECT', True)
        self.delay_randomization_ms = config.get('DELAY_RANDOMIZATION_MS', (800, 2500))
        self.retry_policy = config.get('RETRY_POLICY', {'attempts': 3, 'backoff': [2, 4, 8]})
        self.force_refresh = config.get('FORCE_REFRESH', False)

        # Google Sheets services
        self.service = None
        self.drive_service = None

        # Scraping pipeline
        self.scraper = EnhancedScrapingPipeline()

        # State tracking
        self.links_processed_today = 0
        self.processing_ledger = {}  # (row_id, url) -> status
        self.column_mapping = {}  # header -> column index
        self.next_empty_column = AX_COLUMN_INDEX + 1  # Start after AX

        # Statistics
        self.stats = {
            'rows_processed': 0,
            'links_found': 0,
            'links_processed': 0,
            'links_skipped': 0,
            'errors': 0,
            'columns_created': 0,
            'start_time': None,
            'end_time': None
        }

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging for the orchestrator."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [%(levelname)s] - %(message)s',
            handlers=[
                logging.FileHandler('link_intelligence.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def authenticate(self) -> bool:
        """Authenticate with Google Sheets API."""
        try:
            self.logger.info("[AUTH] Authenticating with Google Sheets API...")
            result = authenticate_google_sheets()
            if result:
                self.service, self.drive_service, _ = result
                self.logger.info("[OK] Authentication successful")
                return True
            self.logger.error("[ERROR] Authentication failed")
            return False
        except Exception as e:
            self.logger.error(f"[ERROR] Authentication error: {e}")
            return False

    def normalize_url(self, url: str) -> str:
        """
        Normalize URL: add scheme, remove UTM params, clean up.

        Args:
            url: Raw URL string

        Returns:
            Normalized URL string
        """
        if not url:
            return ""

        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            parsed = urlparse(url)

            # Remove UTM and common tracking parameters
            if parsed.query:
                query_params = parse_qs(parsed.query)
                tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
                                 'utm_content', 'fbclid', 'gclid', 'ref', 'source'}
                cleaned_params = {k: v for k, v in query_params.items()
                                if k.lower() not in tracking_params}

                # Rebuild query string
                if cleaned_params:
                    from urllib.parse import urlencode
                    query_string = urlencode(cleaned_params, doseq=True)
                else:
                    query_string = ''

                # Rebuild URL
                parsed = parsed._replace(query=query_string)

            # Remove fragment
            parsed = parsed._replace(fragment='')

            # Rebuild and return
            return urlunparse(parsed).rstrip('/')

        except Exception as e:
            self.logger.warning(f"URL normalization failed for {url}: {e}")
            return url

    def discover_links_in_row(self, row_data: List[str]) -> List[str]:
        """
        Discover all links in a row by scanning every cell.

        Args:
            row_data: List of cell values in the row

        Returns:
            List of normalized, deduplicated URLs
        """
        links = []
        url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+|'
            r'www\.[^\s<>"{}|\\^`\[\]]+|'
            r'[a-zA-Z0-9][a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s<>"{}|\\^`\[\]]*)?'
        )

        for cell in row_data:
            if not cell:
                continue

            # Find all URLs in the cell
            found_urls = url_pattern.findall(str(cell))

            for url in found_urls:
                normalized = self.normalize_url(url)
                if normalized and self._is_valid_url(normalized):
                    links.append(normalized)

        # Deduplicate while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)

        return unique_links[:self.max_links_per_row]  # Respect max links per row

    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid and should be processed.

        Args:
            url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)

            # Must have scheme and netloc
            if not (parsed.scheme and parsed.netloc):
                return False

            # Only allow http and https schemes
            if parsed.scheme not in ['http', 'https']:
                return False

            # Check for proper domain with TLD
            if '.' not in parsed.netloc:
                return False

            # Skip common invalid patterns
            invalid_domains = ['localhost', '127.0.0.1', '0.0.0.0']
            if any(domain in parsed.netloc for domain in invalid_domains):
                return False

            # Skip URL shorteners (optional - you might want to expand these)
            shorteners = ['bit.ly', 'tinyurl.com', 'goo.gl', 'ow.ly', 't.co']
            if any(short in parsed.netloc for short in shorteners):
                self.logger.info(f"[WARNING] URL shortener detected: {url}")
                # Could expand here if needed

            return True

        except Exception:
            return False

    def search_link_intelligence(self, url: str) -> Dict[str, Any]:
        """
        Perform web search to gather intelligence about a URL/domain.

        Args:
            url: URL to search for

        Returns:
            Dictionary with search intelligence
        """
        intel = {
            'brand': '',
            'category': '',
            'size_signals': [],
            'linkedin_presence': '',
            'crunchbase_presence': '',
            'recent_news': [],
            'summary_bullets': []
        }

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')

            # Construct search query
            search_query = f'"{domain}" company overview employees industry'

            if self.search_engine.lower() == 'google':
                intel = self._google_search_intelligence(domain, search_query)
            elif self.search_engine.lower() == 'bing':
                intel = self._bing_search_intelligence(domain, search_query)
            else:
                self.logger.warning(f"Unsupported search engine: {self.search_engine}")

        except Exception as e:
            self.logger.error(f"Search intelligence failed for {url}: {e}")

        return intel

    def _google_search_intelligence(self, domain: str, query: str) -> Dict[str, Any]:
        """
        Perform Google search for intelligence gathering.

        Args:
            domain: Domain to search
            query: Search query

        Returns:
            Intelligence dictionary
        """
        intel = {
            'brand': domain.split('.')[0].title(),
            'category': '',
            'size_signals': [],
            'linkedin_presence': '',
            'crunchbase_presence': '',
            'recent_news': [],
            'summary_bullets': []
        }

        try:
            # Apply random delay
            delay = random.uniform(*self.delay_randomization_ms) / 1000
            time.sleep(delay)

            headers = {
                'User-Agent': f'{self.user_agent_id} Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # Search for company info
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=10"
            response = requests.get(search_url, headers=headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract text snippets
                snippets = []
                for g in soup.find_all('div', class_='g'):
                    snippet = g.get_text()
                    if snippet:
                        snippets.append(snippet[:500])

                # Analyze snippets for intelligence
                text = ' '.join(snippets).lower()

                # Category detection
                categories = {
                    'SaaS': ['saas', 'software as a service', 'cloud software'],
                    'E-commerce': ['ecommerce', 'e-commerce', 'online store', 'shop online'],
                    'Agency': ['agency', 'marketing agency', 'digital agency', 'creative agency'],
                    'Consulting': ['consulting', 'consultancy', 'advisory', 'professional services'],
                    'Technology': ['technology', 'tech company', 'software company', 'IT'],
                    'Healthcare': ['healthcare', 'medical', 'health tech', 'biotech'],
                    'Finance': ['fintech', 'financial', 'banking', 'investment', 'payments'],
                    'Education': ['edtech', 'education', 'learning', 'training', 'academy']
                }

                for cat, keywords in categories.items():
                    if any(kw in text for kw in keywords):
                        intel['category'] = cat
                        break

                # Size signals
                size_patterns = [
                    (r'(\d+)\+?\s*employees', 'employees'),
                    (r'\$(\d+[MBK])\s*revenue', 'revenue'),
                    (r'(\d+)\+?\s*customers', 'customers'),
                    (r'(\d+)\+?\s*users', 'users')
                ]

                for pattern, label in size_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        intel['size_signals'].append(f"{label}: {matches[0]}")

                # LinkedIn presence
                if 'linkedin.com/company/' in text:
                    linkedin_match = re.search(r'linkedin\.com/company/[^\s]+', text)
                    if linkedin_match:
                        intel['linkedin_presence'] = f"https://{linkedin_match.group()}"

                # Crunchbase presence
                if 'crunchbase.com/organization/' in text:
                    intel['crunchbase_presence'] = 'Yes'

                # Recent news (look for year mentions)
                current_year = datetime.now().year
                recent_years = [str(current_year), str(current_year - 1)]
                for year in recent_years:
                    if year in text:
                        intel['recent_news'].append(f"Activity in {year}")
                        break

                # Generate summary bullets
                bullets = []
                if intel['category']:
                    bullets.append(f"Category: {intel['category']}")
                if intel['size_signals']:
                    bullets.append(f"Size: {', '.join(intel['size_signals'][:2])}")
                if intel['linkedin_presence']:
                    bullets.append("LinkedIn presence confirmed")
                if intel['crunchbase_presence']:
                    bullets.append("Listed on Crunchbase")
                if intel['recent_news']:
                    bullets.append(f"Recent activity: {intel['recent_news'][0]}")
                if not bullets:
                    bullets.append(f"Limited public information for {domain}")

                intel['summary_bullets'] = bullets[:6]

        except Exception as e:
            self.logger.error(f"Google search failed: {e}")
            intel['summary_bullets'] = [f"Search unavailable for {domain}"]

        return intel

    def _bing_search_intelligence(self, domain: str, query: str) -> Dict[str, Any]:
        """Bing search implementation (placeholder)."""
        # Similar to Google but using Bing API
        return {
            'brand': domain.split('.')[0].title(),
            'category': '',
            'size_signals': [],
            'linkedin_presence': '',
            'crunchbase_presence': '',
            'recent_news': [],
            'summary_bullets': [f"Bing search pending for {domain}"]
        }

    def scrape_link_intelligence(self, url: str) -> Dict[str, Any]:
        """
        Scrape a URL for detailed intelligence.

        Args:
            url: URL to scrape

        Returns:
            Dictionary with scraped intelligence
        """
        intel = {
            'title': '',
            'meta_description': '',
            'h1': '',
            'value_proposition': '',
            'pricing_cta': '',
            'contact_capture': [],
            'tech_signals': [],
            'freshness': '',
            'social_links': [],
            'emails': [],
            'phones': [],
            'summary_bullets': []
        }

        try:
            # Check robots.txt if respect is enabled
            if self.robots_respect and not self._check_robots_allowed(url):
                intel['summary_bullets'] = ['Blocked by robots.txt']
                return intel

            # Apply random delay
            delay = random.uniform(*self.delay_randomization_ms) / 1000
            time.sleep(delay)

            # Scrape with retry logic
            for attempt in range(self.retry_policy['attempts']):
                try:
                    result = self.scraper.scrape_url_with_retry(url)

                    if result.get('status') == 'success':
                        # Parse the content
                        soup = BeautifulSoup(result.get('content', ''), 'html.parser')

                        # Extract metadata
                        intel['title'] = result.get('metadata', {}).get('title', '')[:100]
                        intel['meta_description'] = result.get('metadata', {}).get('description', '')[:200]

                        # Extract H1
                        h1_tag = soup.find('h1')
                        if h1_tag:
                            intel['h1'] = h1_tag.get_text(strip=True)[:100]

                        # Extract value proposition (look for hero text)
                        hero_selectors = ['.hero', '.banner', '.jumbotron', 'section:first-of-type']
                        for selector in hero_selectors:
                            hero = soup.select_one(selector)
                            if hero:
                                hero_text = hero.get_text(strip=True)[:300]
                                if len(hero_text) > 50:
                                    intel['value_proposition'] = hero_text
                                    break

                        # Look for pricing/CTA
                        cta_keywords = ['get started', 'try free', 'sign up', 'demo', 'pricing',
                                      'plans', 'buy now', 'contact sales']
                        cta_elements = []
                        for keyword in cta_keywords:
                            elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
                            cta_elements.extend(elements[:2])

                        if cta_elements:
                            intel['pricing_cta'] = 'Yes - ' + ', '.join([e.strip()[:30] for e in cta_elements[:3]])

                        # Extract contact methods
                        contact_methods = []

                        # Email extraction
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, str(soup))
                        if emails:
                            intel['emails'] = list(set(emails))[:5]
                            contact_methods.append(f"Email ({len(emails)} found)")

                        # Phone extraction
                        phone_pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
                        phones = re.findall(phone_pattern, str(soup))
                        if phones:
                            intel['phones'] = list(set(phones))[:3]
                            contact_methods.append(f"Phone ({len(phones)} found)")

                        # Forms detection
                        forms = soup.find_all('form')
                        if forms:
                            contact_methods.append(f"Forms ({len(forms)} found)")

                        intel['contact_capture'] = contact_methods

                        # Technology detection
                        tech_signals = []

                        # CMS detection
                        cms_patterns = {
                            'WordPress': ['wp-content', 'wp-includes', 'wordpress'],
                            'Shopify': ['shopify', 'myshopify.com', 'cdn.shopify'],
                            'Wix': ['wix.com', 'wixstatic.com'],
                            'Squarespace': ['squarespace.com', 'sqsp.net'],
                            'Webflow': ['webflow.io', 'webflow.com'],
                            'HubSpot': ['hubspot', 'hs-scripts', 'hsforms']
                        }

                        page_text = str(soup).lower()
                        for tech, patterns in cms_patterns.items():
                            if any(pattern in page_text for pattern in patterns):
                                tech_signals.append(f"CMS: {tech}")
                                break

                        # Analytics detection
                        analytics_patterns = {
                            'Google Analytics': ['google-analytics.com', 'gtag', 'ga.js'],
                            'Google Tag Manager': ['googletagmanager.com', 'gtm.js'],
                            'Facebook Pixel': ['facebook.com/tr', 'fbq'],
                            'Hotjar': ['hotjar.com', 'hjid'],
                            'Segment': ['segment.com', 'analytics.js']
                        }

                        for tech, patterns in analytics_patterns.items():
                            if any(pattern in page_text for pattern in patterns):
                                tech_signals.append(tech)

                        intel['tech_signals'] = tech_signals[:5]

                        # Social links extraction
                        social_domains = ['facebook.com', 'twitter.com', 'x.com', 'linkedin.com',
                                        'instagram.com', 'youtube.com', 'github.com']
                        social_links = []
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if any(domain in href for domain in social_domains):
                                social_links.append(href)

                        intel['social_links'] = list(set(social_links))[:5]

                        # Freshness detection (look for dates)
                        current_year = str(datetime.now().year)
                        if current_year in page_text:
                            intel['freshness'] = f"Current year ({current_year}) mentioned"
                        elif str(int(current_year) - 1) in page_text:
                            intel['freshness'] = f"Last year ({int(current_year) - 1}) mentioned"
                        else:
                            intel['freshness'] = "No recent dates found"

                        # Deep scrape if requested
                        if self.scrape_depth == 'deep':
                            intel = self._deep_scrape_pages(url, soup, intel)

                        # Generate summary bullets
                        bullets = []
                        if intel['title']:
                            bullets.append(f"Title: {intel['title'][:50]}")
                        if intel['value_proposition']:
                            bullets.append(f"Value: {intel['value_proposition'][:80]}")
                        if intel['pricing_cta']:
                            bullets.append(f"CTA: {intel['pricing_cta'][:50]}")
                        if intel['tech_signals']:
                            bullets.append(f"Tech: {', '.join(intel['tech_signals'][:3])}")
                        if intel['contact_capture']:
                            bullets.append(f"Contact: {', '.join(intel['contact_capture'])}")
                        if intel['social_links']:
                            bullets.append(f"Social: {len(intel['social_links'])} profiles found")
                        if intel['freshness']:
                            bullets.append(f"Freshness: {intel['freshness']}")

                        intel['summary_bullets'] = bullets[:10]
                        break  # Success, exit retry loop

                    elif result.get('status') in ['blocked', 'not_found']:
                        intel['summary_bullets'] = [f"Page {result.get('status')}: {result.get('error', '')}"]
                        break

                    else:
                        # Retry with backoff
                        if attempt < self.retry_policy['attempts'] - 1:
                            backoff = self.retry_policy['backoff'][attempt]
                            self.logger.info(f"Retry {attempt + 1} for {url} in {backoff}s")
                            time.sleep(backoff)
                        else:
                            intel['summary_bullets'] = [f"Scrape failed after {attempt + 1} attempts"]

                except Exception as e:
                    self.logger.error(f"Scrape attempt {attempt + 1} failed: {e}")
                    if attempt == self.retry_policy['attempts'] - 1:
                        intel['summary_bullets'] = [f"Error: {str(e)[:100]}"]

        except Exception as e:
            self.logger.error(f"Scrape intelligence failed for {url}: {e}")
            intel['summary_bullets'] = [f"Scrape error: {str(e)[:100]}"]

        return intel

    def _check_robots_allowed(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed, False otherwise
        """
        try:
            from urllib.robotparser import RobotFileParser

            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()

            return rp.can_fetch(self.user_agent_id, url)

        except Exception as e:
            self.logger.warning(f"Robots.txt check failed for {url}: {e}")
            return True  # Allow if we can't check

    def _deep_scrape_pages(self, base_url: str, homepage_soup: BeautifulSoup,
                          intel: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform deep scraping of key pages.

        Args:
            base_url: Base URL
            homepage_soup: BeautifulSoup object of homepage
            intel: Current intelligence dictionary

        Returns:
            Updated intelligence dictionary
        """
        key_pages = ['pricing', 'plans', 'about', 'contact', 'products', 'features']
        pages_scraped = 0
        max_pages = 3

        for page in key_pages:
            if pages_scraped >= max_pages:
                break

            # Look for links to key pages
            page_link = None
            for link in homepage_soup.find_all('a', href=True):
                href = link['href'].lower()
                if f'/{page}' in href or f'{page}.html' in href:
                    page_link = urljoin(base_url, link['href'])
                    break

            if page_link:
                try:
                    # Apply delay
                    time.sleep(random.uniform(*self.delay_randomization_ms) / 1000)

                    # Scrape the page
                    result = self.scraper.scrape_url_with_retry(page_link)

                    if result.get('status') == 'success':
                        pages_scraped += 1

                        # Add insights based on page type
                        if page in ['pricing', 'plans']:
                            # Look for pricing information
                            content = result.get('content', '').lower()
                            if '$' in content or '€' in content or '£' in content:
                                intel['summary_bullets'].append(f"Pricing page found with pricing info")
                            if 'free' in content or 'trial' in content:
                                intel['summary_bullets'].append(f"Free tier or trial mentioned")

                        elif page == 'about':
                            # Look for company info
                            content = result.get('content', '')
                            year_founded = re.search(r'founded in (\d{4})', content, re.IGNORECASE)
                            if year_founded:
                                intel['summary_bullets'].append(f"Founded in {year_founded.group(1)}")

                        elif page == 'contact':
                            # Extract additional contact info
                            content = result.get('content', '')
                            addresses = re.findall(r'\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd)',
                                                  content, re.IGNORECASE)
                            if addresses:
                                intel['summary_bullets'].append(f"Physical address found")

                except Exception as e:
                    self.logger.warning(f"Deep scrape failed for {page_link}: {e}")

        if pages_scraped > 0:
            intel['summary_bullets'].append(f"Deep scraped {pages_scraped} additional pages")

        return intel

    def calculate_lead_score(self, row_data: Dict[str, Any], all_link_intel: List[Dict[str, Any]]) -> Tuple[int, str]:
        """
        Calculate lead score based on weighted rubric.

        Args:
            row_data: Original row data
            all_link_intel: List of intelligence for all links

        Returns:
            Tuple of (score, rationale)
        """
        scores = {
            'icp_fit': 0,  # 25%
            'commercial_readiness': 0,  # 20%
            'engagement_signals': 0,  # 15%
            'technical_fit': 0,  # 15%
            'data_completeness': 0,  # 10%
            'authority_trust': 0,  # 10%
            'health': 0  # 5%
        }

        rationale_parts = []

        # Aggregate intelligence from all links
        aggregated = {
            'categories': [],
            'has_pricing': False,
            'has_cta': False,
            'has_contact': False,
            'tech_stack': [],
            'social_count': 0,
            'is_fresh': False,
            'has_linkedin': False,
            'has_crunchbase': False,
            'size_signals': []
        }

        for link_intel in all_link_intel:
            search_intel = link_intel.get('search_intel', {})
            scrape_intel = link_intel.get('scrape_intel', {})

            # Aggregate data
            if search_intel.get('category'):
                aggregated['categories'].append(search_intel['category'])
            if scrape_intel.get('pricing_cta'):
                aggregated['has_pricing'] = True
                aggregated['has_cta'] = True
            if scrape_intel.get('contact_capture'):
                aggregated['has_contact'] = True
            if scrape_intel.get('tech_signals'):
                aggregated['tech_stack'].extend(scrape_intel['tech_signals'])
            if scrape_intel.get('social_links'):
                aggregated['social_count'] += len(scrape_intel['social_links'])
            if 'current' in scrape_intel.get('freshness', '').lower():
                aggregated['is_fresh'] = True
            if search_intel.get('linkedin_presence'):
                aggregated['has_linkedin'] = True
            if search_intel.get('crunchbase_presence'):
                aggregated['has_crunchbase'] = True
            if search_intel.get('size_signals'):
                aggregated['size_signals'].extend(search_intel['size_signals'])

        # ICP Fit (25%)
        icp_score = 50  # Base score
        if aggregated['categories']:
            # Check against target categories (customize based on your ICP)
            target_categories = ['SaaS', 'Technology', 'E-commerce', 'Agency']
            if any(cat in target_categories for cat in aggregated['categories']):
                icp_score += 30
                rationale_parts.append("ICP match")
            else:
                rationale_parts.append("ICP partial")

        if aggregated['size_signals']:
            # Company has size indicators
            icp_score += 20

        scores['icp_fit'] = min(100, icp_score)

        # Commercial Readiness (20%)
        commercial_score = 0
        if aggregated['has_pricing']:
            commercial_score += 40
            rationale_parts.append("pricing visible")
        if aggregated['has_cta']:
            commercial_score += 30
        if aggregated['has_contact']:
            commercial_score += 30

        scores['commercial_readiness'] = min(100, commercial_score)

        # Engagement Signals (15%)
        engagement_score = 0
        if aggregated['is_fresh']:
            engagement_score += 40
            rationale_parts.append("active site")
        if aggregated['social_count'] > 0:
            engagement_score += min(40, aggregated['social_count'] * 10)
        if aggregated['has_linkedin']:
            engagement_score += 20
            rationale_parts.append("LinkedIn active")

        scores['engagement_signals'] = min(100, engagement_score)

        # Technical Fit (15%)
        tech_score = 50  # Base score
        if aggregated['tech_stack']:
            # Check for target technologies (customize based on your solution)
            target_tech = ['WordPress', 'Shopify', 'Google Analytics', 'HubSpot']
            matches = [t for t in aggregated['tech_stack'] if any(target in t for target in target_tech)]
            if matches:
                tech_score += 50
                rationale_parts.append(f"tech: {matches[0]}")

        scores['technical_fit'] = min(100, tech_score)

        # Data Completeness (10%)
        data_score = 0
        if all_link_intel:
            data_score += 30
        if len(all_link_intel) > 1:
            data_score += 30
        if aggregated['categories']:
            data_score += 20
        if aggregated['size_signals']:
            data_score += 20

        scores['data_completeness'] = min(100, data_score)

        # Authority/Trust (10%)
        authority_score = 0
        if aggregated['has_linkedin']:
            authority_score += 40
        if aggregated['has_crunchbase']:
            authority_score += 40
            rationale_parts.append("Crunchbase listed")
        if aggregated['social_count'] > 2:
            authority_score += 20

        scores['authority_trust'] = min(100, authority_score)

        # Health (5%)
        health_score = 50  # Base score
        if aggregated['is_fresh']:
            health_score += 25
        if all_link_intel and all(li.get('scrape_intel', {}).get('summary_bullets')
                                  for li in all_link_intel):
            health_score += 25

        scores['health'] = min(100, health_score)

        # Calculate weighted final score
        weights = {
            'icp_fit': 0.25,
            'commercial_readiness': 0.20,
            'engagement_signals': 0.15,
            'technical_fit': 0.15,
            'data_completeness': 0.10,
            'authority_trust': 0.10,
            'health': 0.05
        }

        final_score = sum(scores[key] * weights[key] for key in scores)
        final_score = round(final_score)

        # Build rationale
        if not rationale_parts:
            if final_score < 30:
                rationale_parts.append("limited data")
            elif final_score < 60:
                rationale_parts.append("partial match")
            else:
                rationale_parts.append("good potential")

        rationale = f"({'; '.join(rationale_parts[:4])})"

        return final_score, rationale

    def generate_final_report(self, all_link_intel: List[Dict[str, Any]]) -> str:
        """
        Generate comprehensive final report for all links.

        Args:
            all_link_intel: List of intelligence for all links

        Returns:
            Final report string
        """
        bullets = []

        # Summary of links processed
        bullets.append(f"• Analyzed {len(all_link_intel)} link(s)")

        # Categories found
        categories = []
        for intel in all_link_intel:
            if intel.get('search_intel', {}).get('category'):
                categories.append(intel['search_intel']['category'])
        if categories:
            unique_cats = list(set(categories))
            bullets.append(f"• Industries: {', '.join(unique_cats)}")

        # Technology stack
        all_tech = []
        for intel in all_link_intel:
            tech = intel.get('scrape_intel', {}).get('tech_signals', [])
            all_tech.extend(tech)
        if all_tech:
            unique_tech = list(set(all_tech))[:5]
            bullets.append(f"• Technologies: {', '.join(unique_tech)}")

        # Contact availability
        contact_methods = set()
        for intel in all_link_intel:
            methods = intel.get('scrape_intel', {}).get('contact_capture', [])
            contact_methods.update(methods)
        if contact_methods:
            bullets.append(f"• Contact methods: {', '.join(list(contact_methods)[:3])}")

        # Commercial indicators
        has_pricing = any(intel.get('scrape_intel', {}).get('pricing_cta') for intel in all_link_intel)
        if has_pricing:
            bullets.append("• Commercial: Pricing/CTA present")

        # Social presence
        total_social = sum(len(intel.get('scrape_intel', {}).get('social_links', []))
                          for intel in all_link_intel)
        if total_social > 0:
            bullets.append(f"• Social presence: {total_social} profile(s) found")

        # LinkedIn/Crunchbase
        has_linkedin = any(intel.get('search_intel', {}).get('linkedin_presence') for intel in all_link_intel)
        has_crunchbase = any(intel.get('search_intel', {}).get('crunchbase_presence') for intel in all_link_intel)

        if has_linkedin or has_crunchbase:
            presence = []
            if has_linkedin:
                presence.append("LinkedIn")
            if has_crunchbase:
                presence.append("Crunchbase")
            bullets.append(f"• Professional networks: {', '.join(presence)}")

        # Freshness
        is_fresh = any('current' in intel.get('scrape_intel', {}).get('freshness', '').lower()
                      for intel in all_link_intel)
        if is_fresh:
            bullets.append("• Site freshness: Recently updated")

        # Size signals
        all_size_signals = []
        for intel in all_link_intel:
            signals = intel.get('search_intel', {}).get('size_signals', [])
            all_size_signals.extend(signals)
        if all_size_signals:
            bullets.append(f"• Size indicators: {', '.join(all_size_signals[:2])}")

        # Key findings
        key_findings = []
        for intel in all_link_intel:
            if intel.get('scrape_intel', {}).get('value_proposition'):
                val_prop = intel['scrape_intel']['value_proposition'][:100]
                key_findings.append(f"Value prop: {val_prop}")
                break

        if key_findings:
            bullets.append(f"• {key_findings[0]}")

        # Warnings or issues
        errors = []
        for intel in all_link_intel:
            summary_bullets = intel.get('scrape_intel', {}).get('summary_bullets', [])
            if summary_bullets and isinstance(summary_bullets[0], str):
                if 'error' in summary_bullets[0].lower():
                    errors.append(intel['url'][:30])

        if errors:
            bullets.append(f"• Issues: Some links had errors")

        # Ensure we have 6-12 bullets
        if len(bullets) < 6:
            bullets.append("• Additional analysis may be needed")

        return '\n'.join(bullets[:12])

    def process_row(self, row_index: int, row_data: List[str], headers: List[str]) -> Dict[str, Any]:
        """
        Process a single row: discover links, gather intelligence, calculate score.

        Args:
            row_index: Row number (0-based)
            row_data: List of cell values
            headers: List of column headers

        Returns:
            Dictionary with all enrichment data
        """
        # Create row dictionary for easier access
        row_dict = {headers[i]: row_data[i] if i < len(row_data) else ''
                   for i in range(len(headers))}

        # Discover all links in the row
        links = self.discover_links_in_row(row_data)

        self.logger.info(f"[ROW {row_index + 1}] found {len(links)} links " +
                        f"(processing up to {min(len(links), self.max_links_per_row)}; " +
                        f"limit remaining: {self.daily_link_limit - self.links_processed_today})")

        # Process each link
        all_link_intel = []

        for i, url in enumerate(links):
            # Check daily limit
            if self.links_processed_today >= self.daily_link_limit:
                self.logger.warning(f"[LIMIT] Daily link limit reached ({self.daily_link_limit})")
                break

            # Check if already processed (idempotency)
            ledger_key = (row_index, url)
            if ledger_key in self.processing_ledger and not self.force_refresh:
                if self.processing_ledger[ledger_key] == 'done':
                    self.logger.info(f"  L{i+1} {url[:50]} → [SKIPPED - already processed]")
                    self.stats['links_skipped'] += 1
                    continue

            # Process the link
            self.logger.info(f"  L{i+1} {url[:50]} → search...")

            link_intel = {
                'url': url,
                'search_intel': {},
                'scrape_intel': {}
            }

            try:
                # Search intelligence
                search_intel = self.search_link_intelligence(url)
                link_intel['search_intel'] = search_intel

                self.logger.info(f"  L{i+1} {url[:50]} → scrape...")

                # Scrape intelligence
                scrape_intel = self.scrape_link_intelligence(url)
                link_intel['scrape_intel'] = scrape_intel

                # Mark as processed
                self.processing_ledger[ledger_key] = 'done'
                self.links_processed_today += 1
                self.stats['links_processed'] += 1

                self.logger.info(f"  L{i+1} {url[:50]} → writeback... [OK]")

            except Exception as e:
                self.logger.error(f"  L{i+1} {url[:50]} → [ERROR: {str(e)[:50]}]")
                link_intel['error'] = str(e)
                self.processing_ledger[ledger_key] = 'error'
                self.stats['errors'] += 1

            all_link_intel.append(link_intel)

        # Generate final report
        final_report = self.generate_final_report(all_link_intel) if all_link_intel else "No links processed"

        # Calculate lead score
        lead_score, rationale = self.calculate_lead_score(row_dict, all_link_intel)

        # Prepare enrichment data for writeback
        enrichment_data = {
            'links': all_link_intel,
            'final_report': final_report,
            'lead_score': lead_score,
            'lead_rationale': rationale,
            'row_dict': row_dict
        }

        return enrichment_data

    def write_enrichment_to_sheet(self, row_index: int, enrichment_data: Dict[str, Any],
                                 sheet_data: List[List[str]]) -> bool:
        """
        Write enrichment data to Google Sheet starting after column AX.

        Args:
            row_index: Row number (0-based)
            enrichment_data: Enrichment data to write
            sheet_data: Current sheet data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current headers
            headers = sheet_data[0] if sheet_data else []

            # Find first empty column after AX
            start_col = self._find_empty_columns_after_ax(headers)

            # Prepare column data
            columns_to_write = []
            column_headers = []

            # Add columns for each link
            for i, link_intel in enumerate(enrichment_data['links']):
                # L{i} URL
                column_headers.append(f"L{i+1} URL")
                columns_to_write.append(link_intel['url'])

                # L{i} Search Summary
                column_headers.append(f"L{i+1} Search Summary")
                search_bullets = link_intel.get('search_intel', {}).get('summary_bullets', [])
                columns_to_write.append(' | '.join(search_bullets))

                # L{i} Scrape Summary
                column_headers.append(f"L{i+1} Scrape Summary")
                scrape_bullets = link_intel.get('scrape_intel', {}).get('summary_bullets', [])
                columns_to_write.append(' | '.join(scrape_bullets))

            # Add final report and lead score
            column_headers.append("Final Report (All Links)")
            columns_to_write.append(enrichment_data['final_report'])

            column_headers.append("Lead Score (0-100)")
            columns_to_write.append(f"{enrichment_data['lead_score']} {enrichment_data['lead_rationale']}")

            # Add ARP fields if enabled
            if self.arp_mode:
                arp_data = self._generate_arp_data(enrichment_data)

                arp_headers = [
                    "ARP: Primary Domain",
                    "ARP: Company Name",
                    "ARP: Category/Industry",
                    "ARP: Country/Region",
                    "ARP: Tech Stack Highlights",
                    "ARP: Contact Channels",
                    "ARP: Pricing/Plans Presence",
                    "ARP: Recent Activity",
                    "ARP: LinkedIn Presence",
                    "ARP: Notes"
                ]

                column_headers.extend(arp_headers)
                columns_to_write.extend([
                    arp_data.get('primary_domain', ''),
                    arp_data.get('company_name', ''),
                    arp_data.get('category', ''),
                    arp_data.get('country', ''),
                    arp_data.get('tech_stack', ''),
                    arp_data.get('contact_channels', ''),
                    arp_data.get('pricing_presence', ''),
                    arp_data.get('recent_activity', ''),
                    arp_data.get('linkedin_presence', ''),
                    arp_data.get('notes', '')
                ])

            # Write headers if needed
            if row_index == 1 or not self._headers_exist(headers, column_headers, start_col):
                self._write_headers(column_headers, start_col)
                self.stats['columns_created'] += len(column_headers)

            # Write row data
            self._write_row_data(row_index, columns_to_write, start_col)

            return True

        except Exception as e:
            self.logger.error(f"Failed to write enrichment for row {row_index}: {e}")
            return False

    def _find_empty_columns_after_ax(self, headers: List[str]) -> int:
        """Find first empty column after AX (column 49)."""
        # Start checking from column AY (index 50)
        start_check = AX_COLUMN_INDEX + 1

        # Find first completely empty column
        for i in range(start_check, len(headers)):
            if not headers[i] or headers[i].strip() == '':
                return i

        # If no empty column found, use next column after last
        return max(len(headers), start_check)

    def _headers_exist(self, current_headers: List[str], new_headers: List[str], start_col: int) -> bool:
        """Check if headers already exist."""
        for i, header in enumerate(new_headers):
            col_index = start_col + i
            if col_index >= len(current_headers):
                return False
            if current_headers[col_index] != header:
                return False
        return True

    def _write_headers(self, headers: List[str], start_col: int):
        """Write headers to sheet."""
        # Convert column index to A1 notation
        start_col_letter = self._index_to_column_letter(start_col)
        end_col_letter = self._index_to_column_letter(start_col + len(headers) - 1)

        range_name = f"{self.tab_name}!{start_col_letter}1:{end_col_letter}1"

        body = {
            'values': [headers]
        }

        self.service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        self.logger.info(f"[WRITE] Created {len(headers)} column headers starting at {start_col_letter}")

    def _write_row_data(self, row_index: int, data: List[str], start_col: int):
        """Write data to a specific row."""
        # Convert to A1 notation (row_index is 0-based, sheets are 1-based)
        sheet_row = row_index + 1
        start_col_letter = self._index_to_column_letter(start_col)
        end_col_letter = self._index_to_column_letter(start_col + len(data) - 1)

        range_name = f"{self.tab_name}!{start_col_letter}{sheet_row}:{end_col_letter}{sheet_row}"

        body = {
            'values': [data]
        }

        self.service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

    def _index_to_column_letter(self, index: int) -> str:
        """Convert column index to letter (0 -> A, 49 -> AX, etc)."""
        result = ""
        while index >= 0:
            result = chr(index % 26 + ord('A')) + result
            index = index // 26 - 1
        return result

    def _generate_arp_data(self, enrichment_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate ARP (Automated Research & Product) enrichment fields."""
        arp_data = {}

        # Extract from all links
        all_links = enrichment_data.get('links', [])

        # Primary domain
        if all_links:
            parsed = urlparse(all_links[0]['url'])
            arp_data['primary_domain'] = parsed.netloc.replace('www.', '')

        # Company name (from search or domain)
        for link in all_links:
            brand = link.get('search_intel', {}).get('brand')
            if brand:
                arp_data['company_name'] = brand
                break

        if not arp_data.get('company_name') and arp_data.get('primary_domain'):
            arp_data['company_name'] = arp_data['primary_domain'].split('.')[0].title()

        # Category/Industry
        categories = []
        for link in all_links:
            cat = link.get('search_intel', {}).get('category')
            if cat:
                categories.append(cat)
        arp_data['category'] = ', '.join(list(set(categories)))

        # Country/Region (would need geocoding or more analysis)
        arp_data['country'] = 'Not determined'

        # Tech stack
        all_tech = []
        for link in all_links:
            tech = link.get('scrape_intel', {}).get('tech_signals', [])
            all_tech.extend(tech)
        arp_data['tech_stack'] = ', '.join(list(set(all_tech))[:5])

        # Contact channels
        contact_methods = set()
        for link in all_links:
            methods = link.get('scrape_intel', {}).get('contact_capture', [])
            contact_methods.update(methods)
        arp_data['contact_channels'] = ', '.join(list(contact_methods))

        # Pricing presence
        has_pricing = any(link.get('scrape_intel', {}).get('pricing_cta') for link in all_links)
        arp_data['pricing_presence'] = 'Y' if has_pricing else 'N'

        # Recent activity
        is_fresh = any('current' in link.get('scrape_intel', {}).get('freshness', '').lower()
                      for link in all_links)
        arp_data['recent_activity'] = 'Active' if is_fresh else 'Unknown'

        # LinkedIn presence
        linkedin_url = ''
        for link in all_links:
            li_presence = link.get('search_intel', {}).get('linkedin_presence')
            if li_presence:
                linkedin_url = li_presence
                break

        if linkedin_url:
            arp_data['linkedin_presence'] = f"Y + {linkedin_url}"
        else:
            arp_data['linkedin_presence'] = 'N'

        # Notes
        notes = []
        if enrichment_data.get('lead_score', 0) > 70:
            notes.append("High potential lead")
        if len(all_links) > 3:
            notes.append(f"Multiple web properties ({len(all_links)})")

        arp_data['notes'] = '; '.join(notes) if notes else ''

        return arp_data

    def run(self) -> Dict[str, Any]:
        """
        Main execution method for the orchestrator.

        Returns:
            Statistics dictionary
        """
        self.stats['start_time'] = datetime.now()

        self.logger.info("[START] Starting Link Intelligence Orchestrator")
        self.logger.info(f"Configuration: Sheet={self.sheet_id}, Tab={self.tab_name}, " +
                        f"Scope={self.row_scope}, Daily Limit={self.daily_link_limit}")

        # Authenticate
        if not self.authenticate():
            self.logger.error("Failed to authenticate with Google Sheets")
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
                self.logger.error("No data found in sheet")
                return self.stats

            headers = sheet_data[0]

            # Determine row range
            if self.row_scope == 'all rows':
                start_row = 1  # Skip header
                end_row = len(sheet_data)
            else:
                # Parse range like "2:500"
                parts = self.row_scope.split(':')
                start_row = int(parts[0]) - 1  # Convert to 0-based
                end_row = min(int(parts[1]), len(sheet_data)) if len(parts) > 1 else len(sheet_data)

            self.logger.info(f"Processing rows {start_row + 1} to {end_row}")

            # Process each row
            for row_index in range(start_row, end_row):
                if row_index >= len(sheet_data):
                    break

                row_data = sheet_data[row_index]

                # Skip empty rows
                if not any(row_data):
                    continue

                # Process the row
                enrichment_data = self.process_row(row_index, row_data, headers)

                # Write enrichment to sheet
                if enrichment_data.get('links'):
                    self.write_enrichment_to_sheet(row_index, enrichment_data, sheet_data)

                self.stats['rows_processed'] += 1

                # Check daily limit
                if self.links_processed_today >= self.daily_link_limit:
                    self.logger.warning(f"Daily limit of {self.daily_link_limit} links reached")
                    break

        except Exception as e:
            self.logger.error(f"Fatal error during processing: {e}")
            self.logger.error(traceback.format_exc())

        # Final statistics
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        self.logger.info("=" * 60)
        self.logger.info("FINAL STATISTICS")
        self.logger.info("=" * 60)
        self.logger.info(f"Rows processed: {self.stats['rows_processed']}")
        self.logger.info(f"Links found: {self.stats['links_found']}")
        self.logger.info(f"Links processed: {self.stats['links_processed']}")
        self.logger.info(f"Links skipped: {self.stats['links_skipped']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info(f"Columns created: {self.stats['columns_created']}")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info("=" * 60)

        return self.stats


if __name__ == "__main__":
    # Example configuration
    config = {
        'SHEET_ID': 'your-sheet-id-here',
        'TAB_NAME': 'Sheet1',
        'ROW_SCOPE': 'all rows',
        'DAILY_LINK_LIMIT': 500,
        'MAX_LINKS_PER_ROW': 10,
        'SEARCH_ENGINE': 'Google',
        'SCRAPE_DEPTH': 'light',
        'ARP_MODE': 'on',
        'USER_AGENT_ID': 'LinkIntelBot/1.0',
        'ROBOTS_RESPECT': True,
        'DELAY_RANDOMIZATION_MS': (800, 2500),
        'RETRY_POLICY': {'attempts': 3, 'backoff': [2, 4, 8]},
        'FORCE_REFRESH': False
    }

    orchestrator = LinkIntelligenceOrchestrator(config)
    stats = orchestrator.run()