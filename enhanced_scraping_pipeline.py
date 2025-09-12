import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any
import logging

class EnhancedScrapingPipeline:
    """
    Enhanced web scraping pipeline with robust error handling,
    rate limiting, and platform-specific optimizations
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        self.setup_logging()
        
        # Rate limiting configuration
        self.request_delays = {
            'linkedin.com': 3,     # LinkedIn is strict
            'facebook.com': 4,     # Facebook is very strict
            'twitter.com': 2,      # Twitter/X moderate
            'x.com': 2,           # Twitter/X moderate
            'default': 1.5        # General sites
        }
        
        # Platform-specific configurations
        self.platform_configs = {
            'linkedin.com': {
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Cache-Control': 'no-cache',
                },
                'timeout': 15,
                'max_retries': 2
            },
            'facebook.com': {
                'headers': {
                    'Accept-Encoding': 'identity',  # Disable compression
                    'Accept-Language': 'en-US,en;q=0.9',
                },
                'timeout': 20,
                'max_retries': 1  # Facebook blocks aggressively
            },
            'twitter.com': {
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                },
                'timeout': 12,
                'max_retries': 2
            },
            'x.com': {
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                },
                'timeout': 12,
                'max_retries': 2
            }
        }
    
    def setup_session(self):
        """Configure the requests session with default headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
    
    def setup_logging(self):
        """Setup logging for the scraping pipeline"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc.lower()
        except:
            return 'unknown'
    
    def get_platform_config(self, url: str) -> Dict:
        """Get platform-specific configuration"""
        domain = self.get_domain(url)
        
        # Check for specific platform configurations
        for platform, config in self.platform_configs.items():
            if platform in domain:
                return config
        
        # Default configuration
        return {
            'headers': {},
            'timeout': 10,
            'max_retries': 3
        }
    
    def get_request_delay(self, url: str) -> float:
        """Get appropriate delay for the platform"""
        domain = self.get_domain(url)
        
        for platform, delay in self.request_delays.items():
            if platform in domain:
                return delay
        
        return self.request_delays['default']
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def clean_content(self, soup: BeautifulSoup, url: str) -> str:
        """Clean and extract content based on platform"""
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header']):
            element.decompose()
        
        domain = self.get_domain(url)
        text_content = ""
        
        # Platform-specific content extraction
        if 'linkedin.com' in domain:
            # LinkedIn specific selectors
            content_selectors = [
                '.pv-about-section',
                '.pv-top-card-section',
                '.org-top-card-summary-info-list',
                '.org-about-us-section',
                'main[role=\"main\"]',
                '.artdeco-card',
                'section'
            ]
            
            extracted_text = []
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10:  # Only meaningful content
                        extracted_text.append(text)
            
            text_content = '\\n'.join(extracted_text)
        
        elif 'facebook.com' in domain:
            # Facebook specific selectors
            content_selectors = [
                '[data-pagelet=\"page\"]',
                '.intro',
                '[role=\"main\"]',
                '.userContent',
                '.story_body_container'
            ]
            
            extracted_text = []
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10:
                        extracted_text.append(text)
            
            text_content = '\\n'.join(extracted_text)
        
        elif 'twitter.com' in domain or 'x.com' in domain:
            # Twitter/X specific selectors
            content_selectors = [
                '[data-testid=\"UserProfileHeader_Items\"]',
                '[data-testid=\"UserDescription\"]',
                '[data-testid=\"tweet\"]',
                'main[role=\"main\"]',
                '.profile',
                '.ProfileHeaderCard'
            ]
            
            extracted_text = []
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10:
                        extracted_text.append(text)
            
            text_content = '\\n'.join(extracted_text)
        
        else:
            # General content extraction
            # Priority order: main content, articles, divs with content
            content_selectors = [
                'main',
                'article',
                '.content',
                '.main-content',
                '#content',
                '#main',
                'body'
            ]
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    text_content = element.get_text(strip=True)
                    break
            
            if not text_content:
                text_content = soup.get_text(strip=True)
        
        # Clean up whitespace and formatting
        if text_content:
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = ' '.join(chunk for chunk in chunks if chunk)
            text_content = re.sub(r'\\s+', ' ', text_content).strip()
        
        return text_content
    
    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from the page"""
        metadata = {}
        
        # Title
        title_tag = soup.find('title')
        metadata['title'] = title_tag.get_text().strip() if title_tag else ""
        
        # Meta tags
        meta_tags = {
            'description': ['name', 'description'],
            'keywords': ['name', 'keywords'],
            'og_title': ['property', 'og:title'],
            'og_description': ['property', 'og:description'],
            'og_type': ['property', 'og:type'],
            'og_url': ['property', 'og:url'],
            'og_image': ['property', 'og:image'],
            'twitter_title': ['name', 'twitter:title'],
            'twitter_description': ['name', 'twitter:description'],
            'twitter_card': ['name', 'twitter:card']
        }
        
        for key, (attr_name, attr_value) in meta_tags.items():
            meta_tag = soup.find('meta', attrs={attr_name: attr_value})
            if meta_tag:
                metadata[key] = meta_tag.get('content', '').strip()
        
        return metadata
    
    def scrape_url_with_retry(self, url: str) -> Dict[str, Any]:
        """Scrape URL with retry logic and error handling"""
        
        if not self.validate_url(url):
            return {
                'url': url,
                'status': 'failed',
                'error': 'Invalid URL format',
                'content': '',
                'metadata': {},
                'response_code': None
            }
        
        config = self.get_platform_config(url)
        delay = self.get_request_delay(url)
        max_retries = config.get('max_retries', 3)
        
        self.logger.info(f"Scraping {url} (max_retries: {max_retries}, delay: {delay}s)")
        
        for attempt in range(max_retries + 1):
            try:
                # Apply platform-specific headers
                session_headers = self.session.headers.copy()
                session_headers.update(config.get('headers', {}))
                
                # Make request
                response = self.session.get(
                    url,
                    headers=session_headers,
                    timeout=config.get('timeout', 10),
                    allow_redirects=True
                )
                
                # Handle different response codes
                if response.status_code == 200:
                    # Success - parse content
                    try:
                        # Detect encoding
                        if response.encoding == 'ISO-8859-1':
                            response.encoding = response.apparent_encoding
                        
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract content and metadata
                        content = self.clean_content(soup, url)
                        metadata = self.extract_metadata(soup)
                        
                        result = {
                            'url': url,
                            'status': 'success',
                            'content': content[:5000] + "..." if len(content) > 5000 else content,
                            'full_content_length': len(content),
                            'metadata': metadata,
                            'response_code': response.status_code,
                            'content_type': response.headers.get('content-type', ''),
                            'final_url': response.url,
                            'attempts': attempt + 1
                        }
                        
                        self.logger.info(f"Successfully scraped {url} ({len(content)} chars)")
                        return result
                        
                    except Exception as e:
                        self.logger.error(f"Content parsing failed for {url}: {str(e)}")
                        return {
                            'url': url,
                            'status': 'failed',
                            'error': f'Content parsing error: {str(e)}',
                            'content': '',
                            'metadata': {},
                            'response_code': response.status_code,
                            'attempts': attempt + 1
                        }
                
                elif response.status_code == 999:
                    # LinkedIn anti-bot protection
                    self.logger.warning(f"Anti-bot protection detected for {url}")
                    return {
                        'url': url,
                        'status': 'blocked',
                        'error': 'Anti-bot protection (999)',
                        'content': 'Content blocked by anti-bot protection',
                        'metadata': {},
                        'response_code': 999,
                        'attempts': attempt + 1
                    }
                
                elif response.status_code in [403, 429]:
                    # Rate limited or forbidden - wait longer
                    if attempt < max_retries:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        self.logger.warning(f"Rate limited {url}, waiting {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {
                            'url': url,
                            'status': 'blocked',
                            'error': f'Rate limited (HTTP {response.status_code})',
                            'content': '',
                            'metadata': {},
                            'response_code': response.status_code,
                            'attempts': attempt + 1
                        }
                
                elif response.status_code == 404:
                    # Not found
                    return {
                        'url': url,
                        'status': 'not_found',
                        'error': 'Page not found (404)',
                        'content': '',
                        'metadata': {},
                        'response_code': 404,
                        'attempts': attempt + 1
                    }
                
                else:
                    # Other HTTP errors - retry
                    if attempt < max_retries:
                        wait_time = delay
                        self.logger.warning(f"HTTP {response.status_code} for {url}, retrying in {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {
                            'url': url,
                            'status': 'failed',
                            'error': f'HTTP {response.status_code}',
                            'content': '',
                            'metadata': {},
                            'response_code': response.status_code,
                            'attempts': attempt + 1
                        }
            
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    self.logger.warning(f"Timeout for {url}, retrying...")
                    time.sleep(delay)
                    continue
                else:
                    return {
                        'url': url,
                        'status': 'failed',
                        'error': 'Request timeout',
                        'content': '',
                        'metadata': {},
                        'response_code': None,
                        'attempts': attempt + 1
                    }
            
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    self.logger.warning(f"Request error for {url}: {str(e)}, retrying...")
                    time.sleep(delay)
                    continue
                else:
                    return {
                        'url': url,
                        'status': 'failed',
                        'error': f'Request error: {str(e)}',
                        'content': '',
                        'metadata': {},
                        'response_code': None,
                        'attempts': attempt + 1
                    }
            
            except Exception as e:
                return {
                    'url': url,
                    'status': 'failed',
                    'error': f'Unexpected error: {str(e)}',
                    'content': '',
                    'metadata': {},
                    'response_code': None,
                    'attempts': attempt + 1
                }
        
        # If we get here, all retries failed
        return {
            'url': url,
            'status': 'failed',
            'error': 'Max retries exceeded',
            'content': '',
            'metadata': {},
            'response_code': None,
            'attempts': max_retries + 1
        }
    
    def scrape_multiple_urls(self, urls: Dict[str, str]) -> Dict[str, Dict]:
        """Scrape multiple URLs with appropriate delays"""
        results = {}
        
        for url_type, url in urls.items():
            self.logger.info(f"Processing {url_type}: {url}")
            
            # Scrape the URL
            result = self.scrape_url_with_retry(url)
            results[url_type] = result
            
            # Respectful delay between requests
            delay = self.get_request_delay(url)
            time.sleep(delay)
        
        return results

