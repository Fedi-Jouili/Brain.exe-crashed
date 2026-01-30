"""
Session State Management
"""

import streamlit as st
from typing import Dict, Any


def init_session_state():
    """Initialize session state variables"""
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {}

    if "recent_searches" not in st.session_state:
        st.session_state.recent_searches = []

    if "search_history" not in st.session_state:
        st.session_state.search_history = []


def save_user_profile(profile: Dict[str, Any]):
    """Save user profile to session state"""
    st.session_state.user_profile = profile


def get_user_profile() -> Dict[str, Any]:
    """Get user profile from session state"""
    return st.session_state.get("user_profile", {})


def add_recent_search(query: str):
    """Add query to recent searches"""
    if "recent_searches" not in st.session_state:
        st.session_state.recent_searches = []

    if query and query not in st.session_state.recent_searches:
        st.session_state.recent_searches.append(query)

        # Keep only last 10
        if len(st.session_state.recent_searches) > 10:
            st.session_state.recent_searches = st.session_state.recent_searches[-10:]
