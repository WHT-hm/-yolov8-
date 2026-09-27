<template>
  <div class="dashboard" v-loading="loading">
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" :style="{ background: card.color }">
            <el-icon :size="22"><component :is="card.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>病虫害种类分布</template>
          <v-chart class="chart" :option="speciesOption" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>严重程度分布</template>
          <v-chart class="chart" :option="severityOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>近 7 天检测趋势</template>
          <v-chart class="chart-wide" :option="trendOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>各病虫害受害程度排行</template>
          <v-chart class="chart" :option="damageRankingOption" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>受害部位分布</template>
          <v-chart class="chart" :option="partDistributionOption" autoresize />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getDashboardStats } from '../api/dashboard'

const loading = ref(false)
const stats = ref(null)

// 安全的置信度显示函数
function normalizeConfidence(value) {
  if (typeof value === 'number') {
    if (value > 1) {
      return (value / 100).toFixed(0)
    }
    return (value * 100).toFixed(0)
  }
  return '0'
}

const statCards = computed(() => {
  if (!stats.value) return []
  return [
    { label: '总检测次数', value: stats.value.total_detections, icon: 'Tickets', color: '#3d63e0' },
    { label: '今日检测次数', value: stats.value.today_detections, icon: 'Camera', color: '#1f9d6b' },
    { label: '涉及病虫害种类', value: stats.value.pest_species_count, icon: 'Warning', color: '#b6552f' },
    { label: '平均置信度', value: normalizeConfidence(stats.value.avg_confidence) + '%', icon: 'DataAnalysis', color: '#12a3b0' },
  ]
})

const severityColor = { 低: '#67c23a', 中: '#e6a23c', 高: '#f56c6c' }
const speciesPalette = ['#3d63e0', '#1f9d6b', '#ff8a4c', '#12a3b0', '#b6552f', '#8e5fd6', '#e0538c', '#d4b106', '#6c8ffb', '#4caf7a']

const speciesOption = computed(() => ({
  color: speciesPalette,
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, type: 'scroll' },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{d}%' },
      data: (stats.value?.species_distribution || []).map((d) => ({ name: d.name, value: d.count })),
    },
  ],
}))

const severityOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 30, bottom: 30 },
  xAxis: { type: 'category', data: (stats.value?.severity_distribution || []).map((d) => d.level) },
  yAxis: { type: 'value' },
  series: [
    {
      type: 'bar',
      barWidth: 40,
      data: (stats.value?.severity_distribution || []).map((d) => ({
        value: d.count,
        itemStyle: { color: severityColor[d.level] || '#409eff' },
      })),
    },
  ],
}))

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 30, bottom: 30 },
  xAxis: { type: 'category', data: (stats.value?.trend || []).map((d) => d.date.slice(5)) },
  yAxis: { type: 'value' },
  series: [
    {
      type: 'line',
      smooth: true,
      areaStyle: { color: 'rgba(61,99,224,0.15)' },
      lineStyle: { color: '#3d63e0', width: 3 },
      itemStyle: { color: '#3d63e0' },
      data: (stats.value?.trend || []).map((d) => d.count),
    },
  ],
}))

const damageRankingOption = computed(() => {
  const ranking = [...(stats.value?.damage_ranking || [])].sort((a, b) => a.avg_damage_ratio - b.avg_damage_ratio)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 90, right: 30, top: 20, bottom: 20 },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    yAxis: { type: 'category', data: ranking.map((d) => d.pest_name) },
    series: [
      {
        type: 'bar',
        barWidth: 16,
        label: { show: true, position: 'right', formatter: '{c}%' },
        data: ranking.map((d) => ({
          value: d.avg_damage_ratio,
          itemStyle: { color: d.avg_damage_ratio >= 60 ? '#f56c6c' : d.avg_damage_ratio >= 30 ? '#e6a23c' : '#67c23a' },
        })),
      },
    ],
  }
})

const partPalette = { 叶片: '#1f9d6b', 茎秆: '#e6a23c', 根部: '#b6552f', 其他: '#909399' }
const partDistributionOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{d}%' },
      data: (stats.value?.part_distribution || []).map((d) => ({
        name: d.part,
        value: d.count,
        itemStyle: { color: partPalette[d.part] || '#409eff' },
      })),
    },
  ],
}))

async function fetchStats() {
  loading.value = true
  try {
    stats.value = await getDashboardStats()
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>

<style scoped>
.stat-row {
  margin-bottom: 20px;
}
.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 14px;
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1b2a38;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.chart-row {
  margin-bottom: 20px;
}
.chart,
.chart-wide {
  height: 300px;
}
</style>
