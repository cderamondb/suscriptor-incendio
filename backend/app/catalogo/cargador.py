"""Carga tarifario.xlsx y lo convierte en un objeto Tarifario validado."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

from openpyxl import load_workbook

from app.dominio.modelos import (
    ClaseConstruccion,
    FactorConstruccion,
    FactorDeducible,
    FactorProteccion,
    FacultadRol,
    NivelApetito,
    NivelProteccion,
    Ocupacion,
    ParametrosTarifario,
    RolUsuario,
    Tarifario,
    TasaSismo,
    TramoSiniestralidad,
)

HOJAS_REQUERIDAS = [
    "parametros", "ocupaciones", "construccion", "proteccion",
    "deducible", "siniestralidad", "sismo", "facultades",
]


class ErrorCargaTarifario(Exception):
    def __init__(self, hoja: str, fila: int, detalle: str) -> None:
        self.hoja = hoja
        self.fila = fila
        super().__init__(f"[{hoja}] fila {fila}: {detalle}")


def _dec(valor: object, hoja: str, fila: int, col: str) -> Decimal:
    if valor is None:
        raise ErrorCargaTarifario(hoja, fila, f"columna '{col}' vacía")
    try:
        return Decimal(str(valor))
    except InvalidOperation as e:
        raise ErrorCargaTarifario(hoja, fila, f"'{col}' no es numérico: {valor}") from e


def _str(valor: object, hoja: str, fila: int, col: str) -> str:
    if valor is None or str(valor).strip() == "":
        raise ErrorCargaTarifario(hoja, fila, f"columna '{col}' vacía")
    return str(valor).strip()


def cargar_tarifario(ruta: str | Path) -> Tarifario:
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"Tarifario no encontrado: {ruta}")

    wb = load_workbook(ruta, read_only=True, data_only=True)
    hojas_presentes = set(wb.sheetnames)
    for hoja in HOJAS_REQUERIDAS:
        if hoja not in hojas_presentes:
            raise ErrorCargaTarifario(hoja, 0, "hoja faltante")

    parametros = _cargar_parametros(wb["parametros"])
    ocupaciones = _cargar_ocupaciones(wb["ocupaciones"])
    construccion = _cargar_construccion(wb["construccion"])
    proteccion = _cargar_proteccion(wb["proteccion"])
    deducible = _cargar_deducible(wb["deducible"])
    siniestralidad = _cargar_siniestralidad(wb["siniestralidad"])
    sismo = _cargar_sismo(wb["sismo"])
    facultades = _cargar_facultades(wb["facultades"])
    wb.close()

    return Tarifario(
        parametros=parametros,
        ocupaciones=ocupaciones,
        construccion=construccion,
        proteccion=proteccion,
        deducible=deducible,
        siniestralidad=siniestralidad,
        sismo=sismo,
        facultades=facultades,
    )


def _cargar_parametros(ws: object) -> ParametrosTarifario:
    h = "parametros"
    pares: dict[str, str] = {}
    for fila_num, fila in enumerate(_filas(ws), start=2):
        clave = _str(fila[0], h, fila_num, "clave")
        pares[clave] = str(fila[1]) if fila[1] is not None else ""

    for clave in ("version", "vigente_desde", "moneda", "prima_minima", "pct_comision"):
        if clave not in pares:
            raise ErrorCargaTarifario(h, 0, f"falta parámetro '{clave}'")

    return ParametrosTarifario(
        version=pares["version"],
        vigente_desde=pares["vigente_desde"],
        moneda=pares["moneda"],
        prima_minima=Decimal(pares["prima_minima"]),
        pct_comision=Decimal(pares["pct_comision"]),
    )


def _cargar_ocupaciones(ws: object) -> dict[str, Ocupacion]:
    h = "ocupaciones"
    resultado: dict[str, Ocupacion] = {}
    for fila_num, fila in enumerate(_filas(ws), start=2):
        codigo = _str(fila[0], h, fila_num, "codigo")
        descripcion = _str(fila[1], h, fila_num, "descripcion")
        apetito_str = _str(fila[3], h, fila_num, "apetito")
        apetito = NivelApetito(apetito_str)

        tasa: Decimal | None = None
        if apetito != NivelApetito.DECLINAR:
            tasa = _dec(fila[2], h, fila_num, "tasa_base_por_mil")

        resultado[codigo] = Ocupacion(
            codigo=codigo,
            descripcion=descripcion,
            tasa_base_por_mil=tasa if tasa is not None else Decimal("0"),
            apetito=apetito,
        )
    return resultado


def _cargar_construccion(ws: object) -> dict[ClaseConstruccion, FactorConstruccion]:
    h = "construccion"
    resultado: dict[ClaseConstruccion, FactorConstruccion] = {}
    for fila_num, fila in enumerate(_filas(ws), start=2):
        clase = ClaseConstruccion(_str(fila[0], h, fila_num, "clase"))
        resultado[clase] = FactorConstruccion(
            clase=clase,
            descripcion=_str(fila[1], h, fila_num, "descripcion"),
            factor=_dec(fila[2], h, fila_num, "factor"),
        )
    return resultado


def _cargar_proteccion(ws: object) -> dict[NivelProteccion, FactorProteccion]:
    h = "proteccion"
    resultado: dict[NivelProteccion, FactorProteccion] = {}
    for fila_num, fila in enumerate(_filas(ws), start=2):
        nivel = NivelProteccion(_str(fila[0], h, fila_num, "nivel"))
        resultado[nivel] = FactorProteccion(
            nivel=nivel,
            descripcion=_str(fila[1], h, fila_num, "descripcion"),
            factor=_dec(fila[2], h, fila_num, "factor"),
        )
    return resultado


def _cargar_deducible(ws: object) -> dict[Decimal, FactorDeducible]:
    h = "deducible"
    resultado: dict[Decimal, FactorDeducible] = {}
    for fila_num, fila in enumerate(_filas(ws), start=2):
        monto = _dec(fila[0], h, fila_num, "monto_uf")
        resultado[monto] = FactorDeducible(
            monto_uf=monto,
            factor=_dec(fila[1], h, fila_num, "factor"),
        )
    return resultado


def _cargar_siniestralidad(ws: object) -> list[TramoSiniestralidad]:
    h = "siniestralidad"
    resultado: list[TramoSiniestralidad] = []
    for fila_num, fila in enumerate(_filas(ws), start=2):
        hasta_pct: Decimal | None = None
        if fila[0] is not None and str(fila[0]).strip() != "":
            hasta_pct = Decimal(str(fila[0]))
        factor = _dec(fila[1], h, fila_num, "factor")
        apetito: NivelApetito | None = None
        if fila[2] is not None and str(fila[2]).strip() != "":
            apetito = NivelApetito(str(fila[2]).strip())
        resultado.append(TramoSiniestralidad(
            hasta_pct=hasta_pct,
            factor=factor,
            apetito=apetito,
        ))
    return resultado


def _cargar_sismo(ws: object) -> dict[int, TasaSismo]:
    h = "sismo"
    resultado: dict[int, TasaSismo] = {}
    for fila_num, fila in enumerate(_filas(ws), start=2):
        zona = int(_dec(fila[0], h, fila_num, "zona"))
        tasas: dict[ClaseConstruccion, Decimal] = {}
        for i, clase in enumerate([
            ClaseConstruccion.A, ClaseConstruccion.B,
            ClaseConstruccion.C, ClaseConstruccion.D,
        ]):
            tasas[clase] = _dec(fila[1 + i], h, fila_num, clase.value)
        resultado[zona] = TasaSismo(zona=zona, tasas=tasas)
    return resultado


def _cargar_facultades(ws: object) -> dict[RolUsuario, FacultadRol]:
    h = "facultades"
    resultado: dict[RolUsuario, FacultadRol] = {}
    for fila_num, fila in enumerate(_filas(ws), start=2):
        rol = RolUsuario(_str(fila[0], h, fila_num, "rol"))
        resultado[rol] = FacultadRol(
            rol=rol,
            max_suma_asegurada_uf=_dec(fila[1], h, fila_num, "max_suma_asegurada_uf"),
            max_ajuste_pct=_dec(fila[2], h, fila_num, "max_ajuste_pct"),
            aprueba_referir=_str(fila[3], h, fila_num, "aprueba_referir").upper() == "SI",
        )
    return resultado


def _filas(ws: object) -> list[tuple[object, ...]]:
    filas = list(ws)  # type: ignore[call-overload]
    if len(filas) <= 1:
        return []
    return [tuple(c.value for c in fila) for fila in filas[1:]]
