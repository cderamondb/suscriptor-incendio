"""Catálogo de herramientas del agente — §6.4."""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.dominio.datos_minimos import evaluar_completitud
from app.dominio.modelos import FichaRiesgo

# ── Schemas de entrada (Pydantic) ─────────────────────────────────────

class ListarDocumentosInput(BaseModel):
    caso_id: str


class LeerDocumentoInput(BaseModel):
    documento_id: str
    desde: int | None = None
    hasta: int | None = None


class RegistrarDatoInput(BaseModel):
    campo: str
    valor: object
    origen_documento_id: str
    origen_ubicacion: str
    cita: str
    confianza: str = "ALTA"


class RegistrarAlertaInput(BaseModel):
    tipo: str
    detalle: str
    origen_documento_id: str | None = None
    origen_ubicacion: str | None = None


class BuscarOcupacionInput(BaseModel):
    texto: str


class ConsultarProductosInput(BaseModel):
    ocupacion: str
    coberturas: list[str] | None = None


class EvaluarCompletitudInput(BaseModel):
    caso_id: str


class BuscarComparablesInput(BaseModel):
    caso_id: str


class SimularTarifaInput(BaseModel):
    caso_id: str
    coberturas: list[str] | None = None
    deducible: str | None = None
    ajuste_comercial: str = "0"


HERRAMIENTAS_SCHEMA: list[dict] = [
    {
        "name": "listar_documentos",
        "description": "Lista los documentos cargados en un caso.",
        "input_schema": {
            "type": "object",
            "properties": {"caso_id": {"type": "string"}},
            "required": ["caso_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "leer_documento",
        "description": "Lee el contenido de un documento: texto por páginas o imagen.",
        "input_schema": {
            "type": "object",
            "properties": {
                "documento_id": {"type": "string"},
                "desde": {"type": "integer", "description": "Página/fila desde"},
                "hasta": {"type": "integer", "description": "Página/fila hasta"},
            },
            "required": ["documento_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "registrar_dato",
        "description": "Registra un dato en la ficha con su origen y cita textual.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campo": {"type": "string"},
                "valor": {},
                "origen_documento_id": {"type": "string"},
                "origen_ubicacion": {"type": "string"},
                "cita": {"type": "string"},
                "confianza": {"type": "string", "enum": ["ALTA", "MEDIA", "BAJA"]},
            },
            "required": ["campo", "valor", "origen_documento_id", "origen_ubicacion", "cita"],
            "additionalProperties": False,
        },
    },
    {
        "name": "registrar_alerta",
        "description": "Registra una alerta sobre el caso.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string"},
                "detalle": {"type": "string"},
                "origen_documento_id": {"type": "string"},
                "origen_ubicacion": {"type": "string"},
            },
            "required": ["tipo", "detalle"],
            "additionalProperties": False,
        },
    },
    {
        "name": "buscar_ocupacion",
        "description": "Busca 5 candidatos de ocupación en el catálogo.",
        "input_schema": {
            "type": "object",
            "properties": {"texto": {"type": "string"}},
            "required": ["texto"],
            "additionalProperties": False,
        },
    },
    {
        "name": "consultar_productos",
        "description": "Productos vigentes aplicables a una ocupación.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ocupacion": {"type": "string"},
                "coberturas": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["ocupacion"],
            "additionalProperties": False,
        },
    },
    {
        "name": "evaluar_completitud",
        "description": "Evalúa completitud de la ficha: faltantes bloqueantes y no bloqueantes.",
        "input_schema": {
            "type": "object",
            "properties": {"caso_id": {"type": "string"}},
            "required": ["caso_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "buscar_comparables",
        "description": "Busca riesgos similares anonimizados en la cartera.",
        "input_schema": {
            "type": "object",
            "properties": {"caso_id": {"type": "string"}},
            "required": ["caso_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "simular_tarifa",
        "description": "Simula la tarificación con dominio.tarifa.tarificar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "caso_id": {"type": "string"},
                "coberturas": {"type": "array", "items": {"type": "string"}},
                "deducible": {"type": "string"},
                "ajuste_comercial": {"type": "string"},
            },
            "required": ["caso_id"],
            "additionalProperties": False,
        },
    },
]


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).lower()
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def _verificar_cita_en_fragmento(cita: str, fragmento_texto: str) -> bool:
    return _normalizar(cita) in _normalizar(fragmento_texto)


