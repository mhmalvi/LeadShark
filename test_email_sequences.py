#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Email Sequence Generation Integration

Tests the complete v5.1 email sequence generation within the enrichment pipeline
"""

import os
import sys

# Configure stdout encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from ai_email_sequence_generator import AIEmailSequenceGenerator

def test_email_sequence_generator():
    """Test standalone email sequence generator"""

    print("="*80)
    print("🧪 TESTING EMAIL SEQUENCE GENERATOR (Standalone)")
    print("="*80)

    # Check if API key is set
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        print("❌ OPENAI_API_KEY not set!")
        print("   Set it with: set OPENAI_API_KEY=sk-your-key-here")
        return False

    print(f"✅ API key detected: {api_key[:20]}...")

    # Test data (enriched lead)
    lead_data = {
        'name': 'Lorenzo Smith',
        'company': 'Ahead Creative',
        'title': 'Creative Director',
        'industry': 'Marketing Agency',
        'linkedin_headline': 'Creative Director helping brands tell better stories',
        'linkedin_company': 'Ahead Creative',
        'linkedin_experience': 'Leading creative strategy for 50+ brands',
        'recent_activity': 'Recently expanded into TV spot production',
        'pain_points': 'Manual client reporting | Time-consuming approval workflows | Limited analytics',
        'trigger_events': 'hiring: Hiring two new creative directors',
        'social_proof': '8 years in business | 200+ clients',
        'lead_score': 85,
        'ai_category': 'Full-service marketing agency',
        'ai_value_proposition': 'Comprehensive creative and strategic services'
    }

    sender_info = {
        'name': 'Alex Johnson',
        'company': 'WorkflowPro',
        'title': 'Head of Partnerships',
        'value_proposition': 'We help creative agencies automate client reporting and save 10+ hours/week'
    }

    product_info = {
        'name': 'WorkflowPro',
        'category': 'workflow automation',
        'key_benefit': 'automated client reporting and approval workflows',
        'target_industries': ['Marketing', 'Advertising', 'Creative Agency']
    }

    # Generate sequence
    print("\n📨 Generating 5-email sequence...")
    generator = AIEmailSequenceGenerator(api_key=api_key)

    try:
        sequence = generator.generate_complete_sequence(
            lead_data=lead_data,
            sender_info=sender_info,
            product_info=product_info
        )

        print("✅ Email sequence generated successfully!\n")

        # Display results
        for email_num in range(1, 6):
            email_key = f'email_{email_num}'
            email = sequence.get(email_key, {})

            print("="*80)
            print(f"EMAIL #{email_num}: {email.get('name', 'Unknown')}")
            print(f"Timing: {email.get('timing', 'N/A')}")
            print(f"Goal: {email.get('goal', 'N/A')}")
            print("="*80)
            print(f"\nSUBJECT: {email.get('subject', 'N/A')}")
            print(f"\nBODY:\n{email.get('body', 'N/A')}")
            if email.get('ps'):
                print(f"\n{email.get('ps', '')}")
            print()

        # Test sheet formatting
        print("\n" + "="*80)
        print("📊 GOOGLE SHEETS FORMAT")
        print("="*80)
        formatted = generator.format_sequence_for_sheets(sequence)

        for col_name, value in formatted.items():
            display_value = value[:100] + "..." if len(str(value)) > 100 else value
            print(f"{col_name}: {display_value}")

        return True

    except Exception as e:
        print(f"❌ Email sequence generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hybrid_enricher_integration():
    """Test email sequence integration in hybrid enricher"""

    print("\n" + "="*80)
    print("🧪 TESTING HYBRID ENRICHER INTEGRATION")
    print("="*80)

    try:
        from hybrid_ai_enhanced_enricher import HybridAIEnhancedEnricher

        print("✅ Successfully imported HybridAIEnhancedEnricher")

        # Check if email sequence generator is initialized
        enricher = HybridAIEnhancedEnricher(
            sheet_id='test',
            dry_run=True
        )

        if hasattr(enricher, 'email_sequence_generator'):
            print("✅ Email sequence generator initialized")

            # Check if API client exists
            if enricher.email_sequence_generator.client:
                print("✅ OpenAI GPT client detected")
            else:
                print("⚠️  OpenAI GPT client not initialized (API key missing)")
        else:
            print("❌ Email sequence generator NOT initialized")
            return False

        # Check if headers include email sequence columns
        from hybrid_ai_enhanced_enricher import HYBRID_ENRICHMENT_HEADERS

        email_seq_headers = [h for h in HYBRID_ENRICHMENT_HEADERS if '📨' in h]

        print(f"✅ Found {len(email_seq_headers)} email sequence columns:")
        for header in email_seq_headers[:5]:  # Show first 5
            print(f"   - {header}")
        if len(email_seq_headers) > 5:
            print(f"   ... and {len(email_seq_headers) - 5} more")

        # Check total column count
        print(f"\n📊 Total enrichment columns: {len(HYBRID_ENRICHMENT_HEADERS)}")

        if len(HYBRID_ENRICHMENT_HEADERS) == 85:
            print("✅ Column count correct (85 columns)")
        else:
            print(f"❌ Column count incorrect (expected 85, got {len(HYBRID_ENRICHMENT_HEADERS)})")
            return False

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""

    print("\n" + "="*80)
    print("🦈 LEADSHARK v5.1 - EMAIL SEQUENCE INTEGRATION TEST")
    print("="*80 + "\n")

    # Test 1: Standalone generator
    test1_passed = test_email_sequence_generator()

    # Test 2: Hybrid enricher integration
    test2_passed = test_hybrid_enricher_integration()

    # Summary
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    print(f"✅ Standalone Generator: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Hybrid Enricher Integration: {'PASSED' if test2_passed else 'FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! Email sequences ready to use.")
        print("\n📖 Next steps:")
        print("   1. Set OPENAI_API_KEY environment variable")
        print("   2. Run: python hybrid_ai_enhanced_enricher.py")
        print("   3. Check sheet for 15 new email sequence columns")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")

    print("="*80 + "\n")


if __name__ == "__main__":
    main()
