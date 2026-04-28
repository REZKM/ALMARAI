"""
Almarai · Daily X Monitoring Dashboard  (v3)
============================================
v1 layout fully preserved + v2 additions (day picker, narrative, themes, alerts,
day-over-day deltas, top pos/neg posts, icons). Saudi map reverted to bar chart.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path
import base64
import os
import re

# ---------- CONFIG ----------
st.set_page_config(
    page_title="Almarai · Daily X Monitoring",
    page_icon="🥛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BRAND_GREEN  = "#00A650"
BRAND_BLUE   = "#00AEEF"
BRAND_PURPLE = "#313092"
SENT_POS = "#1D9E75"
SENT_NEG = "#E24B4A"
SENT_NEU = "#888780"

DATA_FILE = Path("data/latest.xlsx")
LOGO_FILE = Path("assets/almarai_logo.svg")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", os.getenv("ADMIN_PASSWORD", "almarai2026"))


# ---------- THEME KEYWORDS ----------
THEME_KEYWORDS = {
    'Price complaint':   ['غالي', 'ارتفاع', 'رفع السعر', 'اسعار', 'الأسعار', 'price', 'expensive', 'increase'],
    'Boycott narrative': ['مقاطعة', 'قاطع', 'قاطعوا', 'boycott'],
    'Product quality':   ['جوده', 'جودة', 'سيء', 'سيئ', 'طعم', 'بودره', 'بودرة', 'quality', 'taste'],
    'Health concerns':   ['دهون', 'سكر', 'سكريات', 'صحه', 'صحة', 'fat', 'sugar', 'health'],
    'Weight reduction':  ['وزن', 'كميه', 'كمية', 'حجم', 'weight', 'size'],
    'Stock / financial': ['سهم', 'اسهم', 'الأسهم', 'تداول', 'محفظه', 'محفظة', 'stock', 'shares'],
    'Positive product':  ['طيب', 'لذيذ', 'احب', 'أحب', 'افضل', 'أفضل', 'delicious', 'love', 'best'],
}


# ---------- STYLING ----------
# NOTE: KPI values use INLINE styles (not CSS classes) to bypass Streamlit
# specificity issues that were rendering the numbers in low-contrast color.
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Almarai', sans-serif !important; }}
.stApp, .main, [data-testid="stAppViewContainer"] {{ background: #FFFFFF !important; }}

.brand-hdr {{
    background: linear-gradient(90deg, {BRAND_GREEN} 0%, {BRAND_BLUE} 100%);
    padding: 20px 28px; border-radius: 12px; margin-bottom: 18px;
    display: flex; align-items: center; justify-content: space-between; color: white;
}}
.brand-title {{ font-size: 22px; font-weight: 700; margin: 0; color: white !important; }}
.brand-sub {{ font-size: 13px; opacity: 0.9; margin: 0; color: white !important; }}
.risk-pill {{ background: rgba(255,255,255,0.22); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; color: white !important; }}

.crisis-bar {{
    background: #FFF3E0; border-left: 4px solid #BA7517;
    padding: 14px 18px; border-radius: 8px; margin: 12px 0 18px;
}}
.crisis-bar.high {{ background: #FCEBEB; border-left-color: #A32D2D; }}
.crisis-bar.low {{ background: #EAF3DE; border-left-color: #3B6D11; }}
.crisis-headline {{ font-weight: 700; margin-bottom: 6px; font-size: 13px; color: #1a1a1a !important; }}
.crisis-narrative {{ font-size: 13px; line-height: 1.7; color: #1a1a1a !important; }}
.crisis-narrative b {{ color: #000 !important; font-weight: 700; }}

.post-card {{
    background: white; padding: 12px; border-radius: 8px;
    border: 1px solid #EEE; border-left: 3px solid #888780;
    margin-bottom: 8px; font-size: 13px;
}}
.post-card.pos {{ border-left-color: {SENT_POS}; }}
.post-card.neg {{ border-left-color: {SENT_NEG}; }}
.post-card.neu {{ border-left-color: {SENT_NEU}; }}
.post-author {{ color: {BRAND_BLUE} !important; font-weight: 700; font-size: 13px; }}
.post-meta {{ color: #999 !important; font-size: 11px; }}
.post-text {{ direction: rtl; text-align: right; font-size: 13px; line-height: 1.7; color: #222 !important; margin: 6px 0; max-height: 80px; overflow: hidden; }}
.post-stats {{ font-size: 11px; color: #666 !important; display: flex; gap: 14px; margin-top: 6px; flex-wrap: wrap; align-items: center; }}
.post-stats b {{ color: #1a1a1a !important; font-weight: 700; }}
.sent-tag {{ padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 600; text-transform: uppercase; }}
.s-pos {{ background: #EAF3DE !important; color: #27500A !important; }}
.s-neg {{ background: #FCEBEB !important; color: #791F1F !important; }}
.s-neu {{ background: #F1EFE8 !important; color: #444441 !important; }}

.sec-h {{ font-size: 14px; font-weight: 700; color: #333 !important; margin: 18px 0 10px; padding-bottom: 6px; border-bottom: 1px solid #EEE; }}

.alert-row {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #F0F0F0; font-size: 13px; color: #1a1a1a; }}
.alert-row:last-child {{ border-bottom: none; }}
.alert-status {{ font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 10px; }}
.alert-status.fired {{ background: #FCEBEB !important; color: #791F1F !important; }}
.alert-status.ok {{ background: #EAF3DE !important; color: #27500A !important; }}

.crisis-card {{ background: white; padding: 14px; border-radius: 8px; border: 1px solid #EEE; }}
.crisis-card-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #F0F0F0; font-size: 13px; color: #1a1a1a; }}
.crisis-card-row:last-child {{ border-bottom: none; }}

#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1300px; }}
</style>
""", unsafe_allow_html=True)