# Update the DataEnrichment class to use the enhanced scraping
class DataEnrichment:
    """Enhanced data enrichment with improved scraping pipeline"""
    
    def __init__(self):
        self.scraping_pipeline = EnhancedScrapingPipeline()
    
    def scrape_url_enhanced(self, url: str) -> Dict[str, Any]:
        """Use enhanced scraping pipeline"""
        return self.scraping_pipeline.scrape_url_with_retry(url)
    
    # Include all the API methods from the previous data_enrichment.py
    def verify_email_eva(self, email):
        """Verify email using EVA Email Verification API"""
        try:
            import requests
            url = f"https://api.eva.pingutil.com/email?email={email}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'service': 'EVA',
                    'status': 'success',
                    'deliverable': data.get('status') == 'deliverable',
                    'data': data
                }
            else:
                return {'service': 'EVA', 'status': 'failed', 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'service': 'EVA', 'status': 'error', 'error': str(e)}
    
    def get_gender(self, first_name):
        """Get gender prediction using Gender API"""
        try:
            import requests
            url = f"https://api.genderize.io/?name={first_name}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'service': 'Genderize',
                    'status': 'success',
                    'gender': data.get('gender'),
                    'probability': data.get('probability'),
                    'count': data.get('count')
                }
            else:
                return {'service': 'Genderize', 'status': 'failed', 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'service': 'Genderize', 'status': 'error', 'error': str(e)}
    
    def search_github(self, company_name):
        """Search GitHub for company repositories"""
        try:
            import requests
            from urllib.parse import quote
            
            search_query = quote(f'"{company_name}" OR "{company_name.replace("-", " ")}" in:name,description')
            url = f"https://api.github.com/search/users?q={search_query}&type=org"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                orgs = data.get('items', [])
                
                repo_url = f"https://api.github.com/search/repositories?q={search_query}"
                repo_response = requests.get(repo_url, timeout=10)
                
                repo_data = repo_response.json() if repo_response.status_code == 200 else {}
                repos = repo_data.get('items', [])
                
                return {
                    'service': 'GitHub',
                    'status': 'success',
                    'organizations': orgs[:5],
                    'repositories': repos[:10],
                    'total_orgs': len(orgs),
                    'total_repos': len(repos)
                }
            else:
                return {'service': 'GitHub', 'status': 'failed', 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'service': 'GitHub', 'status': 'error', 'error': str(e)}
    
    def google_company_search(self, company_name, location=""):
        """Search Google for company information"""
        try:
            import requests
            from urllib.parse import quote
            
            search_query = f'"{company_name}" {location} company size employees industry'
            encoded_query = quote(search_query)
            
            url = f"https://www.google.com/search?q={encoded_query}&num=10"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                text = response.text
                
                # Look for industry mentions
                industry_keywords = [
                    'marketing', 'advertising', 'digital agency', 'media', 'consulting',
                    'technology', 'software', 'services', 'solutions'
                ]
                
                industries_found = []
                for keyword in industry_keywords:
                    if keyword.lower() in text.lower():
                        industries_found.append(keyword)
                
                return {
                    'service': 'Google Search',
                    'status': 'success',
                    'industry_mentions': list(set(industries_found)),
                    'search_results_found': True
                }
            else:
                return {'service': 'Google Search', 'status': 'failed', 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'service': 'Google Search', 'status': 'error', 'error': str(e)}

if __name__ == "__main__":
    # Test the enhanced scraping pipeline
    pipeline = EnhancedScrapingPipeline()
    
    # Test URLs
    test_urls = {
        'website': 'https://www.scierkalang.com',
        'linkedin': 'https://www.linkedin.com/company/scierka-lang-media'
    }
    
    print("Testing Enhanced Scraping Pipeline...")
    results = pipeline.scrape_multiple_urls(test_urls)
    
    for url_type, result in results.items():
        print(f"\\n{url_type.upper()}:")
        print(f"Status: {result['status']}")
        print(f"Content Length: {result.get('full_content_length', 0)}")
        if result.get('metadata', {}).get('title'):
            print(f"Title: {result['metadata']['title'][:100]}...")