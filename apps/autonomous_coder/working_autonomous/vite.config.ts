import { defineConfig } from 'vite'
import { resolve } from 'path'

// Vite 7 configuration
export default defineConfig({
  root: '.',
  build: {
    target: 'esnext', // Modern browsers only
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html')
      }
    }
  },
  server: {
    port: 5173,
    open: true
  },
  css: {
    modules: {
      localsConvention: 'camelCase'
    }
  }
})
