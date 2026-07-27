# Real-Time Event-Driven Notification System

A full-stack notification system that delivers real-time updates to users using WebSockets and an event-driven architecture powered by Redis Pub/Sub.

**Live Demo:** [https://notification-system-cyan.vercel.app](https://notification-system-cyan.vercel.app/)
**Backend API Docs:** [https://notification-system-idbs.onrender.com/docs](https://notification-system-idbs.onrender.com/docs)

> Note: the backend is hosted on Render's free tier, which spins down after periods of inactivity. The first request after idle time may take 30–50 seconds to respond while the server wakes up.

---

## Why This Project

Most CRUD apps stop at request/response. This project explores what happens when the server needs to _push_ information to the client the moment something happens — the same pattern behind LinkedIn's "X liked your post," Swiggy's live order tracking, or Slack's message badges.

It was built to understand, hands-on, how real-time systems are actually architected: how WebSockets differ from polling, how a message broker decouples event producers from consumers, and how that decoupling becomes essential once an app needs to scale beyond a single server instance.

---

## Tech Stack

**Frontend**

- Next.js (App Router) + TypeScript
- Tailwind CSS

**Backend**

- FastAPI (Python, async)
- SQLAlchemy ORM
- PostgreSQL (via [Neon](https://neon.tech))
- Redis Pub/Sub (via Render Key Value)
- JWT authentication (`python-jose`, `passlib`/bcrypt)

**Infrastructure**

- Backend + Redis hosted on Render
- Database hosted on Neon
- Frontend hosted on Vercel
- Docker (used locally for Postgres + Redis during development)

---

## Features

- **Real-time delivery** — new notifications appear instantly via WebSocket, no polling or manual refresh
- **Event-driven architecture** — routes publish events to Redis; a decoupled listener consumes them and pushes to connected clients, so multiple backend instances could scale horizontally without sharing in-memory state
- **JWT authentication** — register/login with hashed passwords (bcrypt); all notification routes and the WebSocket connection are protected and scoped to the authenticated user only
- **Cursor-based pagination** — "Load more" fetches older notifications using an ID-based cursor, avoiding the skip/duplicate bugs offset pagination has on a live-inserting feed
- **Unread count badge** — derived live from state, no separate network call needed
- **WebSocket auto-reconnect** — exponential backoff reconnect logic if the connection drops, with stale-connection guards to prevent race conditions on reconnect
- **Logout with confirmation modal**

---

## Architecture

```
Client (Next.js)
      │
      │  REST (fetch) + WebSocket
      ▼
FastAPI backend  ──publish──▶  Redis Pub/Sub  ──subscribe──▶  Background listener
      │                                                              │
      ▼                                                              ▼
PostgreSQL (Neon)                                          WebSocket push to
                                                             connected client
```

1. Client authenticates via `/login`, receives a JWT
2. Client opens a WebSocket connection, passing the JWT as a query param (browsers can't set custom headers on the WebSocket handshake)
3. Creating a notification saves it to Postgres, then **publishes** an event to a Redis channel
4. A background listener task (started via FastAPI's `lifespan`) **subscribes** to that channel and pushes matching events to the correct user's live WebSocket connection
5. If a user isn't connected, the notification still persists in Postgres and loads on their next visit via the REST endpoint

The publish/subscribe indirection means the API route that creates a notification never needs to know which server instance (if there were several) holds a given user's WebSocket connection — it just announces the event, and whichever instance is subscribed and holds that connection handles the delivery.

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (for local Postgres + Redis)

### 1. Clone the repo

```bash
git clone https://github.com/pranavsikhwal/notification_system.git
cd notification_system
```

### 2. Start local Postgres and Redis

```bash
docker run -d --name postgres-notifications -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=notifications -p 5432:5432 postgres
docker run -d --name redis-notifications -p 6379:6379 redis
```

### 3. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/notifications
REDIS_URL=redis://localhost:6379
SECRET_KEY=generate-with-python-secrets-token-hex-32
```

Run the backend:

```bash
uvicorn main:app --reload
```

API docs available at `http://127.0.0.1:8000/docs`

### 4. Frontend setup

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Run the frontend:

```bash
npm run dev
```

App available at `http://localhost:3000/notifications`

---

## Environment Variables Reference

| Variable              | Used by  | Description                                                 |
| --------------------- | -------- | ----------------------------------------------------------- |
| `DATABASE_URL`        | Backend  | PostgreSQL connection string                                |
| `REDIS_URL`           | Backend  | Redis connection string                                     |
| `SECRET_KEY`          | Backend  | Signing key for JWTs — must differ between local/production |
| `NEXT_PUBLIC_API_URL` | Frontend | Base URL of the FastAPI backend                             |

---

## Known Limitations / Future Improvements

- Logout is client-side only (JWT isn't invalidated server-side) — a Redis-backed token blocklist would allow true server-side revocation
- No auto-reconnect check for token _expiry_ specifically — a dropped connection retries indefinitely even if the underlying token has expired, rather than redirecting to login
- Single-region deployment on free-tier hosting, so cold starts (~30–50s) occur after inactivity
- No multi-device read-status sync (marking a notification read on one device doesn't push that update to another open session for the same user)

---
