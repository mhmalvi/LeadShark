import requests
from bs4 import BeautifulSoup
import time
import json
import re

urls = [
    "https://www.linkedin.com/in/scierka",
    "https://www.scierkalang.com", 
    "https://www.linkedin.com/company/scierka-lang-media",
    "https://twitter.com/ScierkaLang",
    "https://www.facebook.com/ScierkaMedia"
]

# More realistic browser headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

session = requests.Session()
session.headers.update(headers)

scraped_data = {}

def clean_and_extract_text(soup, url):
    """Clean and extract readable text content"""
    
    # Remove script and style elements
    for script in soup(["script", "style", "noscript"]):
        script.decompose()
    
    # Get text and clean it up
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_metadata(soup):
    """Extract useful metadata from the page"""
    metadata = {}
    
    # Title
    title_tag = soup.find('title')
    metadata['title'] = title_tag.get_text().strip() if title_tag else "No title found"
    
    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    metadata['description'] = meta_desc.get('content', '').strip() if meta_desc else "No description found"
    
    # Open Graph data
    og_title = soup.find('meta', attrs={'property': 'og:title'})
    if og_title:
        metadata['og_title'] = og_title.get('content', '')
    
    og_type = soup.find('meta', attrs={'property': 'og:type'})
    if og_type:
        metadata['og_type'] = og_type.get('content', '')
    
    # Twitter card data
    twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
    if twitter_title:
        metadata['twitter_title'] = twitter_title.get('content', '')
    
    return metadata

for url in urls:
    try:
        print(f"Scraping: {url}")
        
        # Special handling for different platforms
        current_headers = headers.copy()
        if 'linkedin.com' in url:
            current_headers['Accept'] = 'text/html,application/xhtml+xml'
        elif 'facebook.com' in url:
            current_headers['Accept-Encoding'] = 'identity'  # Disable compression for Facebook
        
        response = session.get(url, headers=current_headers, timeout=30)
        
        # Check if we got blocked (LinkedIn returns 999)
        if response.status_code == 999:
            print(f"  - Blocked by anti-bot protection (status 999)")
            scraped_data[url] = {
                'title': 'Blocked by anti-bot protection',
                'description': 'LinkedIn/platform blocked the scraping attempt',
                'content': 'Content not accessible due to anti-bot protection',
                'status': 'blocked',
                'response_code': 999
            }
            continue
        
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        print(f"  - Content type: {content_type}")
        
        # Try to detect encoding issues
        if 'charset' not in content_type.lower():
            response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract metadata
        metadata = extract_metadata(soup)
        
        # Extract clean text content
        clean_text = clean_and_extract_text(soup, url)
        
        scraped_data[url] = {
            **metadata,
            'content': clean_text[:5000] + "..." if len(clean_text) > 5000 else clean_text,
            'full_content_length': len(clean_text),
            'status': 'success',
            'response_code': response.status_code,
            'content_type': content_type
        }
        
        print(f"  + Successfully scraped: {metadata['title']} ({len(clean_text)} chars)")
        
    except requests.exceptions.RequestException as e:
        print(f"  - Network error: {str(e)}")
        scraped_data[url] = {
            'error': str(e),
            'status': 'failed'
        }
    except Exception as e:
        print(f"  - Unexpected error: {str(e)}")
        scraped_data[url] = {
            'error': f"Unexpected error: {str(e)}",
            'status': 'failed'
        }
    
    # Respectful delay
    time.sleep(2)

# Save results
with open('scraped_content_final.json', 'w', encoding='utf-8') as f:
    json.dump(scraped_data, f, indent=2, ensure_ascii=False)

print(f"\n{'='*80}")
print("FINAL SCRAPING RESULTS")
print(f"{'='*80}")

successful_scrapes = 0
for url, data in scraped_data.items():
    print(f"\n{url}")
    if data['status'] == 'success':
        successful_scrapes += 1
        print(f"  + Title: {data['title']}")
        print(f"  + Content: {data['full_content_length']} characters")
        if data.get('og_title'):
            print(f"  + OG Title: {data['og_title']}")
    elif data['status'] == 'blocked':
        print(f"  ! Blocked: {data['title']}")
    else:
        print(f"  - Failed: {data.get('error', 'Unknown error')}")

print(f"\nSummary: {successful_scrapes}/5 URLs successfully scraped")
print("Results saved to 'scraped_content_final.json'")