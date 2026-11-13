import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import TablaFactores from "../componentes/TablaFactores";
import type { PropuestaTarifa } from "../tipos";

describe("TablaFactores", () => {
  const propuesta: PropuestaTarifa = {
    version_tarifario: "2024-01",
    tasa_incendio: "0.50",
    tasa_sismo: "0.30",
    factor_construccion: "1.00",
    factor_proteccion: "0.95",
    factor_deducible: "1.00",
    factor_siniestralidad: "1.00",
    lineas: [
      {
        ubicacion_idx: 0,
        item_tipo: "EDIFICIO",
        cobertura: "INCENDIO",
        suma_asegurada: "5000.00",
        tasa_por_mil: "0.50",
        prima: "2.50",
        prima_neta: "2.38",
      },
    ],
    prima_tecnica: "2.50",
    ajuste_comercial: "0",
    prima_ajustada: "2.50",
    prima_neta: "2.38",
    iva: "0.45",
    prima_bruta: "2.83",
    comision: "0.24",
    comision_corredor: "0.24",
    alertas: [],
  };

  it("renderiza tasas", () => {
    render(<TablaFactores propuesta={propuesta} />);
    expect(screen.getByText("Tasa incendio")).toBeTruthy();
    expect(screen.getByText("0.50‰")).toBeTruthy();
  });

  it("renderiza líneas de prima", () => {
    render(<TablaFactores propuesta={propuesta} />);
    expect(screen.getByText("EDIFICIO")).toBeTruthy();
    expect(screen.getByText("INCENDIO")).toBeTruthy();
  });

  it("renderiza totales con formato es-CL", () => {
    render(<TablaFactores propuesta={propuesta} />);
    expect(screen.getByText("Prima bruta")).toBeTruthy();
    expect(screen.getByText("2,83 UF")).toBeTruthy();
  });

  it("muestra comisión corredor", () => {
    render(<TablaFactores propuesta={propuesta} />);
    expect(screen.getByText("Comisión corredor")).toBeTruthy();
  });
});
