<template>
  <div class="global-search" ref="rootRef">
    <el-input
      v-model="keyword"
      placeholder="搜索检测记录 / 病虫害知识库"
      class="search-input"
      clearable
      @input="onInput"
      @focus="showDropdown = true"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>

    <div v-if="showDropdown && keyword.trim()" class="search-dropdown">
      <div v-if="loading" class="dropdown-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        搜索中...
      </div>
      <template v-else-if="historyResults.length || knowledgeResults.length">
        <div v-if="historyResults.length" class="result-group">
          <div class="group-title">检测记录</div>
          <div
            v-for="item in historyResults"
            :key="'h-' + item.id"
            class="result-item"
            @mousedown.prevent="goHistory(item)"
          >
            <span class="result-main">{{ item.pest_types.join('、') }}</span>
            <span class="result-sub">{{ item.crop_type }} · {{ formatTime(item.created_at) }}</span>
          </div>
        </div>
        <div v-if="knowledgeResults.length" class="result-group">
          <div class="group-title">病虫害知识库</div>
          <div
            v-for="item in knowledgeResults"
            :key="'k-' + item.name"
            class="result-item"
            @mousedown.prevent="goKnowledge(item)"
          >
            <span class="result-main">{{ item.name }}</span>
            <span class="result-sub">{{ item.cropType }} · {{ item.symptoms }}</span>
          </div>
        </div>
      </template>
      <div v-else class="dropdown-empty">未找到相关结果</div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Loading, Search } from '@element-plus/icons-vue'
import { listDetections } from '../api/detection'
import { pestKnowledgeBase } from '../data/pestKnowledge'

const router = useRouter()
const rootRef = ref(null)

const keyword = ref('')
const showDropdown = ref(false)
const loading = ref(false)
const historyResults = ref([])
const knowledgeResults = ref([])

let debounceTimer = null

function onInput() {
  showDropdown.value = true
  clearTimeout(debounceTimer)
  const value = keyword.value.trim()
  if (!value) {
    historyResults.value = []
    knowledgeResults.value = []
    return
  }
  debounceTimer = setTimeout(() => runSearch(value), 300)
}

async function runSearch(value) {
  knowledgeResults.value = pestKnowledgeBase
    .filter(
      (item) =>
        item.name.includes(value) ||
        item.aliases.some((a) => a.includes(value)) ||
        item.symptoms.includes(value)
    )
    .slice(0, 5)

  loading.value = true
  try {
    const res = await listDetections({ keyword: value, page: 1, page_size: 5 })
    historyResults.value = res.items
  } catch {
    historyResults.value = []
  } finally {
    loading.value = false
  }
}

function formatTime(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

function goHistory(item) {
  showDropdown.value = false
  router.push({ path: '/history', query: { keyword: item.pest_types[0] } })
}

function goKnowledge(item) {
  showDropdown.value = false
  router.push({ path: '/knowledge', query: { name: item.name } })
}

function handleClickOutside(e) {
  if (rootRef.value && !rootRef.value.contains(e.target)) {
    showDropdown.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', handleClickOutside))
</script>

<style scoped>
.global-search {
  position: relative;
  width: 320px;
}
.search-input :deep(.el-input__wrapper) {
  border-radius: 20px;
  background: #f2f4f7;
  box-shadow: none;
}
.search-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(17, 26, 46, 0.15);
  padding: 8px 0;
  max-height: 360px;
  overflow-y: auto;
  z-index: 200;
}
.group-title {
  font-size: 12px;
  color: #a0a5ad;
  padding: 6px 16px;
}
.result-item {
  padding: 8px 16px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.result-item:hover {
  background: #f5f7f6;
}
.result-main {
  font-size: 14px;
  color: #1b2a38;
  font-weight: 600;
}
.result-sub {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dropdown-loading,
.dropdown-empty {
  padding: 16px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}
</style>
