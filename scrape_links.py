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

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

scraped_data = {}

for url in urls:
    try:
        print(f"Scraping: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '').strip() if meta_desc else "No description found"
        
        # Extract all text content (cleaned)
        text_content = soup.get_text()
        # Clean up the text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        scraped_data[url] = {
            'title': title_text,
            'description': description,
            'content': clean_text[:2000] + "..." if len(clean_text) > 2000 else clean_text,  # Limit content length
            'status': 'success'
        }
        
        print(f"Successfully scraped: {title_text}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error scraping {url}: {str(e)}")
        scraped_data[url] = {
            'error': str(e),
            'status': 'failed'
        }
    
    # Add delay between requests to be respectful
    time.sleep(1)

# Save results to JSON file
with open('scraped_content.json', 'w', encoding='utf-8') as f:
    json.dump(scraped_data, f, indent=2, ensure_ascii=False)

print(f"\nScraping completed. Results saved to 'scraped_content.json'")

# Print summary
for url, data in scraped_data.items():
    if data['status'] == 'success':
        print(f"\n{url}")
        print(f"Title: {data['title']}")
        print(f"Description: {data['description']}")
        print("-" * 80)
    else:
        print(f"\n{url} - FAILED: {data['error']}")