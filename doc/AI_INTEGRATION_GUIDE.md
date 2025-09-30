# 🤖 LeadShark AI Integration Guide
## Anthropic Claude API Integration for Enhanced Lead Intelligence

📅 **Last Updated:** 2025-09-30
🔧 **Version:** v3.0-AI
🤖 **Model:** Claude 3.5 Sonnet

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Setup Instructions](#setup-instructions)
4. [Usage](#usage)
5. [API Key Management](#api-key-management)
6. [Configuration](#configuration)
7. [Cost Considerations](#cost-considerations)
8. [Troubleshooting](#troubleshooting)
9. [Examples](#examples)

---

## 🎯 Overview

LeadShark now integrates **Anthropic's Claude API** to provide AI-powered lead intelligence analysis. This enhancement combines traditional web scraping and API enrichment with advanced natural language understanding for deeper, more actionable insights.

### What's New?

- **🤖 AI Content Analysis:** Intelligent company categorization and value proposition extraction
- **🎯 Smart Lead Scoring:** AI-powered qualification with detailed reasoning
- **📊 Intelligence Reports:** Natural language summaries with actionable recommendations
- **🏷️ Category Classification:** Accurate industry and business model detection
- **🛡️ Automatic Fallback:** Graceful degradation to rule-based methods when AI unavailable

---

## ✨ Features

### 1. AI-Powered Company Analysis

Claude analyzes scraped website content to extract:

- **Primary Category & Industry** (SaaS, E-commerce, Agency, etc.)
- **Business Model** (B2B, B2C, B2B2C, Marketplace, etc.)
- **Value Proposition** (Concise 1-sentence summary)
- **Target Market** (Customer profile and segments)
- **Company Size Indicators** (Employee count, revenue signals)
- **Technology Stack** (Visible technologies and platforms)
- **Commercial Readiness** (Pricing visibility, CTA presence)
- **Key Differentiators** (Unique selling points)

**Confidence Scoring:** Each analysis includes confidence metrics (0-100%)

### 2. Intelligent Lead Scoring

AI evaluates leads across multiple dimensions:

- **ICP Fit Score** (0-100): Match to ideal customer profile
- **Commercial Readiness Score** (0-100): Evidence of buying intent
- **Engagement Potential Score** (0-100): Likelihood of response
- **Priority Tier** (High/Medium/Low): Actionable classification
- **Strengths & Weaknesses:** Detailed analysis
- **Recommended Actions:** Specific next steps for engagement

### 3. Intelligence Report Generation

Professional markdown reports with:

- **Executive Summary** (2-3 sentences)
- **Company Overview** (Business, industry, size)
- **Key Insights** (3-5 actionable bullet points)
- **Engagement Recommendations** (Specific outreach strategies)
- **Risk Factors** (Concerns or red flags)

### 4. Smart Fallback System

- **No API Key?** Falls back to rule-based enrichment
- **Rate Limit Hit?** Continues with traditional methods
- **API Error?** Graceful degradation without stopping pipeline
- **Zero Downtime:** Processing never fails due to AI unavailability

---

## 🚀 Setup Instructions

### Step 1: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install new dependencies
pip install anthropic==0.39.0

# Or install all requirements
pip install -r requirements.txt
```

### Step 2: Get Anthropic API Key

1. Go to **https://console.anthropic.com**
2. Sign up or log in to your account
3. Navigate to **Settings > API Keys**
4. Click **"Create Key"**
5. Copy your API key (starts with `sk-ant-api03-...`)

**⚠️ IMPORTANT:** Keep this key secret! Never share or commit to git.

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

Add your API key to `.env`:

```bash
# Anthropic Claude API Configuration
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=2048
ANTHROPIC_TEMPERATURE=0.3

# Enable AI features
AI_ENRICHMENT_ENABLED=true
```

### Step 4: Verify Installation

```bash
# Test API connection
python anthropic_enrichment.py

# Expected output:
# 🧪 Testing Anthropic API Connection...
# ✅ Anthropic client initialized
# 📝 Testing content analysis...
# ✅ AI analysis successful!
```

---

## 💻 Usage

### Basic Usage

```bash
# Test with first 3 rows
python ai_powered_enricher.py \
  --sheet-id "your_sheet_id_here" \
  --test

# Process specific number of rows
python ai_powered_enricher.py \
  --sheet-id "your_sheet_id_here" \
  --max-rows 10

# Process all rows
python ai_powered_enricher.py \
  --sheet-id "your_sheet_id_here"

# Start from specific row
python ai_powered_enricher.py \
  --sheet-id "your_sheet_id_here" \
  --start-row 50 \
  --max-rows 100
```

### Programmatic Usage

```python
from ai_powered_enricher import AIPoweredEnricher

# Initialize enricher
enricher = AIPoweredEnricher(
    sheet_id="your_sheet_id",
    tab_name="Sheet1"
)

# Process sheet
stats = enricher.process_sheet(
    max_rows=10,  # Optional: limit rows
    start_row=1   # Optional: starting row
)

# View results
print(f"Processed: {stats['rows_processed']}")
print(f"AI-enhanced: {stats['ai_enhanced']}")
```

### API Module Usage

```python
from anthropic_enrichment import AnthropicEnrichment

# Initialize AI enricher
ai = AnthropicEnrichment()

# Check if enabled
if ai.is_enabled():
    # Analyze company content
    analysis = ai.analyze_company_content(
        content=scraped_website_text,
        company_name="TechCorp",
        url="https://techcorp.com"
    )

    print(f"Category: {analysis.get('category')}")
    print(f"Value Prop: {analysis.get('value_proposition')}")
    print(f"Confidence: {analysis.get('confidence_score'):.0%}")

    # Generate lead score
    lead_data = {
        'name': 'John Smith',
        'company': 'TechCorp',
        'email': 'john@techcorp.com',
        'website': 'https://techcorp.com'
    }

    scoring = ai.generate_lead_score_reasoning(lead_data)
    print(f"Lead Score: {scoring.get('lead_score')}/100")
    print(f"Priority: {scoring.get('priority_tier')}")

    # Generate intelligence report
    report = ai.generate_intelligence_report({
        **lead_data,
        **analysis
    })

    print(report)
```

---

## 🔐 API Key Management

### Security Best Practices

✅ **DO:**
- Store API key in `.env` file
- Add `.env` to `.gitignore`
- Use environment variables only
- Rotate keys periodically
- Monitor usage in Anthropic console

❌ **DON'T:**
- Commit API keys to git
- Share keys in chat/email
- Hardcode keys in code
- Use keys in screenshots
- Store in plaintext files

### Key Rotation

When rotating keys:

1. Generate new key in Anthropic console
2. Update `.env` file with new key
3. Delete old key from console
4. Restart application
5. Verify new key works

### Environment Variables

The system reads these environment variables:

```bash
ANTHROPIC_API_KEY       # Required: Your API key
ANTHROPIC_MODEL         # Optional: Model to use (default: claude-3-5-sonnet-20241022)
ANTHROPIC_MAX_TOKENS    # Optional: Max tokens per request (default: 2048)
ANTHROPIC_TEMPERATURE   # Optional: Response randomness (default: 0.3)
AI_ENRICHMENT_ENABLED   # Optional: Enable/disable AI (default: true)
```

---

## ⚙️ Configuration

### Model Selection

Available models (as of 2025-09-30):

- **claude-3-5-sonnet-20241022** (Recommended)
  - Best balance of speed and intelligence
  - Ideal for lead enrichment
  - Cost: $3/MTok input, $15/MTok output

- **claude-3-opus-20240229**
  - Highest intelligence
  - Slower and more expensive
  - Use for complex analysis only

- **claude-3-haiku-20240307**
  - Fastest and cheapest
  - Lower quality analysis
  - Good for simple classification

### Token Limits

- **Default:** 2048 tokens (~1500 words)
- **Minimum:** 512 tokens
- **Maximum:** 4096 tokens
- **Recommendation:** 2048 for most use cases

Higher limits = more detailed analysis but higher cost.

### Temperature Settings

- **0.0-0.3:** Deterministic, consistent (recommended for lead scoring)
- **0.4-0.7:** Balanced creativity
- **0.8-1.0:** More creative, less predictable

**Default 0.3** provides consistent, reliable analysis.

### Feature Flags

Enable/disable specific features:

```bash
# In .env file
AI_ENRICHMENT_ENABLED=true          # Master switch for all AI features
ENABLE_AI_CONTENT_ANALYSIS=true     # Company content analysis
ENABLE_AI_LEAD_SCORING=true         # Lead scoring
ENABLE_AI_REPORT_GENERATION=true    # Intelligence reports
ENABLE_AI_CLASSIFICATION=true       # Category classification
```

---

## 💰 Cost Considerations

### Pricing (Claude 3.5 Sonnet)

- **Input:** $3 per million tokens (~750,000 words)
- **Output:** $15 per million tokens (~750,000 words)

### Typical Usage Per Lead

- **Content Analysis:** ~1,500 input tokens + 500 output tokens = $0.012
- **Lead Scoring:** ~800 input tokens + 300 output tokens = $0.007
- **Report Generation:** ~1,000 input tokens + 600 output tokens = $0.012

**Total per lead:** ~$0.03 - $0.05 with all features enabled

### Cost Optimization

**Reduce costs by:**

1. **Disable unused features**
   ```bash
   ENABLE_AI_REPORT_GENERATION=false  # Save ~40% per lead
   ```

2. **Reduce token limits**
   ```bash
   ANTHROPIC_MAX_TOKENS=1024  # Save ~50% on output tokens
   ```

3. **Use cheaper model for simple tasks**
   ```bash
   ANTHROPIC_MODEL=claude-3-haiku-20240307  # 90% cheaper
   ```

4. **Batch processing** (already implemented)

5. **Cache results** (to avoid re-analyzing same content)

### Monthly Estimates

| Leads/Month | Cost (Full Features) | Cost (Optimized) |
|-------------|---------------------|------------------|
| 100         | $3-5                | $1-2             |
| 500         | $15-25              | $5-10            |
| 1,000       | $30-50              | $10-20           |
| 5,000       | $150-250            | $50-100          |

### Free Tier

- **$5 free credit** for new accounts
- Enough for ~100-150 leads with full features
- No expiration on credits

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "anthropic package not installed"

```bash
pip install anthropic==0.39.0
```

#### 2. "ANTHROPIC_API_KEY not set"

Check `.env` file exists and has correct key:

```bash
cat .env | grep ANTHROPIC_API_KEY
```

#### 3. "API connection failed"

- Verify API key is correct
- Check internet connection
- Verify Anthropic service status: https://status.anthropic.com

#### 4. "Rate limit exceeded"

- Wait 60 seconds and retry
- Reduce processing speed
- Upgrade Anthropic plan for higher limits

#### 5. "AI enrichment disabled"

Check these conditions:
```python
# Should print True
from anthropic_enrichment import AnthropicEnrichment
ai = AnthropicEnrichment()
print(ai.is_enabled())
```

If False, check:
- anthropic package installed?
- ANTHROPIC_API_KEY set in .env?
- AI_ENRICHMENT_ENABLED=true?

### Debug Mode

Enable detailed logging:

```bash
# In .env
LOG_LEVEL=DEBUG

# Or set environment variable
export LOG_LEVEL=DEBUG
python ai_powered_enricher.py --sheet-id "your_id" --test
```

### Test API Connection

```bash
# Quick test
python -c "from anthropic_enrichment import test_anthropic_connection; test_anthropic_connection()"
```

### View Statistics

After processing, check:
- `ai_enrichment.log` - Detailed logs
- Console output - Summary statistics
- Anthropic console - Usage dashboard

---

## 📚 Examples

### Example 1: Test AI Connection

```python
#!/usr/bin/env python3
from anthropic_enrichment import test_anthropic_connection

if __name__ == "__main__":
    success = test_anthropic_connection()
    if success:
        print("✅ AI enrichment ready!")
    else:
        print("❌ AI enrichment unavailable - check configuration")
```

### Example 2: Analyze Company Content

```python
from anthropic_enrichment import AnthropicEnrichment

ai = AnthropicEnrichment()

content = """
Acme Corp is a leading provider of cloud-based project management software.
We help teams of all sizes collaborate more effectively with our intuitive
platform. Trusted by over 10,000 companies worldwide. Pricing starts at $10/user/month.
"""

analysis = ai.analyze_company_content(
    content=content,
    company_name="Acme Corp",
    url="https://acmecorp.com"
)

print(f"Category: {analysis['category']}")
print(f"Business Model: {analysis['business_model']}")
print(f"Value Prop: {analysis['value_proposition']}")
print(f"Confidence: {analysis['confidence_score']:.0%}")
```

### Example 3: Score a Lead

```python
from anthropic_enrichment import AnthropicEnrichment

ai = AnthropicEnrichment()

lead = {
    'name': 'Sarah Johnson',
    'email': 'sarah@techstartup.com',
    'company': 'TechStartup Inc',
    'title': 'VP of Sales',
    'linkedin': 'https://linkedin.com/in/sarahjohnson',
    'website': 'https://techstartup.com'
}

scoring = ai.generate_lead_score_reasoning(lead)

print(f"Lead Score: {scoring['lead_score']}/100")
print(f"Priority: {scoring['priority_tier']}")
print(f"\nStrengths:")
for strength in scoring['strengths']:
    print(f"  + {strength}")

print(f"\nRecommended Actions:")
for action in scoring['recommended_actions']:
    print(f"  → {action}")
```

### Example 4: Process Sheet with Custom Settings

```python
from ai_powered_enricher import AIPoweredEnricher
import os

# Set custom configuration
os.environ['ANTHROPIC_MAX_TOKENS'] = '1024'
os.environ['ANTHROPIC_TEMPERATURE'] = '0.2'

enricher = AIPoweredEnricher(
    sheet_id="1234567890abcdef",
    tab_name="Leads"
)

# Process with limits
stats = enricher.process_sheet(
    max_rows=50,
    start_row=1
)

print(f"""
Enrichment Complete!
===================
Rows Processed: {stats['rows_processed']}
AI-Enhanced: {stats['ai_enhanced']}
Rule-Based: {stats['rule_based_only']}
Errors: {stats['errors']}
""")
```

---

## 🆘 Support

### Getting Help

1. **Check logs:** `ai_enrichment.log`
2. **Review documentation:** This guide
3. **Test connection:** `python anthropic_enrichment.py`
4. **Check Anthropic status:** https://status.anthropic.com
5. **File issue:** https://github.com/yourusername/leadshark/issues

### Additional Resources

- **Anthropic Documentation:** https://docs.anthropic.com
- **Claude API Reference:** https://docs.anthropic.com/en/api
- **LeadShark Documentation:** `doc/` directory
- **Example Code:** `anthropic_enrichment.py`, `ai_powered_enricher.py`

---

## 🎉 Conclusion

With Anthropic Claude integration, LeadShark now provides:

✅ **Deeper Insights:** AI-powered analysis beyond rule-based methods
✅ **Better Scoring:** Intelligent lead qualification with reasoning
✅ **Actionable Intelligence:** Natural language reports with recommendations
✅ **Reliability:** Automatic fallback ensures uninterrupted processing
✅ **Cost-Effective:** Optimized for ~$0.03-0.05 per lead

**🦈🤖 LeadShark + Claude: Predatory Intelligence Meets AI Power**

---

*Last updated: 2025-09-30*
*Version: v3.0-AI*
*Questions? Check the troubleshooting section or file an issue.*