# ---------- HELPERS ----------
@st.cache_data(ttl=300)
def load_data(filepath):
    df = pd.read_excel(filepath, skiprows=6)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    for c in ['X Likes','X Reposts','X Replies','Reach (new)','Impressions','X Followers']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
    df['Engagement'] = df['X Likes'] + df['X Reposts'] + df['X Replies']
    df['Sentiment'] = df['Sentiment'].fillna('neutral').str.lower()
    df['Hour'] = df['Date'].dt.hour
    df['DateOnly'] = df['Date'].dt.date
    return df


def get_logo_b64():
    if LOGO_FILE.exists():
        with open(LOGO_FILE, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ""


def fmt_int(n):
    n = int(n)
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 10_000:    return f"{n/1_000:.0f}K"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return f"{n:,}"


def delta_str(curr, prev):
    if prev == 0:
        return ("New", "#999") if curr > 0 else ("—", "#999")
    pct = (curr - prev) / prev * 100
    if abs(pct) < 5:
        return (f"≈ {pct:+.0f}%", "#999")
    arrow = "▲" if pct > 0 else "▼"
    color = SENT_POS if pct > 0 else SENT_NEG
    return (f"{arrow} {abs(pct):.0f}% vs prev", color)


def kpi_card(icon, label, value, delta_text, delta_color, top_color):
    """Returns inline-styled HTML for a KPI card. Uses inline styles to bypass
    Streamlit CSS specificity issues that caused values to render light/invisible."""
    return f"""
    <div style="background:#FFFFFF;padding:14px 16px;border-radius:10px;border:1px solid #ECECEC;border-top:3px solid {top_color};height:100%;">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
        <span style="font-size:14px;opacity:0.7;">{icon}</span>
        <span style="font-size:10px;color:#777;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">{label}</span>
      </div>
      <div style="font-size:24px;font-weight:800;color:#0B0B0B;line-height:1.1;font-family:'Almarai',sans-serif;">{value}</div>
      <div style="font-size:11px;margin-top:4px;color:{delta_color};font-weight:600;">{delta_text}</div>
    </div>
    """


def detect_themes(df):
    if len(df) == 0: return []
    text = df['Full Text'].astype(str).str.lower()
    out = []
    for theme, kws in THEME_KEYWORDS.items():
        pattern = '|'.join(re.escape(k) for k in kws)
        mask = text.str.contains(pattern, na=False, regex=True)
        cnt = int(mask.sum())
        if cnt > 0:
            out.append({'name': theme, 'count': cnt, 'reach': int(df[mask]['Reach (new)'].sum()), 'pct': cnt/len(df)*100})
    return sorted(out, key=lambda x: x['count'], reverse=True)


def generate_narrative(df, prev_df=None, label="this period"):
    if len(df) == 0:
        return "No mentions captured for this period."
    parts = []
    n = len(df)
    sent = df['Sentiment'].value_counts(normalize=True) * 100
    neg_pct = sent.get('negative', 0)
    pos_pct = sent.get('positive', 0)

    if prev_df is not None and len(prev_df) > 0:
        delta = (n - len(prev_df)) / len(prev_df) * 100
        if delta > 50:
            parts.append(f"<b>Volume surged</b> to {n} mentions ({delta:+.0f}% vs previous).")
        elif delta > 20:
            parts.append(f"Volume rose to {n} mentions ({delta:+.0f}% vs previous).")
        elif delta < -50:
            parts.append(f"Volume fell sharply to {n} mentions ({delta:+.0f}% vs previous).")
        elif delta < -20:
            parts.append(f"Volume eased to {n} mentions ({delta:+.0f}% vs previous).")
        else:
            parts.append(f"{n} mentions captured, in line with previous period ({delta:+.0f}%).")
    else:
        parts.append(f"{n} mentions captured for {label}.")

    if neg_pct > 35:
        parts.append(f"<b>Sentiment skewed heavily negative</b> ({neg_pct:.0f}%).")
    elif neg_pct > 25:
        parts.append(f"Negative sentiment was elevated ({neg_pct:.0f}%).")
    elif pos_pct > neg_pct + 10:
        parts.append(f"Sentiment leaned positive ({pos_pct:.0f}% positive vs {neg_pct:.0f}% negative).")
    else:
        parts.append(f"Sentiment was largely neutral with {neg_pct:.0f}% negative.")

    themes = detect_themes(df)
    if themes:
        top_themes = themes[:2]
        names = ' and '.join([f"<b>{t['name'].lower()}</b> ({t['count']})" for t in top_themes])
        parts.append(f"Conversation centered on {names}.")

    if n > 0:
        top_post = df.nlargest(1, 'Reach (new)').iloc[0]
        verified = ' (verified)' if top_post.get('X Verified') else ''
        parts.append(f"Highest-reach post came from <b>@{top_post['Author']}</b>{verified} at {fmt_int(top_post['Reach (new)'])} reach.")

    verified_neg = len(df[(df['Sentiment']=='negative') & (df['X Verified']==True)])
    if verified_neg > 0:
        parts.append(f"⚠ <b>{verified_neg} verified account(s)</b> posted negative content.")

    return ' '.join(parts)


def compute_alerts(df, prev_df=None):
    alerts = []
    if len(df) == 0:
        return alerts
    n = len(df)
    neg_pct = (df['Sentiment']=='negative').mean() * 100
    high_reach_neg = len(df[(df['Sentiment']=='negative') & (df['Reach (new)']>10000)])
    verified_neg = len(df[(df['Sentiment']=='negative') & (df['X Verified']==True)])

    fired = neg_pct > 30
    alerts.append({'label': 'Negative share > 30%', 'status': 'fired' if fired else 'ok', 'detail': f"{neg_pct:.0f}% negative" + (" ⚠" if fired else "")})

    fired = high_reach_neg > 0
    alerts.append({'label': 'Single neg post reach > 10K', 'status': 'fired' if fired else 'ok', 'detail': f"{high_reach_neg} post(s)" + (" ⚠" if fired else "")})

    fired = verified_neg >= 3
    alerts.append({'label': 'Verified negative ≥ 3', 'status': 'fired' if fired else 'ok', 'detail': f"{verified_neg} verified neg"})

    if prev_df is not None and len(prev_df) > 0:
        delta = (n - len(prev_df)) / len(prev_df) * 100
        fired = delta > 100
        alerts.append({'label': 'Volume spike > 2× previous', 'status': 'fired' if fired else 'ok', 'detail': f"{delta:+.0f}% vs prev" + (" ⚠" if fired else "")})

    boycott_count = df['Full Text'].astype(str).str.contains('مقاطع|قاطع|boycott', regex=True, case=False, na=False).sum()
    fired = boycott_count >= 5
    alerts.append({'label': 'Boycott mentions ≥ 5', 'status': 'fired' if fired else 'ok', 'detail': f"{boycott_count} mention(s)" + (" ⚠" if fired else "")})

    return alerts


# ---------- ADMIN MODE ----------
mode = st.query_params.get("mode", "dashboard")
if mode == "admin":
    st.title("🔒 Admin · Upload daily mentions")
    pw = st.text_input("Admin password", type="password")
    if pw == ADMIN_PASSWORD:
        st.success("Authenticated")
        uploaded = st.file_uploader("Upload Brandwatch export (.xlsx)", type=['xlsx'])
        if uploaded:
            DATA_FILE.parent.mkdir(exist_ok=True)
            with open(DATA_FILE, 'wb') as f:
                f.write(uploaded.getbuffer())
            archive_dir = Path("data/archive"); archive_dir.mkdir(exist_ok=True, parents=True)
            archive_path = archive_dir / f"{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            with open(archive_path, 'wb') as f:
                f.write(uploaded.getbuffer())
            st.cache_data.clear()
            st.success(f"✓ Uploaded. Archived to {archive_path.name}")
            st.markdown("[← Back to dashboard](/?mode=dashboard)")
        else:
            if DATA_FILE.exists():
                ts = datetime.fromtimestamp(DATA_FILE.stat().st_mtime)
                st.caption(f"Currently serving: data/latest.xlsx · uploaded {ts.strftime('%Y-%m-%d %H:%M')}")
    elif pw:
        st.error("Wrong password")
    st.stop()


# ---------- LOAD DATA ----------
if not DATA_FILE.exists():
    st.error("No data file found. Upload via /?mode=admin")
    st.stop()
df_all = load_data(DATA_FILE)
all_dates = sorted(df_all['DateOnly'].unique())


# ---------- TIME SCOPE PICKER ----------
scope_col1, scope_col2, scope_col3, scope_col4 = st.columns([1.5, 2, 2, 1])
with scope_col1:
    view_mode = st.radio("View", ["Single day", "Last 7 days", "Custom range"], label_visibility='collapsed')

with scope_col2:
    if view_mode == "Single day":
        sel_day = st.selectbox(
            "Day",
            options=list(reversed(all_dates)),
            index=0,
            format_func=lambda d: d.strftime('%a, %b %d, %Y'),
            label_visibility='collapsed'
        )
        df_period = df_all[df_all['DateOnly'] == sel_day].copy()
        prev_dates = [d for d in all_dates if d < sel_day]
        prev_day = prev_dates[-1] if prev_dates else None
        df_prev = df_all[df_all['DateOnly'] == prev_day].copy() if prev_day else pd.DataFrame()
        period_label = sel_day.strftime('%b %d, %Y')
        comp_label = f"vs {prev_day.strftime('%b %d')}" if prev_day else ""
    elif view_mode == "Last 7 days":
        end = max(all_dates)
        start = end - timedelta(days=6)
        df_period = df_all[(df_all['DateOnly'] >= start) & (df_all['DateOnly'] <= end)].copy()
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=6)
        df_prev = df_all[(df_all['DateOnly'] >= prev_start) & (df_all['DateOnly'] <= prev_end)].copy()
        period_label = f"{start.strftime('%b %d')} – {end.strftime('%b %d')}"
        comp_label = "vs prev 7 days"
    else:
        date_range = st.date_input("Range", value=(min(all_dates), max(all_dates)),
                                   min_value=min(all_dates), max_value=max(all_dates),
                                   label_visibility='collapsed')
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            df_period = df_all[(df_all['DateOnly'] >= start) & (df_all['DateOnly'] <= end)].copy()
            span = (end - start).days + 1
            prev_end = start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=span - 1)
            df_prev = df_all[(df_all['DateOnly'] >= prev_start) & (df_all['DateOnly'] <= prev_end)].copy()
            period_label = f"{start.strftime('%b %d')} – {end.strftime('%b %d')}"
            comp_label = f"vs prev {span} days"
        else:
            df_period = df_all.copy(); df_prev = pd.DataFrame()
            period_label = "all data"; comp_label = ""

