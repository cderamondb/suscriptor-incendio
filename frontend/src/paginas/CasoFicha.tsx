import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { obtenerFicha, confirmarFicha, corregirFicha, ApiErrorResponse } from "../api/cliente";
import CampoConOrigen from "../componentes/CampoConOrigen";
import { formatMonto } from "../formato";
import type { FichaResponse, Campo, UbicacionRiesgo } from "../tipos";

export default function CasoFicha() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<FichaResponse | null>(null);
  const [error, setError] = useState("");
  const [confirmando, setConfirmando] = useState(false);

  function cargar() {
    if (!id) return;
    obtenerFicha(id)
      .then(setData)
      .catch((err) => setError(err instanceof ApiErrorResponse ? err.message : "Error al cargar ficha"));
  }

  useEffect(cargar, [id]);

  async function handleConfirmar() {
    if (!id) return;
    setError("");
    setConfirmando(true);
    try {
      await confirmarFicha(id);
      navigate(`/casos/${id}/propuesta`);
    } catch (err) {
      if (err instanceof ApiErrorResponse) {
        setError(err.message);
        if (err.detalle && typeof err.detalle === "object" && "campos" in (err.detalle as Record<string, unknown>)) {
          setError(`Campos faltantes: ${(err.detalle as { campos: string[] }).campos.join(", ")}`);
        }
      } else {
        setError("Error al confirmar");
      }
    } finally {
      setConfirmando(false);
    }
  }

  async function handleCorregir(campo: string, valor: string) {
    if (!id) return;
    try {
      await corregirFicha(id, campo, valor, "Corrección manual");
      cargar();
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Error al corregir");
    }
  }

  const ficha = data?.ficha;

  function renderCampo(label: string, campo: Campo<unknown> | undefined, ruta: string) {
    if (!campo) return null;
    return (
      <CampoConOrigen
        label={label}
        campo={campo}
        onCorregir={(valor) => handleCorregir(ruta, valor)}
      />
    );
  }

  function renderUbicacion(ub: UbicacionRiesgo, idx: number) {
    return (
      <div key={idx} className="border rounded p-3 space-y-2 bg-white">
        <h3 className="font-semibold text-sm">Ubicación {idx + 1}</h3>
        {renderCampo("Dirección", ub.direccion, `ubicaciones.${idx}.direccion`)}
        {renderCampo("Comuna", ub.comuna, `ubicaciones.${idx}.comuna`)}
        {renderCampo("Región", ub.region, `ubicaciones.${idx}.region`)}
        {renderCampo("Ocupación", ub.ocupacion_codigo, `ubicaciones.${idx}.ocupacion_codigo`)}
        {renderCampo("Construcción", ub.construccion_clase, `ubicaciones.${idx}.construccion_clase`)}
        {renderCampo("Protección", ub.proteccion, `ubicaciones.${idx}.proteccion`)}
        {renderCampo("Zona sísmica", ub.zona_sismica, `ubicaciones.${idx}.zona_sismica`)}
        {ub.items.length > 0 && (
          <div className="mt-2">
            <span className="text-xs font-medium text-gray-500">Ítems asegurados:</span>
            <ul className="text-sm mt-1 space-y-1">
              {ub.items.map((item, j) => (
                <li key={j} className="flex justify-between bg-gray-50 rounded px-2 py-1">
                  <span>{item.tipo}</span>
                  <span className="font-mono">{formatMonto(item.suma_asegurada)} UF</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <nav className="flex gap-4 text-sm mb-6 border-b pb-2">
        <button onClick={() => navigate(`/casos/${id}/documentos`)} className="text-gray-500 hover:text-gray-700 pb-2">
          Documentos
        </button>
        <span className="font-semibold text-blue-600 border-b-2 border-blue-600 pb-2">
          Ficha
        </span>
        <button onClick={() => navigate(`/casos/${id}/propuesta`)} className="text-gray-500 hover:text-gray-700 pb-2">
          Propuesta
        </button>
      </nav>

      <h1 className="text-lg font-bold mb-4">Ficha de riesgo</h1>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {!ficha ? (
        <p className="text-gray-500 text-sm">No hay ficha aún. Extraiga primero los datos con IA.</p>
      ) : (
        <div className="space-y-4">
          <div className="space-y-2 bg-white border rounded p-3">
            <h2 className="font-semibold text-sm">Datos generales</h2>
            {renderCampo("Razón social", ficha.razon_social, "razon_social")}
            {renderCampo("RUT", ficha.rut, "rut")}
            {renderCampo("Actividad", ficha.actividad_declarada, "actividad_declarada")}
            {renderCampo("Deducible (UF)", ficha.deducible_uf, "deducible_uf")}
            {renderCampo("Vigencia desde", ficha.vigencia_desde, "vigencia_desde")}
            {renderCampo("Vigencia hasta", ficha.vigencia_hasta, "vigencia_hasta")}
          </div>

          <div className="space-y-2">
            <h2 className="font-semibold text-sm">Ubicaciones</h2>
            {ficha.ubicaciones.map((ub, i) => renderUbicacion(ub, i))}
          </div>

          {ficha.alertas.length > 0 && (
            <div className="border border-yellow-300 bg-yellow-50 rounded p-3">
              <h2 className="font-semibold text-sm mb-2">Alertas</h2>
              <ul className="space-y-1">
                {ficha.alertas.map((a, i) => (
                  <li key={i} className="text-sm">
                    <span className="font-medium">{a.tipo}:</span> {a.detalle}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data && (
            <div className="text-xs text-gray-500 border rounded p-3 bg-white">
              <span className="font-medium">Tokens:</span>{" "}
              entrada {data.tokens.entrada} · salida {data.tokens.salida} · cache {data.tokens.cache}
              {" · "}
              <span className="font-medium">Costo estimado:</span> USD {data.costo_estimado_usd.toFixed(4)}
            </div>
          )}

          {data?.completitud && !data.completitud.completo && (
            <div className="border border-red-300 bg-red-50 rounded p-3">
              <h2 className="font-semibold text-sm mb-1">Campos faltantes</h2>
              <ul className="text-sm space-y-0.5">
                {data.completitud.faltantes
                  .filter((f) => f.bloqueante)
                  .map((f, i) => (
                    <li key={i} className="text-red-700">⚠ {f.ruta}</li>
                  ))}
              </ul>
            </div>
          )}

          <button
            onClick={handleConfirmar}
            disabled={confirmando}
            className="bg-green-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-green-700 disabled:opacity-50 min-h-[44px]"
          >
            {confirmando ? "Confirmando..." : "Confirmar ficha"}
          </button>
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
