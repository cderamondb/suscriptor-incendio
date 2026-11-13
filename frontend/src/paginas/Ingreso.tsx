import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, ApiErrorResponse } from "../api/cliente";

export default function Ingreso() {
  const [correo, setCorreo] = useState("");
  const [clave, setClave] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setCargando(true);
    try {
      await login(correo, clave);
      navigate("/bandeja");
    } catch (err) {
      if (err instanceof ApiErrorResponse) {
        setError(err.message);
      } else {
        setError("Error de conexión");
      }
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold text-center mb-6">
          SuscriptorIA Incendio
        </h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="correo" className="block text-sm font-medium mb-1">
              Correo
            </label>
            <input
              id="correo"
              type="email"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              required
              className="w-full border rounded px-3 py-2 text-sm"
              autoComplete="email"
            />
          </div>
          <div>
            <label htmlFor="clave" className="block text-sm font-medium mb-1">
              Contraseña
            </label>
            <input
              id="clave"
              type="password"
              value={clave}
              onChange={(e) => setClave(e.target.value)}
              required
              className="w-full border rounded px-3 py-2 text-sm"
              autoComplete="current-password"
            />
          </div>
          {error && (
            <p className="text-red-600 text-sm">{error}</p>
          )}
          <button
            type="submit"
            disabled={cargando}
            className="w-full bg-blue-600 text-white rounded py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 min-h-[44px]"
          >
            {cargando ? "Ingresando..." : "Ingresar"}
          </button>
        </form>
      </div>
    </div>
  );
}
