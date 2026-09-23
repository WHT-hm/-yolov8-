<template>
  <div class="knowledge-page">
    <el-card shadow="never" class="filter-card">
      <el-radio-group v-model="activeCrop" @change="() => {}">
        <el-radio-button label="全部" />
        <el-radio-button v-for="c in cropTypes" :key="c" :label="c" />
      </el-radio-group>
    </el-card>

    <el-row :gutter="20" class="card-grid">
      <el-col :span="6" v-for="item in filteredList" :key="item.name">
        <el-card shadow="hover" class="pest-card" @click="openDetail(item)">
          <div class="pest-icon" :class="severityClass(item.severity)">🐛</div>
          <div class="pest-name">{{ item.name }}</div>
          <div class="pest-crop">
            <el-tag size="small" type="info">{{ item.cropType }}</el-tag>
            <el-tag size="small" :type="severityTagType(item.severity)" class="severity-tag">
              {{ item.severity }}危害
            </el-tag>
          </div>
          <div class="pest-summary">{{ item.symptoms }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="detailVisible" :title="detail?.name" width="520px">
      <div v-if="detail">
        <div class="detail-tags">
          <el-tag type="info">{{ detail.cropType }}</el-tag>
          <el-tag :type="severityTagType(detail.severity)">{{ detail.severity }}危害</el-tag>
          <el-tag v-for="a in detail.aliases" :key="a" type="success" effect="plain">{{ a }}</el-tag>
        </div>
        <el-descriptions :column="1" border class="detail-desc">
          <el-descriptions-item label="危害症状">{{ detail.symptoms }}</el-descriptions-item>
          <el-descriptions-item label="防治建议">{{ detail.prevention }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { cropTypes, pestKnowledgeBase } from '../data/pestKnowledge'

const route = useRoute()
const activeCrop = ref('全部')
const detailVisible = ref(false)
const detail = ref(null)

const filteredList = computed(() => {
  if (activeCrop.value === '全部') return pestKnowledgeBase
  return pestKnowledgeBase.filter((item) => item.cropType === activeCrop.value)
})

function severityTagType(level) {
  return { 低: 'success', 中: 'warning', 高: 'danger' }[level] || 'info'
}

function severityClass(level) {
  return { 低: 'is-low', 中: 'is-mid', 高: 'is-high' }[level] || ''
}

function openDetail(item) {
  detail.value = item
  detailVisible.value = true
}

onMounted(() => {
  if (route.query.name) {
    const matched = pestKnowledgeBase.find((item) => item.name === route.query.name)
    if (matched) openDetail(matched)
  }
})
</script>

<style scoped>
.filter-card {
  margin-bottom: 20px;
}
.card-grid {
  row-gap: 20px;
}
.pest-card {
  cursor: pointer;
  height: 100%;
}
.pest-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  background: #eaf5ea;
  margin-bottom: 10px;
}
.pest-icon.is-low {
  background: #eef9ea;
}
.pest-icon.is-mid {
  background: #fdf3e2;
}
.pest-icon.is-high {
  background: #fdeaea;
}
.pest-name {
  font-size: 16px;
  font-weight: 700;
  color: #1b2a38;
  margin-bottom: 8px;
}
.pest-crop {
  margin-bottom: 10px;
}
.severity-tag {
  margin-left: 6px;
}
.pest-summary {
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.detail-tags {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.detail-desc {
  margin-top: 8px;
}
</style>
