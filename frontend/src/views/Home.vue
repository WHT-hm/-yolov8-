<template>
  <div class="home-page">
    <section class="hero">
      <div class="hero-text">
        <div class="hero-badge">智慧农业 · AI 病虫害防治</div>
        <h1>农作物病虫害检测系统</h1>
        <p>基于 YOLOv8 目标检测模型，实现农作物病虫害的快速识别与统计分析，助力精准防治、减损增产。</p>
        <div class="hero-actions">
          <el-button size="large" class="hero-btn-primary" :icon="Camera" @click="$router.push('/detection')">
            立即开始检测
          </el-button>
          <el-button size="large" class="hero-btn-ghost" :icon="DataAnalysis" @click="$router.push('/dashboard')">
            查看数据统计
          </el-button>
        </div>
      </div>
      <div class="hero-decor">🐛🌿🦗</div>
    </section>

    <section class="stats-strip" v-loading="loading">
      <div class="stat-item" v-for="s in statItems" :key="s.label">
        <div class="stat-num" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </section>

    <section class="features">
      <h2 class="section-title">核心功能</h2>
      <el-row :gutter="20">
        <el-col :span="6" v-for="f in features" :key="f.title">
          <el-card shadow="hover" class="feature-card" @click="$router.push(f.path)">
            <div class="feature-icon" :style="{ background: f.color }">
              <el-icon :size="24"><component :is="f.icon" /></el-icon>
            </div>
            <div class="feature-title">{{ f.title }}</div>
            <div class="feature-desc">{{ f.desc }}</div>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <el-row :gutter="20" class="lower-row">
      <el-col :span="12">
        <section class="panel">
          <h2 class="section-title">最新检测动态</h2>
          <el-card shadow="never" class="panel-card" v-loading="activityLoading">
            <el-empty v-if="!recentActivity.length" description="暂无检测记录" />
            <el-timeline v-else>
              <el-timeline-item
                v-for="item in recentActivity"
                :key="item.id"
                :color="severityColor(item.severity)"
                :timestamp="formatTime(item.created_at)"
              >
                <span class="timeline-link" @click="goHistory(item)">
                  {{ item.pest_types.join('、') }}
                </span>
                <span class="timeline-sub">· {{ item.crop_type }} · 置信度 {{ (item.avg_confidence * 100).toFixed(0) }}%</span>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </section>
      </el-col>
      <el-col :span="12">
        <section class="panel">
          <h2 class="section-title">防治小贴士</h2>
          <el-card shadow="never" class="panel-card tips-card">
            <el-carousel height="220px" indicator-position="outside" :interval="4500">
              <el-carousel-item v-for="tip in tips" :key="tip.name">
                <div class="tip-slide">
                  <div class="tip-icon">💡</div>
                  <div class="tip-name">{{ tip.name }}（{{ tip.cropType }}）</div>
                  <div class="tip-text">{{ tip.prevention }}</div>
                </div>
              </el-carousel-item>
            </el-carousel>
          </el-card>
        </section>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Camera, DataAnalysis } from '@element-plus/icons-vue'
import { getDashboardStats } from '../api/dashboard'
import { listDetections } from '../api/detection'
import { pestKnowledgeBase } from '../data/pestKnowledge'

const router = useRouter()

const loading = ref(false)
const stats = ref(null)
const activityLoading = ref(false)
const recentActivity = ref([])

const statItems = computed(() => [
  { label: '累计检测次数', value: stats.value?.total_detections ?? '--', color: 'var(--accent-home)' },
  { label: '今日检测次数', value: stats.value?.today_detections ?? '--', color: 'var(--accent-dashboard)' },
  { label: '覆盖病虫害种类', value: stats.value?.pest_species_count ?? '--', color: 'var(--accent-knowledge)' },
  {
    label: '平均识别置信度',
    value: stats.value ? (stats.value.avg_confidence * 100).toFixed(0) + '%' : '--',
    color: 'var(--accent-history)',
  },
])

