import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  obtenerAnalisis,
  crearPropuesta,
  decidirPropuesta,
  crearCotizacion,
  urlPdf,
  ApiErrorResponse,
} from "../api/cliente";
import TablaFactores from "../componentes/TablaFactores";
import type { ResultadoApetito, PropuestaTarifa } from "../tipos";

export default function CasoPropuesta() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [apetito, setApetito] = useState<ResultadoApetito | null>(null);
  const [propuesta, setPropuesta] = useState<PropuestaTarifa | null>(null);
  const [version, setVersion] = useState<number>(0);
  const [ajuste, setAjuste] = useState("0");
  const [comentario, setComentario] = useState("");
  const [cotizacionId, setCotizacionId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    if (!id) return;
    obtenerAnalisis(id)
      .then((data) => setApetito(data.apetito))
      .catch(() => {});
  }, [id]);

  async function handleCrearPropuesta() {
    if (!id) return;
    setError("");
    setCargando(true);
    try {
      const data = await crearPropuesta(id, ajuste);
      setPropuesta(data.propuesta);
      setVersion(data.version);
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Error al crear propuesta");
    } finally {
      setCargando(false);
    }
  }

  async function handleDecision(decision: "aprobar" | "rechazar") {
    if (!id) return;
    setError("");
    setCargando(true);
    try {
      await decidirPropuesta(id, version, decision, comentario);
      if (decision === "aprobar") {
        const cot = await crearCotizacion(id, version);
        setCotizacionId(cot.cotizacion_id);
      } else {
        navigate(`/casos/${id}/ficha`);
      }
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Error en decisión");
    } finally {
      setCargando(false);
    }
  }

  const COLORES_APETITO: Record<string, string> = {
    DENTRO: "bg-green-100 text-green-800 border-green-300",
    REFERIR: "bg-yellow-100 text-yellow-800 border-yellow-300",
    DECLINAR: "bg-red-100 text-red-800 border-red-300",
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <nav className="flex gap-4 text-sm mb-6 border-b pb-2">
        <button onClick={() => navigate(`/casos/${id}/documentos`)} className="text-gray-500 hover:text-gray-700 pb-2">
          Documentos
        </button>
        <button onClick={() => navigate(`/casos/${id}/ficha`)} className="text-gray-500 hover:text-gray-700 pb-2">
          Ficha
        </button>
        <span className="font-semibold text-blue-600 border-b-2 border-blue-600 pb-2">
          Propuesta
        </span>
      </nav>

      <h1 className="text-lg font-bold mb-4">Propuesta y cotización</h1>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {apetito && (
        <div className={`border rounded p-3 mb-4 ${COLORES_APETITO[apetito.resultado] ?? ""}`}>
          <h2 className="font-semibold text-sm mb-1">
            Apetito: {apetito.resultado}
          </h2>
          {apetito.reglas_activadas.length > 0 && (
            <ul className="text-xs space-y-0.5">
              {apetito.reglas_activadas.map((r, i) => (
                <li key={i}>{r.codigo}: {r.motivo}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {!propuesta && (
        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium block mb-1">Ajuste comercial</label>
            <input
              type="text"
              value={ajuste}
              onChange={(e) => setAjuste(e.target.value)}
              className="border rounded px-3 py-2 text-sm w-32"
              placeholder="0"
            />
          </div>
          <button
            onClick={handleCrearPropuesta}
            disabled={cargando}
            className="bg-blue-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 min-h-[44px]"
          >
            {cargando ? "Calculando..." : "Generar propuesta"}
          </button>
        </div>
      )}

      {propuesta && (
        <div className="space-y-4">
          <TablaFactores propuesta={propuesta} />

          {!cotizacionId && (
            <div className="space-y-3 border-t pt-4">
              <div>
                <label className="text-sm font-medium block mb-1">Comentario (opcional)</label>
                <textarea
                  value={comentario}
                  onChange={(e) => setComentario(e.target.value)}
                  rows={2}
                  className="border rounded px-3 py-2 text-sm w-full"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleDecision("aprobar")}
                  disabled={cargando}
                  className="bg-green-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-green-700 disabled:opacity-50 min-h-[44px]"
                >
                  Aprobar y cotizar
                </button>
                <button
                  onClick={() => handleDecision("rechazar")}
                  disabled={cargando}
                  className="border border-red-300 text-red-600 rounded px-4 py-2 text-sm font-medium hover:bg-red-50 disabled:opacity-50 min-h-[44px]"
                >
                  Rechazar
                </button>
              </div>
            </div>
          )}

          {cotizacionId && (
            <div className="border border-green-300 bg-green-50 rounded p-4 space-y-2">
              <p className="text-sm font-medium text-green-800">Cotización generada</p>
              <a
                href={urlPdf(cotizacionId)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block bg-green-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-green-700 min-h-[44px] leading-[28px]"
              >
                Descargar PDF
              </a>
            </div>
          )}
        </div>
      )}

      <div className="mt-8">
        <button
          onClick={() => navigate("/bandeja")}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← Volver a la bandeja
        </button>
      </div>
    </div>
  );
}
