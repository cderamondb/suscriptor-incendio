"""Funciones CRUD para todas las tablas."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.persistencia.modelos_db import (
    AuditoriaDB,
    CasoDB,
    CotizacionDB,
    DocumentoContenidoDB,
    DocumentoDB,
    PresupuestoDiarioDB,
    PropuestaDB,
    TrabajoDB,
    UsuarioDB,
)

# ── Usuarios ──────────────────────────────────────────────────────────

def obtener_usuario_por_correo(db: Session, correo: str) -> UsuarioDB | None:
    return db.query(UsuarioDB).filter(UsuarioDB.correo == correo).first()


def obtener_usuario(db: Session, usuario_id: int) -> UsuarioDB | None:
    return db.query(UsuarioDB).filter(UsuarioDB.id == usuario_id).first()


def crear_usuario(db: Session, correo: str, nombre: str, hash_clave: str, rol: str) -> UsuarioDB:
    usuario = UsuarioDB(correo=correo, nombre=nombre, hash_clave=hash_clave, rol=rol)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


# ── Casos ─────────────────────────────────────────────────────────────

def crear_caso(
    db: Session,
    asegurado: str,
    rut: str,
    corredor: str = "",
    ejecutivo: str = "",
    moneda: str = "UF",
    vigencia_solicitada: str = "",
    creado_por: int | None = None,
) -> CasoDB:
    caso = CasoDB(
        asegurado=asegurado,
        rut=rut,
        corredor=corredor,
        ejecutivo=ejecutivo,
        moneda=moneda,
        vigencia_solicitada=vigencia_solicitada,
        creado_por=creado_por,
    )
    db.add(caso)
    db.commit()
    db.refresh(caso)
    return caso


def obtener_caso(db: Session, caso_id: str) -> CasoDB | None:
    return db.query(CasoDB).filter(CasoDB.id == caso_id).first()


def listar_casos(
    db: Session,
    estado: str | None = None,
    corredor: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[CasoDB]:
    q = db.query(CasoDB)
    if estado:
        q = q.filter(CasoDB.estado == estado)
    if corredor:
        q = q.filter(CasoDB.corredor.ilike(f"%{corredor}%"))
    return q.order_by(CasoDB.creado.desc()).offset(offset).limit(limit).all()


def actualizar_caso(db: Session, caso: CasoDB, **campos: object) -> CasoDB:
    for k, v in campos.items():
        setattr(caso, k, v)
    caso.actualizado = datetime.now(UTC)
    db.commit()
    db.refresh(caso)
    return caso


# ── Documentos ────────────────────────────────────────────────────────

def crear_documento(
    db: Session,
    caso_id: str,
    nombre: str,
    tipo_mime: str,
    contenido_bytes: bytes,
    total_paginas: int = 0,
    fragmentos: object = None,
) -> DocumentoDB:
    doc = DocumentoDB(
        caso_id=caso_id,
        nombre=nombre,
        tipo_mime=tipo_mime,
        total_paginas=total_paginas,
        fragmentos=fragmentos,
    )
    db.add(doc)
    db.flush()

    contenido = DocumentoContenidoDB(
        documento_id=doc.id,
        bytes_=contenido_bytes,
        sha256=hashlib.sha256(contenido_bytes).hexdigest(),
        tipo_mime=tipo_mime,
    )
    db.add(contenido)
    db.commit()
    db.refresh(doc)
    return doc


def obtener_documento(db: Session, documento_id: str) -> DocumentoDB | None:
    return db.query(DocumentoDB).filter(DocumentoDB.id == documento_id).first()


def obtener_contenido_documento(db: Session, documento_id: str) -> bytes | None:
    contenido = (
        db.query(DocumentoContenidoDB)
        .filter(DocumentoContenidoDB.documento_id == documento_id)
        .first()
    )
    return contenido.bytes_ if contenido else None


def listar_documentos_caso(db: Session, caso_id: str) -> list[DocumentoDB]:
    return db.query(DocumentoDB).filter(DocumentoDB.caso_id == caso_id).all()


# ── Propuestas ────────────────────────────────────────────────────────

def crear_propuesta(
    db: Session,
    caso_id: str,
    version: int,
    datos: dict,
    ajuste_comercial: Decimal = Decimal("0"),
) -> PropuestaDB:
    propuesta = PropuestaDB(
        caso_id=caso_id,
        version=version,
        datos=datos,
        ajuste_comercial=ajuste_comercial,
    )
    db.add(propuesta)
    db.commit()
    db.refresh(propuesta)
    return propuesta


def obtener_propuesta(db: Session, caso_id: str, version: int) -> PropuestaDB | None:
    return (
        db.query(PropuestaDB)
        .filter(PropuestaDB.caso_id == caso_id, PropuestaDB.version == version)
        .first()
    )


def max_version_propuesta(db: Session, caso_id: str) -> int:
    resultado = (
        db.query(func.max(PropuestaDB.version))
        .filter(PropuestaDB.caso_id == caso_id)
        .scalar()
    )
    return resultado or 0


# ── Cotizaciones ──────────────────────────────────────────────────────

def crear_cotizacion(
    db: Session,
    caso_id: str,
    propuesta_id: int,
    pdf_bytes: bytes,
) -> CotizacionDB:
    numero = (
        db.query(func.coalesce(func.max(CotizacionDB.numero), 0))
        .scalar()
        or 0
    ) + 1
    cotizacion = CotizacionDB(
        caso_id=caso_id,
        propuesta_id=propuesta_id,
        numero=numero,
        pdf_bytes=pdf_bytes,
    )
    db.add(cotizacion)
    db.commit()
    db.refresh(cotizacion)
    return cotizacion


def obtener_cotizacion(db: Session, cotizacion_id: int) -> CotizacionDB | None:
    return db.query(CotizacionDB).filter(CotizacionDB.id == cotizacion_id).first()


# ── Trabajos ──────────────────────────────────────────────────────────

def crear_trabajo(
    db: Session,
    caso_id: str,
    tipo: str,
    prompt_version: str | None = None,
    modelo: str | None = None,
) -> TrabajoDB:
    trabajo = TrabajoDB(
        caso_id=caso_id,
        tipo=tipo,
        prompt_version=prompt_version,
        modelo=modelo,
    )
    db.add(trabajo)
    db.commit()
    db.refresh(trabajo)
    return trabajo


def obtener_trabajo(db: Session, trabajo_id: str) -> TrabajoDB | None:
    return db.query(TrabajoDB).filter(TrabajoDB.id == trabajo_id).first()


def hay_trabajo_en_curso(db: Session, caso_id: str) -> bool:
    return (
        db.query(TrabajoDB)
        .filter(TrabajoDB.caso_id == caso_id, TrabajoDB.estado == "EN_CURSO")
        .first()
    ) is not None


def marcar_trabajos_reinicio(db: Session) -> int:
    filas = (
        db.query(TrabajoDB)
        .filter(TrabajoDB.estado.in_(["EN_CURSO", "EN_COLA"]))
        .update(
            {"estado": "ERROR", "codigo_error": "REINICIO_PROCESO",
             "terminado": datetime.now(UTC)},
            synchronize_session="fetch",
        )
    )
    db.commit()
    return filas


# ── Auditoría ─────────────────────────────────────────────────────────

def registrar_auditoria(
    db: Session,
    tabla: str,
    registro_id: str,
    accion: str,
    usuario_id: int | None = None,
    valor_anterior: dict | None = None,
    valor_nuevo: dict | None = None,
    motivo: str = "",
) -> AuditoriaDB:
    entrada = AuditoriaDB(
        tabla=tabla,
        registro_id=registro_id,
        accion=accion,
        usuario_id=usuario_id,
        valor_anterior=valor_anterior,
        valor_nuevo=valor_nuevo,
        motivo=motivo,
    )
    db.add(entrada)
    db.commit()
    return entrada


# ── Presupuesto diario ───────────────────────────────────────────────

def obtener_tokens_dia(db: Session, fecha: object) -> int:
    registro = (
        db.query(PresupuestoDiarioDB)
        .filter(PresupuestoDiarioDB.fecha == fecha)
        .first()
    )
    return registro.tokens_total if registro else 0


def sumar_tokens_dia(db: Session, fecha: object, tokens: int) -> None:
    registro = (
        db.query(PresupuestoDiarioDB)
        .filter(PresupuestoDiarioDB.fecha == fecha)
        .first()
    )
    if registro:
        registro.tokens_total = registro.tokens_total + tokens
    else:
        registro = PresupuestoDiarioDB(fecha=fecha, tokens_total=tokens)
        db.add(registro)
    db.commit()