def _es_origen_imagen(tipo_mime: str, fragmento: dict | None) -> bool:
    if tipo_mime.startswith("image/"):
        return True
    return bool(fragmento and fragmento.get("es_escaneada"))


def ejecutar_herramienta(
    nombre: str,
    entrada: dict,
    db: Session,
    caso_id: str,
) -> dict:
    """Ejecuta una herramienta y devuelve el resultado como dict."""

    if nombre == "listar_documentos":
        return _listar_documentos(db, caso_id)
    elif nombre == "leer_documento":
        try:
            inp = LeerDocumentoInput(**entrada)
        except ValidationError as e:
            return {"is_error": True, "codigo": "VALIDACION", "mensaje": str(e)}
        return _leer_documento(db, inp)
    elif nombre == "registrar_dato":
        try:
            inp = RegistrarDatoInput(**entrada)
        except ValidationError as e:
            return {"is_error": True, "codigo": "VALIDACION", "mensaje": str(e)}
        return _registrar_dato(db, caso_id, inp)
    elif nombre == "registrar_alerta":
        try:
            inp = RegistrarAlertaInput(**entrada)
        except ValidationError as e:
            return {"is_error": True, "codigo": "VALIDACION", "mensaje": str(e)}
        return _registrar_alerta(db, caso_id, inp)
    elif nombre == "buscar_ocupacion":
        try:
            inp = BuscarOcupacionInput(**entrada)
        except ValidationError as e:
            return {"is_error": True, "codigo": "VALIDACION", "mensaje": str(e)}
        return _buscar_ocupacion(inp)
    elif nombre == "consultar_productos":
        try:
            inp = ConsultarProductosInput(**entrada)
        except ValidationError as e:
            return {"is_error": True, "codigo": "VALIDACION", "mensaje": str(e)}
        return _consultar_productos(inp)
    elif nombre == "evaluar_completitud":
        return _evaluar_completitud(db, caso_id)
    elif nombre == "buscar_comparables":
        return _buscar_comparables(db, caso_id)
    elif nombre == "simular_tarifa":
        try:
            inp = SimularTarifaInput(**entrada)
        except ValidationError as e:
            return {"is_error": True, "codigo": "VALIDACION", "mensaje": str(e)}
        return _simular_tarifa(db, caso_id, inp)
    else:
        return {"is_error": True, "codigo": "HERRAMIENTA_DESCONOCIDA", "mensaje": nombre}


def _listar_documentos(db: Session, caso_id: str) -> dict:
    from app.persistencia.crud import listar_documentos_caso
    docs = listar_documentos_caso(db, caso_id)
    return {
        "documentos": [
            {"id": d.id, "nombre": d.nombre, "tipo": d.tipo_mime, "paginas": d.total_paginas}
            for d in docs
        ],
    }


def _leer_documento(db: Session, inp: LeerDocumentoInput) -> dict:
    from app.persistencia.crud import obtener_contenido_documento, obtener_documento
    doc = obtener_documento(db, inp.documento_id)
    if not doc:
        return {"is_error": True, "codigo": "NO_ENCONTRADO", "mensaje": "Documento no existe"}

    contenido = obtener_contenido_documento(db, inp.documento_id)
    if not contenido:
        return {"is_error": True, "codigo": "SIN_CONTENIDO", "mensaje": "Sin contenido"}

    if doc.tipo_mime == "application/pdf":
        from app.ingesta.pdf import extraer_pdf
        pdf = extraer_pdf(contenido)
        paginas = pdf.paginas
        desde = (inp.desde or 1) - 1
        hasta = inp.hasta or len(paginas)
        seleccion = paginas[desde:hasta]
        return {
            "documento_id": inp.documento_id,
            "tipo": "pdf",
            "paginas": [
                {
                    "numero": p.numero,
                    "texto": p.texto,
                    "es_escaneada": p.es_escaneada,
                }
                for p in seleccion
            ],
        }
    elif "spreadsheet" in doc.tipo_mime or "excel" in doc.tipo_mime:
        from app.ingesta.excel import extraer_excel
        excel = extraer_excel(contenido)
        return {
            "documento_id": inp.documento_id,
            "tipo": "excel",
            "hojas": list(excel.hojas),
            "celdas": [
                {
                    "hoja": c.hoja,
                    "celda": c.celda,
                    "valor": str(c.valor) if c.valor is not None else None,
                    "rango_combinado": c.rango_combinado,
                }
                for c in excel.celdas
            ],
        }
    elif doc.tipo_mime.startswith("image/"):
        return {
            "documento_id": inp.documento_id,
            "tipo": "imagen",
            "mensaje": "Imagen disponible para visión",
        }
    else:
        return {"documento_id": inp.documento_id, "tipo": doc.tipo_mime}


