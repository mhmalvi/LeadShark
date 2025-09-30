# 🦈 LeadShark Enhanced Enrichment - Quick Start Guide

## Overview

LeadShark v3.0 Enhanced Enrichment provides comprehensive lead intelligence through:
- **Multi-link scraping** (5 links per row with platform-specific extraction)
- **API enrichment** (Gender, Email, GitHub, Company, LinkedIn verification)
- **Lead scoring** (0-100 with weighted factors)
- **Context generation** (Professional paragraph synthesis)
- **Rate limiting & caching** (Cost optimization and quota management)

---

## Installation

### 1. Ensure Dependencies

```bash
pip install requests beautifulsoup4 google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. Verify Files

Ensure these new files exist in your `leadshark/` directory:
- `link_type_classifier.py`
- `lead_scoring_engine.py`
- `context_generator.py`
- `api_rate_limiter.py`
- `multi_link_scraper.py`
- `enhanced_enrichment_engine.py`

---

## Quick Test

### Run the Test Suite

```bash
cd leadshark
python test_enhanced_enrichment.py
```

**Expected Output:**
```
🦈 LeadShark Enhanced Enrichment Test Suite
============================================================
TEST 1: Link Type Classifier
...
✅ PASS: Link Type Classifier
✅ PASS: Lead Scoring Engine
✅ PASS: Context Generator
✅ PASS: API Rate Limiter
✅ PASS: Full Integration

Total: 5/5 tests passed
🎉 All tests passed! System ready for production.
```

---

## Basic Usage

### Example 1: Enrich a Single Row

```python
from enhanced_enrichment_engine import EnhancedEnrichmentEngine

# Initialize
engine = EnhancedEnrichmentEngine()

# Prepare row data
row_data = {
    'name': 'John Doe',
    'first_name': 'John',
    'email': 'john@example.com',
    'company': 'ExampleCorp',
    'location': 'New York',
    'linkedin_url': 'https://linkedin.com/in/johndoe',
    'website': 'https://example.com',
    'twitter_url': 'https://twitter.com/johndoe'
}

# Enrich
result = engine.enrich_row(row_data, max_links=5)

# Access results
print(f"Lead Score: {result['lead_score']} - {result['lead_tags']}")
print(f"Processing Time: {result['processing_time_ms']}ms")
print(f"\nComplete Context:\n{result['complete_context']}")

# Link data
for link_idx, link_data in result['link_data'].items():
    print(f"\nLink {link_idx}: {link_data['link_display']}")
    print(link_data['summary'])

# API enrichment
for api_name, api_data in result['api_enrichment'].items():
    print(f"\n{api_name}: {api_data['source']}")
```

---

### Example 2: Check API Quotas

```python
from enhanced_enrichment_engine import EnhancedEnrichmentEngine

engine = EnhancedEnrichmentEngine()

# Get quota status
quotas = engine.get_api_quota_status()

for api_name, status in quotas.items():
    print(f"{api_name}:")
    print(f"  Quota: {status.get('quota', 'unlimited')}")
    print(f"  Remaining: {status.get('remaining', 'unlimited')}")
    print(f"  Period: {status.get('period', 'N/A')}")
```

---

### Example 3: Classify Links

```python
from link_type_classifier import LinkTypeClassifier

classifier = LinkTypeClassifier()

urls = [
    'https://linkedin.com/in/johndoe',
    'https://example.com',
    'https://twitter.com/johndoe'
]

for url in urls:
    link_type = classifier.classify_url(url)
    display_name = classifier.get_display_name(link_type)
    template = classifier.get_extraction_template(link_type)

    print(f"{url}")
    print(f"  Type: {display_name}")
    print(f"  Priority Fields: {template['priority_fields'][:3]}")
```

---

### Example 4: Calculate Lead Score

```python
from lead_scoring_engine import LeadScoringEngine

scorer = LeadScoringEngine()

# Prepare scoring data (from enrichment results)
scoring_data = {
    'scraped_content': {
        'linkedin': {
            'extracted': {
                'title': 'CEO & Founder',
                'key_fields': {'connections': 5000}
            }
        }
    },
    'api_results': {
        'email_verification': {'deliverable': True},
        'github': {'total_repos': 45}
    }
}

score, tags, breakdown = scorer.calculate_score(scoring_data)

print(f"Score: {score}/100 - {tags}")
print("\nBreakdown:")
for factor, value in breakdown.items():
    print(f"  {factor}: {value}%")
