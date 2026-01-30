"""
PriceSense - AI-Powered Financial Product Recommendations
Streamlit Frontend Application
"""
import streamlit as st
import requests
import json
from typing import Optional, Dict, List
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Page Configuration
st.set_page_config(
    page_title="PriceSense - Smart Shopping Assistant",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subheader {
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .recommendation-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
    }
    .score-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        margin: 5px;
    }
    .score-high {
        background-color: #d4edda;
        color: #155724;
    }
    .score-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    .score-low {
        background-color: #f8d7da;
        color: #721c24;
    }
    .metric-card {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .trust-score {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .trust-high { color: #28a745; }
    .trust-medium { color: #ffc107; }
    .trust-low { color: #dc3545; }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if the API is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_recommendations(
    query: str,
    user_profile: Optional[Dict] = None,
    use_cache: bool = True
) -> Dict:
    """Get product recommendations from the API"""
    payload = {
        "query": query,
        "use_cache": use_cache
    }
    
    if user_profile:
        payload["user_profile"] = user_profile
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/search",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None


def submit_feedback(
    user_id: str,
    product_id: str,
    action: str,
    query: str,
    rating: Optional[int] = None
) -> bool:
    """Submit user feedback to the API"""
    payload = {
        "user_id": user_id,
        "product_id": product_id,
        "action": action,
        "query": query
    }
    
    if rating:
        payload["rating"] = rating
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/feedback/action",
            json=payload,
            timeout=10
        )
        return response.status_code == 200
    except:
        return False


def get_score_color(score: float) -> str:
    """Determine score color class"""
    if score >= 70:
        return "score-high"
    elif score >= 50:
        return "score-medium"
    else:
        return "score-low"


def get_trust_color(trust: float) -> str:
    """Determine trust score color class"""
    if trust >= 80:
        return "trust-high"
    elif trust >= 60:
        return "trust-medium"
    else:
        return "trust-low"


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"


def render_recommendation_card(rec: Dict, idx: int, query: str):
    """Render a single recommendation card"""
    product = rec.get('product', {})
    scores = rec.get('scores', {})
    affordability = rec.get('affordability', {})
    explanation = rec.get('explanation', '')
    trust_score = rec.get('trust_score', 0.0)
    
    # Product name and rank
    st.markdown(f"### {idx}. {product.get('name', 'Unknown Product')}")
    
    # Price and basic info
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Price", format_currency(product.get('price', 0)))
    
    with col2:
        if product.get('rating'):
            st.metric("Rating", f"⭐ {product.get('rating')}/5")
    
    with col3:
        final_score = rec.get('final_score', 0)
        st.metric("Match Score", f"{final_score:.1f}/100")
    
    with col4:
        trust_class = get_trust_color(trust_score)
        st.markdown(f"<div class='trust-score {trust_class}'>{trust_score:.0f}% Trust</div>", 
                   unsafe_allow_html=True)
    
    # Score breakdown
    with st.expander("📊 Score Breakdown"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Scoring Components:**")
            for component, score in scores.items():
                if component != 'final_score':
                    score_class = get_score_color(score)
                    st.markdown(
                        f"<div class='score-badge {score_class}'>"
                        f"{component}: {score:.1f}</div>",
                        unsafe_allow_html=True
                    )
        
        with col2:
            if affordability:
                st.write("**Affordability Analysis:**")
                st.write(f"💵 Cash Affordable: {'✅ Yes' if affordability.get('can_afford_cash') else '❌ No'}")
                st.write(f"💳 Financing Available: {'✅ Yes' if affordability.get('can_afford_financing') else '❌ No'}")
                st.write(f"⚠️ Risk Level: {affordability.get('risk_level', 'N/A')}")
    
    # Explanation
    if explanation:
        st.markdown("**💡 Why this recommendation?**")
        st.info(explanation)
    
    # Feedback buttons
    col1, col2, col3, col4 = st.columns(4)
    
    # Initialize session state for feedback if not exists
    feedback_key = f"feedback_{product.get('product_id')}_{idx}"
    if feedback_key not in st.session_state:
        st.session_state[feedback_key] = None
    
    with col1:
        if st.button("👍 Like", key=f"like_{idx}"):
            user_id = st.session_state.get('user_id', 'guest')
            if submit_feedback(user_id, product.get('product_id'), 'click', query):
                st.session_state[feedback_key] = "liked"
                st.success("Thanks for the feedback!")
    
    with col2:
        if st.button("🛒 Purchase", key=f"purchase_{idx}"):
            user_id = st.session_state.get('user_id', 'guest')
            if submit_feedback(user_id, product.get('product_id'), 'purchase', query):
                st.session_state[feedback_key] = "purchased"
                st.success("Purchase recorded! 🎉")
    
    with col3:
        if st.button("👎 Not Interested", key=f"dislike_{idx}"):
            user_id = st.session_state.get('user_id', 'guest')
            if submit_feedback(user_id, product.get('product_id'), 'dismiss', query):
                st.session_state[feedback_key] = "dismissed"
                st.info("Noted. We'll improve recommendations.")
    
    st.markdown("---")


def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">🛍️ PriceSense</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">AI-Powered Smart Shopping with Financial Intelligence</p>', 
               unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ API is not available. Please ensure the backend server is running at http://localhost:8000")
        st.info("Run: `cd backend && uvicorn main:app --reload`")
        return
    
    # Sidebar - User Profile
    with st.sidebar:
        st.header("👤 Your Financial Profile")
        
        use_profile = st.checkbox("Include financial analysis", value=False)
        
        user_profile = None
        if use_profile:
            st.subheader("Income & Expenses")
            monthly_income = st.number_input(
                "Monthly Income ($)",
                min_value=0.0,
                value=5000.0,
                step=100.0,
                help="Your gross monthly income"
            )
            
            monthly_expenses = st.number_input(
                "Monthly Expenses ($)",
                min_value=0.0,
                value=3500.0,
                step=100.0,
                help="Your regular monthly expenses"
            )
            
            st.subheader("Financial Status")
            savings = st.number_input(
                "Total Savings ($)",
                min_value=0.0,
                value=10000.0,
                step=500.0,
                help="Your total savings"
            )
            
            current_debt = st.number_input(
                "Current Debt ($)",
                min_value=0.0,
                value=5000.0,
                step=500.0,
                help="Total outstanding debt"
            )
            
            credit_score = st.slider(
                "Credit Score",
                min_value=300,
                max_value=850,
                value=720,
                step=10,
                help="Your credit score (300-850)"
            )
            
            # Calculate disposable income
            disposable = monthly_income - monthly_expenses
            st.metric("Disposable Income", format_currency(disposable))
            
            user_profile = {
                "user_id": st.session_state.get('user_id', 'guest'),
                "monthly_income": monthly_income,
                "monthly_expenses": monthly_expenses,
                "savings": savings,
                "current_debt": current_debt,
                "credit_score": credit_score
            }
            
            # Store user_id in session state
            if 'user_id' not in st.session_state:
                st.session_state['user_id'] = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        st.markdown("---")
        
        # Settings
        st.header("⚙️ Settings")
        use_cache = st.checkbox("Use cache for faster results", value=True)
    
    # Main content - Search
    st.header("🔍 Search for Products")
    
    # Search input
    query = st.text_input(
        "What are you looking for?",
        placeholder="e.g., gaming laptop, wireless headphones, 4K TV...",
        help="Describe the product you're looking for"
    )
    
    # Search button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Perform search
    if search_button and query:
        with st.spinner("🤖 AI is analyzing your request..."):
            result = get_recommendations(query, user_profile, use_cache)
        
        if result and result.get('success'):
            recommendations = result.get('recommendations', [])
            
            # Display metadata
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Results Found", len(recommendations))
            
            with col2:
                path = result.get('path_taken', 'UNKNOWN')
                path_emoji = {"FAST": "⚡", "SMART": "🧠", "DEEP": "🔬"}.get(path, "❓")
                st.metric("Path Used", f"{path_emoji} {path}")
            
            with col3:
                exec_time = result.get('execution_time_ms', 0) / 1000
                st.metric("Response Time", f"{exec_time:.2f}s")
            
            with col4:
                complexity = result.get('complexity_score', 0)
                st.metric("Query Complexity", f"{complexity:.2f}")
            
            st.markdown("---")
            
            # Display recommendations
            if recommendations:
                st.header(f"🎯 Top {len(recommendations)} Recommendations")
                
                for idx, rec in enumerate(recommendations, 1):
                    render_recommendation_card(rec, idx, query)
            else:
                st.warning("No recommendations found. Try a different search query.")
        
        elif result:
            # Show errors
            errors = result.get('errors', [])
            if errors:
                for error in errors:
                    st.error(f"Error: {error}")
            else:
                st.error("Search failed. Please try again.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>🤖 Powered by Multi-Agent AI System</p>
        <p style='font-size: 0.9rem;'>
            Discovery • Financial Analysis • Smart Recommendations • Explainable AI
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
