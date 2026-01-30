"""
Styling Utilities - Custom CSS and theming
"""

import streamlit as st


def load_custom_css():
    """Load custom CSS styles"""
    st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
    }

    /* Card styling */
    .stContainer {
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 5px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Metric styling */
    .stMetric {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 1rem;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: bold;
        border-radius: 5px;
    }

    /* Success/Error/Warning boxes */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 5px;
        padding: 1rem;
    }

    /* Product card improvements */
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    /* Footer styling */
    footer {
        visibility: hidden;
    }

    /* Header improvements */
    h1 {
        color: #1f77b4;
        font-weight: 700;
    }

    h2 {
        color: #2c3e50;
        font-weight: 600;
    }

    h3 {
        color: #34495e;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
