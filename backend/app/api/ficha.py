"""Endpoints de ficha: extracción, consulta, corrección y confirmación."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencias import usuario_actual
from app.config import settings


_RE_UB = re.compile(r"^ubicaciones\[(\d+)\]\.(.+)$")
_RE_ITEM = re.compile(r"^items\[(\d+)\]\.(.+)$")

_CAMPOS_TOP = {
    "razon_social", "rut", "actividad_declarada", "deducible_uf",
    "vigencia_desde", "vigencia_hasta", "aseguradora_anterior",
    "prima_anterior", "inspeccion", "siniestralidad",
    "coberturas_solicitadas",
}


def _estructurar_ficha(plana: dict) -> dict:
    """Convierte ficha plana (claves como 'ubicaciones[0].direccion') a estructura anidada."""
    resultado: dict = {}
    ubs: dict[int, dict] = {}

    for clave, valor in plana.items():
        if clave == "alertas":
            resultado["alertas"] = valor if isinstance(valor, list) else []
            continue

        m = _RE_UB.match(clave)
        if m:
            idx = int(m.group(1))
            campo_ub = m.group(2)
            if idx not in ubs:
                ubs[idx] = {"items": []}

            m_item = _RE_ITEM.match(campo_ub)
            if m_item:
                item_idx = int(m_item.group(1))
                item_campo = m_item.group(2)
                items = ubs[idx]["items"]
                while len(items) <= item_idx:
                    items.append({})
                if isinstance(valor, dict) and "valor" in valor:
                    items[item_idx][item_campo] = valor["valor"]
                else:
                    items[item_idx][item_campo] = valor
            else:
                ubs[idx][campo_ub] = valor
            continue

        resultado[clave] = valor

    if ubs:
        max_idx = max(ubs.keys())
        ubicaciones = []
        for i in range(max_idx + 1):
            ub = ubs.get(i, {"items": []})
            if "items" not in ub:
                ub["items"] = []
            ubicaciones.append(ub)
        resultado["ubicaciones"] = ubicaciones
    else:
        resultado["ubicaciones"] = []

    if "alertas" not in resultado:
        resultado["alertas"] = []

    return resultado
from app.dominio.datos_minimos import evaluar_completitud
from app.dominio.estados import transitar
from app.dominio.modelos import EstadoCaso, FichaRiesgo, TransicionInvalida
from app.persistencia.crud import (
    actualizar_caso,
    hay_trabajo_en_curso,
    obtener_caso,
    registrar_auditoria,
)
from app.persistencia.modelos_db import UsuarioDB
from app.persistencia.sesion_db import get_db

router = APIRouter(tags=["ficha"])


@router.post("/casos/{caso_id}/extraccion", status_code=202)
def iniciar_extraccion(
    caso_id: str,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = obtener_caso(db, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    from app.persistencia.crud import listar_documentos_caso
    docs = listar_documentos_caso(db, caso_id)
    if not docs:
        raise HTTPException(status_code=409, detail="Sin documentos cargados")

    if hay_trabajo_en_curso(db, caso_id):
        raise HTTPException(status_code=409, detail="Ya hay un trabajo en curso")

    from app.trabajos.cola import encolar
    trabajo_id = encolar(db, caso_id, "EXTRACCION")
    return {"trabajo_id": trabajo_id}


@router.get("/casos/{caso_id}/ficha")
def obtener_ficha(
    caso_id: str,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = obtener_caso(db, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    ficha_data = caso.ficha or {}
    tokens_entrada = caso.tokens_entrada or 0
    tokens_salida = caso.tokens_salida or 0
    tokens_cache = caso.tokens_cache or 0
    costo = (
        tokens_entrada * settings.precio_token_entrada_usd
        + tokens_salida * settings.precio_token_salida_usd
    )

    completitud = None
    if ficha_data:
        try:
            ficha = FichaRiesgo.model_validate(ficha_data)
            completitud = evaluar_completitud(ficha).model_dump()
        except Exception:
            completitud = None

    ficha_estructurada = _estructurar_ficha(ficha_data) if ficha_data else None

    return {
        "ficha": ficha_estructurada,
        "completitud": completitud,
        "tokens": {
            "entrada": tokens_entrada,
            "salida": tokens_salida,
            "cache": tokens_cache,
        },
        "costo_estimado_usd": round(costo, 6),
    }


class CorreccionRequest(BaseModel):
    campo: str
    valor: object
    motivo: str = ""


@router.patch("/casos/{caso_id}/ficha")
def corregir_ficha(
    caso_id: str,
    body: CorreccionRequest,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = obtener_caso(db, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    ficha_data = dict(caso.ficha) if caso.ficha else {}
    valor_anterior = ficha_data.get(body.campo)

    if body.campo in ficha_data and isinstance(ficha_data[body.campo], dict):
        ficha_data[body.campo]["valor"] = body.valor
        ficha_data[body.campo]["estado"] = "CORREGIDO"
    else:
        ficha_data[body.campo] = {"valor": body.valor, "estado": "CORREGIDO"}

    registrar_auditoria(
        db,
        tabla="casos",
        registro_id=caso_id,
        accion="CORRECCION_FICHA",
        usuario_id=usuario.id,
        valor_anterior={"campo": body.campo, "valor": valor_anterior},
        valor_nuevo={"campo": body.campo, "valor": body.valor},
        motivo=body.motivo,
    )

    actualizar_caso(db, caso, ficha=ficha_data)

    if caso.estado == EstadoCaso.FICHA_CONFIRMADA.value:
        try:
            transitar(EstadoCaso(caso.estado), EstadoCaso.FICHA_EN_REVISION)
            actualizar_caso(db, caso, estado=EstadoCaso.FICHA_EN_REVISION.value)
        except TransicionInvalida:
            pass

    return {"ficha": ficha_data}


@router.post("/casos/{caso_id}/ficha/confirmacion")
def confirmar_ficha(
    caso_id: str,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = obtener_caso(db, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    ficha_data = caso.ficha
    if not ficha_data:
        raise HTTPException(status_code=409, detail="Ficha vacía")

    try:
        ficha = FichaRiesgo.model_validate(ficha_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ficha inválida: {e}") from e

    reporte = evaluar_completitud(ficha)
    bloqueantes = [f for f in reporte.faltantes if f.bloqueante]
    if bloqueantes:
        raise HTTPException(
            status_code=409,
            detail={
                "codigo": "DATOS_INSUFICIENTES",
                "campos": [f.ruta for f in bloqueantes],
            },
        )

    try:
        nuevo_estado = transitar(EstadoCaso(caso.estado), EstadoCaso.FICHA_CONFIRMADA)
    except TransicionInvalida as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    actualizar_caso(db, caso, estado=nuevo_estado.value)

    registrar_auditoria(
        db,
        tabla="casos",
        registro_id=caso_id,
        accion="FICHA_CONFIRMADA",
        usuario_id=usuario.id,
    )

    return {"estado": nuevo_estado.value, "ficha": ficha_data}
