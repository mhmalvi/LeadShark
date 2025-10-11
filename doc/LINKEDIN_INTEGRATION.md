# 🔗 LinkedIn Integration Guide

## Overview

LeadShark now includes **authenticated LinkedIn profile scraping** to enrich your leads with comprehensive LinkedIn data.

**Features:**
- ✅ Profile data extraction (name, headline, company, experience, skills)
- ✅ Company page scraping
- ✅ Activity tracking
- ✅ Authenticated session support
- ✅ Rate limiting and caching
- ✅ Automatic fallback for failed scrapes

---

## Setup Instructions

### 1. Configure LinkedIn Credentials

**Option A: Environment Variables (Recommended)**

**Windows:**
```batch
setup_linkedin_auth.bat
```

**Linux/Mac:**
```bash
source setup_linkedin_auth.sh
```

**Option B: Set Manually**

**Windows:**
```batch
set LINKEDIN_EMAIL=your-email@example.com
set LINKEDIN_PASSWORD=your-password
```

**Linux/Mac:**
```bash
export LINKEDIN_EMAIL="your-email@example.com"
export LINKEDIN_PASSWORD="your-password"
```

**Option C: Make Permanent (Optional)**

**Windows:**
1. Search for "Environment Variables" in Start Menu
2. Click "Environment Variables"
3. Under "User Variables", click "New"
4. Add:
   - Variable: `LINKEDIN_EMAIL`
   - Value: `aalvi.hm@gmail.com`
5. Repeat for `LINKEDIN_PASSWORD`

**Linux/Mac:**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export LINKEDIN_EMAIL="aalvi.hm@gmail.com"
export LINKEDIN_PASSWORD="tools895uhosszzy13w"
```

---

### 2. Verify Integration

Test the LinkedIn scraper:

```bash
python linkedin_scraper.py --profile "https://linkedin.com/in/example-profile"
```

**Expected Output:**
```json
{
  "name": "John Doe",
  "headline": "Software Engineer at TechCorp",
  "current_company": "TechCorp",
  "current_title": "Software Engineer",
  "location": "San Francisco, CA",
  "connections": "500+",
  "experience": [...],
  "skills": ["Python", "JavaScript", "AI"],
  "status": "success"
}
```

---

## How It Works

### Enrichment Pipeline

1. **Authentication**: LinkedIn scraper logs in using provided credentials
2. **Profile Scraping**: Extracts comprehensive profile data
3. **Caching**: Results cached for 24 hours to avoid rate limits
4. **Data Population**: Enriches Google Sheets with LinkedIn data

### Data Extracted

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Full name | "Jane Smith" |
| **Headline** | Professional headline | "Marketing Director at Acme Inc" |
| **Current Company** | Current employer | "Acme Inc" |
| **Current Title** | Current job title | "Marketing Director" |
| **Location** | Geographic location | "New York, NY" |
| **Connections** | Connection count | "500+" |
| **Experience** | Past positions | [{title, company, duration}...] |
| **Skills** | Top skills | ["Marketing", "SEO", "Analytics"] |

---

## LinkedIn Columns in Sheet

After enrichment, you'll see these LinkedIn-specific columns:

| Column | Content | Example |
|--------|---------|---------|
| **Enrich::LinkedIn Verified** | Verification status | "Yes" / "No" |
| **Enrich::LinkedIn Status** | Profile summary | "Marketing Director @ Acme Inc \| (500+ connections)" |
| **Enrich::LinkedIn API Source** | Data source | "LinkedIn API (authenticated scraping)" |

---

## Troubleshooting

### Issue: "LinkedIn blocked request (rate limit or bot detection)"

**Solution:**
- Wait 5-10 minutes before retrying
- Reduce number of requests per session
- Ensure credentials are correct
- LinkedIn may require CAPTCHA verification (login manually once)

### Issue: "LinkedIn authentication failed"

**Solution:**
- Verify credentials are correct
- Check if account has 2FA enabled (may require manual verification)
- Login to LinkedIn manually once to verify account is active

### Issue: "Profile not found"

**Solution:**
- Verify the LinkedIn URL is correct
- Profile may be private or deleted
- Check that URL is in format: `https://linkedin.com/in/username`

### Issue: Empty LinkedIn columns

**Causes:**
1. **No credentials set**: Set `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD`
2. **Rate limit hit**: Wait and retry
3. **Invalid URL**: Check LinkedIn URL format
4. **Private profile**: Profile privacy settings block scraping

---

## Rate Limits & Best Practices

### LinkedIn Rate Limits

- **Requests**: ~100 profile views per hour (approximate)
- **Login Attempts**: 3-5 failed attempts = temporary lock
- **Profile Visits**: LinkedIn tracks unusual activity

### Best Practices

1. **Use Caching**: Results cached for 24 hours automatically
2. **Batch Processing**: Process in small batches (10-20 profiles at a time)
3. **Add Delays**: Built-in rate limiting handles this
4. **Rotate Credentials**: Use multiple LinkedIn accounts for high-volume scraping (optional)

---

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit credentials**: The setup scripts are `.gitignore`'d
2. **Use environment variables**: Don't hardcode credentials in code
3. **Rotate passwords**: Change LinkedIn password periodically
4. **Monitor activity**: Check LinkedIn account for unusual activity

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────┐
│           Hybrid AI Enhanced Enricher               │
└─────────────────┬───────────────────────────────────┘
                  │
                  ├─► Enhanced Enrichment Engine
                  │   └─► LinkedIn Scraper
                  │       ├─► Authentication
                  │       ├─► Profile Scraping
                  │       ├─► Rate Limiting
                  │       └─► Caching
                  │
                  ├─► API Rate Limiter (cache control)
                  │
                  └─► Google Sheets Writer
```

---

## Testing

### Quick Test

```bash
# Set credentials
source setup_linkedin_auth.sh  # or setup_linkedin_auth.bat on Windows

# Test scraper
python linkedin_scraper.py --profile "https://linkedin.com/in/williamhgates"
```

### Full Enrichment Test

```bash
# Run enrichment on sample data
python test_v5_integration.py
```

---

## API Methods

### LinkedInScraper Class

```python
from linkedin_scraper import LinkedInScraper

# Initialize
scraper = LinkedInScraper(
    email="your-email@example.com",
    password="your-password"
)

# Authenticate
scraper.authenticate()

# Scrape profile
result = scraper.scrape_profile("https://linkedin.com/in/username")

# Get summary
summary = scraper.get_profile_summary("https://linkedin.com/in/username")

# Scrape company
company_data = scraper.scrape_company_page("https://linkedin.com/company/company-name")
```

---

## What's Next?

With LinkedIn integration complete, your enrichment pipeline now includes:

1. ✅ **5 Link Scraping** (website, LinkedIn, Twitter, GitHub, etc.)
2. ✅ **LinkedIn Profile Data** (headline, company, experience, skills)
3. ✅ **5 API Integrations** (Gender, Email, GitHub, Google, LinkedIn)
4. ✅ **AI Analysis** (Anthropic Claude + OpenAI GPT)
5. ✅ **Advanced Lead Scoring** (6-factor breakdown + AI boost)
6. ✅ **Enhanced Email Finding** (pattern generation + verification)
7. ✅ **Cold Outreach Components** (subject lines, hooks, CTAs)

**Total Columns: 80 enrichment fields!**

---

## Support

For issues or questions:
1. Check `hybrid_enricher.log` for error messages
2. Review this guide's troubleshooting section
3. Test with `linkedin_scraper.py` directly to isolate issues

---

**Happy Enriching! 🦈🔗**
