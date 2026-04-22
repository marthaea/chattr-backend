from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db
from routers import auth, conversations, messages


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (idempotent)
    await init_db()
    yield


app = FastAPI(
    title="Messaging App API",
    description="Real-time messaging backend with REST + WebSocket support",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(conversations.router, prefix="/conversations")
app.include_router(messages.router, prefix="/messages")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Messaging API is running 🚀"}
