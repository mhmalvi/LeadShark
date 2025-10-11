#!/usr/bin/env python3
"""
🧪 AI Integration Test Suite
Quick verification that Anthropic Claude integration is working correctly
"""

import os
import sys
from typing import Dict, Any

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")


def test_imports() -> bool:
    """Test 1: Verify all required imports"""
    print_header("Test 1: Module Imports")

    tests = {
        'anthropic': False,
        'anthropic_enrichment': False,
        'ai_powered_enricher': False,
        'google_sheets_auth': False,
        'enhanced_scraping_pipeline': False,
        'data_enrichment': False
    }

    # Test anthropic package
    try:
        import anthropic
        tests['anthropic'] = True
        print_success(f"anthropic package v{anthropic.__version__}")
    except ImportError as e:
        print_error(f"anthropic package not installed: {e}")
        print_warning("Run: pip install anthropic==0.39.0")

    # Test custom modules
    try:
        from anthropic_enrichment import AnthropicEnrichment
        tests['anthropic_enrichment'] = True
        print_success("anthropic_enrichment module")
    except ImportError as e:
        print_error(f"anthropic_enrichment.py not found: {e}")

    try:
        from ai_powered_enricher import AIPoweredEnricher
        tests['ai_powered_enricher'] = True
        print_success("ai_powered_enricher module")
    except ImportError as e:
        print_error(f"ai_powered_enricher.py not found: {e}")

    try:
        from google_sheets_auth import authenticate_google_sheets
        tests['google_sheets_auth'] = True
        print_success("google_sheets_auth module")
    except ImportError as e:
        print_error(f"google_sheets_auth.py not found: {e}")

    try:
        from enhanced_scraping_pipeline import EnhancedScrapingPipeline
        tests['enhanced_scraping_pipeline'] = True
        print_success("enhanced_scraping_pipeline module")
    except ImportError as e:
        print_error(f"enhanced_scraping_pipeline.py not found: {e}")

    try:
        from data_enrichment import enrich_gender
        tests['data_enrichment'] = True
        print_success("data_enrichment module")
    except ImportError as e:
        print_error(f"data_enrichment.py not found: {e}")

    all_passed = all(tests.values())
    if all_passed:
        print_success("\nAll imports successful!")
    else:
        print_error(f"\n{sum(not v for v in tests.values())} imports failed")

    return all_passed


def test_environment() -> bool:
    """Test 2: Check environment configuration"""
    print_header("Test 2: Environment Configuration")

    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print_success("Loaded .env file")
    except:
        print_warning(".env file not found or dotenv not installed")

    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY', '')

    if not api_key:
        print_error("ANTHROPIC_API_KEY not set in .env")
        print_info("Add to .env file: ANTHROPIC_API_KEY=sk-ant-api03-...")
        return False

    if not api_key.startswith('sk-ant-api'):
        print_warning("API key format looks incorrect")
        print_info("Should start with: sk-ant-api03-...")
        return False

    # Mask key for display
    masked_key = api_key[:15] + "..." + api_key[-4:]
    print_success(f"API key found: {masked_key}")

    # Check other config
    model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
    print_info(f"Model: {model}")

    max_tokens = os.getenv('ANTHROPIC_MAX_TOKENS', '2048')
    print_info(f"Max tokens: {max_tokens}")

    temperature = os.getenv('ANTHROPIC_TEMPERATURE', '0.3')
    print_info(f"Temperature: {temperature}")

    enabled = os.getenv('AI_ENRICHMENT_ENABLED', 'true').lower() == 'true'
    if enabled:
        print_success("AI enrichment enabled")
    else:
        print_warning("AI enrichment disabled in config")

    return True


def test_api_connection() -> bool:
    """Test 3: Test Anthropic API connection"""
    print_header("Test 3: API Connection")

    try:
        from anthropic_enrichment import AnthropicEnrichment

        ai = AnthropicEnrichment()

        if not ai.is_enabled():
            print_error("AI enrichment not enabled")
            print_info("Check API key and anthropic package installation")
            return False

        print_success(f"Client initialized (model: {ai.model})")

        # Test simple analysis
        print_info("Testing content analysis...")

        test_content = """
        TechCorp is a leading SaaS company providing cloud-based project
        management software. We help teams collaborate more effectively.
        Trusted by over 10,000 companies worldwide.
        """

        result = ai.analyze_company_content(
            content=test_content,
            company_name="TechCorp",
            url="https://techcorp.com"
        )

        if result.get('ai_powered'):
            print_success("AI analysis successful!")
            print_info(f"  Category: {result.get('category', 'N/A')}")
            print_info(f"  Confidence: {result.get('confidence_score', 0):.0%}")
            return True
        else:
            print_warning("Analysis fell back to rule-based methods")
            return False

    except Exception as e:
        print_error(f"API connection failed: {e}")
        return False


