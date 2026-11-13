"""Control de presupuesto de tokens por caso y por día — §7.1.

En F1 los contadores viven en memoria; en F2 migran a Postgres
manteniendo la misma interfaz pública.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.dominio.modelos import PresupuestoAgotado

ZONA_CHILE = timezone(timedelta(hours=-3))


def _hoy_chile() -> str:
    return datetime.now(ZONA_CHILE).strftime("%Y-%m-%d")


class ControlPresupuesto:
    def __init__(
        self,
        max_tokens_por_caso: int = 200_000,
        max_tokens_dia: int = 2_000_000,
    ) -> None:
        self.max_tokens_por_caso = max_tokens_por_caso
        self.max_tokens_dia = max_tokens_dia
        self._por_caso: dict[str, int] = {}
        self._por_dia: dict[str, int] = {}

    def tokens_caso(self, caso_id: str) -> int:
        return self._por_caso.get(caso_id, 0)

    def tokens_dia(self, dia: str | None = None) -> int:
        dia = dia or _hoy_chile()
        return self._por_dia.get(dia, 0)

    def verificar(self, caso_id: str) -> None:
        tokens_caso = self._por_caso.get(caso_id, 0)
        if tokens_caso >= self.max_tokens_por_caso:
            raise PresupuestoAgotado("caso")

        dia = _hoy_chile()
        tokens_dia = self._por_dia.get(dia, 0)
        if tokens_dia >= self.max_tokens_dia:
            raise PresupuestoAgotado("dia")

    def registrar(self, caso_id: str, tokens: int) -> None:
        self._por_caso[caso_id] = self._por_caso.get(caso_id, 0) + tokens
        dia = _hoy_chile()
        self._por_dia[dia] = self._por_dia.get(dia, 0) + tokens
