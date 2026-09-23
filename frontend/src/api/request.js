import axios from 'axios'
import { ElMessage } from 'element-plus'
import { authStore } from '../store/auth'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

request.interceptors.request.use((config) => {
  if (authStore.state.token) {
    config.headers.Authorization = `Bearer ${authStore.state.token}`
  }
  return config
})

request.interceptors.response.use(
  (res) => res.data,
  (err) => {
    if (err.response?.status === 401) {
      authStore.logout()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    const msg = err.response?.data?.detail || err.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default request
