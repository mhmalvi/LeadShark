#!/usr/bin/env python3
"""
🤖 AI API Integration for LeadShark (Anthropic Claude & OpenAI GPT)
Provides AI-powered lead intelligence and enrichment capabilities
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Try importing Anthropic
try:
    from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not installed. Run: pip install anthropic")

# Try importing OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai package not installed. Run: pip install openai")

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai').lower()  # Default to OpenAI
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # Cost-effective default
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '2048'))
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.3'))

# Setup logging
logger = logging.getLogger(__name__)


class AnthropicEnrichment:
    """
    🤖 AI-powered lead enrichment using Claude or GPT

    Supports both Anthropic Claude and OpenAI GPT models.
    Provides intelligent analysis, classification, and insights generation
    for lead data with fallback to rule-based methods when AI unavailable.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize AI enrichment client

        Args:
            api_key: API key (uses env var if not provided)
            model: Model to use (uses env var default if not provided)
            provider: 'anthropic' or 'openai' (default: openai from env)
        """
        self.provider = (provider or AI_PROVIDER).lower()
        self.client = None
        self.enabled = False

        # Set API key and model based on provider
        if self.provider == 'anthropic':
            self.api_key = api_key or ANTHROPIC_API_KEY
            self.model = model or ANTHROPIC_MODEL
        else:  # Default to OpenAI
            self.provider = 'openai'
            self.api_key = api_key or OPENAI_API_KEY
            self.model = model or OPENAI_MODEL

        # Statistics
        self.stats = {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'fallbacks': 0,
            'total_tokens': 0,
            'provider': self.provider
        }

        # Initialize client based on provider
        if self.provider == 'anthropic':
            if ANTHROPIC_AVAILABLE and self.api_key:
                try:
                    self.client = Anthropic(api_key=self.api_key)
                    self.enabled = True
                    logger.info(f"Anthropic Claude API enabled (model: {self.model})")
                except Exception as e:
                    logger.warning(f"Failed to initialize Anthropic client: {e}")
                    self.enabled = False
            else:
                if not ANTHROPIC_AVAILABLE:
                    logger.warning("Anthropic package not installed - AI features disabled")
                elif not self.api_key:
                    logger.warning("ANTHROPIC_API_KEY not set - AI features disabled")
                self.enabled = False

        elif self.provider == 'openai':
            if OPENAI_AVAILABLE and self.api_key:
                try:
                    self.client = OpenAI(api_key=self.api_key)
                    self.enabled = True
                    logger.info(f"OpenAI GPT API enabled (model: {self.model})")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI client: {e}")
                    self.enabled = False
            else:
                if not OPENAI_AVAILABLE:
                    logger.warning("OpenAI package not installed - AI features disabled")
                elif not self.api_key:
                    logger.warning("OPENAI_API_KEY not set - AI features disabled")
                self.enabled = False

    def is_enabled(self) -> bool:
        """Check if AI enrichment is available"""
        return self.enabled

    def analyze_company_content(self, content: str, company_name: str = "",
                                url: str = "") -> Dict[str, Any]:
        """
        🔍 Analyze company website content using Claude

        Args:
            content: Scraped website content
            company_name: Company name for context
            url: Company URL

        Returns:
            Dictionary with AI-generated insights
        """
        if not self.enabled:
            return self._fallback_content_analysis(content, company_name)

        # Truncate content if too long (keep first 4000 chars)
        content_preview = content[:4000] if len(content) > 4000 else content

        prompt = f"""Analyze this company website content and extract key business intelligence.

Company: {company_name or 'Unknown'}
URL: {url or 'Not provided'}

Website Content:
{content_preview}

Please provide a structured analysis with:
1. **Company Category/Industry** (1-3 specific categories)
2. **Business Model** (B2B, B2C, B2B2C, etc.)
3. **Value Proposition** (concise 1-sentence summary)
4. **Target Market** (who are their customers)
5. **Company Size Indicators** (any signals about company size)
6. **Technology Stack** (any visible technologies)
7. **Commercial Readiness** (pricing visibility, CTA presence)
8. **Key Differentiators** (unique selling points)

