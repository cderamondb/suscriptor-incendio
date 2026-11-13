import { useRef, useState } from "react";

interface Props {
  onSubir: (archivos: File[]) => void;
  subiendo: boolean;
}

const TIPOS_ACEPTADOS = ".pdf,.xlsx,.xls,.jpg,.jpeg,.png";

export default function CargaArchivos({ onSubir, subiendo }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [arrastrando, setArrastrando] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const archivos = Array.from(e.target.files ?? []);
    if (archivos.length > 0) onSubir(archivos);
    if (inputRef.current) inputRef.current.value = "";
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setArrastrando(false);
    const archivos = Array.from(e.dataTransfer.files);
    if (archivos.length > 0) onSubir(archivos);
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setArrastrando(true); }}
      onDragLeave={() => setArrastrando(false)}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
        arrastrando ? "border-blue-400 bg-blue-50" : "border-gray-300"
      }`}
    >
      <p className="text-sm text-gray-600 mb-3">
        Arrastre archivos aquí o seleccione
      </p>
      <input
        ref={inputRef}
        type="file"
        accept={TIPOS_ACEPTADOS}
        multiple
        capture="environment"
        onChange={handleChange}
        className="hidden"
        id="carga-archivos"
      />
      <label
        htmlFor="carga-archivos"
        className={`inline-block bg-blue-600 text-white rounded px-4 py-2 text-sm font-medium cursor-pointer hover:bg-blue-700 min-h-[44px] leading-[28px] ${
          subiendo ? "opacity-50 pointer-events-none" : ""
        }`}
      >
        {subiendo ? "Subiendo..." : "Seleccionar archivos"}
      </label>
      <p className="text-xs text-gray-400 mt-2">PDF, Excel, JPG, PNG</p>
    </div>
  );
}
