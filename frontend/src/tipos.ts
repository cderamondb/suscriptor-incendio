export type EstadoCaso =
  | "BORRADOR"
  | "DOCUMENTOS_CARGADOS"
  | "FICHA_EN_REVISION"
  | "FICHA_CONFIRMADA"
  | "PROPUESTA_EN_REVISION"
  | "PROPUESTA_APROBADA"
  | "COTIZADO"
  | "DECLINADO";

export type EstadoCampo = "FALTANTE" | "EXTRAIDO" | "CORREGIDO" | "CONFIRMADO";
export type NivelConfianza = "ALTA" | "MEDIA" | "BAJA";
export type TipoCobertura = "INCENDIO" | "SISMO";
export type TipoItem = "EDIFICIO" | "CONTENIDOS" | "MAQUINARIA" | "EXISTENCIAS";
export type NivelApetito = "DENTRO" | "REFERIR" | "DECLINAR";
export type TipoAlerta =
  | "CONTRADICCION"
  | "PRIMA_MINIMA_APLICADA"
  | "SIN_HISTORIAL"
  | "SINIESTRALIDAD_ALTA"
  | "DOCUMENTO_ILEGIBLE"
  | "CITA_NO_ENCONTRADA";

export interface Origen {
  documento_id: string;
  ubicacion: string;
  cita?: string;
  pagina?: number | null;
  celda?: string | null;
}

export interface Campo<T> {
  valor: T | null;
  estado: EstadoCampo;
  confianza?: NivelConfianza | null;
  origen?: Origen[];
  alternativas?: T[];
}

export interface ItemAsegurado {
  tipo: TipoItem;
  suma_asegurada: string;
}

export interface UbicacionRiesgo {
  direccion: Campo<string>;
  comuna: Campo<string>;
  region: Campo<string>;
  coordenadas: Campo<string>;
  ocupacion_codigo: Campo<string>;
  construccion_clase: Campo<string>;
  construccion_pisos: Campo<number>;
  construccion_anio: Campo<number>;
  construccion_superficie_m2: Campo<number>;
  proteccion: Campo<string>;
  items: ItemAsegurado[];
  zona_sismica: Campo<number>;
}

export interface Alerta {
  tipo: TipoAlerta;
  detalle: string;
  origen?: Origen | null;
}

export interface FichaRiesgo {
  razon_social: Campo<string>;
  rut: Campo<string>;
  actividad_declarada: Campo<string>;
  ubicaciones: UbicacionRiesgo[];
  coberturas_solicitadas: TipoCobertura[];
  deducible_uf: Campo<string>;
  siniestralidad: Campo<{
    siniestros: { fecha: string; causa: string; monto_incurrido: string }[];
    primas_pagadas: string;
  }>;
  vigencia_desde: Campo<string>;
  vigencia_hasta: Campo<string>;
  aseguradora_anterior: Campo<string>;
  prima_anterior: Campo<string>;
  inspeccion: Campo<string>;
  alertas: Alerta[];
}

export interface LineaPrima {
  ubicacion_idx: number;
  item_tipo: TipoItem;
  cobertura: TipoCobertura;
  suma_asegurada: string;
  tasa_por_mil: string;
  prima: string;
  prima_neta: string;
}

export interface PropuestaTarifa {
  version_tarifario: string;
  tasa_incendio: string;
  tasa_sismo: string;
  factor_construccion: string;
  factor_proteccion: string;
  factor_deducible: string;
  factor_siniestralidad: string;
  lineas: LineaPrima[];
  prima_tecnica: string;
  ajuste_comercial: string;
  prima_ajustada: string;
  prima_neta: string;
  iva: string;
  prima_bruta: string;
  comision: string;
  comision_corredor: string;
  alertas: Alerta[];
}

export interface ReglaActivada {
  codigo: string;
  motivo: string;
}

export interface ResultadoApetito {
  resultado: NivelApetito;
  reglas_activadas: ReglaActivada[];
}

export interface CampoFaltante {
  ruta: string;
  bloqueante: boolean;
}

export interface ReporteCompletitud {
  completo: boolean;
  faltantes: CampoFaltante[];
}

export interface CasoResumen {
  id: string;
  asegurado: string;
  rut: string;
  estado: EstadoCaso;
  corredor: string | null;
  creado: string;
}

export interface Trabajo {
  id: string;
  caso_id: string;
  tipo: string;
  estado: string;
  error_codigo: string | null;
  prompt_version: string | null;
  modelo: string | null;
  pasos: number;
  tokens_entrada: number;
  tokens_salida: number;
  tokens_cache: number;
  herramientas_usadas: string[] | null;
  respuesta: unknown;
  creado: string;
  terminado: string | null;
}

export interface FichaResponse {
  ficha: FichaRiesgo | null;
  completitud: ReporteCompletitud | null;
  tokens: { entrada: number; salida: number; cache: number };
  costo_estimado_usd: number;
}

export interface ApiError {
  error: {
    codigo: string;
    mensaje: string;
    detalle?: unknown;
  };
}
