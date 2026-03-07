# CareBridge Enterprise — Phase 1 MVP Design

**Date:** 2026-03-07
**Scope:** Phase 1 MVP — auth, voice capture, output generation, conversation logging
**Build Strategy:** Feature-Slice Full-Stack (Approach B)
**Dev Environment:** Docker Compose
**Frontend Serve:** Separate Vite dev server (port 5173), FastAPI on port 8000

---

## 1. Architecture

### Project Structure

```
carebridge/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app factory + router mounts
│   │   ├── config.py           # Pydantic Settings (reads .env)
│   │   ├── auth/               # User, Hospital, JWT, RBAC
│   │   │   ├── models.py
│   │   │   ├── router.py
│   │   │   ├── dependencies.py
│   │   │   └── schemas.py
│   │   ├── conversations/      # Voice WS, transcription, output generation
│   │   │   ├── models.py
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── voice.py        # Whisper integration
│   │   │   └── generator.py    # Claude API integration
│   │   ├── core/
│   │   │   ├── database.py     # Async SQLAlchemy engine + session
│   │   │   ├── security.py     # bcrypt + JWT encode/decode
│   │   │   ├── middleware.py   # CORS, request logging, audit trail
│   │   │   └── exceptions.py   # Custom exception handlers
│   │   └── tasks/
│   │       ├── celery_app.py
│   │       └── transcription.py  # Async fallback transcription
│   ├── alembic/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_conversations.py
│   │   └── test_generator.py
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── NewConversation.tsx
│   │   │   ├── ConversationReview.tsx
│   │   │   └── ConversationSuccess.tsx
│   │   ├── components/
│   │   │   ├── VoiceRecorder.tsx
│   │   │   ├── ToneSelector.tsx
│   │   │   ├── PromptChips.tsx
│   │   │   ├── FamilySummaryCard.tsx
│   │   │   ├── PhysicianNoteCard.tsx
│   │   │   └── RiskFlagBanner.tsx
│   │   ├── hooks/
│   │   │   ├── useVoiceCapture.ts
│   │   │   ├── useConversation.ts
│   │   │   └── useAuth.ts
│   │   ├── lib/
│   │   │   ├── api.ts          # Axios instance with auth headers
│   │   │   └── colors.ts       # Tailwind color constants
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── vite.config.ts
│   └── package.json
├── docker-compose.yml
├── .env.example
└── docs/
    └── plans/
        └── 2026-03-07-carebridge-mvp-design.md
```

### Docker Compose Services

| Service    | Image              | Port  | Purpose                      |
|------------|--------------------|-------|------------------------------|
| `backend`  | Custom Dockerfile  | 8000  | FastAPI + uvicorn --reload   |
| `frontend` | Custom Dockerfile  | 5173  | Vite dev server              |
| `postgres` | postgres:16        | 5432  | Primary database             |
| `redis`    | redis:7-alpine     | 6379  | Celery broker + result store |
| `minio`    | minio/minio        | 9000  | S3-compatible audio storage  |

---

## 2. Data Models

### Hospital
```python
id: UUID (PK)
name: str
license_tier: Enum(SINGLE, MULTI_SYSTEM)
settings: JSON  # branding, defaults
created_at: datetime
```

### User
```python
id: UUID (PK)
email: str (unique)
hashed_password: str
full_name: str
role: Enum(PHYSICIAN, NURSE, ADMIN, RISK_OFFICER)
hospital_id: UUID (FK -> Hospital)
is_active: bool
created_at: datetime
```

### Conversation
```python
id: UUID (PK)
patient_alias: str          # de-identified, e.g. "Patient A"
physician_id: UUID (FK -> User)
hospital_id: UUID (FK -> Hospital)
status: Enum(DRAFT, FINALIZED)
tone_setting: Enum(optimistic, neutral, concerned)
risk_calibration: float     # 0.0 - 1.0
participants: JSON          # list[str]
organ_supports: JSON        # list[str]
code_status_discussed: bool
code_status_change: str | null
surrogate_name: str | null
surrogate_relationship: str | null
family_questions: JSON      # list[str]
clinician_annotations: JSON # list[str]
created_at: datetime
finalized_at: datetime | null
```

