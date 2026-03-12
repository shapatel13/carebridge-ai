# CareBridge MVP Demo Completion Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix frontend routing and add a Dashboard page to make the CareBridge app demo-ready for investor pitch.

**Architecture:** The backend is complete (FastAPI + SQLite with auth, conversations, AI generation). We're fixing the React frontend routing (`App.tsx` currently points to a portfolio Dashboard) and adding one new page (conversation history/dashboard). We also fix the CSS theme to match CareBridge's light theme and update the backend metadata.

**Tech Stack:** React 18, React Router 6, Zustand, Tailwind CSS 3, Vite 5, FastAPI

---

### Task 1: Fix Tailwind Config and CSS for CareBridge Theme

The existing `tailwind.config.js` and `index.css` are styled for a dark portfolio app. The CareBridge pages use custom color tokens (`navy`, `clinical`, `muted`, `body`, `danger`, `warning`, `success`) that aren't in the config.

**Files:**
- Modify: `frontend/tailwind.config.js`
- Modify: `frontend/src/index.css`

**Step 1: Update tailwind.config.js to add CareBridge colors**

Add these colors to the `extend.colors` section in `frontend/tailwind.config.js`:

```js
navy: {
  light: '#2563EB',
  DEFAULT: '#1E3A5F',
  dark: '#152D4A',
},
clinical: {
  light: '#38BDF8',
  DEFAULT: '#0EA5E9',
  dark: '#0284C7',
},
muted: '#6B7280',
body: '#1F2937',
danger: '#EF4444',
warning: '#F59E0B',
success: '#22C55E',
```

**Step 2: Update index.css for CareBridge light theme**

Replace the dark `@layer base` styles in `frontend/src/index.css` with light theme defaults:

```css
@layer base {
  html {
    @apply bg-gray-50 text-gray-900;
    scroll-behavior: smooth;
  }

  body {
    @apply bg-gray-50 text-gray-900 antialiased;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}
```

Remove the dark-themed `.glass-panel`, `.card-hover`, `.text-gradient`, `.btn-primary`, `.btn-secondary`, `.input-field` component classes and the recharts/selection styles — they're for the portfolio app and not used by CareBridge pages.

**Step 3: Verify the build compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors (or only pre-existing ones)

**Step 4: Commit**

```bash
git add frontend/tailwind.config.js frontend/src/index.css
git commit -m "fix: update Tailwind config and CSS for CareBridge light theme"
```

---

### Task 2: Rewrite App.tsx with CareBridge Routes and Auth Guard

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Replace App.tsx with CareBridge routing**

```tsx
import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import NewConversation from './pages/NewConversation'
import ConversationReview from './pages/ConversationReview'
import ConversationSuccess from './pages/ConversationSuccess'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy" />
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function App() {
  const { fetchUser } = useAuth()

  useEffect(() => {
    fetchUser()
  }, [])

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/new-conversation"
        element={
          <ProtectedRoute>
            <NewConversation />
          </ProtectedRoute>
        }
      />
      <Route
        path="/conversations/:id/review"
        element={
          <ProtectedRoute>
            <ConversationReview />
          </ProtectedRoute>
        }
      />
      <Route
        path="/conversations/:id/success"
        element={
          <ProtectedRoute>
            <ConversationSuccess />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: Error about missing `./pages/Dashboard` — that's expected, we create it in Task 3.

**Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: rewrite App.tsx with CareBridge routes and auth guard"
```

---

### Task 3: Create Dashboard Page (Conversation History)

**Files:**
- Create: `frontend/src/pages/Dashboard.tsx`

**Step 1: Create the Dashboard page**

