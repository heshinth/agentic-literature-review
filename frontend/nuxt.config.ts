// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  runtimeConfig: {
    public: {
      apiBaseUrl:
        import.meta.env.NUXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
    },
  },
});
