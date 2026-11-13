"""Tests de apetito — C1, C2, C4, C7, suma > 500k."""

from decimal import Decimal

from app.dominio.apetito import evaluar_apetito
from app.dominio.modelos import (
    Campo,
    ClaseConstruccion,
    EstadoCampo,
    FichaRiesgo,
    ItemAsegurado,
    NivelApetito,
    NivelProteccion,
    TipoCobertura,
    TipoItem,
    UbicacionRiesgo,
)


def test_c1_dentro(ficha_c1, tarifario):
    r = evaluar_apetito(ficha_c1, tarifario)
    assert r.resultado == NivelApetito.DENTRO
    assert r.reglas_activadas == []


def test_c2_referir(ficha_c2, tarifario):
    r = evaluar_apetito(ficha_c2, tarifario)
    assert r.resultado == NivelApetito.REFERIR
    codigos = [reg.codigo for reg in r.reglas_activadas]
    assert "OCUPACION_REFERIR" in codigos


def test_c4_declinar(ficha_c4, tarifario):
    r = evaluar_apetito(ficha_c4, tarifario)
    assert r.resultado == NivelApetito.DECLINAR
    codigos = [reg.codigo for reg in r.reglas_activadas]
    assert "OCUPACION_DECLINADA" in codigos


def test_c7_referir_siniestralidad(ficha_c7, tarifario):
    r = evaluar_apetito(ficha_c7, tarifario)
    assert r.resultado == NivelApetito.REFERIR
    codigos = [reg.codigo for reg in r.reglas_activadas]
    assert "SINIESTRALIDAD_ALTA" in codigos


def test_suma_asegurada_alta(tarifario):
    def _campo(valor):
        return Campo(valor=valor, estado=EstadoCampo.CONFIRMADO)

    ficha = FichaRiesgo(
        razon_social=_campo("Test"),
        rut=_campo("76.000.000-0"),
        actividad_declarada=_campo("Oficinas"),
        ubicaciones=[UbicacionRiesgo(
            direccion=_campo("Test 1"),
            comuna=_campo("Santiago"),
            region=_campo("Metropolitana"),
            ocupacion_codigo=_campo("OC-101"),
            construccion_clase=_campo(ClaseConstruccion.A),
            proteccion=_campo(NivelProteccion.EXTINTORES),
            items=[
                ItemAsegurado(tipo=TipoItem.EDIFICIO, suma_asegurada=Decimal("600000")),
            ],
        )],
        coberturas_solicitadas=[TipoCobertura.INCENDIO],
        deducible_uf=_campo(Decimal("10")),
        vigencia_desde=_campo("2025-01-01"),
        vigencia_hasta=_campo("2026-01-01"),
    )
    r = evaluar_apetito(ficha, tarifario)
    assert r.resultado == NivelApetito.REFERIR
    codigos = [reg.codigo for reg in r.reglas_activadas]
    assert "SUMA_ASEGURADA_ALTA" in codigos