### ConversationSegment
```python
id: UUID (PK)
conversation_id: UUID (FK -> Conversation)
text: str
confidence: float
segment_order: int
created_at: datetime
```

### GeneratedOutput
```python
id: UUID (PK)
conversation_id: UUID (FK -> Conversation, unique)
physician_note: JSON    # structured sections
family_summary: str
risk_flags: JSON        # list[{type, severity, message, suggestion}]
created_at: datetime
```

---

## 3. Auth Design

### Endpoints
- `POST /auth/login` → `{ access_token, refresh_token, token_type }`
- `POST /auth/demo` → scoped demo JWT, synthetic data, no PHI
- `POST /auth/register` → ADMIN-only user creation
- `POST /auth/refresh` → rotate tokens
- `GET /auth/me` → current user profile

### JWT
- Access token: 15 minutes
- Refresh token: 7 days
- Payload: `{ sub: user_id, role: ..., hospital_id: ..., demo: bool }`

### RBAC Rules
| Role          | Permissions                                                      |
|---------------|------------------------------------------------------------------|
| PHYSICIAN     | Create/edit own conversations, view own data                     |
| NURSE         | Create conversations, cannot finalize without physician co-sign  |
| ADMIN         | Manage users, hospital-wide view, configure settings             |
| RISK_OFFICER  | Read-only all conversations + analytics                          |

### Demo Mode
- `POST /auth/demo` returns a demo-scoped JWT
- Pre-seeded synthetic conversations in the database
- All writes create ephemeral data tagged `is_demo=true`
- Prominently displayed on login screen

---

## 4. Voice Capture & Transcription

### WebSocket Flow
```
Browser MediaRecorder (WebM/opus, 250ms chunks)
  → ws://localhost:8000/ws/transcribe/{conversation_id}
  → FastAPI receives audio chunks
  → Streams to Whisper API (openai.Audio.transcriptions.create)
    with prompt="vasopressin, CRRT, BiPAP, norepinephrine, ..."
  → Returns transcription segments
  → Stores as ConversationSegment records
  → Sends back JSON:
    { type: "transcription", text: "...", confidence: 0.95, prompts: [...] }
```

### Structured Prompt Triggers (client-side keyword detection)
| Prompt Chip               | Triggers On Keywords                          |
|---------------------------|-----------------------------------------------|
| "Organ support discussed?" | ventilator, vasopressor, CRRT, BiPAP         |
| "Trajectory communicated?" | prognosis, trajectory, weeks, months, decline |
| "Code status addressed?"   | code status, DNR, DNI, resuscitate            |
| "Surrogate confirmed?"     | Always shown if surrogate not yet documented  |

### Offline Resilience
- Audio chunks stored in IndexedDB on the client
- If WebSocket drops, client queues and retries
- Fallback: `POST /conversations/{id}/transcribe-file` uploads full audio file
- Celery processes async, updates conversation via polling or SSE

---

## 5. Output Generation (Claude API)

### Endpoint
```
POST /conversations/{id}/generate
  Body: { tone_setting, risk_calibration, ...all conversation metadata }
  Returns: GeneratedOutput
```

### Claude API Call
- Model: `claude-sonnet-4-6`
- System prompt: medico-legal documentation assistant (full spec prompt)
- Tone injection based on `tone_setting`
- Structured JSON output using tool_use/response format

### Output Schema
```python
{
  "physician_note": {
    "participants": str,
    "medical_status_explained": str,
    "prognosis_discussed": str,
    "uncertainty_addressed": str,
    "family_understanding_noted": str,
    "code_status": str,
    "surrogate_decision_maker": str
  },
  "family_summary": str,      # ~150-200 words, 6th-grade reading level
  "risk_flags": [
    {
      "type": str,
      "severity": "yellow" | "red",
      "message": str,
      "suggestion": str
    }
  ]
}
```

