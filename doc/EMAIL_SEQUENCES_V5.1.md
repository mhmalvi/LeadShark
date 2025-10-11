# 📨 AI Email Sequences (v5.1)

## Overview

LeadShark v5.1 introduces **AI-powered sequential email generation** - a complete 5-email cadence personalized to each lead using comprehensive enrichment data.

**Features:**
- ✅ 5-email sequence (Initial → Follow-up → Social Proof → Direct Ask → Break-up)
- ✅ Powered by OpenAI GPT-4o-mini
- ✅ Personalized to all enriched data (LinkedIn, pain points, activity, AI insights)
- ✅ Multiple tone variations per email type
- ✅ Industry-specific messaging
- ✅ Automated timing recommendations
- ✅ 15 new columns (85 total, up from 70)

---

## Email Sequence Structure

### Email 1: Initial Outreach (Day 1)
**Goal:** Introduce yourself and establish relevance
**Tone:** Professional, curious, value-focused
**Length:** 100-150 words

**Personalization:**
- References LinkedIn headline
- Mentions recent company activity (if detected)
- Addresses detected pain points subtly

---

### Email 2: Value Add Follow-up (Day 3)
**Goal:** Provide value without asking for anything
**Tone:** Helpful, educational, non-pushy
**Length:** 100-150 words

**Personalization:**
- Shares relevant insight or resource
- References industry trends
- No CTA, pure value delivery

---

### Email 3: Case Study/Social Proof (Day 7)
**Goal:** Show results with similar companies
**Tone:** Data-driven, proof-focused
**Length:** 100-150 words

**Personalization:**
- Uses AI-detected business category
- References similar company success
- Includes social proof from enrichment data

---

### Email 4: Direct Ask (Day 10)
**Goal:** Clear call-to-action for meeting
**Tone:** Direct, confident, respectful
**Length:** 100-150 words

**Personalization:**
- Summarizes value proposition
- Direct request for 15-min call
- Suggests specific meeting topics

---

### Email 5: Break-up Email (Day 14)
**Goal:** Final attempt with permission to close loop
**Tone:** Humble, understanding, door-open
**Length:** 50-100 words

**Personalization:**
- Acknowledges lack of response
- Offers to close file
- Leaves door open for future contact

---

## New Columns (15 Total)

### Email Sequence Columns

| Column Name | Content | Example |
|-------------|---------|---------|
| **Enrich::📨 Email 1 - Subject** | Subject line for initial email | "Quick question about Acme's recent expansion" |
| **Enrich::📨 Email 1 - Body** | Full email body | "Hi John,\n\nNoticed your work at Acme..." |
| **Enrich::📨 Email 1 - Timing** | When to send | "Day 1" |
| **Enrich::📨 Email 2 - Subject** | Subject line for follow-up | "Resource for Acme's marketing team" |
| **Enrich::📨 Email 2 - Body** | Full email body | "Hi John,\n\nThought this might help..." |
| **Enrich::📨 Email 2 - Timing** | When to send | "Day 3" |
| ... | *Repeat for emails 3-5* | ... |

### Metadata Columns

| Column Name | Content | Example |
|-------------|---------|---------|
| **Enrich::⚙️ Email Sequence Status** | Generation status | "Generated" / "Not Generated" |
| **Enrich::⚙️ Email Sequence Generated At** | Timestamp | "2025-01-15T10:30:00Z" |

---

## How It Works

### Phase 5: Email Sequence Generation

After completing Phases 1-4 (scraping, AI analysis, email finding, cold outreach), the enricher now runs **Phase 5**:

```python
# Collect all enriched data
lead_data = {
    'name': 'John Smith',
    'company': 'Acme Inc',
    'title': 'VP Marketing',
    'industry': 'SaaS',
    'linkedin_headline': 'VP Marketing at Acme | Growth Specialist',
    'recent_activity': 'Recently expanded into TV spot production',
    'pain_points': 'Manual client reporting | Time-consuming workflows',
    'trigger_events': 'hiring: Hiring two new directors',
    'social_proof': '8 years in business | 200+ clients',
    'lead_score': 85,
    'ai_category': 'Marketing Agency',
    'ai_value_proposition': 'Comprehensive creative services'
}

# Generate 5-email sequence
sequence = email_sequence_generator.generate_complete_sequence(
    lead_data=lead_data,
    sender_info=sender_info,
    product_info=product_info
)
```

