import streamlit as st
import requests
import json
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime
import pandas as pd
import html

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
    
    /* Chat container styling */
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 0.5rem 0;
    }
    .chat-container::-webkit-scrollbar {
        width: 6px;
    }
    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }
    .chat-container::-webkit-scrollbar-thumb {
        background: #E20074;
        border-radius: 3px;
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
    nav_items = ["Overview", "Alerts", "Outages", "Region Map"]
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

    # Chat input form
    with st.form("ai_form", clear_on_submit=True):
        q = st.text_input("Ask a question", placeholder="e.g., Why is Midwest lower today?", label_visibility="collapsed")
        submitted = st.form_submit_button("Ask", use_container_width=True, help="Send to AI")
    
    # Display responses directly below the input
    if submitted and q.strip():
        ts = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        ss.chat_history.append({"role": "user", "content": q.strip(), "ts": ts})

        with st.spinner("Thinking..."):
            result = api_post("/qa", {"question": q.strip()}) or {}
        # Expecting: {"summary": "...", "recommendations": ["...", "..."]} (graceful if missing)
        summary = result.get("summary") or "No summary available."
        recos = result.get("recommendations") or []

        bot_response = summary
        if recos:
            bot_response += "\n\n**Recommendations:**\n" + "\n".join([f"• {rec}" for rec in recos])
        
        ss.chat_history.append({"role": "bot", "content": bot_response, "ts": datetime.now().strftime("%Y-%m-%d %I:%M %p")})
        ss.ai_recommendations = recos
        st.rerun()

    # Display the most recent conversation exchange below the input
    if ss.chat_history:
        # Show the last exchange (user question + bot response)
        # Messages are added in order: user, then bot
        if len(ss.chat_history) >= 2:
            # Get the last two messages
            second_last = ss.chat_history[-2]
            last = ss.chat_history[-1]
            
            # Display user message (should be second to last)
            if second_last["role"] == "user":
                st.markdown(
                    f"""
                    <div style="background:#E20074; color:white; padding:0.6rem 0.8rem; border-radius:12px 12px 4px 12px; margin-top:0.5rem; margin-left:20%; text-align:right; word-wrap:break-word;">
                        <div style="font-size:0.85rem;">{html.escape(second_last['content']).replace(chr(10), '<br>')}</div>
                        <div style="font-size:0.7rem; opacity:0.8; margin-top:0.3rem;">{html.escape(second_last.get('ts',''))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Display bot response (should be last)
            if last["role"] == "bot":
                st.markdown(
                    f"""
                    <div style="background:#F3F4F6; color:#111827; padding:0.6rem 0.8rem; border-radius:12px 12px 12px 4px; margin-bottom:0.5rem; margin-right:20%; word-wrap:break-word;">
                        <div style="font-size:0.85rem;">{html.escape(last['content']).replace(chr(10), '<br>')}</div>
                        <div style="font-size:0.7rem; color:#6B7280; margin-top:0.3rem;">{html.escape(last.get('ts',''))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        elif len(ss.chat_history) == 1:
            # Only one message (user question waiting for response)
            msg = ss.chat_history[0]
            if msg["role"] == "user":
                st.markdown(
                    f"""
                    <div style="background:#E20074; color:white; padding:0.6rem 0.8rem; border-radius:12px 12px 4px 12px; margin-top:0.5rem; margin-left:20%; text-align:right; word-wrap:break-word;">
                        <div style="font-size:0.85rem;">{html.escape(msg['content']).replace(chr(10), '<br>')}</div>
                        <div style="font-size:0.7rem; opacity:0.8; margin-top:0.3rem;">{html.escape(msg.get('ts',''))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Show recommendations separately if available (from last response)
    if ss.ai_recommendations:
        st.markdown("**Latest Recommendations**")
        for rec in ss.ai_recommendations:
            st.markdown(f'<div class="ai-reco">{rec}</div>', unsafe_allow_html=True)

    # Conversation History in dropdown/expander
    with st.expander("Conversation history", expanded=False):
        if not ss.chat_history:
            st.caption("No messages yet.")
        else:
            # Display all messages in the conversation history
            for msg in ss.chat_history:
                if msg["role"] == "user":
                    # User message
                    st.markdown(
                        f"""
                        <div style="background:#E20074; color:white; padding:0.6rem 0.8rem; border-radius:12px 12px 4px 12px; margin-bottom:0.5rem; margin-left:20%; text-align:right; word-wrap:break-word;">
                            <div style="font-size:0.85rem;">{html.escape(msg['content']).replace(chr(10), '<br>')}</div>
                            <div style="font-size:0.7rem; opacity:0.8; margin-top:0.3rem;">{html.escape(msg.get('ts',''))}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    # Bot message
                    st.markdown(
                        f"""
                        <div style="background:#F3F4F6; color:#111827; padding:0.6rem 0.8rem; border-radius:12px 12px 12px 4px; margin-bottom:0.5rem; margin-right:20%; word-wrap:break-word;">
                            <div style="font-size:0.85rem;">{html.escape(msg['content']).replace(chr(10), '<br>')}</div>
                            <div style="font-size:0.7rem; color:#6B7280; margin-top:0.3rem;">{html.escape(msg.get('ts',''))}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

# ---------------------------------------------------------
# MAIN CONTENT
# ---------------------------------------------------------
st.title("T-Mobile Customer Happiness Index (MVP)")

# Get overall CHI data
regions_summary = api_get("/regions")
overall_chi = 0
overall_sentiment = 0.0
if regions_summary and regions_summary.get("regions"):
    scores = [r["score"] for r in regions_summary.get("regions", [])]
    overall_chi = sum(scores) / len(scores) if scores else 0
    
    # Calculate average sentiment from CHI data
    # Get sentiment from a sample of regions (optimized - only check first few)
    sentiment_scores = []
    sample_regions = regions_summary.get("regions", [])[:5]  # Sample first 5 regions for performance
    for region in sample_regions:
        region_name = region.get("region", "")
        if region_name:
            chi_data = api_get("/chi", params={"region": region_name})
            if chi_data and chi_data.get("drivers"):
                sentiment = chi_data["drivers"].get("sentiment", 0)
                if sentiment and sentiment != 0:
                    sentiment_scores.append(sentiment)
    
    if sentiment_scores:
        overall_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    else:
        # Default to a positive sentiment based on CHI score (higher CHI = more positive sentiment)
        # CHI ranges roughly 0-100, sentiment ranges -1 to 1
        # Map CHI to sentiment: 0 CHI = -0.5 sentiment, 100 CHI = 0.5 sentiment
        overall_sentiment = (overall_chi / 100.0) - 0.5 if overall_chi > 0 else 0.0

# ---------------- Overview ----------------
if ss.current_page == "Overview":
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card-large">
                <div style="font-size: .9rem; color:#666; margin-bottom:.5rem;">Overall Customer Happiness Index</div>
                <div style="font-size: 4rem; font-weight:700; color:#E20074; margin-bottom:1rem;">{overall_chi:.0f}</div>
                <div style="color:#10B981; font-size:.9rem; margin-bottom:1rem;">^ Happy</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Convert sentiment (-1 to 1) to a 0-100 score
        sentiment_score = ((overall_sentiment + 1) / 2) * 100
        sentiment_label = "Positive" if overall_sentiment > 0.1 else "Neutral" if overall_sentiment > -0.1 else "Negative"
        sentiment_color = "#10B981" if overall_sentiment > 0.1 else "#6B7280" if overall_sentiment > -0.1 else "#DC2626"
        
        st.markdown(f"""
            <div class="metric-card-large">
                <div style="font-size: .9rem; color:#666; margin-bottom:.5rem;">Sentiment analysis (AI-driven)</div>
                <div style="font-size: 3rem; font-weight:700; color:#E20074; margin-bottom:0.5rem;">{sentiment_score:.0f}%</div>
                <div style="color:{sentiment_color}; font-size:.9rem; margin-bottom:1rem;">{sentiment_label}</div>
                <div style="font-size: 0.85rem; color:#666; margin-top:1rem; line-height:1.5;">
                    <div style="margin-bottom:0.4rem;">📞 Call transcripts</div>
                    <div style="margin-bottom:0.4rem;">💬 Chat logs</div>
                    <div style="margin-bottom:0.4rem;">🎫 Ticket notes</div>
                    <div style="margin-bottom:0.4rem;">📊 Overall CHI</div>
                </div>
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
    
    # Get alerts data with AI recommendations
    alerts_data = api_get("/alerts", params={"include_ai_recommendations": "true"})
    all_alerts = alerts_data.get("alerts", []) if alerts_data else []
    
    # Get unique regions from alerts and regions data
    available_regions = sorted(set(a.get('region', '') for a in all_alerts if a.get('region')))
    if ss.regions_data:
        region_names = sorted(set(r.get('region', '') for r in ss.regions_data if r.get('region')))
        available_regions = sorted(set(available_regions + region_names))
    
    # Filter controls
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        selected_region = st.selectbox(
            "Filter by Region",
            options=["All Regions"] + available_regions,
            key="alert_region_filter"
        )
    
    with filter_col2:
        date_filter_option = st.selectbox(
            "Filter by Date",
            options=["All Dates", "Today", "Last 7 days", "Last 30 days", "Custom Range"],
            key="alert_date_filter_option"
        )
    
    # Custom date range input (appears below when selected)
    date_range = None
    if date_filter_option == "Custom Range":
        default_start = (pd.Timestamp.now() - pd.Timedelta(days=7)).date()
        default_end = pd.Timestamp.now().date()
        date_range = st.date_input(
            "Select Date Range",
            value=(default_start, default_end),
            key="alert_date_range"
        )
    
    # Apply filters
    filtered_alerts = all_alerts.copy()
    
    # Region filter
    if selected_region != "All Regions":
        filtered_alerts = [a for a in filtered_alerts if a.get('region', '') == selected_region]
    
    # Date filter
    if date_filter_option == "Today":
        today = pd.Timestamp.now().normalize()
        filtered_alerts = [a for a in filtered_alerts if pd.to_datetime(a.get('ts', '2000-01-01')).normalize() == today]
    elif date_filter_option == "Last 7 days":
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=7)
        filtered_alerts = [a for a in filtered_alerts if pd.to_datetime(a.get('ts', '2000-01-01')) >= cutoff]
    elif date_filter_option == "Last 30 days":
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
        filtered_alerts = [a for a in filtered_alerts if pd.to_datetime(a.get('ts', '2000-01-01')) >= cutoff]
    elif date_filter_option == "Custom Range" and date_range:
        try:
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date = pd.Timestamp(date_range[0])
                end_date = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)  # Include the end date
                filtered_alerts = [
                    a for a in filtered_alerts 
                    if start_date <= pd.to_datetime(a.get('ts', '2000-01-01')) < end_date
                ]
        except Exception:
            # If date range parsing fails, show all alerts
            pass
    
    # Display metrics and alerts
    if filtered_alerts:
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Total Alerts", len(filtered_alerts))
        with col2:
            recent_alerts = [a for a in filtered_alerts if pd.to_datetime(a.get('ts', '2000-01-01')) > pd.Timestamp.now() - pd.Timedelta(hours=24)]
            st.metric("Last 24h", len(recent_alerts))
        with col3: st.metric("Regions Affected", len(set(a.get('region', '') for a in filtered_alerts)))
        st.divider()

        for alert in filtered_alerts[:50]:
            alert_id = alert.get('id')
            ts = alert.get('ts', '')
            if ts:
                try:
                    ts_formatted = pd.to_datetime(ts).strftime("%Y-%m-%d %I:%M %p")
                except:
                    ts_formatted = ts[:19] if len(ts) > 19 else ts
            else:
                ts_formatted = ""
            
            # Alert header (always visible)
            st.markdown(f"""
                <div style="background:#FFF5F9; border-left:4px solid #E20074; padding:1rem; border-radius:4px; margin-bottom:.75rem; cursor:pointer;">
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
                    <div style="color:#333; margin-top:.75rem;"><strong>Reason:</strong> {html.escape(str(alert.get('reason', 'N/A')))}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Quick AI Recommendations (always visible)
            ai_recommendations = alert.get('ai_recommendations', [])
            if ai_recommendations:
                st.markdown("""
                    <div style="margin-top:.5rem; margin-bottom:.75rem; padding:.75rem; background:#F0FDF4; border-left:3px solid #10B981; border-radius:4px;">
                        <div style="color:#10B981; font-weight:600; font-size:.85rem; margin-bottom:.5rem;">🤖 AI-Powered Recommendations</div>
                        <ul style="margin:0; padding-left:1.2rem; color:#333; font-size:.9rem;">
                """, unsafe_allow_html=True)
                for rec in ai_recommendations:
                    st.markdown(f'<li style="margin-bottom:.4rem;">{html.escape(str(rec))}</li>', unsafe_allow_html=True)
                st.markdown("</ul></div>", unsafe_allow_html=True)
            
            # Standard Recommendations section
            standard_recs = alert.get('recommendation', [])
            if standard_recs:
                if not isinstance(standard_recs, list):
                    standard_recs = [standard_recs]
                st.markdown("""
                    <div style="margin-top:.5rem; margin-bottom:.75rem; padding:.75rem; background:#FFF5F9; border-left:3px solid #E20074; border-radius:4px;">
                        <div style="color:#E20074; font-weight:600; font-size:.85rem; margin-bottom:.5rem;">📋 Standard Recommendations</div>
                        <ul style="margin:0; padding-left:1.2rem; color:#333; font-size:.9rem;">
                """, unsafe_allow_html=True)
                for rec in standard_recs:
                    st.markdown(f'<li style="margin-bottom:.4rem;">{html.escape(str(rec))}</li>', unsafe_allow_html=True)
                st.markdown("</ul></div>", unsafe_allow_html=True)
            
            # Detailed Analysis Expander
            if alert_id:
                with st.expander("🔍 View Detailed AI Analysis", expanded=False):
                    # Check if we have cached analysis for this alert
                    analysis_key = f"alert_analysis_{alert_id}"
                    if analysis_key not in ss:
                        with st.spinner("Generating detailed AI analysis..."):
                            analysis_data = api_get(f"/alerts/{alert_id}/analysis")
                            if analysis_data:
                                ss[analysis_key] = analysis_data
                            else:
                                st.error("Failed to load detailed analysis.")
                                continue
                    else:
                        analysis_data = ss[analysis_key]
                    
                    if analysis_data:
                        # Detailed Analysis Section
                        st.markdown("### 📊 Detailed Analysis")
                        analysis_text = analysis_data.get('analysis', 'Analysis unavailable.')
                        st.markdown(f"""
                            <div style="background:#F8F9FA; padding:1rem; border-radius:6px; margin-bottom:1rem; line-height:1.6;">
                        """, unsafe_allow_html=True)
                        st.markdown(analysis_text)
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Root Causes
                        root_causes = analysis_data.get('root_causes', [])
                        if root_causes:
                            st.markdown("### 🔍 Root Causes")
                            st.markdown("""
                                <ul style="line-height:1.8;">
                            """, unsafe_allow_html=True)
                            for cause in root_causes:
                                st.markdown(f'<li style="margin-bottom:.5rem;">{html.escape(str(cause))}</li>', unsafe_allow_html=True)
                            st.markdown("</ul>", unsafe_allow_html=True)
                        
                        # Impact Assessment
                        impact = analysis_data.get('impact_assessment', '')
                        if impact:
                            st.markdown("### ⚠️ Impact Assessment")
                            st.markdown("""
                                <div style="background:#FEF3C7; padding:1rem; border-left:4px solid #F59E0B; border-radius:4px; line-height:1.6;">
                            """, unsafe_allow_html=True)
                            st.markdown(impact)
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Detailed Recommendations
                        detailed_recs = analysis_data.get('recommendations', [])
                        if detailed_recs:
                            st.markdown("### 🎯 Tailored Action Plan")
                            st.markdown("""
                                <div style="background:#ECFDF5; padding:1rem; border-left:4px solid #10B981; border-radius:4px;">
                                    <ol style="line-height:1.8; padding-left:1.5rem;">
                            """, unsafe_allow_html=True)
                            for i, rec in enumerate(detailed_recs, 1):
                                st.markdown(f'<li style="margin-bottom:.75rem; font-weight:500;">{html.escape(str(rec))}</li>', unsafe_allow_html=True)
                            st.markdown("</ol></div>", unsafe_allow_html=True)
        
        if len(filtered_alerts) > 50:
            st.info(f"Showing 50 of {len(filtered_alerts)} alerts. Apply filters to narrow results.")
    else:
        if all_alerts:
            st.info("No alerts match the selected filters. Try adjusting your filter criteria.")
        else:
            st.info("✅ No alerts at this time. All systems operating normally.")

# ---------------- Outages (Simulator) ----------------
elif ss.current_page == "Outages":
    st.markdown("### Outage Simulator")
    st.markdown("Simulate an outage to see the potential impact on Customer Happiness Index (CHI)")
    
    # Get available regions
    regions_summary = api_get("/regions")
    available_regions = []
    if regions_summary and regions_summary.get("regions"):
        available_regions = [r["region"] for r in regions_summary.get("regions", [])]
    elif ss.regions_data:
        available_regions = [r.get("region", "") for r in ss.regions_data if r.get("region")]
    
    if not available_regions:
        st.warning("No regions available. Please seed data first.")
    else:
        # Simulation form
        with st.form("outage_simulator", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                selected_region = st.selectbox(
                    "Select Region",
                    options=available_regions,
                    key="sim_region"
                )
                
                impact_percent = st.slider(
                    "Impact Percentage",
                    min_value=10,
                    max_value=90,
                    value=50,
                    step=10,
                    help="Percentage of network degradation (affects download speed and latency)",
                    key="sim_impact"
                )
            
            with col2:
                duration_minutes = st.number_input(
                    "Duration (minutes)",
                    min_value=5,
                    max_value=120,
                    value=30,
                    step=5,
                    help="How long the outage should last",
                    key="sim_duration"
                )
                
                event_rate = st.number_input(
                    "Event Rate (per minute)",
                    min_value=1,
                    max_value=10,
                    value=3,
                    step=1,
                    help="Number of negative events generated per minute",
                    key="sim_rate"
                )
            
            submitted = st.form_submit_button("🚨 Simulate Outage", use_container_width=True, type="primary")
        
        # Get current CHI before simulation
        current_chi_data = None
        chi_before = 0
        if selected_region:
            current_chi_data = api_get("/chi", params={"region": selected_region})
            chi_before = current_chi_data.get("score", 0) if current_chi_data else 0
        
        # Run simulation
        if submitted and selected_region:
            with st.spinner("Simulating outage and calculating impact..."):
                # Run simulation
                sim_result = api_post("/simulate", {
                    "region": selected_region,
                    "impact_percent": impact_percent,
                    "duration_minutes": duration_minutes,
                    "event_rate_per_minute": event_rate
                })
                
                if sim_result:
                    # Get CHI after simulation
                    chi_after_data = api_get("/chi", params={"region": selected_region})
                    chi_after = chi_after_data.get("score", 0) if chi_after_data else 0
                    chi_drop = chi_before - chi_after
                    
                    # Display results
                    st.success("✅ Outage simulation completed!")
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("CHI Before", f"{chi_before:.1f}")
                    with col2:
                        st.metric("CHI After", f"{chi_after:.1f}")
                    with col3:
                        st.metric("CHI Drop", f"{chi_drop:.1f}", delta=f"-{chi_drop:.1f}")
                    with col4:
                        alerts_created = sim_result.get("alerts_created", 0)
                        st.metric("Alerts Generated", alerts_created)
                    
                    # Visual comparison
                    st.markdown("### Impact Visualization")
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        name="Before Outage",
                        x=["CHI Score"],
                        y=[chi_before],
                        marker_color="#10B981",
                        text=[f"{chi_before:.1f}"],
                        textposition="outside"
                    ))
                    fig.add_trace(go.Bar(
                        name="After Outage",
                        x=["CHI Score"],
                        y=[chi_after],
                        marker_color="#DC2626",
                        text=[f"{chi_after:.1f}"],
                        textposition="outside"
                    ))
                    fig.update_layout(
                        title="CHI Impact from Simulated Outage",
                        yaxis_title="CHI Score",
                        height=400,
                        showlegend=True,
                        plot_bgcolor="white",
                        paper_bgcolor="white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Impact summary
                    st.markdown("### Impact Summary")
                    if chi_drop > 10:
                        severity = "High"
                        color = "#DC2626"
                    elif chi_drop > 5:
                        severity = "Medium"
                        color = "#F59E0B"
                    else:
                        severity = "Low"
                        color = "#10B981"
                    
                    st.markdown(f"""
                        <div style="background:#F8F9FA; padding:1rem; border-radius:6px; border-left:4px solid {color};">
                            <div style="font-weight:600; margin-bottom:.5rem;">Severity: <span style="color:{color};">{severity}</span></div>
                            <div style="color:#666; font-size:.9rem;">
                                The simulated outage resulted in a CHI drop of <strong>{chi_drop:.1f} points</strong> in the <strong>{selected_region}</strong> region.
                                This represents a <strong>{((chi_drop/chi_before)*100):.1f}%</strong> decrease in customer happiness.
                            </div>
                            {f'<div style="margin-top:.5rem; color:#DC2626; font-weight:600;">⚠️ {alerts_created} alert(s) were generated due to this outage.</div>' if alerts_created > 0 else ''}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Show alerts if any were created
                    if alerts_created > 0:
                        st.markdown("### Generated Alerts")
                        alerts_data = api_get("/alerts", params={"include_ai_recommendations": "true"})
                        if alerts_data and alerts_data.get("alerts"):
                            # Show alerts for this region
                            region_alerts = [a for a in alerts_data["alerts"] if a.get("region") == selected_region]
                            for alert in region_alerts[:5]:  # Show up to 5 most recent
                                st.markdown(f"""
                                    <div style="background:#FFF5F9; border-left:4px solid #E20074; padding:.75rem; border-radius:4px; margin-bottom:.5rem;">
                                        <strong style="color:#E20074;">{alert.get('region', 'Unknown')}</strong>
                                        <div style="color:#666; font-size:.85rem; margin-top:.25rem;">{alert.get('reason', 'N/A')}</div>
                                        <div style="color:#DC2626; font-size:.9rem; margin-top:.25rem;">
                                            CHI: {alert.get('chi_before', 0):.1f} → {alert.get('chi_after', 0):.1f}
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                    
                    st.info("💡 Tip: Check the Alerts page to see detailed AI-powered recommendations for addressing this outage.")
                else:
                    st.error("Failed to run simulation. Please try again.")
        
        # Show current CHI if region is selected but simulation hasn't run
        elif selected_region and not submitted:
            if current_chi_data:
                st.markdown("### Current Status")
                st.metric("Current CHI", f"{chi_before:.1f}", help="Current Customer Happiness Index for this region")

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
