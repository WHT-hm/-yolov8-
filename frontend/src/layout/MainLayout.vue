<template>
  <el-container class="app-shell">
    <el-aside :width="collapsed ? '64px' : '220px'" class="app-aside">
      <div class="logo">
        <el-icon class="logo-icon"><Aim /></el-icon>
        <span v-show="!collapsed">病虫害检测系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="app-menu"
        router
        :collapse="collapsed"
        background-color="transparent"
        text-color="#c3cad8"
        active-text-color="#ffffff"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <span class="menu-icon-chip" :style="{ background: item.color }">
            <el-icon><component :is="item.icon" /></el-icon>
          </span>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-icon class="collapse-btn" :size="18" @click="collapsed = !collapsed">
            <Fold v-if="!collapsed" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item>农作物病虫害检测系统</el-breadcrumb-item>
            <el-breadcrumb-item>{{ pageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-center">
          <GlobalSearch />
        </div>
        <div class="header-right">
          <span class="header-clock">{{ clock }}</span>
          <el-dropdown trigger="click" @command="onUserCommand">
            <span class="user-chip">
              <span class="user-avatar">{{ avatarLetter }}</span>
              <span class="user-name">{{ user?.username }}</span>
              <el-icon class="user-caret"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  设置
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <div class="accent-strip" :style="{ background: accentColor }"></div>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GlobalSearch from '../components/GlobalSearch.vue'
import { authStore } from '../store/auth'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta.title || '')
const accentColor = computed(() => `var(${route.meta.accent || '--accent-home'})`)

const user = computed(() => authStore.state.user)
const avatarLetter = computed(() => (user.value?.username || '?').charAt(0).toUpperCase())

function onUserCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'settings') {
    router.push('/settings')
  } else if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

const menuItems = [
  { path: '/home', label: '首页', icon: 'HomeFilled', color: 'var(--accent-home)' },
  { path: '/dashboard', label: '数据统计仪表盘', icon: 'DataAnalysis', color: 'var(--accent-dashboard)' },
  { path: '/detection', label: '病虫害检测', icon: 'Camera', color: 'var(--accent-detection)' },
  { path: '/history', label: '检测历史记录', icon: 'Tickets', color: 'var(--accent-history)' },
  { path: '/knowledge', label: '病虫害知识库', icon: 'Reading', color: 'var(--accent-knowledge)' },
]

const collapsed = ref(false)

const clock = ref('')
let timer = null
function updateClock() {
  clock.value = new Date().toLocaleString('zh-CN', { hour12: false })
}
onMounted(() => {
  updateClock()
  timer = setInterval(updateClock, 1000)
})
onBeforeUnmount(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.app-shell {
  height: 100vh;
}
.app-aside {
  background: linear-gradient(180deg, var(--shell-navy-top) 0%, var(--shell-navy-bottom) 100%);
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
  overflow: hidden;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  white-space: nowrap;
}
.logo-icon {
  font-size: 22px;
  color: #fff;
}
.app-menu {
  border-right: none;
  flex: 1;
  padding: 8px 0;
}
.menu-icon-chip {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 6px;
  color: #fff;
  font-size: 13px;
}
.app-menu :deep(.el-menu-item) {
  margin: 2px 8px;
  border-radius: 8px;
}
.app-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.1);
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  background: #fff;
  border-bottom: 1px solid #e5e9e5;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}
.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
}
.collapse-btn {
  cursor: pointer;
  color: #606266;
}
.collapse-btn:hover {
  color: var(--el-color-primary);
}
.breadcrumb {
  font-size: 14px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}
.header-sub {
  font-size: 12px;
  color: #909399;
}
.header-clock {
  font-size: 13px;
  color: var(--el-color-primary);
  font-variant-numeric: tabular-nums;
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 10px 4px 4px;
  border-radius: 20px;
  transition: background 0.15s ease;
}
.user-chip:hover {
  background: #f2f4f7;
}
.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.user-name {
  font-size: 13px;
  color: #1b2a38;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-caret {
  font-size: 12px;
  color: #909399;
}
.accent-strip {
  height: 3px;
  transition: background 0.2s ease;
}
.app-main {
  background: #f5f7f6;
  background-image: radial-gradient(#dbe9db 1px, transparent 1px);
  background-size: 18px 18px;
  padding: 20px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
