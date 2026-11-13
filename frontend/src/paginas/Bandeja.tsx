import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listarCasos, crearCaso, logout, ApiErrorResponse } from "../api/cliente";
import { estadoLabel, estadoColor, formatFecha } from "../formato";
import type { CasoResumen } from "../tipos";

export default function Bandeja() {
  const [casos, setCasos] = useState<CasoResumen[]>([]);
  const [error, setError] = useState("");
  const [mostrarNuevo, setMostrarNuevo] = useState(false);
  const [asegurado, setAsegurado] = useState("");
  const [rut, setRut] = useState("");
  const [corredor, setCorredor] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    listarCasos()
      .then(setCasos)
      .catch((err) => {
        if (err instanceof ApiErrorResponse && err.codigo === "HTTP_401") {
          navigate("/");
        } else {
          setError("Error al cargar casos");
        }
      });
  }, [navigate]);

  async function handleCrear(e: React.FormEvent) {
    e.preventDefault();
    try {
      const { caso_id } = await crearCaso({
        asegurado,
        rut,
        corredor: corredor || undefined,
      });
      navigate(`/casos/${caso_id}/documentos`);
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Error al crear caso");
    }
  }

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Bandeja de casos</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setMostrarNuevo(true)}
            className="bg-blue-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-blue-700 min-h-[44px]"
          >
            Nuevo caso
          </button>
          <button
            onClick={handleLogout}
            className="border rounded px-4 py-2 text-sm hover:bg-gray-100 min-h-[44px]"
          >
            Salir
          </button>
        </div>
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {mostrarNuevo && (
        <form onSubmit={handleCrear} className="border rounded p-4 mb-6 space-y-3 bg-white">
          <h2 className="font-semibold text-sm">Nuevo caso</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <input
              placeholder="Asegurado"
              value={asegurado}
              onChange={(e) => setAsegurado(e.target.value)}
              required
              className="border rounded px-3 py-2 text-sm"
            />
            <input
              placeholder="RUT"
              value={rut}
              onChange={(e) => setRut(e.target.value)}
              required
              className="border rounded px-3 py-2 text-sm"
            />
            <input
              placeholder="Corredor (opcional)"
              value={corredor}
              onChange={(e) => setCorredor(e.target.value)}
              className="border rounded px-3 py-2 text-sm"
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              className="bg-blue-600 text-white rounded px-4 py-2 text-sm min-h-[44px]"
            >
              Crear
            </button>
            <button
              type="button"
              onClick={() => setMostrarNuevo(false)}
              className="border rounded px-4 py-2 text-sm min-h-[44px]"
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2 pr-4">Asegurado</th>
              <th className="py-2 pr-4">RUT</th>
              <th className="py-2 pr-4">Estado</th>
              <th className="py-2 pr-4">Corredor</th>
              <th className="py-2">Fecha</th>
            </tr>
          </thead>
          <tbody>
            {casos.map((c) => (
              <tr
                key={c.id}
                onClick={() => navigate(`/casos/${c.id}/documentos`)}
                className="border-b hover:bg-gray-50 cursor-pointer"
              >
                <td className="py-2 pr-4">{c.asegurado}</td>
                <td className="py-2 pr-4 font-mono text-xs">{c.rut}</td>
                <td className="py-2 pr-4">
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${estadoColor(c.estado)}`}>
                    {estadoLabel(c.estado)}
                  </span>
                </td>
                <td className="py-2 pr-4">{c.corredor ?? "—"}</td>
                <td className="py-2">{formatFecha(c.creado?.slice(0, 10) ?? "")}</td>
              </tr>
            ))}
            {casos.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-gray-500">
                  Sin casos
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
