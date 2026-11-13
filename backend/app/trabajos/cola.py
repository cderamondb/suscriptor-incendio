"""Cola de trabajos en segundo plano — §0.3.

Máximo 1 trabajo de IA en curso por dyno (Semaphore(1)).
Impide 2 trabajos EN_CURSO sobre el mismo caso.
Diseñado para que mover a worker separado no toque api/ ni agente/.
"""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.persistencia.crud import crear_trabajo, obtener_trabajo
from app.persistencia.sesion_db import SessionLocal

logger = logging.getLogger(__name__)

_semaforo = threading.Semaphore(1)


def encolar(
    db: Session,
    caso_id: str,
    tipo: str,
    mensaje: str | None = None,
) -> str:
    trabajo = crear_trabajo(
        db,
        caso_id=caso_id,
        tipo=tipo,
        prompt_version=settings.prompt_version,
        modelo=settings.inference_model_id,
    )
    trabajo_id = trabajo.id

    hilo = threading.Thread(
        target=_ejecutar_trabajo,
        args=(trabajo_id, caso_id, tipo, mensaje),
        daemon=True,
    )
    hilo.start()
    return trabajo_id


def _ejecutar_trabajo(
    trabajo_id: str,
    caso_id: str,
    tipo: str,
    mensaje: str | None,
) -> None:
    _semaforo.acquire()
    db = SessionLocal()
    try:
        trabajo = obtener_trabajo(db, trabajo_id)
        if not trabajo:
            return
        trabajo.estado = "EN_CURSO"
        db.commit()

        if tipo == "EXTRACCION":
            _ejecutar_extraccion(db, trabajo_id, caso_id)
        elif tipo == "AGENTE":
            _ejecutar_agente(db, trabajo_id, caso_id, mensaje or "")
        else:
            trabajo.estado = "ERROR"
            trabajo.codigo_error = "TIPO_DESCONOCIDO"
            trabajo.terminado = datetime.now(UTC)
            db.commit()

    except Exception as e:
        logger.exception("Error en trabajo %s: %s", trabajo_id, e)
        try:
            trabajo = obtener_trabajo(db, trabajo_id)
            if trabajo and trabajo.estado == "EN_CURSO":
                trabajo.estado = "ERROR"
                trabajo.codigo_error = "ERROR_INTERNO"
                trabajo.terminado = datetime.now(UTC)
                db.commit()
        except Exception:
            logger.exception("Error al marcar trabajo como fallido")
    finally:
        db.close()
        _semaforo.release()


def _ejecutar_extraccion(db: Session, trabajo_id: str, caso_id: str) -> None:
    from app.agente.bucle import ejecutar_bucle
    ejecutar_bucle(db, trabajo_id, caso_id, tipo="EXTRACCION")


def _ejecutar_agente(db: Session, trabajo_id: str, caso_id: str, mensaje: str) -> None:
    from app.agente.bucle import ejecutar_bucle
    ejecutar_bucle(db, trabajo_id, caso_id, tipo="AGENTE", mensaje=mensaje)
