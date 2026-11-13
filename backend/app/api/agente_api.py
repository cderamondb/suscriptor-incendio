"""POST /casos/{id}/agente — interacción libre con el agente."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencias import usuario_actual
from app.persistencia.crud import hay_trabajo_en_curso, obtener_caso
from app.persistencia.modelos_db import UsuarioDB
from app.persistencia.sesion_db import get_db

router = APIRouter(tags=["agente"])


class MensajeAgenteRequest(BaseModel):
    mensaje: str = Field(..., max_length=2000)


@router.post("/casos/{caso_id}/agente", status_code=202)
def mensaje_agente(
    caso_id: str,
    body: MensajeAgenteRequest,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = obtener_caso(db, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    if hay_trabajo_en_curso(db, caso_id):
        raise HTTPException(status_code=409, detail="Ya hay un trabajo en curso para este caso")

    from app.trabajos.cola import encolar
    trabajo_id = encolar(db, caso_id, "AGENTE", mensaje=body.mensaje)
    return {"trabajo_id": trabajo_id}
