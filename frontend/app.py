import streamlit as st
import requests
import json
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime
import pandas as pd

# ---------------------------------------------------------
# Page config
# ---------------------------------------------------------
st.set_page_config(
    page_title="T-Mobile CHI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# T-Mobile Brand Styling (MVP Spec)
# ---------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif !important;
    }
    
    .stApp { 
        background-color: #FFFFFF !important;
    }
    
    /* T-Mobile Brand Colors */
    :root {
        --tm-pink: #E20074;
        --tm-pink-hover: #FF3399;
        --tm-text-primary: #000000;
        --tm-text-secondary: #5A5A5A;
      --tm-bg: #FFFFFF;
        --tm-card-bg: #F8F8F8;
        --tm-alert-red: #FF4D4F;
        --tm-success-green: #52C41A;
        --tm-warning-orange: #FAAD14;
    }
    
    /* Typography - Headings: Bold, all-caps, tight line-height */
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        line-height: 1.2 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] h5,
    [data-testid="stMarkdownContainer"] h6 {
        color: #000000 !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        line-height: 1.2 !important;
    }
    
    /* Body text */
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] strong {
        color: #000000 !important;
        font-weight: 500 !important;
    }
    
    /* Sidebar - Fixed width 280px */
    [data-testid="stSidebar"] {
        background-color: #F8F8F8 !important;
        width: 280px !important;
        min-width: 280px !important;
    }
    [data-testid="stSidebar"] * {
        color: #000000 !important;
    }
    
    /* Sidebar buttons - Pill-shaped with hover color inversion */
    [data-testid="stSidebar"] .stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #E20074 !important;
        border-radius: 25px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(226, 0, 116, 0.1) !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #E20074 !important;
        color: #FFFFFF !important;
        border-color: #E20074 !important;
        box-shadow: 0 4px 12px rgba(226, 0, 116, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #E20074 !important;
        color: #FFFFFF !important;
        border-color: #E20074 !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background-color: #FF3399 !important;
        border-color: #FF3399 !important;
    }
    
    /* Main content buttons */
    .stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #E20074 !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(226, 0, 116, 0.1) !important;
    }
    .stButton > button:hover {
        background-color: #E20074 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(226, 0, 116, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #E20074 !important;
        color: #FFFFFF !important;
        border-color: #E20074 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #FF3399 !important;
        border-color: #FF3399 !important;
    }
    
    /* Cards - Pink shadow hover states */
    .metric-card-large {
        background: #FFFFFF !important;
        padding: 2rem !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        border-left: 4px solid #E20074 !important;
        transition: all 0.3s ease !important;
    }
    .metric-card-large:hover {
        box-shadow: 0 8px 24px rgba(226, 0, 116, 0.2) !important;
        transform: translateY(-4px) !important;
    }
    
    .metric-card-small {
        background: #F8F8F8 !important;
        padding: 1rem !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
    }
    .metric-card-small:hover {
        box-shadow: 0 4px 12px rgba(226, 0, 116, 0.15) !important;
    }
    
    /* Alert cards */
    .alert-card {
        background: #FFFFFF !important;
        border-left: 4px solid #FF4D4F !important;
        padding: 1.5rem !important;
        border-radius: 10px !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease !important;
    }
    .alert-card:hover {
        box-shadow: 0 4px 16px rgba(255, 77, 79, 0.2) !important;
        transform: translateX(4px) !important;
    }
    
    /* Input fields */
    [data-testid="stSidebar"] .stTextInput > div > div > input,
    [data-testid="stSidebar"] .stTextArea > div > textarea,
    .stSelectbox > div > div > div,
    [data-testid="stDateInput"] > div > div > input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 10px !important;
    }
    
    /* AI Support Panel */
    .ai-header { 
        font-weight: 700 !important;
        color: #000000 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-size: 0.9rem !important;
    }
    .ai-title-pill {
        display: inline-block !important;
        padding: 0.4rem 0.8rem !important;
        border-radius: 20px !important;
        background: #FDF2F8 !important;
        color: #E20074 !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        border: 1px solid #FCE7F3 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    .ai-reco {
        background: #FFF5F9 !important;
        border-left: 3px solid #E20074 !important;
        padding: 0.75rem 1rem !important;
        border-radius: 8px !important;
        margin-bottom: 0.5rem !important;
        font-size: 0.9rem !important;
        color: #000000 !important;
    }
    
    /* Status indicators */
    .chi-status-happy { color: #52C41A !important; }
    .chi-status-unstable { color: #FAAD14 !important; }
    .chi-status-critical { color: #FF4D4F !important; }
    
    /* Hide Streamlit defaults */
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }
    header { visibility: hidden !important; }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Data loading
# ---------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REGIONS_FILE = DATA_DIR / "regions.json"

@st.cache_data
def load_regions():
    if REGIONS_FILE.exists():
        with open(REGIONS_FILE) as f:
            return json.load(f)
    return []

# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------
ss = st.session_state
ss.setdefault("api_url", "http://127.0.0.1:8000")
ss.setdefault("regions_data", load_regions())
ss.setdefault("current_page", "Overview")
ss.setdefault("chat_history", [])
ss.setdefault("ai_recommendations", [])
ss.setdefault("last_qa_result", None)

# ---------------------------------------------------------
# API helpers
# ---------------------------------------------------------
def api_get(endpoint, params=None, timeout=30):
    try:
        url = f"{ss.api_url}{endpoint}"
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        st.warning(f"Request to {endpoint} timed out. The backend may be processing a large query.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to backend at {ss.api_url}. Is the backend running?")
        return None
    except Exception as e:
        # Don't show error for alerts if it's just empty
        if endpoint == "/alerts" and "timeout" in str(e).lower():
            return {"alerts": []}
        st.error(f"API Error: {str(e)}")
        return None

def api_post(endpoint, json_data=None):
    try:
        url = f"{ss.api_url}{endpoint}"
        r = requests.post(url, json=json_data, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


def fetch_groq_recommendations(alert: dict) -> tuple:
    """
    Fetch GROQ recommendations for an alert.
    Returns (recommendations_text, source) where source ∈ {'groq', 'fallback', None}
    """
    alert_id = f"{alert.get('region', '')}_{alert.get('ts', '')}"
    
    # Check cache
    cache_key = f"groq_recs_{alert_id}"
    if cache_key in ss:
        return ss[cache_key]
    
    # Extract topics from reason field (format: "... | topics: outage, down, slow")
    reason = alert.get('reason', '')
    topics = []
    if 'topics:' in reason:
        try:
            topics_str = reason.split('topics:')[1].strip()
            topics = [t.strip() for t in topics_str.split(',')]
        except:
            pass
    
    # If no topics found, try to infer from reason
    if not topics:
        reason_lower = reason.lower()
        if 'outage' in reason_lower or 'down' in reason_lower:
            topics.append('outage')
        if 'slow' in reason_lower or 'latency' in reason_lower:
            topics.append('slow_data')
        if 'billing' in reason_lower:
            topics.append('billing')
        if 'roaming' in reason_lower:
            topics.append('roaming')
    
    # Get KPI data from latest CHI for this region
    kpi_data = {}
    region = alert.get('region', '')
    if region:
        chi_data = api_get("/chi", {"region": region})
        if chi_data and chi_data.get('drivers'):
            drivers = chi_data['drivers']
            kpi_data = {
                "latency_ms": drivers.get('latency_ms', 0),
                "throughput_mbps": drivers.get('throughput_mbps', 0),
                "prb_util": drivers.get('prb_util', 0),
                "kpi_health": drivers.get('kpi_health', 0)
            }
    
    # Build context
    context = {
        "region": region or 'Unknown',
        "current_chi": float(alert.get('chi_after', 0)),
        "prev_chi": float(alert.get('chi_before', 0)) if alert.get('chi_before') else None,
        "topics": topics,
        "kpi": kpi_data,
        "time": alert.get('ts', '')
    }
    
    # Fetch from API
    result = api_post("/recommendations", context)
    
    if result and result.get("recommendations"):
        recs = result.get("recommendations", "")
        source = result.get("source", "fallback")
        ss[cache_key] = (recs, source)
        return recs, source
    else:
        # Fallback
        fallback = (
            "Hypothesis: CHI drop likely due to congestion or partial outage across one or more cells.\n"
            "1) Inspect top PRB/throughput offenders; rebalance traffic.\n"
            "2) Verify backhaul and core KPIs; reroute if saturation detected.\n"
            "3) Push customer SMS with ETA + mitigations.\n"
            "4) Temporarily raise QoS for critical services; throttle background traffic.\n"
            "5) Open/attach incident and assign on-call for triage within 30 min."
        )
        ss[cache_key] = (fallback, "fallback")
        return fallback, "fallback"

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def get_chi_status(score):
    """Return status label and color for CHI score."""
    if score >= 70:
        return "Happy", "chi-status-happy"
    elif score >= 50:
        return "Unstable", "chi-status-unstable"
    else:
        return "Critical", "chi-status-critical"

def format_timestamp(ts_str):
    """Format ISO timestamp to readable format."""
    try:
        dt = pd.to_datetime(ts_str)
        return dt.strftime("%Y-%m-%d %I:%M %p")
    except:
        return ts_str[:19] if len(ts_str) > 19 else ts_str

# ---------------------------------------------------------
# SIDEBAR: Nav + Embedded AI
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div style="text-align:center; padding:1.5rem 0;"><h1 style="color:#E20074; margin:0; font-size:1.8rem; font-weight:800; text-transform:uppercase; letter-spacing:2px;">T-Mobile</h1></div>',
        unsafe_allow_html=True
    )
    st.divider()

    # Navigation - Pill-shaped buttons
    nav_items = ["Overview", "Alerts", "Outages", "Region Map"]
    for item in nav_items:
        is_active = ss.current_page == item
        btn_type = "primary" if is_active else "secondary"
        if st.button(item, key=f"nav_{item}", use_container_width=True, type=btn_type):
            ss.current_page = item
            st.rerun()

    st.divider()

    # ---------- AI Support Panel ----------
    st.markdown('<div class="ai-header">AI Support</div>', unsafe_allow_html=True)
    st.markdown('<span class="ai-title-pill">Happiness Index Assistant</span>', unsafe_allow_html=True)
    st.write("")

    with st.form("ai_form", clear_on_submit=True):
        q = st.text_input("Ask a question", placeholder="e.g., Why is Midwest lower today?", label_visibility="collapsed")
        submitted = st.form_submit_button("Ask", use_container_width=True, help="Send to AI")
    
    if submitted and q.strip():
        ts = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        ss.chat_history.append({"role": "user", "content": q.strip(), "ts": ts})

        with st.spinner("Searching Pinecone knowledge base..."):
            result = api_post("/qa", {"question": q.strip()}) or {}
        
        summary = result.get("summary") or "No summary available."
        recos = result.get("actions") or result.get("recommendations") or []
        sources = result.get("sources", {})
        
        ss.last_qa_result = result
        ss.chat_history.append({
            "role": "bot", 
            "content": summary, 
            "ts": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            "sources": sources
        })
        ss.ai_recommendations = recos
        st.rerun()

    # Latest response
    last_bot = None
    for msg in reversed(ss.chat_history):
        if msg["role"] == "bot":
            last_bot = msg
            break
    
    if last_bot:
        st.markdown("**Answer**")
        st.markdown(f'<div class="ai-reco">{last_bot["content"]}</div>', unsafe_allow_html=True)
        
        # Show customer reviews from evidence
        if hasattr(ss, 'last_qa_result') and ss.last_qa_result:
            evidence = ss.last_qa_result.get("drivers", {}).get("evidence", [])
            if evidence:
                st.markdown("**📝 Customer Reviews Found:**")
                for ev in evidence[:5]:
                    st.markdown(f'<div style="background:#F9FAFB; padding:0.75rem; border-radius:6px; margin-bottom:0.5rem; border-left:3px solid #E20074; font-size:0.9rem; color:#000000;">{ev}</div>', unsafe_allow_html=True)
        
        # Show sources
        sources = last_bot.get("sources", {})
        if sources.get("review_count", 0) > 0:
            st.caption(f"📊 Based on {sources.get('review_count')} customer review(s) from Pinecone")
            if sources.get("regions"):
                st.caption(f"📍 Regions: {', '.join(sources.get('regions', [])[:5])}")

    # Recommendations
    if ss.ai_recommendations:
        st.markdown("**AI Recommendations**")
        for rec in ss.ai_recommendations:
            st.markdown(f'<div class="ai-reco">{rec}</div>', unsafe_allow_html=True)

    # Conversation History
    with st.expander("Conversation history"):
        if not ss.chat_history:
            st.caption("No messages yet.")
        else:
            for msg in ss.chat_history:
                who = "You" if msg["role"] == "user" else "Assistant"
                st.markdown(f"**{who}** ({msg.get('ts', '')})")
                st.markdown(f"<div style='color:#5A5A5A;'>{msg['content']}</div>", unsafe_allow_html=True)
                st.markdown("---")

# ---------------------------------------------------------
# MAIN CONTENT
# ---------------------------------------------------------
st.title("T-Mobile Customer Happiness Index")

# Get overall CHI data
regions_summary = api_get("/regions")
overall_chi = 0
if regions_summary and regions_summary.get("regions"):
    scores = [r["score"] for r in regions_summary.get("regions", [])]
    overall_chi = sum(scores) / len(scores) if scores else 0

# ---------------- Overview Page ----------------
if ss.current_page == "Overview":
    # Overall CHI Card with status indicator
    chi_status, chi_status_class = get_chi_status(overall_chi)
    
    # Get previous CHI for trend
    prev_chi = overall_chi  # Simplified - would fetch from history
    chi_delta = overall_chi - prev_chi
    chi_arrow = "↑" if chi_delta >= 0 else "↓"
    chi_color = "#52C41A" if chi_delta >= 0 else "#FF4D4F"
    
    chi_col, sent_col = st.columns([1, 1])
    
    with chi_col:
        st.markdown(f"""
            <div class="metric-card-large">
                <div style="font-size: 0.9rem; color:#5A5A5A; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.5px;">Overall Customer Happiness Index</div>
                <div style="font-size: 4rem; font-weight:800; color:#E20074; margin-bottom:0.25rem; line-height:1;">{overall_chi:.0f}</div>
                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem;">
                    <span style="color:{chi_color}; font-weight:700; font-size:1.2rem;">{chi_arrow}</span>
                    <span style="color:#5A5A5A; font-size:0.9rem;">Since last hour</span>
                </div>
                <div style="padding:0.5rem 1rem; background:#F8F8F8; border-radius:8px; display:inline-block;">
                    <span class="{chi_status_class}" style="font-weight:700; text-transform:uppercase; letter-spacing:1px;">{chi_status}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with sent_col:
        sentiment = api_get("/sentiment_overall") or {"score": 50.0, "samples": 0}
        sent_score = float(sentiment.get("score", 50.0))
        neg_percent = max(0, min(100, 100 - sent_score))
        
        st.markdown(f"""
            <div class="metric-card-large">
                <div style="font-size: 0.9rem; color:#5A5A5A; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.5px;">Sentiment Analysis (AI‑driven)</div>
                <div style="font-size: 4rem; font-weight:800; color:#FF4D4F; margin-bottom:0.25rem; line-height:1;">{neg_percent:.0f}%</div>
                <div style="color:#5A5A5A; font-size:0.85rem; margin-bottom:0.5rem;">Negative Sentiment</div>
                <div style="display:flex; gap:1rem; font-size:0.8rem; color:#5A5A5A;">
                    <span>📞 Call Logs</span>
                    <span>💬 Chat Transcripts</span>
                    <span>🎫 Ticket Notes</span>
                </div>
                <div style="margin-top:0.5rem; font-size:0.75rem; color:#5A5A5A;">Data sourced from Pinecone + GROQ</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Interactive Region Map")

    # Map with color-coded regions
    map_data = []
    regions_dict = {}
    if regions_summary:
        for r in regions_summary.get("regions", []):
            regions_dict[r["region"]] = r["score"]

    for region in ss.regions_data:
        score = regions_dict.get(region["region"], 70.0)
        map_data.append({
            "region": region["region"], 
            "lat": region["lat"], 
            "lon": region["lon"], 
            "score": score
        })

    if map_data:
        df_map = pd.DataFrame(map_data)

        def get_color(score):
            if score >= 70: return "#52C41A"  # Green - Stable
            elif score >= 50: return "#FAAD14"  # Orange - Slight Decline
            else: return "#FF4D4F"  # Red - Unstable

        df_map["color"] = df_map["score"].apply(get_color)

        fig = go.Figure()
        for color_val in df_map["color"].unique():
            dfc = df_map[df_map["color"] == color_val]
            if not dfc.empty:
                fig.add_trace(go.Scattergeo(
                    lon=dfc["lon"], 
                    lat=dfc["lat"],
                    text=dfc["region"] + "<br>CHI: " + dfc["score"].round(1).astype(str) + "<br>Last update: " + datetime.now().strftime("%I:%M %p"),
                    mode="markers",
                    marker=dict(
                        size=35, 
                        color=color_val, 
                        line=dict(width=3, color="white"), 
                        opacity=0.9
                    ),
                    name=f"CHI {dfc['score'].min():.0f}-{dfc['score'].max():.0f}",
                    hovertemplate="<b>%{text}</b><extra></extra>"
                ))
        
        fig.update_layout(
            geo=dict(
                scope="usa", 
                projection_type="albers usa", 
                showland=True, 
                landcolor="#F8F8F8",
                countrycolor="#E5E7EB", 
                coastlinecolor="#E5E7EB", 
                lakecolor="#FFFFFF"
            ),
            height=500, 
            margin=dict(l=0, r=0, t=0, b=0), 
            plot_bgcolor="white", 
            paper_bgcolor="white", 
            showlegend=True,
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#E5E7EB",
                borderwidth=1
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    # Anomaly Detection
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Anomaly Detection")
    alerts_data = api_get("/alerts")
    if alerts_data and alerts_data.get("alerts"):
        for alert in alerts_data["alerts"][:5]:
            ts = format_timestamp(alert.get('ts', ''))
            chi_drop = alert.get('chi_before', 0) - alert.get('chi_after', 0)
            confidence = min(95, max(75, int(chi_drop * 2 + 75)))
            
            st.markdown(f"""
                <div class="alert-card">
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <div>
                            <strong style="color:#E20074; text-transform:uppercase; letter-spacing:0.5px;">{ts} Shift-detected</strong>
                            <div style="color:#000000; margin-top:0.5rem; font-size:0.9rem;">{alert.get('reason', 'N/A')}</div>
                        </div>
                        <div style="color:#E20074; font-weight:700; font-size:1.1rem;">{confidence}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("✅ No anomalies detected at this time.")

# ---------------- Alerts & Anomalies Page ----------------
elif ss.current_page == "Alerts":
    st.markdown("### Alerts & Anomalies")
    
# Filters
    region_options = ["All"] + [r["region"] for r in (regions_summary.get("regions", []) if regions_summary else [])]
    fcol1, fcol2, fcol3 = st.columns([1, 1, 1])
    with fcol1:
        sel_region = st.selectbox("Region", options=region_options, index=0, key="alerts_region")
    with fcol2:
        start_date = st.date_input("Start date", value=None, key="alerts_start")
    with fcol3:
        end_date = st.date_input("End date", value=None, key="alerts_end")
    
    params = {}
    if sel_region and sel_region != "All":
        params["region"] = sel_region
    if start_date:
        params["start"] = f"{start_date}T00:00:00"
    if end_date:
        params["end"] = f"{end_date}T23:59:59"
    
    alerts_data = api_get("/alerts", params=params)
    
    if alerts_data and alerts_data.get("alerts"):
        alerts = alerts_data["alerts"]
        
        # Summary KPIs
        col1, col2, col3 = st.columns(3)
        with col1: 
            st.metric("Total Alerts", len(alerts))
        with col2:
            recent_alerts = [a for a in alerts if pd.to_datetime(a.get('ts', '2000-01-01')) > pd.Timestamp.now() - pd.Timedelta(hours=24)]
            st.metric("Last 24h", len(recent_alerts))
        with col3: 
            st.metric("Regions Affected", len(set(a.get('region', '') for a in alerts)))
        
            st.divider()

        # Alert Cards
        for alert in alerts[:50]:
            ts = format_timestamp(alert.get('ts', ''))
            chi_before = alert.get('chi_before', 0)
            chi_after = alert.get('chi_after', 0)
            chi_drop = chi_before - chi_after
            
            st.markdown(f"""
                <div class="alert-card">
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <div>
                            <strong style="color:#E20074; text-transform:uppercase; letter-spacing:0.5px;">{alert.get('region', 'Unknown')}</strong>
                            <div style="color:#5A5A5A; font-size:0.85rem; margin-top:0.25rem;">{ts}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="color:#5A5A5A; font-size:0.85rem; text-transform:uppercase;">CHI Drop</div>
                            <span style="color:#FF4D4F; font-weight:700; font-size:1.3rem;">
                                {chi_before:.1f} → {chi_after:.1f}
                            </span>
                        </div>
                    </div>
                    <div style="color:#000000; margin-top:0.75rem;"><strong>Reason:</strong> {alert.get('reason', 'N/A')}</div>
                    <div style="color:#5A5A5A; font-size:0.9rem; margin-top:0.5rem;"><strong>Recommendation:</strong> {alert.get('recommendation', 'N/A')}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("✅ No alerts at this time. All systems operating normally.")

# ---------------- Outages Page ----------------
elif ss.current_page == "Outages":
    st.markdown("### Simulate Outage and CHI Impact")

    regions_list = [r["region"] for r in (regions_summary.get("regions", []) if regions_summary else [])]
    col_a, col_b = st.columns(2)
    
    with col_a:
        sim_region = st.selectbox("Region", options=regions_list or ["Unknown"], index=0)
        impact = st.slider("Impact %", min_value=10, max_value=90, value=50, step=5)
        duration = st.slider("Duration (minutes)", min_value=5, max_value=120, value=30, step=5)
        event_rate = st.slider("Event Rate (per minute)", min_value=1, max_value=10, value=3, step=1)
    
    with col_b:
        st.markdown("**Baseline vs. Post‑simulation CHI**")
        baseline = api_get("/chi", {"region": sim_region}) or {}
        baseline_score = float(baseline.get("score", 0))
        st.metric("Baseline CHI", f"{baseline_score:.1f}")
        
        run = st.button("Simulate Outage", use_container_width=True, type="primary")
        
        if run:
            with st.spinner("Simulating outage and recomputing CHI..."):
                resp = api_post("/simulate", {
                    "region": sim_region,
                    "impact_percent": int(impact),
                    "duration_minutes": int(duration),
                    "event_rate_per_minute": int(event_rate),
                }) or {}
                updated = api_get("/chi", {"region": sim_region}) or {}
                updated_score = float(updated.get("score", baseline_score))
                delta = updated_score - baseline_score
                
                # Metrics row
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.metric("CHI Before", f"{baseline_score:.1f}")
                with m2: st.metric("CHI After", f"{updated_score:.1f}", delta=f"{delta:+.1f}")
                drop_abs = baseline_score - updated_score
                with m3: st.metric("CHI Drop", f"{drop_abs:.1f}", delta=f"{-drop_abs:.1f}")
                with m4: st.metric("Alerts Generated", int(resp.get("alerts_created", 0)))

                # Line chart showing drop and recovery
                forecast = baseline.get("forecast", [])
                if forecast:
                    times = [pd.to_datetime(t) for t, _ in forecast]
                    scores = [s for _, s in forecast]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=times,
                        y=scores,
                        mode='lines+markers',
                        name='Predicted CHI',
                        line=dict(color='#E20074', width=3),
                        marker=dict(size=8)
                    ))
                    fig.add_trace(go.Scatter(
                        x=[times[0], times[-1]],
                        y=[baseline_score, updated_score],
                        mode='markers',
                        name='Actual',
                        marker=dict(size=12, color='#FF4D4F', symbol='circle')
                    ))
                    fig.update_layout(
                        title="CHI Drop and Recovery Curve",
                        xaxis_title="Time",
                        yaxis_title="CHI Score",
                        height=400,
                        template="plotly_white",
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                st.caption("Tip: Check the Alerts tab for AI-powered recommendations addressing this outage.")

# ---------------- Region Map Page ----------------
elif ss.current_page == "Region Map":
    st.markdown("### Regional CHI Map")
    
    regions_summary = api_get("/regions")
    regions_dict = {}
    if regions_summary:
        for r in regions_summary.get("regions", []):
            regions_dict[r["region"]] = r["score"]

    map_data = []
    for region in ss.regions_data:
        score = regions_dict.get(region["region"], 70.0)
        map_data.append({
            "region": region["region"], 
            "lat": region["lat"], 
            "lon": region["lon"], 
            "score": score
        })

    if map_data:
        df_map = pd.DataFrame(map_data)

        def get_color(score):
            if score >= 70: return "#52C41A"
            elif score >= 50: return "#FAAD14"
            else: return "#FF4D4F"

        df_map["color"] = df_map["score"].apply(get_color)

        fig = go.Figure()
        for color_val in df_map["color"].unique():
            dfc = df_map[df_map["color"] == color_val]
            if not dfc.empty:
                # Get forecast for tooltip
                forecast_data = api_get("/chi", {"region": dfc.iloc[0]["region"]}) or {}
                forecast = forecast_data.get("forecast", [])
                pred_chi = forecast[0][1] if forecast else dfc.iloc[0]["score"]
                
                fig.add_trace(go.Scattergeo(
                    lon=dfc["lon"], 
                    lat=dfc["lat"],
                    text=dfc["region"] + "<br>Current CHI: " + dfc["score"].round(1).astype(str) + 
                         "<br>Predicted CHI (1h): " + f"{pred_chi:.1f}" +
                         "<br>Trend: " + ("↗ improving" if pred_chi > dfc.iloc[0]["score"] else "↘ declining"),
                    mode="markers",
                    marker=dict(
                        size=40, 
                        color=color_val, 
                        line=dict(width=3, color="white"), 
                        opacity=0.9
                    ),
                    name=f"CHI {dfc['score'].min():.0f}-{dfc['score'].max():.0f}",
                    hovertemplate="<b>%{text}</b><extra></extra>"
                ))
        
        fig.update_layout(
            geo=dict(
                scope="usa", 
                projection_type="albers usa", 
                showland=True, 
                landcolor="#F8F8F8",
                countrycolor="#E5E7EB"
            ),
            height=700, 
            margin=dict(l=0, r=0, t=0, b=0), 
            plot_bgcolor="white", 
            paper_bgcolor="white",
            legend=dict(
                x=0.02,
                y=0.02,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#E5E7EB",
                borderwidth=1
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        # Region Details Table
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Region Details")
        df_display = df_map[["region", "score"]].copy()
        df_display.columns = ["Region", "CHI Score"]
        df_display = df_display.sort_values("CHI Score", ascending=False)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
