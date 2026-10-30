import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    manifest: true,
    rollupOptions: {
      output: {
        // Keep the initial entry small by separating the always-loaded vendor
        // groups. Lazy feature chunks (mermaid/ELK/vis-network) keep their own
        // dynamic chunks; see scripts/check-bundle.mjs for the guard.
        manualChunks(id) {
          if (/[\\/]node_modules[\\/](vue|@vue|pinia|vue-router|vue-i18n|@intlify)[\\/]/.test(id)) {
            return 'vendor-vue'
          }
          if (
            /[\\/]node_modules[\\/](axios|socket\.io-client|engine\.io-client|engine\.io-parser|socket\.io-parser|@socket\.io)[\\/]/.test(
              id,
            )
          ) {
            return 'vendor-realtime'
          }
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
      '/mock-api': {
        // Overridable so e2e can target a dedicated mock-api instance
        // instead of the demo server on 8001 (docker compose).
        target: process.env.MOCK_API_TARGET || 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/mock-api/, ''),
      },
    },
  },
})
