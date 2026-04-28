from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from database import init_db
from routers import auth, conversations, messages, users, media


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Chattr API",
    description="Real-time messaging backend — REST + WebSocket",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS must be added BEFORE any routes or exception handlers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler — ensures CORS headers are present even on 500s
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        headers={"Access-Control-Allow-Origin": "*"},
        content={"detail": str(exc)},
    )


app.include_router(auth.router,          prefix="/auth")
app.include_router(users.router,         prefix="/users")
app.include_router(conversations.router, prefix="/conversations")
app.include_router(messages.router,      prefix="/messages")
app.include_router(media.router,         prefix="/media")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Chattr API is running 🚀", "version": "2.0.0"}
