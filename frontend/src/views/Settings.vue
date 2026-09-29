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
      <h3 class="panel-title">实时摄像头检测</h3>
      <p class="panel-desc">配置和启用实时摄像头病虫害检测功能。</p>

      <!-- 未配置状态 -->
      <div v-if="!cameraConfig.enableCamera" class="camera-setup">
        <el-form :model="cameraConfig" label-width="140px">
          <el-form-item label="启用摄像头">
            <el-switch v-model="cameraConfig.enableCamera" />
            <span class="config-hint">启用后将在浏览器中请求摄像头权限</span>
          </el-form-item>

          <el-form-item label="识别间隔（毫秒）">
            <el-input-number
              v-model="cameraConfig.frameInterval"
              :min="300"
              :max="5000"
              :step="100"
            />
            <span class="config-hint">每多少毫秒发送一帧进行识别（默认800ms）</span>
          </el-form-item>

          <el-form-item label="作物类型">
            <el-select v-model="realtimeCropType" placeholder="自动识别（可选）" clearable>
              <el-option v-for="c in cropTypes" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
        </el-form>

        <el-alert
          type="info"
          :closable="false"
          title="提示：启用摄像头后将请求浏览器权限。请在浏览器权限对话框中允许访问摄像头。"
          show-icon
          style="margin-top: 20px"
        />
      </div>

      <!-- 已配置状态 -->
      <div v-else>
        <el-row :gutter="20">
          <el-col :span="10">
            <el-card shadow="hover">
              <template #header>
                <span>摄像头实时检测</span>
                <el-button text size="small" @click="resetCameraConfig" style="float: right">
                  修改配置
                </el-button>
              </template>

              <div class="realtime-video-container">
                <video
                  v-show="cameraActive"
                  ref="videoRef"
                  class="realtime-video"
                  playsinline
                  autoplay
                  muted
                />
                <div v-if="!cameraActive" class="camera-placeholder">
                  <el-icon class="camera-icon"><VideoCamera /></el-icon>
                  <div>点击下方"开启摄像头"开始检测</div>
                </div>

                <div v-if="cameraActive" class="realtime-overlay">
                  <canvas ref="overlayCanvasRef" class="realtime-canvas" />
                </div>
              </div>

              <div class="action-row">
                <el-button
                  v-if="!cameraActive"
                  type="primary"
                  :icon="VideoCamera"
                  @click="startCamera"
                  :loading="connectingCamera"
                >
                  开启摄像头
                </el-button>
                <el-button v-else type="danger" @click="stopCamera">
                  关闭摄像头
                </el-button>
              </div>
            </el-card>
          </el-col>

          <el-col :span="14">
            <el-card shadow="hover" class="result-card">
              <template #header>实时检测结果</template>
              <el-empty v-if="!realtimeResult" description="摄像头未开启或暂无检测结果" />
              <div v-else>
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="严重程度">
                    <el-tag :type="severityTagType(realtimeResult.severity)">{{ realtimeResult.severity }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="平均置信度">{{ normalizeConfidence(realtimeResult.avg_confidence) }}%</el-descriptions-item>
                </el-descriptions>

                <div class="result-list">
                  <div class="result-list-title">识别到 {{ realtimeResult.pest_types.length }} 种病虫害：</div>
                  <div v-for="pest in realtimeResult.pest_types" :key="pest" class="pest-item">
                    <span>{{ pest }}</span>
                  </div>
                </div>

                <el-alert
                  type="info"
                  :closable="false"
                  title="实时检测结果为模拟数据演示，接入 YOLOv8 模型后将替换为真实检测结果。"
                  show-icon
                  style="margin-top: 20px"
                />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
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
import { onMounted, reactive, ref, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoCamera } from '@element-plus/icons-vue'
import { getSettings, testConnection, updateSettings } from '../api/settings'
import { THEMES, themeStore } from '../store/theme'
import { connectWebSocket, disconnectWebSocket, sendFrame, isWebSocketConnected } from '../api/realtime'
import { getMetaOptions } from '../api/detection'

const apiForm = reactive({ api_base_url: '', model_name: '', api_key: '' })
const apiKeyPlaceholder = ref('尚未设置')
const loadingSettings = ref(false)
const saving = ref(false)
const testing = ref(false)

// Real-time camera settings
const cameraConfig = reactive({
  enableCamera: false,
  frameInterval: 800
})
const cameraActive = ref(false)
const connectingCamera = ref(false)
const videoRef = ref(null)
const overlayCanvasRef = ref(null)
const realtimeCropType = ref('')
const cropTypes = ref([])
const realtimeResult = ref(null)
let cameraStream = null
let frameInterval = null
let wsConnected = false

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

// Real-time camera functions
function canvasToBase64() {
  if (!videoRef.value) return ''
  const canvas = document.createElement('canvas')
  canvas.width = videoRef.value.videoWidth
  canvas.height = videoRef.value.videoHeight
  const ctx = canvas.getContext('2d')
  ctx.drawImage(videoRef.value, 0, 0)
  return canvas.toDataURL('image/jpeg')
}

async function captureAndDetect() {
  if (!isWebSocketConnected()) return

  try {
    const imageBase64 = canvasToBase64()
    const res = await sendFrame(imageBase64, realtimeCropType.value)
    realtimeResult.value = res
    drawDetectionBoxes(res.boxes)
  } catch (error) {
    console.error('检测失败：', error)
  }
}

function drawDetectionBoxes(boxes) {
  if (!overlayCanvasRef.value || !videoRef.value) return

  const canvas = overlayCanvasRef.value
  canvas.width = videoRef.value.videoWidth
  canvas.height = videoRef.value.videoHeight

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  boxes.forEach(box => {
    const x = box.x * canvas.width
    const y = box.y * canvas.height
    const w = box.width * canvas.width
    const h = box.height * canvas.height

    ctx.strokeStyle = '#f56c6c'
    ctx.lineWidth = 2
    ctx.strokeRect(x, y, w, h)

    const label = `${box.pest_name} ${(box.confidence * 100).toFixed(0)}%`
    const fontSize = 14
    ctx.font = `${fontSize}px Arial`
    const textWidth = ctx.measureText(label).width
    const padding = 4

    ctx.fillStyle = '#f56c6c'
    ctx.fillRect(x - 2, y - fontSize - padding * 2, textWidth + padding * 2, fontSize + padding * 2)

    ctx.fillStyle = '#fff'
    ctx.fillText(label, x + padding, y - padding)
  })
}

async function startCamera() {
  connectingCamera.value = true
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false
    })

    if (videoRef.value) {
      videoRef.value.srcObject = cameraStream
      videoRef.value.onloadedmetadata = () => {
        videoRef.value.play()
      }
    }

    cameraActive.value = true

    const token = localStorage.getItem('pw_token')
    await connectWebSocket(token)
    wsConnected = true

    frameInterval = setInterval(() => {
      captureAndDetect()
    }, cameraConfig.frameInterval)

    ElMessage.success('摄像头已启动')
  } catch (error) {
    console.error('启动摄像头失败：', error)
    ElMessage.error('启动摄像头失败，请检查权限设置')
    cameraActive.value = false
  } finally {
    connectingCamera.value = false
  }
}

