import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/Fashion-Agentic-AI-System_01/', // GitHub Pages 서브경로
  plugins: [react()],
  server: {
    port: 5173,
    open: true, // 브라우저 자동 열기
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

