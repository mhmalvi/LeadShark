#!/usr/bin/env python3
"""
Test if scrape_url method exists
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from enhanced_scraping_pipeline import EnhancedScrapingPipeline

def test_scraper():
    """Test if scrape_url method exists"""

    print("Testing EnhancedScrapingPipeline methods...")

    scraper = EnhancedScrapingPipeline()

    # Check available methods
    methods = [method for method in dir(scraper) if not method.startswith('_')]
    print(f"Available methods: {len(methods)}")

    scrape_methods = [method for method in methods if 'scrape' in method.lower()]
    print(f"Scrape methods found: {scrape_methods}")

    # Test if scrape_url exists
    if hasattr(scraper, 'scrape_url'):
        print("[OK] scrape_url method EXISTS")

        # Try to call it with a test URL
        try:
            result = scraper.scrape_url("https://httpbin.org/html")
            print(f"[OK] scrape_url method WORKS: {result.get('status', 'unknown status')}")
            return True
        except Exception as e:
            print(f"[X] scrape_url method exists but FAILED: {e}")
            return False
    else:
        print("[X] scrape_url method MISSING")
        return False

if __name__ == "__main__":
    success = test_scraper()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)