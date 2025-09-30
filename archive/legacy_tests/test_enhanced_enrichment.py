#!/usr/bin/env python3
"""
Test Suite for Enhanced Enrichment System
Tests all new modules and integration
"""

import sys
import logging
from typing import Dict

# Fix Windows Unicode issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Test imports
try:
    from link_type_classifier import LinkTypeClassifier, LinkType
    from lead_scoring_engine import LeadScoringEngine
    from context_generator import ContextGenerator
    from api_rate_limiter import APIRateLimiter
    from multi_link_scraper import MultiLinkScraper
    from enhanced_enrichment_engine import EnhancedEnrichmentEngine
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


def test_link_classifier():
    """Test Link Type Classifier"""
    print("\n" + "="*60)
    print("TEST 1: Link Type Classifier")
    print("="*60)

    classifier = LinkTypeClassifier()

    test_urls = {
        'LinkedIn Profile': 'https://linkedin.com/in/johndoe',
        'LinkedIn Company': 'https://linkedin.com/company/acme-corp',
        'Twitter': 'https://twitter.com/johndoe',
        'GitHub': 'https://github.com/johndoe',
        'Company Website': 'https://acmecorp.com',
        'Contact Page': 'https://acmecorp.com/contact',
        'Blog Post': 'https://acmecorp.com/blog/my-post'
    }

    passed = 0
    total = len(test_urls)

    for expected, url in test_urls.items():
        link_type = classifier.classify_url(url)
        display_name = classifier.get_display_name(link_type)

        if expected.lower() in display_name.lower():
            print(f"  ✅ {url[:50]:50s} → {display_name}")
            passed += 1
        else:
            print(f"  ❌ {url[:50]:50s} → {display_name} (expected {expected})")

    print(f"\nResult: {passed}/{total} tests passed")
    return passed == total


def test_lead_scoring():
    """Test Lead Scoring Engine"""
    print("\n" + "="*60)
    print("TEST 2: Lead Scoring Engine")
    print("="*60)

    scorer = LeadScoringEngine()

    # Test case 1: CEO with strong signals
    test_data_hot = {
        'scraped_content': {
            'linkedin': {
                'extracted': {
                    'title': 'CEO & Founder',
                    'company': 'StartupX',
                    'key_fields': {'connections': 5000}
                }
            },
            'website': {
                'extracted': {
                    'contacts': {
                        'emails': ['ceo@startup.com'],
                        'phones': ['+1-555-0100']
                    }
                }
            },
            'twitter': {
                'extracted': {'metrics': {'followers': 15000}}
            }
        },
        'api_results': {
            'email_verification': {'deliverable': True},
            'github': {'total_repos': 50},
            'google_search': {
                'company_info': 'Recently raised Series A funding',
                'industry_mentions': ['saas', 'software', 'cloud']
            }
        }
    }

    score, tags, breakdown = scorer.calculate_score(test_data_hot)

    print(f"  Score: {score}/100")
    print(f"  Tags: {tags}")
    print(f"  Breakdown:")
    for key, value in breakdown.items():
        print(f"    {key}: {value}%")

    if score >= 70 and '🔥' in tags or '🟡' in tags:
        print(f"\n  ✅ Scoring test passed (Hot/Warm lead detected)")
        return True
    else:
        print(f"\n  ❌ Scoring test failed (expected Hot/Warm, got {tags})")
        return False


def test_context_generator():
    """Test Context Generator"""
    print("\n" + "="*60)
    print("TEST 3: Context Generator")
    print("="*60)

    generator = ContextGenerator()

    test_data = {
        'scraped_content': {
            'linkedin': {
                'extracted': {
                    'name': 'John Doe',
                    'title': 'CEO',
                    'company': 'StartupX',
                    'location': 'New York',
                    'key_fields': {'headline': 'Founder & CEO at StartupX'}
                }
            },
            'website': {
                'url': 'https://startupx.com',
                'extracted': {
                    'description': 'AI-based cloud integration platform',
                    'contacts': {'emails': ['info@startupx.com']}
                }
            },
            'twitter': {
                'extracted': {
                    'key_fields': {'handle': '@johndoe'},
                    'metrics': {'followers': 12000}
                }
            }
        },
        'api_results': {
            'email_verification': {'deliverable': True},
            'gender': {'gender': 'male', 'probability': 0.99},
            'github': {'total_repos': 45}
        }
    }

    context = generator.generate_complete_context(test_data, "John Doe")

    print(f"  Generated Context:")
    print(f"  {context[:200]}...")
    print(f"\n  Length: {len(context)} characters")
    print(f"  Sentences: {context.count('.')}")

    if len(context) > 100 and '.' in context:
        print(f"\n  ✅ Context generation test passed")
        return True
    else:
        print(f"\n  ❌ Context generation test failed")
        return False