with scope_col3:
    sub_filters = st.multiselect("Sentiment", ['positive','neutral','negative'],
                                 default=['positive','neutral','negative'], label_visibility='collapsed')
    if sub_filters:
        df_period = df_period[df_period['Sentiment'].isin(sub_filters)]

with scope_col4:
    st.write("")
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()


# ---------- HEADER ----------
logo_b64 = get_logo_b64()
file_ts = datetime.fromtimestamp(DATA_FILE.stat().st_mtime).strftime('%b %d, %H:%M')

neg_pct_h = (df_period['Sentiment']=='negative').mean() * 100 if len(df_period) > 0 else 0
high_reach_neg_h = len(df_period[(df_period['Sentiment']=='negative') & (df_period['Reach (new)']>10000)])
verified_neg_h = len(df_period[(df_period['Sentiment']=='negative') & (df_period['X Verified']==True)])
if neg_pct_h > 35 or high_reach_neg_h > 5: risk_lvl, risk_color = "HIGH", "#A32D2D"
elif neg_pct_h > 20 or high_reach_neg_h > 2 or verified_neg_h > 5: risk_lvl, risk_color = "MEDIUM", "#BA7517"
else: risk_lvl, risk_color = "LOW", "#3B6D11"

st.markdown(f"""
<div class="brand-hdr">
  <div style="display:flex;align-items:center;gap:14px">
    <div style="background:white;padding:8px;border-radius:8px;width:54px;height:42px;display:flex;align-items:center;justify-content:center">
      <img src="data:image/svg+xml;base64,{logo_b64}" style="height:30px"/>
    </div>
    <div>
      <p class="brand-title">Daily X Monitoring · {period_label}</p>
      <p class="brand-sub">{view_mode} · {comp_label} · Last upload: {file_ts}</p>
    </div>
  </div>
  <span class="risk-pill" style="background:{risk_color}">Risk: {risk_lvl}</span>
</div>
""", unsafe_allow_html=True)

