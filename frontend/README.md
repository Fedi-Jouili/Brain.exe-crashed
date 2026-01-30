# PriceSense Frontend

Streamlit-based web interface for the PriceSense AI recommendation system.

## Features

- 🔍 **Smart Search**: Natural language product search
- 💰 **Financial Profile**: Optional income/expense analysis
- 🎯 **Personalized Recommendations**: AI-powered product matching
- 📊 **Score Breakdown**: Transparent scoring system
- 💡 **Explanations**: Why each product was recommended
- 👍 **Feedback System**: Like, purchase, or dismiss recommendations
- ⚡ **Multiple Paths**: FAST (cached), SMART, or DEEP analysis

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the backend API is running:
```bash
cd ../backend
uvicorn main:app --reload
```

3. Run the Streamlit app:
```bash
streamlit run app.py
```

4. Open your browser to: http://localhost:8501

## Usage

### Basic Search
1. Enter a product query (e.g., "gaming laptop")
2. Click "Search"
3. View recommendations with explanations

### With Financial Analysis
1. Enable "Include financial analysis" in the sidebar
2. Enter your financial information:
   - Monthly income and expenses
   - Savings and debt
   - Credit score
3. Search for products
4. Get personalized affordability analysis

### Provide Feedback
For each recommendation, you can:
- 👍 **Like**: Product matches your needs
- 🛒 **Purchase**: You bought/plan to buy this
- 👎 **Not Interested**: Not a good match

Feedback helps improve future recommendations via Thompson Sampling.

## Architecture

```
User Interface (Streamlit)
         ↓
    API Client (requests)
         ↓
FastAPI Backend (localhost:8000)
         ↓
Multi-Agent System
```

## Configuration

Edit `app.py` to customize:
- `API_BASE_URL`: Backend API URL (default: http://localhost:8000)
- Custom CSS styling
- Layout and UI components

## Features Explained

### Search Paths
- **⚡ FAST**: Cached results (instant)
- **🧠 SMART**: Quick analysis without financial filtering
- **🔬 DEEP**: Full 5-agent pipeline with financial analysis

### Score Components
- **Thompson Sampling**: Learned user preferences
- **Semantic Score**: Query-product relevance
- **Collaborative**: Similar user preferences
- **RAGAS**: Recommendation quality score
- **Financial**: Affordability analysis (if profile provided)

### Trust Scores
- **80-100%**: High confidence (verified facts)
- **60-79%**: Medium confidence (some discrepancies)
- **0-59%**: Low confidence (template/fallback)
