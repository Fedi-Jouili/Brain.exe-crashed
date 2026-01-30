"""
Search Page - Main product search interface
"""

import streamlit as st
from utils.api_client import APIClient
from utils.session_state import get_user_profile, add_recent_search
from components.product_card import render_product_card
import time

st.set_page_config(page_title="Search Products", page_icon="🔍", layout="wide")

api = APIClient()

st.title("🔍 Product Search")

# Sidebar - User Profile Quick View
with st.sidebar:
    st.header("👤 Your Profile")

    profile = get_user_profile()

    if profile.get("user_id"):
        st.success(f"Logged in as: **{profile['user_id']}**")
        st.metric("Monthly Income", f"${profile.get('monthly_income', 0):,.0f}")
        st.metric("Credit Score", profile.get('credit_score', 0))

        if st.button("Edit Profile"):
            st.switch_page("pages/2_👤_Profile.py")
    else:
        st.warning("⚠️ No profile set")
        st.info("Set up your profile for personalized affordability analysis")
        if st.button("Create Profile"):
            st.switch_page("pages/2_👤_Profile.py")

# Main search interface
col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "What are you looking for?",
        placeholder="e.g., laptop for programming, gaming headphones, 4K monitor",
        help="Enter keywords to search products. You can also upload an image below."
    )

with col2:
    max_results = st.select_slider(
        "Results",
        options=[5, 10, 15, 20],
        value=10,
        help="Number of recommendations to show"
    )

# Multimodal search - Image upload
st.markdown("### 🖼️ Image Search (Optional)")
uploaded_image = st.file_uploader(
    "Upload an image to find similar products",
    type=["jpg", "jpeg", "png", "webp"],
    help="Upload a product image to enable multimodal search (text + image)"
)

if uploaded_image:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
    with col2:
        st.info("✨ Multimodal search enabled! We'll find products similar to this image.")

# Search button
if st.button("🔍 Search Products", type="primary", use_container_width=True):
    if not query:
        st.error("⚠️ Please enter a search query")
    else:
        with st.spinner("🔄 Searching products..."):
            start_time = time.time()

            # Add to recent searches
            add_recent_search(query)

            # Prepare request
            search_request = {
                "query": query,
                "max_results": max_results
            }

            # Add user profile if available
            profile = get_user_profile()
            if profile.get("user_id"):
                search_request["user_profile"] = profile

            # Call API
            if uploaded_image:
                # Multimodal search with image
                results = api.search_with_image(
                    query=query,
                    image=uploaded_image,
                    max_results=max_results,
                    user_profile=profile if profile.get("user_id") else None
                )
            else:
                # Text-only search
                results = api.search(search_request)

            search_time = (time.time() - start_time) * 1000  # ms

            if results and results.get("recommendations"):
                recommendations = results["recommendations"]
                metadata = results.get("metadata", {})

                # Display results header
                st.success(f"✅ Found {len(recommendations)} recommendations in {search_time:.0f}ms")

                # Metadata badges
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    complexity = metadata.get("complexity_level", "UNKNOWN")
                    color = {"FAST": "🟢", "SMART": "🟡", "DEEP": "🔴"}.get(complexity, "⚪")
                    st.metric("Path", f"{color} {complexity}")

                with col2:
                    cache_hit = metadata.get("cache_hit", False)
                    st.metric("Cache", "✅ HIT" if cache_hit else "❌ MISS")

                with col3:
                    exec_time = metadata.get("execution_time_ms", 0)
                    st.metric("Execution", f"{exec_time}ms")

                with col4:
                    affordable = metadata.get("affordable_count", 0)
                    st.metric("Affordable", affordable)

                st.markdown("---")

                # Display products
                st.subheader("🎯 Recommended Products")

                for rec in recommendations:
                    render_product_card(rec, api)
                    st.markdown("---")

            else:
                st.error("❌ No results found. Try a different query.")

# Recent searches (stored in session state)
if "recent_searches" in st.session_state and st.session_state.recent_searches:
    with st.expander("🕒 Recent Searches"):
        for recent in st.session_state.recent_searches[-5:]:
            if st.button(f"🔄 {recent}", key=f"recent_{recent}"):
                st.session_state.search_query = recent
                st.rerun()
