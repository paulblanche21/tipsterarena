// vite.config.mjs
import { defineConfig } from 'vite';
import { resolve } from 'path';
import autoprefixer from 'autoprefixer';

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
        main: resolve(__dirname, 'static/js/main.js'),
        styles: resolve(__dirname, 'static/css/styles.css'),
        base: resolve(__dirname, 'static/css/base.css'),
        responsive: resolve(__dirname, 'static/css/responsive.css'),
        sidebar: resolve(__dirname, 'static/css/sidebar.css'),
        navbar: resolve(__dirname, 'static/css/navbar.css'),
        chat: resolve(__dirname, 'static/css/chat.css'),
        tip: resolve(__dirname, 'static/css/tip.css'),
        notification: resolve(__dirname, 'static/css/notification.css'),
        modal: resolve(__dirname, 'static/css/modal.css'),
        post: resolve(__dirname, 'static/css/post.css'),
        landing: resolve(__dirname, 'static/css/landing.css'),
        premium: resolve(__dirname, 'static/css/premium.css'),
        follow: resolve(__dirname, 'static/css/follow.css'),
        profile: resolve(__dirname, 'static/css/profile.css'),
        messages: resolve(__dirname, 'static/css/messages.css'),
        bookmarks: resolve(__dirname, 'static/css/bookmarks.css'),
        avatar: resolve(__dirname, 'static/css/avatar.css'),
        misc: resolve(__dirname, 'static/css/misc.css')
      },
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name.endsWith('.css')) {
            return 'assets/css/[name]-[hash][extname]';
          }
          return 'assets/[name]-[hash][extname]';
        },
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    hmr: {
      protocol: 'ws',
      host: '0.0.0.0',
      port: 3000,
      clientPort: 3000
    },
    watch: {
      ignored: ['**/venv/**', '**/*.py', '**/site-packages/**'],
    },
    cors: true,
    origin: 'http://localhost:3000',
  },
  css: {
    devSourcemap: true,
    modules: false,
    postcss: {
      plugins: [
        autoprefixer()
      ]
    }
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
  },
  base: ''
});