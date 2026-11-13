"""Máquina de estados del caso — §6.1."""

from __future__ import annotations

from app.dominio.modelos import EstadoCaso, TransicionInvalida

TRANSICIONES_VALIDAS: dict[EstadoCaso, set[EstadoCaso]] = {
    EstadoCaso.BORRADOR: {EstadoCaso.DOCUMENTOS_CARGADOS, EstadoCaso.DECLINADO},
    EstadoCaso.DOCUMENTOS_CARGADOS: {EstadoCaso.FICHA_EN_REVISION, EstadoCaso.DECLINADO},
    EstadoCaso.FICHA_EN_REVISION: {EstadoCaso.FICHA_CONFIRMADA, EstadoCaso.DECLINADO},
    EstadoCaso.FICHA_CONFIRMADA: {
        EstadoCaso.PROPUESTA_EN_REVISION,
        EstadoCaso.FICHA_EN_REVISION,
        EstadoCaso.DECLINADO,
    },
    EstadoCaso.PROPUESTA_EN_REVISION: {EstadoCaso.PROPUESTA_APROBADA, EstadoCaso.DECLINADO},
    EstadoCaso.PROPUESTA_APROBADA: {EstadoCaso.COTIZADO, EstadoCaso.DECLINADO},
    EstadoCaso.COTIZADO: {EstadoCaso.DECLINADO},
    EstadoCaso.DECLINADO: set(),
}


def transitar(actual: EstadoCaso, nuevo: EstadoCaso) -> EstadoCaso:
    permitidos = TRANSICIONES_VALIDAS.get(actual, set())
    if nuevo not in permitidos:
        raise TransicionInvalida(actual, nuevo)
    return nuevo
