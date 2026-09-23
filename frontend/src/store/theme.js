import { reactive } from 'vue'
import { updateSettings } from '../api/settings'
import { authStore } from './auth'

export const THEMES = [
  { key: 'forest', label: '森林绿', color: '#1f9d6b' },
  { key: 'ocean', label: '海洋蓝', color: '#2f7de1' },
  { key: 'purple', label: '皇家紫', color: '#7c5cff' },
  { key: 'sunset', label: '日落橙', color: '#ff7a45' },
]

const state = reactive({
  current: localStorage.getItem('pw_theme') || 'forest',
})

function applyThemeToDom(name) {
  document.documentElement.setAttribute('data-theme', name)
}

async function setTheme(name, { sync = true } = {}) {
  state.current = name
  localStorage.setItem('pw_theme', name)
  applyThemeToDom(name)
  if (sync && authStore.isLoggedIn.value) {
    try {
      await updateSettings({ theme: name })
    } catch {
      // 未登录或网络异常时静默失败，主题已在本地生效
    }
  }
}

function initTheme() {
  applyThemeToDom(state.current)
}

export const themeStore = {
  state,
  setTheme,
  initTheme,
}
