"""Carga del system prompt versionado desde /prompts/."""

from __future__ import annotations

from pathlib import Path

from app.config import settings


def cargar_system_prompt(version: str | None = None) -> str:
    version = version or settings.prompt_version
    base = Path(__file__).resolve().parent.parent.parent.parent
    ruta = base / "prompts" / f"suscriptor_{version}.md"
    if not ruta.exists():
        raise FileNotFoundError(f"Prompt no encontrado: {ruta}")
    return ruta.read_text(encoding="utf-8")
