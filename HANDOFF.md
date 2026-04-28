# Almarai · Daily X Monitoring Dashboard — Project Handoff

> **For Claude Code:** This is a handoff from a session where we built and deployed a Streamlit dashboard for an internal-agency client (Almarai brand monitoring on X). The working code is in this same folder. This document explains everything: what was built, what bugs we hit, what's still open, and what to do next.

---

## Goal

Internal-agency tool monitoring Almarai's brand mentions on X (Twitter). Account team uploads a daily Brandwatch export; client gets a permanent URL showing the analysis. Replaces a manual daily PowerPoint deliverable.

## Hard requirements

1. **Permanent public URL** (anyone with link can view, no login)
2. **Password-protected admin upload** at `/?mode=admin` — drag-drop the daily Brandwatch `.xlsx` and dashboard updates
3. **Almarai brand identity** — official logo, brand colors `#00A650` (green) `#00AEEF` (blue) `#313092` (purple), Almarai font from Google Fonts
4. **Single-day default view** — most recent date in data — with toggles for "Last 7 days" and "Custom range"
5. **Day-over-day deltas** on every KPI (▲/▼ % vs previous period)
6. **Free hosting** — no recurring cost
7. **English UI**, but post content displays Arabic with proper RTL rendering (97% of mentions are Arabic — Almarai is a Saudi brand)

## Tech stack

- **Streamlit** for the web app (Python)
- **Plotly** for charts (donut, stacked bar, dual-axis line, horizontal bars)
- **pandas + openpyxl** for data loading
- **Streamlit Community Cloud** for hosting (free tier, public repos only)
- **GitHub** as the data store — uploaded files go into `data/latest.xlsx` in the repo

## Brandwatch data structure

Export = `.xlsx` from Brandwatch "Bulk Mentions Download". File has 6 metadata rows then the header row, so always use `pd.read_excel(file, skiprows=6)`.

Has 197 columns. Used by the dashboard:

| Column | Notes |
|---|---|
| `Date` | datetime |
| `Author` | X handle without @ |
| `Sentiment` | already classified by Brandwatch: `positive` / `neutral` / `negative` (don't re-analyze — Brandwatch's Arabic sentiment beats open-source models for Khaleeji dialect) |
| `Full Text` | Post text (Arabic, needs RTL display) |
| `Url` | Direct X link |
| `X Likes`, `X Reposts`, `X Replies` | Engagement components — sum into `Engagement` column |
| `X Followers`, `X Verified` | Author metrics |
| `Reach (new)`, `Impressions` | Reach metrics |
| `City`, `Country` | Geo (sparse — only ~20% have city) |
| `Hashtags` | Comma-separated string |
| `Almarai Prices Crisis - Almarai Prices Crisis` | Custom Brandwatch theme tag |

⚠️ `Latitude` / `Longitude` columns exist but are **all zeros** — useless. If a map is needed, embed a city → coordinates lookup dictionary in code.

## Dashboard structure (top to bottom)

1. **Time scope picker** — radio: Single day / Last 7 days / Custom range · day selector · sentiment multiselect · Refresh button
2. **Brand header** — Almarai gradient banner with logo, period label, risk pill (LOW/MEDIUM/HIGH)
3. **6 KPI cards** with icons + DoD deltas: 💬 Mentions, 📡 Reach, 👁 Impressions, ❤ Engagement, 👥 Authors, ✓ Verified
4. **Crisis bar with auto-narrative** — amber/red/green box, headline + 3-5 sentence template-generated paragraph
5. **Sentiment donut + Daily volume by sentiment** (stacked bar)
6. **Top 3 by engagement + Top 3 by reach** — post cards. **Reach list deduped against engagement list**
7. **Top 2 positive + Top 2 negative** — by engagement, also deduped against above
8. **Top authors table** (sortable by reach or engagement) + **Top cities horizontal bar chart**
9. **Hourly timeline** — full width, mentions bars + engagement line on dual axis
10. **Conversation themes panel** + **Alert rules panel**
11. **Top hashtags** + **Crisis report card**
12. **Export** — CSV of filtered data + TXT brief