### Data Sources Used

The AI email generator uses data from **all enrichment phases**:

1. **Phase 1 (Scraping):** Company info, scraped content
2. **Phase 2 (AI Analysis):** Business category, value prop, commercial readiness
3. **Phase 3 (Email Finding):** Email patterns, domain info
4. **Phase 4 (Cold Outreach):** Recent activity, pain points, trigger events, social proof
5. **LinkedIn Data:** Headline, company, experience, skills, connections

---

## Setup & Configuration

### 1. Set OpenAI API Key

```bash
# Windows
set OPENAI_API_KEY=sk-your-key-here

# Linux/Mac
export OPENAI_API_KEY="sk-your-key-here"
```

### 2. Configure Sender Info (Optional)

Edit `hybrid_ai_enhanced_enricher.py` line 616-621:

```python
sender_info = {
    'name': 'Your Name',          # Replace with your name
    'company': 'Your Company',    # Replace with your company
    'title': 'Your Title',        # Replace with your title
    'value_proposition': 'We help companies grow'  # Your value prop
}
```

### 3. Configure Product Info (Optional)

Edit `hybrid_ai_enhanced_enricher.py` line 624-629:

```python
product_info = {
    'name': 'Our Solution',       # Replace with product name
    'category': 'software',       # Replace with category
    'key_benefit': 'efficiency and growth',  # Replace with benefit
    'target_industries': [industry] if industry else []
}
```

---

## Usage

### Run Enrichment with Email Sequences

```bash
# Set API key
set OPENAI_API_KEY=sk-your-key-here

# Run enrichment (email sequences generate automatically)
python hybrid_ai_enhanced_enricher.py
```

### Example Output

After enrichment completes, you'll see 15 new columns populated:

**Email 1:**
- Subject: "Quick question about Acme's recent TV expansion"
- Body: "Hi John,\n\nI noticed Acme recently expanded into TV spot production—congrats on the move!..."
- Timing: "Day 1"

**Email 2:**
- Subject: "Resource for streamlining client reporting"
- Body: "Hi John,\n\nNo strings attached, but thought this guide on automated reporting might help your team..."
- Timing: "Day 3"

*(and so on for emails 3-5)*

---

## Personalization Examples

### Based on LinkedIn Data

> "I saw on LinkedIn you've been leading creative strategy for 50+ brands..."

### Based on Recent Activity

> "Congratulations on the recent expansion into TV spot production!"

### Based on Pain Points

> "I know manual client reporting can be time-consuming for agencies like Acme..."

### Based on Trigger Events

> "With two new creative directors joining your team, timing might be perfect to discuss workflow automation..."

### Based on AI Category

> "We've helped several full-service marketing agencies like Acme automate their client workflows..."

---

## Fallback Behavior

If the Anthropic API key is not set or API call fails:

1. **Email Sequence Status:** "Not Generated"
2. **All Email Columns:** Empty
3. **Logging:** Warning message logged
4. **Enrichment:** Continues normally (phases 1-4 still run)

Example log message:
```
[Phase 5] OpenAI API key not set (OPENAI_API_KEY), skipping email sequence generation
```

---

## Testing

### Test Email Sequence Generator Standalone

```bash
# Set API key
set OPENAI_API_KEY=sk-your-key-here

# Run standalone test
python ai_email_sequence_generator.py
```

**Expected Output:**
```
================================================================================
AI-POWERED EMAIL SEQUENCE
================================================================================

================================================================================
EMAIL #1: Initial Outreach
Timing: Day 1
Goal: Introduce yourself and establish relevance
================================================================================

SUBJECT: Quick question about Ahead Creative

BODY:
Hi Lorenzo,

I noticed your work at Ahead Creative...
[personalized email body]

P.S. Saw you recently expanded into TV spots—exciting move!
```

### Test Full Enrichment Pipeline

```bash
# Run integration test (uses sample data)
python test_v5_integration.py
```

---

## Column Count Evolution

| Version | Total Columns | New Feature |
|---------|---------------|-------------|
| v4.0 | 59 | AI intelligence + lead scoring |
| v5.0 | 70 | Cold outreach components |
| **v5.1** | **85** | **AI email sequences (+15 columns)** |

