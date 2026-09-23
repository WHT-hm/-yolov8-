import { computed, reactive } from 'vue'
import { fetchCurrentUser, loginUser, registerUser } from '../api/auth'

const state = reactive({
  token: localStorage.getItem('pw_token') || '',
  user: JSON.parse(localStorage.getItem('pw_user') || 'null'),
})

const isLoggedIn = computed(() => !!state.token)

function persist() {
  if (state.token) {
    localStorage.setItem('pw_token', state.token)
  } else {
    localStorage.removeItem('pw_token')
  }
  if (state.user) {
    localStorage.setItem('pw_user', JSON.stringify(state.user))
  } else {
    localStorage.removeItem('pw_user')
  }
}

function setSession(token, user) {
  state.token = token
  state.user = user
  persist()
}

async function login(username, password) {
  const res = await loginUser({ username, password })
  setSession(res.access_token, res.user)
  return res.user
}

async function register(username, email, password) {
  const res = await registerUser({ username, email, password })
  setSession(res.access_token, res.user)
  return res.user
}

async function fetchMe() {
  const user = await fetchCurrentUser()
  state.user = user
  persist()
  return user
}

function logout() {
  state.token = ''
  state.user = null
  persist()
}

export const authStore = {
  state,
  isLoggedIn,
  login,
  register,
  fetchMe,
  logout,
  setSession,
}
