# 💬 Messaging App — Python Backend

A production-ready REST + WebSocket messaging backend built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

---

## 🗂 Project Structure

```
messaging-app/
├── main.py                  # App entry point
├── database.py              # DB engine & session
├── auth.py                  # JWT + password hashing
├── schemas.py               # Pydantic request/response models
├── ws_manager.py            # WebSocket connection manager
├── models/
│   └── models.py            # SQLAlchemy ORM models
├── routers/
│   ├── auth.py              # POST /auth/register, /auth/login
│   ├── conversations.py     # CRUD for conversations
│   └── messages.py          # REST + WebSocket messages
├── requirements.txt
├── render.yaml              # One-click Render deployment
└── .env.example             # Environment variable template
```

---

## ⚡ Local Setup

### 1. Clone & install dependencies
```bash
git clone <your-repo>
cd messaging-app
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create a free PostgreSQL database
Go to [supabase.com](https://supabase.com) → New Project → Settings → Database → copy the **Connection String (URI)**.

It looks like: `postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres`

Change the scheme to: `postgresql+asyncpg://...`

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in DATABASE_URL and SECRET_KEY
```

### 4. Run the server
```bash
uvicorn main:app --reload
```

Visit **http://localhost:8000/docs** for the interactive API docs (Swagger UI).

---

## 🚀 Deploy to Render (Free)

1. Push your code to a **GitHub** repository
2. Go to [render.com](https://render.com) → New → Web Service → connect your repo
3. Render will detect `render.yaml` automatically
4. In the dashboard, set the `DATABASE_URL` environment variable (from Supabase)
5. Click **Deploy** 🎉

Your API will be live at `https://messaging-app.onrender.com`

> **Note**: Free Render services sleep after 15 min of inactivity.  
> Use [cron-job.org](https://cron-job.org) to ping `GET /` every 10 minutes to keep it awake.

---

## 📡 API Reference

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create a new account |
| POST | `/auth/login` | Log in, receive JWT token |

### Conversations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/conversations/` | Start a new conversation |
| GET | `/conversations/` | List my conversations |
| GET | `/conversations/{id}` | Get conversation details |

### Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/messages/{conversation_id}` | Fetch message history |
| POST | `/messages/` | Send a message (REST) |
| PATCH | `/messages/{conversation_id}/read` | Mark messages as read |
| WS | `/messages/ws/{conversation_id}?token=<jwt>` | Real-time WebSocket |

---

## 🔌 WebSocket Usage

Connect to:
```
ws://localhost:8000/messages/ws/{conversation_id}?token=YOUR_JWT_TOKEN
```

Send a message:
```json
{"content": "Hello, world!"}
```

Receive (all connected participants get this):
```json
{
  "id": 42,
  "conversation_id": 1,
  "sender_id": 3,
  "sender_username": "alice",
  "content": "Hello, world!",
  "sent_at": "2024-01-15T10:30:00Z",
  "is_read": false
}
```

---

## 🗄 Database Schema

```
users          → id, username, email, password_hash, created_at
conversations  → id, name, is_group, created_at
participants   → user_id (FK), conversation_id (FK), joined_at
messages       → id, conversation_id (FK), sender_id (FK), content, sent_at, is_read
```

---

## 🔐 Authentication

All protected endpoints require:
```
Authorization: Bearer <your_jwt_token>
```

Get your token from `POST /auth/login`.

---

## 🛠 Tech Stack

| Tool | Purpose |
|------|---------|
| FastAPI | Web framework |
| SQLAlchemy (async) | ORM |
| asyncpg | PostgreSQL driver |
| python-jose | JWT tokens |
| passlib + bcrypt | Password hashing |
| Supabase | Free PostgreSQL hosting |
| Render | Free API hosting |
