// vite.config.js
import { defineConfig } from 'vite';
import legacy from '@vitejs/plugin-legacy';
import { resolve } from 'path';

export default defineConfig({
  plugins: [
    legacy({
      targets: ['defaults', 'not IE 11'], // Support modern browsers
    }),
  ],
  root: 'static', // Set the root to the 'static' directory
  publicDir: false, // Disable the default public directory since we're using 'static'
  build: {
    outDir: resolve(__dirname, 'static/dist'), // Output to Django's static directory
    emptyOutDir: true, // Clear the output directory before building
    assetsDir: '', // Place assets directly in outDir
    manifest: 'manifest.json', // Generate a manifest.json file for django-vite
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'static/js/main.js'),
        config: resolve(__dirname, 'static/js/config.js'),
        messages: resolve(__dirname, 'static/js/messages.js'),
        carousel: resolve(__dirname, 'static/js/carousel.js'),
        feed: resolve(__dirname, 'static/js/feed.js'),
        follow: resolve(__dirname, 'static/js/follow.js'),
        footballEvents: resolve(__dirname, 'static/js/football-events.js'),
        golfEvents: resolve(__dirname, 'static/js/golf-events.js'),
        horseRacingEvents: resolve(__dirname, 'static/js/horse-racing-events.js'),
        nav: resolve(__dirname, 'static/js/nav.js'),
        post: resolve(__dirname, 'static/js/post.js'),
        profile: resolve(__dirname, 'static/js/profile.js'),
        scripts: resolve(__dirname, 'static/js/scripts.js'),
        tennisEvents: resolve(__dirname, 'static/js/tennis-events.js'),
        tips: resolve(__dirname, 'static/js/tips.js'),
        trendingTips: resolve(__dirname, 'static/js/trending-tips.js'),
        upcomingEvents: resolve(__dirname, 'static/js/upcoming-events.js'),
        utils: resolve(__dirname, 'static/js/utils.js'),
      },
      output: {
        entryFileNames: '[name]-[hash].js', // Include hash for cache busting
        chunkFileNames: '[name]-[hash].js',
        assetFileNames: '[name]-[hash].[ext]',
      },
    },
  },
  server: {
    port: 3000, // Match the port in DJANGO_VITE settings
    host: 'localhost', // Ensure Vite binds to localhost
    strictPort: true, // Fail if the port is already in use
    watch: {
      usePolling: true, // Useful for some environments (e.g., Docker, WSL)
    },
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 3000,
    },
  },
});