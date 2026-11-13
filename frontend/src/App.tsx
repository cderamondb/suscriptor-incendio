import { Routes, Route, Navigate } from "react-router-dom";
import Ingreso from "./paginas/Ingreso";
import Bandeja from "./paginas/Bandeja";
import CasoDocumentos from "./paginas/CasoDocumentos";
import CasoFicha from "./paginas/CasoFicha";
import CasoPropuesta from "./paginas/CasoPropuesta";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Ingreso />} />
      <Route path="/bandeja" element={<Bandeja />} />
      <Route path="/casos/:id/documentos" element={<CasoDocumentos />} />
      <Route path="/casos/:id/ficha" element={<CasoFicha />} />
      <Route path="/casos/:id/propuesta" element={<CasoPropuesta />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
