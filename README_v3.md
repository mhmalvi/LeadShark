# 🦈 LeadShark v3.0 Enhanced Enrichment - Quick Reference

## ⚡ Quick Start (5 minutes)

### 1. Verify Installation
```bash
python test_enhanced_enrichment.py
```
✅ Expected: All 5/5 tests pass

### 2. Check API Quotas
```bash
python run_enhanced_enrichment.py --quotas
```
✅ Expected: Display quota status for all 6 APIs

### 3. Test Single Row
```bash
python run_enhanced_enrichment.py --test
```
✅ Expected: Enrich test data with score and context (~7-11 seconds)

---

## 🚀 Usage Commands

### Test Mode
```bash
# Run comprehensive test suite
python test_enhanced_enrichment.py

# Test single row enrichment
python run_enhanced_enrichment.py --test
```

### API Management
```bash
# Check current quota status
python run_enhanced_enrichment.py --quotas

# View verbose API details
python run_enhanced_enrichment.py --quotas --verbose
```

### Process Google Sheet

#### Dry Run (Preview Only)
```bash
# Preview 5 rows without writing
python run_enhanced_enrichment.py --sheet-id YOUR_SHEET_ID --max-rows 5 --dry-run

# Preview with 3 links per row
python run_enhanced_enrichment.py --sheet-id YOUR_SHEET_ID --max-rows 5 --max-links 3 --dry-run
```

#### Live Processing
```bash
# Enrich 10 rows (5 links per row, default)
python run_enhanced_enrichment.py --sheet-id YOUR_SHEET_ID --max-rows 10

# Enrich 20 rows with 3 links per row
python run_enhanced_enrichment.py --sheet-id YOUR_SHEET_ID --max-rows 20 --max-links 3

# Verbose logging for debugging
python run_enhanced_enrichment.py --sheet-id YOUR_SHEET_ID --max-rows 5 --verbose
```

---

## 📊 Output Column Structure

### 8 Enrichment Columns Added to Sheet

| Column | Content | Format |
|--------|---------|--------|
| **Enrich::Row Key** | Unique identifier | Text |
| **Enrich::Lead Score** | 0-100 score | Number |
| **Enrich::Lead Tags** | Hot/Warm/Cold/Discard + emoji | Text |
| **Enrich::Complete Context** | Professional paragraph | Text |
| **Enrich::Link Data** | All scraped links | JSON |
| **Enrich::API Enrichment** | All API results | JSON |
| **Enrich::Score Breakdown** | Detailed scoring | JSON |
| **Enrich::Status & Meta** | Processing metadata | JSON |

---

## 🎯 Lead Score Classifications

| Score | Tag | Priority | Action |
|-------|-----|----------|--------|
| **80-100** | Hot 🔥 | Immediate | High-priority outreach |
| **60-79** | Warm 🟡 | Follow-up | Nurture campaign |
| **30-59** | Cold 🔵 | Monitor | Drip campaign |
| **0-29** | Discard ⚫ | Skip | Unqualified |

---

## 💰 API Costs & Quotas

### Free Tier Limits
| API | Free Tier | Cost After | Cache TTL |
|-----|-----------|------------|-----------|
| **Genderize.io** | 500/month | $0.01/req | 30 days |
| **EVA Email** | Unlimited | Free | 24 hours |
| **GitHub** | 60/hour | Free (with token: 5000/hour) | 24 hours |
| **Google Search** | 100/day | $5/1000 | 7 days |
| **LinkedIn** | Unlimited | Free | 7 days |

**Estimated cost:** $0 for first 500 leads/month

---

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Required
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials.json
GOOGLE_SHEET_ID=your_sheet_id_here

# Optional (for higher API limits)
GITHUB_TOKEN=your_github_token

