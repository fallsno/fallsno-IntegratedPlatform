import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    strictPort: false,
    proxy: {
      // 监测服务专用 API 路由 (必须在 /api 之前)
      '/api/config': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/api/control': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/api/data': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/api/monitor': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/api/clients': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/api/data_records': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/api/download': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // 版本管理后端 API (端口 8000)
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/lab-api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/lab-api/, '/api'),
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/monitor': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
        ws: true,  // 关键：启用 WebSocket 代理
        rewrite: (path) => path.replace(/^\/monitor/, ''),   // 关键：去掉 /monitor 前缀
      },
      '/socket.io': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
        ws: true,  // 关键：启用 WebSocket 代理
      },
      '/tools': {
        target: 'http://127.0.0.1:5002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/tools/, ''),     // Streamlit 不需要子路径
      },
      // 监测服务的静态文件
      '/static': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      }
    },
  },
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 1500, // 提高警告阈值到 1.5MB
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // 将 Element Plus 单独打包
            if (id.includes('element-plus')) {
              return 'vendor-element-plus';
            }
            // 将 Vue 及其核心生态单独打包
            if (id.includes('vue') || id.includes('@vue') || id.includes('vue-router') || id.includes('pinia')) {
              return 'vendor-vue';
            }
            // 将图表库、流程图等大型库单独打包
            if (id.includes('echarts') || id.includes('zrender')) {
              return 'vendor-echarts';
            }
            if (id.includes('mathjs')) {
              return 'vendor-mathjs';
            }
            if (id.includes('x6') || id.includes('antv')) {
              return 'vendor-antv';
            }
            if (id.includes('axios')) {
              return 'vendor-axios';
            }
            // 其他第三方库打包到一个统一的 vendor chunk 中
            return 'vendor-core';
          }
        }
      }
    }
  },
})