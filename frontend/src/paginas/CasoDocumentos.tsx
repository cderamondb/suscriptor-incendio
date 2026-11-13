import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { listarDocumentos, subirDocumentos, lanzarExtraccion, ApiErrorResponse } from "../api/cliente";
import CargaArchivos from "../componentes/CargaArchivos";
import EstadoTrabajo from "../componentes/EstadoTrabajo";

export default function CasoDocumentos() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [docs, setDocs] = useState<{ documento_id: string; nombre?: string; tipo: string }[]>([]);
  const [trabajoId, setTrabajoId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [subiendo, setSubiendo] = useState(false);

  useEffect(() => {
    if (!id) return;
    listarDocumentos(id)
      .then((lista) => setDocs(lista))
      .catch(() => {});
  }, [id]);

  async function handleSubir(archivos: File[]) {
    if (!id) return;
    setError("");
    setSubiendo(true);
    try {
      const resultado = await subirDocumentos(id, archivos);
      setDocs((prev) => [...prev, ...resultado]);
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Error al subir");
    } finally {
      setSubiendo(false);
    }
  }

  async function handleExtraer() {
    if (!id) return;
    setError("");
    try {
      const { trabajo_id } = await lanzarExtraccion(id);
      setTrabajoId(trabajo_id);
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Error al extraer");
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <nav className="flex gap-4 text-sm mb-6 border-b pb-2">
        <span className="font-semibold text-blue-600 border-b-2 border-blue-600 pb-2">
          Documentos
        </span>
        <button onClick={() => navigate(`/casos/${id}/ficha`)} className="text-gray-500 hover:text-gray-700 pb-2">
          Ficha
        </button>
        <button onClick={() => navigate(`/casos/${id}/propuesta`)} className="text-gray-500 hover:text-gray-700 pb-2">
          Propuesta
        </button>
      </nav>

      <h1 className="text-lg font-bold mb-4">Documentos del caso</h1>

      <CargaArchivos onSubir={handleSubir} subiendo={subiendo} />

      {error && <p className="text-red-600 text-sm mt-3">{error}</p>}

      {docs.length > 0 && (
        <div className="mt-4">
          <h2 className="text-sm font-semibold mb-2">Documentos cargados</h2>
          <ul className="space-y-1">
            {docs.map((d) => (
              <li key={d.documento_id} className="text-sm bg-white border rounded px-3 py-2">
                {d.nombre ?? d.tipo} — <span className="font-mono text-xs text-gray-500">{d.documento_id.slice(0, 8)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6">
        {!trabajoId ? (
          <button
            onClick={handleExtraer}
            disabled={docs.length === 0}
            className="bg-green-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-green-700 disabled:opacity-50 min-h-[44px]"
          >
            Extraer con IA
          </button>
        ) : (
          <EstadoTrabajo
            trabajoId={trabajoId}
            onCompletado={() => navigate(`/casos/${id}/ficha`)}
          />
        )}
      </div>

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
