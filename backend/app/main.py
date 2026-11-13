from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="SuscriptorIA Incendio",
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origenes_cors.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/salud")
def salud() -> dict[str, str]:
    return {
        "estado": "ok",
        "version": "0.1.0",
        "prompt_version": settings.prompt_version,
    }
