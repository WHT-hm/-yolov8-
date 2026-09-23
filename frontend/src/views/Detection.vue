<template>
  <div class="detection-page">
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
              <el-descriptions-item label="平均置信度">{{ (result.avg_confidence * 100).toFixed(0) }}%</el-descriptions-item>
              <el-descriptions-item label="检测时间">{{ formatTime(result.created_at) }}</el-descriptions-item>
            </el-descriptions>

            <div class="result-list">
              <div class="result-list-title">识别到 {{ result.pest_types.length }} 种病虫害：</div>
              <el-tag
                v-for="box in result.boxes"
                :key="box.pest_name + box.x"
                class="result-tag"
                :type="confidenceTagType(box.confidence)"
                effect="dark"
              >
                {{ box.pest_name }} · 置信度 {{ (box.confidence * 100).toFixed(0) }}%
              </el-tag>
            </div>

            <el-alert
              class="mock-alert"
              type="info"
              :closable="false"
              title="当前结果为模拟数据，用于展示界面效果；接入 YOLOv8 模型后将替换为真实检测结果。"
              show-icon
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { createDetection, getMetaOptions } from '../api/detection'

const cropTypes = ref([])
const cropType = ref('')
const selectedFile = ref(null)
const previewUrl = ref('')
const detecting = ref(false)
const result = ref(null)
const resultBoxes = ref([])

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
.result-tag {
  margin: 0 8px 8px 0;
}
.mock-alert {
  margin-top: 24px;
}
</style>
