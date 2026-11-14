"""Carga del system prompt versionado desde /prompts/."""

from __future__ import annotations

from pathlib import Path

from app.config import settings


def cargar_system_prompt(version: str | None = None) -> str:
    version = version or settings.prompt_version
    nombre = f"suscriptor_{version}.md"

    # Buscar en varias ubicaciones posibles
    candidatos = [
        Path(__file__).resolve().parent.parent.parent.parent / "prompts" / nombre,
        Path(__file__).resolve().parent.parent.parent / "prompts" / nombre,
        Path("/app/prompts") / nombre,
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta.read_text(encoding="utf-8")

    raise FileNotFoundError(
        f"Prompt no encontrado: {nombre} (buscado en {[str(c) for c in candidatos]})",
    )
