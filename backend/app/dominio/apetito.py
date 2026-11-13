"""Evaluación de apetito de riesgo — §6.1 evaluar_apetito."""

from __future__ import annotations

from decimal import Decimal

from app.dominio.modelos import (
    FichaRiesgo,
    HistorialSiniestralidad,
    NivelApetito,
    ReglaActivada,
    ResultadoApetito,
    Tarifario,
)


def _calcular_siniestralidad_pct(historial: HistorialSiniestralidad | None) -> Decimal | None:
    if historial is None:
        return None
    if historial.primas_pagadas is None or historial.primas_pagadas == 0:
        return None
    total = sum(
        (s.monto_incurrido for s in historial.siniestros if s.monto_incurrido is not None),
        Decimal("0"),
    )
    from app.dominio.tarifa import r2
    return r2(total / historial.primas_pagadas * Decimal("100"))


def evaluar_apetito(ficha: FichaRiesgo, tarifario: Tarifario) -> ResultadoApetito:
    reglas: list[ReglaActivada] = []
    resultado = NivelApetito.DENTRO

    for i, ub in enumerate(ficha.ubicaciones):
        codigo = ub.ocupacion_codigo.valor
        if codigo is None:
            continue
        ocupacion = tarifario.ocupaciones.get(codigo)
        if ocupacion is None:
            continue

        if ocupacion.apetito == NivelApetito.DECLINAR:
            reglas.append(ReglaActivada(
                codigo="OCUPACION_DECLINADA",
                motivo=f"Ocupación {codigo} ({ocupacion.descripcion}) fuera de apetito",
            ))
            resultado = NivelApetito.DECLINAR
        elif ocupacion.apetito == NivelApetito.REFERIR:
            reglas.append(ReglaActivada(
                codigo="OCUPACION_REFERIR",
                motivo=f"Ocupación {codigo} ({ocupacion.descripcion}) requiere referir",
            ))
            if resultado != NivelApetito.DECLINAR:
                resultado = NivelApetito.REFERIR

        # Suma asegurada total por ubicación > 500,000 UF → REFERIR
        suma_total = sum(item.suma_asegurada for item in ub.items)
        if suma_total > Decimal("500000"):
            reglas.append(ReglaActivada(
                codigo="SUMA_ASEGURADA_ALTA",
                motivo=f"Ubicación {i}: suma asegurada {suma_total} UF > 500.000 UF",
            ))
            if resultado != NivelApetito.DECLINAR:
                resultado = NivelApetito.REFERIR

    # Siniestralidad
    historial = ficha.siniestralidad.valor if ficha.siniestralidad.valor else None
    siniestralidad_pct = _calcular_siniestralidad_pct(historial)

    if siniestralidad_pct is not None:
        for tramo in tarifario.siniestralidad:
            if tramo.hasta_pct is None or siniestralidad_pct <= tramo.hasta_pct:
                if tramo.apetito == NivelApetito.REFERIR:
                    reglas.append(ReglaActivada(
                        codigo="SINIESTRALIDAD_ALTA",
                        motivo=f"Siniestralidad {siniestralidad_pct}% requiere referir",
                    ))
                    if resultado != NivelApetito.DECLINAR:
                        resultado = NivelApetito.REFERIR
                break

    return ResultadoApetito(resultado=resultado, reglas_activadas=reglas)