Respond with a JSON object matching this structure:
{{
  "category": "Primary category",
  "subcategories": ["sub1", "sub2"],
  "business_model": "B2B/B2C/etc",
  "value_proposition": "One sentence value prop",
  "target_market": "Description of target customers",
  "size_signals": ["signal1", "signal2"],
  "tech_stack": ["tech1", "tech2"],
  "commercial_readiness": "Assessment of sales readiness",
  "differentiators": ["diff1", "diff2"],
  "confidence_score": 0.85,
  "analysis_summary": "3-sentence executive summary"
}}"""

        try:
            self.stats['requests'] += 1

            # Call appropriate API
            if self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    messages=[{"role": "user", "content": prompt}]
                )
                content_text = response.content[0].text
                self.stats['total_tokens'] += response.usage.input_tokens + response.usage.output_tokens

            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                content_text = response.choices[0].message.content
                self.stats['total_tokens'] += response.usage.total_tokens

            self.stats['successes'] += 1

            # Parse JSON response
            try:
                analysis = json.loads(content_text)
                analysis['ai_powered'] = True
                analysis['model'] = self.model
                analysis['provider'] = self.provider
                return analysis
            except json.JSONDecodeError:
                # If not valid JSON, extract what we can
                logger.warning(f"{self.provider.title()} response not valid JSON, extracting text")
                return {
                    'analysis_summary': content_text[:500],
                    'ai_powered': True,
                    'model': self.model,
                    'provider': self.provider,
                    'raw_response': content_text
                }

        except Exception as e:
            error_type = type(e).__name__
            if 'RateLimit' in error_type:
                logger.warning(f"Rate limit hit: {e}")
            elif 'API' in error_type or 'Auth' in error_type:
                logger.error(f"{self.provider.title()} API error: {e}")
            else:
                logger.error(f"Unexpected error in AI analysis: {e}")

            self.stats['failures'] += 1
            return self._fallback_content_analysis(content, company_name)

    def generate_lead_score_reasoning(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 Generate intelligent lead score with AI reasoning

        Args:
            lead_data: Dictionary with lead information

        Returns:
            Dictionary with score and detailed reasoning
        """
        if not self.enabled:
            return self._fallback_lead_scoring(lead_data)

        # Prepare lead context
        context = json.dumps(lead_data, indent=2)

        prompt = f"""Analyze this lead and provide a qualification score with reasoning.

Lead Data:
{context}

Please evaluate based on:
1. **ICP Fit** - Does this match an ideal customer profile?
2. **Commercial Signals** - Evidence of buying intent
3. **Engagement Potential** - Likelihood of response
4. **Data Quality** - Completeness and accuracy of information
5. **Company Health** - Business viability indicators

Provide a JSON response:
{{
  "lead_score": 75,
  "score_explanation": "Detailed 2-3 sentence explanation",
  "icp_fit_score": 80,
  "commercial_readiness_score": 70,
  "engagement_potential_score": 75,
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"],
  "recommended_actions": ["action1", "action2"],
  "priority_tier": "High/Medium/Low",
  "confidence": 0.85
}}"""

        try:
            self.stats['requests'] += 1

            # Call appropriate API
            if self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    temperature=TEMPERATURE,
                    messages=[{"role": "user", "content": prompt}]
                )
                content_text = response.content[0].text
                self.stats['total_tokens'] += response.usage.input_tokens + response.usage.output_tokens

            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=1024,
                    temperature=TEMPERATURE,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                content_text = response.choices[0].message.content
                self.stats['total_tokens'] += response.usage.total_tokens

            self.stats['successes'] += 1

            # Parse JSON
            scoring = json.loads(content_text)
            scoring['ai_powered'] = True
            scoring['provider'] = self.provider
            return scoring

        except Exception as e:
            logger.error(f"AI lead scoring failed: {e}")
            self.stats['failures'] += 1
            return self._fallback_lead_scoring(lead_data)

    def generate_intelligence_report(self, enrichment_data: Dict[str, Any]) -> str:
        """
        📊 Generate natural language intelligence report

        Args:
            enrichment_data: Complete enrichment data for a lead

        Returns:
            Formatted markdown intelligence report
        """
        if not self.enabled:
            return self._fallback_report_generation(enrichment_data)

        context = json.dumps(enrichment_data, indent=2)[:3000]

        prompt = f"""Generate a concise, actionable intelligence report for this lead.

Enrichment Data:
{context}

Create a professional markdown report with:
1. **Executive Summary** (2-3 sentences)
2. **Company Overview** (business, industry, size)
3. **Key Insights** (3-5 bullet points)
4. **Engagement Recommendations** (2-3 specific actions)
5. **Risk Factors** (if any concerns)

Keep it concise, actionable, and focused on sales/business development value.
Use emojis sparingly and only for section headers."""

        try:
            self.stats['requests'] += 1

            # Call appropriate API
            if self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    temperature=0.4,
                    messages=[{"role": "user", "content": prompt}]
                )
                report = response.content[0].text
                self.stats['total_tokens'] += response.usage.input_tokens + response.usage.output_tokens

            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=1500,
                    temperature=0.4,
                    messages=[{"role": "user", "content": prompt}]
                )
                report = response.choices[0].message.content
                self.stats['total_tokens'] += response.usage.total_tokens

            self.stats['successes'] += 1

            # Add AI attribution
            report += f"\n\n---\n*AI-Generated Report ({self.provider.title()} {self.model})*"

            return report

        except Exception as e:
            logger.error(f"AI report generation failed: {e}")
            self.stats['failures'] += 1
            return self._fallback_report_generation(enrichment_data)

    def classify_company_category(self, company_name: str, description: str = "",
                                  website_content: str = "") -> Dict[str, Any]:
        """
        🏷️ Intelligently classify company category/industry

        Args:
            company_name: Company name
            description: Company description
            website_content: Website text (optional)

        Returns:
            Dictionary with category, subcategories, confidence
        """
        if not self.enabled:
            return self._fallback_classification(company_name, description)

        context = f"""
Company: {company_name}
Description: {description[:500] if description else 'Not provided'}
Website: {website_content[:500] if website_content else 'Not provided'}
"""

        prompt = f"""Classify this company into relevant business categories.

{context}

Provide classification as JSON:
{{
  "primary_category": "Main industry/category",
  "subcategories": ["sub1", "sub2", "sub3"],
  "business_type": "SaaS/E-commerce/Agency/Consulting/etc",
  "target_vertical": "Vertical they serve",
  "confidence": 0.9
}}"""

        try:
            self.stats['requests'] += 1

            # Call appropriate API
            if self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=512,
                    temperature=TEMPERATURE,
                    messages=[{"role": "user", "content": prompt}]
                )
                content_text = response.content[0].text
                self.stats['total_tokens'] += response.usage.input_tokens + response.usage.output_tokens

            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=512,
                    temperature=TEMPERATURE,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                content_text = response.choices[0].message.content
                self.stats['total_tokens'] += response.usage.total_tokens

            result = json.loads(content_text)
            self.stats['successes'] += 1

            result['ai_powered'] = True
            result['provider'] = self.provider
            return result

        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            self.stats['failures'] += 1
            return self._fallback_classification(company_name, description)

    # Fallback methods (rule-based) when AI unavailable

    def _fallback_content_analysis(self, content: str, company_name: str) -> Dict[str, Any]:
        """Rule-based content analysis fallback"""
        self.stats['fallbacks'] += 1

        # Simple keyword-based analysis
        content_lower = content.lower()

        categories = []
        if any(kw in content_lower for kw in ['saas', 'software as a service', 'cloud']):
            categories.append('SaaS')
        if any(kw in content_lower for kw in ['ecommerce', 'e-commerce', 'online store']):
            categories.append('E-commerce')
        if any(kw in content_lower for kw in ['agency', 'marketing', 'digital']):
            categories.append('Agency')

        return {
            'category': categories[0] if categories else 'Unknown',
            'subcategories': categories[1:] if len(categories) > 1 else [],
            'analysis_summary': f"Basic analysis of {company_name}",
            'ai_powered': False,
            'fallback_method': 'keyword_matching',
            'confidence_score': 0.5
        }

    def _fallback_lead_scoring(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based lead scoring fallback"""
        self.stats['fallbacks'] += 1

        # Simple scoring based on data completeness
        score = 50  # Base score

        if lead_data.get('email'):
            score += 10
        if lead_data.get('company_name'):
            score += 10
        if lead_data.get('linkedin_url'):
            score += 10
        if lead_data.get('website_url'):
            score += 10
        if lead_data.get('title'):
            score += 5

        return {
            'lead_score': min(score, 100),
            'score_explanation': 'Basic scoring based on data completeness',
            'ai_powered': False,
            'fallback_method': 'rule_based',
            'confidence': 0.6
        }

    def _fallback_report_generation(self, enrichment_data: Dict[str, Any]) -> str:
        """Simple report generation fallback"""
        self.stats['fallbacks'] += 1

        company = enrichment_data.get('company_name', 'Unknown Company')

        report = f"""# Intelligence Report: {company}

## Summary
Basic enrichment data collected for {company}.

## Available Data
- Email: {enrichment_data.get('email', 'Not available')}
- LinkedIn: {enrichment_data.get('linkedin_url', 'Not available')}
- Website: {enrichment_data.get('website_url', 'Not available')}

---
*📊 Basic Report (AI unavailable)*
"""
        return report

    def _fallback_classification(self, company_name: str, description: str) -> Dict[str, Any]:
        """Simple classification fallback"""
        self.stats['fallbacks'] += 1

        return {
            'primary_category': 'Unknown',
            'subcategories': [],
            'business_type': 'Unknown',
            'ai_powered': False,
            'fallback_method': 'basic',
            'confidence': 0.3
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            **self.stats,
            'enabled': self.enabled,
            'model': self.model,
            'success_rate': f"{(self.stats['successes'] / max(self.stats['requests'], 1)) * 100:.1f}%",
            'fallback_rate': f"{(self.stats['fallbacks'] / max(self.stats['requests'] + self.stats['fallbacks'], 1)) * 100:.1f}%"
        }

    def print_stats(self):
        """Print usage statistics"""
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("🤖 ANTHROPIC AI ENRICHMENT STATISTICS")
        print("=" * 60)
        print(f"Status: {'✅ Enabled' if stats['enabled'] else '❌ Disabled'}")
        print(f"Model: {stats['model']}")
        print(f"Requests: {stats['requests']}")
        print(f"Successes: {stats['successes']}")
        print(f"Failures: {stats['failures']}")
        print(f"Fallbacks: {stats['fallbacks']}")
        print(f"Total Tokens: {stats['total_tokens']:,}")
        print(f"Success Rate: {stats['success_rate']}")
        print(f"Fallback Rate: {stats['fallback_rate']}")
        print("=" * 60)


# Convenience function for quick testing
def test_anthropic_connection():
    """Test Anthropic API connection and basic functionality"""
    print("\n🧪 Testing Anthropic API Connection...")

    enricher = AnthropicEnrichment()

    if not enricher.is_enabled():
        print("❌ Anthropic API not available")
        print("   Check:")
        print("   1. anthropic package installed: pip install anthropic")
        print("   2. ANTHROPIC_API_KEY set in .env file")
        return False

    print("✅ Anthropic client initialized")

    # Test with simple analysis
    test_content = """
    TechCorp is a leading SaaS company providing cloud-based project management solutions.
    We help teams collaborate more effectively with our intuitive platform.
    Trusted by over 10,000 companies worldwide.
    """

    print("\n📝 Testing content analysis...")
    result = enricher.analyze_company_content(test_content, "TechCorp", "https://techcorp.com")

    if result.get('ai_powered'):
        print("✅ AI analysis successful!")
        print(f"   Category: {result.get('category', 'N/A')}")
        print(f"   Confidence: {result.get('confidence_score', 'N/A')}")
    else:
        print("⚠️  Fell back to rule-based analysis")

    # Print stats
    enricher.print_stats()

    return enricher.is_enabled()


if __name__ == "__main__":
    # Run connection test
    test_anthropic_connection()