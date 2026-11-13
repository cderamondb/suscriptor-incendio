"""Fixtures compartidos para todos los tests de F1."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.catalogo.cargador import cargar_tarifario
from app.catalogo.repositorio import Repositorio
from app.dominio.modelos import (
    Campo,
    ClaseConstruccion,
    EstadoCampo,
    FichaRiesgo,
    HistorialSiniestralidad,
    ItemAsegurado,
    NivelProteccion,
    Siniestro,
    TipoCobertura,
    TipoItem,
    UbicacionRiesgo,
)

TARIFARIO_PATH = (
    Path(__file__).resolve().parent.parent.parent / "datos" / "ejemplo" / "tarifario.xlsx"
)


@pytest.fixture
def tarifario():
    return cargar_tarifario(TARIFARIO_PATH)


@pytest.fixture
def repositorio(tarifario):
    return Repositorio(tarifario)


def _campo(valor, estado=EstadoCampo.CONFIRMADO):
    return Campo(valor=valor, estado=estado)


def _ubicacion_c1():
    return UbicacionRiesgo(
        direccion=_campo("Av. Providencia 1234"),
        comuna=_campo("Providencia"),
        region=_campo("Metropolitana"),
        ocupacion_codigo=_campo("OC-101"),
        construccion_clase=_campo(ClaseConstruccion.A),
        proteccion=_campo(NivelProteccion.RED_HUMEDA_DETECCION),
        items=[
            ItemAsegurado(tipo=TipoItem.EDIFICIO, suma_asegurada=Decimal("50000")),
            ItemAsegurado(tipo=TipoItem.CONTENIDOS, suma_asegurada=Decimal("10000")),
        ],
        zona_sismica=_campo(2),
    )


@pytest.fixture
def ficha_c1():
    return FichaRiesgo(
        razon_social=_campo("Comercializadora Demo SpA"),
        rut=_campo("76.123.456-7"),
        actividad_declarada=_campo("Arriendo de oficinas"),
        ubicaciones=[_ubicacion_c1()],
        coberturas_solicitadas=[TipoCobertura.INCENDIO, TipoCobertura.SISMO],
        deducible_uf=_campo(Decimal("10")),
        siniestralidad=_campo(HistorialSiniestralidad(
            siniestros=[],
            primas_pagadas=Decimal("500"),
        )),
        vigencia_desde=_campo("2025-01-01"),
        vigencia_hasta=_campo("2026-01-01"),
    )


@pytest.fixture
def ficha_c2():
    return FichaRiesgo(
        razon_social=_campo("Mueblería Ficticia SpA"),
        rut=_campo("76.987.654-3"),
        actividad_declarada=_campo("Fabricación de muebles"),
        ubicaciones=[UbicacionRiesgo(
            direccion=_campo("Calle Industrial 567"),
            comuna=_campo("Maipú"),
            region=_campo("Metropolitana"),
            ocupacion_codigo=_campo("OC-310"),
            construccion_clase=_campo(ClaseConstruccion.C),
            proteccion=_campo(NivelProteccion.EXTINTORES),
            items=[
                ItemAsegurado(tipo=TipoItem.EDIFICIO, suma_asegurada=Decimal("30000")),
                ItemAsegurado(tipo=TipoItem.MAQUINARIA, suma_asegurada=Decimal("15000")),
                ItemAsegurado(tipo=TipoItem.EXISTENCIAS, suma_asegurada=Decimal("5000")),
            ],
        )],
        coberturas_solicitadas=[TipoCobertura.INCENDIO],
        deducible_uf=_campo(Decimal("50")),
        siniestralidad=_campo(HistorialSiniestralidad(
            siniestros=[
                Siniestro(
                    fecha="2022-06-15", causa="Cortocircuito",
                    monto_incurrido=Decimal("4500"),
                ),
            ],
            primas_pagadas=Decimal("10000"),
        )),
        vigencia_desde=_campo("2025-01-01"),
        vigencia_hasta=_campo("2026-01-01"),
    )


@pytest.fixture
def ficha_c3():
    return FichaRiesgo(
        razon_social=_campo("Oficina Pequeña Ltda"),
        rut=_campo("76.111.222-3"),
        actividad_declarada=_campo("Oficinas"),
        ubicaciones=[UbicacionRiesgo(
            direccion=_campo("Pasaje Test 100"),
            comuna=_campo("Santiago"),
            region=_campo("Metropolitana"),
            ocupacion_codigo=_campo("OC-101"),
            construccion_clase=_campo(ClaseConstruccion.A),
            proteccion=_campo(NivelProteccion.ROCIADORES),
            items=[
                ItemAsegurado(tipo=TipoItem.EDIFICIO, suma_asegurada=Decimal("10000")),
            ],
        )],
        coberturas_solicitadas=[TipoCobertura.INCENDIO],
        deducible_uf=_campo(Decimal("100")),
        siniestralidad=_campo(HistorialSiniestralidad(
            siniestros=[],
            primas_pagadas=Decimal("200"),
        )),
        vigencia_desde=_campo("2025-01-01"),
        vigencia_hasta=_campo("2026-01-01"),
    )


@pytest.fixture
def ficha_c4():
    return FichaRiesgo(
        razon_social=_campo("Pirotecnia Ficticia SpA"),
        rut=_campo("76.444.555-6"),
        actividad_declarada=_campo("Fabricación de fuegos artificiales"),
        ubicaciones=[UbicacionRiesgo(
            direccion=_campo("Camino Rural 999"),
            comuna=_campo("Buin"),
            region=_campo("Metropolitana"),
            ocupacion_codigo=_campo("OC-999"),
            construccion_clase=_campo(ClaseConstruccion.D),
            proteccion=_campo(NivelProteccion.EXTINTORES),
            items=[
                ItemAsegurado(tipo=TipoItem.EDIFICIO, suma_asegurada=Decimal("20000")),
            ],
        )],
        coberturas_solicitadas=[TipoCobertura.INCENDIO],
        deducible_uf=_campo(Decimal("10")),
        vigencia_desde=_campo("2025-01-01"),
        vigencia_hasta=_campo("2026-01-01"),
    )


@pytest.fixture
def ficha_c5():
    """C1 sin clase de construcción."""
    ub = _ubicacion_c1()
    ub.construccion_clase = Campo()  # FALTANTE
    return FichaRiesgo(
        razon_social=_campo("Comercializadora Demo SpA"),
        rut=_campo("76.123.456-7"),
        actividad_declarada=_campo("Arriendo de oficinas"),
        ubicaciones=[ub],
        coberturas_solicitadas=[TipoCobertura.INCENDIO, TipoCobertura.SISMO],
        deducible_uf=_campo(Decimal("10")),
        vigencia_desde=_campo("2025-01-01"),
        vigencia_hasta=_campo("2026-01-01"),
    )


@pytest.fixture
def ficha_c7():
    """C1 con siniestralidad 120%."""
    return FichaRiesgo(
        razon_social=_campo("Comercializadora Demo SpA"),
        rut=_campo("76.123.456-7"),
        actividad_declarada=_campo("Arriendo de oficinas"),
        ubicaciones=[_ubicacion_c1()],
        coberturas_solicitadas=[TipoCobertura.INCENDIO, TipoCobertura.SISMO],
        deducible_uf=_campo(Decimal("10")),
        siniestralidad=_campo(HistorialSiniestralidad(
            siniestros=[
                Siniestro(fecha="2021-03-10", causa="Incendio eléctrico",
                          monto_incurrido=Decimal("6000")),
            ],
            primas_pagadas=Decimal("5000"),
        )),
        vigencia_desde=_campo("2025-01-01"),
        vigencia_hasta=_campo("2026-01-01"),
    )
