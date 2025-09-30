# 🦈 LeadShark Enhanced Data Collection Strategy

## Executive Summary

LeadShark scrapes multiple links per row in a Google Sheet and stores structured results in dedicated columns with:
- **Individual link columns** with clean summaries + JSON data
- **Combined context** paragraph summarizing all findings
- **Lead scoring** with 0-100 numeric prioritization
- **Professional formatting** for human-friendly analysis

---

## 🎯 Core Workflow

### 1. Input Data
Each row contains:
- Contact/company name
- Multiple links (LinkedIn, website, social media, etc.)

### 2. Scraping Process
For **every link** in each row:
1. Visit the page
2. Extract relevant structured data
3. Format cleanly (no raw HTML/messy text)
4. Store in dedicated columns

### 3. Output Structure
**Per row, you get:**
- ✅ One column pair per link (Summary + JSON)
- ✅ Combined context summary
- ✅ Lead score (0-100)
- ✅ Lead tags (Hot/Warm/Cold)
- ✅ Timestamp

---

## 📊 Example Output

### Before Scraping (Raw Input)
| Name | Email | LinkedIn | Website | Twitter |
|------|-------|----------|---------|---------|
| John Doe | john@startupx.com | linkedin.com/in/johndoe | johndoe.com | twitter.com/johndoe |

### After Scraping + API Enrichment (Full Output)
| Name | LinkedIn Data | Website Data | Twitter Data | Complete Context | Lead Score | Lead Tags | Gender | Gender Conf | Email Status | GitHub Repos | Company Industry |
|------|---------------|--------------|--------------|------------------|------------|-----------|--------|-------------|--------------|--------------|------------------|
| John Doe | **Link:** linkedin.com/in/johndoe<br>**Headline:** CEO at StartupX<br>**Location:** New York<br>**Experience:** 10+ yrs in SaaS | **Link:** johndoe.com<br>**About:** Tech consulting firm<br>**Services:** Cloud solutions, AI tools<br>**Contact:** info@johndoe.com | **Link:** twitter.com/johndoe<br>**Bio:** Tech geek. SaaS founder.<br>**Followers:** 12k<br>**Engagement:** High | John is CEO of StartupX, based in New York, with 10+ years in SaaS. Runs consulting firm offering AI & cloud services. Active on Twitter with 12k followers. Email verified (Genderize.io: Male 99%, EVA: Deliverable). Active GitHub profile with 45 repos. | 85 | Hot 🔥 | Male | 99% | Valid, Deliverable | 45 | SaaS, Cloud, AI |

---

## 🔍 Scraping Fields by Link Type

### LinkedIn Profile
**Priority fields:**
- `profile_url`
- `full_name`
- `headline` / `current_title`
- `company` (current employer)
- `location` (city, country)
- `summary` / `about` (first 300–600 chars)
- `top_experiences` (array: title, company, dates)
- `education` (top entries)
- `skills` (top 10)
- `endorsements_count`
- `profile_image_url`
- `contact_info` (email/phone if visible)

### Company Website (homepage/about/services)
**Priority fields:**
- `url`
- `company_name`
- `tagline` / one-liner
- `description` (2–3 sentence summary)
- `services_products` (list)
- `key_people` (names/roles)
- `address` / `locations`
- `email_contacts` (list)
- `phone_numbers`
- `social_links` (list)
- `pricing_or_plans`
- `tech_stack` (if detectable)

### Twitter / X
**Priority fields:**
- `url`
- `handle`
- `name`
- `bio`
- `location`
- `followers_count`
- `following_count`
- `recent_tweets` (1–3 sample)
- `engagement_indicator` (avg likes/retweets of recent 5)
- `verified` (bool)

### GitHub
**Priority fields:**
- `url`
- `username`
- `display_name`
- `bio`
- `top_repos` (name, stars, description)
- `followers_count`
- `languages_used` (top languages)
- `organizations`

### Crunchbase / AngelList / Startup Profiles
**Priority fields:**
- `url`
- `company_name`
- `description`
- `founded_year`
- `headquarters`
- `funding_stage` / `total_funding`
- `key_team` (founders, CEO)
- `investors` (list)
- `latest_news` / events

