import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/sesion": "http://localhost:8000",
      "/casos": "http://localhost:8000",
      "/documentos": "http://localhost:8000",
      "/cotizaciones": "http://localhost:8000",
      "/trabajos": "http://localhost:8000",
      "/salud": "http://localhost:8000",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
  },
});
