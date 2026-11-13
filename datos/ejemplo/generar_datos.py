"""Genera tarifario.xlsx y cartera.xlsx con datos ficticios de §8."""

from pathlib import Path

from openpyxl import Workbook


def generar_tarifario(ruta: Path) -> None:
    wb = Workbook()

    # ── parametros ─────────────────────────────────────────────────────
    ws = wb.active
    assert ws is not None
    ws.title = "parametros"
    ws.append(["clave", "valor"])
    for clave, valor in [
        ("version", "2024-01"),
        ("vigente_desde", "2024-01-01"),
        ("moneda", "UF"),
        ("prima_minima", "15"),
        ("pct_comision", "0.15"),
    ]:
        ws.append([clave, valor])

    # ── ocupaciones ────────────────────────────────────────────────────
    ws = wb.create_sheet("ocupaciones")
    ws.append(["codigo", "descripcion", "tasa_base_por_mil", "apetito"])
    for fila in [
        ("OC-101", "Oficinas", "0.80", "DENTRO"),
        ("OC-205", "Bodega no inflamables", "1.50", "DENTRO"),
        ("OC-310", "Fábrica de muebles de madera", "3.20", "REFERIR"),
        ("OC-999", "Fábrica de fuegos artificiales", None, "DECLINAR"),
    ]:
        ws.append(list(fila))

    # ── construccion ───────────────────────────────────────────────────
    ws = wb.create_sheet("construccion")
    ws.append(["clase", "descripcion", "factor"])
    for fila in [
        ("A", "Hormigón armado", "0.90"),
        ("B", "Albañilería reforzada", "1.00"),
        ("C", "Estructura metálica", "1.25"),
        ("D", "Madera", "1.60"),
    ]:
        ws.append(list(fila))

    # ── proteccion ─────────────────────────────────────────────────────
    ws = wb.create_sheet("proteccion")
    ws.append(["nivel", "descripcion", "factor"])
    for fila in [
        ("ROCIADORES", "Sistema de rociadores automáticos", "0.75"),
        ("RED_HUMEDA_DETECCION", "Red húmeda con detección automática", "0.90"),
        ("EXTINTORES", "Extintores portátiles", "1.00"),
        ("NINGUNA", "Sin protecciones contra incendio", "1.20"),
    ]:
        ws.append(list(fila))

    # ── deducible ──────────────────────────────────────────────────────
    ws = wb.create_sheet("deducible")
    ws.append(["monto_uf", "factor"])
    for fila in [("10", "1.00"), ("50", "0.92"), ("100", "0.85")]:
        ws.append(list(fila))

    # ── siniestralidad ─────────────────────────────────────────────────
    ws = wb.create_sheet("siniestralidad")
    ws.append(["hasta_pct", "factor", "apetito"])
    for fila in [
        ("30", "0.95", None),
        ("60", "1.00", None),
        ("100", "1.20", None),
        (None, "1.50", "REFERIR"),
    ]:
        ws.append(list(fila))

    # ── sismo ──────────────────────────────────────────────────────────
    ws = wb.create_sheet("sismo")
    ws.append(["zona", "A", "B", "C", "D"])
    for fila in [
        (1, "0.50", "0.70", "1.00", "1.50"),
        (2, "0.80", "1.10", "1.60", "2.40"),
        (3, "1.10", "1.50", "2.20", "3.20"),
    ]:
        ws.append(list(fila))

    # ── facultades ─────────────────────────────────────────────────────
    ws = wb.create_sheet("facultades")
    ws.append(["rol", "max_suma_asegurada_uf", "max_ajuste_pct", "aprueba_referir"])
    for fila in [
        ("SUSCRIPTOR", "200000", "15", "NO"),
        ("SUSCRIPTOR_SENIOR", "1000000", "25", "SI"),
    ]:
        ws.append(list(fila))

    wb.save(ruta)


def generar_cartera(ruta: Path) -> None:
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "cartera"
    ws.append([
        "riesgo_id", "ocupacion_codigo", "ocupacion_desc",
        "construccion_clase", "suma_asegurada_uf",
        "tasa_aplicada_por_mil", "siniestralidad_pct", "anio",
    ])
    datos = [
        ("R001", "OC-101", "Oficinas centro", "A", 55000, 0.62, 10, 2023),
        ("R002", "OC-101", "Oficinas providencia", "A", 48000, 0.65, 0, 2023),
        ("R003", "OC-101", "Oficinas las condes", "A", 70000, 0.60, 5, 2022),
        ("R004", "OC-101", "Oficinas ñuñoa", "A", 42000, 0.68, 15, 2023),
        ("R005", "OC-101", "Oficinas viña del mar", "A", 65000, 0.61, 0, 2022),
        ("R006", "OC-101", "Oficinas santiago centro", "B", 60000, 0.72, 8, 2023),
        ("R007", "OC-205", "Bodega san bernardo", "B", 80000, 1.50, 20, 2023),
        ("R008", "OC-205", "Bodega quilicura", "A", 120000, 1.35, 0, 2022),
        ("R009", "OC-310", "Mueblería maipú", "C", 45000, 3.80, 40, 2023),
        ("R010", "OC-310", "Fábrica muebles rancagua", "C", 35000, 3.65, 55, 2022),
        ("R011", "OC-101", "Oficinas concepción", "A", 200000, 0.55, 0, 2023),
        ("R012", "OC-101", "Oficinas temuco", "D", 30000, 1.10, 25, 2022),
        ("R013", "OC-205", "Bodega pudahuel", "B", 500000, 1.48, 10, 2023),
        ("R014", "OC-101", "Oficinas la serena", "A", 15000, 0.70, 0, 2023),
        ("R015", "OC-101", "Oficinas antofagasta", "A", 58000, 0.63, 12, 2022),
    ]
    for fila in datos:
        ws.append(list(fila))
    wb.save(ruta)


if __name__ == "__main__":
    directorio = Path(__file__).parent
    generar_tarifario(directorio / "tarifario.xlsx")
    generar_cartera(directorio / "cartera.xlsx")
    print("Archivos generados en", directorio)
