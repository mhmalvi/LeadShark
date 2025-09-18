TITLE: Google Sheets Prospect Enrichment — Smart Column Detection & Creation (Python)

ROLE:
You are a senior Python engineer. Build a production-grade CLI that:
1) reads a Google Sheet,
2) iterates rows,
3) discovers link(s) in designated or auto-discovered input columns,
4) scrapes/collects data only where ToS/robots allow (prefer official APIs),
5) writes compact results back to the SAME ROW:
   - one single-cell summary per link,
   - one single-cell COMBINED_REPORT (merged insights),
   - one single-cell LEAD_SCORE (0–100) + short rationale,
   - STATUS + LAST_RUN.
Be **idempotent** (re-runs overwrite the same cells). Produce complete, runnable code + README.

NON-NEGOTIABLES (Compliance & Safety):
- Respect robots.txt and Terms of Service. Do NOT scrape forbidden sites (e.g., LinkedIn). If forbidden: SKIP and record “Skipped (ToS/robots)”.
- Prefer official APIs when tokens exist (Twitter/X, YouTube).
- Use `requests+BeautifulSoup` for simple pages; use Playwright headless ONLY if needed.
- Rate limit + jitter; per-domain concurrency = 1; timeouts; retries on 429/5xx.
- Keep cells compact: per-link summary ≤ MAX_CELL_CHARS; COMBINED_REPORT ≤ MAX_COMBINED_CHARS.
- Deterministic scoring for the same inputs.

CONFIG (.env):
GOOGLE_AUTH_MODE=oauth|service_account
GOOGLE_SHEET_ID=...
WORKSHEET_NAME=Sheet1
INPUT_COLUMNS=auto                 # "auto" = discover URL columns (see below)
MAX_LINK_SUMMARIES=5               # number of per-link summary cells to create/maintain
HEADER_NAMESPACE=ENRICH_           # prefix for managed headers (namespaced)
PER_DOMAIN_RPS=0.2
TIMEOUT_SECONDS=20
MAX_CELL_CHARS=4000
MAX_COMBINED_CHARS=5000
USER_AGENT="ProspectResearchBot/1.0 (+contact@example.com)"
DRY_RUN=false
# Optional API keys (prefer APIs over scraping if provided)
TWITTER_BEARER=
YOUTUBE_API_KEY=

SCHEMA (managed headers):
- Per-link summaries: ENRICH_LINK_1_SUMMARY ... ENRICH_LINK_N_SUMMARY (N = MAX_LINK_SUMMARIES)
- COMBINED_REPORT:  ENRICH_COMBINED_REPORT
- LEAD_SCORE:       ENRICH_LEAD_SCORE
- SCORE_NOTES:      ENRICH_LEAD_SCORE_NOTES
- STATUS:           ENRICH_STATUS           # OK | SKIPPED_TOS | NO_LINKS | ERROR
- LAST_RUN:         ENRICH_LAST_RUN         # ISO8601
- (Optional) SCHEMA_VERSION cell in row 1 to support future migrations: ENRICH_SCHEMA_VERSION = 1

SMART COLUMN DETECTION & CREATION:
- Never assume a fixed column like AX.
- On startup, scan the header row:
  1) **Detect existing managed block** by finding headers with the `HEADER_NAMESPACE` prefix.
     - If found, **reuse in place** (respect their current order).
     - If some managed headers are missing (e.g., you lowered/raised MAX_LINK_SUMMARIES), **create the missing ones** contiguously to the right of the managed block so the block stays compact.
  2) If no managed headers exist yet:
     - Identify the **last used column** in the sheet.
     - **Create a fresh managed block** immediately to the right with the exact headers listed in SCHEMA.
- Idempotency guarantee:
  - On re-runs, the same managed headers are recognized and reused; values for each processed row are overwritten, not appended.
  - If the number of links in a row exceeds MAX_LINK_SUMMARIES, summarize the extras within COMBINED_REPORT and write “(+N more)”.

INPUT COLUMN DISCOVERY (when INPUT_COLUMNS=auto):
- Consider a column a “URL candidate” if:
  - header contains any of: link, url, website, site, twitter, x.com, youtube, github, social, profile, portfolio, company; OR
  - any cell in that column matches a URL regex.
- Extract URLs from those columns for each row; split on comma, space, pipe, newline; normalize and de-duplicate by (scheme, host, path).

