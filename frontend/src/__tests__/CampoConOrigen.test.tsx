import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import CampoConOrigen from "../componentes/CampoConOrigen";
import type { Campo } from "../tipos";

describe("CampoConOrigen", () => {
  const campo: Campo<string> = {
    valor: "Acme S.A.",
    estado: "EXTRAIDO",
    confianza: "ALTA",
    origen: [{ documento_id: "abc12345def67890abcdef1234567890", ubicacion: "p1", cita: "texto citado" }],
  };

  it("muestra el valor y label", () => {
    render(<CampoConOrigen label="Razón social" campo={campo} />);
    expect(screen.getByText("Razón social")).toBeTruthy();
    expect(screen.getByText("Acme S.A.")).toBeTruthy();
  });

  it("muestra badge de estado", () => {
    render(<CampoConOrigen label="Test" campo={campo} />);
    expect(screen.getByText("EXTRAIDO")).toBeTruthy();
  });

  it("muestra botón de origen y abre visor", () => {
    render(<CampoConOrigen label="Test" campo={campo} />);
    const btn = screen.getByText("origen");
    fireEvent.click(btn);
    expect(screen.getByText(/abc12345/)).toBeTruthy();
  });

  it("permite edición inline", () => {
    const onCorregir = vi.fn();
    render(<CampoConOrigen label="Test" campo={campo} onCorregir={onCorregir} />);
    fireEvent.click(screen.getByText("Acme S.A."));
    const input = screen.getByDisplayValue("Acme S.A.");
    fireEvent.change(input, { target: { value: "Nuevo" } });
    fireEvent.click(screen.getByText("OK"));
    expect(onCorregir).toHaveBeenCalledWith("Nuevo");
  });
});
