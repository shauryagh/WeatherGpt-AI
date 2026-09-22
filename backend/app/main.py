from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import chat, weather

# Create tables on startup (fine for MVP; use Alembic migrations for production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Conversational AI backend for weather forecasting, alerts, and climate information.",
    version="0.1.0",
)

origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(weather.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
