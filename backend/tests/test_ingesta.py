"""Tests de ingesta — detección, PDF, Excel, imagen, rechazos."""

from pathlib import Path

import pytest

from app.ingesta.detector import detectar_tipo
from app.ingesta.errores import ArchivoNoSoportado, ArchivoProtegido
from app.ingesta.excel import extraer_excel
from app.ingesta.imagen import MAX_DIMENSION, extraer_imagen
from app.ingesta.pdf import extraer_pdf

FIXTURES = Path(__file__).parent / "fixtures"


# ── Detector ───────────────────────────────────────────────────────────

def test_detectar_pdf():
    contenido = (FIXTURES / "slip_c1.pdf").read_bytes()
    assert detectar_tipo(contenido) == "application/pdf"


def test_detectar_excel():
    contenido = (FIXTURES / "schedule_c1.xlsx").read_bytes()
    tipo_xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert detectar_tipo(contenido) == tipo_xlsx


def test_detectar_jpeg():
    contenido = (FIXTURES / "foto_riesgo_01.jpg").read_bytes()
    assert detectar_tipo(contenido) == "image/jpeg"


def test_detectar_png():
    from io import BytesIO

    from PIL import Image
    img = Image.new("RGB", (10, 10))
    buf = BytesIO()
    img.save(buf, format="PNG")
    assert detectar_tipo(buf.getvalue()) == "image/png"


def test_rechazar_exe():
    contenido = b"MZ" + b"\x00" * 100
    with pytest.raises(ArchivoNoSoportado):
        detectar_tipo(contenido)


def test_rechazar_heic():
    contenido = b"\x00\x00\x00\x18ftypheic" + b"\x00" * 100
    with pytest.raises(ArchivoNoSoportado):
        detectar_tipo(contenido)


def test_rechazar_desconocido():
    with pytest.raises(ArchivoNoSoportado):
        detectar_tipo(b"\x00\x01\x02\x03")


# ── PDF ────────────────────────────────────────────────────────────────

def test_pdf_texto():
    contenido = (FIXTURES / "slip_c1.pdf").read_bytes()
    doc = extraer_pdf(contenido)
    assert doc.total_paginas >= 1
    assert not doc.paginas[0].es_escaneada
    assert "Comercializadora" in doc.paginas[0].texto


def test_pdf_escaneado():
    contenido = (FIXTURES / "informe_escaneado.pdf").read_bytes()
    doc = extraer_pdf(contenido)
    assert doc.total_paginas >= 1
    assert doc.paginas[0].es_escaneada
    assert doc.paginas[0].imagen_bytes is not None


def test_pdf_protegido():
    import tempfile

    import pymupdf
    tmp = tempfile.mktemp(suffix=".pdf")
    doc = pymupdf.open()
    doc.new_page()
    perm = pymupdf.PDF_PERM_ACCESSIBILITY
    encrypt_meth = pymupdf.PDF_ENCRYPT_AES_256
    doc.save(tmp, encryption=encrypt_meth, owner_pw="owner", user_pw="user", permissions=perm)
    doc.close()
    contenido = Path(tmp).read_bytes()
    Path(tmp).unlink(missing_ok=True)
    with pytest.raises(ArchivoProtegido):
        extraer_pdf(contenido)


# ── Excel ──────────────────────────────────────────────────────────────

def test_excel_celdas():
    contenido = (FIXTURES / "schedule_c1.xlsx").read_bytes()
    doc = extraer_excel(contenido)
    assert "Ubicaciones" in doc.hojas
    assert "Siniestralidad" in doc.hojas
    assert len(doc.celdas) > 0


def test_excel_celda_combinada():
    contenido = (FIXTURES / "schedule_c1.xlsx").read_bytes()
    doc = extraer_excel(contenido)
    combinadas = [c for c in doc.celdas if c.rango_combinado is not None]
    assert len(combinadas) > 0


# ── Imagen ─────────────────────────────────────────────────────────────

def test_imagen_normalizada():
    contenido = (FIXTURES / "foto_riesgo_01.jpg").read_bytes()
    img = extraer_imagen(contenido)
    assert max(img.ancho, img.alto) <= MAX_DIMENSION
    assert img.formato == "JPEG"
    assert len(img.contenido) > 0
