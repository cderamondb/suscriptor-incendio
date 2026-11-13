import { useEffect, useState } from "react";
import { obtenerTrabajo, ApiErrorResponse } from "../api/cliente";
import type { Trabajo } from "../tipos";

interface Props {
  trabajoId: string;
  onCompletado: () => void;
}

export default function EstadoTrabajo({ trabajoId, onCompletado }: Props) {
  const [trabajo, setTrabajo] = useState<Trabajo | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let activo = true;
    const intervalo = setInterval(async () => {
      try {
        const t = await obtenerTrabajo(trabajoId);
        if (!activo) return;
        setTrabajo(t);
        if (t.estado === "OK" || t.estado === "ERROR") {
          clearInterval(intervalo);
          if (t.estado === "OK") {
            setTimeout(() => { if (activo) onCompletado(); }, 800);
          }
        }
      } catch (err) {
        if (!activo) return;
        setError(err instanceof ApiErrorResponse ? err.message : "Error al consultar trabajo");
        clearInterval(intervalo);
      }
    }, 3000);

    return () => { activo = false; clearInterval(intervalo); };
  }, [trabajoId, onCompletado]);

  if (error) return <p className="text-red-600 text-sm">{error}</p>;

  return (
    <div className="border rounded p-4 bg-white space-y-2">
      <div className="flex items-center gap-2">
        {trabajo?.estado === "OK" ? (
          <span className="text-green-600 font-medium text-sm">Completado</span>
        ) : trabajo?.estado === "ERROR" ? (
          <span className="text-red-600 font-medium text-sm">
            Error: {trabajo.error_codigo ?? "desconocido"}
          </span>
        ) : (
          <>
            <svg className="animate-spin h-4 w-4 text-blue-600" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="text-sm text-gray-600">Procesando...</span>
          </>
        )}
      </div>
      {trabajo && trabajo.tokens_entrada > 0 && (
        <p className="text-xs text-gray-500">
          Tokens: entrada {trabajo.tokens_entrada} · salida {trabajo.tokens_salida}
        </p>
      )}
    </div>
  );
}
