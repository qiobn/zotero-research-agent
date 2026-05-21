"""FastAPI application for Project B — research assistant agent backend.

This is a placeholder scaffold. The full implementation will include:
- /chat endpoint with streaming SSE
- /index endpoint for building vector indices
- /cite endpoint for citation suggestions
- MCP server co-hosted in the same process
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Project B backend starting")
    yield
    logger.info("Project B backend shutting down")


app = FastAPI(
    title="Research Assistant Agent",
    description="AI-powered research assistant with Zotero integration",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
