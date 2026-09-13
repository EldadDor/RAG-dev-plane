import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  root: 'apps/rag-dev-plane',
  plugins: [react()],
  build: {
    outDir: '../../build/dist/rag-dev-plane',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/workspaces': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
