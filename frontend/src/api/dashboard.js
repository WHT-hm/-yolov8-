import request from './request'

export function getDashboardStats() {
  return request.get('/dashboard/stats')
}

export function getRiskAlert() {
  return request.get('/dashboard/risk-alert')
}
