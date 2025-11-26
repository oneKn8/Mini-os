import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    host: '0.0.0.0',
    port: 3101,
    proxy: {
      '/api': {
        target: 'http://localhost:8101',
        changeOrigin: true,
      },
    },
  },
})
