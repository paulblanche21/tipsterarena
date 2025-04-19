// vite.config.mjs
import { defineConfig } from 'vite';
import legacy from '@vitejs/plugin-legacy';
import { djangoVitePlugin } from 'django-vite-plugin';
import path from 'path';

console.log('Vite config loaded with port 3000');

export default defineConfig({
  plugins: [
    djangoVitePlugin({
      pythonExecutable: '/Users/paulblanche/Desktop/Tipster Arena/venv/bin/python3',
      settingsModule: 'tipsterarena.settings',
    }),
    legacy(),
  ],
  build: {
    outDir: 'static/dist',
    manifest: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'static/js/main.js'),
        styles: path.resolve(__dirname, 'static/css/styles.css'),
        tips: path.resolve(__dirname, 'static/js/pages/tips.js'),
        upcoming_events: path.resolve(__dirname, 'static/js/pages/upcoming-events.js'),
        config: path.resolve(__dirname, 'static/js/config.js'),
      },
      output: {
        entryFileNames: '[name]-[hash].js',
        chunkFileNames: '[name]-[hash].js',
        assetFileNames: '[name]-[hash].[ext]',
      },
    },
    css: {
      minify: true,
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
      ignored: ['**/venv/**', '**/*.py', '**/site-packages/**'],
    },
  },
  css: {
    devSourcemap: true,
  },
});