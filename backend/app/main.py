"""FastAPI principal — registra routers, error handlers y startup."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.agente_api import router as agente_router
from app.api.casos import router as casos_router
from app.api.cotizaciones import router as cotizaciones_router
from app.api.documentos import router as documentos_router
from app.api.errores import registrar_manejadores
from app.api.ficha import router as ficha_router
from app.api.propuestas import router as propuestas_router
from app.api.sesion import router as sesion_router
from app.api.trabajos import router as trabajos_router
from app.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from app.persistencia.modelos_db import Base
    from app.persistencia.sesion_db import SessionLocal, engine

    Base.metadata.create_all(bind=engine)

    from app.persistencia.crud import marcar_trabajos_reinicio

    db = SessionLocal()
    try:
        marcar_trabajos_reinicio(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="SuscriptorIA Incendio",
    version="0.2.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origenes_cors.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_manejadores(app)

app.include_router(sesion_router)
app.include_router(casos_router)
app.include_router(documentos_router)
app.include_router(ficha_router)
app.include_router(propuestas_router)
app.include_router(cotizaciones_router)
app.include_router(agente_router)
app.include_router(trabajos_router)


@app.get("/salud")
def salud() -> dict[str, str]:
    return {
        "estado": "ok",
        "version": "0.2.0",
        "prompt_version": settings.prompt_version,
    }


if os.path.isdir("static"):
    app.mount(
        "/", StaticFiles(directory="static", html=True), name="static",
    )
