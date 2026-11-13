"""Generador de cotización PDF — §6.1 generar_cotizacion.

Incluye: número, asegurado, ubicaciones, coberturas, sumas, deducibles,
prima neta, IVA, prima bruta, vigencia 30 días, condiciones.
NO incluye: tasa técnica, factores, comparables, apetito, notas internas.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.dominio.modelos import PropuestaTarifa


def _formato_monto(valor: Decimal | str) -> str:
    if isinstance(valor, str):
        try:
            valor = Decimal(valor)
        except Exception:
            return str(valor)
    partes = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return partes


def generar_cotizacion(propuesta: PropuestaTarifa, caso: object) -> bytes:
    plantillas_dir = Path(__file__).parent / "plantillas"
    env = Environment(loader=FileSystemLoader(str(plantillas_dir)), autoescape=True)
    env.filters["monto"] = _formato_monto
    template = env.get_template("cotizacion.html")

    ubicaciones_data = []
    lineas_por_ub: dict[int, list[dict]] = {}
    for linea in propuesta.lineas:
        if linea.ubicacion_idx not in lineas_por_ub:
            lineas_por_ub[linea.ubicacion_idx] = []
        lineas_por_ub[linea.ubicacion_idx].append({
            "item": linea.item_tipo.value,
            "cobertura": linea.cobertura.value,
            "suma_asegurada": _formato_monto(linea.suma_asegurada),
            "prima": _formato_monto(linea.prima),
        })

    ficha = caso.ficha if hasattr(caso, "ficha") and caso.ficha else {}

    for idx in sorted(lineas_por_ub.keys()):
        direccion = f"Ubicación {idx + 1}"
        if isinstance(ficha, dict):
            ubics = ficha.get("ubicaciones", [])
            if isinstance(ubics, list) and idx < len(ubics):
                ub_data = ubics[idx]
                if isinstance(ub_data, dict):
                    dir_campo = ub_data.get("direccion", {})
                    if isinstance(dir_campo, dict):
                        direccion = dir_campo.get("valor", direccion) or direccion

        ubicaciones_data.append({
            "direccion": direccion,
            "lineas": lineas_por_ub[idx],
        })

    deducible = ""
    if isinstance(ficha, dict):
        ded_campo = ficha.get("deducible_uf", {})
        if isinstance(ded_campo, dict):
            deducible = str(ded_campo.get("valor", ""))

    numero = getattr(caso, "id", "")[:8].upper() if hasattr(caso, "id") else "000"
    fecha_emision = datetime.now(UTC).strftime("%d-%m-%Y")

    html = template.render(
        numero=numero,
        asegurado=getattr(caso, "asegurado", ""),
        rut=getattr(caso, "rut", ""),
        corredor=getattr(caso, "corredor", ""),
        ubicaciones=ubicaciones_data,
        prima_neta=_formato_monto(propuesta.prima_neta),
        iva=_formato_monto(propuesta.iva),
        prima_bruta=_formato_monto(propuesta.prima_bruta),
        comision=_formato_monto(propuesta.comision),
        deducible=deducible,
        fecha_emision=fecha_emision,
    )

    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except (ImportError, OSError):
        return html.encode("utf-8")
