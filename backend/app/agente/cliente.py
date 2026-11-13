"""Interfaz ClienteLLM y tres implementaciones: Heroku, Anthropic, Falso."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class BloqueHerramienta:
    id: str
    nombre: str
    entrada: dict


@dataclass
class BloqueTexto:
    texto: str


@dataclass
class Respuesta:
    contenido: list[BloqueTexto | BloqueHerramienta] = field(default_factory=list)
    motivo_termino: str = "end_turn"
    tokens_entrada: int = 0
    tokens_salida: int = 0
    tokens_cache: int = 0
    modelo: str = ""


class ClienteLLM(Protocol):
    def enviar(
        self,
        mensajes: list[dict],
        herramientas: list[dict],
        system: str = "",
    ) -> Respuesta: ...


class ClienteHeroku:
    def __init__(self, url: str, key: str, model_id: str, timeout: int = 120):
        self.url = url
        self.key = key
        self.model_id = model_id
        self.timeout = timeout

    def enviar(
        self,
        mensajes: list[dict],
        herramientas: list[dict],
        system: str = "",
    ) -> Respuesta:
        import anthropic
        client = anthropic.Anthropic(
            base_url=self.url,
            api_key=self.key,
            timeout=self.timeout,
        )
        kwargs: dict = {
            "model": self.model_id,
            "max_tokens": 4096,
            "messages": mensajes,
        }
        if system:
            kwargs["system"] = system
        if herramientas:
            kwargs["tools"] = herramientas
            kwargs["tool_choice"] = {"type": "auto"}

        resp = client.messages.create(**kwargs)
        return self._mapear(resp)

    def _mapear(self, resp: object) -> Respuesta:
        bloques: list[BloqueTexto | BloqueHerramienta] = []
        for bloque in resp.content:  # type: ignore[attr-defined]
            if bloque.type == "text":
                bloques.append(BloqueTexto(texto=bloque.text))
            elif bloque.type == "tool_use":
                bloques.append(BloqueHerramienta(
                    id=bloque.id, nombre=bloque.name, entrada=bloque.input,
                ))
        return Respuesta(
            contenido=bloques,
            motivo_termino=resp.stop_reason,  # type: ignore[attr-defined]
            tokens_entrada=resp.usage.input_tokens,  # type: ignore[attr-defined]
            tokens_salida=resp.usage.output_tokens,  # type: ignore[attr-defined]
            tokens_cache=getattr(resp.usage, "cache_read_input_tokens", 0) or 0,  # type: ignore[attr-defined]
            modelo=resp.model,  # type: ignore[attr-defined]
        )


class ClienteAnthropic:
    def __init__(
        self, api_key: str,
        model_id: str = "claude-sonnet-4-20250514",
        timeout: int = 120,
    ):
        self.api_key = api_key
        self.model_id = model_id
        self.timeout = timeout

    def enviar(
        self,
        mensajes: list[dict],
        herramientas: list[dict],
        system: str = "",
    ) -> Respuesta:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key, timeout=self.timeout)
        kwargs: dict = {
            "model": self.model_id,
            "max_tokens": 4096,
            "messages": mensajes,
        }
        if system:
            kwargs["system"] = system
        if herramientas:
            kwargs["tools"] = herramientas
            kwargs["tool_choice"] = {"type": "auto"}

        resp = client.messages.create(**kwargs)
        return ClienteHeroku._mapear(self, resp)  # type: ignore[arg-type]


class ClienteFalso:
    """Cliente para tests: devuelve secuencias predefinidas de respuestas."""

    def __init__(self, respuestas: list[Respuesta] | None = None):
        self._respuestas = list(respuestas or [])
        self._idx = 0
        self.llamadas: list[dict] = []

    def enviar(
        self,
        mensajes: list[dict],
        herramientas: list[dict],
        system: str = "",
    ) -> Respuesta:
        self.llamadas.append({
            "mensajes": mensajes,
            "herramientas": herramientas,
            "system": system,
        })
        if self._idx < len(self._respuestas):
            resp = self._respuestas[self._idx]
            self._idx += 1
            return resp
        return Respuesta(
            contenido=[BloqueTexto(texto="Sin más respuestas predefinidas.")],
            motivo_termino="end_turn",
            tokens_entrada=100,
            tokens_salida=50,
        )