if len(df_period) == 0:
    st.warning("No mentions for this period / filter combination.")
    st.stop()


# ---------- KPI ROW (with icons + DoD deltas, INLINE STYLES for visibility) ----------
prev_n = len(df_prev) if len(df_prev) else 0
prev_reach = df_prev['Reach (new)'].sum() if len(df_prev) else 0
prev_imp = df_prev['Impressions'].sum() if len(df_prev) else 0
prev_eng = df_prev['Engagement'].sum() if len(df_prev) else 0
prev_auth = df_prev['Author'].nunique() if len(df_prev) else 0
prev_ver = (df_prev['X Verified']==True).sum() if len(df_prev) else 0

d1 = delta_str(len(df_period), prev_n)
d2 = delta_str(df_period['Reach (new)'].sum(), prev_reach)
d3 = delta_str(df_period['Impressions'].sum(), prev_imp)
d4 = delta_str(df_period['Engagement'].sum(), prev_eng)
d5 = delta_str(df_period['Author'].nunique(), prev_auth)
d6 = delta_str((df_period['X Verified']==True).sum(), prev_ver)

kpi_html = f"""
<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:18px">
{kpi_card('💬', 'Mentions',    f"{len(df_period):,}",                       d1[0], d1[1], BRAND_BLUE)}
{kpi_card('📡', 'Reach',       fmt_int(df_period['Reach (new)'].sum()),     d2[0], d2[1], BRAND_GREEN)}
{kpi_card('👁', 'Impressions', fmt_int(df_period['Impressions'].sum()),     d3[0], d3[1], BRAND_PURPLE)}
{kpi_card('❤', 'Engagement',  f"{df_period['Engagement'].sum():,}",         d4[0], d4[1], '#BA7517')}
{kpi_card('👥', 'Authors',     f"{df_period['Author'].nunique():,}",        d5[0], d5[1], BRAND_BLUE)}
{kpi_card('✓', 'Verified',    f"{(df_period['X Verified']==True).sum():,}", d6[0], d6[1], BRAND_PURPLE)}
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# ---------- CRISIS BAR + AUTO-NARRATIVE ----------
crisis_class = "high" if neg_pct_h > 35 else ("low" if neg_pct_h < 20 and len(df_period) > 0 else "")
narrative = generate_narrative(df_period, df_prev, label=period_label)
st.markdown(f"""
<div class="crisis-bar {crisis_class}">
  <div class="crisis-headline">📊 Period analysis · {period_label}</div>
  <div class="crisis-narrative">{narrative}</div>
