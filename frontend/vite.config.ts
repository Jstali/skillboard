import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Allow external connections
    port: 5173,
    strictPort: false,
    hmr: {
      clientPort: 5173, // Use the same port for HMR WebSocket
    },
    watch: {
      usePolling: true, // Enable polling for file changes in Docker
    },
    proxy: {
      '/api': {
        // Use Docker service name 'backend' for container-to-container communication
        // Falls back to localhost for local development outside Docker
        target: 'http://backend:2608',
        changeOrigin: true,
        secure: false,
        ws: true, // Enable WebSocket proxy
      },
    },
  },
})

