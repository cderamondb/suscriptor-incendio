"""Verificación de facultades por rol — §6.1 verificar_facultad."""

from __future__ import annotations

from decimal import Decimal

from app.dominio.modelos import (
    FacultadExcedida,
    NivelApetito,
    ResultadoApetito,
    ResultadoFacultad,
    RolUsuario,
    Tarifario,
)


def verificar_facultad(
    suma_asegurada_total: Decimal,
    ajuste_comercial: Decimal,
    apetito: ResultadoApetito,
    rol: RolUsuario,
    tarifario: Tarifario,
) -> ResultadoFacultad:
    facultad = tarifario.facultades.get(rol)

    if facultad is None:
        return ResultadoFacultad(permitido=False, requiere=RolUsuario.SUSCRIPTOR)

    ajuste_abs = abs(ajuste_comercial) * Decimal("100")

    if suma_asegurada_total > facultad.max_suma_asegurada_uf:
        if rol == RolUsuario.SUSCRIPTOR:
            senior = tarifario.facultades.get(RolUsuario.SUSCRIPTOR_SENIOR)
            if senior and suma_asegurada_total <= senior.max_suma_asegurada_uf:
                return ResultadoFacultad(permitido=False, requiere=RolUsuario.SUSCRIPTOR_SENIOR)
        return ResultadoFacultad(permitido=False, requiere=None)

    if ajuste_abs > facultad.max_ajuste_pct:
        if rol == RolUsuario.SUSCRIPTOR:
            senior = tarifario.facultades.get(RolUsuario.SUSCRIPTOR_SENIOR)
            if senior and ajuste_abs <= senior.max_ajuste_pct:
                return ResultadoFacultad(permitido=False, requiere=RolUsuario.SUSCRIPTOR_SENIOR)
        return ResultadoFacultad(permitido=False, requiere=None)

    if apetito.resultado == NivelApetito.REFERIR and not facultad.aprueba_referir:
        return ResultadoFacultad(permitido=False, requiere=RolUsuario.SUSCRIPTOR_SENIOR)

    if apetito.resultado == NivelApetito.DECLINAR:
        return ResultadoFacultad(permitido=False, requiere=None)

    return ResultadoFacultad(permitido=True, requiere=None)


def exigir_facultad(
    suma_asegurada_total: Decimal,
    ajuste_comercial: Decimal,
    apetito: ResultadoApetito,
    rol: RolUsuario,
    tarifario: Tarifario,
) -> None:
    resultado = verificar_facultad(
        suma_asegurada_total, ajuste_comercial, apetito, rol, tarifario,
    )
    if not resultado.permitido:
        raise FacultadExcedida(requiere=resultado.requiere)
