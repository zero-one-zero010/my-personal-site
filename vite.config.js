import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  // 1. 这里放插件配置（只写一份）
  plugins: [vue()],

  // 2. 这里放服务器代理配置（把 server 写在里面）
  server: {
    proxy: {
      '/qweather-api': {
        target: 'https://devapi.qweather.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/qweather-api/, '')
      }
    }
  }
})