```

---

## Integration with Google Sheets

### Column Structure

**For each row, add these columns:**

#### Link Columns (repeat for Links 1-5):
- `Link 1`, `Link 1 — Short Summary`, `Link 1 — JSON`
- `Link 2`, `Link 2 — Short Summary`, `Link 2 — JSON`
- ... (up to Link 5)

#### Summary Columns:
- `Complete Context`
- `Lead Score`
- `Lead Tags`
- `Last Scraped`

#### API Enrichment Columns:
- `Gender`, `Gender Confidence`, `Gender API Source`
- `Email Status`, `Email Deliverability`, `Email API Source`
- `GitHub Profile`, `GitHub Repos Count`, `GitHub Activity`, `GitHub API Source`
- `Company Info`, `Company Industry`, `Google Search API Source`
- `LinkedIn Verified`, `LinkedIn Status`, `LinkedIn API Source`

### Writing Results to Sheet

```python
def write_enrichment_to_sheet(sheet_service, sheet_id, row_index, result):
    """Write enrichment results to Google Sheet"""

    # Prepare updates
    updates = []

    # Link data (columns vary based on your sheet)
    for link_idx, link_data in result['link_data'].items():
        col_offset = (link_idx - 1) * 3
        updates.extend([
            {
                'range': f'A{row_index}',  # Adjust column
                'values': [[link_data['url']]]
            },
            {
                'range': f'B{row_index}',  # Summary column
                'values': [[link_data['summary']]]
            },
            {
                'range': f'C{row_index}',  # JSON column
                'values': [[link_data['json']]]
            }
        ])

    # Summary columns
    updates.extend([
        {'range': f'Z{row_index}', 'values': [[result['complete_context']]]},
        {'range': f'AA{row_index}', 'values': [[result['lead_score']]]},
        {'range': f'AB{row_index}', 'values': [[result['lead_tags']]]},
        {'range': f'AC{row_index}', 'values': [[result['last_scraped']]]}
    ])

    # API enrichment columns
    if 'gender' in result['api_enrichment']:
        gender_data = result['api_enrichment']['gender']['data']
        updates.extend([
            {'range': f'AD{row_index}', 'values': [[gender_data.get('gender', '')]]},
            {'range': f'AE{row_index}', 'values': [[gender_data.get('probability', 0) * 100]]},
            {'range': f'AF{row_index}', 'values': [[result['api_enrichment']['gender']['source']]]}
        ])

    # ... (add more API enrichment columns)

    # Batch update
    body = {
        'valueInputOption': 'RAW',
        'data': updates
    }

    sheet_service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body=body
    ).execute()
```

---

## API Rate Limits & Costs

### Free Tier Limits

| API | Free Tier | Cost After | Notes |
|-----|-----------|------------|-------|
| **Genderize.io** | 500/month | $0.01/request | Cache for 30 days |
| **EVA Email** | Unlimited | Free | No key needed |
| **GitHub** | 60/hour (unauth) | Free with token (5000/hour) | Use authenticated |
| **Google Search** | 100/day | $5/1000 | Cache for 7 days |
| **LinkedIn Scrape** | No limit | Free | 3s delay |

### Cost Optimization Tips

1. **Use caching** - Responses cached automatically
2. **Deduplicate names** - Same first names share cache
3. **Batch processing** - Process in chunks
4. **GitHub auth** - Use personal access token for 5000/hour
5. **Monitor quotas** - Check `engine.get_api_quota_status()`

---

## Lead Scoring Details

### Scoring Factors

| Factor | Weight | What It Measures |
|--------|--------|------------------|
| **Role / Decision Power** | 30% | CEO, Founder, C-level detection |
| **Company Fit** | 25% | Industry match, funding status |
| **Engagement / Visibility** | 15% | Social media followers, connections |
| **Contactability** | 15% | Email/phone availability |
| **Tech / Product Fit** | 10% | Technical background, GitHub presence |
| **Recency / Signal** | 5% | Recent activity, hiring signals |

### Classification Thresholds

- **🔥 Hot** (80-100): Immediate priority outreach
- **🟡 Warm** (60-79): Nurture campaign, follow-up
- **🔵 Cold** (30-59): Monitor, drip campaign
- **⚫ Discard** (0-29): Unqualified, skip

---

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Ensure all files are in the same directory
ls leadshark/*.py

# Check Python path
python -c "import sys; print(sys.path)"
```

**2. Rate Limit Errors**
```python
# Check quota status
engine.get_api_quota_status()

# Clear cache if needed
engine.rate_limiter.clear_cache('genderize')
```

**3. Scraping Blocked**
```
# Platform blocked (999 error)
# Solution: Respect delays, use authenticated APIs
# LinkedIn especially sensitive - 3s minimum delay
```

**4. Cache Issues**
```bash
# Clear all caches
rm -rf .api_cache/

# Or programmatically
engine.rate_limiter.clear_cache()
```

---

## Performance Tuning

### Processing Speed

- **Default**: 20-40 seconds per row (with 5 links + APIs)
- **Optimized**: 15-25 seconds (with caching hits)
- **Throughput**: 90-180 rows/hour

### Optimization Strategies

1. **Reduce max_links** - Process fewer links per row
2. **Skip APIs** - Disable non-critical enrichments
3. **Increase delays** - More respectful, but slower
4. **Batch processing** - Process multiple rows in parallel (advanced)

---

## Next Steps

1. **Run tests**: `python test_enhanced_enrichment.py`
2. **Test single row**: Use Example 1 code
3. **Check quotas**: Use Example 2 code
4. **Integrate with sheets**: Update existing enrichers
5. **Monitor performance**: Track processing times

---

## Support

**Documentation:**
- `implementation_progress_29-9-25.md` - Full implementation details
- `code-analysis-29-9-25.md` - Original system architecture
- `data-up-29-9-25.md` - Data collection strategy

**Test Files:**
- `test_enhanced_enrichment.py` - Comprehensive test suite

**Need Help?**
- Review test output for errors
- Check API quota status
- Verify all files are present
- Ensure dependencies installed

---

**🦈 LeadShark v3.0 Enhanced Enrichment** - Built with predatory precision for comprehensive lead intelligence.