### YouTube Channel
**Priority fields:**
- `url`
- `channel_name`
- `subscribers_count`
- `recent_video_titles` (3)
- `channel_description`
- `engagement_sample` (avg views/likes of last 3)

### Instagram / TikTok
**Priority fields:**
- `url`
- `handle`
- `bio`
- `followers_count`
- `engagement_sample` (recent posts avg likes/comments)
- `top_hashtags`

### Generic Web Page / Blog Post
**Priority fields:**
- `url`
- `page_title`
- `meta_description`
- `author`
- `publish_date`
- `excerpt` (first 150–300 chars)
- `contact_info_found` (emails/phones)

### Job Posting (career page / LinkedIn jobs)
**Priority fields:**
- `url`
- `job_title`
- `company`
- `location`
- `employment_type`
- `posted_date`
- `job_description_summary` (3–5 bullet points)
- `seniority_level`
- `apply_link` / contact

### Contact Page
**Priority fields:**
- `url`
- `emails_found` (list)
- `phones_found` (list)
- `contact_form` (bool)

---

## 📋 Google Sheets Column Structure

### Recommended Column Headers (for 5 links per row)

```
[Name]
[Link 1] [Link 1 — Short Summary] [Link 1 — JSON]
[Link 2] [Link 2 — Short Summary] [Link 2 — JSON]
[Link 3] [Link 3 — Short Summary] [Link 3 — JSON]
[Link 4] [Link 4 — Short Summary] [Link 4 — JSON]
[Link 5] [Link 5 — Short Summary] [Link 5 — JSON]
[Complete Context]
[Lead Score]
[Lead Tags]
[Last Scraped]

--- API Enrichment Columns ---
[Gender] [Gender Confidence] [Gender API Source]
[Email Status] [Email Deliverability] [Email API Source]
[GitHub Profile] [GitHub Repos Count] [GitHub Activity] [GitHub API Source]
[Company Info] [Company Industry] [Google Search API Source]
[LinkedIn Verified] [LinkedIn Status] [LinkedIn API Source]
```

### Cell Content Examples

**Link 1 — Short Summary** (human-readable):
```
LinkedIn: linkedin.com/in/johndoe
Title: CEO at StartupX
Location: New York, USA
Experience: 10 yrs SaaS, ex-Stripe
Top skills: Product Strategy, Growth, APIs
```

**Link 1 — JSON** (machine-readable, single-line):
```json
{"source":"linkedin","url":"...","name":"John Doe","title":"CEO","location":"New York, USA","skills":["Product Strategy","Growth"],"followers":1200}
```

**Complete Context** (synthesized paragraph):
```
John Doe is CEO of StartupX (NY) with 10+ years in SaaS. Company offers AI-based cloud integrations (johndoe.com). John is active on Twitter (12k followers) and lists contact info on the website (info@johndoe.com). Recent press shows a Series A raise — high-priority lead.
```

**API Enrichment Examples:**

**Gender Columns:**
```
Gender: Male
Gender Confidence: 99%
Gender API Source: Genderize.io
```

**Email Verification Columns:**
```
Email Status: Valid
Email Deliverability: Deliverable
Email API Source: EVA API
```

**GitHub Enrichment Columns:**
```
GitHub Profile: github.com/johndoe
GitHub Repos Count: 45
GitHub Activity: High (commits in last 30 days)
GitHub API Source: GitHub REST API v3
```

**Company Intelligence Columns:**
```
Company Info: AI-based cloud integration platform
Company Industry: SaaS, Cloud Computing, AI
Google Search API Source: Google Custom Search API
```

**LinkedIn Verification Columns:**
```
LinkedIn Verified: Yes
LinkedIn Status: Profile accessible, premium account
LinkedIn API Source: Web scraping (platform-optimized)
```

---

## 🔌 External API Enrichment Sources

