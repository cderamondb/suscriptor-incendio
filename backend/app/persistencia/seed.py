"""Seed idempotente: usuario de evaluación + caso C1 precargado."""

from __future__ import annotations

import os
from pathlib import Path

from argon2 import PasswordHasher
from sqlalchemy.orm import Session

from app.persistencia.crud import (
    crear_documento,
    obtener_caso,
    obtener_usuario_por_correo,
)
from app.persistencia.modelos_db import UsuarioDB

ph = PasswordHasher()

CASO_C1_ID = "c1-demo-oficinas-000000"


def ejecutar_seed(db: Session) -> None:
    from app.persistencia.modelos_db import Base
    from app.persistencia.sesion_db import engine
    Base.metadata.create_all(bind=engine)
    _seed_usuarios(db)
    _seed_caso_c1(db)


def _seed_usuarios(db: Session) -> None:
    usuarios = [
        {
            "correo": "evaluacion@demo.cl",
            "nombre": "Evaluador Demo",
            "rol": "SUSCRIPTOR_SENIOR",
            "env_clave": "CLAVE_EVALUACION",
        },
        {
            "correo": "suscriptor@demo.cl",
            "nombre": "Suscriptor Demo",
            "rol": "SUSCRIPTOR",
            "env_clave": "CLAVE_SUSCRIPTOR",
        },
        {
            "correo": "ejecutivo@demo.cl",
            "nombre": "Ejecutivo Demo",
            "rol": "EJECUTIVO_COMERCIAL",
            "env_clave": "CLAVE_EJECUTIVO",
        },
    ]

    for u in usuarios:
        clave = os.environ.get(u["env_clave"], "")
        if not clave:
            continue
        existente = obtener_usuario_por_correo(db, u["correo"])
        if existente:
            continue
        usuario = UsuarioDB(
            correo=u["correo"],
            nombre=u["nombre"],
            hash_clave=ph.hash(clave),
            rol=u["rol"],
        )
        db.add(usuario)
    db.commit()


def _seed_caso_c1(db: Session) -> None:
    existente = obtener_caso(db, CASO_C1_ID)
    if existente:
        return

    usuario_eval = obtener_usuario_por_correo(db, "evaluacion@demo.cl")
    creado_por = usuario_eval.id if usuario_eval else None

    from app.persistencia.modelos_db import CasoDB
    caso = CasoDB(
        id=CASO_C1_ID,
        asegurado="Comercializadora Demo SpA",
        rut="76.123.456-7",
        corredor="Corredor Ficticio Ltda",
        ejecutivo="Ejecutivo Demo",
        moneda="UF",
        vigencia_solicitada="2025-01-01 a 2026-01-01",
        estado="DOCUMENTOS_CARGADOS",
        creado_por=creado_por,
    )
    db.add(caso)
    db.commit()

    fixtures_dir = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"

    archivos = [
        ("slip_c1.pdf", "application/pdf"),
        ("schedule_c1.xlsx",
         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ]

    for nombre, tipo_mime in archivos:
        ruta = fixtures_dir / nombre
        if not ruta.exists():
            continue
        contenido = ruta.read_bytes()
        crear_documento(
            db,
            caso_id=CASO_C1_ID,
            nombre=nombre,
            tipo_mime=tipo_mime,
            contenido_bytes=contenido,
        )
