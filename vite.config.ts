import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    fs: {
      // 排除 SillyTavern 目录，避免依赖扫描错误
      deny: ['**/SillyTavern/**']
    }
  },
  optimizeDeps: {
    // 排除 JSZip 等 SillyTavern 的依赖
    exclude: ['JSZip']
  }
})
