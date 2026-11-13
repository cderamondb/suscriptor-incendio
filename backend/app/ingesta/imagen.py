"""Extracción y normalización de imágenes JPG/PNG con Pillow."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import ExifTags, Image

MAX_DIMENSION = 2048


@dataclass
class ImagenNormalizada:
    contenido: bytes
    ancho: int
    alto: int
    formato: str
    fecha_exif: str | None = None
    gps_exif: str | None = None


def _extraer_metadatos_exif(img: Image.Image) -> tuple[str | None, str | None]:
    fecha: str | None = None
    gps: str | None = None
    try:
        exif = img.getexif()
        if not exif:
            return None, None

        for tag_id, valor in exif.items():
            tag = ExifTags.TAGS.get(tag_id, "")
            es_fecha_original = tag == "DateTimeOriginal" and isinstance(valor, str)
            es_fecha_fallback = tag == "DateTime" and fecha is None and isinstance(valor, str)
            if es_fecha_original or es_fecha_fallback:
                fecha = valor

        gps_info = exif.get_ifd(ExifTags.IFD.GPSInfo)
        if gps_info:
            gps = str(dict(gps_info))
    except Exception:
        pass
    return fecha, gps


def extraer_imagen(contenido: bytes) -> ImagenNormalizada:
    img = Image.open(BytesIO(contenido))

    fecha, gps = _extraer_metadatos_exif(img)

    # Strip EXIF
    if hasattr(img, "get_flattened_data"):
        datos = list(img.get_flattened_data())
    else:
        datos = list(img.getdata())
    img_limpia = Image.new(img.mode, img.size)
    img_limpia.putdata(datos)

    # Redimensionar si excede MAX_DIMENSION
    ancho, alto = img_limpia.size
    if max(ancho, alto) > MAX_DIMENSION:
        ratio = MAX_DIMENSION / max(ancho, alto)
        nuevo_ancho = int(ancho * ratio)
        nuevo_alto = int(alto * ratio)
        img_limpia = img_limpia.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
        ancho, alto = nuevo_ancho, nuevo_alto

    # Convertir a RGB si es necesario para JPEG
    formato = img.format or "PNG"
    buf = BytesIO()
    if formato.upper() == "JPEG" and img_limpia.mode != "RGB":
        img_limpia = img_limpia.convert("RGB")
    img_limpia.save(buf, format=formato)

    return ImagenNormalizada(
        contenido=buf.getvalue(),
        ancho=ancho,
        alto=alto,
        formato=formato,
        fecha_exif=fecha,
        gps_exif=gps,
    )
