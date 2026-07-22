import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The frontend calls /api/runs; Vite proxies that to the FastAPI service on
// :8000 and strips the /api prefix, so the backend just sees /runs.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
