#!/usr/bin/env python3
"""
Fresh test - completely reload modules
"""

import sys
import os
import importlib

# Clear import cache
modules_to_reload = []
for module_name in list(sys.modules.keys()):
    if any(name in module_name for name in ['enhanced_scraping', 'compact_enricher']):
        modules_to_reload.append(module_name)

for module_name in modules_to_reload:
    if module_name in sys.modules:
        del sys.modules[module_name]

sys.path.append(os.path.dirname(__file__))

# Fresh import
from enhanced_scraping_pipeline import EnhancedScrapingPipeline

def test_method():
    print("Testing fresh import...")

    scraper = EnhancedScrapingPipeline()

    # Check methods
    methods = [method for method in dir(scraper) if 'scrape' in method and not method.startswith('_')]
    print(f"Scrape methods: {methods}")

    # Test scrape_url
    if hasattr(scraper, 'scrape_url'):
        print("SUCCESS: scrape_url method found!")

        # Try simple test
        try:
            result = scraper.scrape_url("https://example.com")
            print(f"Method call result: {result.get('status', 'no status')}")
            return True
        except Exception as e:
            print(f"Method call failed: {e}")
            return False
    else:
        print("FAILED: scrape_url method still missing")
        return False

if __name__ == "__main__":
    success = test_method()
    print(f"Final result: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)