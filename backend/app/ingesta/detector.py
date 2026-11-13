"""Detección de tipo de archivo por magic bytes, no por extensión."""

from __future__ import annotations

from app.ingesta.errores import ArchivoNoSoportado

FIRMAS: list[tuple[bytes, int, str]] = [
    (b"%PDF", 0, "application/pdf"),
    (b"PK\x03\x04", 0, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    (b"\xff\xd8\xff", 0, "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", 0, "image/png"),
]

TIPOS_SOPORTADOS = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg",
    "image/png",
}

FIRMAS_BLOQUEADAS: list[tuple[bytes, int, str]] = [
    (b"MZ", 0, "application/x-executable"),
    (b"\x00\x00\x00\x18ftypheic", 0, "image/heic"),
    (b"\x00\x00\x00\x1cftypheic", 0, "image/heic"),
    (b"\x00\x00\x00\x20ftypheic", 0, "image/heic"),
]


def detectar_tipo(contenido: bytes) -> str:
    for firma, offset, tipo in FIRMAS_BLOQUEADAS:
        if len(contenido) > offset and contenido[offset:offset + len(firma)] == firma:
            raise ArchivoNoSoportado(tipo)

    for firma, offset, tipo in FIRMAS:
        if len(contenido) > offset and contenido[offset:offset + len(firma)] == firma:
            return tipo

    raise ArchivoNoSoportado("desconocido")
