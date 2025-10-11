# 💰 LeadShark API Cost Optimization Guide

**Date:** 2025-10-06
**Version:** v5.1
**Goal:** Reduce API costs by 60-80% while maintaining enrichment quality

---

## 📊 Current API Cost Breakdown (Per Lead)

### Phase 1: Multi-Link Scraping
- **Free** - No API costs (web scraping only)
- Rate limiting: Built-in delays to avoid blocking

### Phase 2: AI Intelligence
- **OpenAI GPT-4o-mini:** ~$0.0004 per analysis
  - Input: ~1000 tokens (scraped content)
  - Output: ~500 tokens (structured analysis)
  - Cost: $0.00015 per 1K input + $0.0006 per 1K output = **~$0.00045/lead**

### Phase 3: API Enrichment (5 APIs)
1. **Genderize.io** - FREE (1000 req/day)
2. **EVA Email Verification** - FREE (no limit)
3. **GitHub API** - FREE (5000 req/hour)
4. **Google Custom Search** - FREE (100 searches/day) OR $5/1000 after
5. **LinkedIn Scraping** - FREE (web scraping with rate limits)

**Total Phase 3:** $0.00 - $0.005 (if Google quota exceeded)

### Phase 4: Cold Outreach Personalization
- **No API costs** - Uses existing scraped data

### Phase 5: AI Email Sequences
- **OpenAI GPT-4o-mini:** ~$0.001 per sequence (5 emails)
  - Input: ~1500 tokens (lead data + prompt)
  - Output: ~750 tokens (5 emails)
  - Cost: $0.00015 per 1K input + $0.0006 per 1K output = **~$0.00068/lead**

---

## 💸 Total Current Cost Per Lead

| Scenario | Cost/Lead | Cost/100 Leads | Cost/1000 Leads |
|----------|-----------|----------------|-----------------|
| **Best Case** (all free APIs) | $0.0012 | $0.12 | $1.20 |
| **Typical** (some Google API) | $0.0018 | $0.18 | $1.80 |
| **Worst Case** (all paid APIs) | $0.0025 | $0.25 | $2.50 |

**Primary Cost Drivers:**
1. **OpenAI GPT-4o-mini (AI Intelligence)** (35% of cost) - $0.00045/lead
2. **OpenAI GPT-4o-mini (Email Sequences)** (53% of cost) - $0.00068/lead
3. **Google Search API** (0-40% of cost) - $0.00-0.005/lead

---

## 🎯 Optimization Strategies

### Strategy 1: Smart Caching (60-80% Cost Reduction)

**Implementation:**
- Cache AI analysis results by company domain
- Cache email verification results for 30 days
- Cache GitHub/Google Search results for 7 days
- Cache personalization hooks for 14 days

**Expected Savings:**
- **Anthropic calls:** 70% reduction (companies repeat)
- **OpenAI calls:** 50% reduction (similar industries)
- **Google Search:** 80% reduction (company info stable)

**Code Changes Required:**
```python
# Add to hybrid_ai_enhanced_enricher.py
class SmartCache:
    def __init__(self, cache_dir='.api_cache'):
        self.cache_dir = cache_dir
        self.ttl = {
            'ai_analysis': 30 * 24 * 3600,  # 30 days
            'email_verification': 30 * 24 * 3600,
            'google_search': 7 * 24 * 3600,
            'github': 7 * 24 * 3600,
            'personalization': 14 * 24 * 3600
        }

    def get(self, key, cache_type):
        # Check cache and TTL
        # Return cached result or None

    def set(self, key, value, cache_type):
        # Store in cache with timestamp
```

**Impact:**
- Cost/Lead: $0.011 → **$0.003-0.005**
- Cost/1000 Leads: $11.00 → **$3.00-5.00**

---

### Strategy 2: Conditional AI Enrichment (30-50% Reduction)

**Implementation:**
- Only call Anthropic Claude for high-value leads (score > 40)
- Use lightweight regex extraction for low-score leads
- Skip email sequences for "Cold" leads (score < 30)

**Logic:**
```python
# In hybrid_ai_enhanced_enricher.py
if lead_score < 30:
    # Skip AI analysis, use basic categorization
    ai_result = extract_basic_category(scraped_content)
    skip_email_sequences = True
elif lead_score < 60:
    # Use cheaper GPT-4o-mini for analysis
    ai_result = openai_analysis(scraped_content)
else:
    # Use Claude for high-quality analysis
    ai_result = anthropic_analysis(scraped_content)
```

