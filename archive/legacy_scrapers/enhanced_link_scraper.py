"""
🦈 LeadShark Enhanced Link Scraper
Platform-specific data extraction with structured output
"""

import re
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, urljoin
from datetime import datetime
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class URLClassifier:
    """Classify URLs by platform type"""

    PLATFORM_PATTERNS = {
        'linkedin': [
            r'linkedin\.com/in/',
            r'linkedin\.com/company/',
            r'linkedin\.com/pub/',
        ],
        'twitter': [
            r'twitter\.com/',
            r'x\.com/',
        ],
        'github': [
            r'github\.com/',
        ],
        'facebook': [
            r'facebook\.com/',
            r'fb\.com/',
        ],
        'instagram': [
            r'instagram\.com/',
        ],
        'youtube': [
            r'youtube\.com/channel/',
            r'youtube\.com/c/',
            r'youtube\.com/user/',
            r'youtube\.com/@',
        ],
        'crunchbase': [
            r'crunchbase\.com/organization/',
            r'crunchbase\.com/person/',
        ],
        'angellist': [
            r'angel\.co/',
            r'wellfound\.com/',
        ],
        'tiktok': [
            r'tiktok\.com/@',
        ],
    }

    @classmethod
    def classify(cls, url: str) -> str:
        """Classify URL by platform type"""
        url_lower = url.lower()

        for platform, patterns in cls.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return platform

        # Check if it's a job posting
        if any(keyword in url_lower for keyword in ['/jobs/', '/careers/', '/job/', '/career/']):
            return 'job'

        # Check if it's a contact page
        if any(keyword in url_lower for keyword in ['/contact', '/about/contact', '/get-in-touch']):
            return 'contact'

        # Default to website or generic
        parsed = urlparse(url)
        if parsed.netloc:
            return 'website'

        return 'generic'