def test_lead_scoring() -> bool:
    """Test 4: Test lead scoring functionality"""
    print_header("Test 4: Lead Scoring")

    try:
        from anthropic_enrichment import AnthropicEnrichment

        ai = AnthropicEnrichment()

        if not ai.is_enabled():
            print_warning("Skipping - AI not enabled")
            return False

        print_info("Testing lead scoring...")

        test_lead = {
            'name': 'John Smith',
            'email': 'john@techcorp.com',
            'company': 'TechCorp Inc',
            'title': 'VP of Sales',
            'linkedin': 'https://linkedin.com/in/johnsmith',
            'website': 'https://techcorp.com'
        }

        result = ai.generate_lead_score_reasoning(test_lead)

        if result.get('ai_powered'):
            print_success("Lead scoring successful!")
            print_info(f"  Score: {result.get('lead_score', 0)}/100")
            print_info(f"  Priority: {result.get('priority_tier', 'N/A')}")
            return True
        else:
            print_warning("Scoring fell back to rule-based methods")
            return False

    except Exception as e:
        print_error(f"Lead scoring failed: {e}")
        return False


def test_report_generation() -> bool:
    """Test 5: Test intelligence report generation"""
    print_header("Test 5: Intelligence Report Generation")

    try:
        from anthropic_enrichment import AnthropicEnrichment

        ai = AnthropicEnrichment()

        if not ai.is_enabled():
            print_warning("Skipping - AI not enabled")
            return False

        print_info("Testing report generation...")

        test_data = {
            'name': 'Jane Doe',
            'company_name': 'Acme Corp',
            'email': 'jane@acmecorp.com',
            'ai_category': 'SaaS',
            'ai_lead_score': 85
        }

        report = ai.generate_intelligence_report(test_data)

        if len(report) > 100:
            print_success("Report generated successfully!")
            print_info(f"  Report length: {len(report)} chars")
            return True
        else:
            print_warning("Report generation may have issues")
            return False

    except Exception as e:
        print_error(f"Report generation failed: {e}")
        return False


def test_fallback_behavior() -> bool:
    """Test 6: Test fallback to rule-based methods"""
    print_header("Test 6: Fallback Behavior")

    try:
        from anthropic_enrichment import AnthropicEnrichment

        # Create enricher with invalid key to test fallback
        ai = AnthropicEnrichment(api_key="invalid_key")

        print_info("Testing with invalid API key (should fallback)...")

        result = ai.analyze_company_content(
            content="Test content",
            company_name="TestCo"
        )

        if not result.get('ai_powered'):
            print_success("Fallback working correctly!")
            print_info(f"  Fallback method: {result.get('fallback_method', 'N/A')}")
            return True
        else:
            print_error("Fallback not working - should use rule-based")
            return False

    except Exception as e:
        print_error(f"Fallback test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and display summary"""
    # Set UTF-8 encoding for Windows
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("LeadShark AI Integration Test Suite")
    print("Testing Anthropic Claude integration...")
    print(f"{Colors.END}")

    results = {
        'Module Imports': test_imports(),
        'Environment Config': test_environment(),
        'API Connection': test_api_connection(),
        'Lead Scoring': test_lead_scoring(),
        'Report Generation': test_report_generation(),
        'Fallback Behavior': test_fallback_behavior()
    }

    # Summary
    print_header("Test Summary")

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}")
        print("SUCCESS: All tests passed! AI integration is working correctly.")
        print(f"{Colors.END}")
        print("\nReady to process leads with AI-powered enrichment!")
        print(f"\nNext steps:")
        print(f"  1. Run: python ai_powered_enricher.py --sheet-id 'YOUR_ID' --test")
        print(f"  2. Check your Google Sheet for enriched data")
        print(f"  3. Review logs: ai_enrichment.log")
        return True
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}")
        print(f"WARNING: {total - passed} test(s) failed - review errors above")
        print(f"{Colors.END}")
        print(f"\nTroubleshooting:")
        print(f"  1. Install: pip install anthropic==0.39.0")
        print(f"  2. Set API key in .env: ANTHROPIC_API_KEY=sk-ant-api03-...")
        print(f"  3. Check: cat .env | grep ANTHROPIC_API_KEY")
        print(f"  4. Review: doc/AI_INTEGRATION_GUIDE.md")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)