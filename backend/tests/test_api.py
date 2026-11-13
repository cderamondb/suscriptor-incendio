"""Tests de API — cada endpoint de §6.2 con TestClient + SQLite in-memory."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.agente.bucle import set_cliente_override
from app.agente.cliente import BloqueTexto, ClienteFalso, Respuesta


@pytest.fixture(autouse=True)
def _cliente_falso():
    cliente = ClienteFalso(respuestas=[
        Respuesta(
            contenido=[BloqueTexto(texto="Extracción completada.")],
            motivo_termino="end_turn",
            tokens_entrada=100,
            tokens_salida=50,
        ),
    ])
    set_cliente_override(cliente)
    yield
    set_cliente_override(None)


@pytest.fixture
def client(db_session):
    from app.main import app
    from app.persistencia.sesion_db import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_cookie(client, db_session):
    from app.persistencia.modelos_db import UsuarioDB
    usuario = UsuarioDB(
        correo="test@demo.cl",
        nombre="Test",
        hash_clave="test123",
        rol="SUSCRIPTOR_SENIOR",
    )
    db_session.add(usuario)
    db_session.commit()

    from app.api.dependencias import firmar_cookie
    cookie = firmar_cookie(usuario.id)
    return {"Cookie": f"sesion={cookie}"}


# ── Salud ─────────────────────────────────────────────────────────────

def test_salud(client):
    r = client.get("/salud")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"


# ── Sesión ────────────────────────────────────────────────────────────

def test_login_credenciales_invalidas(client):
    r = client.post("/sesion", json={"correo": "nadie@demo.cl", "clave": "wrong"})
    assert r.status_code == 401


def test_no_autenticado(client):
    r = client.get("/casos")
    assert r.status_code == 401


# ── Casos ─────────────────────────────────────────────────────────────

def test_crear_caso(client, auth_cookie):
    r = client.post("/casos", json={
        "asegurado": "Test SpA",
        "rut": "76.000.000-0",
    }, headers=auth_cookie)
    assert r.status_code == 201
    assert "caso_id" in r.json()


def test_listar_casos(client, auth_cookie):
    client.post("/casos", json={"asegurado": "A", "rut": "1"}, headers=auth_cookie)
    r = client.get("/casos", headers=auth_cookie)
    assert r.status_code == 200
    assert len(r.json()) >= 1


# ── Documentos ────────────────────────────────────────────────────────

def test_subir_documento(client, auth_cookie):
    r = client.post("/casos", json={"asegurado": "A", "rut": "1"}, headers=auth_cookie)
    caso_id = r.json()["caso_id"]

    fixtures = Path(__file__).parent / "fixtures"
    slip = fixtures / "slip_c1.pdf"
    if not slip.exists():
        pytest.skip("Fixture slip_c1.pdf no disponible")

    r = client.post(
        f"/casos/{caso_id}/documentos",
        files=[("archivos", ("slip.pdf", slip.read_bytes(), "application/pdf"))],
        headers=auth_cookie,
    )
    assert r.status_code == 202
    assert len(r.json()) == 1


def test_subir_tipo_no_soportado(client, auth_cookie):
    r = client.post("/casos", json={"asegurado": "A", "rut": "1"}, headers=auth_cookie)
    caso_id = r.json()["caso_id"]

    r = client.post(
        f"/casos/{caso_id}/documentos",
        files=[("archivos", ("malware.exe", b"MZ" + b"\x00" * 100, "application/octet-stream"))],
        headers=auth_cookie,
    )
    assert r.status_code == 415


# ── Ficha ─────────────────────────────────────────────────────────────

def test_ficha_caso_no_encontrado(client, auth_cookie):
    r = client.get("/casos/inexistente/ficha", headers=auth_cookie)
    assert r.status_code == 404


def test_confirmar_ficha_sin_datos(client, auth_cookie, db_session):
    r = client.post("/casos", json={"asegurado": "A", "rut": "1"}, headers=auth_cookie)
    caso_id = r.json()["caso_id"]

    from app.persistencia.crud import actualizar_caso, obtener_caso
    caso = obtener_caso(db_session, caso_id)
    actualizar_caso(db_session, caso, estado="FICHA_EN_REVISION", ficha={})

    r = client.post(f"/casos/{caso_id}/ficha/confirmacion", headers=auth_cookie)
    assert r.status_code == 409


# ── Propuestas ────────────────────────────────────────────────────────

def test_propuesta_sin_ficha_confirmada(client, auth_cookie):
    r = client.post("/casos", json={"asegurado": "A", "rut": "1"}, headers=auth_cookie)
    caso_id = r.json()["caso_id"]

    r = client.post(f"/casos/{caso_id}/propuestas", json={"ajuste_comercial": "0"}, headers=auth_cookie)
    assert r.status_code == 409


# ── Cotizaciones ──────────────────────────────────────────────────────

def test_cotizacion_propuesta_no_aprobada(client, auth_cookie):
    r = client.post("/casos", json={"asegurado": "A", "rut": "1"}, headers=auth_cookie)
    caso_id = r.json()["caso_id"]

    r = client.post(f"/casos/{caso_id}/cotizaciones", json={"propuesta_version": 1}, headers=auth_cookie)
    assert r.status_code == 404


# ── Trabajos ──────────────────────────────────────────────────────────

def test_trabajo_no_encontrado(client, auth_cookie):
    r = client.get("/trabajos/inexistente", headers=auth_cookie)
    assert r.status_code == 404
