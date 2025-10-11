#!/usr/bin/env python3
"""
LeadShark v5.0 Integration Test
Tests all new features: email finding, cold outreach, enhanced lead scoring
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

def test_email_pattern_generation():
    """Test email pattern generator"""
    print("=" * 60)
    print("TEST 1: Email Pattern Generation")
    print("=" * 60)

    from data_enrichment import DataEnrichment
    enricher = DataEnrichment()

    variants = enricher.generate_email_variants("John", "Doe", "example.com")

    print(f"✅ Generated {len(variants)} email variants:")
    for i, email in enumerate(variants, 1):
        print(f"  {i}. {email}")

    assert len(variants) >= 9, "Should generate at least 9 variants"
    assert "john@example.com" in variants
    assert "john.doe@example.com" in variants
    print("✅ Email pattern generation: PASS\n")


def test_email_extraction():
    """Test email extraction from content"""
    print("=" * 60)
    print("TEST 2: Email Extraction from Content")
    print("=" * 60)

    from data_enrichment import DataEnrichment
    enricher = DataEnrichment()

    content = """
    Contact us at john.doe@example.com for more info.
    Sales: sales@example.com
    Support: support@example.com (ignored)
    CEO: jane.smith@example.com
    """

    emails = enricher.extract_emails_from_content(content)

    print(f"✅ Extracted {len(emails)} emails:")
    for email in emails:
        print(f"  - {email}")

    assert "john.doe@example.com" in emails
    assert "jane.smith@example.com" in emails
    assert "support@example.com" not in emails  # Should be filtered
    print("✅ Email extraction: PASS\n")


def test_lead_scoring_improvements():
    """Test enhanced lead scoring"""
    print("=" * 60)
    print("TEST 3: Enhanced Lead Scoring")
    print("=" * 60)

    from lead_scoring_engine import LeadScoringEngine

    scorer = LeadScoringEngine()

    # Test data: Small business owner
    test_data = {
        'scraped_content': {
            'linkedin': {
                'extracted': {
                    'title': 'Owner & Founder',
                    'key_fields': {
                        'headline': 'Owner at Example Corp',
                        'connections': 500
                    }
                }
            }
        },
        'api_results': {
            'google_search': {
                'company_info': 'Small business with 10 employees',
                'industry_mentions': ['marketing', 'digital agency']
            },
            'email_verification': {
                'deliverable': False  # But has email variants
            }
        },
        'email_enrichment': {
            'email_variants': ['john@example.com', 'john.doe@example.com']  # For partial credit
        }
    }

    score, tag, breakdown = scorer.calculate_score(test_data)

    print(f"Lead Score: {score}/100")
    print(f"Lead Tag: {tag}")
    print(f"\nBreakdown:")
    for factor, value in breakdown.items():
        print(f"  {factor}: {value}%")

    # Should get boost for small business owner
    assert score >= 50, f"Owner of small business should score >= 50, got {score}"
    assert tag in ["Warm 🟡", "Hot 🔥"], f"Should be Warm or Hot, got {tag}"
    print(f"✅ Lead scoring improvements: PASS (Score: {score}, Tag: {tag})\n")


def test_cold_outreach_engine():
    """Test cold outreach personalization"""
    print("=" * 60)
    print("TEST 4: Cold Outreach Engine")
    print("=" * 60)

    from cold_outreach_engine import ColdOutreachEngine

    engine = ColdOutreachEngine()

    test_content = """
    Ahead Creative is a full-service marketing agency based in Melbourne, Australia.
    Founded in 2015, we've helped over 200 clients grow their brands.
    We recently expanded into TV spot production and are hiring two new creative directors.
    Our work has been featured in AdWeek and we were named Top Agency of 2023.
    """

    result = engine.generate_complete_email_components(
        person_name="Lorenzo Smith",
        company_name="Ahead Creative",
        industry="Marketing Agency",
        scraped_content=test_content,
        product_category="workflow automation"
    )

    print("✅ Generated cold outreach components:")
    print(f"\n📧 Subject Lines:")
    print(f"  1. {result['subject_line_1']}")
    print(f"  2. {result['subject_line_2']}")
    print(f"  3. {result['subject_line_3']}")

    print(f"\n💬 Opening Line:")
    print(f"  {result['opening_line']}")

    print(f"\n🎯 Value Proposition:")
    print(f"  {result['value_prop_match']}")

    print(f"\n🚀 Call to Action:")
    print(f"  {result['suggested_cta']}")

    print(f"\n📊 Personalization Data:")
    print(f"  Recent Activity: {result['recent_activity'][:100]}...")
    print(f"  Social Proof: {result['social_proof']}")
    print(f"  Trigger Event: {result['trigger_event'][:100]}..." if result['trigger_event'] else "  Trigger Event: None")

    # Validate all components generated
    assert result['subject_line_1'], "Should generate subject line 1"
    assert result['subject_line_2'], "Should generate subject line 2"
    assert result['subject_line_3'], "Should generate subject line 3"
    assert result['opening_line'], "Should generate opening line"
    assert result['value_prop_match'], "Should generate value prop"
    assert result['suggested_cta'], "Should generate CTA"

    print("\n✅ Cold outreach engine: PASS\n")


def test_recent_activity_extraction():
    """Test recent activity signal detection"""
    print("=" * 60)
    print("TEST 5: Recent Activity Extraction")
    print("=" * 60)

    from cold_outreach_engine import ColdOutreachEngine

    engine = ColdOutreachEngine()

    content = "We recently launched our new AI-powered platform and are expanding to three new markets."

    activity = engine._extract_recent_activity(content)

    print(f"✅ Extracted recent activity:")
    print(f"  {activity}")

    assert activity, "Should extract recent activity"
    assert "recently" in activity.lower() or "launched" in activity.lower()
    print("✅ Recent activity extraction: PASS\n")


def test_trigger_event_detection():
    """Test trigger event detection"""
    print("=" * 60)
    print("TEST 6: Trigger Event Detection")
    print("=" * 60)

    from cold_outreach_engine import ColdOutreachEngine

    engine = ColdOutreachEngine()

    content = """
    Company X raised $5M in Series A funding last month.
    They are hiring 3 senior engineers.
    The company just launched a new product line.
    """

    events = engine._extract_trigger_events(content)

    print(f"✅ Detected {len(events)} trigger events:")
    for event in events:
        print(f"  - {event['type']}: {event['description'][:80]}...")

    assert len(events) >= 2, "Should detect multiple trigger events"
    event_types = [e['type'] for e in events]
    assert 'funding' in event_types or 'hiring' in event_types
    print("✅ Trigger event detection: PASS\n")


def test_social_proof_extraction():
    """Test social proof extraction"""
    print("=" * 60)
    print("TEST 7: Social Proof Extraction")
    print("=" * 60)

    from cold_outreach_engine import ColdOutreachEngine

    engine = ColdOutreachEngine()

    content = """
    Founded in 2015, we've grown to serve over 500 clients worldwide.
    Our community has 10,000 followers on social media.
    """

    social_proof = engine._extract_social_proof(content)

    print(f"✅ Extracted social proof:")
    for key, value in social_proof.items():
        print(f"  {key}: {value}")

    assert 'years_in_business' in social_proof or 'client_count' in social_proof
    print("✅ Social proof extraction: PASS\n")


def test_integration_all_features():
    """Test all features together"""
    print("=" * 60)
    print("TEST 8: Full Integration Test")
    print("=" * 60)

    print("✅ Testing complete enrichment pipeline...")

    # Simulate row data
    test_row = {
        'name': 'John Doe',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'company': 'Example Corp',
        'organization_name': 'Example Corp',
        'website': 'https://example.com',
        'title': 'Founder & CEO',
        'industry': 'Marketing',
        'linkedin_url': 'https://linkedin.com/in/johndoe'
    }

    print(f"Test Lead: {test_row['name']} @ {test_row['company']}")
    print(f"Title: {test_row['title']}")

    # Test 1: Email pattern generation
    from data_enrichment import DataEnrichment
    enricher = DataEnrichment()
    email_variants = enricher.generate_email_variants("John", "Doe", "example.com")
    print(f"✅ Generated {len(email_variants)} email variants")

    # Test 2: Cold outreach components
    from cold_outreach_engine import ColdOutreachEngine
    outreach = ColdOutreachEngine()
    components = outreach.generate_complete_email_components(
        person_name="John Doe",
        company_name="Example Corp",
        industry="Marketing",
        scraped_content="Founded in 2020, Example Corp serves 100+ clients"
    )
    print(f"✅ Generated cold outreach components")

    # Test 3: Lead scoring
    from lead_scoring_engine import LeadScoringEngine
    scorer = LeadScoringEngine()

    scoring_data = {
        'scraped_content': {
            'linkedin': {
                'extracted': {
                    'title': 'Founder & CEO',
                    'key_fields': {'headline': 'Founder at Example Corp'}
                }
            }
        },
        'api_results': {}
    }

    score, tag, breakdown = scorer.calculate_score(scoring_data)
    print(f"✅ Lead score calculated: {score}/100 - {tag}")

    print("\n✅ Full integration test: PASS\n")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🦈 LEADSHARK v5.0 INTEGRATION TEST SUITE")
    print("=" * 60)
    print()

    tests = [
        test_email_pattern_generation,
        test_email_extraction,
        test_lead_scoring_improvements,
        test_cold_outreach_engine,
        test_recent_activity_extraction,
        test_trigger_event_detection,
        test_social_proof_extraction,
        test_integration_all_features
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - v5.0 READY FOR PRODUCTION!")
    else:
        print(f"\n⚠️  {failed} test(s) failed - review errors above")

    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
