# 🤖 LeadShark AI - Quick Start Guide
## Get AI-Powered Lead Enrichment Running in 5 Minutes

---

## ⚡ Quick Setup (5 Minutes)

### 1. Install Dependencies (1 min)

```bash
pip install anthropic==0.39.0
```

### 2. Get API Key (2 min)

1. Visit: https://console.anthropic.com
2. Sign up (free $5 credit included)
3. Go to Settings → API Keys
4. Click "Create Key"
5. Copy your key (starts with `sk-ant-api03-...`)

### 3. Configure (1 min)

```bash
# Create .env file
cp .env.example .env

# Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE" >> .env
```

### 4. Test (30 seconds)

```bash
python anthropic_enrichment.py
```

Expected output:
```
🧪 Testing Anthropic API Connection...
✅ Anthropic client initialized
✅ AI analysis successful!
```

### 5. Run Enrichment (30 seconds)

```bash
# Test with first 3 rows
python ai_powered_enricher.py \
  --sheet-id "YOUR_SHEET_ID" \
  --test
```

**Done! 🎉** Your leads are now being enriched with AI-powered intelligence.

---

## 📊 What You Get

### Before (Traditional LeadShark)
- Gender detection
- Email verification
- Website scraping
- Basic categorization

### After (AI-Powered LeadShark) ✨
- **AI Content Analysis:** Intelligent company categorization
- **Smart Lead Scoring:** 0-100 score with reasoning
- **Intelligence Reports:** Natural language summaries
- **Action Recommendations:** Specific engagement strategies
- **Confidence Metrics:** Data quality indicators

---

## 💡 Usage Examples

### Basic Usage

```bash
# Process first 10 rows
python ai_powered_enricher.py \
  --sheet-id "1234567890abcdef" \
  --max-rows 10

# Process all rows
python ai_powered_enricher.py \
  --sheet-id "1234567890abcdef"
```

### Programmatic Usage

```python
from ai_powered_enricher import AIPoweredEnricher

enricher = AIPoweredEnricher(
    sheet_id="your_sheet_id",
    tab_name="Sheet1"
)

stats = enricher.process_sheet(max_rows=10)
print(f"Processed: {stats['rows_processed']}")
print(f"AI-enhanced: {stats['ai_enhanced']}")
```

---

## 💰 Cost

- **Free Tier:** $5 credit = ~100-150 leads enriched
- **After Free:** ~$0.03-0.05 per lead
- **Monthly Examples:**
  - 100 leads = $3-5
  - 500 leads = $15-25
  - 1,000 leads = $30-50

---

## 🛡️ Safety Features

✅ **Automatic Fallback:** Falls back to traditional methods if AI unavailable
✅ **No Breaking Changes:** Works with existing LeadShark setup
✅ **Secure by Default:** API keys never exposed or logged
✅ **Rate Limit Handling:** Graceful degradation on API limits

---

## 🔧 Troubleshooting

### "anthropic not installed"
```bash
pip install anthropic==0.39.0
```

### "API key not set"
```bash
# Check .env file
cat .env | grep ANTHROPIC_API_KEY
```

### "AI enrichment disabled"
```bash
# Test connection
python anthropic_enrichment.py
```

---

## 📚 Full Documentation

- **Complete Guide:** `doc/AI_INTEGRATION_GUIDE.md`
- **API Reference:** `anthropic_enrichment.py`
- **Integration Example:** `ai_powered_enricher.py`

---

## 🎯 Next Steps

1. ✅ Test with 3-5 rows (`--test`)
2. ✅ Review enriched data in Google Sheet
3. ✅ Process full dataset
4. ✅ Customize scoring logic (optional)
5. ✅ Monitor usage in Anthropic console

---

## 🆘 Need Help?

1. Check logs: `ai_enrichment.log`
2. Review docs: `doc/AI_INTEGRATION_GUIDE.md`
3. Test API: `python anthropic_enrichment.py`
4. File issue: GitHub Issues

---

**🦈🤖 LeadShark + Claude: Intelligence Meets AI**

*Ready in 5 minutes • Secure by default • $5 free credit*