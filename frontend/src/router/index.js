import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'
import { authStore } from '../store/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('../views/Home.vue'),
        meta: { title: '首页', accent: '--accent-home' },
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '数据统计仪表盘', accent: '--accent-dashboard' },
      },
      {
        path: 'detection',
        name: 'Detection',
        component: () => import('../views/Detection.vue'),
        meta: { title: '病虫害检测', accent: '--accent-detection' },
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('../views/History.vue'),
        meta: { title: '检测历史记录', accent: '--accent-history' },
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../views/PestKnowledge.vue'),
        meta: { title: '病虫害知识库', accent: '--accent-knowledge' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { title: '个人中心', accent: '--accent-dashboard' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue'),
        meta: { title: '设置', accent: '--accent-history' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const loggedIn = authStore.isLoggedIn.value
  if (!to.meta.public && !loggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login' && loggedIn) {
    return { path: '/home' }
  }
  return true
})

export default router