### 1. Genderize.io API
**Purpose:** Gender detection from first names
**Endpoint:** `https://api.genderize.io/`
**Free Tier:** 500 requests/month
**Accuracy:** 99%
**Output Columns:** `[Gender]`, `[Gender Confidence]`, `[Gender API Source]`
**Data Returned:**
```json
{
  "name": "John",
  "gender": "male",
  "probability": 0.99,
  "count": 234567
}
```

### 2. EVA (Email Verification API)
**Purpose:** Email validation and deliverability checks
**Endpoint:** `https://api.eva.pingutil.com/email`
**Free Tier:** Unlimited (basic validation)
**Output Columns:** `[Email Status]`, `[Email Deliverability]`, `[Email API Source]`
**Data Returned:**
```json
{
  "status": "valid",
  "deliverable": true,
  "smtp_check": true,
  "disposable": false
}
```

### 3. GitHub REST API v3
**Purpose:** Developer profile and repository intelligence
**Endpoint:** `https://api.github.com/`
**Rate Limit:** 60 requests/hour (unauthenticated), 5000/hour (authenticated)
**Output Columns:** `[GitHub Profile]`, `[GitHub Repos Count]`, `[GitHub Activity]`, `[GitHub API Source]`
**Data Returned:**
```json
{
  "login": "johndoe",
  "public_repos": 45,
  "followers": 234,
  "bio": "Senior engineer at StartupX",
  "location": "New York",
  "organizations": ["startupx", "opensource-community"]
}
```

### 4. Google Custom Search API
**Purpose:** Company information and web intelligence gathering
**Endpoint:** `https://www.googleapis.com/customsearch/v1`
**Free Tier:** 100 queries/day
**Output Columns:** `[Company Info]`, `[Company Industry]`, `[Google Search API Source]`
**Data Returned:**
```json
{
  "items": [
    {
      "title": "StartupX - AI Cloud Solutions",
      "snippet": "Leading provider of AI-based cloud integration...",
      "link": "https://startupx.com"
    }
  ]
}
```

### 5. LinkedIn Web Scraping (Platform-Optimized)
**Purpose:** Professional profile and company verification
**Method:** HTTP requests with platform-specific headers and rate limiting
**Rate Limit:** 1 request/3 seconds (respectful scraping)
**Output Columns:** `[LinkedIn Verified]`, `[LinkedIn Status]`, `[LinkedIn API Source]`
**Data Extracted:**
- Profile accessibility
- Current title and company
- Connection count (when visible)
- Premium account status
- Profile completeness

### API Usage Best Practices

**Rate Limiting:**
- ✅ Genderize.io: 500/month → Batch by unique first names
- ✅ EVA: Unlimited → No batching needed
- ✅ GitHub: 60/hour → Use authenticated token for 5000/hour
- ✅ Google Search: 100/day → Cache results, prioritize high-value queries
- ✅ LinkedIn Scraping: 1/3s → Respectful delays, use request pools

**Error Handling:**
- API quota exceeded → Log to `[API Source]` column with "QUOTA_EXCEEDED"
- Network timeout → Retry 3x with exponential backoff
- Invalid response → Mark as "API_ERROR" with timestamp
- Authentication failure → Alert user to check API keys

**Cost Optimization:**
- Deduplicate API calls (e.g., same name/email across multiple rows)
- Cache results for 24 hours in local storage
- Prioritize free tiers and batch operations
- Use fallback strategies when APIs unavailable

---

## 🎯 Lead Scoring System

### Scoring Rubric (Total: 100 points)

| Factor | Weight | Description |
|--------|--------|-------------|
| **Role / Decision Power** | 30 | Executive / Founder / C-level |
| **Company Fit** | 25 | Industry + size match |
| **Engagement / Visibility** | 15 | Followers, activity, engagement |
| **Contactability** | 15 | Public email / phone available |
| **Tech / Product Fit** | 10 | Uses relevant tech or services |
| **Recency / Signal Strength** | 5 | Recent news, job posting, activity |

### Example Calculation

