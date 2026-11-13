"""Catálogo de datos mínimos y evaluación de completitud — §6.1, §6.3."""

from __future__ import annotations

from app.dominio.modelos import (
    CampoFaltante,
    FichaRiesgo,
    ReporteCompletitud,
    TipoCobertura,
)


def evaluar_completitud(ficha: FichaRiesgo) -> ReporteCompletitud:
    faltantes: list[CampoFaltante] = []

    # Asegurado (bloqueantes)
    if ficha.razon_social.valor is None:
        faltantes.append(CampoFaltante(ruta="razon_social", bloqueante=True))
    if ficha.rut.valor is None:
        faltantes.append(CampoFaltante(ruta="rut", bloqueante=True))
    if ficha.actividad_declarada.valor is None:
        faltantes.append(CampoFaltante(ruta="actividad_declarada", bloqueante=True))

    if not ficha.ubicaciones:
        faltantes.append(CampoFaltante(ruta="ubicaciones", bloqueante=True))

    for i, ub in enumerate(ficha.ubicaciones):
        prefijo = f"ubicaciones[{i}]"

        # Ubicación (bloqueantes)
        if ub.direccion.valor is None:
            faltantes.append(CampoFaltante(ruta=f"{prefijo}.direccion", bloqueante=True))
        if ub.comuna.valor is None:
            faltantes.append(CampoFaltante(ruta=f"{prefijo}.comuna", bloqueante=True))
        if ub.region.valor is None:
            faltantes.append(CampoFaltante(ruta=f"{prefijo}.region", bloqueante=True))
        # Coordenadas: no bloqueante
        if ub.coordenadas.valor is None:
            faltantes.append(CampoFaltante(ruta=f"{prefijo}.coordenadas", bloqueante=False))

        # Ocupación (bloqueante)
        if ub.ocupacion_codigo.valor is None:
            faltantes.append(CampoFaltante(ruta=f"{prefijo}.ocupacion_codigo", bloqueante=True))

        # Construcción: clase bloqueante, resto no
        if ub.construccion_clase.valor is None:
            faltantes.append(CampoFaltante(
                ruta=f"{prefijo}.construccion.clase", bloqueante=True,
            ))
        if ub.construccion_pisos.valor is None:
            faltantes.append(CampoFaltante(
                ruta=f"{prefijo}.construccion.pisos", bloqueante=False,
            ))
        if ub.construccion_anio.valor is None:
            faltantes.append(CampoFaltante(
                ruta=f"{prefijo}.construccion.anio", bloqueante=False,
            ))
        if ub.construccion_superficie_m2.valor is None:
            faltantes.append(CampoFaltante(
                ruta=f"{prefijo}.construccion.superficie_m2", bloqueante=False,
            ))

        # Protecciones (bloqueante)
        if ub.proteccion.valor is None:
            faltantes.append(CampoFaltante(ruta=f"{prefijo}.proteccion", bloqueante=True))

        # Sumas aseguradas (al menos un ítem > 0)
        if not ub.items:
            faltantes.append(CampoFaltante(ruta=f"{prefijo}.items", bloqueante=True))

        # Zona sísmica: solo si se solicita sismo
        if TipoCobertura.SISMO in ficha.coberturas_solicitadas and ub.zona_sismica.valor is None:
            faltantes.append(CampoFaltante(
                ruta=f"{prefijo}.zona_sismica", bloqueante=True,
            ))

    # Coberturas (bloqueante)
    if not ficha.coberturas_solicitadas:
        faltantes.append(CampoFaltante(ruta="coberturas_solicitadas", bloqueante=True))

    # Deducible (bloqueante)
    if ficha.deducible_uf.valor is None:
        faltantes.append(CampoFaltante(ruta="deducible_uf", bloqueante=True))

    # Siniestralidad (no bloqueante, solo alerta)
    if ficha.siniestralidad.valor is None:
        faltantes.append(CampoFaltante(ruta="siniestralidad", bloqueante=False))

    # Vigencia (bloqueante)
    if ficha.vigencia_desde.valor is None:
        faltantes.append(CampoFaltante(ruta="vigencia_desde", bloqueante=True))
    if ficha.vigencia_hasta.valor is None:
        faltantes.append(CampoFaltante(ruta="vigencia_hasta", bloqueante=True))

    # Antecedentes (no bloqueante)
    if ficha.aseguradora_anterior.valor is None:
        faltantes.append(CampoFaltante(ruta="aseguradora_anterior", bloqueante=False))
    if ficha.prima_anterior.valor is None:
        faltantes.append(CampoFaltante(ruta="prima_anterior", bloqueante=False))
    if ficha.inspeccion.valor is None:
        faltantes.append(CampoFaltante(ruta="inspeccion", bloqueante=False))

    bloqueantes = [f for f in faltantes if f.bloqueante]
    return ReporteCompletitud(
        completo=len(bloqueantes) == 0,
        faltantes=faltantes,
    )
