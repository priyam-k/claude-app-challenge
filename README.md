# Testudo++ 🐢⚡

AI-powered campus companion for UMD students. Built for hackathon in 48 hours.

## Features
- 🗓️ **Smart Schedule Builder** - Natural language course scheduling
- 📸 **Event Scanner** - Photo-to-calendar event extraction
- 🧭 **Campus Compass** - Dining, bus, and event queries
- 🤖 **AI Advisor** - Course requirement recommendations

## Quick Start

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Tech Stack
- Frontend: React + Vite + Tailwind
- Backend: FastAPI + Claude AI
- Data: UMD Schedule of Classes API + mock data
