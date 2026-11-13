"""Tests de datos mínimos — C5 y completitud."""

from app.dominio.datos_minimos import evaluar_completitud
from app.dominio.modelos import TipoCobertura


def test_c5_faltante_bloqueante(ficha_c5):
    """C5: C1 sin clase de construcción → bloqueante."""
    r = evaluar_completitud(ficha_c5)
    assert not r.completo
    rutas_bloqueantes = [f.ruta for f in r.faltantes if f.bloqueante]
    assert "ubicaciones[0].construccion.clase" in rutas_bloqueantes


def test_ficha_c1_completa(ficha_c1):
    """C1 completa: sin bloqueantes."""
    r = evaluar_completitud(ficha_c1)
    bloqueantes = [f for f in r.faltantes if f.bloqueante]
    assert bloqueantes == []
    assert r.completo


def test_zona_sismica_condicional(ficha_c1):
    """Zona sísmica es bloqueante solo si se solicita sismo."""
    ficha_c1.ubicaciones[0].zona_sismica.valor = None
    ficha_c1.coberturas_solicitadas = [TipoCobertura.INCENDIO, TipoCobertura.SISMO]
    r = evaluar_completitud(ficha_c1)
    rutas_bloqueantes = [f.ruta for f in r.faltantes if f.bloqueante]
    assert "ubicaciones[0].zona_sismica" in rutas_bloqueantes

    ficha_c1.coberturas_solicitadas = [TipoCobertura.INCENDIO]
    r2 = evaluar_completitud(ficha_c1)
    rutas_bloqueantes2 = [f.ruta for f in r2.faltantes if f.bloqueante]
    assert "ubicaciones[0].zona_sismica" not in rutas_bloqueantes2
