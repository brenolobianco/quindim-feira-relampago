export default defineNuxtConfig({
  modules: ['@nuxt/ui'],
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    apiUrl: 'http://localhost:8000',
  },
  compatibilityDate: '2025-07-15',
})
