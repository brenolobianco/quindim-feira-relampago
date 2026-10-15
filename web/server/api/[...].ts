export default defineEventHandler((event) => {
  const caminho = getRouterParam(event, '_')
  return proxyRequest(event, `${useRuntimeConfig(event).apiUrl}/v1/${caminho}`)
})
