<template>
  <div class="page">
    <div class="page-head">
      <div class="eyebrow">Companies</div>
      <h1 class="page-title">Hiring Companies</h1>
      <p class="page-sub">Browse companies that are hiring; click any company to see its recent postings.</p>
    </div>

    <div class="card searchbar">
      <el-input v-model="q" placeholder="Search company name" clearable style="width: 300px"
                :prefix-icon="Search" @keyup.enter="reload" />
      <el-button type="primary" :icon="Search" @click="reload">Search</el-button>
    </div>

    <div v-loading="loading" class="company-grid">
      <div class="card company-card rise" v-for="c in rows" :key="c.company_id" @click="open(c)">
        <div class="cc-head">
          <div class="cc-avatar">{{ initial(c.name) }}</div>
          <div class="cc-name-wrap">
            <div class="company-name">{{ c.name }}</div>
            <div class="muted cc-loc">{{ [c.city, c.country].filter(Boolean).join(', ') || 'Location unknown' }}</div>
          </div>
        </div>
        <div class="company-meta">
          <span><el-icon><User /></el-icon> {{ c.employee_count ? c.employee_count.toLocaleString() : '—' }} <i>employees</i></span>
          <span><el-icon><Star /></el-icon> {{ c.follower_count ? c.follower_count.toLocaleString() : '—' }} <i>followers</i></span>
        </div>
      </div>
      <div v-if="!loading && !rows.length" class="empty">No companies found.</div>
    </div>

    <el-pagination
      class="pager"
      layout="total, prev, pager, next" :total="total" :current-page="page" :page-size="size"
      @current-change="(p) => { page = p; load() }"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Search, User, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = ref('')
const page = ref(1)
const size = ref(24)

const initial = (name) => (name || '?').trim().charAt(0).toUpperCase()

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (q.value) params.q = q.value
    const res = await api.get('/companies', { params })
    rows.value = res.items
    total.value = res.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
function reload() { page.value = 1; load() }
function open(c) { router.push(`/companies/${c.company_id}`) }
onMounted(load)
</script>

<style scoped>
.searchbar { display: flex; gap: 10px; align-items: center; margin-bottom: 18px; }
.company-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(264px, 1fr)); gap: 1px; background: var(--line); border: 1px solid var(--line); min-height: 120px; }
.company-card { cursor: pointer; border: none; border-radius: 0; transition: background 0.14s; }
.company-card:hover { background: var(--surface-2); }
.cc-head { display: flex; align-items: center; gap: 12px; }
.cc-avatar {
  width: 42px; height: 42px; flex-shrink: 0;
  display: grid; place-items: center; font-family: var(--serif); font-weight: 600; font-size: 19px; color: var(--ink-800);
  background: var(--surface-2); border: 1px solid var(--line-strong);
}
.company-card:hover .cc-avatar { background: var(--surface); }
.cc-name-wrap { min-width: 0; }
.company-name { font-weight: 600; font-size: 15px; color: var(--ink-900); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cc-loc { margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.company-meta { display: flex; gap: 18px; margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--line); color: var(--ink-600); font-size: 12.5px; font-family: var(--mono); }
.company-meta span { display: flex; align-items: center; gap: 5px; font-weight: 500; }
.company-meta i { font-style: normal; color: var(--ink-400); font-weight: 400; }
.company-meta :deep(.el-icon) { color: var(--ink-400); }
.pager { margin-top: 18px; justify-content: flex-end; }
.empty { grid-column: 1 / -1; padding: 40px; text-align: center; color: var(--ink-400); background: var(--surface); }
</style>