**Impact:**
- ~40% of leads skip expensive AI (Cold leads)
- ~30% use cheaper GPT instead of Claude (Warm leads)
- Only 30% use full Claude analysis (Hot leads)

**Savings:**
- Anthropic cost: $0.0105 → **$0.004/lead**
- Email sequences: $0.00068 → **$0.0004/lead**

---

### Strategy 3: Batch Processing (20-30% Reduction)

**Implementation:**
- Process leads in batches of 10-20
- Single API call for multiple leads where possible
- Deduplicate company lookups

**Example:**
```python
# Group leads by company domain
companies = group_by_domain(leads)

# Single API call per unique company
for domain, company_leads in companies.items():
    company_info = get_company_info(domain)  # 1 API call
    for lead in company_leads:
        lead.company_info = company_info  # Reuse result
```

**Impact:**
- Google Search calls: 100 → **30-40** (for 100 leads)
- Company AI analysis: 100 → **40-50** (for 100 leads)

---

### Strategy 4: Use Free Alternatives (40-60% Reduction)

**Current → Alternative:**

1. **Anthropic Claude → GPT-4o-mini for analysis**
   - Cost: $0.0105 → **$0.0004** (96% cheaper)
   - Quality: Similar for structured categorization
   - Use Case: All AI intelligence except nuanced analysis

2. **Google Custom Search → Web scraping**
   - Cost: $0.005 → **$0.00** (100% free)
   - Quality: Same data, slower
   - Use Case: Company info extraction

3. **Hunter.io/ZeroBounce → EVA + Pattern Generation**
   - Cost: Paid APIs → **Free** (already implemented)
   - Quality: Good enough for 80% of cases

**Implementation:**
```python
# Use GPT-4o-mini instead of Claude for AI analysis
def analyze_with_gpt(content):
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": analysis_prompt}],
        temperature=0.3,
        max_tokens=500
    )
    return parse_analysis(response)
```

---

### Strategy 5: Intelligent Rate Limiting (Prevent Overage Charges)

**Implementation:**
- Track daily API usage per service
- Stop enrichment when approaching free tier limits
- Queue remaining leads for next day

**Code:**
```python
class APIRateLimiter:
    def __init__(self):
        self.limits = {
            'genderize': 1000,  # per day
            'google_search': 100,  # per day
            'github': 5000,  # per hour
        }
        self.usage = {}

    def can_call(self, service):
        current = self.usage.get(service, 0)
        return current < self.limits[service]

    def increment(self, service):
        self.usage[service] = self.usage.get(service, 0) + 1
```

---

## 🚀 Recommended Implementation Plan

### Phase 1: Quick Wins (Implement First)
1. ✅ **Smart Caching** - 60% cost reduction, easy to implement
2. ✅ **Conditional AI** - Skip AI for low-score leads
3. ✅ **Rate Limiting** - Prevent overage charges

**Expected Savings:** 70-80% cost reduction
**Implementation Time:** 2-3 hours

### Phase 2: Advanced Optimizations
4. **Batch Processing** - Group by company domain
5. **Replace Claude with GPT-4o-mini** - For non-critical analysis

**Expected Additional Savings:** 10-15% cost reduction
**Implementation Time:** 4-6 hours

### Phase 3: Quality Monitoring
6. **A/B Testing** - Compare output quality (Claude vs GPT-4o-mini)
7. **Cache Hit Rate Tracking** - Monitor cache effectiveness

---

## 📈 Projected Cost After Optimization

| Scenario | Before | After | Savings |
|----------|--------|-------|---------|
| **Per Lead** | $0.013 | **$0.002-0.004** | 70-85% |
| **100 Leads** | $1.30 | **$0.20-0.40** | 70-85% |
| **1000 Leads** | $13.00 | **$2.00-4.00** | 70-85% |

**Breakdown After Optimization:**
- Anthropic Claude: $0.0105 → $0.0015 (caching + conditional)
- OpenAI GPT: $0.00068 → $0.0003 (caching + conditional)
- Google Search: $0.005 → $0.0001 (caching + free scraping)
- Other APIs: $0.00 (remain free)

**Total: ~$0.002/lead** (85% reduction!)

---

## ⚙️ Implementation Code Snippets

### 1. Smart Caching

