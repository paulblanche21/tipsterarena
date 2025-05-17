// vite.config.mjs
import { defineConfig } from 'vite';
import { resolve } from 'path';

console.log('Vite config loaded with port 3000');

export default defineConfig({
  build: {
    outDir: 'static/dist',
    manifest: true,
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    rollupOptions: {
      input: {
        main: 'static/js/main.js',
        styles: 'static/css/styles.css',
        base: 'static/css/base.css',
        responsive: 'static/css/responsive.css',
        sidebar: 'static/css/sidebar.css',
        navbar: 'static/css/navbar.css',
        chat: 'static/css/chat.css',
        tip: 'static/css/tip.css',
        notification: 'static/css/notification.css',
        modal: 'static/css/modal.css',
        post: 'static/css/post.css',
        landing: 'static/css/landing.css',
        premium: 'static/css/premium.css',
        follow: 'static/css/follow.css',
        profile: 'static/css/profile.css',
        messages: 'static/css/messages.css',
        bookmarks: 'static/css/bookmarks.css',
        avatar: 'static/css/avatar.css',
        misc: 'static/css/misc.css'
      },
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
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
      ignored: ['**/venv/**', '**/*.py', '**/site-packages/**'],
    },
  },
  css: {
    devSourcemap: false,
    minify: true,
  },
  optimizeDeps: {
    include: [
      'static/js/main.js',
      'static/js/notifications.js',
      'static/js/tips.js',
      'static/js/follow.js',
      'static/js/config.js',
      'static/js/mobile-header.js'
    ]
  }
});