# Processing Settings
MAX_ROWS_PER_BATCH=50
MAX_LINKS_PER_ROW=5
PROCESSING_DELAY=2.0
LOG_LEVEL=INFO
```

### Adjust Processing Speed
```python
# Edit run_enhanced_enrichment.py or call directly
enricher = EnhancedCompactEnricher(
    sheet_id="YOUR_SHEET_ID",
    max_links=3,  # Reduce for faster processing
    dry_run=False
)
```

---

## 📈 Performance Tips

### Optimize for Speed
1. **Reduce max_links:** Use `--max-links 3` instead of 5
2. **Use caching:** Run duplicates for instant results
3. **Batch processing:** Process 10-20 rows at a time
4. **GitHub token:** Add token for 5000/hour limit (vs 60/hour)

### Optimize for Cost
1. **Enable caching:** Automatic (24-hour TTL)
2. **Deduplicate names:** Same first names use cached gender data
3. **Monitor quotas:** Check `--quotas` regularly
4. **Adjust cache TTL:** Edit `api_rate_limiter.py` for longer caching

---

## 🐛 Troubleshooting

### Test Suite Fails
```bash
# Check imports
python -c "from enhanced_enrichment_engine import EnhancedEnrichmentEngine"

# Verify all files exist
ls *enrichment*.py
```

### Google Sheets Auth Failed
```bash
# Check credentials file
ls credentials.json

# Re-authenticate (if needed)
python manual_auth.py
```

### Rate Limit Exceeded
```bash
# Check current status
python run_enhanced_enrichment.py --quotas

# Clear cache if needed (use with caution)
rm -rf .api_cache/
```

### Slow Processing
- **Expected:** 7-11 seconds per row (first run)
- **With cache:** 5-7 seconds per row
- **LinkedIn anti-bot:** Adds 3-5 seconds delay
- **Reduce links:** Use `--max-links 3` for faster processing

---

## 📚 Documentation

### Main Docs
- **Quick Start:** `doc/ENHANCED_ENRICHMENT_QUICKSTART.md`
- **Implementation:** `doc/IMPLEMENTATION_COMPLETE.md`
- **Progress Report:** `doc/implementation_progress_29-9-25.md`
- **Final Status:** `doc/FINAL_STATUS.md`

### Code Examples
- **Test Suite:** `test_enhanced_enrichment.py`
- **CLI Runner:** `run_enhanced_enrichment.py`
- **Core Engine:** `enhanced_enrichment_engine.py`

---

## 🔧 Advanced Usage

### Python API
```python
from enhanced_enrichment_engine import EnhancedEnrichmentEngine

# Initialize
engine = EnhancedEnrichmentEngine()

# Enrich single row
row_data = {
    'name': 'John Doe',
    'first_name': 'John',
    'email': 'john@example.com',
    'company': 'ExampleCorp',
    'linkedin_url': 'https://linkedin.com/in/johndoe',
    'website': 'https://example.com'
}

result = engine.enrich_row(row_data, max_links=5)

# Access results
print(f"Score: {result['lead_score']} - {result['lead_tags']}")
print(f"Context: {result['complete_context']}")
print(f"Links: {len(result['link_data'])}")
print(f"APIs: {len(result['api_enrichment'])}")
```

### Check Quotas Programmatically
```python
from enhanced_enrichment_engine import EnhancedEnrichmentEngine

engine = EnhancedEnrichmentEngine()
quotas = engine.get_api_quota_status()

for api_name, status in quotas.items():
    print(f"{api_name}: {status['remaining']}/{status['quota']}")
```

---

## ✅ Production Checklist

### Before First Run
- [ ] Test suite passes (5/5 tests)
- [ ] Google Sheets credentials configured
- [ ] API keys added to .env (optional but recommended)
- [ ] Test with `--dry-run` first
- [ ] Verify quota status with `--quotas`

### Regular Monitoring
- [ ] Check API quotas weekly
- [ ] Review enrichment quality
- [ ] Adjust scoring weights if needed
- [ ] Clear cache monthly (optional)
- [ ] Monitor processing speed

---

## 🎉 Success Indicators

✅ **System Working Correctly:**
- Test suite: 5/5 tests pass
- Processing time: 7-11 seconds per row
- API calls: 5/5 successful
- Cache hit rate: 70-100%
- Lead scores: Distributed across Hot/Warm/Cold/Discard

⚠️ **Needs Attention:**
- Test failures
- Processing time >20 seconds consistently
- API errors >10%
- Low cache hit rate (<50%)
- All leads scoring same category

---

**🦈 LeadShark v3.0 Enhanced Enrichment**
*Ready to hunt with predatory precision!*

**Version:** v3.0-Enhanced-Compact
**Status:** Production-Ready ✅
**Test Pass Rate:** 100%
**Last Verified:** 2025-09-30