```python
import os
import json
import time
import hashlib

class SmartCache:
    def __init__(self, cache_dir='.api_cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        # Cache TTL in seconds
        self.ttl = {
            'ai_analysis': 30 * 24 * 3600,  # 30 days
            'email_verification': 30 * 24 * 3600,
            'google_search': 7 * 24 * 3600,
            'github': 7 * 24 * 3600,
            'personalization': 14 * 24 * 3600
        }

    def _get_cache_key(self, key, cache_type):
        """Generate cache key hash"""
        key_str = f"{cache_type}:{key}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key, cache_type):
        """Get cached result if valid"""
        cache_key = self._get_cache_key(key, cache_type)
        cache_file = os.path.join(self.cache_dir, cache_type, f"{cache_key}.json")

        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # Check TTL
            age = time.time() - cached['timestamp']
            if age > self.ttl.get(cache_type, 7 * 24 * 3600):
                return None  # Expired

            return cached['data']
        except:
            return None

    def set(self, key, value, cache_type):
        """Store in cache"""
        cache_key = self._get_cache_key(key, cache_type)
        cache_dir = os.path.join(self.cache_dir, cache_type)
        os.makedirs(cache_dir, exist_ok=True)

        cache_file = os.path.join(cache_dir, f"{cache_key}.json")

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': time.time(),
                    'data': value
                }, f, indent=2)
        except:
            pass  # Silent fail
```

### 2. Conditional AI Enrichment

```python
def intelligent_ai_enrichment(self, scraped_content, lead_score):
    """
    Use appropriate AI model based on lead score
    - Score < 30: Skip AI, use basic extraction
    - Score 30-60: Use GPT-4o-mini (cheap)
    - Score > 60: Use Claude (premium)
    """
    # Check cache first
    cache_key = hashlib.md5(scraped_content.encode()).hexdigest()
    cached = self.cache.get(cache_key, 'ai_analysis')
    if cached:
        return cached

    if lead_score < 30:
        # Cold lead - basic extraction only
        result = self.extract_basic_category(scraped_content)
    elif lead_score < 60:
        # Warm lead - use cheaper GPT-4o-mini
        result = self.analyze_with_gpt(scraped_content)
    else:
        # Hot lead - use premium Claude
        result = self.analyze_with_claude(scraped_content)

    # Cache result
    self.cache.set(cache_key, result, 'ai_analysis')
    return result
```

### 3. Batch Processing by Company

```python
def batch_process_by_company(self, rows):
    """Process multiple leads from same company efficiently"""
    # Group by company domain
    companies = {}
    for row in rows:
        domain = extract_domain(row.get('website', ''))
        if domain not in companies:
            companies[domain] = []
        companies[domain].append(row)

    results = []
    for domain, company_rows in companies.items():
        # Single company lookup for all leads
        company_info = self.get_company_info(domain)  # 1 API call
        company_ai = self.analyze_company(company_info)  # 1 AI call

        # Reuse for all leads from this company
        for row in company_rows:
            row_result = self.enrich_lead(row, company_info, company_ai)
            results.append(row_result)

    return results
```

---

## 📊 Monitoring & Metrics

Track these metrics to measure optimization effectiveness:

```python
class CostTracker:
    def __init__(self):
        self.costs = {
            'anthropic': 0,
            'openai': 0,
            'google_search': 0,
        }
        self.api_calls = {
            'anthropic': 0,
            'openai': 0,
            'google_search': 0,
        }
        self.cache_hits = 0
        self.cache_misses = 0

    def log_api_call(self, service, cost):
        self.costs[service] += cost
        self.api_calls[service] += 1

    def log_cache(self, hit=True):
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def get_summary(self):
        total_cost = sum(self.costs.values())
        cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses)

        return {
            'total_cost': total_cost,
            'cost_per_lead': total_cost / (self.cache_hits + self.cache_misses),
            'cache_hit_rate': f"{cache_hit_rate:.1%}",
            'api_calls': self.api_calls
        }
```

---

## ✅ Next Steps

1. **Implement Smart Caching** (highest impact, easiest)
2. **Add Conditional AI** (second highest impact)
3. **Test with 10-20 leads** to verify quality
4. **Monitor cache hit rates** and API costs
5. **Gradually roll out** to full production

**Expected Result:** 70-85% cost reduction with minimal quality loss!

---

**Questions?** See `hybrid_enricher.log` for detailed API usage tracking.
