<template>
  <div class="detection-page">
    <el-tabs v-model="activeTab">
      <!-- 标签1：图片检测 -->
      <el-tab-pane label="图片检测" name="upload">
        <div class="tab-content">
          <el-row :gutter="20">
            <el-col :span="10">
              <el-card shadow="hover">
                <template #header>上传待检测图片</template>
                <el-upload
                  drag
                  :auto-upload="false"
                  :limit="1"
                  :show-file-list="false"
                  accept="image/*"
                  :on-change="handleFileChange"
                >
                  <template v-if="!previewUrl">
                    <el-icon class="upload-icon"><UploadFilled /></el-icon>
                    <div class="upload-text">拖拽图片到此处，或<em>点击上传</em></div>
                    <div class="upload-hint">支持 jpg / png / bmp / webp</div>
                  </template>
                  <div v-else class="preview-wrap" @click.stop>
                    <div class="image-box">
                      <img :src="previewUrl" />
                      <div
                        v-for="(box, idx) in resultBoxes"
                        :key="idx"
                        class="det-box"
                        :style="boxStyle(box)"
                      >
                        <span class="det-label">{{ box.pest_name }} {{ (box.confidence * 100).toFixed(0) }}%</span>
                      </div>
                    </div>
                  </div>
                </el-upload>

                <div class="form-row">
                  <span class="form-label">作物类型：</span>
                  <el-select v-model="cropType" placeholder="自动识别（可选）" clearable style="width: 200px">
                    <el-option v-for="c in cropTypes" :key="c" :label="c" :value="c" />
                  </el-select>
                </div>

                <div class="action-row">
                  <el-button type="primary" :icon="Search" :loading="detecting" :disabled="!selectedFile" @click="startDetect">
                    开始检测
                  </el-button>
                  <el-button v-if="selectedFile" @click="reset">重新选择</el-button>
                </div>
              </el-card>
            </el-col>

            <el-col :span="14">
              <el-card shadow="hover" class="result-card">
                <template #header>检测结果</template>
                <el-empty v-if="!result" description="暂无检测结果，请先上传图片并开始检测" />
                <div v-else>
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="作物类型">{{ result.crop_type }}</el-descriptions-item>
                    <el-descriptions-item label="严重程度">
                      <el-tag :type="severityTagType(result.severity)">{{ result.severity }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="平均置信度">{{ normalizeConfidence(result.avg_confidence) }}%</el-descriptions-item>
                    <el-descriptions-item label="检测时间">{{ formatTime(result.created_at) }}</el-descriptions-item>
                  </el-descriptions>

                  <div class="result-list">
                    <div class="result-list-title">识别到 {{ result.pest_types.length }} 种病虫害：</div>
                    <div v-for="box in sortedBoxes" :key="box.pest_name + box.x" class="box-row">
                      <span class="box-pest-link" @click="goKnowledge(box.pest_name)">{{ box.pest_name }}</span>
                      <el-tag size="small" :type="confidenceTagType(box.confidence)" effect="dark">
                        置信度 {{ (box.confidence * 100).toFixed(0) }}%
                      </el-tag>
                      <el-tag size="small" type="info" effect="plain">{{ box.plant_part }}</el-tag>
                      <div class="damage-bar">
                        <span class="damage-label">受害占比</span>
                        <el-progress
                          :percentage="box.damage_ratio"
                          :color="damageColor(box.damage_ratio)"
                          :stroke-width="8"
                          style="flex: 1"
                        />
                      </div>
                    </div>
                  </div>

                  <el-alert
                    class="mock-alert"
                    type="info"
                    :closable="false"
                    title="当前结果（含受害占比、受害部位）为模拟数据，用于展示界面效果；接入 YOLOv8 模型后将替换为真实检测结果。"
                    show-icon
                  />
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- 标签2：实时识别 -->
      <el-tab-pane label="实时识别" name="realtime">
        <div class="tab-content">
          <!-- 未配置状态 -->
          <div v-if="!wsConfigured" class="realtime-setup">
            <el-card class="setup-card">
              <div class="setup-title">⚙️ 实时识别配置</div>
              <el-divider />

              <el-form :model="wsConfig" label-width="140px">
                <el-form-item label="摄像头状态">
                  <el-tag v-if="cameraActive" type="success">已启用</el-tag>
                  <el-tag v-else type="info">未启用</el-tag>
                </el-form-item>

                <el-form-item label="启用摄像头">
                  <el-switch v-model="wsConfig.enableCamera" @change="handleCameraToggle" />
                  <span class="config-hint">启用后将在浏览器中请求摄像头权限</span>
                </el-form-item>

                <el-form-item label="识别间隔（毫秒）">
                  <el-input-number
                    v-model="wsConfig.frameInterval"
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
            </el-card>
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

                    <!-- 实时检测框渲染 -->
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
                    <el-button v-if="cameraActive" type="success" @click="captureFrame">
                      截图保存
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
                      <div v-for="pest in realtimeResult.pest_types" :key="pest" class="box-row">
                        <span class="box-pest-link" @click="goKnowledge(pest)">{{ pest }}</span>
                      </div>
                    </div>

                    <el-alert
                      class="mock-alert"
                      type="info"
                      :closable="false"
                      title="实时检测结果为模拟数据演示，接入 YOLOv8 模型后将替换为真实检测结果。"
                      show-icon
                    />
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { onMounted, ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, VideoCamera } from '@element-plus/icons-vue'
import { createDetection, getMetaOptions } from '../api/detection'
import { connectWebSocket, disconnectWebSocket, sendFrame, isWebSocketConnected } from '../api/realtime'

const router = useRouter()

// 标签页状态
const activeTab = ref('upload')

// ============ 图片检测相关 ============
const cropTypes = ref([])
const cropType = ref('')
const selectedFile = ref(null)
const previewUrl = ref('')
const detecting = ref(false)
const result = ref(null)
const resultBoxes = ref([])

// ============ 实时识别相关 ============
const wsConfigured = ref(false)  // 是否已配置摄像头
const wsConfig = ref({
  enableCamera: false,
  frameInterval: 800
})
const cameraActive = ref(false)
const connectingCamera = ref(false)
const videoRef = ref(null)
const overlayCanvasRef = ref(null)
const realtimeCropType = ref('')
const realtimeResult = ref(null)
let cameraStream = null
let frameInterval = null
let wsConnected = false

// ============ 辅助函数 ============

// 安全的置信度显示函数 - 处理任何可能的值格式
function normalizeConfidence(value) {
  if (typeof value === 'number') {
    // 如果值 > 1，假设它是百分比，自动转换
    if (value > 1) {
      return (value / 100).toFixed(0)
    }
    // 如果值 <= 1，假设它是小数，乘以100显示
    return (value * 100).toFixed(0)
  }
  return '0'
}

// ============ 图片检测方法 ============

function handleFileChange(file) {
  selectedFile.value = file.raw
  previewUrl.value = URL.createObjectURL(file.raw)
  result.value = null
  resultBoxes.value = []
}

function boxStyle(box) {
  return {
    left: box.x * 100 + '%',
    top: box.y * 100 + '%',
    width: box.width * 100 + '%',
    height: box.height * 100 + '%',
  }
}

function reset() {
  selectedFile.value = null
  previewUrl.value = ''
  result.value = null
  resultBoxes.value = []
}

function severityTagType(level) {
  return { 低: 'success', 中: 'warning', 高: 'danger' }[level] || 'info'
}

function confidenceTagType(conf) {
  if (conf >= 0.85) return 'danger'
  if (conf >= 0.6) return 'warning'
  return 'success'
}

function damageColor(ratio) {
  if (ratio >= 60) return '#f56c6c'
  if (ratio >= 30) return '#e6a23c'
  return '#67c23a'
}

function goKnowledge(pestName) {
  router.push({ path: '/knowledge', query: { name: pestName } })
}

const sortedBoxes = computed(() => {
  if (!result.value) return []
  return [...result.value.boxes].sort((a, b) => b.damage_ratio - a.damage_ratio)
})

function formatTime(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

async function startDetect() {
  if (!selectedFile.value) return
  detecting.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    if (cropType.value) formData.append('crop_type', cropType.value)
    const res = await createDetection(formData)
    result.value = res
    resultBoxes.value = res.boxes
    ElMessage.success('检测完成')
  } catch (error) {
    ElMessage.error('检测失败')
  } finally {
    detecting.value = false
  }
}

// ============ 实时识别方法 ============

function handleCameraToggle(enabled) {
  if (enabled) {
    wsConfig.value.enableCamera = true
    wsConfigured.value = true
  } else {
    wsConfigured.value = false
    if (cameraActive.value) {
      stopCamera()
    }
  }
}

function resetCameraConfig() {
  if (cameraActive.value) {
    stopCamera()
  }
  wsConfigured.value = false
}

async function startCamera() {
  connectingCamera.value = true
  try {
    // 请求摄像头权限
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

    // 连接 WebSocket
    const token = localStorage.getItem('pw_token')
    await connectWebSocket(token)
    wsConnected = true

    // 定期截取帧并发送检测
    frameInterval = setInterval(() => {
      captureAndDetect()
    }, wsConfig.value.frameInterval)  // 使用配置的间隔

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
  // 停止帧捕获
  if (frameInterval) {
    clearInterval(frameInterval)
    frameInterval = null
  }

  // 关闭摄像头流
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop())
    cameraStream = null
  }

  // 断开 WebSocket
  if (wsConnected) {
    disconnectWebSocket()
    wsConnected = false
  }

  cameraActive.value = false
  realtimeResult.value = null
  ElMessage.success('摄像头已关闭')
}

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

    // 更新结果并绘制检测框
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

  // 绘制检测框
  boxes.forEach(box => {
    const x = box.x * canvas.width
    const y = box.y * canvas.height
    const w = box.width * canvas.width
    const h = box.height * canvas.height

    // 绘制矩形框
    ctx.strokeStyle = '#f56c6c'
    ctx.lineWidth = 2
    ctx.strokeRect(x, y, w, h)

    // 绘制标签背景
    const label = `${box.pest_name} ${(box.confidence * 100).toFixed(0)}%`
    const fontSize = 14
    ctx.font = `${fontSize}px Arial`
    const textWidth = ctx.measureText(label).width
    const padding = 4

    ctx.fillStyle = '#f56c6c'
    ctx.fillRect(x - 2, y - fontSize - padding * 2, textWidth + padding * 2, fontSize + padding * 2)

    // 绘制文字
    ctx.fillStyle = '#fff'
    ctx.fillText(label, x + padding, y - padding)
  })
}