## Risk level (in header)

- **HIGH** if neg% > 35% OR high-reach-negative > 5
- **MEDIUM** if neg% > 20% OR high-reach-neg > 2 OR verified-neg > 5
- **LOW** otherwise

## Admin upload

`ADMIN_PASSWORD` is set in Streamlit Cloud → app Settings → Secrets. Default fallback is `"almarai2026"`.

---

# Bugs encountered & solutions (all fixed in current app.py)

### Bug 1 — KPI numbers rendered nearly invisible
**Root cause:** Streamlit injects internal CSS classes that override custom CSS rules due to specificity.
**Fix:** Use **inline styles** directly in the HTML — inline always beats class-level specificity. Set `color: #0B0B0B` and `font-weight: 800`.

### Bug 2 — Streamlit Cloud build hangs at "Processing dependencies"
**Root cause:** Pinned `pandas==2.2.3` etc. don't have pre-built wheels for Python 3.14 (Streamlit Cloud's current default).
**Fix:** Unpin everything in `requirements.txt`. Lets pip pick whatever versions have wheels for the running Python.

### Bug 3 — KPI HTML displayed as raw text instead of rendering
**Root cause:** When you write multi-line HTML inside a Python triple-quoted f-string with leading indentation, Streamlit's markdown parser interprets any line starting with 4+ spaces as a markdown code block, so it renders the HTML as text.
**Fix:** `kpi_card()` and `render_post()` return HTML as a single concatenated string with **zero leading whitespace** using parentheses concatenation instead of triple-quoted f-strings.

⚠️ **Anywhere you write multi-line HTML in a triple-quoted Python string with indentation will hit this same bug.** Always concatenate with no leading whitespace, or use `textwrap.dedent()`.

---

# Persistence limitation (architectural, not a bug)

Streamlit Community Cloud has **ephemeral filesystem**. Files written to `data/latest.xlsx` get wiped on container restart.

**Recommended fix:** Implement GitHub-commit-on-upload. After admin uploads a file, also commit it to the repo via PyGithub or the GitHub REST API. Needs a GitHub Personal Access Token with `contents:write` scope, stored in Streamlit secrets as `GH_TOKEN`. Then in the admin handler, after writing the file locally, also commit it to the repo. ~30 min to add.

---

# Suggested next steps in priority order

1. **Implement GitHub-commit-on-upload** for true persistence (PyGithub + PAT in secrets). Solves the ephemeral-storage problem.
2. **Competitor share-of-voice** — track Nadec, Al-Safi, Juhayna, Almarai together. Needs separate Brandwatch queries combined into a single export with a brand-name column.
3. **Scheduled daily email** of the brief at 9am to a recipient list (SendGrid free tier or Resend). Could be a separate cron-triggered Python script via GitHub Actions.
4. **PDF export with charts** (currently TXT only). Either render dashboard via headless Chrome (`playwright`), or build PDF from scratch with `reportlab` or `weasyprint`.
5. **Sentiment correction logging** — analyst clicks 👍/👎 on a post's sentiment classification, logs corrections to a CSV for monthly Brandwatch review. Important because Brandwatch misclassified ~3 of 7 verified-negative posts in the test data (positive stock recommendations flagged as negative due to words like "decline" referring to general market context).
6. **Real Saudi choropleth map** if region-level data becomes available — would need a Saudi GeoJSON with 13 regions. Currently using horizontal bar chart for cities.
7. **Confidence/quality indicator on Brandwatch sentiment** — surface low-confidence sentiments (very short posts, posts mentioning multiple brands, posts with stock-market keywords) so the analyst knows to review them.

---

# How to run locally

```bash
cd almarai-dashboard
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501. Sample data in `data/latest.xlsx` (300 mentions, Mar 31 – Apr 26, 2026).

# How to test the admin flow locally

Visit http://localhost:8501/?mode=admin and use password `almarai2026` (the fallback). Upload any Brandwatch `.xlsx` to test the replacement flow.
