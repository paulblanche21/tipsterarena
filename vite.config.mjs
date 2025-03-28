// vite.config.mjs
import { defineConfig } from 'vite';

console.log('Vite config loaded with port 3000');

export default defineConfig({
  build: {
    outDir: 'static/dist', // Output to static/dist relative to root
    manifest: true,
    rollupOptions: {
      input: {
        main: 'static/js/main.js', // Correct relative to root
        styles: 'static/css/styles.css', // Correct relative to root
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
    watch: {
      ignored: ['**/venv/**', '**/*.py', '**/site-packages/**'], // Ignore virtualenv and Python files
    },
  },
});