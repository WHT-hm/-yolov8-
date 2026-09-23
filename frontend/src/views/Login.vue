<template>
  <div class="login-page">
    <div class="login-decor"></div>
    <el-card class="login-card" shadow="always">
      <div class="brand">
        <el-icon class="brand-icon"><Aim /></el-icon>
        <span class="brand-name">农作物病虫害检测系统</span>
      </div>

      <template v-if="mode === 'login'">
        <el-form :model="loginForm" label-position="top" @submit.prevent>
          <el-form-item label="用户名">
            <el-input v-model="loginForm.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              show-password
              @keyup.enter="onLogin"
            />
          </el-form-item>
          <el-button
            type="primary"
            class="submit-btn"
            :loading="loading"
            @click="onLogin"
          >
            登录
          </el-button>
        </el-form>
        <div class="switch-link">
          还没有账号？<a @click="mode = 'register'">立即注册</a>
        </div>
      </template>

      <template v-else>
        <el-form :model="registerForm" label-position="top" @submit.prevent>
          <el-form-item label="用户名">
            <el-input v-model="registerForm.username" placeholder="设置一个用户名" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="registerForm.email" placeholder="请输入邮箱地址" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="至少 6 位密码"
              show-password
            />
          </el-form-item>
          <el-form-item label="确认密码">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              show-password
              @keyup.enter="onRegister"
            />
          </el-form-item>
          <el-button
            type="primary"
            class="submit-btn"
            :loading="loading"
            @click="onRegister"
          >
            注册并登录
          </el-button>
        </el-form>
        <div class="switch-link">
          已有账号？<a @click="mode = 'login'">去登录</a>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Aim } from '@element-plus/icons-vue'
import { authStore } from '../store/auth'

const route = useRoute()
const router = useRouter()

const mode = ref('login')
const loading = ref(false)

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '', confirmPassword: '' })

function goAfterAuth() {
  const redirect = route.query.redirect
  router.push(typeof redirect === 'string' ? redirect : '/home')
}

async function onLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await authStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    goAfterAuth()
  } catch {
    // 错误提示已由 axios 拦截器统一处理
  } finally {
    loading.value = false
  }
}

async function onRegister() {
  if (!registerForm.username || !registerForm.email || !registerForm.password) {
    ElMessage.warning('请完整填写注册信息')
    return
  }
  if (registerForm.password.length < 6) {
    ElMessage.warning('密码长度至少为 6 位')
    return
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    await authStore.register(registerForm.username, registerForm.email, registerForm.password)
    ElMessage.success('注册成功，已自动登录')
    goAfterAuth()
  } catch {
    // 错误提示已由 axios 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: linear-gradient(120deg, var(--shell-navy-top) 0%, var(--el-color-primary-dark-2) 55%, var(--el-color-primary) 100%);
}
.login-decor {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.12) 1px, transparent 1px);
  background-size: 24px 24px;
  opacity: 0.5;
}
.login-card {
  position: relative;
  width: 380px;
  border-radius: 16px;
  padding: 8px;
}
.brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: #1b2a38;
  margin-bottom: 20px;
}
.brand-icon {
  font-size: 22px;
  color: var(--el-color-primary);
}
.submit-btn {
  width: 100%;
  margin-top: 4px;
}
.switch-link {
  margin-top: 14px;
  text-align: center;
  font-size: 12px;
  color: #909399;
}
.switch-link a {
  color: var(--el-color-primary);
  cursor: pointer;
  font-weight: 600;
}
.switch-link a:hover {
  text-decoration: underline;
}
</style>
