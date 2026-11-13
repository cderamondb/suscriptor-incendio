"""Tests de máquina de estados del caso."""

import pytest

from app.dominio.estados import transitar
from app.dominio.modelos import EstadoCaso, TransicionInvalida


def test_flujo_normal():
    estado = EstadoCaso.BORRADOR
    estado = transitar(estado, EstadoCaso.DOCUMENTOS_CARGADOS)
    estado = transitar(estado, EstadoCaso.FICHA_EN_REVISION)
    estado = transitar(estado, EstadoCaso.FICHA_CONFIRMADA)
    estado = transitar(estado, EstadoCaso.PROPUESTA_EN_REVISION)
    estado = transitar(estado, EstadoCaso.PROPUESTA_APROBADA)
    estado = transitar(estado, EstadoCaso.COTIZADO)
    assert estado == EstadoCaso.COTIZADO


def test_declinacion_desde_cualquier_estado():
    for estado in EstadoCaso:
        if estado == EstadoCaso.DECLINADO:
            continue
        resultado = transitar(estado, EstadoCaso.DECLINADO)
        assert resultado == EstadoCaso.DECLINADO


def test_transiciones_invalidas():
    invalidas = [
        (EstadoCaso.BORRADOR, EstadoCaso.FICHA_CONFIRMADA),
        (EstadoCaso.DOCUMENTOS_CARGADOS, EstadoCaso.PROPUESTA_APROBADA),
        (EstadoCaso.COTIZADO, EstadoCaso.BORRADOR),
        (EstadoCaso.DECLINADO, EstadoCaso.BORRADOR),
        (EstadoCaso.DECLINADO, EstadoCaso.FICHA_EN_REVISION),
    ]
    for desde, hacia in invalidas:
        with pytest.raises(TransicionInvalida):
            transitar(desde, hacia)


def test_ficha_confirmada_puede_volver_a_revision():
    estado = transitar(EstadoCaso.FICHA_CONFIRMADA, EstadoCaso.FICHA_EN_REVISION)
    assert estado == EstadoCaso.FICHA_EN_REVISION
