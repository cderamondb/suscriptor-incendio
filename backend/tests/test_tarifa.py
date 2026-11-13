"""Tests de tarificación — C1, C2, C3, C7 con valores exactos de §8."""

from decimal import Decimal

from app.dominio.modelos import TipoAlerta
from app.dominio.tarifa import tarificar


def test_c1_prima_bruta(ficha_c1, tarifario):
    p = tarificar(ficha_c1, tarifario)
    assert p.tasa_incendio == Decimal("0.6156")
    assert p.prima_bruta == Decimal("101.08")
    assert p.prima_neta == Decimal("84.94")
    assert p.iva == Decimal("16.14")
    assert p.comision == Decimal("12.74")


def test_c1_lineas_incendio(ficha_c1, tarifario):
    p = tarificar(ficha_c1, tarifario)
    incendio = [lin for lin in p.lineas if lin.cobertura.value == "INCENDIO"]
    assert len(incendio) == 2
    assert incendio[0].prima == Decimal("30.78")
    assert incendio[1].prima == Decimal("6.16")


def test_c1_lineas_sismo(ficha_c1, tarifario):
    p = tarificar(ficha_c1, tarifario)
    sismo = [lin for lin in p.lineas if lin.cobertura.value == "SISMO"]
    assert len(sismo) == 2
    assert sismo[0].prima == Decimal("40.00")
    assert sismo[1].prima == Decimal("8.00")


def test_c2_muebleria(ficha_c2, tarifario):
    p = tarificar(ficha_c2, tarifario, ajuste_comercial=Decimal("-0.10"))
    assert p.tasa_incendio == Decimal("3.6800")
    assert p.prima_tecnica == Decimal("184.00")
    assert p.prima_ajustada == Decimal("165.60")
    assert p.prima_neta == Decimal("165.60")
    assert p.iva == Decimal("31.46")
    assert p.prima_bruta == Decimal("197.06")


def test_c3_prima_minima_y_redondeo(ficha_c3, tarifario):
    p = tarificar(ficha_c3, tarifario)
    assert p.tasa_incendio == Decimal("0.4361")
    assert p.prima_neta == Decimal("15.00")
    assert p.iva == Decimal("2.85")
    assert p.prima_bruta == Decimal("17.85")
    tipos_alerta = [a.tipo for a in p.alertas]
    assert TipoAlerta.PRIMA_MINIMA_APLICADA in tipos_alerta


def test_c7_siniestralidad_alta(ficha_c7, tarifario):
    p = tarificar(ficha_c7, tarifario)
    assert p.tasa_incendio == Decimal("0.9720")
    assert p.prima_bruta == Decimal("126.52")
    assert p.prima_neta == Decimal("106.32")
    assert p.iva == Decimal("20.20")


def test_limites_tramo_siniestralidad(tarifario):
    """Verifica que los límites exactos de tramo se aplican correctamente."""

    tramos = tarifario.siniestralidad
    assert tramos[0].hasta_pct == Decimal("30")
    assert tramos[0].factor == Decimal("0.95")
    assert tramos[1].hasta_pct == Decimal("60")
    assert tramos[1].factor == Decimal("1.00")
    assert tramos[2].hasta_pct == Decimal("100")
    assert tramos[2].factor == Decimal("1.20")
    assert tramos[3].hasta_pct is None
    assert tramos[3].factor == Decimal("1.50")
