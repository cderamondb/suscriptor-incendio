import { useState } from "react";
import VisorOrigen from "./VisorOrigen";
import type { Campo } from "../tipos";

interface Props {
  label: string;
  campo: Campo<unknown>;
  onCorregir?: (valor: string) => void;
}

const BADGE_COLORES: Record<string, string> = {
  extraido: "bg-blue-100 text-blue-700",
  confirmado: "bg-green-100 text-green-700",
  corregido: "bg-yellow-100 text-yellow-700",
};

export default function CampoConOrigen({ label, campo, onCorregir }: Props) {
  const [editando, setEditando] = useState(false);
  const [valorEdit, setValorEdit] = useState("");
  const [mostrarOrigen, setMostrarOrigen] = useState(false);

  function iniciarEdicion() {
    setValorEdit(String(campo.valor ?? ""));
    setEditando(true);
  }

  function guardar() {
    if (onCorregir && valorEdit !== String(campo.valor ?? "")) {
      onCorregir(valorEdit);
    }
    setEditando(false);
  }

  function cancelar() {
    setEditando(false);
  }

  const valorStr = campo.valor != null ? String(campo.valor) : "—";

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs text-gray-500 min-w-[100px]">{label}</span>
        {editando ? (
          <div className="flex gap-1 flex-1">
            <input
              value={valorEdit}
              onChange={(e) => setValorEdit(e.target.value)}
              className="border rounded px-2 py-1 text-sm flex-1 min-w-0"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter") guardar();
                if (e.key === "Escape") cancelar();
              }}
            />
            <button onClick={guardar} className="text-xs text-green-600 hover:underline">OK</button>
            <button onClick={cancelar} className="text-xs text-gray-400 hover:underline">X</button>
          </div>
        ) : (
          <span
            className="text-sm cursor-pointer hover:underline"
            onClick={iniciarEdicion}
            title="Click para editar"
          >
            {valorStr}
          </span>
        )}
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${BADGE_COLORES[campo.estado] ?? "bg-gray-100 text-gray-600"}`}>
          {campo.estado}
        </span>
        {campo.confianza != null && (
          <span className="text-[10px] text-gray-400">{campo.confianza}</span>
        )}
        {campo.origen && (
          <button
            onClick={() => setMostrarOrigen(true)}
            className="text-[10px] text-blue-500 hover:underline"
            title="Ver origen"
          >
            origen
          </button>
        )}
      </div>
      {mostrarOrigen && campo.origen && campo.origen[0] && (
        <VisorOrigen origen={campo.origen[0]} onCerrar={() => setMostrarOrigen(false)} />
      )}
    </div>
  );
}