---

## Performance Notes

### Generation Time

- **Phase 5 (Email Sequences):** ~5-10 seconds per lead (GPT API)
- **Total Per-Row Time:** ~15-25 seconds (all phases)

### API Costs

- **GPT-4o-mini:** ~$0.001 per email sequence (5 emails)
- **Per Row:** ~$0.001 for Phase 5
- **100 Rows:** ~$0.10 for email sequences

---

## Troubleshooting

### Issue: "Email Sequence Status" shows "Not Generated"

**Causes:**
1. `OPENAI_API_KEY` not set
2. Missing lead name or company name
3. API call failed (rate limit, network error)

**Solutions:**
1. Set environment variable: `set OPENAI_API_KEY=sk-...`
2. Verify row has "name" and "company" columns
3. Check `hybrid_enricher.log` for error details

---

### Issue: Email content is generic

**Causes:**
1. Limited enrichment data (empty LinkedIn, no activity, etc.)
2. AI fallback mode triggered

**Solutions:**
1. Ensure Phases 1-4 complete successfully
2. Configure LinkedIn credentials for better profile data
3. Verify Google Search API for company info

---

### Issue: Empty email columns despite API key set

**Causes:**
1. Row missing required data (name, company)
2. Previous phase failed (no combined_content)

**Solutions:**
1. Check row has populated "name" and "company" columns
2. Review Phase 1-4 logs for failures
3. Verify enrichment columns are populated

---

## Advanced Configuration

### Custom Email Templates

To customize the AI prompt structure, edit `ai_email_sequence_generator.py` line 236:

```python
prompt = f"""You are an expert cold email copywriter. Write Email #{email_num}...

[Customize prompt instructions here]
"""
```

### Adjust Email Length

Edit `ai_email_sequence_generator.py` line 281:

```python
6. Keep email body 100-150 words (short and punchy)
# Change to: 6. Keep email body 150-200 words for more detail
```

### Change Sequence Timing

Edit `ai_email_sequence_generator.py` line 46-77:

```python
'email_1': {'timing': 'Day 1'},  # Change to 'Day 0' for immediate send
'email_2': {'timing': 'Day 3'},  # Change to 'Day 2' for faster follow-up
...
```

---

## API Reference

### AIEmailSequenceGenerator Class

```python
from ai_email_sequence_generator import AIEmailSequenceGenerator

# Initialize
generator = AIEmailSequenceGenerator(api_key='sk-ant-...')

# Generate sequence
sequence = generator.generate_complete_sequence(
    lead_data={
        'name': 'John Smith',
        'company': 'Acme Inc',
        'title': 'VP Marketing',
        # ... (see full schema in code)
    },
    sender_info={
        'name': 'Your Name',
        'company': 'Your Company',
        'title': 'Your Title',
        'value_proposition': 'We help companies grow'
    },
    product_info={
        'name': 'Your Product',
        'category': 'software',
        'key_benefit': 'efficiency',
        'target_industries': ['SaaS', 'Marketing']
    }
)

# Returns:
{
    'email_1': {
        'subject': '...',
        'body': '...',
        'ps': '...',
        'timing': 'Day 1',
        'goal': '...',
        'name': 'Initial Outreach'
    },
    'email_2': { ... },
    ...
}
```

---

## What's Next?

Your LeadShark enrichment pipeline now includes:

1. ✅ **Multi-Link Scraping** (5 links × 3 columns)
2. ✅ **AI Intelligence** (Anthropic Claude + OpenAI GPT)
3. ✅ **API Enrichment** (5 APIs: Gender, Email, GitHub, Google, LinkedIn)
4. ✅ **Lead Scoring** (6-factor breakdown + AI boost)
5. ✅ **Email Finding** (pattern generation + verification)
6. ✅ **Cold Outreach** (personalization + components)
7. ✅ **Email Sequences** (5-email GPT-powered cadence) **NEW!**

**Total: 85 enrichment columns!** 🎉

---

## Support

For issues or questions:
1. Check `hybrid_enricher.log` for error details
2. Review troubleshooting section above
3. Test `ai_email_sequence_generator.py` standalone to isolate issues

---

**Happy Sequencing! 🦈📨**
