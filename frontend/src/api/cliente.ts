import type {
  CasoResumen,
  FichaResponse,
  PropuestaTarifa,
  ResultadoApetito,
  Trabajo,
} from "../tipos";

class ApiErrorResponse extends Error {
  codigo: string;
  detalle?: unknown;
  constructor(codigo: string, mensaje: string, detalle?: unknown) {
    super(mensaje);
    this.codigo = codigo;
    this.detalle = detalle;
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    credentials: "include",
    headers: {
      ...(init?.headers ?? {}),
      ...(!init?.body || init.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
    },
  });
  if (!res.ok) {
    let body: { error?: { codigo?: string; mensaje?: string; detalle?: unknown } } = {};
    try {
      body = await res.json();
    } catch {
      /* vacío */
    }
    const err = body?.error;
    throw new ApiErrorResponse(
      err?.codigo ?? `HTTP_${res.status}`,
      err?.mensaje ?? res.statusText,
      err?.detalle,
    );
  }
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) return res.json();
  return undefined as T;
}

export { ApiErrorResponse };

export async function login(correo: string, clave: string) {
  return request<{ usuario_id: number; correo: string; rol: string }>(
    "/sesion",
    { method: "POST", body: JSON.stringify({ correo, clave }) },
  );
}

export async function logout() {
  return request<void>("/sesion", { method: "DELETE" });
}

export async function crearCaso(data: {
  asegurado: string;
  rut: string;
  corredor?: string;
}) {
  return request<{ caso_id: string }>("/casos", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listarCasos(params?: {
  estado?: string;
  corredor?: string;
  offset?: number;
  limit?: number;
}) {
  const qs = new URLSearchParams();
  if (params?.estado) qs.set("estado", params.estado);
  if (params?.corredor) qs.set("corredor", params.corredor);
  if (params?.offset != null) qs.set("offset", String(params.offset));
  if (params?.limit != null) qs.set("limit", String(params.limit));
  const q = qs.toString();
  return request<CasoResumen[]>(`/casos${q ? `?${q}` : ""}`);
}

export async function subirDocumentos(casoId: string, archivos: File[]) {
  const form = new FormData();
  archivos.forEach((f) => form.append("archivos", f));
  return request<{ documento_id: string; tipo: string; estado: string }[]>(
    `/casos/${casoId}/documentos`,
    { method: "POST", body: form },
  );
}

export async function lanzarExtraccion(casoId: string) {
  return request<{ trabajo_id: string }>(`/casos/${casoId}/extraccion`, {
    method: "POST",
  });
}

export async function obtenerFicha(casoId: string) {
  return request<FichaResponse>(`/casos/${casoId}/ficha`);
}

export async function corregirFicha(
  casoId: string,
  campo: string,
  valor: unknown,
  motivo?: string,
) {
  return request<{ ficha: unknown }>(`/casos/${casoId}/ficha`, {
    method: "PATCH",
    body: JSON.stringify({ campo, valor, motivo }),
  });
}

export async function confirmarFicha(casoId: string) {
  return request<{ estado: string }>(`/casos/${casoId}/ficha/confirmacion`, {
    method: "POST",
  });
}

export async function obtenerAnalisis(casoId: string) {
  return request<{
    apetito: ResultadoApetito;
    comparables: unknown[];
  }>(`/casos/${casoId}/analisis`);
}

export async function crearPropuesta(
  casoId: string,
  ajusteComercial: string = "0",
) {
  return request<{ version: number; propuesta: PropuestaTarifa }>(
    `/casos/${casoId}/propuestas`,
    { method: "POST", body: JSON.stringify({ ajuste_comercial: ajusteComercial }) },
  );
}

export async function decidirPropuesta(
  casoId: string,
  version: number,
  decision: "aprobar" | "rechazar",
  comentario: string = "",
) {
  return request<{ estado: string; version: number }>(
    `/casos/${casoId}/propuestas/${version}/decision`,
    { method: "POST", body: JSON.stringify({ decision, comentario }) },
  );
}

export async function crearCotizacion(casoId: string, propuestaVersion: number) {
  return request<{ cotizacion_id: string; numero: number }>(
    `/casos/${casoId}/cotizaciones`,
    { method: "POST", body: JSON.stringify({ propuesta_version: propuestaVersion }) },
  );
}

export function urlPdf(cotizacionId: string) {
  return `/cotizaciones/${cotizacionId}/pdf`;
}

export async function enviarMensajeAgente(casoId: string, mensaje: string) {
  return request<{ trabajo_id: string }>(`/casos/${casoId}/agente`, {
    method: "POST",
    body: JSON.stringify({ mensaje }),
  });
}

export async function obtenerTrabajo(trabajoId: string) {
  return request<Trabajo>(`/trabajos/${trabajoId}`);
}