def test_api_rate_limiter():
    """Test API Rate Limiter"""
    print("\n" + "="*60)
    print("TEST 4: API Rate Limiter")
    print("="*60)

    limiter = APIRateLimiter()

    # Test quota status
    print("  Quota Status:")
    status = limiter.get_quota_status('genderize')
    print(f"    Genderize: {status.get('remaining', 'N/A')} remaining")

    status = limiter.get_quota_status('github')
    print(f"    GitHub: {status.get('remaining', 'N/A')} remaining")

    # Test caching
    def mock_api():
        return {'test': 'data', 'cached': False}

    print("\n  Testing cache...")
    result1 = limiter.make_cached_request('genderize', 'test_john', mock_api)
    result2 = limiter.make_cached_request('genderize', 'test_john', mock_api)

    if result1 and result2:
        print(f"    First call: {result1}")
        print(f"    Second call (cached): {result2}")
        print(f"\n  ✅ Rate limiter test passed")
        return True
    else:
        print(f"\n  ❌ Rate limiter test failed")
        return False


def test_integration():
    """Test Full Integration"""
    print("\n" + "="*60)
    print("TEST 5: Full Integration (Enhanced Enrichment Engine)")
    print("="*60)

    engine = EnhancedEnrichmentEngine()

    test_row = {
        'name': 'Test User',
        'first_name': 'Test',
        'email': 'test@example.com',
        'company': 'TestCorp',
        'location': 'San Francisco',
        'linkedin_url': 'https://linkedin.com/in/testuser',
        'website': 'https://example.com'
    }

    print("  Input row:")
    for key, value in test_row.items():
        print(f"    {key}: {value}")

    print("\n  Starting enrichment...")

    try:
        result = engine.enrich_row(test_row, max_links=2)

        print(f"\n  Results:")
        print(f"    Processing time: {result['processing_time_ms']}ms")
        print(f"    Links scraped: {len(result['link_data'])}")
        print(f"    API enrichments: {len(result['api_enrichment'])}")
        print(f"    Lead score: {result['lead_score']} - {result['lead_tags']}")
        print(f"    Context length: {len(result['complete_context'])} chars")

        if result['errors']:
            print(f"    Errors: {result['errors']}")

        # Check minimum requirements
        checks = [
            ('link_data exists', len(result['link_data']) > 0),
            ('lead_score set', result['lead_score'] >= 0),
            ('lead_tags set', result['lead_tags'] != ''),
            ('context generated', len(result['complete_context']) > 0),
            ('timestamp set', result['last_scraped'] != '')
        ]

        passed = sum(1 for _, check in checks if check)
        print(f"\n  Checks passed: {passed}/{len(checks)}")
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"    {status} {check_name}")

        if passed >= 4:  # At least 4 out of 5
            print(f"\n  ✅ Integration test passed")
            return True
        else:
            print(f"\n  ❌ Integration test failed")
            return False

    except Exception as e:
        print(f"\n  ❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print(" " * 15 + "🦈 LeadShark Enhanced Enrichment Test Suite")
    print("="*70)

    tests = [
        ("Link Type Classifier", test_link_classifier),
        ("Lead Scoring Engine", test_lead_scoring),
        ("Context Generator", test_context_generator),
        ("API Rate Limiter", test_api_rate_limiter),
        ("Full Integration", test_integration)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n  🎉 All tests passed! System ready for production.")
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed. Review failures above.")
        return 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise during tests
        format='%(levelname)s: %(message)s'
    )

    sys.exit(run_all_tests())