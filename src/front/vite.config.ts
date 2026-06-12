import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': resolve(__dirname, 'src') },
  },
  // En production, les assets vont dans ../src/elite_deck/web/
  // pour être servis directement par aiohttp
  build: {
    outDir: '../elite_deck/src/elite_deck/web',
    emptyOutDir: true,
  },
  server: {
    // En dev, proxy le WebSocket et l'API vers Python
    proxy: {
      '/ws':  { target: 'ws://localhost:3300',  ws: true },
      '/api': { target: 'http://localhost:3300' },
    },
  },
})
