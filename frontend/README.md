# FinCommerce Engine - Frontend

Streamlit web application for the FinCommerce Engine recommendation system.

## Features

- 🔍 **Product Search**: Text and image-based search
- 💰 **Affordability Analysis**: Real-time budget checks
- 🎯 **Smart Recommendations**: Thompson Sampling-powered
- 📊 **Admin Dashboard**: System metrics and monitoring
- 👤 **User Profiles**: Personalized financial analysis

## Installation

```bash
cd frontend
pip install -r requirements.txt
```

## Running the App

```bash
# Ensure backend is running first
cd ../backend
python main.py

# In another terminal, start frontend
cd frontend
streamlit run app.py
```

The app will open in your browser at: `http://localhost:8501`

## Usage

1. **Setup Profile**: Navigate to Profile page and enter your financial information
2. **Search Products**: Use the Search page to find products
3. **Review Recommendations**: See affordability analysis and AI explanations
4. **Track Interactions**: Click buttons to track actions (Thompson Sampling)
5. **Monitor System**: View metrics on the Dashboard page

## Architecture

- **Main Entry**: `app.py`
- **Pages**: Multi-page app with navigation
  - `1_🔍_Search.py` - Product search interface
  - `2_👤_Profile.py` - User profile management
  - `3_📊_Dashboard.py` - Admin metrics dashboard
- **Components**: Reusable UI components
  - `product_card.py` - Product display with interactions
- **Utils**: API client and session management
  - `api_client.py` - Backend API communication
  - `session_state.py` - Session state management
  - `styling.py` - Custom CSS styling

## Configuration

Edit `utils/api_client.py` to change backend URL:

```python
def __init__(self, base_url: str = "http://localhost:8000"):
```

## Project Structure

```
frontend/
├── app.py                      # Main entry point
├── pages/
│   ├── 1_🔍_Search.py         # Search page
│   ├── 2_👤_Profile.py        # Profile page
│   └── 3_📊_Dashboard.py      # Dashboard page
├── components/
│   ├── __init__.py
│   └── product_card.py        # Product display component
├── utils/
│   ├── __init__.py
│   ├── api_client.py          # Backend API client
│   ├── session_state.py       # Session management
│   └── styling.py             # Custom CSS
├── assets/                     # Static assets
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Troubleshooting

### Issue: Cannot connect to backend
**Solution**: Ensure backend is running on port 8000

```bash
cd backend
python main.py
```

### Issue: Slow search
**Solution**: Check backend logs for performance issues

### Issue: Session state lost
**Solution**: Streamlit session state is temporary - save important data externally

### Issue: Import errors
**Solution**: Install all dependencies

```bash
pip install -r requirements.txt
```

## Features by Page

### Home (app.py)
- System status overview
- Quick navigation
- Quick start guide

### Search Page
- Text search input
- Image upload (multimodal search)
- Real-time recommendations
- Product cards with affordability
- Interaction tracking

### Profile Page
- User information form
- Financial data entry
- Profile summary display

### Dashboard Page
- System health monitoring
- Thompson Sampling statistics
- Cache performance metrics
- Auto-refresh capability

## Development

### Adding New Pages

1. Create new file in `pages/` directory with format: `N_🔧_Name.py`
2. Use the same page config as other pages
3. Import utilities from `utils/` module

### Adding New Components

1. Create new file in `components/` directory
2. Define render function
3. Import in pages where needed

## Production Deployment

1. Set environment variables for production backend URL
2. Configure authentication if needed
3. Enable HTTPS
4. Set up monitoring and logging
5. Consider using Streamlit Cloud or Docker

## Support

For issues or questions, check:
- Backend API documentation: `http://localhost:8000/api/docs`
- Project repository: [GitHub URL]
- Report bugs: [Issues URL]

## License

[Your License Here]

## Acknowledgments

Built with:
- Streamlit
- FinCommerce Engine Backend
- LangGraph, Thompson Sampling, Gemini 2.0 Flash
