"""
FinCommerce Engine - Streamlit Frontend
Production-ready web application for AI-powered product recommendations
"""

import streamlit as st
from utils.api_client import APIClient
from utils.session_state import init_session_state
from utils.styling import load_custom_css

# Page configuration
st.set_page_config(
    page_title="FinCommerce Engine",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/fincommerce',
        'Report a bug': 'https://github.com/yourusername/fincommerce/issues',
        'About': '# FinCommerce Engine\nAI-Powered Smart Shopping Assistant'
    }
)

# Initialize
init_session_state()
load_custom_css()

# API Client
api = APIClient()

# Check backend health
health = api.get_health()

# Main page
st.title("🛒 FinCommerce Engine")
st.markdown("""
### AI-Powered Smart Shopping with Financial Intelligence

Welcome to FinCommerce Engine - the intelligent recommendation system that understands your budget.

**Features:**
- 🔍 **Smart Search**: Find products using text or images
- 💰 **Affordability Analysis**: Real-time budget checks
- 🎯 **Personalized Recommendations**: Powered by Thompson Sampling
- ⚡ **Lightning Fast**: 3-tier complexity routing (FAST/SMART/DEEP)
- 🤖 **AI Explanations**: Gemini 2.0 Flash-powered insights
""")

# System status
col1, col2, col3 = st.columns(3)

with col1:
    if health and health.get("status") == "healthy":
        st.success("✅ Backend Online")
    else:
        st.error("❌ Backend Offline")

with col2:
    if health:
        services = health.get("services", {})
        healthy_count = sum(1 for v in services.values() if "healthy" in str(v))
        st.info(f"🔧 {healthy_count}/{len(services)} Services Healthy")

with col3:
    if health:
        uptime = health.get("uptime_seconds", 0)
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        st.metric("⏱️ Uptime", f"{hours}h {minutes}m")

# Quick start guide
with st.expander("📖 Quick Start Guide"):
    st.markdown("""
    ### How to Use FinCommerce Engine

    1. **Set Up Your Profile** (👤 Profile page)
       - Enter your monthly income
       - Add your credit score
       - Set your budget preferences

    2. **Search for Products** (🔍 Search page)
       - Type what you're looking for
       - Upload an image (optional)
       - Get instant recommendations

    3. **Review Recommendations**
       - See affordability analysis
       - Read AI-generated explanations
       - Check alternative financing options

    4. **Interact with Products**
       - View, click, or purchase products
       - System learns from your actions (Thompson Sampling)
       - Future recommendations improve automatically

    5. **Monitor Performance** (📊 Dashboard page - Admin only)
       - View Thompson Sampling metrics
       - Check cache hit rates
       - Analyze system performance
    """)

# Navigation
st.markdown("---")
st.markdown("### 🚀 Get Started")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Start Searching", use_container_width=True):
        st.switch_page("pages/1_🔍_Search.py")

with col2:
    if st.button("👤 Setup Profile", use_container_width=True):
        st.switch_page("pages/2_👤_Profile.py")

with col3:
    if st.button("📊 View Dashboard", use_container_width=True):
        st.switch_page("pages/3_📊_Dashboard.py")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>FinCommerce Engine v1.0.0 | Powered by LangGraph, Thompson Sampling & Gemini 2.0 Flash</p>
    <p>Built with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
