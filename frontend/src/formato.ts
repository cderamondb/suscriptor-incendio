export function formatMonto(valor: string | number): string {
  const num = typeof valor === "string" ? parseFloat(valor) : valor;
  if (isNaN(num)) return String(valor);
  const partes = num.toFixed(2).split(".");
  const entero = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${entero},${partes[1]}`;
}

export function formatFecha(iso: string): string {
  if (!iso) return "";
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}-${m}-${y}`;
}

const ESTADO_LABELS: Record<string, string> = {
  BORRADOR: "Borrador",
  DOCUMENTOS_CARGADOS: "Docs cargados",
  FICHA_EN_REVISION: "Ficha en revisión",
  FICHA_CONFIRMADA: "Ficha confirmada",
  PROPUESTA_EN_REVISION: "Propuesta en revisión",
  PROPUESTA_APROBADA: "Propuesta aprobada",
  COTIZADO: "Cotizado",
  DECLINADO: "Declinado",
};

export function estadoLabel(estado: string): string {
  return ESTADO_LABELS[estado] ?? estado;
}

const ESTADO_COLORES: Record<string, string> = {
  BORRADOR: "bg-gray-200 text-gray-700",
  DOCUMENTOS_CARGADOS: "bg-blue-100 text-blue-700",
  FICHA_EN_REVISION: "bg-yellow-100 text-yellow-700",
  FICHA_CONFIRMADA: "bg-green-100 text-green-700",
  PROPUESTA_EN_REVISION: "bg-orange-100 text-orange-700",
  PROPUESTA_APROBADA: "bg-emerald-100 text-emerald-700",
  COTIZADO: "bg-indigo-100 text-indigo-700",
  DECLINADO: "bg-red-100 text-red-700",
};

export function estadoColor(estado: string): string {
  return ESTADO_COLORES[estado] ?? "bg-gray-200 text-gray-700";
}
