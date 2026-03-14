# CareBridge AI

An ICU physician-to-family communication platform that transforms serious illness conversations into structured documentation, plain-language family summaries, and medico-legal risk assessments — powered by Claude AI.

## Features

- **Guided Conversation Wizard**: 4-step workflow (Patient Setup, Transcript Capture, Clinician Notes, Review & Generate)
- **Voice-to-Text Transcription**: Browser-based speech recognition for real-time conversation capture
- **AI-Generated Outputs**: Structured physician notes, family-friendly summaries, and medico-legal risk flags
- **Smart Suggestion Chips**: Pre-fill annotations and family questions with transcript-aware keyword detection
- **Multi-Language Support**: Family summaries in English, Spanish, Chinese, Vietnamese, Arabic, and Korean
- **PDF Export**: Hospital-branded PDF generation for physician notes and family summaries
- **Risk Flag Timeline**: Interactive severity-sorted timeline with copy-to-clipboard follow-up suggestions
- **Real-Time Readability Score**: Flesch-Kincaid grade-level badge on family summaries
- **Side-by-Side Tone Comparison**: Compare previous vs. regenerated outputs when adjusting tone
- **Shift Handoff**: AI-generated handoff summaries covering all patients for incoming physicians
- **Dark Mode**: Full dark theme support across all pages

## Quick Start

```bash
# On any platform (Windows, macOS, Linux)
python start.py
```

This single command will:
1. Install frontend dependencies (`npm install`)
2. Build the React frontend (`npm run build`)
3. Start the FastAPI server on http://localhost:8000

Access the application at: **http://localhost:8000**

API documentation: **http://localhost:8000/docs**

## Alternative Start Methods

### Python (cross-platform)
```bash
python start.py
```

### Windows
```cmd
start.bat
```

### macOS/Linux
```bash
./start.sh
```

### Manual (for development)
```bash
# Terminal 1 - Frontend dev server
cd frontend
npm install
npm run dev        # Runs on http://localhost:5173

# Terminal 2 - Backend
cd backend
pip install -e .
python -m uvicorn app.main:app --reload --port 8000
```

## Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Anthropic API Key** (for Claude AI generation; falls back to demo mode without one)

### Backend Setup
```bash
cd backend
pip install -e .
```

### Environment Variables
Create `backend/.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...    # Required for AI generation
SECRET_KEY=your-secret-key       # JWT authentication secret
```

## Architecture

```
carebridge-ai/
├── backend/                    # FastAPI + SQLAlchemy async backend
│   ├── app/
│   │   ├── auth/               # JWT authentication, user models
│   │   ├── conversations/      # Core conversation logic
│   │   │   ├── generator.py    # Claude AI integration + prompts
│   │   │   ├── models.py       # SQLAlchemy models
│   │   │   ├── router.py       # API endpoints
│   │   │   └── schemas.py      # Pydantic schemas
│   │   ├── core/               # Database, config
│   │   └── main.py             # FastAPI app + static serving
│   └── pyproject.toml
├── frontend/                   # React + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── components/         # UI components
│   │   │   ├── wizard/         # 4-step conversation wizard
│   │   │   ├── AppHeader.tsx   # Navigation + dark mode toggle
│   │   │   ├── RiskTimeline.tsx # Interactive risk flag timeline
│   │   │   └── WizardProgress.tsx
│   │   ├── hooks/              # Auth, conversation, theme stores
│   │   ├── lib/                # PDF generation, readability scoring
│   │   └── pages/              # Dashboard, wizard, review, handoff
│   ├── package.json
│   └── vite.config.ts
├── start.py                    # One-command startup script
├── start.sh                    # Unix startup script
└── start.bat                   # Windows startup script
```

## How It Works

1. **Physician logs in** and starts a new conversation from the dashboard
2. **Step 1 - Patient Setup**: Enter patient alias, family presence, language, organ supports, surrogate info
3. **Step 2 - Transcript**: Record or type the conversation transcript
4. **Step 3 - Clinician Notes**: Select tone, check code status, add annotations and family questions (with smart auto-detection from transcript)
5. **Step 4 - Review & Generate**: Review all inputs, then generate AI outputs
6. **Review Page**: View physician note, family summary (with readability score), risk flags (as interactive timeline), export PDF, compare tone changes
7. **Shift Handoff**: Generate an AI-powered handoff summary covering all patients for the incoming physician

## API Endpoints

### Authentication
- `POST /auth/register` - Register new physician
- `POST /auth/login` - Login and receive JWT token

### Conversations
- `POST /conversations` - Create a new conversation
- `GET /conversations` - List all conversations for the physician
- `GET /conversations/{id}` - Get conversation with segments and output
- `PATCH /conversations/{id}` - Update conversation metadata
- `POST /conversations/{id}/segments` - Add transcript segment
- `POST /conversations/{id}/generate` - Generate AI outputs
- `POST /conversations/{id}/finalize` - Lock conversation
- `POST /conversations/handoff` - Generate shift handoff summary

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Zustand, jsPDF, Lucide Icons
- **Backend**: FastAPI, SQLAlchemy (async), SQLite (aiosqlite), Pydantic v2
- **AI**: Anthropic Claude (claude-haiku-4-5) via official SDK
- **Auth**: JWT tokens with bcrypt password hashing

## License

MIT License - Free for personal and commercial use.