ROW WORKFLOW (strict order):
1) Read row; extract + normalize all URLs from discovered columns; de-dup by host+path.
2) Classify each URL and choose HANDLER:
   - WEBSITE (generic): title, meta description, H1/H2, about/company hints, contact/pricing cues, 1–3 recent blog/news headlines.
   - X/TWITTER (if TWITTER_BEARER): profile bio + up to 3 recent posts (text only). Else → SKIP (ToS).
   - YOUTUBE (if YOUTUBE_API_KEY): channel title/description + 3 latest video titles.
   - GITHUB: repo/org summary (stars, topics, README highlights).
   - NEWS ARTICLE: title, publish date, 2–3 takeaways.
   - FORBIDDEN (LinkedIn, etc.): mark as “Skipped (ToS/robots)”.
3) Write **per-link summaries** into ENRICH_LINK_1..N in the order encountered (up to MAX_LINK_SUMMARIES).
   - Format (Markdown mini-brief; ≤ MAX_CELL_CHARS):
     ```
     **Source:** <domain/platform>
     **URL:** <normalized>
     **Key Points:** • 3–6 bullets (tight, non-redundant)
     **Signals for Outreach:** • 2–4 bullets (pain/intent/ICP clues)
     **Last Checked:** <ISO8601>
     ```
4) Build **ENRICH_COMBINED_REPORT** (≤ MAX_COMBINED_CHARS):
   - “Profile Snapshot” (2–4 lines)
   - “Pain / Opportunity Signals” (3–6 bullets)
   - “Suggested Angle & CTA” (2–3 bullets)
   - “Data Sources” (domain names only; note “(+N more)” if applicable)
   - If some links were skipped: mention counts only (no details).
5) Compute **ENRICH_LEAD_SCORE (0–100)** with **ENRICH_LEAD_SCORE_NOTES** (≤ 5 lines):
   - Deterministic weighted rubric (sum to 100):
     • Relevance to our services (30)
     • Purchase intent (25) — pricing pages, “contact sales,” hiring roles we solve, recent launches
     • Authority/Size (20) — follower/traffic proxies, org signals
     • Recency (15) — posts/updates/news within 90 days
     • Data quality (10) — clarity/consistency across sources
   - NOTES list which factors fired: “Pricing page found; Hiring RevOps; 2 posts last 30d,” etc.
6) Write **ENRICH_STATUS** (OK | SKIPPED_TOS | NO_LINKS | ERROR) and **ENRICH_LAST_RUN** (ISO8601).
7) Idempotent write: re-runs overwrite these managed cells only; original columns remain untouched.

SCRAPING RULES & RESILIENCE:
- Check robots.txt for WEBSITE handler; if disallowed, mark “Skipped (robots)”.
- Retries: exponential backoff (max 2) for 429/5xx; per-domain concurrency = 1.
- Timeouts per request; skip gracefully with a terse reason inside that link’s summary.
- Use simple on-disk cache (hash(URL)) with 24h TTL; `--no-cache` to bypass.
- DRY_RUN=true prints a neat preview table showing the exact values per managed header without writing.

CLI:
--sheet-id ... --worksheet ...
--rows "2-500" (optional)
--dry-run
--only-new                 # process rows with empty ENRICH_COMBINED_REPORT only
--force-domains "twitter.com,youtube.com"  # restrict handlers if needed
--max-link-summaries 5     # can override MAX_LINK_SUMMARIES at runtime (will expand headers if needed)

DELIVERABLES:
- /app.py (entrypoint)
- /handlers/{website.py,twitter.py,youtube.py,github.py,news.py}
- /utils/{sheets.py,io.py,normalize.py,robots.py,summarize.py,scoring.py,cache.py,logging.py}
- requirements.txt (gspread OR pygsheets + google-auth libs, requests, beautifulsoup4, python-dotenv, playwright, tldextract)
- README.md: setup (OAuth vs service account), sample .env, usage, troubleshooting (429s, robots, missing APIs), and ToS notes.
- Tests:
  - URL extraction + de-dup (multi-URL cells)
  - **Smart column management**: detect existing managed block, create if absent, expand when MAX_LINK_SUMMARIES increases
  - Summary length trimming
  - Scoring determinism
  - Integration with a mock sheet:
    A) website + twitter + youtube
    B) website only
    C) linkedin (→ “Skipped (ToS)”) + website → still produces COMBINED_REPORT

DEFINITION OF DONE:
- First run creates a compact managed header block (with HEADER_NAMESPACE) to the right of existing data.
- Subsequent runs reuse that block; no header duplication.
- Each processed row ends with up to N per-link summaries, a concise COMBINED_REPORT, a numeric LEAD_SCORE + NOTES, STATUS, and LAST_RUN.
- Forbidden domains are never scraped; they’re clearly marked as skipped and excluded from the score.