class PlatformExtractor:
    """Base class for platform-specific data extraction"""

    def __init__(self, html: str, url: str):
        self.html = html
        self.url = url
        self.soup = BeautifulSoup(html, 'html.parser')

    def extract_meta_tags(self) -> Dict[str, str]:
        """Extract meta tags"""
        meta = {}

        # OpenGraph tags
        for tag in self.soup.find_all('meta', property=re.compile(r'^og:')):
            key = tag.get('property', '').replace('og:', '')
            meta[f'og_{key}'] = tag.get('content', '')

        # Twitter cards
        for tag in self.soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')}):
            key = tag.get('name', '').replace('twitter:', '')
            meta[f'twitter_{key}'] = tag.get('content', '')

        # Standard meta tags
        for name in ['description', 'keywords', 'author']:
            tag = self.soup.find('meta', attrs={'name': name})
            if tag:
                meta[name] = tag.get('content', '')

        return meta

    def extract_json_ld(self) -> List[Dict]:
        """Extract JSON-LD structured data"""
        json_ld_scripts = self.soup.find_all('script', type='application/ld+json')
        results = []

        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                results.append(data)
            except:
                continue

        return results

    def extract_emails(self) -> List[str]:
        """Extract email addresses"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = self.soup.get_text()
        emails = re.findall(email_pattern, text)
        return list(set(emails))[:5]  # Limit to 5 unique emails

    def extract_phones(self) -> List[str]:
        """Extract phone numbers"""
        phone_patterns = [
            r'\+?1?\s*\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})',
            r'\+\d{1,3}\s?\d{1,14}',
        ]

        text = self.soup.get_text()
        phones = []

        for pattern in phone_patterns:
            found = re.findall(pattern, text)
            phones.extend([match if isinstance(match, str) else ''.join(match) for match in found])

        return list(set(phones))[:3]  # Limit to 3 unique phones


class LinkedInExtractor(PlatformExtractor):
    """Extract LinkedIn profile/company data"""

    def extract(self) -> Dict[str, Any]:
        """Extract LinkedIn-specific fields"""
        data = {
            'source': 'linkedin',
            'url': self.url,
            'extracted': {
                'title': None,
                'name': None,
                'company': None,
                'location': None,
                'description': None,
                'key_fields': {},
                'contacts': {'emails': [], 'phones': []},
                'metrics': {},
                'top_items': [],
            }
        }

        # Try to extract from meta tags first
        meta = self.extract_meta_tags()

        # Title from OpenGraph or page title
        data['extracted']['title'] = (
            meta.get('og_title') or
            self.soup.find('title').text if self.soup.find('title') else None
        )

        # Description
        data['extracted']['description'] = (
            meta.get('og_description') or
            meta.get('description', '')
        )[:600]

        # Try to extract structured data
        json_ld = self.extract_json_ld()
        for item in json_ld:
            if item.get('@type') == 'Person':
                data['extracted']['name'] = item.get('name')
                data['extracted']['title'] = item.get('jobTitle')
                data['extracted']['company'] = item.get('worksFor', {}).get('name') if isinstance(item.get('worksFor'), dict) else None
            elif item.get('@type') == 'Organization':
                data['extracted']['name'] = item.get('name')
                data['extracted']['description'] = item.get('description', '')[:600]

        # LinkedIn-specific fields
        if '/in/' in self.url:  # Profile
            data['extracted']['key_fields']['profile_type'] = 'personal'
        elif '/company/' in self.url:  # Company
            data['extracted']['key_fields']['profile_type'] = 'company'

        return data


class WebsiteExtractor(PlatformExtractor):
    """Extract generic website/company data"""

    def extract(self) -> Dict[str, Any]:
        """Extract website-specific fields"""
        data = {
            'source': 'website',
            'url': self.url,
            'extracted': {
                'title': None,
                'name': None,
                'company': None,
                'location': None,
                'description': None,
                'key_fields': {},
                'contacts': {'emails': [], 'phones': []},
                'metrics': {},
                'top_items': [],
            }
        }

        meta = self.extract_meta_tags()
        json_ld = self.extract_json_ld()

        # Title
        data['extracted']['title'] = (
            meta.get('og_title') or
            self.soup.find('title').text if self.soup.find('title') else None
        )

        # Description
        data['extracted']['description'] = (
            meta.get('og_description') or
            meta.get('description', '')
        )[:600]

        # Extract from JSON-LD
        for item in json_ld:
            if item.get('@type') == 'Organization':
                data['extracted']['company'] = item.get('name')
                data['extracted']['name'] = item.get('name')

                # Location
                if 'address' in item:
                    addr = item['address']
                    if isinstance(addr, dict):
                        data['extracted']['location'] = f"{addr.get('addressLocality', '')}, {addr.get('addressRegion', '')}"

                # Contact info
                if 'email' in item:
                    data['extracted']['contacts']['emails'].append(item['email'])
                if 'telephone' in item:
                    data['extracted']['contacts']['phones'].append(item['telephone'])

        # Extract emails and phones from content
        data['extracted']['contacts']['emails'] = list(set(
            data['extracted']['contacts']['emails'] + self.extract_emails()
        ))[:5]

        data['extracted']['contacts']['phones'] = list(set(
            data['extracted']['contacts']['phones'] + self.extract_phones()
        ))[:3]

        # Extract services/products from headings and lists
        services = []
        for heading in self.soup.find_all(['h2', 'h3']):
            text = heading.get_text().strip()
            if any(keyword in text.lower() for keyword in ['service', 'product', 'solution', 'offering']):
                # Get following list items
                next_ul = heading.find_next('ul')
                if next_ul:
                    services.extend([li.get_text().strip() for li in next_ul.find_all('li')[:5]])

        if services:
            data['extracted']['key_fields']['services_products'] = services[:5]

        return data


class TwitterExtractor(PlatformExtractor):
    """Extract Twitter/X profile data"""

    def extract(self) -> Dict[str, Any]:
        """Extract Twitter-specific fields"""
        data = {
            'source': 'twitter',
            'url': self.url,
            'extracted': {
                'title': None,
                'name': None,
                'company': None,
                'location': None,
                'description': None,
                'key_fields': {},
                'contacts': {'emails': [], 'phones': []},
                'metrics': {},
                'top_items': [],
            }
        }

        meta = self.extract_meta_tags()

        # Name and handle
        data['extracted']['name'] = meta.get('og_title', '')
        data['extracted']['title'] = meta.get('twitter_title', '')

        # Bio/description
        data['extracted']['description'] = (
            meta.get('twitter_description') or
            meta.get('og_description', '')
        )[:300]

        # Handle from URL
        parsed = urlparse(self.url)
        handle = parsed.path.strip('/').split('/')[0] if parsed.path else None
        if handle:
            data['extracted']['key_fields']['handle'] = '@' + handle

        return data


class GitHubExtractor(PlatformExtractor):
    """Extract GitHub profile/repo data"""

    def extract(self) -> Dict[str, Any]:
        """Extract GitHub-specific fields"""
        data = {
            'source': 'github',
            'url': self.url,
            'extracted': {
                'title': None,
                'name': None,
                'company': None,
                'location': None,
                'description': None,
                'key_fields': {},
                'contacts': {'emails': [], 'phones': []},
                'metrics': {},
                'top_items': [],
            }
        }

        meta = self.extract_meta_tags()

        # Name and title
        data['extracted']['title'] = meta.get('og_title', '')
        data['extracted']['description'] = meta.get('og_description', '')[:600]

        # Username from URL
        parsed = urlparse(self.url)
        username = parsed.path.strip('/').split('/')[0] if parsed.path else None
        if username:
            data['extracted']['key_fields']['username'] = username

        return data


class JobPostingExtractor(PlatformExtractor):
    """Extract job posting data"""

    def extract(self) -> Dict[str, Any]:
        """Extract job posting fields"""
        data = {
            'source': 'job',
            'url': self.url,
            'extracted': {
                'title': None,
                'name': None,
                'company': None,
                'location': None,
                'description': None,
                'key_fields': {},
                'contacts': {'emails': [], 'phones': []},
                'metrics': {},
                'top_items': [],
            }
        }

        meta = self.extract_meta_tags()
        json_ld = self.extract_json_ld()

        # Extract from JSON-LD (common for job postings)
        for item in json_ld:
            if item.get('@type') == 'JobPosting':
                data['extracted']['title'] = item.get('title')
                data['extracted']['company'] = item.get('hiringOrganization', {}).get('name')
                data['extracted']['location'] = item.get('jobLocation', {}).get('address', {}).get('addressLocality')
                data['extracted']['description'] = item.get('description', '')[:600]

                data['extracted']['key_fields']['employment_type'] = item.get('employmentType')
                data['extracted']['key_fields']['posted_date'] = item.get('datePosted')

        # Fallback to meta tags
        if not data['extracted']['title']:
            data['extracted']['title'] = meta.get('og_title', '')
        if not data['extracted']['description']:
            data['extracted']['description'] = meta.get('og_description', '')[:600]

        return data


class ContactPageExtractor(PlatformExtractor):
    """Extract contact page data"""

    def extract(self) -> Dict[str, Any]:
        """Extract contact information"""
        data = {
            'source': 'contact',
            'url': self.url,
            'extracted': {
                'title': None,
                'name': None,
                'company': None,
                'location': None,
                'description': None,
                'key_fields': {},
                'contacts': {'emails': [], 'phones': []},
                'metrics': {},
                'top_items': [],
            }
        }

        # Extract all emails and phones
        data['extracted']['contacts']['emails'] = self.extract_emails()
        data['extracted']['contacts']['phones'] = self.extract_phones()

        # Check for contact form
        has_form = bool(self.soup.find('form'))
        data['extracted']['key_fields']['contact_form'] = has_form

        # Title
        if self.soup.find('title'):
            data['extracted']['title'] = self.soup.find('title').text

        return data


class GenericExtractor(PlatformExtractor):
    """Extract generic page data"""

    def extract(self) -> Dict[str, Any]:
        """Extract generic fields"""
        data = {
            'source': 'generic',
            'url': self.url,
            'extracted': {
                'title': None,
                'name': None,
                'company': None,
                'location': None,
                'description': None,
                'key_fields': {},
                'contacts': {'emails': [], 'phones': []},
                'metrics': {},
                'top_items': [],
            }
        }

        meta = self.extract_meta_tags()

        # Title
        data['extracted']['title'] = (
            meta.get('og_title') or
            self.soup.find('title').text if self.soup.find('title') else None
        )

        # Description
        data['extracted']['description'] = (
            meta.get('og_description') or
            meta.get('description', '')
        )[:600]

        # Author
        if meta.get('author'):
            data['extracted']['key_fields']['author'] = meta['author']

        # Extract text snippet
        paragraphs = self.soup.find_all('p')[:3]
        if paragraphs:
            data['extracted']['key_fields']['excerpt'] = ' '.join([p.get_text().strip() for p in paragraphs])[:300]

        return data


class EnhancedLinkScraper:
    """Main scraper with platform-specific extraction"""

    EXTRACTOR_MAP = {
        'linkedin': LinkedInExtractor,
        'website': WebsiteExtractor,
        'twitter': TwitterExtractor,
        'github': GitHubExtractor,
        'job': JobPostingExtractor,
        'contact': ContactPageExtractor,
        'generic': GenericExtractor,
    }

    def __init__(self, rate_limit_delay: float = 1.0):
        self.rate_limit_delay = rate_limit_delay
        self.domain_last_request = defaultdict(float)
        self.session = requests.Session()

        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]

    def _get_headers(self, platform: str = 'generic') -> Dict[str, str]:
        """Get platform-specific headers"""
        import random

        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        return headers

    def _respect_rate_limit(self, domain: str):
        """Enforce per-domain rate limiting"""
        now = time.time()
        last_request = self.domain_last_request[domain]

        time_since_last = now - last_request
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)

        self.domain_last_request[domain] = time.time()

    def scrape_link(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """Scrape a single link with platform-specific extraction"""

        # Classify URL
        platform = URLClassifier.classify(url)

        # Parse domain for rate limiting
        parsed = urlparse(url)
        domain = parsed.netloc

        # Respect rate limit
        self._respect_rate_limit(domain)

        # Try to fetch with retries
        for attempt in range(max_retries):
            try:
                headers = self._get_headers(platform)
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=15,
                    allow_redirects=True
                )

                # Check for auth required or blocked
                if response.status_code == 401 or response.status_code == 403:
                    return self._create_error_result(url, platform, 'Authentication required or access denied')

                if response.status_code == 429:
                    logger.warning(f"Rate limited on {domain}, attempt {attempt + 1}")
                    time.sleep((attempt + 1) * 2)
                    continue

                if response.status_code != 200:
                    if attempt < max_retries - 1:
                        time.sleep((attempt + 1) * 1)
                        continue
                    return self._create_error_result(url, platform, f'HTTP {response.status_code}')

                # Extract data using platform-specific extractor
                html = response.text
                extractor_class = self.EXTRACTOR_MAP.get(platform, GenericExtractor)
                extractor = extractor_class(html, url)

                data = extractor.extract()
                data['confidence'] = self._calculate_confidence(data)
                data['scrape_timestamp'] = datetime.utcnow().isoformat() + 'Z'

                return data

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on {url}, attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 1)
                    continue
                return self._create_error_result(url, platform, 'Timeout')

            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 1)
                    continue
                return self._create_error_result(url, platform, str(e))

        return self._create_error_result(url, platform, 'Max retries exceeded')

    def _create_error_result(self, url: str, platform: str, error_msg: str) -> Dict[str, Any]:
        """Create error result structure"""
        return {
            'source': platform,
            'url': url,
            'extracted': {
                'title': None,
                'name': None,
                'company': None,
                'location': None,
                'description': None,
                'key_fields': {'error': error_msg},
                'contacts': {'emails': [], 'phones': []},
                'metrics': {},
                'top_items': [],
            },
            'confidence': 0.0,
            'scrape_timestamp': datetime.utcnow().isoformat() + 'Z',
            'error': error_msg
        }

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data completeness"""
        fields = data.get('extracted', {})

        score = 0.0
        max_score = 7.0

        # Score based on field presence
        if fields.get('title'):
            score += 1.0
        if fields.get('description') and len(fields['description']) > 50:
            score += 1.5
        if fields.get('name') or fields.get('company'):
            score += 1.0
        if fields.get('location'):
            score += 0.5
        if fields.get('contacts', {}).get('emails'):
            score += 1.0
        if fields.get('key_fields') and len(fields['key_fields']) > 0:
            score += 1.0
        if fields.get('metrics') and len(fields['metrics']) > 0:
            score += 1.0

        return round((score / max_score) * 100, 1)