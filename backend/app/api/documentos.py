"""POST /casos/{id}/documentos y GET /documentos/{id}/fragmento."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencias import usuario_actual
from app.config import settings
from app.dominio.modelos import EstadoCaso
from app.ingesta.detector import detectar_tipo
from app.ingesta.errores import ArchivoNoSoportado
from app.persistencia.crud import (
    actualizar_caso,
    crear_documento,
    listar_documentos_caso,
    obtener_caso,
    obtener_contenido_documento,
    obtener_documento,
)
from app.persistencia.modelos_db import UsuarioDB
from app.persistencia.sesion_db import get_db

router = APIRouter(tags=["documentos"])


@router.post("/casos/{caso_id}/documentos", status_code=202)
async def subir_documentos(
    caso_id: str,
    archivos: list[UploadFile],
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = obtener_caso(db, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    if len(archivos) > settings.max_archivos_por_carga:
        raise HTTPException(
            status_code=413,
            detail=f"Máximo {settings.max_archivos_por_carga} archivos",
        )

    resultado = []
    for archivo in archivos:
        contenido = await archivo.read()
        if len(contenido) > settings.tamano_max_archivo_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo {archivo.filename} excede el límite",
            )

        try:
            tipo_mime = detectar_tipo(contenido)
        except ArchivoNoSoportado:
            raise HTTPException(
                status_code=415,
                detail=f"Tipo no soportado: {archivo.filename}",
            ) from None

        doc = crear_documento(
            db,
            caso_id=caso_id,
            nombre=archivo.filename or "sin_nombre",
            tipo_mime=tipo_mime,
            contenido_bytes=contenido,
        )
        resultado.append({"documento_id": doc.id, "tipo": tipo_mime, "estado": "CARGADO"})

    if caso.estado == EstadoCaso.BORRADOR.value:
        actualizar_caso(db, caso, estado=EstadoCaso.DOCUMENTOS_CARGADOS.value)

    return resultado


@router.get("/casos/{caso_id}/documentos")
def listar_documentos(
    caso_id: str,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    caso = obtener_caso(db, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    docs = listar_documentos_caso(db, caso_id)
    return [
        {
            "documento_id": d.id,
            "nombre": d.nombre,
            "tipo": d.tipo_mime,
            "creado_en": d.creado.isoformat() if d.creado else None,
        }
        for d in docs
    ]


@router.get("/documentos/{documento_id}/fragmento")
def obtener_fragmento(
    documento_id: str,
    ubicacion: str = "",
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(usuario_actual),
):
    doc = obtener_documento(db, documento_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if not doc.fragmentos:
        contenido = obtener_contenido_documento(db, documento_id)
        if not contenido:
            raise HTTPException(status_code=404, detail="Contenido no encontrado")
        return {"documento_id": documento_id, "tipo": doc.tipo_mime, "ubicacion": ubicacion}

    for frag in doc.fragmentos:
        if isinstance(frag, dict) and frag.get("ubicacion") == ubicacion:
            return frag

    return {"documento_id": documento_id, "fragmentos": doc.fragmentos, "ubicacion": ubicacion}
