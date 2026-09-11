<template>
  <div class="page">
    <div class="page-head">
      <div class="eyebrow">Job Postings</div>
      <h1 class="page-title">Browse Job Postings</h1>
      <p class="page-sub">Search, filter and inspect the full detail of every posting in the dataset.</p>
    </div>

    <div class="card filterbar">
      <el-form :inline="true" @submit.prevent>
        <el-form-item>
          <el-input v-model="filters.q" placeholder="Search title / location" clearable style="width: 248px"
                    :prefix-icon="Search" @keyup.enter="reload" />
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.category" placeholder="Category" clearable style="width: 200px">
            <el-option v-for="c in categories" :key="c.name" :label="c.name" :value="c.name" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.work_type" placeholder="Work type" clearable style="width: 152px">
            <el-option v-for="w in workTypes" :key="w" :label="w" :value="w" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="filters.remote" label="Remote only" border />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="reload">Search</el-button>
          <el-button :icon="RefreshLeft" @click="reset">Reset</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card" v-loading="loading">
      <div class="result-meta">
        <span>Found <b class="tnum">{{ total.toLocaleString() }}</b> postings</span>
        <span class="muted">Click any row to view the full posting</span>
      </div>
      <el-table :data="rows" style="width: 100%" @row-click="open" :row-style="{ height: '54px' }">
        <el-table-column prop="title" label="Title" min-width="248" show-overflow-tooltip>
          <template #default="{ row }"><span class="title-cell">{{ row.title }}</span></template>
        </el-table-column>
        <el-table-column prop="company_name" label="Company" min-width="160" show-overflow-tooltip />
        <el-table-column prop="location" label="Location" min-width="150" show-overflow-tooltip>
          <template #default="{ row }"><span class="loc"><el-icon><Location /></el-icon>{{ row.location || '—' }}</span></template>
        </el-table-column>
        <el-table-column label="Category" min-width="166">
          <template #default="{ row }"><el-tag size="small" effect="plain" round>{{ row.job_category }}</el-tag></template>
        </el-table-column>
        <el-table-column label="Salary" min-width="124" align="right">
          <template #default="{ row }">
            <span class="tnum sal">{{ row.normalized_salary ? '$' + Math.round(row.normalized_salary).toLocaleString() : '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Mode" width="98">
          <template #default="{ row }">
            <el-tag v-if="row.remote_allowed" type="success" size="small" effect="light" round>Remote</el-tag>
            <span v-else class="muted">On-site</span>
          </template>
        </el-table-column>
        <template #empty><div class="empty">No postings match your filters.</div></template>
      </el-table>
      <el-pagination
        class="pager"
        layout="total, sizes, prev, pager, next"
        :total="total" :current-page="filters.page" :page-size="filters.size"
        :page-sizes="[10, 20, 50]"
        @current-change="(p) => { filters.page = p; load() }"
        @size-change="(s) => { filters.size = s; filters.page = 1; load() }"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Search, RefreshLeft, Location } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const categories = ref([])
const workTypes = ['Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship', 'Volunteer']
const filters = reactive({ q: '', category: '', work_type: '', remote: false, page: 1, size: 20 })

async function load() {
  loading.value = true
  try {
    const params = { page: filters.page, size: filters.size }
    if (filters.q) params.q = filters.q
    if (filters.category) params.category = filters.category
    if (filters.work_type) params.work_type = filters.work_type
    if (filters.remote) params.remote = 1
    const res = await api.get('/postings', { params })
    rows.value = res.items
    total.value = res.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
function reload() { filters.page = 1; load() }
function reset() {
  Object.assign(filters, { q: '', category: '', work_type: '', remote: false, page: 1 })
  load()
}
function open(row) { router.push(`/postings/${row.job_id}`) }

onMounted(async () => {
  load()
  try {
    const dash = await api.get('/analytics/dashboard')
    categories.value = dash.categories
  } catch (e) { /* non-fatal */ }
})
</script>

<style scoped>
.filterbar { margin-bottom: 16px; padding-bottom: 4px; }
.filterbar :deep(.el-form-item) { margin-bottom: 14px; }
.result-meta { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 12px; }
.result-meta b { font-size: 16px; color: var(--ink-900); }
.title-cell { font-weight: 600; color: var(--ink-800); }
.loc { display: inline-flex; align-items: center; gap: 5px; color: var(--ink-600); }
.loc :deep(.el-icon) { color: var(--ink-400); }
.sal { font-weight: 600; color: var(--ink-800); }
.pager { margin-top: 16px; justify-content: flex-end; }
.empty { padding: 30px; color: var(--ink-400); }
</style>
