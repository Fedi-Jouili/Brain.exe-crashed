"""
Dashboard Page - Admin metrics and monitoring
"""

import streamlit as st
from utils.api_client import APIClient
import time

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

api = APIClient()

st.title("📊 System Dashboard")

# Auto-refresh toggle
auto_refresh = st.checkbox("🔄 Auto-refresh (every 5s)", value=False)

if auto_refresh:
    time.sleep(5)
    st.rerun()

# Refresh button
if st.button("🔄 Refresh Now"):
    st.rerun()

# System Health
st.header("🏥 System Health")

health = api.get_health()

if health:
    status = health.get("status", "unknown")

    if status == "healthy":
        st.success(f"✅ System Status: {status.upper()}")
    else:
        st.warning(f"⚠️ System Status: {status.upper()}")

    # Service status
    st.subheader("🔧 Services")

    services = health.get("services", {})

    cols = st.columns(3)

    for i, (service, status_text) in enumerate(services.items()):
        with cols[i % 3]:
            if "healthy" in str(status_text):
                st.success(f"✅ {service}")
            else:
                st.error(f"❌ {service}")
            st.caption(str(status_text))
else:
    st.error("❌ Cannot connect to backend")

# Thompson Sampling Stats
st.markdown("---")
st.header("🎰 Thompson Sampling Statistics")

thompson_stats = api.get_thompson_stats()

if thompson_stats:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Products Tracked",
            thompson_stats.get("products_tracked", 0)
        )

    with col2:
        st.metric(
            "Avg Alpha (α)",
            f"{thompson_stats.get('avg_alpha', 0):.2f}"
        )

    with col3:
        st.metric(
            "Avg Beta (β)",
            f"{thompson_stats.get('avg_beta', 0):.2f}"
        )

    with col4:
        st.metric(
            "Avg Conversion",
            f"{thompson_stats.get('avg_conversion', 0):.3f}"
        )

    # Confidence distribution
    confidence = thompson_stats.get("confidence", {})
    if confidence:
        st.subheader("📊 Confidence Distribution")
        st.bar_chart(confidence)

# Cache Statistics
st.markdown("---")
st.header("⚡ Cache Performance")

cache_stats = api.get_cache_stats()

if cache_stats and cache_stats.get("cache_enabled"):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Keys",
            cache_stats.get("total_keys", 0)
        )

    with col2:
        st.metric(
            "Search Cache Keys",
            cache_stats.get("search_cache_keys", 0)
        )

    with col3:
        st.metric(
            "Memory Usage",
            f"{cache_stats.get('memory_usage_mb', 0):.2f} MB"
        )

    with col4:
        hit_rate = cache_stats.get("hit_rate_percent", 0)
        st.metric("Cache Hit Rate", f"{hit_rate:.1f}%")
else:
    st.warning("⚠️ Cache not enabled or stats unavailable")
