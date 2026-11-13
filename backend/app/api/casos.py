"""POST /casos y GET /casos."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencias import usuario_actual
from app.persistencia.crud import crear_caso, listar_casos
from app.persistencia.modelos_db import UsuarioDB
from app.persistencia.sesion_db import get_db

router = APIRouter(tags=["casos"])


class CrearCasoRequest(BaseModel):
    asegurado: str
    rut: str
    corredor: str = ""
    ejecutivo: str = ""
    moneda: str = "UF"
    vigencia_solicitada: str = ""


@router.post("/casos", status_code=201)
def crear(
    body: CrearCasoRequest,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = crear_caso(
        db,
        asegurado=body.asegurado,
        rut=body.rut,
        corredor=body.corredor,
        ejecutivo=body.ejecutivo,
        moneda=body.moneda,
        vigencia_solicitada=body.vigencia_solicitada,
        creado_por=usuario.id,
    )
    return {"caso_id": caso.id}


@router.get("/casos")
def listar(
    estado: str | None = Query(None),
    corredor: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    casos = listar_casos(db, estado=estado, corredor=corredor, offset=offset, limit=limit)
    return [
        {
            "id": c.id,
            "asegurado": c.asegurado,
            "rut": c.rut,
            "estado": c.estado,
            "corredor": c.corredor,
            "creado": c.creado.isoformat() if c.creado else None,
        }
        for c in casos
    ]
