"""Tests de control de presupuesto — C9."""

from unittest.mock import patch

import pytest

from app.agente.presupuesto import ControlPresupuesto
from app.dominio.modelos import PresupuestoAgotado


def test_c9_caso_agotado():
    ctrl = ControlPresupuesto(max_tokens_por_caso=1000, max_tokens_dia=10_000_000)
    ctrl.registrar("caso_1", 1000)
    with pytest.raises(PresupuestoAgotado) as exc:
        ctrl.verificar("caso_1")
    assert exc.value.tipo == "caso"


def test_c9_dia_agotado():
    ctrl = ControlPresupuesto(max_tokens_por_caso=10_000_000, max_tokens_dia=5000)
    ctrl.registrar("caso_1", 3000)
    ctrl.registrar("caso_2", 2000)
    with pytest.raises(PresupuestoAgotado) as exc:
        ctrl.verificar("caso_3")
    assert exc.value.tipo == "dia"


def test_presupuesto_ok():
    ctrl = ControlPresupuesto(max_tokens_por_caso=10000, max_tokens_dia=100000)
    ctrl.registrar("caso_1", 500)
    ctrl.verificar("caso_1")  # no lanza


def test_cambio_de_dia_chile():
    ctrl = ControlPresupuesto(max_tokens_por_caso=10_000_000, max_tokens_dia=1000)

    with patch("app.agente.presupuesto._hoy_chile", return_value="2025-01-01"):
        ctrl.registrar("caso_1", 1000)
        with pytest.raises(PresupuestoAgotado):
            ctrl.verificar("caso_2")

    with patch("app.agente.presupuesto._hoy_chile", return_value="2025-01-02"):
        ctrl.verificar("caso_2")  # nuevo día, no lanza
