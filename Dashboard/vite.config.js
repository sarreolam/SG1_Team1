import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/SG1_Team1/',
  build: {
    outDir: '../docs',
    emptyOutDir: true,
  },
})