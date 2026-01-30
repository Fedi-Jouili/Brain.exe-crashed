"""
Profile Page - User profile management
"""

import streamlit as st
from utils.session_state import save_user_profile, get_user_profile

st.set_page_config(page_title="User Profile", page_icon="👤", layout="wide")

st.title("👤 User Profile")

st.markdown("""
Set up your financial profile for personalized affordability analysis.
Your information is stored locally in this session only.
""")

# Load existing profile
profile = get_user_profile()

with st.form("profile_form"):
    st.subheader("📝 Basic Information")

    user_id = st.text_input(
        "User ID",
        value=profile.get("user_id", ""),
        placeholder="e.g., USER12345",
        help="Unique identifier for your profile"
    )

    st.subheader("💰 Financial Information")

    col1, col2 = st.columns(2)

    with col1:
        monthly_income = st.number_input(
            "Monthly Income ($)",
            min_value=0.0,
            value=float(profile.get("monthly_income", 0)),
            step=100.0,
            help="Your gross monthly income"
        )

        monthly_expenses = st.number_input(
            "Monthly Expenses ($)",
            min_value=0.0,
            value=float(profile.get("monthly_expenses", 0)),
            step=100.0,
            help="Your total monthly expenses"
        )

        savings = st.number_input(
            "Savings ($)",
            min_value=0.0,
            value=float(profile.get("savings", 0)),
            step=500.0,
            help="Your current savings"
        )

    with col2:
        credit_score = st.number_input(
            "Credit Score",
            min_value=300,
            max_value=850,
            value=int(profile.get("credit_score", 650)),
            help="Your credit score (300-850)"
        )

        current_debt = st.number_input(
            "Current Debt ($)",
            min_value=0.0,
            value=float(profile.get("current_debt", 0)),
            step=100.0,
            help="Your total current debt"
        )

        risk_tolerance = st.selectbox(
            "Risk Tolerance",
            options=["low", "medium", "high"],
            index=["low", "medium", "high"].index(profile.get("risk_tolerance", "medium")),
            help="Your financial risk tolerance"
        )

    submitted = st.form_submit_button("💾 Save Profile", use_container_width=True)

    if submitted:
        if not user_id:
            st.error("⚠️ User ID is required")
        elif monthly_income <= 0:
            st.error("⚠️ Monthly income must be greater than 0")
        else:
            # Save profile
            new_profile = {
                "user_id": user_id,
                "monthly_income": monthly_income,
                "monthly_expenses": monthly_expenses,
                "credit_score": credit_score,
                "savings": savings,
                "current_debt": current_debt,
                "risk_tolerance": risk_tolerance
            }

            save_user_profile(new_profile)
            st.success("✅ Profile saved successfully!")
            st.balloons()

# Display current profile
if profile.get("user_id"):
    st.markdown("---")
    st.subheader("📊 Your Profile Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Monthly Income", f"${profile.get('monthly_income', 0):,.0f}")

    with col2:
        st.metric("Credit Score", profile.get('credit_score', 0))

    with col3:
        disposable = profile.get('monthly_income', 0) - profile.get('monthly_expenses', 0)
        st.metric("Disposable Income", f"${disposable:,.0f}")

    with col4:
        dti = (profile.get('current_debt', 0) / profile.get('monthly_income', 1)) * 100 if profile.get('monthly_income', 0) > 0 else 0
        st.metric("DTI Ratio", f"{dti:.1f}%")
