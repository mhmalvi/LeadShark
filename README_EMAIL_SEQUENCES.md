# 📨 LeadShark v5.1 - AI Email Sequences

**Complete 5-email cold outreach sequences powered by OpenAI GPT-4o-mini**

---

## ✅ What's New

LeadShark now generates **personalized 5-email sequences** for each lead using:
- All enriched data (LinkedIn, company info, AI analysis, cold outreach signals)
- OpenAI GPT-4o-mini for context-aware email writing
- 15 new columns in Google Sheets (85 total, up from 70)

**Email Sequence:**
1. **Email 1 (Day 1):** Initial outreach - introduce yourself and establish relevance
2. **Email 2 (Day 3):** Value-add follow-up - provide value without asking for anything
3. **Email 3 (Day 7):** Social proof - show results with similar companies
4. **Email 4 (Day 10):** Direct ask - clear CTA for 15-min call
5. **Email 5 (Day 14):** Break-up - humble, understanding, door-open

---

## 🚀 Quick Start

### 1. Set Your OpenAI API Key

```bash
# Windows
set OPENAI_API_KEY=sk-your-key-here

# Linux/Mac
export OPENAI_API_KEY="sk-your-key-here"
```

### 2. (Optional) Customize Sender Info

Edit `hybrid_ai_enhanced_enricher.py` lines 617-622:

```python
sender_info = {
    'name': 'Your Name',          # ← Change this
    'company': 'Your Company',    # ← Change this
    'title': 'Your Title',        # ← Change this
    'value_proposition': 'We help companies grow'  # ← Change this
}
```

### 3. Run Enrichment

```bash
python hybrid_ai_enhanced_enricher.py
```

---

## 📊 New Columns

The enricher now adds **15 email sequence columns**:

| Column | Content |
|--------|---------|
| `Enrich::📨 Email 1 - Subject` | Personalized subject line |
| `Enrich::📨 Email 1 - Body` | 100-150 word email body |
| `Enrich::📨 Email 1 - Timing` | "Day 1" |
| `Enrich::📨 Email 2-5...` | *Same structure for emails 2-5* |
| `Enrich::⚙️ Email Sequence Status` | "Generated" / "Not Generated" |
| `Enrich::⚙️ Email Sequence Generated At` | ISO timestamp |

---

## 💡 How It Works

### Phase 5: AI Email Sequences

After completing Phases 1-4, the enricher:

1. **Collects comprehensive lead data** from all previous phases:
   - LinkedIn profile (headline, experience, company)
   - AI business analysis (category, value proposition)
   - Cold outreach signals (pain points, trigger events, recent activity)
   - Lead scoring and enrichment data

2. **Calls OpenAI GPT-4o-mini** with a comprehensive prompt containing:
   - All lead information
   - Your sender/product info
   - Email sequence context (which email in the sequence)
   - Tone and goal for this specific email

3. **Generates 5 personalized emails** tailored to:
   - The lead's LinkedIn headline and experience
   - Their company's recent activity and trigger events
   - Detected pain points and business needs
   - Industry-specific messaging

---

## 🧪 Test It

### Standalone Test
```bash
python ai_email_sequence_generator.py
```

### Integration Test
```bash
python test_email_sequences.py
```

**Expected Output:**
```
✅ Standalone Generator: PASSED
✅ Hybrid Enricher Integration: PASSED
```

---

## 💰 Cost

- **Per Lead:** ~$0.001 (5 emails via GPT-4o-mini)
- **100 Leads:** ~$0.10
- **1000 Leads:** ~$1.00

**Much cheaper than Anthropic Claude!** 🎉

---

## ⚠️ Troubleshooting

### Issue: "Email Sequence Status" = "Not Generated"

**Solutions:**
1. Set `OPENAI_API_KEY`:
   ```bash
   set OPENAI_API_KEY=sk-your-key-here
   ```

2. Verify row has "name" and "company" columns

3. Check `hybrid_enricher.log` for errors

### Issue: Generic email content

**Causes:** Limited enrichment data (missing LinkedIn, no activity, etc.)

**Solutions:**
1. Ensure Phases 1-4 complete successfully
2. Configure LinkedIn credentials for better profile data
3. Verify Google Search API for company info

---

## 📚 Documentation

- **Full Feature Guide:** `doc/EMAIL_SEQUENCES_V5.1.md`
- **Implementation Status:** `doc/V5.1_IMPLEMENTATION_STATUS.md`
- **Main README:** `README_V5.md`

---

## 🎯 What You Get

**Complete enrichment pipeline with 85 columns:**

1. ✅ Multi-Link Scraping (15 columns)
2. ✅ AI Intelligence (8 columns) - Anthropic Claude + OpenAI GPT
3. ✅ Lead Scoring (3 columns)
4. ✅ API Enrichment (15 columns) - Gender, Email, GitHub, Google, LinkedIn
5. ✅ Enhanced Email Finding (4 columns)
6. ✅ Cold Outreach Personalization (5 columns)
7. ✅ Cold Email Components (6 columns)
8. ✅ **AI Email Sequences (15 columns)** ← NEW!
9. ✅ Score Breakdown (6 columns)
10. ✅ Processing Metadata (6 columns)

---

## ✨ Example Output

**Email 1 (Day 1):**
```
Subject: Helping Ahead Creative Streamline Client Reporting

Hi Lorenzo,

I came across your impressive work at Ahead Creative, especially with
the recent expansion into TV spot production. It's clear you're committed
to pushing creative boundaries for your clients.

I noticed that manual client reporting and lengthy approval workflows
can be significant time drains. At WorkflowPro, we specialize in automating
these processes, saving creative agencies like yours over 10 hours a week.

Would you be open to a brief chat next week?

Best,
Alex Johnson
Head of Partnerships | WorkflowPro

P.S. Congratulations on the new hires! Exciting times ahead.
```

**All emails are personalized to the specific lead's:**
- LinkedIn profile and experience
- Company's recent activity
- Detected pain points
- Industry and business category

---

**Ready to enrich! 🦈📨**

For support, check `hybrid_enricher.log` or see full documentation in `doc/`.
