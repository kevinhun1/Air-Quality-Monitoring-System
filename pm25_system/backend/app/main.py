from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import Base, engine
from app.models import user, sensor_reading, alert, invite
import os

# By default we do NOT auto-create tables on import. To enable automatic
# table creation (useful for local development), set the env var
# `DEV_CREATE_TABLES=true` before starting the server. This avoids
# accidental schema changes in production.
_create_tables = os.getenv("DEV_CREATE_TABLES", "").lower() in ("1", "true", "yes")
if _create_tables:
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PM2.5 Monitoring System",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "PM2.5 Backend Running Successfully"}


# include routers
from app.routers import auth as auth_router

app.include_router(auth_router.router)
