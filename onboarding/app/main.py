import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes import health, links, submit


def configure_logging():
    """
    Structured JSON-compatible logging to stdout.
    CloudWatch captures stdout from the container automatically.
    """
    s = get_settings()
    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, s.log_level.upper(), logging.INFO),
        format="%(message)s",  # Emit raw message — audit.py handles JSON formatting
    )
    # Suppress noisy third-party loggers
    logging.getLogger("simple_salesforce").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


app = FastAPI(
    title="Driver Onboarding Portal",
    version="1.0.0",
    description="SOX-compliant driver application intake — stores to AWS S3 and Salesforce",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your domain(s) in production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(links.router)
app.include_router(submit.router)

# Serve the driver-facing frontend at /
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
