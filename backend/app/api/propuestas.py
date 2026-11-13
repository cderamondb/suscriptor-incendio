"""Endpoints de análisis, propuestas y decisión."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencias import usuario_actual
from app.catalogo.cargador import cargar_tarifario
from app.catalogo.repositorio import Repositorio
from app.config import settings
from app.dominio.apetito import evaluar_apetito
from app.dominio.estados import transitar
from app.dominio.facultades import verificar_facultad
from app.dominio.modelos import (
    EstadoCaso,
    FichaRiesgo,
    RolUsuario,
    TransicionInvalida,
)
from app.dominio.tarifa import tarificar
from app.persistencia.crud import (
    actualizar_caso,
    crear_propuesta,
    max_version_propuesta,
    obtener_caso,
    obtener_propuesta,
    registrar_auditoria,
)
from app.persistencia.modelos_db import UsuarioDB
from app.persistencia.sesion_db import get_db

router = APIRouter(tags=["propuestas"])


def _cargar_tarifario():
    ruta = Path(settings.ruta_tarifario)
    if not ruta.is_absolute():
        ruta = Path(__file__).resolve().parent.parent.parent.parent / ruta
    return cargar_tarifario(ruta)


@router.get("/casos/{caso_id}/analisis")
def analisis(
    caso_id: str,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = obtener_caso(db, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    if caso.estado not in (
        EstadoCaso.FICHA_CONFIRMADA.value,
        EstadoCaso.PROPUESTA_EN_REVISION.value,
        EstadoCaso.PROPUESTA_APROBADA.value,
        EstadoCaso.COTIZADO.value,
    ):
        raise HTTPException(status_code=409, detail="La ficha no está confirmada")

    ficha = FichaRiesgo.model_validate(caso.ficha)
    tarifario = _cargar_tarifario()
    repo = Repositorio(tarifario)

    apetito = evaluar_apetito(ficha, tarifario)
    comparables = repo.buscar_comparables(ficha)

    return {
        "apetito": apetito.model_dump(),
        "comparables": comparables,
    }


class CrearPropuestaRequest(BaseModel):
    coberturas: list[str] | None = None
    deducible: str | None = None
    ajuste_comercial: str = "0"


@router.post("/casos/{caso_id}/propuestas", status_code=201)
def crear_propuesta_endpoint(
    caso_id: str,
    body: CrearPropuestaRequest,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = obtener_caso(db, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    if caso.estado not in (
        EstadoCaso.FICHA_CONFIRMADA.value,
        EstadoCaso.PROPUESTA_EN_REVISION.value,
    ):
        raise HTTPException(status_code=409, detail="Estado no permite crear propuesta")

    ficha = FichaRiesgo.model_validate(caso.ficha)
    tarifario = _cargar_tarifario()

    try:
        ajuste = Decimal(body.ajuste_comercial)
    except (InvalidOperation, ValueError):
        raise HTTPException(
            status_code=422, detail="ajuste_comercial inválido",
        ) from None

    propuesta_tarifa = tarificar(ficha, tarifario, ajuste_comercial=ajuste)

    nueva_version = max_version_propuesta(db, caso_id) + 1
    propuesta = crear_propuesta(
        db,
        caso_id=caso_id,
        version=nueva_version,
        datos=propuesta_tarifa.model_dump(mode="json"),
        ajuste_comercial=ajuste,
    )

    try:
        nuevo_estado = transitar(EstadoCaso(caso.estado), EstadoCaso.PROPUESTA_EN_REVISION)
        actualizar_caso(db, caso, estado=nuevo_estado.value)
    except TransicionInvalida:
        pass

    return {"version": propuesta.version, "propuesta": propuesta_tarifa.model_dump(mode="json")}


class DecisionRequest(BaseModel):
    decision: str
    comentario: str = ""


@router.post("/casos/{caso_id}/propuestas/{version}/decision")
def decidir_propuesta(
    caso_id: str,
    version: int,
    body: DecisionRequest,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = obtener_caso(db, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    propuesta = obtener_propuesta(db, caso_id, version)
    if not propuesta:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    if propuesta.estado not in ("BORRADOR", "EN_REVISION"):
        raise HTTPException(status_code=409, detail="Propuesta ya decidida")

    if body.decision == "aprobar":
        ficha = FichaRiesgo.model_validate(caso.ficha)
        tarifario = _cargar_tarifario()
        apetito = evaluar_apetito(ficha, tarifario)

        rol = RolUsuario(usuario.rol)
        suma_total = sum(
            item.suma_asegurada
            for ub in ficha.ubicaciones
            for item in ub.items
        )
        resultado_facultad = verificar_facultad(
            suma_asegurada_total=suma_total,
            ajuste_comercial=Decimal(str(propuesta.ajuste_comercial)),
            apetito=apetito,
            rol=rol,
            tarifario=tarifario,
        )
        if not resultado_facultad.permitido:
            from app.dominio.modelos import FacultadExcedida
            raise FacultadExcedida(resultado_facultad.requiere)

        propuesta.estado = "APROBADA"
        propuesta.decidido_por = usuario.id
        propuesta.comentario = body.comentario
        db.commit()

        try:
            nuevo_estado = transitar(EstadoCaso(caso.estado), EstadoCaso.PROPUESTA_APROBADA)
            actualizar_caso(db, caso, estado=nuevo_estado.value)
        except TransicionInvalida:
            pass

    elif body.decision == "rechazar":
        propuesta.estado = "RECHAZADA"
        propuesta.decidido_por = usuario.id
        propuesta.comentario = body.comentario
        db.commit()
    else:
        raise HTTPException(status_code=422, detail="Decisión debe ser 'aprobar' o 'rechazar'")

    registrar_auditoria(
        db,
        tabla="propuestas",
        registro_id=str(propuesta.id),
        accion=f"DECISION_{body.decision.upper()}",
        usuario_id=usuario.id,
        valor_nuevo={"decision": body.decision, "comentario": body.comentario},
    )

    return {"estado": propuesta.estado, "version": propuesta.version}
