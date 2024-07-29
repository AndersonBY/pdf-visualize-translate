/**
 * @Author: Bi Ying
 * @Date:   2024-07-22 22:59:16
 * @Last Modified by:   Bi Ying
 * @Last Modified time: 2024-07-29 12:06:29
 */
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const defaultConfig = {
  plugins: [vue({
    script: {
      defineModel: true
    }
  })],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // 'pdfjs-dist': fileURLToPath(new URL('node_modules/pdfjs-dist/build/pdf.mjs', import.meta.url)),
      // 'pdfjs-worker': fileURLToPath(new URL('node_modules/pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url)),
    }
  },
  optimizeDeps: {
    include: [
      'ant-design-vue',
      'pdfjs-dist',
      'pdfjs-dist/build/pdf.worker.mjs',
    ],
  },
  // build: {
  //   rollupOptions: {
  //     output: {
  //       manualChunks: {
  //         pdfjsWorker: ['pdfjs-dist/build/pdf.worker.min.mjs'],
  //       },
  //     },
  //   },
  // },
}

export default defineConfig(({ command, mode, ssrBuild }) => {
  if (command == 'serve') {
    return {
      ...defaultConfig,
      server: {
        proxy: {
          '/api': {
            target: `http://127.0.0.1:5000/api`,
            ws: true,
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/api/, ""),
          },
          '/static': {
            target: `http://127.0.0.1:5000/static`,
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/static/, ""),
          },
        }
      },
    }
  } else {
    return {
      ...defaultConfig,
      base: '/static/',
    }
  }
});