def _registrar_dato(db: Session, caso_id: str, inp: RegistrarDatoInput) -> dict:
    from app.persistencia.crud import obtener_caso, obtener_contenido_documento, obtener_documento

    doc = obtener_documento(db, inp.origen_documento_id)
    if not doc:
        return {
            "is_error": True,
            "codigo": "DOCUMENTO_NO_ENCONTRADO",
            "mensaje": "Documento no existe",
        }

    es_imagen = _es_origen_imagen(doc.tipo_mime, None)

    if not es_imagen:
        contenido = obtener_contenido_documento(db, inp.origen_documento_id)
        if contenido:
            texto_fragmento = ""
            if doc.tipo_mime == "application/pdf":
                from app.ingesta.pdf import extraer_pdf
                pdf = extraer_pdf(contenido)
                for p in pdf.paginas:
                    if not p.es_escaneada:
                        texto_fragmento += p.texto + "\n"
                    else:
                        es_imagen = True
                        break
            elif "spreadsheet" in doc.tipo_mime or "excel" in doc.tipo_mime:
                from app.ingesta.excel import extraer_excel
                excel = extraer_excel(contenido)
                texto_fragmento = " ".join(
                    str(c.valor) for c in excel.celdas if c.valor is not None
                )

            cita_ok = _verificar_cita_en_fragmento(inp.cita, texto_fragmento)
            if not es_imagen and texto_fragmento and not cita_ok:
                return {
                        "is_error": True,
                        "codigo": "CITA_NO_ENCONTRADA",
                        "mensaje": f"La cita '{inp.cita}' no se encontró en el documento",
                    }

    confianza = inp.confianza
    if es_imagen and confianza == "ALTA":
        confianza = "MEDIA"

    caso = obtener_caso(db, caso_id)
    if not caso:
        return {"is_error": True, "codigo": "CASO_NO_ENCONTRADO", "mensaje": "Caso no existe"}

    ficha_data = dict(caso.ficha) if caso.ficha else {}

    campo_data = ficha_data.get(inp.campo, {})
    if not isinstance(campo_data, dict):
        campo_data = {}

    campo_data["valor"] = inp.valor
    campo_data["estado"] = "EXTRAIDO"
    campo_data["confianza"] = confianza
    if "origen" not in campo_data:
        campo_data["origen"] = []
    campo_data["origen"].append({
        "documento_id": inp.origen_documento_id,
        "ubicacion": inp.origen_ubicacion,
        "cita": inp.cita,
    })

    ficha_data[inp.campo] = campo_data
    caso.ficha = ficha_data
    db.commit()

    return {"ok": True, "campo": inp.campo, "estado": "EXTRAIDO", "confianza": confianza}


def _registrar_alerta(db: Session, caso_id: str, inp: RegistrarAlertaInput) -> dict:
    from app.persistencia.crud import obtener_caso

    caso = obtener_caso(db, caso_id)
    if not caso:
        return {"is_error": True, "codigo": "CASO_NO_ENCONTRADO", "mensaje": "Caso no existe"}

    ficha_data = dict(caso.ficha) if caso.ficha else {}
    alertas = ficha_data.get("alertas", [])
    if not isinstance(alertas, list):
        alertas = []

    alerta = {"tipo": inp.tipo, "detalle": inp.detalle}
    if inp.origen_documento_id:
        alerta["origen"] = {
            "documento_id": inp.origen_documento_id,
            "ubicacion": inp.origen_ubicacion or "",
            "cita": "",
        }
    alertas.append(alerta)
    ficha_data["alertas"] = alertas
    caso.ficha = ficha_data
    db.commit()

    return {"ok": True, "tipo": inp.tipo}


