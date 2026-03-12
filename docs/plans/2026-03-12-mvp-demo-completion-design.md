# CareBridge MVP Demo Completion Design

**Date:** 2026-03-12
**Goal:** Get the existing CareBridge app to a polished investor demo state
**Approach:** Fix frontend routing on master branch (Approach 1)

## Current State

The backend is 100% complete: auth, conversation CRUD, segments, `/generate` (with Claude API + demo fallback), `/finalize`. All four frontend pages exist (Login, NewConversation, ConversationReview, ConversationSuccess) and are fully implemented. The only blocker is `App.tsx` routing to a vestigial portfolio Dashboard instead of the CareBridge pages.

## Changes Required

### 1. Fix App.tsx Routing (Critical)

Replace portfolio routes with CareBridge routes + auth guard:

- `/login` → Login page
- `/` → Redirect to `/dashboard` (authenticated) or `/login` (unauthenticated)
- `/dashboard` → New conversation history page (protected)
- `/new-conversation` → NewConversation (protected)
- `/conversations/:id/review` → ConversationReview (protected)
- `/conversations/:id/success` → ConversationSuccess (protected)

Auth guard: call `useAuth().fetchUser()` on mount to restore JWT sessions. Redirect unauthenticated users to `/login`.

### 2. Add Dashboard/History Page (New)

Simple conversation list using existing `GET /conversations` API:

- Shows cards with patient alias, status badge (DRAFT/FINALIZED), date, tone, risk flag count
- Empty state with "Start your first conversation" CTA
- "New Conversation" button in header
- Click a conversation → navigate to review page

### 3. Demo Data Polish

Pre-seed a completed demo conversation on backend startup so the demo button immediately shows rich data:

- A finalized conversation with realistic ICU family meeting transcript
- Generated output with physician note (all 7 sections), family summary, and risk flags
- Investors see the full output quality on first click

### 4. Voice + Text Input

Both already implemented. Text input is primary for demo reliability. Mic button stays visible for "and we support voice capture" moment.

## Out of Scope

- Docker/PostgreSQL migration (SQLite is fine for demo)
- Portfolio code removal (hidden from UI, not blocking)
- PDF export (Phase 2, button already shows disabled with tooltip)
- WebSocket voice streaming
- Alembic migrations
