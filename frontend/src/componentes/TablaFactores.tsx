import { formatMonto } from "../formato";
import type { PropuestaTarifa } from "../tipos";

interface Props {
  propuesta: PropuestaTarifa;
}

export default function TablaFactores({ propuesta }: Props) {
  return (
    <div className="space-y-4 text-sm">
      <div className="grid grid-cols-2 gap-2 bg-white border rounded p-3">
        <span className="text-gray-500">Tasa incendio</span>
        <span className="text-right font-mono">{propuesta.tasa_incendio}‰</span>
        <span className="text-gray-500">Tasa sismo</span>
        <span className="text-right font-mono">{propuesta.tasa_sismo}‰</span>
        <span className="text-gray-500">Factor construcción</span>
        <span className="text-right font-mono">{propuesta.factor_construccion}</span>
        <span className="text-gray-500">Factor protección</span>
        <span className="text-right font-mono">{propuesta.factor_proteccion}</span>
        <span className="text-gray-500">Factor deducible</span>
        <span className="text-right font-mono">{propuesta.factor_deducible}</span>
        <span className="text-gray-500">Factor siniestralidad</span>
        <span className="text-right font-mono">{propuesta.factor_siniestralidad}</span>
        <span className="text-gray-500">Ajuste comercial</span>
        <span className="text-right font-mono">{propuesta.ajuste_comercial}</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border">
          <thead>
            <tr className="bg-gray-50 text-left">
              <th className="px-2 py-1 border-b">Ubicación</th>
              <th className="px-2 py-1 border-b">Ítem</th>
              <th className="px-2 py-1 border-b">Cobertura</th>
              <th className="px-2 py-1 border-b text-right">Suma (UF)</th>
              <th className="px-2 py-1 border-b text-right">Prima neta (UF)</th>
            </tr>
          </thead>
          <tbody>
            {propuesta.lineas.map((l, i) => (
              <tr key={i} className="border-b">
                <td className="px-2 py-1">{l.ubicacion_idx + 1}</td>
                <td className="px-2 py-1">{l.item_tipo}</td>
                <td className="px-2 py-1">{l.cobertura}</td>
                <td className="px-2 py-1 text-right font-mono">{formatMonto(l.suma_asegurada)}</td>
                <td className="px-2 py-1 text-right font-mono">{formatMonto(l.prima_neta)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white border rounded p-3 space-y-1">
        <div className="flex justify-between">
          <span className="text-gray-500">Prima técnica</span>
          <span className="font-mono">{formatMonto(propuesta.prima_tecnica)} UF</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Prima neta</span>
          <span className="font-mono">{formatMonto(propuesta.prima_neta)} UF</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">IVA</span>
          <span className="font-mono">{formatMonto(propuesta.iva)} UF</span>
        </div>
        <div className="flex justify-between font-semibold">
          <span>Prima bruta</span>
          <span className="font-mono">{formatMonto(propuesta.prima_bruta)} UF</span>
        </div>
        <div className="flex justify-between text-gray-500">
          <span>Comisión corredor</span>
          <span className="font-mono">{formatMonto(propuesta.comision_corredor)} UF</span>
        </div>
      </div>
    </div>
  );
}