### Safety Rules (baked into system prompt)
1. Never predict survival probability or use "X% chance"
2. Always acknowledge uncertainty explicitly
3. Always document who was present
4. Physician note = what was SAID, not what IS clinically
5. Family summary validates emotions before providing information

### Tone Calibration
- `optimistic`: "Frame trajectory with measured hope. Emphasize improvements."
- `neutral`: "Present information factually without directional framing."
- `concerned`: "Acknowledge the serious nature. Validate distress explicitly."

---

## 6. Frontend Pages

### Page 1: `/login`
- Centered card, CareBridge AI logo (navy)
- Email + Password fields
- "Sign In" button (navy primary)
- "Demo Mode (No PHI)" link (prominent, below sign-in)
- Footer: "This tool provides language assistance only and does not replace clinical judgment."

### Page 2: `/new-conversation`
Two-column layout:
- **Left:** Large mic button (tap to record), running transcript display, 3-chip tone selector (😊 😐 😟), prompt chips (dismissable), patient alias field
- **Right:** Clinician annotations list, family questions list, organ supports checklist, code status toggle, surrogate name/relationship fields, "Generate Structured Communication >" button (primary blue)

### Page 3: `/conversations/:id/review`
Two cards side-by-side:
- **Left (Family Summary):** Plain-language summary, risk flag banners (amber/red), related education video thumbnails (placeholder in Phase 1)
- **Right (Physician Note):** Expandable sections (Participants, Medical Status, Prognosis, Uncertainty, Family Understanding, Code Status, Surrogate), "Copy to EHR >" button
- Bottom: "Edit Inputs >" and "Finalize & Log >" buttons

### Page 4: `/conversations/:id/success`
- Large ✅ green checkmark (centered)
- Summary: Date, Provider name, Flags detected
- "Start New Update" button
- "Export Log PDF >" button (Phase 2, disabled with tooltip in Phase 1)

### Color System
```
Primary:    #1E3A5F  (deep navy)
Accent:     #4A90D9  (clinical blue)
Success:    #27AE60  (green)
Warning:    #F39C12  (amber)
Danger:     #E74C3C  (red)
Background: #F8F9FA  (light gray)
Card bg:    #FFFFFF
Text:       #2C3E50  (primary) / #7F8C8D (secondary)
```

---

## 7. Build Slices (Implementation Order)

### Slice 1: Project Scaffold + Auth
- pyproject.toml, Dockerfile, docker-compose.yml, .env.example
- FastAPI app factory, CORS, request logging middleware
- PostgreSQL async engine + Alembic migrations
- User + Hospital models, JWT auth, RBAC dependencies
- Demo mode with synthetic seed data
- React app scaffold (Vite + Tailwind + React Router)
- Login page (form + demo button)

### Slice 2: Voice Capture + Transcription
- WebSocket endpoint `/ws/transcribe/{conversation_id}`
- Whisper integration with medical vocabulary boosting
- ConversationSegment model + storage
- Celery fallback transcription task
- React: VoiceRecorder component, useVoiceCapture hook
- NewConversation page (mic button, transcript display, tone selector, prompt chips)

### Slice 3: Output Generation + Review
- Claude API integration with full system prompt
- `POST /conversations/{id}/generate` endpoint
- GeneratedOutput model + storage
- React: FamilySummaryCard, PhysicianNoteCard, RiskFlagBanner
- ConversationReview page (two-column output display)
- Copy-to-clipboard for physician note

### Slice 4: Finalization + Success
- `POST /conversations/{id}/finalize` endpoint
- Conversation status update to FINALIZED
- React: ConversationSuccess page (checkmark, summary, actions)
- End-to-end integration test (auth → voice → generate → finalize)

---

## 8. Testing Strategy

- **Unit tests:** pytest for each service (auth, transcription, generator)
- **Integration tests:** pytest-asyncio with test DB (in-memory SQLite or test postgres)
- **Mock strategy:** Mock Whisper and Claude APIs in tests using pytest fixtures
- **Edge cases for generator:** 50+ test cases (no surrogate, conflicting prognosis, multi-organ failure language, etc.)
- **Frontend:** Manual testing in Phase 1 (E2E test setup deferred to Phase 2)
