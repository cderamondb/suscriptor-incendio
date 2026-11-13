"""Motor de tarificación determinista — §6.1 pasos 1-6."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.dominio.modelos import (
    Alerta,
    ClaseConstruccion,
    DatosInsuficientes,
    FichaRiesgo,
    FueraDeTarifa,
    HistorialSiniestralidad,
    LineaPrima,
    NivelProteccion,
    PropuestaTarifa,
    Tarifario,
    TipoAlerta,
    TipoCobertura,
)


def r4(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def r2(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calcular_siniestralidad_pct(historial: HistorialSiniestralidad | None) -> Decimal | None:
    if historial is None:
        return None
    if historial.primas_pagadas is None or historial.primas_pagadas == 0:
        return None
    total_incurrido = sum(
        (s.monto_incurrido for s in historial.siniestros if s.monto_incurrido is not None),
        Decimal("0"),
    )
    return r2(total_incurrido / historial.primas_pagadas * Decimal("100"))


def tarificar(
    ficha: FichaRiesgo,
    tarifario: Tarifario,
    ajuste_comercial: Decimal = Decimal("0"),
) -> PropuestaTarifa:
    alertas: list[Alerta] = []

    campos_faltantes: list[str] = []
    if not ficha.ubicaciones:
        campos_faltantes.append("ubicaciones")
    if not ficha.coberturas_solicitadas:
        campos_faltantes.append("coberturas_solicitadas")
    if ficha.deducible_uf.valor is None:
        campos_faltantes.append("deducible_uf")

    for i, ub in enumerate(ficha.ubicaciones):
        if ub.ocupacion_codigo.valor is None:
            campos_faltantes.append(f"ubicaciones[{i}].ocupacion_codigo")
        if ub.construccion_clase.valor is None:
            campos_faltantes.append(f"ubicaciones[{i}].construccion.clase")
        if ub.proteccion.valor is None:
            campos_faltantes.append(f"ubicaciones[{i}].proteccion")
        if not ub.items:
            campos_faltantes.append(f"ubicaciones[{i}].items")
        if (
            TipoCobertura.SISMO in ficha.coberturas_solicitadas
            and ub.zona_sismica.valor is None
        ):
            campos_faltantes.append(f"ubicaciones[{i}].zona_sismica")

    if campos_faltantes:
        raise DatosInsuficientes(campos_faltantes)

    assert ficha.deducible_uf.valor is not None

    ub0 = ficha.ubicaciones[0]
    assert ub0.ocupacion_codigo.valor is not None
    assert ub0.construccion_clase.valor is not None
    assert ub0.proteccion.valor is not None

    ocupacion_codigo: str = ub0.ocupacion_codigo.valor
    clase: ClaseConstruccion = ub0.construccion_clase.valor
    proteccion: NivelProteccion = ub0.proteccion.valor
    deducible_uf: Decimal = ficha.deducible_uf.valor

    if ocupacion_codigo not in tarifario.ocupaciones:
        raise FueraDeTarifa(f"ocupación no tarifada: {ocupacion_codigo}")

    ocupacion = tarifario.ocupaciones[ocupacion_codigo]
    tasa_base = ocupacion.tasa_base_por_mil

    if clase not in tarifario.construccion:
        raise FueraDeTarifa(f"clase de construcción no tarifada: {clase}")
    f_construccion = tarifario.construccion[clase].factor

    if proteccion not in tarifario.proteccion:
        raise FueraDeTarifa(f"protección no tarifada: {proteccion}")
    f_proteccion = tarifario.proteccion[proteccion].factor

    if deducible_uf not in tarifario.deducible:
        raise FueraDeTarifa(f"deducible no tarifado: {deducible_uf} UF")
    f_deducible = tarifario.deducible[deducible_uf].factor

    # Siniestralidad
    historial = ficha.siniestralidad.valor if ficha.siniestralidad.valor else None
    siniestralidad_pct = _calcular_siniestralidad_pct(historial)

    if siniestralidad_pct is None:
        f_siniestralidad = Decimal("1.00")
        alertas.append(Alerta(
            tipo=TipoAlerta.SIN_HISTORIAL, detalle="Sin historial de siniestralidad",
        ))
    else:
        f_siniestralidad = Decimal("1.00")
        for tramo in tarifario.siniestralidad:
            if tramo.hasta_pct is None or siniestralidad_pct <= tramo.hasta_pct:
                f_siniestralidad = tramo.factor
                break

    # Paso 1: tasa incendio
    tasa_incendio = r4(tasa_base * f_construccion * f_proteccion * f_deducible * f_siniestralidad)

    # Paso 2: tasa sismo (si aplica)
    tasa_sismo: Decimal | None = None
    if TipoCobertura.SISMO in ficha.coberturas_solicitadas:
        zona = ub0.zona_sismica.valor
        assert zona is not None
        if zona not in tarifario.sismo:
            raise FueraDeTarifa(f"zona sísmica no tarifada: {zona}")
        tasa_sismo = r4(tarifario.sismo[zona].tasas[clase])

    # Pasos 3-4: primas por línea
    lineas: list[LineaPrima] = []
    for i, ub in enumerate(ficha.ubicaciones):
        for item in ub.items:
            lineas.append(LineaPrima(
                ubicacion_idx=i,
                item_tipo=item.tipo,
                cobertura=TipoCobertura.INCENDIO,
                suma_asegurada=item.suma_asegurada,
                tasa_por_mil=tasa_incendio,
                prima=r2(item.suma_asegurada * tasa_incendio / Decimal("1000")),
            ))
            if tasa_sismo is not None:
                assert ub.zona_sismica.valor is not None
                zona_ub = ub.zona_sismica.valor
                clase_ub = ub.construccion_clase.valor
                assert clase_ub is not None
                tasa_sismo_ub = r4(tarifario.sismo[zona_ub].tasas[clase_ub])
                lineas.append(LineaPrima(
                    ubicacion_idx=i,
                    item_tipo=item.tipo,
                    cobertura=TipoCobertura.SISMO,
                    suma_asegurada=item.suma_asegurada,
                    tasa_por_mil=tasa_sismo_ub,
                    prima=r2(item.suma_asegurada * tasa_sismo_ub / Decimal("1000")),
                ))

    prima_tecnica = sum((lin.prima for lin in lineas), Decimal("0"))

    # Paso 4: ajuste comercial
    prima_ajustada = r2(prima_tecnica * (Decimal("1") + ajuste_comercial))

    # Paso 5: prima mínima
    prima_minima = tarifario.parametros.prima_minima
    prima_neta = max(prima_ajustada, prima_minima)
    if prima_ajustada < prima_minima:
        alertas.append(Alerta(
            tipo=TipoAlerta.PRIMA_MINIMA_APLICADA,
            detalle=f"Prima ajustada {prima_ajustada} UF < mínima {prima_minima} UF",
        ))

    # Paso 6: IVA, bruta, comisión
    tasa_iva = Decimal("0.19")
    iva = r2(prima_neta * tasa_iva)
    prima_bruta = prima_neta + iva
    comision = r2(prima_neta * tarifario.parametros.pct_comision)

    return PropuestaTarifa(
        version_tarifario=tarifario.parametros.version,
        tasa_incendio=tasa_incendio,
        tasa_sismo=tasa_sismo,
        factor_construccion=f_construccion,
        factor_proteccion=f_proteccion,
        factor_deducible=f_deducible,
        factor_siniestralidad=f_siniestralidad,
        lineas=lineas,
        prima_tecnica=prima_tecnica,
        ajuste_comercial=ajuste_comercial,
        prima_ajustada=prima_ajustada,
        prima_neta=prima_neta,
        iva=iva,
        prima_bruta=prima_bruta,
        comision=comision,
        alertas=alertas,
    )
