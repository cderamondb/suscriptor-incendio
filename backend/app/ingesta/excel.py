"""Extracción de contenido de archivos Excel con openpyxl."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell

from app.ingesta.errores import ArchivoCorrupto


@dataclass
class CeldaExcel:
    hoja: str
    celda: str
    valor: str
    rango_combinado: str | None = None


@dataclass
class DocumentoExcel:
    hojas: list[str] = field(default_factory=list)
    celdas: list[CeldaExcel] = field(default_factory=list)


def extraer_excel(contenido: bytes) -> DocumentoExcel:
    try:
        wb = load_workbook(BytesIO(contenido), read_only=False, data_only=True)
    except Exception as e:
        raise ArchivoCorrupto(str(e)) from e

    hojas = wb.sheetnames
    celdas: list[CeldaExcel] = []

    for nombre_hoja in hojas:
        ws = wb[nombre_hoja]

        rangos_combinados: dict[str, str] = {}
        for rango in ws.merged_cells.ranges:
            rango_str = str(rango)
            for celda in rango.cells:
                coord = ws.cell(row=celda[0], column=celda[1]).coordinate
                rangos_combinados[f"{nombre_hoja}!{coord}"] = rango_str

        for fila in ws.iter_rows():
            for celda in fila:
                if isinstance(celda, MergedCell):
                    continue
                if celda.value is None:
                    continue
                coord = celda.coordinate
                ref = f"{nombre_hoja}!{coord}"
                rango = rangos_combinados.get(ref)
                celdas.append(CeldaExcel(
                    hoja=nombre_hoja,
                    celda=coord,
                    valor=str(celda.value),
                    rango_combinado=rango,
                ))

    wb.close()
    return DocumentoExcel(hojas=hojas, celdas=celdas)
