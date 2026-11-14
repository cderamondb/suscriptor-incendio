"""GET /trabajos/{id}."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencias import usuario_actual
from app.persistencia.crud import obtener_trabajo
from app.persistencia.modelos_db import UsuarioDB
from app.persistencia.sesion_db import get_db

router = APIRouter(tags=["trabajos"])


@router.get("/trabajos/{trabajo_id}")
def consultar_trabajo(
    trabajo_id: str,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    trabajo = obtener_trabajo(db, trabajo_id)
    if not trabajo:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")

    return {
        "id": trabajo.id,
        "caso_id": trabajo.caso_id,
        "tipo": trabajo.tipo,
        "estado": trabajo.estado,
        "error_codigo": trabajo.codigo_error,
        "prompt_version": trabajo.prompt_version,
        "modelo": trabajo.modelo,
        "pasos": trabajo.pasos,
        "tokens_entrada": trabajo.tokens_entrada or 0,
        "tokens_salida": trabajo.tokens_salida or 0,
        "tokens_cache": trabajo.tokens_cache or 0,
        "herramientas_usadas": trabajo.herramientas_usadas,
        "respuesta": trabajo.resultado,
        "creado": trabajo.creado.isoformat() if trabajo.creado else None,
        "terminado": trabajo.terminado.isoformat() if trabajo.terminado else None,
    }
