<template>
  <div class="settings-page">
    <el-card shadow="never" class="panel-card">
      <h3 class="panel-title">模型接口设置</h3>
      <p class="panel-desc">
        配置你自己的 AI 模型接口地址与密钥，用于后续接入真实的检测 / 对话模型。
      </p>
      <el-form :model="apiForm" label-width="110px" v-loading="loadingSettings">
        <el-form-item label="接口地址">
          <el-input v-model="apiForm.api_base_url" placeholder="例如：https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="apiForm.model_name" placeholder="例如：gpt-4o-mini" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="apiForm.api_key"
            type="password"
            show-password
            :placeholder="apiKeyPlaceholder"
          />
        </el-form-item>
        <div class="form-actions">
          <el-button @click="onTestConnection" :loading="testing">测试连接</el-button>
          <el-button type="primary" :loading="saving" @click="onSaveApi">保存设置</el-button>
        </div>
      </el-form>
    </el-card>

    <el-card shadow="never" class="panel-card">
      <h3 class="panel-title">外观设置</h3>
      <p class="panel-desc">选择一套界面配色主题，实时预览生效。</p>
      <div class="theme-swatches">
        <div
          v-for="t in THEMES"
          :key="t.key"
          class="theme-swatch"
          :class="{ active: themeStore.state.current === t.key }"
          @click="onPickTheme(t.key)"
        >
          <span class="swatch-dot" :style="{ background: t.color }"></span>
          <span class="swatch-label">{{ t.label }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, testConnection, updateSettings } from '../api/settings'
import { THEMES, themeStore } from '../store/theme'

const apiForm = reactive({ api_base_url: '', model_name: '', api_key: '' })
const apiKeyPlaceholder = ref('尚未设置')
const loadingSettings = ref(false)
const saving = ref(false)
const testing = ref(false)

async function loadSettings() {
  loadingSettings.value = true
  try {
    const s = await getSettings()
    apiForm.api_base_url = s.api_base_url || ''
    apiForm.model_name = s.model_name || ''
    apiForm.api_key = ''
    apiKeyPlaceholder.value = s.has_api_key ? `已设置：${s.api_key_masked}（留空则不修改）` : '尚未设置'
  } finally {
    loadingSettings.value = false
  }
}

async function onSaveApi() {
  saving.value = true
  try {
    const payload = {
      api_base_url: apiForm.api_base_url,
      model_name: apiForm.model_name,
    }
    if (apiForm.api_key) {
      payload.api_key = apiForm.api_key
    }
    const s = await updateSettings(payload)
    apiForm.api_key = ''
    apiKeyPlaceholder.value = s.has_api_key ? `已设置：${s.api_key_masked}（留空则不修改）` : '尚未设置'
    ElMessage.success('设置已保存')
  } catch {
    // 错误提示已由 axios 拦截器统一处理
  } finally {
    saving.value = false
  }
}

async function onTestConnection() {
  if (!apiForm.api_base_url) {
    ElMessage.warning('请先填写接口地址')
    return
  }
  testing.value = true
  try {
    const res = await testConnection({
      api_base_url: apiForm.api_base_url,
      api_key: apiForm.api_key,
      model_name: apiForm.model_name,
    })
    if (res.success) {
      ElMessage.success(res.message)
    } else {
      ElMessage.error(res.message)
    }
  } catch {
    // 错误提示已由 axios 拦截器统一处理
  } finally {
    testing.value = false
  }
}

function onPickTheme(key) {
  themeStore.setTheme(key)
}

onMounted(loadSettings)
</script>

<style scoped>
.panel-card {
  margin-bottom: 20px;
}
.panel-title {
  font-size: 15px;
  color: #1b2a38;
  margin: 0 0 6px;
  padding-left: 10px;
  border-left: 4px solid var(--el-color-primary);
}
.panel-desc {
  font-size: 12px;
  color: #909399;
  margin: 0 0 18px;
  padding-left: 14px;
}
.form-actions {
  display: flex;
  gap: 12px;
  padding-left: 110px;
}
.theme-swatches {
  display: flex;
  gap: 16px;
  padding-left: 14px;
}
.theme-swatch {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 10px;
  border: 2px solid #e5e9e5;
  cursor: pointer;
  transition: border-color 0.15s ease;
}
.theme-swatch.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.swatch-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: inline-block;
}
.swatch-label {
  font-size: 13px;
  color: #1b2a38;
}
</style>
