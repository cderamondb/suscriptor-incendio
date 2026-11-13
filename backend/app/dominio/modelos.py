from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────────────────────────────

class EstadoCaso(str, Enum):
    BORRADOR = "BORRADOR"
    DOCUMENTOS_CARGADOS = "DOCUMENTOS_CARGADOS"
    FICHA_EN_REVISION = "FICHA_EN_REVISION"
    FICHA_CONFIRMADA = "FICHA_CONFIRMADA"
    PROPUESTA_EN_REVISION = "PROPUESTA_EN_REVISION"
    PROPUESTA_APROBADA = "PROPUESTA_APROBADA"
    COTIZADO = "COTIZADO"
    DECLINADO = "DECLINADO"


class NivelApetito(str, Enum):
    DENTRO = "DENTRO"
    REFERIR = "REFERIR"
    DECLINAR = "DECLINAR"


class ClaseConstruccion(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class NivelProteccion(str, Enum):
    ROCIADORES = "ROCIADORES"
    RED_HUMEDA_DETECCION = "RED_HUMEDA_DETECCION"
    EXTINTORES = "EXTINTORES"
    NINGUNA = "NINGUNA"


class RolUsuario(str, Enum):
    SUSCRIPTOR = "SUSCRIPTOR"
    SUSCRIPTOR_SENIOR = "SUSCRIPTOR_SENIOR"
    EJECUTIVO_COMERCIAL = "EJECUTIVO_COMERCIAL"
    ADMIN = "ADMIN"


class TipoCobertura(str, Enum):
    INCENDIO = "INCENDIO"
    SISMO = "SISMO"


class TipoAlerta(str, Enum):
    CONTRADICCION = "CONTRADICCION"
    PRIMA_MINIMA_APLICADA = "PRIMA_MINIMA_APLICADA"
    SIN_HISTORIAL = "SIN_HISTORIAL"
    SINIESTRALIDAD_ALTA = "SINIESTRALIDAD_ALTA"
    DOCUMENTO_ILEGIBLE = "DOCUMENTO_ILEGIBLE"
    CITA_NO_ENCONTRADA = "CITA_NO_ENCONTRADA"


class EstadoCampo(str, Enum):
    FALTANTE = "FALTANTE"
    EXTRAIDO = "EXTRAIDO"
    CORREGIDO = "CORREGIDO"
    CONFIRMADO = "CONFIRMADO"


class NivelConfianza(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class TipoItem(str, Enum):
    EDIFICIO = "EDIFICIO"
    CONTENIDOS = "CONTENIDOS"
    MAQUINARIA = "MAQUINARIA"
    EXISTENCIAS = "EXISTENCIAS"


# ── Campo[T] ───────────────────────────────────────────────────────────

T = TypeVar("T")


class Origen(BaseModel):
    documento_id: str
    ubicacion: str
    cita: str


class Campo(BaseModel, Generic[T]):
    valor: T | None = None
    estado: EstadoCampo = EstadoCampo.FALTANTE
    confianza: NivelConfianza | None = None
    origen: list[Origen] = Field(default_factory=list)
    alternativas: list[T] = Field(default_factory=list)


# ── Modelos de negocio ─────────────────────────────────────────────────

class Siniestro(BaseModel):
    fecha: str | None = None
    causa: str | None = None
    monto_incurrido: Decimal | None = None


class HistorialSiniestralidad(BaseModel):
    siniestros: list[Siniestro] = Field(default_factory=list)
    primas_pagadas: Decimal | None = None


class ItemAsegurado(BaseModel):
    tipo: TipoItem
    suma_asegurada: Decimal


class UbicacionRiesgo(BaseModel):
    direccion: Campo[str] = Field(default_factory=Campo)
    comuna: Campo[str] = Field(default_factory=Campo)
    region: Campo[str] = Field(default_factory=Campo)
    coordenadas: Campo[str] = Field(default_factory=Campo)
    ocupacion_codigo: Campo[str] = Field(default_factory=Campo)
    construccion_clase: Campo[ClaseConstruccion] = Field(default_factory=Campo)
    construccion_pisos: Campo[int] = Field(default_factory=Campo)
    construccion_anio: Campo[int] = Field(default_factory=Campo)
    construccion_superficie_m2: Campo[Decimal] = Field(default_factory=Campo)
    proteccion: Campo[NivelProteccion] = Field(default_factory=Campo)
    items: list[ItemAsegurado] = Field(default_factory=list)
    zona_sismica: Campo[int] = Field(default_factory=Campo)


class FichaRiesgo(BaseModel):
    razon_social: Campo[str] = Field(default_factory=Campo)
    rut: Campo[str] = Field(default_factory=Campo)
    actividad_declarada: Campo[str] = Field(default_factory=Campo)
    ubicaciones: list[UbicacionRiesgo] = Field(default_factory=list)
    coberturas_solicitadas: list[TipoCobertura] = Field(default_factory=list)
    deducible_uf: Campo[Decimal] = Field(default_factory=Campo)
    siniestralidad: Campo[HistorialSiniestralidad] = Field(default_factory=Campo)
    vigencia_desde: Campo[str] = Field(default_factory=Campo)
    vigencia_hasta: Campo[str] = Field(default_factory=Campo)
    aseguradora_anterior: Campo[str] = Field(default_factory=Campo)
    prima_anterior: Campo[Decimal] = Field(default_factory=Campo)
    inspeccion: Campo[str] = Field(default_factory=Campo)
    alertas: list[Alerta] = Field(default_factory=list)


class Alerta(BaseModel):
    tipo: TipoAlerta
    detalle: str
    origen: Origen | None = None


# ── Tarifario ──────────────────────────────────────────────────────────

class Ocupacion(BaseModel):
    codigo: str
    descripcion: str
    tasa_base_por_mil: Decimal
    apetito: NivelApetito


class FactorConstruccion(BaseModel):
    clase: ClaseConstruccion
    descripcion: str
    factor: Decimal


class FactorProteccion(BaseModel):
    nivel: NivelProteccion
    descripcion: str
    factor: Decimal


class FactorDeducible(BaseModel):
    monto_uf: Decimal
    factor: Decimal


class TramoSiniestralidad(BaseModel):
    hasta_pct: Decimal | None = None
    factor: Decimal
    apetito: NivelApetito | None = None


class TasaSismo(BaseModel):
    zona: int
    tasas: dict[ClaseConstruccion, Decimal]


class FacultadRol(BaseModel):
    rol: RolUsuario
    max_suma_asegurada_uf: Decimal
    max_ajuste_pct: Decimal
    aprueba_referir: bool


class ParametrosTarifario(BaseModel):
    version: str
    vigente_desde: str
    moneda: str
    prima_minima: Decimal
    pct_comision: Decimal


class Tarifario(BaseModel):
    parametros: ParametrosTarifario
    ocupaciones: dict[str, Ocupacion] = Field(default_factory=dict)
    construccion: dict[ClaseConstruccion, FactorConstruccion] = Field(default_factory=dict)
    proteccion: dict[NivelProteccion, FactorProteccion] = Field(default_factory=dict)
    deducible: dict[Decimal, FactorDeducible] = Field(default_factory=dict)
    siniestralidad: list[TramoSiniestralidad] = Field(default_factory=list)
    sismo: dict[int, TasaSismo] = Field(default_factory=dict)
    facultades: dict[RolUsuario, FacultadRol] = Field(default_factory=dict)


# ── Resultado de tarificación ──────────────────────────────────────────

class LineaPrima(BaseModel):
    ubicacion_idx: int
    item_tipo: TipoItem
    cobertura: TipoCobertura
    suma_asegurada: Decimal
    tasa_por_mil: Decimal
    prima: Decimal


class PropuestaTarifa(BaseModel):
    version_tarifario: str
    tasa_incendio: Decimal | None = None
    tasa_sismo: Decimal | None = None
    factor_construccion: Decimal | None = None
    factor_proteccion: Decimal | None = None
    factor_deducible: Decimal | None = None
    factor_siniestralidad: Decimal | None = None
    lineas: list[LineaPrima] = Field(default_factory=list)
    prima_tecnica: Decimal = Decimal("0")
    ajuste_comercial: Decimal = Decimal("0")
    prima_ajustada: Decimal = Decimal("0")
    prima_neta: Decimal = Decimal("0")
    iva: Decimal = Decimal("0")
    prima_bruta: Decimal = Decimal("0")
    comision: Decimal = Decimal("0")
    alertas: list[Alerta] = Field(default_factory=list)


# ── Resultado de apetito ───────────────────────────────────────────────

class ReglaActivada(BaseModel):
    codigo: str
    motivo: str


class ResultadoApetito(BaseModel):
    resultado: NivelApetito
    reglas_activadas: list[ReglaActivada] = Field(default_factory=list)


# ── Resultado de facultad ──────────────────────────────────────────────

class ResultadoFacultad(BaseModel):
    permitido: bool
    requiere: RolUsuario | None = None


# ── Resultado de completitud ───────────────────────────────────────────

class CampoFaltante(BaseModel):
    ruta: str
    bloqueante: bool


class ReporteCompletitud(BaseModel):
    completo: bool
    faltantes: list[CampoFaltante] = Field(default_factory=list)


# ── Excepciones ────────────────────────────────────────────────────────

class DatosInsuficientes(Exception):
    def __init__(self, campos: list[str]) -> None:
        self.campos = campos
        super().__init__(f"Datos insuficientes: {', '.join(campos)}")


class FueraDeTarifa(Exception):
    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(f"Fuera de tarifa: {motivo}")


class FueraDeApetito(Exception):
    def __init__(self, reglas: list[ReglaActivada]) -> None:
        self.reglas = reglas
        super().__init__(f"Fuera de apetito: {[r.codigo for r in reglas]}")


class FacultadExcedida(Exception):
    def __init__(self, requiere: RolUsuario | None = None) -> None:
        self.requiere = requiere
        super().__init__(f"Facultad excedida, requiere: {requiere}")


class TransicionInvalida(Exception):
    def __init__(self, desde: EstadoCaso, hacia: EstadoCaso) -> None:
        self.desde = desde
        self.hacia = hacia
        super().__init__(f"Transición inválida: {desde} → {hacia}")


class PresupuestoAgotado(Exception):
    def __init__(self, tipo: str = "caso") -> None:
        self.tipo = tipo
        super().__init__(f"Presupuesto agotado: {tipo}")


# Forward reference update
FichaRiesgo.model_rebuild()
