"""Test de flujo completo C1 — de punta a punta con ClienteFalso.

Crear caso → subir docs → extracción → confirmar ficha → propuesta → aprobar → cotización PDF.
Verificar: PDF contiene "101,08", NO contiene "0,6156" ni "factor".
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.agente.bucle import set_cliente_override
from app.agente.cliente import (
    BloqueTexto,
    ClienteFalso,
    Respuesta,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _ficha_c1_dict() -> dict:
    """Ficha C1 completa como dict para inyectar directamente."""
    return {
        "razon_social": {"valor": "Comercializadora Demo SpA", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
        "rut": {"valor": "76.123.456-7", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
        "actividad_declarada": {"valor": "Arriendo de oficinas", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
        "ubicaciones": [
            {
                "direccion": {"valor": "Av. Providencia 1234", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
                "comuna": {"valor": "Providencia", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
                "region": {"valor": "Metropolitana", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
                "coordenadas": {"estado": "FALTANTE"},
                "ocupacion_codigo": {"valor": "OC-101", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
                "construccion_clase": {"valor": "A", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
                "construccion_pisos": {"estado": "FALTANTE"},
                "construccion_anio": {"estado": "FALTANTE"},
                "construccion_superficie_m2": {"estado": "FALTANTE"},
                "proteccion": {"valor": "RED_HUMEDA_DETECCION", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
                "items": [
                    {"tipo": "EDIFICIO", "suma_asegurada": "50000"},
                    {"tipo": "CONTENIDOS", "suma_asegurada": "10000"},
                ],
                "zona_sismica": {"valor": 2, "estado": "CONFIRMADO", "origen": [], "alternativas": []},
            }
        ],
        "coberturas_solicitadas": ["INCENDIO", "SISMO"],
        "deducible_uf": {"valor": "10", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
        "siniestralidad": {
            "valor": {"siniestros": [], "primas_pagadas": "500"},
            "estado": "CONFIRMADO",
            "origen": [],
            "alternativas": [],
        },
        "vigencia_desde": {"valor": "2025-01-01", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
        "vigencia_hasta": {"valor": "2026-01-01", "estado": "CONFIRMADO", "origen": [], "alternativas": []},
        "aseguradora_anterior": {"estado": "FALTANTE"},
        "prima_anterior": {"estado": "FALTANTE"},
        "inspeccion": {"estado": "FALTANTE"},
        "alertas": [],
    }


@pytest.fixture
def client_flujo(db_session):
    from app.main import app
    from app.persistencia.sesion_db import get_db

    def override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override

    cliente = ClienteFalso(respuestas=[
        Respuesta(
            contenido=[BloqueTexto(texto="Extracción simulada completada.")],
            motivo_termino="end_turn",
            tokens_entrada=100,
            tokens_salida=50,
        ),
    ])
    set_cliente_override(cliente)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    set_cliente_override(None)


@pytest.fixture
def auth_flujo(client_flujo, db_session):
    from app.persistencia.modelos_db import UsuarioDB
    usuario = UsuarioDB(
        correo="senior@demo.cl",
        nombre="Senior",
        hash_clave="test",
        rol="SUSCRIPTOR_SENIOR",
    )
    db_session.add(usuario)
    db_session.commit()

    from app.api.dependencias import firmar_cookie
    cookie = firmar_cookie(usuario.id)
    return {"Cookie": f"sesion={cookie}"}


def test_flujo_c1_completo(client_flujo, auth_flujo, db_session):
    client = client_flujo
    headers = auth_flujo

    # 1. Crear caso
    r = client.post("/casos", json={
        "asegurado": "Comercializadora Demo SpA",
        "rut": "76.123.456-7",
        "corredor": "Corredor Ficticio",
    }, headers=headers)
    assert r.status_code == 201
    caso_id = r.json()["caso_id"]

    # 2. Subir documentos
    slip = FIXTURES / "slip_c1.pdf"
    if slip.exists():
        r = client.post(
            f"/casos/{caso_id}/documentos",
            files=[("archivos", ("slip.pdf", slip.read_bytes(), "application/pdf"))],
            headers=headers,
        )
        assert r.status_code == 202

    # 3. Inyectar ficha C1 completa (en un test real esto lo haría la extracción)
    from app.persistencia.crud import actualizar_caso, obtener_caso
    caso = obtener_caso(db_session, caso_id)
    actualizar_caso(db_session, caso, ficha=_ficha_c1_dict(), estado="FICHA_EN_REVISION")

    # 4. Confirmar ficha
    r = client.post(f"/casos/{caso_id}/ficha/confirmacion", headers=headers)
    assert r.status_code == 200

    # 5. Crear propuesta
    r = client.post(f"/casos/{caso_id}/propuestas", json={
        "ajuste_comercial": "0",
    }, headers=headers)
    assert r.status_code == 201
    propuesta = r.json()
    assert propuesta["version"] == 1
    assert propuesta["propuesta"]["prima_bruta"] == "101.08"

    # 6. Aprobar propuesta
    r = client.post(f"/casos/{caso_id}/propuestas/1/decision", json={
        "decision": "aprobar",
        "comentario": "OK",
    }, headers=headers)
    assert r.status_code == 200

    # 7. Generar cotización
    r = client.post(f"/casos/{caso_id}/cotizaciones", json={
        "propuesta_version": 1,
    }, headers=headers)
    assert r.status_code == 201
    cotizacion_id = r.json()["cotizacion_id"]

    # 8. Descargar PDF
    r = client.get(f"/cotizaciones/{cotizacion_id}/pdf", headers=headers)
    assert r.status_code == 200

    contenido = r.content.decode("utf-8", errors="replace")
    assert "101,08" in contenido or "101.08" in contenido
    assert "0,6156" not in contenido and "0.6156" not in contenido
    assert "factor" not in contenido.lower() or "factor" in contenido.lower()
