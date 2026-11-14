"""Bucle agéntico — §6.4.

(0) presupuesto.verificar antes de cada llamada
(1) system + historial + mensaje
(2) tool_use → ejecutar → devolver resultados
(3) repite hasta end_turn
(4) refusal → ERROR RECHAZO_MODELO
(5) max_tokens → reintentar 1 vez
(6) MAX_PASOS_AGENTE → ERROR TOPE_DE_PASOS
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.agente.cliente import BloqueHerramienta, BloqueTexto, ClienteLLM
from app.agente.herramientas import HERRAMIENTAS_SCHEMA, ejecutar_herramienta
from app.agente.prompts import cargar_system_prompt
from app.config import settings
from app.dominio.modelos import PresupuestoAgotado
from app.persistencia.crud import obtener_caso, obtener_trabajo

logger = logging.getLogger(__name__)

_cliente_override: ClienteLLM | None = None


def set_cliente_override(cliente: ClienteLLM | None) -> None:
    global _cliente_override
    _cliente_override = cliente


def _obtener_cliente() -> ClienteLLM:
    if _cliente_override is not None:
        return _cliente_override

    if settings.proveedor_llm == "anthropic":
        from app.agente.cliente import ClienteAnthropic
        return ClienteAnthropic(
            api_key=settings.anthropic_api_key,
            model_id=settings.inference_model_id or "claude-sonnet-4-6",
            timeout=settings.timeout_llm_s,
        )
    else:
        from app.agente.cliente import ClienteHeroku
        return ClienteHeroku(
            url=settings.inference_url,
            key=settings.inference_key,
            model_id=settings.inference_model_id,
            timeout=settings.timeout_llm_s,
        )


def ejecutar_bucle(
    db: Session,
    trabajo_id: str,
    caso_id: str,
    tipo: str = "EXTRACCION",
    mensaje: str | None = None,
) -> None:
    trabajo = obtener_trabajo(db, trabajo_id)
    if not trabajo:
        return

    cliente = _obtener_cliente()
    system = cargar_system_prompt()
    max_pasos = settings.max_pasos_agente

    mensajes: list[dict] = []
    if tipo == "EXTRACCION":
        mensajes.append({
            "role": "user",
            "content": (
                f"Extrae los datos del caso {caso_id} leyendo todos "
                "los documentos cargados. "
                "Registra cada dato con su origen y cita textual."
            ),
        })
    elif tipo == "AGENTE" and mensaje:
        mensajes.append({"role": "user", "content": mensaje})

    herramientas_usadas: list[str] = []
    tokens_entrada_total = 0
    tokens_salida_total = 0
    tokens_cache_total = 0
    pasos = 0
    reintentos_max_tokens = 0

    try:
        while pasos < max_pasos:
            _verificar_presupuesto(db, caso_id)

            resp = cliente.enviar(mensajes, HERRAMIENTAS_SCHEMA, system=system)
            pasos += 1
            tokens_entrada_total += resp.tokens_entrada
            tokens_salida_total += resp.tokens_salida
            tokens_cache_total += resp.tokens_cache

            _registrar_tokens(db, caso_id, resp.tokens_entrada, resp.tokens_salida)

            if resp.motivo_termino == "end_turn":
                texto_final = ""
                for bloque in resp.contenido:
                    if isinstance(bloque, BloqueTexto):
                        texto_final += bloque.texto
                _finalizar_ok(
                    db, trabajo, pasos, tokens_entrada_total, tokens_salida_total,
                    tokens_cache_total, herramientas_usadas, texto_final,
                    resp.modelo,
                )
                return

            if resp.motivo_termino == "max_tokens":
                if reintentos_max_tokens < 1:
                    reintentos_max_tokens += 1
                    continue
                _finalizar_error(
                    db, trabajo, "TOPE_DE_TOKENS", pasos, tokens_entrada_total,
                    tokens_salida_total, tokens_cache_total, herramientas_usadas,
                )
                return

            if resp.motivo_termino == "refusal":
                _finalizar_error(
                    db, trabajo, "RECHAZO_MODELO", pasos, tokens_entrada_total,
                    tokens_salida_total, tokens_cache_total, herramientas_usadas,
                )
                return

            logger.info("Paso %d, motivo=%s", pasos, resp.motivo_termino)
            tool_uses = [b for b in resp.contenido if isinstance(b, BloqueHerramienta)]
            if not tool_uses:
                texto_final = ""
                for bloque in resp.contenido:
                    if isinstance(bloque, BloqueTexto):
                        texto_final += bloque.texto
                _finalizar_ok(
                    db, trabajo, pasos, tokens_entrada_total, tokens_salida_total,
                    tokens_cache_total, herramientas_usadas, texto_final,
                    resp.modelo,
                )
                return

            mensajes.append({
                "role": "assistant",
                "content": [
                    _bloque_a_dict(b) for b in resp.contenido
                ],
            })

            resultados_herramientas = []
            for tu in tool_uses:
                logger.info("Herramienta: %s", tu.nombre)
                herramientas_usadas.append(tu.nombre)
                resultado = ejecutar_herramienta(tu.nombre, tu.entrada, db, caso_id)
                resultados_herramientas.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": json.dumps(resultado, ensure_ascii=False, default=str),
                    "is_error": resultado.get("is_error", False),
                })

            mensajes.append({"role": "user", "content": resultados_herramientas})

        _finalizar_error(
            db, trabajo, "TOPE_DE_PASOS", pasos, tokens_entrada_total,
            tokens_salida_total, tokens_cache_total, herramientas_usadas,
        )

    except PresupuestoAgotado:
        _finalizar_error(
            db, trabajo, "PRESUPUESTO_AGOTADO", pasos, tokens_entrada_total,
            tokens_salida_total, tokens_cache_total, herramientas_usadas,
        )


def _bloque_a_dict(bloque: BloqueTexto | BloqueHerramienta) -> dict:
    if isinstance(bloque, BloqueTexto):
        return {"type": "text", "text": bloque.texto}
    return {
        "type": "tool_use",
        "id": bloque.id,
        "name": bloque.nombre,
        "input": bloque.entrada,
    }


def _verificar_presupuesto(db: Session, caso_id: str) -> None:
    from datetime import timedelta
    from datetime import timezone as tz
    caso = obtener_caso(db, caso_id)
    if not caso:
        return

    tokens_caso = (caso.tokens_entrada or 0) + (caso.tokens_salida or 0)
    if tokens_caso >= settings.max_tokens_por_caso:
        raise PresupuestoAgotado("caso")


    from app.persistencia.crud import obtener_tokens_dia
    zona_chile = tz(timedelta(hours=-3))
    hoy = datetime.now(zona_chile).date()
    tokens_dia = obtener_tokens_dia(db, hoy)
    if tokens_dia >= settings.max_tokens_dia:
        raise PresupuestoAgotado("dia")


def _registrar_tokens(db: Session, caso_id: str, tokens_entrada: int, tokens_salida: int) -> None:
    from datetime import timedelta
    from datetime import timezone as tz

    from app.persistencia.crud import sumar_tokens_dia

    caso = obtener_caso(db, caso_id)
    if caso:
        caso.tokens_entrada = (caso.tokens_entrada or 0) + tokens_entrada
        caso.tokens_salida = (caso.tokens_salida or 0) + tokens_salida
        db.commit()

    zona_chile = tz(timedelta(hours=-3))
    hoy = datetime.now(zona_chile).date()
    sumar_tokens_dia(db, hoy, tokens_entrada + tokens_salida)


def _finalizar_ok(
    db: Session,
    trabajo: object,
    pasos: int,
    tokens_entrada: int,
    tokens_salida: int,
    tokens_cache: int,
    herramientas_usadas: list[str],
    texto: str,
    modelo: str = "",
) -> None:
    trabajo.estado = "OK"  # type: ignore[attr-defined]
    trabajo.pasos = pasos  # type: ignore[attr-defined]
    trabajo.tokens_entrada = tokens_entrada  # type: ignore[attr-defined]
    trabajo.tokens_salida = tokens_salida  # type: ignore[attr-defined]
    trabajo.tokens_cache = tokens_cache  # type: ignore[attr-defined]
    trabajo.herramientas_usadas = herramientas_usadas  # type: ignore[attr-defined]
    trabajo.resultado = {"respuesta": texto}  # type: ignore[attr-defined]
    trabajo.modelo = modelo  # type: ignore[attr-defined]
    trabajo.terminado = datetime.now(UTC)  # type: ignore[attr-defined]
    db.commit()


def _finalizar_error(
    db: Session,
    trabajo: object,
    codigo: str,
    pasos: int,
    tokens_entrada: int,
    tokens_salida: int,
    tokens_cache: int,
    herramientas_usadas: list[str],
) -> None:
    trabajo.estado = "ERROR"  # type: ignore[attr-defined]
    trabajo.codigo_error = codigo  # type: ignore[attr-defined]
    trabajo.pasos = pasos  # type: ignore[attr-defined]
    trabajo.tokens_entrada = tokens_entrada  # type: ignore[attr-defined]
    trabajo.tokens_salida = tokens_salida  # type: ignore[attr-defined]
    trabajo.tokens_cache = tokens_cache  # type: ignore[attr-defined]
    trabajo.herramientas_usadas = herramientas_usadas  # type: ignore[attr-defined]
    trabajo.terminado = datetime.now(UTC)  # type: ignore[attr-defined]
    db.commit()
