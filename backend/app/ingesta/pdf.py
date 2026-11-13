"""Extracción de contenido de archivos PDF con PyMuPDF."""

from __future__ import annotations

from dataclasses import dataclass, field

import pymupdf

from app.ingesta.errores import ArchivoCorrupto, ArchivoProtegido


@dataclass
class PaginaPDF:
    numero: int
    texto: str
    es_escaneada: bool
    imagen_bytes: bytes | None = None


@dataclass
class DocumentoPDF:
    paginas: list[PaginaPDF] = field(default_factory=list)
    total_paginas: int = 0


def extraer_pdf(contenido: bytes) -> DocumentoPDF:
    try:
        doc = pymupdf.open(stream=contenido, filetype="pdf")
    except Exception as e:
        raise ArchivoCorrupto(str(e)) from e

    if doc.is_encrypted:
        doc.close()
        raise ArchivoProtegido("PDF protegido con contraseña")

    paginas: list[PaginaPDF] = []
    total = len(doc)

    for i in range(total):
        pagina = doc[i]
        texto = pagina.get_text("text").strip()

        if len(texto) < 50:
            pix = pagina.get_pixmap(dpi=150)
            imagen = pix.tobytes("png")
            paginas.append(PaginaPDF(
                numero=i + 1,
                texto=texto,
                es_escaneada=True,
                imagen_bytes=imagen,
            ))
        else:
            paginas.append(PaginaPDF(
                numero=i + 1,
                texto=texto,
                es_escaneada=False,
            ))

    doc.close()
    return DocumentoPDF(paginas=paginas, total_paginas=total)