async function captureFrame() {
  if (!videoRef.value) return

  try {
    const imageBase64 = canvasToBase64()
    // 转换为 Blob 并创建 File 对象
    const blobBin = atob(imageBase64.split(',')[1])
    const array = []
    for (let i = 0; i < blobBin.length; i++) {
      array.push(blobBin.charCodeAt(i))
    }
    const file = new File([new Uint8Array(array)], `realtime-${Date.now()}.jpg`, { type: 'image/jpeg' })

    // 上传检测
    const formData = new FormData()
    formData.append('file', file)
    if (realtimeCropType.value) formData.append('crop_type', realtimeCropType.value)

    const res = await createDetection(formData)
    result.value = res
    resultBoxes.value = res.boxes
    activeTab.value = 'upload'  // 切换到图片检测标签展示结果
    ElMessage.success('截图已保存到检测历史')
  } catch (error) {
    console.error('截图保存失败：', error)
    ElMessage.error('截图保存失败')
  }
}

onMounted(async () => {
  const meta = await getMetaOptions()
  cropTypes.value = meta.crop_types
})

onBeforeUnmount(() => {
  stopCamera()
})
</script>

<style scoped>
.upload-icon {
  font-size: 48px;
  color: var(--el-color-primary-light-3);
}
.upload-text {
  color: #606266;
  margin-top: 8px;
}
.upload-text em {
  color: var(--el-color-primary);
  font-style: normal;
}
.upload-hint {
  color: #c0c4cc;
  font-size: 12px;
  margin-top: 4px;
}
.preview-wrap {
  padding: 10px;
}
.image-box {
  position: relative;
  display: inline-block;
  width: 100%;
}
.image-box img {
  display: block;
  width: 100%;
  border-radius: 4px;
}
.det-box {
  position: absolute;
  border: 2px solid #f56c6c;
  box-sizing: border-box;
}
.det-label {
  position: absolute;
  top: -20px;
  left: -2px;
  background: #f56c6c;
  color: #fff;
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 2px;
  white-space: nowrap;
}
.form-row {
  margin-top: 16px;
  display: flex;
  align-items: center;
}
.form-label {
  color: #606266;
  font-size: 14px;
}
.action-row {
  margin-top: 16px;
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
.box-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f2f0;
  flex-wrap: wrap;
}
.box-row:last-child {
  border-bottom: none;
}
.box-pest-link {
  font-weight: 600;
  color: var(--el-color-primary);
  cursor: pointer;
  min-width: 70px;
}
.box-pest-link:hover {
  text-decoration: underline;
}
.damage-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  margin-top: 2px;
}
.damage-label {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}
.mock-alert {
  margin-top: 24px;
}

/* ============ 实时识别相关样式 ============ */
.tab-content {
  padding-top: 20px;
}

.realtime-setup {
  max-width: 600px;
  margin: 0 auto;
}

.setup-card {
  margin-top: 20px;
}

.setup-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.config-hint {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

.realtime-video-container {
  position: relative;
  display: block;
  width: 100%;
  background: #000;
  border-radius: 4px;
  overflow: hidden;
  min-height: 360px;
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

:deep(.el-tabs__content) {
  padding: 0;
}
</style>