function stopCamera() {
  if (frameInterval) {
    clearInterval(frameInterval)
    frameInterval = null
  }

  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop())
    cameraStream = null
  }

  if (wsConnected) {
    disconnectWebSocket()
    wsConnected = false
  }

  cameraActive.value = false
  realtimeResult.value = null
  ElMessage.success('摄像头已关闭')
}

function resetCameraConfig() {
  if (cameraActive.value) {
    stopCamera()
  }
  cameraConfig.enableCamera = false
}

function normalizeConfidence(value) {
  if (typeof value === 'number') {
    if (value > 1) {
      return (value / 100).toFixed(0)
    }
    return (value * 100).toFixed(0)
  }
  return '0'
}

function severityTagType(level) {
  return { 低: 'success', 中: 'warning', 高: 'danger' }[level] || 'info'
}

onMounted(async () => {
  await loadSettings()
  const meta = await getMetaOptions()
  cropTypes.value = meta.crop_types
})

onBeforeUnmount(() => {
  if (cameraActive.value) {
    stopCamera()
  }
})
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
.config-hint {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
.camera-setup {
  padding: 0;
}
.realtime-video-container {
  position: relative;
  display: block;
  width: 100%;
  background: #000;
  border-radius: 4px;
  overflow: hidden;
  min-height: 360px;
  margin-bottom: 16px;
}
.realtime-video {
  display: block;
  width: 100%;
  height: auto;
  background: #000;
}
.camera-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 360px;
  background: #f0f2f0;
  color: #909399;
}
.camera-icon {
  font-size: 64px;
  color: #c0c4cc;
  margin-bottom: 10px;
}
.realtime-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.realtime-canvas {
  display: block;
  width: 100%;
  height: 100%;
}
.action-row {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}
.result-card {
  min-height: 420px;
}
.result-list {
  margin-top: 20px;
}
.result-list-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}
.pest-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f2f0;
}
.pest-item:last-child {
  border-bottom: none;
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
