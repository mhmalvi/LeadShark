import requests
from bs4 import BeautifulSoup
import time
import json

urls = [
    "https://www.linkedin.com/in/scierka",
    "https://www.scierkalang.com", 
    "https://www.linkedin.com/company/scierka-lang-media",
    "https://twitter.com/ScierkaLang",
    "https://www.facebook.com/ScierkaMedia"
]

# Enhanced headers to mimic real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

# Create a session to maintain cookies
session = requests.Session()
session.headers.update(headers)

scraped_data = {}

def extract_content(soup, url):
    """Enhanced content extraction based on platform"""
    
    # Extract title
    title = soup.find('title')
    title_text = title.get_text().strip() if title else "No title found"
    
    # Extract meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    description = meta_desc.get('content', '').strip() if meta_desc else "No description found"
    
    # Platform-specific extraction
    content_text = ""
    
    if "linkedin.com" in url:
        # LinkedIn specific selectors
        profile_content = soup.find_all(['section', 'div'], class_=lambda x: x and any(term in x.lower() for term in ['profile', 'experience', 'about', 'summary']))
        if profile_content:
            content_text = '\n'.join([elem.get_text(strip=True) for elem in profile_content])
        else:
            content_text = soup.get_text()
    
    elif "twitter.com" in url or "x.com" in url:
        # Twitter specific selectors
        tweets = soup.find_all(['article', 'div'], attrs={'data-testid': lambda x: x and 'tweet' in str(x).lower()})
        if tweets:
            content_text = '\n'.join([tweet.get_text(strip=True) for tweet in tweets])
        else:
            content_text = soup.get_text()
    
    elif "facebook.com" in url:
        # Facebook specific selectors
        posts = soup.find_all(['div'], class_=lambda x: x and any(term in x.lower() for term in ['post', 'story', 'userContent']))
        if posts:
            content_text = '\n'.join([post.get_text(strip=True) for post in posts])
        else:
            content_text = soup.get_text()
    
    else:
        # General extraction
        content_text = soup.get_text()
    
    # Clean up the text
    lines = (line.strip() for line in content_text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    clean_text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return {
        'title': title_text,
        'description': description,
        'content': clean_text[:5000] + "..." if len(clean_text) > 5000 else clean_text,
        'content_length': len(clean_text)
    }

for url in urls:
    try:
        print(f"Scraping: {url}")
        
        # Add longer timeout and retry logic
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract content using enhanced method
        extracted = extract_content(soup, url)
        
        scraped_data[url] = {
            **extracted,
            'status': 'success',
            'response_code': response.status_code,
            'content_type': response.headers.get('content-type', 'unknown')
        }
        
        print(f"Successfully scraped: {extracted['title']} (Content length: {extracted['content_length']} chars)")
        
    except requests.exceptions.RequestException as e:
        print(f"Error scraping {url}: {str(e)}")
        scraped_data[url] = {
            'error': str(e),
            'status': 'failed'
        }
    except Exception as e:
        print(f"Unexpected error scraping {url}: {str(e)}")
        scraped_data[url] = {
            'error': f"Unexpected error: {str(e)}",
            'status': 'failed'
        }
    
    # Add delay between requests
    time.sleep(2)

# Save results to JSON file
with open('scraped_content_authenticated.json', 'w', encoding='utf-8') as f:
    json.dump(scraped_data, f, indent=2, ensure_ascii=False)

print(f"\nScraping completed. Results saved to 'scraped_content_authenticated.json'")

# Print summary
print("\n" + "="*80)
print("SCRAPING SUMMARY")
print("="*80)

for url, data in scraped_data.items():
    if data['status'] == 'success':
        print(f"\nURL: {url}")
        print(f"Title: {data['title']}")
        print(f"Description: {data['description'][:100]}..." if len(data['description']) > 100 else f"Description: {data['description']}")
        print(f"Content Length: {data['content_length']} characters")
        print("-" * 80)
    else:
        print(f"\nURL: {url}")
        print(f"STATUS: FAILED - {data['error']}")
        print("-" * 80)