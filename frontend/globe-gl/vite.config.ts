import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // globe.gl は CommonJS 形式のため最適化から除外
  optimizeDeps: {
    exclude: ['globe.gl'],
  },
  build: {
    // 大きなチャンクの警告を抑制（globe.gl + three.js は合計~1MB）
    chunkSizeWarningLimit: 2000,
  },
})
