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
          <img v-if="item.imageUrl" :src="item.imageUrl" class="pest-thumb" :class="severityClass(item.severity)" />
          <div v-else class="pest-icon" :class="severityClass(item.severity)">🐛</div>
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

        <div class="appearance-section">
          <div class="appearance-title">外观识别</div>
          <div class="appearance-body">
            <img v-if="detail.imageUrl" :src="detail.imageUrl" class="appearance-photo" />
            <div v-else class="appearance-icon" :class="severityClass(detail.severity)">🐛</div>
            <div class="appearance-actions">
              <a
                class="search-link"
                :href="imageSearchUrl(detail.name)"
                target="_blank"
                rel="noopener noreferrer"
              >
                <el-button type="primary" plain :icon="Search">在线搜图识别</el-button>
              </a>
              <div v-if="detail.imageCredit" class="appearance-credit">{{ detail.imageCredit }}</div>
              <div class="appearance-hint">
                {{ detail.imageUrl ? '图片来自开放授权图库，仅供外观参考；' : '本应用暂未内置该虫害的实拍图片，' }}如需更多图片可点击右侧按钮前往搜索引擎查看
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
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

function imageSearchUrl(name) {
  return `https://image.baidu.com/search/index?tn=baiduimage&word=${encodeURIComponent(name + ' 病虫害')}`
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
.pest-thumb {
  width: 100%;
  height: 100px;
  object-fit: cover;
  border-radius: 6px;
  margin-bottom: 10px;
  display: block;
  border: 2px solid transparent;
}
.pest-thumb.is-low {
  border-color: #67c23a;
}
.pest-thumb.is-mid {
  border-color: #e6a23c;
}
.pest-thumb.is-high {
  border-color: #f56c6c;
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
.appearance-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
.appearance-title {
  font-size: 14px;
  font-weight: 700;
  color: #1b2a38;
  margin-bottom: 12px;
}
.appearance-body {
  display: flex;
  align-items: center;
  gap: 16px;
}
.appearance-icon {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  background: #eaf5ea;
}
.appearance-icon.is-low {
  background: #eef9ea;
}
.appearance-icon.is-mid {
  background: #fdf3e2;
}
.appearance-icon.is-high {
  background: #fdeaea;
}
.appearance-photo {
  width: 140px;
  height: 140px;
  flex-shrink: 0;
  object-fit: cover;
  border-radius: 8px;
}
.appearance-credit {
  margin-top: 8px;
  font-size: 11px;
  color: #c0c4cc;
}
.appearance-actions {
  flex: 1;
}
.search-link {
  text-decoration: none;
}
.appearance-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}
</style>
