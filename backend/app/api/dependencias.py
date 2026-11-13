"""Dependencias compartidas de la API: autenticación y sesión de BD."""

from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.config import settings
from app.persistencia.crud import obtener_usuario
from app.persistencia.modelos_db import UsuarioDB
from app.persistencia.sesion_db import get_db

_serializer = URLSafeTimedSerializer(settings.secret_key)

COOKIE_NAME = "sesion"
MAX_AGE = 86400 * 7


def firmar_cookie(usuario_id: int) -> str:
    return _serializer.dumps({"uid": usuario_id})


def usuario_actual(
    sesion: str | None = Cookie(None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> UsuarioDB:
    if not sesion:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        data = _serializer.loads(sesion, max_age=MAX_AGE)
    except BadSignature:
        raise HTTPException(status_code=401, detail="Sesión inválida") from None
    usuario = obtener_usuario(db, data["uid"])
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return usuario