</div>
""", unsafe_allow_html=True)


# ---------- SENTIMENT DONUT + DAILY VOLUME (always shown) ----------
c1, c2 = st.columns([1, 2])
with c1:
    st.markdown('<div class="sec-h">Sentiment breakdown</div>', unsafe_allow_html=True)
    sc = df_period['Sentiment'].value_counts()
    fig = go.Figure(go.Pie(
        labels=['Positive','Neutral','Negative'],
        values=[int(sc.get('positive',0)), int(sc.get('neutral',0)), int(sc.get('negative',0))],
        hole=0.65, marker=dict(colors=[SENT_POS, SENT_NEU, SENT_NEG], line=dict(width=0)),
        textinfo='percent', textfont=dict(size=12, color='white'),
    ))
    fig.update_layout(height=260, margin=dict(t=10,b=10,l=10,r=10), showlegend=True,
                      legend=dict(orientation='h', y=-0.1, x=0.5, xanchor='center'),
                      paper_bgcolor='white', plot_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.markdown('<div class="sec-h">Daily volume by sentiment</div>', unsafe_allow_html=True)
    daily = df_period.groupby(['DateOnly','Sentiment']).size().unstack(fill_value=0)
    for s in ['positive','neutral','negative']:
        if s not in daily.columns: daily[s] = 0
    fig = go.Figure()
    fig.add_trace(go.Bar(x=daily.index, y=daily['positive'], name='Positive', marker_color=SENT_POS))
    fig.add_trace(go.Bar(x=daily.index, y=daily['neutral'], name='Neutral', marker_color=SENT_NEU))
    fig.add_trace(go.Bar(x=daily.index, y=daily['negative'], name='Negative', marker_color=SENT_NEG))
    fig.update_layout(barmode='stack', height=260, margin=dict(t=10,b=10,l=10,r=10),
                      showlegend=True, legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
                      paper_bgcolor='white', plot_bgcolor='white',
                      xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#F0F0F0'))
    if view_mode == "Single day":
        st.caption("Single bar reflects the selected day. Switch to 'Last 7 days' or 'Custom range' to see trend.")
    st.plotly_chart(fig, use_container_width=True)


# ---------- TOP POSTS · 4 categories with deduplication ----------
def render_post(row, primary_metric):
    sent = row['Sentiment']
    sent_class = {'positive':'pos','negative':'neg','neutral':'neu'}.get(sent,'neu')
    text = str(row.get('Full Text',''))[:280]
    url = str(row.get('Url',''))
    verified = ' ✓' if row.get('X Verified') else ''
    if primary_metric == 'engagement':
        primary = f"❤ <b>{row['Engagement']:,}</b> engagement"
    else:
        primary = f"📡 <b>{fmt_int(row['Reach (new)'])}</b> reach"
    return f"""
    <div class="post-card {sent_class}">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="post-author">@{row['Author']}{verified}</span>
        <span class="post-meta">{row['Date'].strftime('%b %d · %H:%M')}</span>
      </div>
      <div class="post-text">{text}</div>
      <div class="post-stats">
        <span>{primary}</span>
        <span>♥ <b>{row['X Likes']:,}</b></span>
        <span>↻ <b>{row['X Reposts']:,}</b></span>
        <span>💬 <b>{row['X Replies']:,}</b></span>
        <span>👥 <b>{fmt_int(row['X Followers'])}</b></span>
        <span class="sent-tag s-{sent_class}">{sent}</span>
        <a href="{url}" target="_blank" style="margin-left:auto;color:{BRAND_BLUE};font-size:11px">View on X →</a>
      </div>
    </div>
    """

# Restored to 3 each (matching v1), then deduped, then 2 pos/neg
top_eng_df = df_period.nlargest(3, 'Engagement')
seen_urls = set(top_eng_df['Url'].astype(str))

top_reach_pool = df_period[~df_period['Url'].astype(str).isin(seen_urls)]
top_reach_df = top_reach_pool.nlargest(3, 'Reach (new)')
seen_urls.update(top_reach_df['Url'].astype(str))

top_pos_pool = df_period[(df_period['Sentiment']=='positive') & (~df_period['Url'].astype(str).isin(seen_urls))]
top_pos_df = top_pos_pool.nlargest(2, 'Engagement')
seen_urls.update(top_pos_df['Url'].astype(str))

top_neg_pool = df_period[(df_period['Sentiment']=='negative') & (~df_period['Url'].astype(str).isin(seen_urls))]
top_neg_df = top_neg_pool.nlargest(2, 'Engagement')

c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="sec-h">❤ Top 3 by engagement</div>', unsafe_allow_html=True)
    if len(top_eng_df):
        for _, r in top_eng_df.iterrows():
            st.markdown(render_post(r, 'engagement'), unsafe_allow_html=True)
    else:
        st.caption("No posts in this period.")
with c2:
    st.markdown('<div class="sec-h">📡 Top 3 by reach <span style="font-weight:400;color:#999;font-size:11px">· deduped</span></div>', unsafe_allow_html=True)
    if len(top_reach_df):
        for _, r in top_reach_df.iterrows():
            st.markdown(render_post(r, 'reach'), unsafe_allow_html=True)
    else:
        st.caption("No additional posts (already shown in engagement).")

c1, c2 = st.columns(2)
with c1:
    st.markdown(f'<div class="sec-h" style="color:{SENT_POS}">😊 Top 2 positive (by engagement)</div>', unsafe_allow_html=True)
    if len(top_pos_df):
        for _, r in top_pos_df.iterrows():
            st.markdown(render_post(r, 'engagement'), unsafe_allow_html=True)
    else:
        st.caption("No additional positive posts in this period.")
with c2:
    st.markdown(f'<div class="sec-h" style="color:{SENT_NEG}">⚠ Top 2 negative (by engagement)</div>', unsafe_allow_html=True)
    if len(top_neg_df):
        for _, r in top_neg_df.iterrows():
            st.markdown(render_post(r, 'engagement'), unsafe_allow_html=True)
    else:
        st.caption("No additional negative posts in this period.")


# ---------- AUTHORS + CITY BAR CHART (back to v1 style) ----------
c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="sec-h">👥 Top 10 authors</div>', unsafe_allow_html=True)
    rank_by = st.radio("Rank by", ['Reach','Engagement'], horizontal=True, label_visibility='collapsed', key='author_rank')
    sort_col = 'Reach' if rank_by == 'Reach' else 'Engagement'
    auth = df_period.groupby('Author').agg(
        Posts=('Author','count'),
        Reach=('Reach (new)','sum'),
        Engagement=('Engagement','sum'),
        Followers=('X Followers','max'),
        Verified=('X Verified','max')
    ).sort_values(sort_col, ascending=False).head(10).reset_index()
    auth['Author'] = auth.apply(lambda r: f"@{r['Author']} ✓" if r['Verified'] else f"@{r['Author']}", axis=1)
    st.dataframe(
        auth[['Author','Posts','Reach','Engagement','Followers']],
        hide_index=True, use_container_width=True,
        column_config={
            'Reach': st.column_config.NumberColumn(format="%d"),
            'Engagement': st.column_config.NumberColumn(format="%d"),
            'Followers': st.column_config.NumberColumn(format="%d"),
        }
    )

with c2:
    st.markdown('<div class="sec-h">📍 Top cities</div>', unsafe_allow_html=True)
    city_data = df_period[df_period['City'].notna()].groupby('City').agg(
        Mentions=('City','count'),
        Reach=('Reach (new)','sum'),
        Engagement=('Engagement','sum')
    ).sort_values('Mentions', ascending=False).head(10).reset_index()
    if len(city_data):
        fig = px.bar(
            city_data, x='Mentions', y='City', orientation='h',
            color='Mentions', color_continuous_scale=[[0, BRAND_BLUE], [1, BRAND_GREEN]],
            text='Mentions',
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(height=380, margin=dict(t=10,b=10,l=10,r=10),
                          yaxis=dict(autorange='reversed', title=None),
                          xaxis=dict(title=None, showgrid=False),
                          coloraxis_showscale=False,
                          paper_bgcolor='white', plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{df_period['City'].notna().sum()} of {len(df_period)} mentions had geo data")
    else:
        st.info("No city data in this period")


# ---------- HOURLY TIMELINE (full width — kept from v1) ----------
st.markdown('<div class="sec-h">⏰ Hourly timeline · Mentions vs Engagement</div>', unsafe_allow_html=True)
hourly = df_period.groupby('Hour').agg(Mentions=('Hour','count'), Engagement=('Engagement','sum')).reindex(range(24), fill_value=0).reset_index()
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(x=hourly['Hour'], y=hourly['Mentions'], name='Mentions', marker_color=BRAND_BLUE), secondary_y=False)
fig.add_trace(go.Scatter(x=hourly['Hour'], y=hourly['Engagement'], name='Engagement',
                         line=dict(color=BRAND_GREEN, width=3), mode='lines+markers',
                         marker=dict(size=6)), secondary_y=True)
fig.update_layout(height=320, margin=dict(t=10,b=10,l=10,r=10),
                  xaxis=dict(title='Hour of day', tickmode='linear', tick0=0, dtick=1),
                  paper_bgcolor='white', plot_bgcolor='white',
                  legend=dict(orientation='h', y=1.1, x=0.5, xanchor='center'))
fig.update_yaxes(title_text="Mentions", secondary_y=False, gridcolor='#F0F0F0')
fig.update_yaxes(title_text="Engagement", secondary_y=True, showgrid=False)
st.plotly_chart(fig, use_container_width=True)
if hourly['Mentions'].sum() > 0:
    peak_hour = int(hourly.loc[hourly['Mentions'].idxmax(),'Hour'])
    peak_eng = int(hourly.loc[hourly['Engagement'].idxmax(),'Hour'])
    st.caption(f"Peak posting hour: {peak_hour:02d}:00 · Peak engagement hour: {peak_eng:02d}:00")


# ---------- THEMES + ALERTS (added from v2) ----------
c1, c2 = st.columns([1.2, 1])
with c1:
    st.markdown('<div class="sec-h">🏷 Conversation themes</div>', unsafe_allow_html=True)
    themes = detect_themes(df_period)
    if themes:
        theme_df = pd.DataFrame(themes)
        neg_themes = {'Price complaint','Boycott narrative','Product quality','Health concerns','Weight reduction'}
        pos_themes = {'Positive product'}
        colors = [SENT_NEG if t in neg_themes else (SENT_POS if t in pos_themes else BRAND_PURPLE) for t in theme_df['name']]
        fig = go.Figure(go.Bar(
            x=theme_df['count'], y=theme_df['name'], orientation='h',
            marker=dict(color=colors),
            text=theme_df.apply(lambda r: f"{r['count']} · {fmt_int(r['reach'])} reach", axis=1),
            textposition='outside',
        ))
        fig.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10),
                          yaxis=dict(autorange='reversed', title=None),
                          xaxis=dict(title=None, showgrid=False),
                          paper_bgcolor='white', plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No themes detected in this period.")

with c2:
    st.markdown('<div class="sec-h">🚨 Alert rules</div>', unsafe_allow_html=True)
    alerts = compute_alerts(df_period, df_prev)
    rows = ""
    for a in alerts:
        rows += f'<div class="alert-row"><span style="font-size:12px">{a["label"]}</span><span class="alert-status {a["status"]}">{a["detail"]}</span></div>'
    st.markdown(f'<div style="background:white;padding:14px;border-radius:8px;border:1px solid #EEE">{rows}</div>', unsafe_allow_html=True)


# ---------- HASHTAGS + CRISIS REPORT CARD (restored from v1) ----------
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown('<div class="sec-h"># Top hashtags</div>', unsafe_allow_html=True)
    all_tags = []
    for h in df_period['Hashtags'].dropna():
        all_tags.extend([t.strip() for t in str(h).split(',') if t.strip()])
    tag_counts = Counter(all_tags).most_common(15)
    if tag_counts:
        tag_df = pd.DataFrame(tag_counts, columns=['Hashtag','Count'])
        fig = px.bar(tag_df, x='Count', y='Hashtag', orientation='h', text='Count',
                     color_discrete_sequence=[BRAND_PURPLE])
        fig.update_traces(textposition='outside')
        fig.update_layout(height=400, margin=dict(t=10,b=10,l=10,r=10),
                          yaxis=dict(autorange='reversed', title=None),
                          xaxis=dict(title=None, showgrid=False),
                          paper_bgcolor='white', plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hashtags in this period.")

with c2:
    st.markdown('<div class="sec-h">📋 Crisis report card</div>', unsafe_allow_html=True)
    crisis_data = [
        ("Negative share", f"{neg_pct_h:.1f}%", "high" if neg_pct_h > 35 else ("med" if neg_pct_h > 20 else "low")),
        ("High-reach negative (>10K)", str(high_reach_neg_h), "high" if high_reach_neg_h > 5 else ("med" if high_reach_neg_h > 2 else "low")),
        ("Verified neg accounts", str(verified_neg_h), "high" if verified_neg_h > 5 else ("med" if verified_neg_h > 2 else "low")),
        ("Crisis-tagged mentions", f"{df_period['Almarai Prices Crisis - Almarai Prices Crisis'].notna().sum()}", "med"),
        ("Total volume", f"{len(df_period):,}", "low"),
    ]
    rows = ""
    for label, val, lvl in crisis_data:
        color = {"high":"#A32D2D","med":"#BA7517","low":"#3B6D11"}[lvl]
        icon = {"high":"⚠","med":"●","low":"✓"}[lvl]
        rows += f'<div class="crisis-card-row"><span>{label}</span><span style="color:{color};font-weight:700">{val} {icon}</span></div>'
    st.markdown(f'<div class="crisis-card">{rows}</div>', unsafe_allow_html=True)


# ---------- EXPORTS ----------
st.markdown('<div class="sec-h">📥 Export</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    csv = df_period[['Date','Author','Sentiment','Full Text','X Likes','X Reposts','X Replies','Reach (new)','City','Url']].to_csv(index=False).encode('utf-8')
    st.download_button("Download data (CSV)", csv, f"almarai_x_{period_label.replace(' ','_').replace(',','')}.csv", "text/csv")
with c2:
    summary = f"""ALMARAI X DAILY MONITORING REPORT
