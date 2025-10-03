# Testudo++ Setup Guide

## Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Anthropic API key

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
copy .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run backend
uvicorn main:app --reload
```

Backend will run on `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

Frontend will run on `http://localhost:5173`

## Testing the App

1. **Schedule Builder**: Try "I need a COMM gen-ed on Tuesdays"
2. **Event Scanner**: Upload a sample event flyer
3. **Campus Compass**: Ask "Where can I get vegetarian food?"
4. **Advisor**: Ask "I need one more CS core course"

## Troubleshooting

- **CORS errors**: Make sure backend is running on port 8000
- **API errors**: Check that ANTHROPIC_API_KEY is set in backend/.env
- **Module errors**: Ensure all dependencies are installed

## Demo Flow

For the hackathon demo:
1. Start with Schedule Builder (show NL parsing)
2. Upload event flyer (show OCR + calendar export)
3. Ask Compass question (show campus data integration)
4. Show Advisor recommendations

## Next Steps

- Replace mock data with real UMD Schedule of Classes API
- Add more campus data sources
- Implement calendar sync
- Add professor ratings integration
