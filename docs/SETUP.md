# Setup Guide

## Prerequisites
- Node.js 18+
- Python 3.9+
- PostgreSQL 13+
- Mapbox API key

## Installation

### Backend Setup
1. Navigate to `backend/` directory
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Set up PostgreSQL database
6. Run migrations: `python database.py`
7. Start server: `uvicorn main:app --reload`

### Frontend Setup
1. Navigate to `frontend/` directory
2. Install dependencies: `npm install`
3. Set up environment variables (Mapbox API key)
4. Start development server: `npm start`

### Scraper Setup
1. Navigate to `scraper/` directory
2. Install dependencies: `pip install -r requirements.txt`
3. Run scraper: `python crimemap_scraper.py`

## Environment Variables
Create `.env` files in respective directories with required API keys and database credentials.
