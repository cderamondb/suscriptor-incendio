"""Manejadores uniformes de errores — §6.2."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.dominio.modelos import (
    DatosInsuficientes,
    FacultadExcedida,
    FueraDeApetito,
    FueraDeTarifa,
    PresupuestoAgotado,
    TransicionInvalida,
)


def _error_response(status: int, codigo: str, mensaje: str, detalle: dict | None = None):
    return JSONResponse(
        status_code=status,
        content={"error": {"codigo": codigo, "mensaje": mensaje, "detalle": detalle or {}}},
    )


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(DatosInsuficientes)
    async def _datos(request: Request, exc: DatosInsuficientes):
        return _error_response(409, "DATOS_INSUFICIENTES", str(exc), {"campos": exc.campos})

    @app.exception_handler(FueraDeTarifa)
    async def _tarifa(request: Request, exc: FueraDeTarifa):
        return _error_response(422, "FUERA_DE_TARIFA", str(exc), {"motivo": exc.motivo})

    @app.exception_handler(FueraDeApetito)
    async def _apetito(request: Request, exc: FueraDeApetito):
        return _error_response(
            422, "FUERA_DE_APETITO", str(exc),
            {"reglas": [{"codigo": r.codigo, "motivo": r.motivo} for r in exc.reglas]},
        )

    @app.exception_handler(FacultadExcedida)
    async def _facultad(request: Request, exc: FacultadExcedida):
        return _error_response(
            403, "FACULTAD_EXCEDIDA", str(exc),
            {"requiere": exc.requiere.value if exc.requiere else None},
        )

    @app.exception_handler(TransicionInvalida)
    async def _transicion(request: Request, exc: TransicionInvalida):
        return _error_response(
            409, "TRANSICION_INVALIDA", str(exc),
            {"desde": exc.desde.value, "hacia": exc.hacia.value},
        )

    @app.exception_handler(PresupuestoAgotado)
    async def _presupuesto(request: Request, exc: PresupuestoAgotado):
        return _error_response(429, "PRESUPUESTO_AGOTADO", str(exc), {"tipo": exc.tipo})
