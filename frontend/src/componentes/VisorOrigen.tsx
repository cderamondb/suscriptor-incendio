import type { Origen } from "../tipos";

interface Props {
  origen: Origen;
  onCerrar: () => void;
}

export default function VisorOrigen({ origen, onCerrar }: Props) {
  return (
    <div className="border rounded p-3 bg-gray-50 text-xs space-y-1 relative">
      <button
        onClick={onCerrar}
        className="absolute top-1 right-2 text-gray-400 hover:text-gray-700"
      >
        ✕
      </button>
      <p><span className="font-medium">Documento:</span> {origen.documento_id.slice(0, 8)}…</p>
      {origen.pagina != null && <p><span className="font-medium">Página:</span> {origen.pagina}</p>}
      {origen.celda && <p><span className="font-medium">Celda:</span> {origen.celda}</p>}
      {origen.cita && (
        <blockquote className="border-l-2 border-blue-300 pl-2 italic text-gray-600 mt-1">
          {origen.cita}
        </blockquote>
      )}
    </div>
  );
}