def _buscar_ocupacion(inp: BuscarOcupacionInput) -> dict:
    from app.catalogo.cargador import cargar_tarifario
    ruta = Path(settings.ruta_tarifario)
    if not ruta.is_absolute():
        ruta = Path(__file__).resolve().parent.parent.parent.parent / ruta
    tarifario = cargar_tarifario(ruta)

    texto_norm = _normalizar(inp.texto)
    candidatos = []
    for codigo, oc in tarifario.ocupaciones.items():
        score = 0
        if texto_norm in _normalizar(oc.descripcion):
            score = 2
        elif any(p in _normalizar(oc.descripcion) for p in texto_norm.split()):
            score = 1
        if score > 0:
            candidatos.append((score, codigo, oc.descripcion))

    candidatos.sort(key=lambda x: -x[0])
    return {
        "candidatos": [
            {"codigo": c[1], "descripcion": c[2]} for c in candidatos[:5]
        ],
    }


def _consultar_productos(inp: ConsultarProductosInput) -> dict:
    return {
        "productos": [
            {
                "id": "incendio_estandar",
                "nombre": "Incendio Estándar",
                "coberturas": ["INCENDIO", "SISMO"],
            },
        ],
    }


def _evaluar_completitud(db: Session, caso_id: str) -> dict:
    from app.persistencia.crud import obtener_caso
    caso = obtener_caso(db, caso_id)
    if not caso or not caso.ficha:
        return {"completo": False, "faltantes": ["ficha vacía"]}

    try:
        ficha = FichaRiesgo.model_validate(caso.ficha)
    except Exception:
        return {"completo": False, "faltantes": ["ficha inválida"]}

    reporte = evaluar_completitud(ficha)
    return reporte.model_dump()


def _buscar_comparables(db: Session, caso_id: str) -> dict:
    from app.catalogo.cargador import cargar_tarifario
    from app.catalogo.repositorio import Repositorio
    from app.persistencia.crud import obtener_caso
    caso = obtener_caso(db, caso_id)
    if not caso or not caso.ficha:
        return {"comparables": []}

    try:
        ficha = FichaRiesgo.model_validate(caso.ficha)
    except Exception:
        return {"comparables": []}

    ruta = Path(settings.ruta_tarifario)
    if not ruta.is_absolute():
        ruta = Path(__file__).resolve().parent.parent.parent.parent / ruta
    tarifario = cargar_tarifario(ruta)
    repo = Repositorio(tarifario)
    return {"comparables": repo.buscar_comparables(ficha)}


def _simular_tarifa(db: Session, caso_id: str, inp: SimularTarifaInput) -> dict:
    from app.catalogo.cargador import cargar_tarifario
    from app.dominio.tarifa import tarificar
    from app.persistencia.crud import obtener_caso

    caso = obtener_caso(db, caso_id)
    if not caso or not caso.ficha:
        return {"is_error": True, "codigo": "SIN_FICHA", "mensaje": "Caso sin ficha"}

    try:
        ficha = FichaRiesgo.model_validate(caso.ficha)
    except Exception as e:
        return {"is_error": True, "codigo": "FICHA_INVALIDA", "mensaje": str(e)}

    ruta = Path(settings.ruta_tarifario)
    if not ruta.is_absolute():
        ruta = Path(__file__).resolve().parent.parent.parent.parent / ruta
    tarifario = cargar_tarifario(ruta)

    try:
        ajuste = Decimal(inp.ajuste_comercial)
    except (InvalidOperation, ValueError):
        ajuste = Decimal("0")

    try:
        resultado = tarificar(ficha, tarifario, ajuste_comercial=ajuste)
    except Exception as e:
        return {"is_error": True, "codigo": "ERROR_TARIFA", "mensaje": str(e)}

    return resultado.model_dump(mode="json")