```
Role: Founder → 1.0 × 30 = 30
Company fit: Good match → 0.8 × 25 = 20
Engagement: Moderate → 0.6 × 15 = 9
Contactability: Email present → 1.0 × 15 = 15
Tech fit: Low → 0.2 × 10 = 2
Recent signal: Press mention → 1.0 × 5 = 5
─────────────────────────────────────
Total = 81 / 100 → Hot Lead 🔥
```

### Score Thresholds

| Score | Tag | Action |
|-------|-----|--------|
| 80–100 | 🔥 **Hot** | Priority outreach |
| 60–79 | 🟡 **Warm** | Nurture campaign |
| 30–59 | 🔵 **Cold** | Monitor/drip campaign |
| 0–29 | ⚫ **Discard** | Unqualified |

---

## 🤖 Machine-Friendly JSON Schema

**Standard schema for all link types:**

```json
{
  "source": "linkedin|website|twitter|github|crunchbase|youtube|instagram|generic|job",
  "url": "https://...",
  "extracted": {
    "title": null,
    "name": null,
    "company": null,
    "location": null,
    "description": null,
    "key_fields": {},
    "contacts": {
      "emails": [],
      "phones": []
    },
    "metrics": {
      "followers": null,
      "stars": null,
      "subscribers": null
    },
    "top_items": [],
    "raw_text_snippet": null
  },
  "confidence": 0.0,
  "scrape_timestamp": "2025-09-30T12:00:00Z"
}
```

**Note:** Use `extracted.key_fields` for site-specific data (e.g., `{"skills":["x","y"], "funding_total":"$5M"}`).

---

## ⚙️ Agent Action Plan (Implementation)

### For each row in sheet:

1. **Read all raw link columns**

2. **For each link:**
   - Classify link type (by domain/path heuristics)
   - Visit page, fetch HTML (respect robots.txt & rate-limit)
   - Extract fields per link type (see tables above)
   - Use micro-parsers: meta tags, JSON-LD, schema.org, OpenGraph
   - Normalize into JSON schema
   - Build Short Summary string + JSON compact string
   - Update corresponding columns in same row

3. **After all links processed:**
   - Generate Complete Context paragraph (merge top fields)
   - Compute Lead Score using scoring function
   - Write Lead Tags and Last Scraped timestamp
   - Save/commit row updates in single batch

---

## 🛡️ Guardrails & Best Practices

### Rate-Limiting & Politeness
- ✅ Limit to **1 request/sec per domain**
- ✅ Respect `robots.txt`
- ✅ Rotate user-agent
- ✅ Backoff on HTTP 429
- ⚠️ Don't hammer LinkedIn — use APIs or commercial providers

### Auth-Required Pages
- If login required, mark `access: restricted` and skip
- Attempt API-based fallback if available

### Error Handling
- Write `ERROR: <short reason>` in Short Summary
- Set JSON to `null` on scrape failure

### Privacy & Compliance
- ✅ Only scrape **publicly available** contact info
- ✅ Respect platform terms of service
- ⚠️ Do not scrape non-public PII

### Data Management
- **Deduplication:** Canonicalize URLs to avoid duplicate links
- **Storage:** Keep JSON column for machine parsing, hide for humans
- **Versioning:** Add Last Scraped ISO timestamp
- **Trend analysis:** Optionally keep `Prev Lead Score`

---

## 📐 Formatting Tips

### Human-Readable Columns
- Use **bolded labels** for quick scanning
- Clear **Label:** prefix format
- 2–5 lines per summary
- Present tense, third person

### JSON Columns
- Single-line compact JSON
- Parse-friendly for tools (Apps Script, Zapier, Make)
- Hide/lock column for human viewers

### Complete Context
- 3–6 sentences
- Grammatically correct
- Third-person narrative
- Professional yet friendly tone

---

## 🎉 End Goal

**Professional, organized, human-friendly Google Sheet with:**
- ✅ One column pair per link (Summary + JSON)
- ✅ Combined context summary
- ✅ Lead score with tags
- ✅ Timestamp for tracking
- ✅ Clean, scannable formatting
- ✅ Machine-parseable JSON backup data

**Result:** A lead enrichment system that serves both humans (easy reading) and machines (automation-ready).