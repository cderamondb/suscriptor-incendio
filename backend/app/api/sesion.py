"""POST /sesion y DELETE /sesion — autenticación con cookie."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencias import COOKIE_NAME, firmar_cookie
from app.persistencia.crud import obtener_usuario_por_correo
from app.persistencia.sesion_db import get_db

router = APIRouter(tags=["sesion"])

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    _ph = PasswordHasher()
except ImportError:
    _ph = None  # type: ignore[assignment]
    VerifyMismatchError = Exception  # type: ignore[assignment,misc]


class LoginRequest(BaseModel):
    correo: str
    clave: str


@router.post("/sesion")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> JSONResponse:
    usuario = obtener_usuario_por_correo(db, body.correo)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    try:
        if _ph:
            _ph.verify(usuario.hash_clave, body.clave)
        else:
            if usuario.hash_clave != body.clave:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Credenciales inválidas") from None

    cookie_valor = firmar_cookie(usuario.id)
    resp = JSONResponse(
        content={"usuario_id": usuario.id, "correo": usuario.correo, "rol": usuario.rol},
    )
    resp.set_cookie(
        key=COOKIE_NAME,
        value=cookie_valor,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7,
    )
    return resp


@router.delete("/sesion", status_code=204)
def logout() -> JSONResponse:
    resp = JSONResponse(content=None, status_code=204)
    resp.delete_cookie(COOKIE_NAME)
    return resp
