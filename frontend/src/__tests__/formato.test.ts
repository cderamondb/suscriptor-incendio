import { describe, it, expect } from "vitest";
import { formatMonto, formatFecha, estadoLabel, estadoColor } from "../formato";

describe("formatMonto", () => {
  it("formatea entero", () => {
    expect(formatMonto(1000)).toBe("1.000,00");
  });

  it("formatea decimal string", () => {
    expect(formatMonto("1234.56")).toBe("1.234,56");
  });

  it("formatea número pequeño", () => {
    expect(formatMonto("101.08")).toBe("101,08");
  });

  it("maneja cero", () => {
    expect(formatMonto(0)).toBe("0,00");
  });

  it("retorna original si no es número", () => {
    expect(formatMonto("abc")).toBe("abc");
  });
});

describe("formatFecha", () => {
  it("convierte ISO a dd-mm-yyyy", () => {
    expect(formatFecha("2025-01-15")).toBe("15-01-2025");
  });

  it("retorna vacío para vacío", () => {
    expect(formatFecha("")).toBe("");
  });
});

describe("estadoLabel", () => {
  it("traduce BORRADOR", () => {
    expect(estadoLabel("BORRADOR")).toBe("Borrador");
  });

  it("retorna original si no existe", () => {
    expect(estadoLabel("OTRO")).toBe("OTRO");
  });
});

describe("estadoColor", () => {
  it("retorna color para COTIZADO", () => {
    expect(estadoColor("COTIZADO")).toContain("bg-indigo");
  });

  it("retorna gris por defecto", () => {
    expect(estadoColor("DESCONOCIDO")).toContain("bg-gray");
  });
});