const features = [
  { title: '病虫害检测', desc: '上传田间照片，快速获取识别结果与防治提示', icon: 'Camera', color: 'var(--accent-detection)', path: '/detection' },
  { title: '数据统计仪表盘', desc: '多维度图表展示病虫害分布与发生趋势', icon: 'DataAnalysis', color: 'var(--accent-dashboard)', path: '/dashboard' },
  { title: '检测历史记录', desc: '追溯每一次检测的图片、结果与时间线', icon: 'Tickets', color: 'var(--accent-history)', path: '/history' },
  { title: '病虫害知识库', desc: '常见病虫害症状与科学防治建议速查', icon: 'Reading', color: 'var(--accent-knowledge)', path: '/knowledge' },
]

const tips = pestKnowledgeBase.slice(0, 5)

function severityColor(level) {
  return { 低: '#67c23a', 中: '#e6a23c', 高: '#f56c6c' }[level] || '#909399'
}

function formatTime(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

function goHistory(item) {
  router.push({ path: '/history', query: { keyword: item.pest_types[0] } })
}

async function fetchStats() {
  loading.value = true
  try {
    stats.value = await getDashboardStats()
  } finally {
    loading.value = false
  }
}

async function fetchActivity() {
  activityLoading.value = true
  try {
    const res = await listDetections({ page: 1, page_size: 5 })
    recentActivity.value = res.items
  } finally {
    activityLoading.value = false
  }
}

onMounted(() => {
  fetchStats()
  fetchActivity()
})
</script>

<style scoped>
.hero {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  padding: 48px 40px;
  background: linear-gradient(120deg, #111a2e 0%, #17405c 45%, #12a3b0 100%);
  color: #fff;
  margin-bottom: 24px;
}
.hero-text {
  max-width: 640px;
  position: relative;
  z-index: 1;
}
.hero-badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  padding: 4px 14px;
  font-size: 12px;
  margin-bottom: 14px;
}
.hero-text h1 {
  font-size: 32px;
  margin: 0 0 12px;
}
.hero-text p {
  font-size: 14px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 0 24px;
}
.hero-actions {
  display: flex;
  gap: 12px;
}
.hero-btn-primary {
  background: var(--accent-home);
  border-color: var(--accent-home);
  color: #fff;
}
.hero-btn-primary:hover {
  opacity: 0.9;
  background: var(--accent-home);
  border-color: var(--accent-home);
  color: #fff;
}
.hero-btn-ghost {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.4);
  color: #fff;
}
.hero-btn-ghost:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.6);
  color: #fff;
}
.hero-decor {
  position: absolute;
  right: 30px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 64px;
  opacity: 0.25;
  letter-spacing: 12px;
}

.stats-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}
.stat-item {
  text-align: center;
  border-right: 1px solid #f0f2f0;
}
.stat-item:last-child {
  border-right: none;
}
.stat-num {
  font-size: 28px;
  font-weight: 700;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 6px;
}

.section-title {
  font-size: 18px;
  color: #1b2a38;
  margin: 0 0 16px;
  padding-left: 10px;
  border-left: 4px solid var(--accent-home);
}
.features {
  margin-bottom: 32px;
}
.feature-card {
  cursor: pointer;
  height: 100%;
}
.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-bottom: 12px;
}
.feature-title {
  font-size: 15px;
  font-weight: 600;
  color: #1b2a38;
  margin-bottom: 6px;
}
.feature-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}

.lower-row {
  margin-bottom: 12px;
}
.panel-card {
  min-height: 260px;
}
.timeline-link {
  color: #1b2a38;
  font-weight: 600;
  cursor: pointer;
}
.timeline-link:hover {
  color: var(--el-color-primary);
}
.timeline-sub {
  font-size: 12px;
  color: #909399;
  margin-left: 6px;
}
.tips-card :deep(.el-card__body) {
  padding: 12px;
}
.tip-slide {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 0 32px;
}
.tip-icon {
  font-size: 28px;
  margin-bottom: 8px;
}
.tip-name {
  font-weight: 700;
  color: var(--accent-knowledge);
  margin-bottom: 8px;
}
.tip-text {
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
}
</style>
