"""Modelos SQLAlchemy — 9 tablas de §6.2 y §6.3."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.types import JSON


def _jsonb():
    return JSON().with_variant(PG_JSONB(), "postgresql")


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class UsuarioDB(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    correo = Column(String(255), unique=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    hash_clave = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False)
    creado = Column(DateTime(timezone=True), default=_utcnow)


class CasoDB(Base):
    __tablename__ = "casos"

    id = Column(String(36), primary_key=True, default=_uuid)
    asegurado = Column(String(255), nullable=False)
    rut = Column(String(20), nullable=False)
    corredor = Column(String(255), default="")
    ejecutivo = Column(String(255), default="")
    moneda = Column(String(10), default="UF")
    vigencia_solicitada = Column(String(100), default="")
    estado = Column(String(50), nullable=False, default="BORRADOR")
    ficha = Column(_jsonb(), nullable=True)
    tokens_entrada = Column(Integer, default=0)
    tokens_salida = Column(Integer, default=0)
    tokens_cache = Column(Integer, default=0)
    creado = Column(DateTime(timezone=True), default=_utcnow)
    actualizado = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    documentos = relationship("DocumentoDB", back_populates="caso", lazy="selectin")
    propuestas = relationship("PropuestaDB", back_populates="caso", lazy="selectin")
    trabajos = relationship("TrabajoDB", back_populates="caso", lazy="selectin")


class DocumentoDB(Base):
    __tablename__ = "documentos"

    id = Column(String(36), primary_key=True, default=_uuid)
    caso_id = Column(String(36), ForeignKey("casos.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    tipo_mime = Column(String(100), nullable=False)
    total_paginas = Column(Integer, default=0)
    fragmentos = Column(_jsonb(), nullable=True)
    creado = Column(DateTime(timezone=True), default=_utcnow)

    caso = relationship("CasoDB", back_populates="documentos")
    contenido = relationship("DocumentoContenidoDB", back_populates="documento", uselist=False)


class DocumentoContenidoDB(Base):
    __tablename__ = "documentos_contenido"

    documento_id = Column(String(36), ForeignKey("documentos.id"), primary_key=True)
    bytes_ = Column("bytes", LargeBinary, nullable=False)
    sha256 = Column(String(64), nullable=False)
    tipo_mime = Column(String(100), nullable=False)

    documento = relationship("DocumentoDB", back_populates="contenido")


class PropuestaDB(Base):
    __tablename__ = "propuestas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    caso_id = Column(String(36), ForeignKey("casos.id"), nullable=False)
    version = Column(Integer, nullable=False)
    datos = Column(_jsonb(), nullable=True)
    ajuste_comercial = Column(Numeric(10, 4), default=0)
    estado = Column(String(50), default="BORRADOR")
    decidido_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    comentario = Column(Text, default="")
    creado = Column(DateTime(timezone=True), default=_utcnow)

    caso = relationship("CasoDB", back_populates="propuestas")

    __table_args__ = (
        UniqueConstraint("caso_id", "version", name="uq_propuesta_caso_version"),
    )


class CotizacionDB(Base):
    __tablename__ = "cotizaciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    caso_id = Column(String(36), ForeignKey("casos.id"), nullable=False)
    propuesta_id = Column(Integer, ForeignKey("propuestas.id"), nullable=False)
    numero = Column(Integer, nullable=False)
    pdf_bytes = Column(LargeBinary, nullable=True)
    creado = Column(DateTime(timezone=True), default=_utcnow)


class TrabajoDB(Base):
    __tablename__ = "trabajos"

    id = Column(String(36), primary_key=True, default=_uuid)
    caso_id = Column(String(36), ForeignKey("casos.id"), nullable=False)
    tipo = Column(String(50), nullable=False)
    estado = Column(String(50), nullable=False, default="EN_COLA")
    codigo_error = Column(String(100), nullable=True)
    prompt_version = Column(String(20), nullable=True)
    modelo = Column(String(100), nullable=True)
    pasos = Column(Integer, default=0)
    tokens_entrada = Column(Integer, default=0)
    tokens_salida = Column(Integer, default=0)
    tokens_cache = Column(Integer, default=0)
    herramientas_usadas = Column(_jsonb(), nullable=True)
    resultado = Column(_jsonb(), nullable=True)
    creado = Column(DateTime(timezone=True), default=_utcnow)
    terminado = Column(DateTime(timezone=True), nullable=True)

    caso = relationship("CasoDB", back_populates="trabajos")


class AuditoriaDB(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tabla = Column(String(100), nullable=False)
    registro_id = Column(String(100), nullable=False)
    accion = Column(String(50), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    valor_anterior = Column(_jsonb(), nullable=True)
    valor_nuevo = Column(_jsonb(), nullable=True)
    motivo = Column(Text, default="")
    creado = Column(DateTime(timezone=True), default=_utcnow)


class PresupuestoDiarioDB(Base):
    __tablename__ = "presupuesto_diario"

    fecha = Column(Date, primary_key=True)
    tokens_total = Column(Integer, default=0)
