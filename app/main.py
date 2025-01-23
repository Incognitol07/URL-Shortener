# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.config import settings
from app.routers import url_router, auth_router
from app.background_jobs import start_scheduler, scheduler

templates = Jinja2Templates(directory="app/templates")

# Create the FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    print("Starting up the application...")
    # Initialize database (create tables if they don't exist)
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    try:
        yield
    finally:
        scheduler.shutdown()
        print("Shutting down the application...")

app = FastAPI(
    title=settings.APP_NAME,
    description="An API",
    version="1.0.0",
    debug=settings.DEBUG,  # Enable debug mode if in development
    lifespan=lifespan,
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include router
app.include_router(url_router)
app.include_router(auth_router)


# Root endpoint for health check
@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


