"""Consultas sobre el tarifario cargado."""

from __future__ import annotations

from decimal import Decimal

from app.dominio.modelos import (
    ClaseConstruccion,
    FactorConstruccion,
    FactorDeducible,
    FactorProteccion,
    FacultadRol,
    FueraDeTarifa,
    NivelProteccion,
    Ocupacion,
    RolUsuario,
    Tarifario,
    TasaSismo,
    TramoSiniestralidad,
)


class Repositorio:
    def __init__(self, tarifario: Tarifario) -> None:
        self._t = tarifario

    @property
    def tarifario(self) -> Tarifario:
        return self._t

    def obtener_ocupacion(self, codigo: str) -> Ocupacion:
        if codigo not in self._t.ocupaciones:
            raise FueraDeTarifa(f"ocupación no tarifada: {codigo}")
        return self._t.ocupaciones[codigo]

    def factor_construccion(self, clase: ClaseConstruccion) -> FactorConstruccion:
        if clase not in self._t.construccion:
            raise FueraDeTarifa(f"clase de construcción no tarifada: {clase}")
        return self._t.construccion[clase]

    def factor_proteccion(self, nivel: NivelProteccion) -> FactorProteccion:
        if nivel not in self._t.proteccion:
            raise FueraDeTarifa(f"nivel de protección no tarifado: {nivel}")
        return self._t.proteccion[nivel]

    def factor_deducible(self, monto_uf: Decimal) -> FactorDeducible:
        if monto_uf not in self._t.deducible:
            raise FueraDeTarifa(f"deducible no tarifado: {monto_uf} UF")
        return self._t.deducible[monto_uf]

    def tramo_siniestralidad(self, pct: Decimal) -> TramoSiniestralidad:
        for tramo in self._t.siniestralidad:
            if tramo.hasta_pct is None or pct <= tramo.hasta_pct:
                return tramo
        raise FueraDeTarifa(f"siniestralidad fuera de tramos: {pct}%")

    def tasa_sismo(self, zona: int) -> TasaSismo:
        if zona not in self._t.sismo:
            raise FueraDeTarifa(f"zona sísmica no tarifada: {zona}")
        return self._t.sismo[zona]

    def facultad(self, rol: RolUsuario) -> FacultadRol | None:
        return self._t.facultades.get(rol)

    def buscar_comparables(
        self,
        ocupacion_codigo: str,
        construccion_clase: ClaseConstruccion,
        suma_asegurada: Decimal,
        n: int = 5,
    ) -> list[dict[str, object]]:
        return []
