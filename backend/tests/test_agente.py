"""Tests del agente — ClienteFalso con secuencias: C8, C9, refusal, tope de pasos."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.agente.bucle import ejecutar_bucle, set_cliente_override
from app.agente.cliente import (
    BloqueHerramienta,
    BloqueTexto,
    ClienteFalso,
    Respuesta,
)
from app.persistencia.crud import crear_caso, crear_documento, crear_trabajo, obtener_trabajo


def _fixture_slip_bytes():
    ruta = Path(__file__).parent / "fixtures" / "slip_c1.pdf"
    if ruta.exists():
        return ruta.read_bytes()
    return b"%PDF-1.4 test content Comercializadora Demo"


# ── Extracción normal ─────────────────────────────────────────────────

def test_extraccion_normal(db_session):
    caso = crear_caso(db_session, asegurado="Test", rut="1-1")
    crear_documento(
        db_session, caso.id, "slip.pdf", "application/pdf",
        _fixture_slip_bytes(),
    )

    cliente = ClienteFalso(respuestas=[
        Respuesta(
            contenido=[
                BloqueHerramienta(id="t1", nombre="listar_documentos", entrada={"caso_id": caso.id}),
            ],
            motivo_termino="tool_use",
            tokens_entrada=50, tokens_salida=30,
        ),
        Respuesta(
            contenido=[BloqueTexto(texto="Extracción completada.")],
            motivo_termino="end_turn",
            tokens_entrada=50, tokens_salida=30,
        ),
    ])
    set_cliente_override(cliente)

    trabajo = crear_trabajo(db_session, caso.id, "EXTRACCION")
    trabajo.estado = "EN_CURSO"
    db_session.commit()

    ejecutar_bucle(db_session, trabajo.id, caso.id, tipo="EXTRACCION")

    trabajo = obtener_trabajo(db_session, trabajo.id)
    assert trabajo.estado == "OK"
    assert trabajo.pasos == 2
    assert "listar_documentos" in trabajo.herramientas_usadas

    set_cliente_override(None)


# ── C8: cita falsa → CITA_NO_ENCONTRADA ──────────────────────────────

def test_c8_cita_no_encontrada(db_session):
    caso = crear_caso(db_session, asegurado="Test", rut="1-1")
    doc = crear_documento(
        db_session, caso.id, "slip.pdf", "application/pdf",
        _fixture_slip_bytes(),
    )

    cliente = ClienteFalso(respuestas=[
        Respuesta(
            contenido=[
                BloqueHerramienta(
                    id="t1",
                    nombre="registrar_dato",
                    entrada={
                        "campo": "razon_social",
                        "valor": "Empresa Falsa",
                        "origen_documento_id": doc.id,
                        "origen_ubicacion": "pág. 1",
                        "cita": "TEXTO QUE NO EXISTE EN EL DOCUMENTO",
                        "confianza": "ALTA",
                    },
                ),
            ],
            motivo_termino="tool_use",
            tokens_entrada=50, tokens_salida=30,
        ),
        Respuesta(
            contenido=[BloqueTexto(texto="No pude registrar el dato.")],
            motivo_termino="end_turn",
            tokens_entrada=20, tokens_salida=10,
        ),
    ])
    set_cliente_override(cliente)

    trabajo = crear_trabajo(db_session, caso.id, "EXTRACCION")
    trabajo.estado = "EN_CURSO"
    db_session.commit()

    ejecutar_bucle(db_session, trabajo.id, caso.id, tipo="EXTRACCION")

    trabajo = obtener_trabajo(db_session, trabajo.id)
    assert trabajo.estado == "OK"
    assert caso.ficha is None or "razon_social" not in (caso.ficha or {})

    set_cliente_override(None)


# ── C9: presupuesto agotado ───────────────────────────────────────────

def test_c9_presupuesto_agotado(db_session):
    caso = crear_caso(db_session, asegurado="Test", rut="1-1")
    caso.tokens_entrada = 200_001
    db_session.commit()

    cliente = ClienteFalso(respuestas=[
        Respuesta(
            contenido=[BloqueTexto(texto="No debería llegar aquí.")],
            motivo_termino="end_turn",
            tokens_entrada=50, tokens_salida=30,
        ),
    ])
    set_cliente_override(cliente)

    trabajo = crear_trabajo(db_session, caso.id, "EXTRACCION")
    trabajo.estado = "EN_CURSO"
    db_session.commit()

    ejecutar_bucle(db_session, trabajo.id, caso.id, tipo="EXTRACCION")

    trabajo = obtener_trabajo(db_session, trabajo.id)
    assert trabajo.estado == "ERROR"
    assert trabajo.codigo_error == "PRESUPUESTO_AGOTADO"

    set_cliente_override(None)


# ── Refusal → RECHAZO_MODELO ─────────────────────────────────────────

def test_refusal(db_session):
    caso = crear_caso(db_session, asegurado="Test", rut="1-1")

    cliente = ClienteFalso(respuestas=[
        Respuesta(
            contenido=[BloqueTexto(texto="No puedo hacer eso.")],
            motivo_termino="refusal",
            tokens_entrada=50, tokens_salida=30,
        ),
    ])
    set_cliente_override(cliente)

    trabajo = crear_trabajo(db_session, caso.id, "AGENTE")
    trabajo.estado = "EN_CURSO"
    db_session.commit()

    ejecutar_bucle(db_session, trabajo.id, caso.id, tipo="AGENTE", mensaje="Haz algo malo")

    trabajo = obtener_trabajo(db_session, trabajo.id)
    assert trabajo.estado == "ERROR"
    assert trabajo.codigo_error == "RECHAZO_MODELO"

    set_cliente_override(None)


# ── Tope de pasos ─────────────────────────────────────────────────────

def test_tope_de_pasos(db_session):
    caso = crear_caso(db_session, asegurado="Test", rut="1-1")

    respuestas_infinitas = [
        Respuesta(
            contenido=[
                BloqueHerramienta(id=f"t{i}", nombre="listar_documentos", entrada={"caso_id": caso.id}),
            ],
            motivo_termino="tool_use",
            tokens_entrada=10, tokens_salida=5,
        )
        for i in range(25)
    ]

    cliente = ClienteFalso(respuestas=respuestas_infinitas)
    set_cliente_override(cliente)

    trabajo = crear_trabajo(db_session, caso.id, "EXTRACCION")
    trabajo.estado = "EN_CURSO"
    db_session.commit()

    with pytest.MonkeyPatch.context() as m:
        m.setattr("app.config.settings.max_pasos_agente", 3)
        ejecutar_bucle(db_session, trabajo.id, caso.id, tipo="EXTRACCION")

    trabajo = obtener_trabajo(db_session, trabajo.id)
    assert trabajo.estado == "ERROR"
    assert trabajo.codigo_error == "TOPE_DE_PASOS"

    set_cliente_override(None)


# ── tool_use_id correcto ──────────────────────────────────────────────

def test_tool_use_id_correcto(db_session):
    caso = crear_caso(db_session, asegurado="Test", rut="1-1")

    cliente = ClienteFalso(respuestas=[
        Respuesta(
            contenido=[
                BloqueHerramienta(id="call_abc", nombre="listar_documentos", entrada={"caso_id": caso.id}),
                BloqueHerramienta(id="call_xyz", nombre="evaluar_completitud", entrada={"caso_id": caso.id}),
            ],
            motivo_termino="tool_use",
            tokens_entrada=50, tokens_salida=30,
        ),
        Respuesta(
            contenido=[BloqueTexto(texto="Listo.")],
            motivo_termino="end_turn",
            tokens_entrada=20, tokens_salida=10,
        ),
    ])
    set_cliente_override(cliente)

    trabajo = crear_trabajo(db_session, caso.id, "EXTRACCION")
    trabajo.estado = "EN_CURSO"
    db_session.commit()

    ejecutar_bucle(db_session, trabajo.id, caso.id, tipo="EXTRACCION")

    assert len(cliente.llamadas) == 2
    segunda_llamada = cliente.llamadas[1]
    tool_results = segunda_llamada["mensajes"][-1]["content"]
    ids = [tr["tool_use_id"] for tr in tool_results]
    assert "call_abc" in ids
    assert "call_xyz" in ids

    set_cliente_override(None)
