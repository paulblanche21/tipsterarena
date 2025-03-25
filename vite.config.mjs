// vite.config.mjs
import { defineConfig } from 'vite';

console.log('Vite config loaded with port 3000');

export default defineConfig({
  build: {
    outDir: 'static/dist',
    manifest: true,
    rollupOptions: {
      input: {
        main: 'static/js/main.js',
      },
      output: {
        entryFileNames: '[name]-[hash].js',
        chunkFileNames: '[name]-[hash].js',
        assetFileNames: '[name]-[hash].[ext]',
      },
    },
  },
  server: {
    port: 3000,
    host: 'localhost',
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 3000,
    },
  },
});