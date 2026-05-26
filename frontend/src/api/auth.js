import request from './request'

export async function login(username, password) {
  return await request.post('/auth/token', { username, password })
}

export async function getUserInfo(token) {
  const config = token ? { headers: { Authorization: `Bearer ${token}` } } : {}
  return await request.get('/auth/me', config)
}

export async function logout() {
  return await request.post('/auth/logout')
}

export async function changePassword(oldPassword, newPassword) {
  return await request.post('/auth/change-password', { oldPassword, newPassword })
}

export async function getKeycloakLoginUrl() {
  return await request.get('/auth/keycloak/login')
}

export async function keycloakCallback(code, state) {
  return await request.post('/auth/keycloak/callback', { code, state })
}
