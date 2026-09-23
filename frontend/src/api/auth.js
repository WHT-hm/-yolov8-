import request from './request'

export function registerUser(data) {
  return request.post('/auth/register', data)
}

export function loginUser(data) {
  return request.post('/auth/login', data)
}

export function fetchCurrentUser() {
  return request.get('/auth/me')
}

export function updateCurrentUser(data) {
  return request.put('/auth/me', data)
}

export function changePassword(data) {
  return request.post('/auth/change-password', data)
}
