import request from './request'

export async function getSystemStatus() {
  return await request.get('/system/status')
}

export async function getConfigSchema() {
  return await request.get('/system/config/schema')
}

export async function getAllConfigs() {
  return await request.get('/system/config')
}

export async function getCategoryConfig(category) {
  return await request.get(`/system/config/${category}`)
}

export async function updateCategoryConfig(category, configs) {
  return await request.put(`/system/config/${category}`, { configs })
}

export async function testDatabaseConnection(configs) {
  return await request.post('/system/test/database', { configs })
}

export async function testRedisConnection(configs) {
  return await request.post('/system/test/redis', { configs })
}

export async function testMilvusConnection(configs) {
  return await request.post('/system/test/milvus', { configs })
}

export async function testLlmConnection(configs) {
  return await request.post('/system/test/llm', { configs })
}

export async function initializeSystem(data) {
  return await request.post('/system/init', data)
}

export async function listLlmProviders() {
  return await request.get('/system/llm/providers')
}

export async function listProviderModels(providerName) {
  return await request.get(`/system/llm/providers/${providerName}/models`)
}

export async function getProviderDefaultConfig(providerName) {
  return await request.get(`/system/llm/providers/${providerName}/default-config`)
}

export async function fetchModelsFromApi(provider, apiKey, apiBase) {
  return await request.post('/system/llm/fetch-models', { provider, apiKey, apiBase })
}

export {
  listLlmProviders as getLLMProviders,
  testLlmConnection as testConnection,
  initializeSystem as initSystem
}
