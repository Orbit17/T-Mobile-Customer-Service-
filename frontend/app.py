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
# T-Mobile styling (floating chatbot CSS removed)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .nav-item { padding: 0.75rem 1rem; margin: 0.25rem 0; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
    .nav-item:hover { background-color: #F8F9FA; }
    .nav-item.active { background-color: #E20074; color: white; }

    .metric-card-large {
        background: white; padding: 2rem; border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid #E20074;
    }
    .metric-card-small {
        background: white; padding: 1rem; border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;
    }

    /* Sidebar AI section */
    .ai-header { font-weight: 700; color: #111827; }
    .ai-title-pill {
        display:inline-block; padding: .35rem .6rem; border-radius: 9999px;
        background:#FDF2F8; color:#E20074; font-weight:600; font-size:.85rem;
        border:1px solid #FCE7F3;
    }
    .ai-ask-btn button { background:#E20074 !important; color:white !important; border:none !important; }
    .ai-ask-btn button:hover { background:#C1005F !important; }
    .ai-reco {
        background:#FFF5F9; border-left:3px solid #E20074;
        padding:.6rem .8rem; border-radius:6px; margin-bottom:.5rem; font-size:.92rem;
    }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
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
ss.setdefault("chat_history", [])  # [{role: 'user'|'bot', content:str, ts:str}]
ss.setdefault("ai_recommendations", [])  # list[str]

# ---------------------------------------------------------
# API helpers
# ---------------------------------------------------------
def api_get(endpoint, params=None):
    try:
        url = f"{ss.api_url}{endpoint}"
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
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

# ---------------------------------------------------------
# SIDEBAR: Nav + Embedded AI
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div style="text-align:center; padding:1.5rem 0;"><h1 style="color:#E20074; margin:0; font-size:1.5rem;">T-Mobile</h1></div>',
        unsafe_allow_html=True
    )
    st.divider()

    # Navigation
    nav_items = ["Overview", "Alerts", "Outages", "Report", "Region Map"]
    for item in nav_items:
        is_active = ss.current_page == item
        btn_type = "primary" if is_active else "secondary"
        if st.button(item, key=f"nav_{item}", use_container_width=True, type=btn_type):
            ss.current_page = item
            st.rerun()

    st.divider()

    # ---------- Embedded AI (minimal) ----------
    st.markdown('<div class="ai-header">AI Support</div>', unsafe_allow_html=True)
    st.markdown('<span class="ai-title-pill">Happiness Index Assistant</span>', unsafe_allow_html=True)
    st.write("")  # small spacer

    with st.form("ai_form", clear_on_submit=True):
        q = st.text_input("Ask a question", placeholder="e.g., Why is Midwest lower today?", label_visibility="collapsed")
        submitted = st.form_submit_button("Ask", use_container_width=True, help="Send to AI")
    if submitted and q.strip():
        ts = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        ss.chat_history.append({"role": "user", "content": q.strip(), "ts": ts})

        with st.spinner("Thinking..."):
            result = api_post("/qa", {"question": q.strip()}) or {}
        # Expecting: {"summary": "...", "recommendations": ["...", "..."]} (graceful if missing)
        summary = result.get("summary") or "No summary available."
        recos = result.get("recommendations") or []

        ss.chat_history.append({"role": "bot", "content": summary, "ts": datetime.now().strftime("%Y-%m-%d %I:%M %p")})
        ss.ai_recommendations = recos
        st.experimental_rerun()

    # Recommendations (if any)
    if ss.ai_recommendations:
        st.markdown("**AI Recommendations**")
        for rec in ss.ai_recommendations:
            st.markdown(f'<div class="ai-reco">{rec}</div>', unsafe_allow_html=True)

    # Conversation History in dropdown
    with st.expander("Conversation history"):
        if not ss.chat_history:
            st.caption("No messages yet.")
        else:
            for msg in ss.chat_history[-200:]:  # limit to last 200
                who = "You" if msg["role"] == "user" else "Assistant"
                color = "#111827" if msg["role"] == "user" else "#6B7280"
                st.markdown(f"**{who}**  \n<span style='color:{color}'>{msg['content']}</span>  \n<small>{msg.get('ts','')}</small>", unsafe_allow_html=True)

# ---------------------------------------------------------
# MAIN CONTENT
# ---------------------------------------------------------
st.title("T-Mobile Customer Happiness Index (MVP)")

# Get overall CHI data
regions_summary = api_get("/regions")
overall_chi = 0
if regions_summary and regions_summary.get("regions"):
    scores = [r["score"] for r in regions_summary.get("regions", [])]
    overall_chi = sum(scores) / len(scores) if scores else 0

# ---------------- Overview ----------------
if ss.current_page == "Overview":
    col_main, col_metrics = st.columns([2, 3])

    with col_main:
        st.markdown(f"""
            <div class="metric-card-large">
                <div style="font-size: .9rem; color:#666; margin-bottom:.5rem;">Overall Customer Happiness Index</div>
                <div style="font-size: 4rem; font-weight:700; color:#E20074; margin-bottom:1rem;">{overall_chi:.0f}</div>
                <div style="color:#10B981; font-size:.9rem; margin-bottom:1rem;">^ Happy</div>
            </div>
        """, unsafe_allow_html=True)

        if regions_summary and regions_summary.get("regions"):
            trend_data = pd.DataFrame({
                'time': pd.date_range(end=pd.Timestamp.now(), periods=12, freq='5min'),
                'chi': [overall_chi + (i * 0.5) for i in range(12)]
            })
            trend_fig = px.line(trend_data, x='time', y='chi',
                                color_discrete_sequence=["#E20074"], height=100)
            trend_fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
                xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False)
            )
            st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})

    with col_metrics:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
                <div class="metric-card-small">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #E20074;">78%</div>
                    <div style="color:#10B981; font-size:.85rem;">↑6%</div>
                    <div style="color:#666; font-size:.75rem; margin-top:.5rem;">Approval last week</div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("""
                <div class="metric-card-small" style="margin-top: 1rem;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #E20074;">72%</div>
                    <div style="color:#10B981; font-size:.85rem;">↑3</div>
                    <div style="color:#666; font-size:.75rem; margin-top:.5rem;">Average wait time</div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
                <div class="metric-card-small">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #E20074;">45</div>
                    <div style="color:#666; font-size:.75rem; margin-top:.5rem;">NPS First month</div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("""
                <div class="metric-card-small" style="margin-top: 1rem;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #E20074;">7.8M</div>
                    <div style="color:#DC2626; font-size:.85rem;">↓0.2M</div>
                    <div style="color:#666; font-size:.75rem; margin-top:.5rem;">Oct. price</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Region Map")

    # Map
    map_data = []
    regions_dict = {}
    if regions_summary:
        for r in regions_summary.get("regions", []):
            regions_dict[r["region"]] = r["score"]

    for region in ss.regions_data:
        score = regions_dict.get(region["region"], 70.0)
        map_data.append({"region": region["region"], "lat": region["lat"], "lon": region["lon"], "score": score})

    if map_data:
        df_map = pd.DataFrame(map_data)

        def get_color(score):
            if score > 70: return "#E20074"
            elif score > 50: return "#FF6B35"
            else: return "#DC2626"

        df_map["color"] = df_map["score"].apply(get_color)

        fig = go.Figure()
        for color_val in df_map["color"].unique():
            dfc = df_map[df_map["color"] == color_val]
            if not dfc.empty:
                fig.add_trace(go.Scattergeo(
                    lon=dfc["lon"], lat=dfc["lat"],
                    text=dfc["region"] + "<br>CHI: " + dfc["score"].round(1).astype(str),
                    mode="markers",
                    marker=dict(size=30, color=color_val, line=dict(width=3, color="white"), opacity=0.9),
                    name=f"CHI {dfc['score'].min():.0f}-{dfc['score'].max():.0f}"
                ))
        fig.update_layout(
            geo=dict(scope="usa", projection_type="albers usa", showland=True, landcolor="#F8F9FA",
                     countrycolor="#E5E7EB", coastlinecolor="#E5E7EB", lakecolor="#FFFFFF"),
            height=400, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor="white", paper_bgcolor="white", showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)

    # Anomaly Detection
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Anomaly Detection")
    alerts_data = api_get("/alerts")
    if alerts_data and alerts_data.get("alerts"):
        for alert in alerts_data["alerts"][:5]:
            ts = alert.get('ts', '')
            if ts:
                try:
                    ts_formatted = pd.to_datetime(ts).strftime("%I:%M %p")
                except:
                    ts_formatted = ts[:19] if len(ts) > 19 else ts
            else:
                ts_formatted = ""
            chi_drop = alert.get('chi_before', 0) - alert.get('chi_after', 0)
            confidence = min(95, max(75, int(chi_drop * 2 + 75)))
            st.markdown(f"""
                <div style="background:#FFF5F9; border-left:4px solid #E20074; padding:1rem; border-radius:4px; margin-bottom:.75rem;">
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <div>
                            <strong style="color:#E20074;">{ts_formatted} Shift-detected</strong>
                            <div style="color:#333; margin-top:.5rem; font-size:.9rem;">{alert.get('reason', 'N/A')}</div>
                        </div>
                        <div style="color:#E20074; font-weight:600;">{confidence}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No anomalies detected at this time.")

# ---------------- Alerts ----------------
elif ss.current_page == "Alerts":
    st.markdown("### Alerts & Anomalies")
    alerts_data = api_get("/alerts")
    if alerts_data and alerts_data.get("alerts"):
        alerts = alerts_data["alerts"]
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Total Alerts", len(alerts))
        with col2:
            recent_alerts = [a for a in alerts if pd.to_datetime(a.get('ts', '2000-01-01')) > pd.Timestamp.now() - pd.Timedelta(hours=24)]
            st.metric("Last 24h", len(recent_alerts))
        with col3: st.metric("Regions Affected", len(set(a.get('region', '') for a in alerts)))
        st.divider()

        for alert in alerts[:50]:
            ts = alert.get('ts', '')
            if ts:
                try:
                    ts_formatted = pd.to_datetime(ts).strftime("%Y-%m-%d %I:%M %p")
                except:
                    ts_formatted = ts[:19] if len(ts) > 19 else ts
            else:
                ts_formatted = ""
            st.markdown(f"""
                <div style="background:#FFF5F9; border-left:4px solid #E20074; padding:1rem; border-radius:4px; margin-bottom:.75rem;">
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <div>
                            <strong style="color:#E20074;">{alert.get('region', 'Unknown')}</strong>
                            <div style="color:#666; font-size:.85rem; margin-top:.25rem;">{ts_formatted}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="color:#666; font-size:.85rem;">CHI Drop</div>
                            <span style="color:#DC2626; font-weight:700; font-size:1.1rem;">
                                {alert.get('chi_before', 0):.1f} → {alert.get('chi_after', 0):.1f}
                            </span>
                        </div>
                    </div>
                    <div style="color:#333; margin-top:.75rem;"><strong>Reason:</strong> {alert.get('reason', 'N/A')}</div>
                    <div style="color:#666; font-size:.9rem; margin-top:.5rem;"><strong>Recommendation:</strong> {alert.get('recommendation', 'N/A')}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("✅ No alerts at this time. All systems operating normally.")

# ---------------- Outages ----------------
elif ss.current_page == "Outages":
    st.markdown("### Network Outages")
    st.info("Outage monitoring and management features will be displayed here.")

# ---------------- Report ----------------
elif ss.current_page == "Report":
    st.markdown("### Reports")
    st.info("Report generation and analytics will be displayed here.")

# ---------------- Region Map ----------------
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
        map_data.append({"region": region["region"], "lat": region["lat"], "lon": region["lon"], "score": score})

    if map_data:
        df_map = pd.DataFrame(map_data)

        def get_color(score):
            if score > 70: return "#E20074"
            elif score > 50: return "#FF6B35"
            else: return "#DC2626"

        df_map["color"] = df_map["score"].apply(get_color)

        fig = go.Figure()
        for color_val in df_map["color"].unique():
            dfc = df_map[df_map["color"] == color_val]
            if not dfc.empty:
                fig.add_trace(go.Scattergeo(
                    lon=dfc["lon"], lat=dfc["lat"],
                    text=dfc["region"] + "<br>CHI: " + dfc["score"].round(1).astype(str),
                    mode="markers",
                    marker=dict(size=35, color=color_val, line=dict(width=3, color="white"), opacity=0.9),
                    name=f"CHI {dfc['score'].min():.0f}-{dfc['score'].max():.0f}"
                ))
        fig.update_layout(
            geo=dict(scope="usa", projection_type="albers usa", showland=True, landcolor="#F8F9FA",
                     countrycolor="#E5E7EB"),
            height=600, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor="white", paper_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Region Details")
        df_display = df_map[["region", "score"]].copy()
        df_display.columns = ["Region", "CHI Score"]
        df_display = df_display.sort_values("CHI Score", ascending=False)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