```tsx
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import api from '../lib/api'
import {
  Plus,
  Stethoscope,
  LogOut,
  FileText,
  AlertTriangle,
  Clock,
  CheckCircle,
} from 'lucide-react'

interface ConversationSummary {
  id: string
  patient_alias: string
  status: string
  tone_setting: string
  created_at: string
  finalized_at: string | null
  organ_supports: string[] | null
  code_status_discussed: boolean
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/conversations')
      .then((res) => setConversations(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Stethoscope className="w-6 h-6 text-navy" />
            <h1 className="font-bold text-navy text-lg">CareBridge AI</h1>
            {user?.is_demo && (
              <span className="text-xs bg-clinical/10 text-clinical px-2 py-0.5 rounded-full font-medium">
                DEMO
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted hidden sm:block">{user?.full_name}</span>
            <button
              onClick={() => {
                logout()
                navigate('/login')
              }}
              className="text-muted hover:text-navy transition-colors"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Title + New Button */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-body">Conversations</h2>
            <p className="text-sm text-muted mt-1">
              Manage your ICU serious illness communications
            </p>
          </div>
          <button
            onClick={() => navigate('/new-conversation')}
            className="px-5 py-2.5 bg-navy hover:bg-navy-dark text-white font-semibold rounded-xl transition-colors flex items-center gap-2 shadow-sm"
          >
            <Plus className="w-5 h-5" />
            New Conversation
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy" />
          </div>
        ) : conversations.length === 0 ? (
          /* Empty State */
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-clinical/10 mb-4">
              <FileText className="w-8 h-8 text-clinical" />
            </div>
            <h3 className="text-lg font-semibold text-body mb-2">
              No conversations yet
            </h3>
            <p className="text-muted text-sm mb-6 max-w-md mx-auto">
              Start your first structured communication to generate physician
              notes, family summaries, and risk flags.
            </p>
            <button
              onClick={() => navigate('/new-conversation')}
              className="px-6 py-3 bg-navy hover:bg-navy-dark text-white font-semibold rounded-xl transition-colors inline-flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Start First Conversation
            </button>
          </div>
        ) : (
          /* Conversation Cards */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() =>
                  navigate(
                    conv.status === 'FINALIZED'
                      ? `/conversations/${conv.id}/review`
                      : `/conversations/${conv.id}/review`
                  )
                }
                className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md hover:border-gray-200 transition-all text-left"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-body">
                    {conv.patient_alias}
                  </h3>
                  <span
                    className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      conv.status === 'FINALIZED'
                        ? 'bg-green-50 text-success'
                        : 'bg-amber-50 text-warning'
                    }`}
                  >
                    {conv.status === 'FINALIZED' ? (
                      <span className="flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" /> Finalized
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Draft
                      </span>
                    )}
                  </span>
                </div>
                <div className="text-xs text-muted space-y-1">
                  <p>
                    Tone: {conv.tone_setting} &middot;{' '}
                    {new Date(conv.created_at).toLocaleDateString()}
                  </p>
                  {conv.organ_supports && conv.organ_supports.length > 0 && (
                    <p className="flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3 text-warning" />
                      {conv.organ_supports.length} organ support
                      {conv.organ_supports.length > 1 ? 's' : ''}
                    </p>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/pages/Dashboard.tsx
git commit -m "feat: add Dashboard page with conversation history list"
```

---

### Task 4: Update Login Redirect to Dashboard

Currently `Login.tsx` redirects to `/new-conversation` after login. For the investor demo, redirect to `/dashboard` so they see the conversation history first (including the pre-seeded demo conversation).

**Files:**
- Modify: `frontend/src/pages/Login.tsx`

**Step 1: Update Login.tsx redirects**

Change line 14 from:
```tsx
if (user) return <Navigate to="/new-conversation" replace />
```
to:
```tsx
if (user) return <Navigate to="/dashboard" replace />
```

Change line 22 from:
```tsx
navigate('/new-conversation')
```
to:
```tsx
navigate('/dashboard')
```

Change line 37 from:
```tsx
navigate('/new-conversation')
```
to:
```tsx
navigate('/dashboard')
```

**Step 2: Commit**

```bash
git add frontend/src/pages/Login.tsx
git commit -m "fix: redirect login to dashboard instead of new-conversation"
```

---

### Task 5: Update Backend Metadata for CareBridge

**Files:**
- Modify: `backend/app/main.py`

**Step 1: Update FastAPI title and health check**

Change the `FastAPI()` constructor (line 131-136) title from "AI Investment Portfolio Analysis System" to:
```python
app = FastAPI(
    title="CareBridge AI",
    description="ICU Serious Illness Communication Platform - AI-powered physician notes, family summaries, and risk detection",
    version="1.0.0",
    lifespan=lifespan,
)
```

Change the health check (line 174):
```python
return {"status": "ok", "service": "carebridge-ai"}
```

**Step 2: Commit**

```bash
git add backend/app/main.py
git commit -m "fix: update backend metadata to CareBridge branding"
```

---

### Task 6: Build, Start, and Verify End-to-End Demo Flow

**Step 1: Install frontend dependencies and build**

Run: `cd frontend && npm install && npm run build`
Expected: Build succeeds, outputs to `frontend/dist/`

**Step 2: Start the backend**

Run: `cd backend && pip install -e . && python -m uvicorn app.main:app --port 8000`
Expected: Server starts, logs "Database tables created" and "Demo data seeded successfully"

**Step 3: Verify the demo flow in browser**

1. Navigate to `http://localhost:8000` → should redirect to `/login`
2. Click "Try Demo Mode (No PHI)" → should redirect to `/dashboard`
3. See pre-seeded "Patient A (Mr. Rodriguez)" conversation card with "Finalized" badge
4. Click the card → should show ConversationReview with physician note, family summary, risk flags
5. Click "New Conversation" → should open NewConversation page with voice/text input
6. Type sample text, click "Generate" → should create conversation and show review page

**Step 4: Final commit**

No files to commit — this is verification only. If anything is broken, fix and commit.
