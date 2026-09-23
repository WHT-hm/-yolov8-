<template>
  <div class="history-page">
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="filters" @submit.prevent>
        <el-form-item label="病虫害类型">
          <el-select v-model="filters.pest_type" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="p in pestTypes" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度">
          <el-select v-model="filters.severity" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="s in severityLevels" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="病虫害/作物名称" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="onSearch">查询</el-button>
          <el-button :icon="RefreshLeft" @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="table-card" v-loading="loading">
      <el-table :data="records" stripe>
        <el-table-column label="缩略图" width="90">
          <template #default="{ row }">
            <el-image
              :src="row.thumbnail_url"
              fit="cover"
              class="thumb"
              :preview-src-list="[row.image_url]"
            />
          </template>
        </el-table-column>
        <el-table-column label="病虫害类型">
          <template #default="{ row }">
            <el-tag v-for="p in row.pest_types" :key="p" class="pest-tag" size="small">{{ p }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="crop_type" label="作物类型" width="100" />
        <el-table-column label="置信度" width="100">
          <template #default="{ row }">{{ (row.avg_confidence * 100).toFixed(0) }}%</template>
        </el-table-column>
        <el-table-column label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="severityTagType(row.severity)">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="检测时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">详情</el-button>
            <el-button link type="danger" @click="removeRecord(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pagination"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchList"
        @current-change="fetchList"
      />
    </el-card>

    <el-dialog v-model="detailVisible" title="检测详情" width="600px">
      <div v-if="detail">
        <div class="detail-image-box">
          <img :src="detail.image_url" />
          <div
            v-for="(box, idx) in detail.boxes"
            :key="idx"
            class="det-box"
            :style="{
              left: box.x * 100 + '%',
              top: box.y * 100 + '%',
              width: box.width * 100 + '%',
              height: box.height * 100 + '%',
            }"
          >
            <span class="det-label">{{ box.pest_name }} {{ (box.confidence * 100).toFixed(0) }}%</span>
          </div>
        </div>
        <el-descriptions :column="2" border class="detail-desc">
          <el-descriptions-item label="作物类型">{{ detail.crop_type }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="severityTagType(detail.severity)">{{ detail.severity }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="平均置信度">{{ (detail.avg_confidence * 100).toFixed(0) }}%</el-descriptions-item>
          <el-descriptions-item label="检测时间">{{ formatTime(detail.created_at) }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshLeft, Search } from '@element-plus/icons-vue'
import { deleteDetection, getDetection, getMetaOptions, listDetections } from '../api/detection'

const route = useRoute()

const records = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)

const filters = ref({ pest_type: '', severity: '', keyword: '' })
const pestTypes = ref([])
const severityLevels = ref([])

const detailVisible = ref(false)
const detail = ref(null)

async function fetchList() {
  loading.value = true
  try {
    const res = await listDetections({
      page: page.value,
      page_size: pageSize.value,
      pest_type: filters.value.pest_type || undefined,
      severity: filters.value.severity || undefined,
      keyword: filters.value.keyword || undefined,
    })
    records.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  fetchList()
}

function onReset() {
  filters.value = { pest_type: '', severity: '', keyword: '' }
  onSearch()
}

async function viewDetail(row) {
  detail.value = await getDetection(row.id)
  detailVisible.value = true
}

async function removeRecord(row) {
  try {
    await ElMessageBox.confirm('确定删除该条检测记录吗？', '提示', { type: 'warning' })
  } catch {
    return
  }
  await deleteDetection(row.id)
  ElMessage.success('已删除')
  fetchList()
}

function severityTagType(level) {
  return { 低: 'success', 中: 'warning', 高: 'danger' }[level] || 'info'
}

function formatTime(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(async () => {
  const meta = await getMetaOptions()
  pestTypes.value = meta.pest_types
  severityLevels.value = meta.severity_levels
  if (route.query.keyword) {
    filters.value.keyword = String(route.query.keyword)
  }
  fetchList()
})
</script>

<style scoped>
.filter-card {
  margin-bottom: 16px;
}
.thumb {
  width: 56px;
  height: 56px;
  border-radius: 4px;
  cursor: pointer;
}
.pest-tag {
  margin: 2px 4px 2px 0;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
  display: flex;
}
.detail-image-box {
  position: relative;
  margin-bottom: 16px;
}
.detail-image-box img {
  width: 100%;
  display: block;
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
.detail-desc {
  margin-top: 8px;
}
</style>
