<template>
  <div class="detection-page">
    <!-- 标签页：图片检测 -->
    <el-card shadow="hover">
      <template #header>图片检测</template>
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
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { createDetection, getMetaOptions } from '../api/detection'

const router = useRouter()

// Image detection related
const cropTypes = ref([])
const cropType = ref('')
const selectedFile = ref(null)
const previewUrl = ref('')
const detecting = ref(false)
const result = ref(null)
const resultBoxes = ref([])

// Helper functions
function normalizeConfidence(value) {
  if (typeof value === 'number') {
    if (value > 1) {
      return (value / 100).toFixed(0)
    }
    return (value * 100).toFixed(0)
  }
  return '0'
}

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

onMounted(async () => {
  const meta = await getMetaOptions()
  cropTypes.value = meta.crop_types
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
</style>
