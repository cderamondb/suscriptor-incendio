"""Tests de facultades — C6."""

from decimal import Decimal

import pytest

from app.dominio.apetito import evaluar_apetito
from app.dominio.facultades import exigir_facultad, verificar_facultad
from app.dominio.modelos import (
    FacultadExcedida,
    NivelApetito,
    ResultadoApetito,
    RolUsuario,
)


def test_c6_suscriptor_excedido_ajuste(ficha_c1, tarifario):
    """C1 con ajuste -20%: SUSCRIPTOR excedido (±15%)."""
    apetito = evaluar_apetito(ficha_c1, tarifario)
    suma = Decimal("60000")
    r = verificar_facultad(suma, Decimal("-0.20"), apetito, RolUsuario.SUSCRIPTOR, tarifario)
    assert not r.permitido
    assert r.requiere == RolUsuario.SUSCRIPTOR_SENIOR


def test_c6_senior_aprueba_ajuste_20(ficha_c1, tarifario):
    """C1 con ajuste -20%: SUSCRIPTOR_SENIOR aprueba (±25%)."""
    apetito = evaluar_apetito(ficha_c1, tarifario)
    suma = Decimal("60000")
    r = verificar_facultad(suma, Decimal("-0.20"), apetito, RolUsuario.SUSCRIPTOR_SENIOR, tarifario)
    assert r.permitido


def test_c6_ajuste_30_requiere_comite(ficha_c1, tarifario):
    """C1 con ajuste -30%: requiere COMITE (excede ±25% de senior)."""
    apetito = evaluar_apetito(ficha_c1, tarifario)
    suma = Decimal("60000")
    r = verificar_facultad(suma, Decimal("-0.30"), apetito, RolUsuario.SUSCRIPTOR_SENIOR, tarifario)
    assert not r.permitido
    assert r.requiere is None  # COMITE (fuera de todos los roles)


def test_c6_referir_suscriptor_no_aprueba(tarifario):
    """Apetito REFERIR: SUSCRIPTOR no puede aprobar."""
    apetito = ResultadoApetito(resultado=NivelApetito.REFERIR, reglas_activadas=[])
    suma = Decimal("60000")
    r = verificar_facultad(suma, Decimal("0"), apetito, RolUsuario.SUSCRIPTOR, tarifario)
    assert not r.permitido
    assert r.requiere == RolUsuario.SUSCRIPTOR_SENIOR


def test_c6_referir_senior_aprueba(tarifario):
    """Apetito REFERIR: SUSCRIPTOR_SENIOR puede aprobar."""
    apetito = ResultadoApetito(resultado=NivelApetito.REFERIR, reglas_activadas=[])
    suma = Decimal("60000")
    r = verificar_facultad(suma, Decimal("0"), apetito, RolUsuario.SUSCRIPTOR_SENIOR, tarifario)
    assert r.permitido


def test_exigir_facultad_excedida(ficha_c1, tarifario):
    apetito = evaluar_apetito(ficha_c1, tarifario)
    suma = Decimal("60000")
    with pytest.raises(FacultadExcedida):
        exigir_facultad(suma, Decimal("-0.20"), apetito, RolUsuario.SUSCRIPTOR, tarifario)
