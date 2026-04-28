# Almarai · Daily X Monitoring Dashboard

A branded interactive dashboard that auto-generates daily reports from Brandwatch X exports. One permanent URL for the client, password-protected admin upload page for you.

## What it does

- **Public dashboard** (default URL) — KPIs, sentiment analysis, top engaged/reach posts, top authors, top cities, hourly timeline (mentions vs engagement), top hashtags, crisis report card. Fully interactive: filter by date range, sentiment, city, verification status.
- **Admin upload** (`/?mode=admin`) — drag-drop the daily Brandwatch `.xlsx` export. Password-protected. Auto-archives every upload with timestamp.
- **Crisis monitoring** — automatic risk level (Low/Medium/High) based on negative sentiment %, high-reach negative posts, and verified accounts with negative sentiment.
- **Brand-matched** — Almarai green/blue/purple, official logo, Almarai font from Google Fonts.

## File structure

```
almarai-dashboard/
├── app.py                          # Main Streamlit app
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── .gitignore
├── .streamlit/
│   ├── config.toml                 # Brand theme
│   └── secrets.toml.example        # Template for password
├── assets/
│   └── almarai_logo.svg            # Official logo
└── data/
    └── latest.xlsx                 # Current Brandwatch export (auto-replaced via admin upload)
```

## Deploy in 10 minutes (Streamlit Community Cloud — FREE)

You'll need: a GitHub account, a Streamlit Cloud account (sign up with the same GitHub).

### Step 1 — Push to GitHub

1. Create a new GitHub repo. Name it `almarai-dashboard` (or anything). Make it **public** (free Streamlit tier requires this) OR keep it private if you have Streamlit Teams.
2. Upload all the files in this folder to the repo. You can drag-drop them via the GitHub web UI:
   - Go to your new repo → "Add file" → "Upload files"
   - Drag the entire contents of this folder
   - Click "Commit changes"

### Step 2 — Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **"New app"**.
3. Select your `almarai-dashboard` repo, branch `main`, main file `app.py`.
4. Click **"Advanced settings"** → in the **Secrets** field, paste:
   ```
   ADMIN_PASSWORD = "pick-a-strong-password-here"
   ```
5. Click **"Deploy"**. Wait ~2 minutes.

You'll get a permanent URL like `https://almarai-dashboard.streamlit.app`. This is the URL you give the client.

### Step 3 — Test it

- Open your URL → you'll see the dashboard with the sample data already loaded.
- Open `your-url/?mode=admin` → enter the password you set → upload a new Brandwatch file.
- Refresh the dashboard URL — new numbers appear within ~5 minutes (or click the 🔄 Refresh button).

## Daily workflow (your team)

1. Export from Brandwatch: Bulk Mentions Download → `.xlsx`
2. Open `your-url/?mode=admin` in any browser
3. Enter password
4. Drag-drop the file
5. Done. Client sees updated dashboard.

## Notes on data persistence

⚠️ **Important:** Streamlit Community Cloud has *ephemeral* storage. If the app restarts (rare, but happens during deploys or maintenance), uploaded files reset to whatever's in the GitHub repo.

**Two options:**

### Option A — Simple (recommended for daily use)
Just re-upload via admin page after any restart. The `data/latest.xlsx` in the repo serves as the fallback. To make today's upload truly permanent, periodically commit the latest file to the repo.

### Option B — Persistent storage (zero maintenance)
Use Supabase Storage or AWS S3 for true persistence. I can wire this in — takes ~30 min more setup. Tell me if you want it; you'll need a free Supabase account.

## Customizing

- **Brand colors:** edit constants at top of `app.py` (`BRAND_GREEN`, `BRAND_BLUE`, `BRAND_PURPLE`)
- **Crisis thresholds:** edit the risk-level logic in `app.py` around line 130
- **Add competitors / share-of-voice:** add a comparison column from Brandwatch and let me know
- **Change admin password:** update Streamlit Cloud → app Settings → Secrets

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "No data file found" | Upload a file via `/?mode=admin` |
| Dashboard shows old numbers | Click 🔄 Refresh in the top right (clears 5-min cache) |
| Upload fails | Check file is `.xlsx` (not `.xls` or `.csv`) and from Brandwatch Bulk Mentions Download |
| Forgot admin password | Update in Streamlit Cloud → Settings → Secrets, then "Reboot app" |

---

Built for Almarai X monitoring. Brandwatch export columns expected: `Date, Author, Sentiment, Full Text, X Likes, X Reposts, X Replies, Reach (new), Impressions, X Followers, X Verified, City, Hashtags, Url`.
