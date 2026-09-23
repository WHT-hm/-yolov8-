<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="never" class="profile-card">
          <div class="avatar" :style="{ background: avatarColor }">
            {{ avatarLetter }}
          </div>
          <div class="profile-name">{{ user?.username }}</div>
          <div class="profile-email">{{ user?.email }}</div>
          <div class="profile-joined">注册于 {{ formatDate(user?.created_at) }}</div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="never" class="panel-card">
          <h3 class="panel-title">基本信息</h3>
          <el-form :model="profileForm" label-width="90px">
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" />
            </el-form-item>
            <el-button type="primary" :loading="savingProfile" @click="saveProfile">
              保存修改
            </el-button>
          </el-form>
        </el-card>

        <el-card shadow="never" class="panel-card">
          <h3 class="panel-title">修改密码</h3>
          <el-form :model="pwdForm" label-width="90px">
            <el-form-item label="原密码">
              <el-input v-model="pwdForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="pwdForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input v-model="pwdForm.confirm" type="password" show-password />
            </el-form-item>
            <el-button type="primary" :loading="savingPwd" @click="savePassword">
              修改密码
            </el-button>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { changePassword, updateCurrentUser } from '../api/auth'
import { authStore } from '../store/auth'

const user = computed(() => authStore.state.user)

const profileForm = reactive({ username: '', email: '' })
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })

const savingProfile = ref(false)
const savingPwd = ref(false)

const avatarLetter = computed(() => (user.value?.username || '?').charAt(0).toUpperCase())
const avatarColor = computed(() => 'var(--el-color-primary)')

function formatDate(iso) {
  if (!iso) return '--'
  return new Date(iso).toLocaleDateString('zh-CN')
}

async function saveProfile() {
  if (!profileForm.username || !profileForm.email) {
    ElMessage.warning('用户名和邮箱不能为空')
    return
  }
  savingProfile.value = true
  try {
    const updated = await updateCurrentUser({
      username: profileForm.username,
      email: profileForm.email,
    })
    authStore.state.user = updated
    localStorage.setItem('pw_user', JSON.stringify(updated))
    ElMessage.success('个人信息已更新')
  } catch {
    // 错误提示已由 axios 拦截器统一处理
  } finally {
    savingProfile.value = false
  }
}

async function savePassword() {
  if (!pwdForm.old_password || !pwdForm.new_password) {
    ElMessage.warning('请填写原密码和新密码')
    return
  }
  if (pwdForm.new_password.length < 6) {
    ElMessage.warning('新密码长度至少为 6 位')
    return
  }
  if (pwdForm.new_password !== pwdForm.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  savingPwd.value = true
  try {
    await changePassword({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功')
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm = ''
  } catch {
    // 错误提示已由 axios 拦截器统一处理
  } finally {
    savingPwd.value = false
  }
}

onMounted(() => {
  if (user.value) {
    profileForm.username = user.value.username
    profileForm.email = user.value.email
  }
})
</script>

<style scoped>
.profile-card {
  text-align: center;
  padding: 24px 0;
}
.avatar {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 700;
  color: #fff;
}
.profile-name {
  font-size: 18px;
  font-weight: 700;
  color: #1b2a38;
}
.profile-email {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.profile-joined {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 8px;
}
.panel-card {
  margin-bottom: 20px;
}
.panel-title {
  font-size: 15px;
  color: #1b2a38;
  margin: 0 0 16px;
  padding-left: 10px;
  border-left: 4px solid var(--el-color-primary);
}
</style>
