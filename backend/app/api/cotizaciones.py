"""POST /casos/{id}/cotizaciones y GET /cotizaciones/{id}/pdf."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencias import usuario_actual
from app.dominio.estados import transitar
from app.dominio.modelos import EstadoCaso, PropuestaTarifa, TransicionInvalida
from app.persistencia.crud import (
    actualizar_caso,
    crear_cotizacion,
    obtener_caso,
    obtener_cotizacion,
    obtener_propuesta,
    registrar_auditoria,
)
from app.persistencia.modelos_db import UsuarioDB
from app.persistencia.sesion_db import get_db

router = APIRouter(tags=["cotizaciones"])


class CrearCotizacionRequest(BaseModel):
    propuesta_version: int


@router.post("/casos/{caso_id}/cotizaciones", status_code=201)
def crear_cotizacion_endpoint(
    caso_id: str,
    body: CrearCotizacionRequest,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = obtener_caso(db, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    propuesta = obtener_propuesta(db, caso_id, body.propuesta_version)
    if not propuesta:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    if propuesta.estado != "APROBADA":
        raise HTTPException(status_code=409, detail="Propuesta no aprobada")

    propuesta_tarifa = PropuestaTarifa.model_validate(propuesta.datos)

    from app.cotizacion.generador import generar_cotizacion
    pdf_bytes = generar_cotizacion(propuesta_tarifa, caso)

    cotizacion = crear_cotizacion(
        db,
        caso_id=caso_id,
        propuesta_id=propuesta.id,
        pdf_bytes=pdf_bytes,
    )

    try:
        nuevo_estado = transitar(EstadoCaso(caso.estado), EstadoCaso.COTIZADO)
        actualizar_caso(db, caso, estado=nuevo_estado.value)
    except TransicionInvalida:
        pass

    registrar_auditoria(
        db,
        tabla="cotizaciones",
        registro_id=str(cotizacion.id),
        accion="COTIZACION_CREADA",
        usuario_id=usuario.id,
    )

    return {"cotizacion_id": cotizacion.id, "numero": cotizacion.numero}


@router.get("/cotizaciones/{cotizacion_id}/pdf")
def descargar_pdf(
    cotizacion_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    cotizacion = obtener_cotizacion(db, cotizacion_id)
    if not cotizacion or not cotizacion.pdf_bytes:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    return Response(
        content=cotizacion.pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cotizacion_{cotizacion.numero}.pdf"},
    )