Period: {period_label} ({view_mode})
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

ANALYSIS
{re.sub('<[^>]+>','', narrative)}

VOLUME
- Mentions: {len(df_period):,}
- Authors: {df_period['Author'].nunique():,}
- Verified: {(df_period['X Verified']==True).sum():,}

REACH & ENGAGEMENT
- Reach: {df_period['Reach (new)'].sum():,}
- Impressions: {df_period['Impressions'].sum():,}
- Engagement: {df_period['Engagement'].sum():,}

SENTIMENT
- Positive: {(df_period['Sentiment']=='positive').sum()} ({(df_period['Sentiment']=='positive').mean()*100:.1f}%)
- Neutral:  {(df_period['Sentiment']=='neutral').sum()} ({(df_period['Sentiment']=='neutral').mean()*100:.1f}%)
- Negative: {(df_period['Sentiment']=='negative').sum()} ({(df_period['Sentiment']=='negative').mean()*100:.1f}%)

CRISIS INDICATORS
- Risk: {risk_lvl}
- High-reach negative: {high_reach_neg_h}
- Verified negative: {verified_neg_h}
"""
    st.download_button("Download brief (TXT)", summary, f"almarai_brief_{period_label.replace(' ','_').replace(',','')}.txt")
with c3:
    st.markdown(f"<div style='padding-top:8px;font-size:12px;color:#777'>Admin: <a href='/?mode=admin'>/?mode=admin</a></div>", unsafe_allow_html=True)


st.markdown(f"""
<div style="text-align:center;color:#999;font-size:11px;margin-top:30px;padding-top:14px;border-top:1px solid #EEE">
Almarai · X Monitoring Dashboard · v3 · Defaults to most recent day
</div>
""", unsafe_allow_html=True)
