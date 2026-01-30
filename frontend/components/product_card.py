"""
Product Card Component - Displays product with affordability and interactions
"""

import streamlit as st
from typing import Dict, Any


def render_product_card(recommendation: Dict[str, Any], api_client) -> None:
    """
    Render a product recommendation card.

    Args:
        recommendation: Recommendation dict from API
        api_client: API client for interactions
    """
    product = recommendation["product"]
    rank = recommendation["rank"]
    final_score = recommendation.get("final_score", 0)
    affordability = recommendation.get("affordability")
    explanation = recommendation.get("explanation", {})
    scores = recommendation.get("scores", {})

    # Container for card
    with st.container():
        # Header row
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            # Product image
            image_url = product.get("image_url")
            if image_url:
                st.image(image_url, use_column_width=True)
            else:
                st.info("No image")

        with col2:
            # Product details
            st.subheader(f"#{rank} {product['name']}")

            # Price and rating
            price = product.get("price", 0)
            rating = product.get("rating", 0)
            num_reviews = product.get("num_reviews", 0)

            st.markdown(f"""
            **💰 Price:** ${price:,.2f}
            **⭐ Rating:** {rating:.1f}/5 ({num_reviews:,} reviews)
            **📦 Category:** {product.get('category', 'Unknown')}
            **🏷️ Brand:** {product.get('brand', 'Unknown')}
            """)

            # Stock status
            if product.get("in_stock", True):
                st.success("✅ In Stock")
            else:
                st.error("❌ Out of Stock")

        with col3:
            # Final score
            st.metric("Score", f"{final_score:.1f}/100")

            # Affordability badge
            if affordability:
                render_affordability_badge(affordability)

        # Explanation
        if explanation and explanation.get("text"):
            with st.expander("💡 Why this recommendation?"):
                st.markdown(explanation["text"])

                # Trust indicators
                col1, col2, col3 = st.columns(3)
                with col1:
                    trust = explanation.get("trust", 0)
                    st.metric("Trust Score", f"{trust:.0%}")
                with col2:
                    verified = explanation.get("verified", False)
                    st.write("✅ Verified" if verified else "⚠️ Not Verified")
                with col3:
                    used_llm = explanation.get("used_llm", False)
                    st.write("🤖 AI Generated" if used_llm else "📝 Template")

        # Score breakdown
        with st.expander("📊 Score Breakdown"):
            score_cols = st.columns(4)

            with score_cols[0]:
                thompson = scores.get("thompson", 0)
                st.metric("Thompson", f"{thompson:.1f}")

            with score_cols[1]:
                financial = scores.get("financial", 0)
                st.metric("Financial", f"{financial:.2f}")

            with score_cols[2]:
                collaborative = scores.get("collaborative", 0)
                st.metric("Collaborative", f"{collaborative:.1f}")

            with score_cols[3]:
                diversity = scores.get("diversity_bonus", 0)
                st.metric("Diversity", f"{diversity:.1f}")

        # Interaction buttons
        st.markdown("### 👆 Actions")

        col1, col2, col3, col4 = st.columns(4)

        user_id = st.session_state.get("user_profile", {}).get("user_id", "anonymous")
        product_id = product["product_id"]

        with col1:
            if st.button("👁️ View", key=f"view_{product_id}"):
                result = api_client.track_interaction(user_id, product_id, "view")
                if result:
                    st.success("✅ Tracked: View")

        with col2:
            if st.button("👆 Click", key=f"click_{product_id}"):
                result = api_client.track_interaction(user_id, product_id, "click")
                if result:
                    st.success("✅ Tracked: Click")

        with col3:
            if st.button("🛒 Add to Cart", key=f"cart_{product_id}"):
                result = api_client.track_interaction(user_id, product_id, "add_to_cart")
                if result:
                    st.success("✅ Tracked: Added to Cart")

        with col4:
            if st.button("💳 Purchase", key=f"purchase_{product_id}"):
                result = api_client.track_interaction(user_id, product_id, "purchase")
                if result:
                    st.balloons()
                    st.success("🎉 Purchase Tracked!")
                    st.info("Future recommendations will improve based on this purchase!")


def render_affordability_badge(affordability: Dict[str, Any]) -> None:
    """Render affordability status badge"""
    can_afford_cash = affordability.get("can_afford_cash", False)
    can_afford_financing = affordability.get("can_afford_financing", False)
    risk_level = affordability.get("risk_level", "unknown")

    if can_afford_cash:
        st.success("✅ Affordable (Cash)")
    elif can_afford_financing:
        st.warning("💳 Affordable (Financing)")
    else:
        st.error("❌ Currently Unaffordable")

    # Risk indicator
    risk_colors = {
        "safe": "🟢",
        "caution": "🟡",
        "risky": "🔴"
    }

    risk_icon = risk_colors.get(risk_level, "⚪")
    st.caption(f"{risk_icon} Risk Level: {risk_level.title()}")
