<template>
  <div class="page" v-loading="loading">
    <button class="back" @click="$router.back()"><el-icon><ArrowLeft /></el-icon> Back to companies</button>

    <div v-if="company.company_id" class="detail-layout">
      <div class="card">
        <div class="hero">
          <div class="co-avatar">{{ initial }}</div>
          <div>
            <h1 class="co-name">{{ company.name }}</h1>
            <p class="muted co-loc">
              <el-icon><Location /></el-icon>
              {{ [company.city, company.state, company.country].filter(Boolean).join(', ') || 'Location unknown' }}
            </p>
          </div>
        </div>

        <div class="stats-row">
          <div class="stat-box">
            <b class="tnum">{{ company.employee_count?.toLocaleString() || '—' }}</b>
            <span>Employees</span>
          </div>
          <div class="stat-box">
            <b class="tnum">{{ company.follower_count?.toLocaleString() || '—' }}</b>
            <span>Followers</span>
          </div>
          <div class="stat-box">
            <b class="tnum">{{ company.posting_count?.toLocaleString() || 0 }}</b>
            <span>Postings</span>
          </div>
        </div>

        <h4 class="section-title">About</h4>
        <p class="desc">{{ company.description || 'No description available.' }}</p>

        <h4 class="section-title" style="margin-top: 20px">Specialities</h4>
        <div class="tags">
          <el-tag v-for="(s, i) in (company.specialities || []).slice(0, 30)" :key="i" size="small" effect="plain" round>{{ s }}</el-tag>
          <span v-if="!company.specialities?.length" class="muted">None listed.</span>
        </div>
      </div>

      <div class="card">
        <h4 class="section-title">Recent postings</h4>
        <ul class="postings">
          <li v-for="p in company.postings" :key="p.job_id" @click="$router.push(`/postings/${p.job_id}`)">
            <span class="p-title">{{ p.title }}</span>
            <span class="muted">{{ p.location }} · {{ p.job_category }}</span>
          </li>
          <li v-if="!company.postings?.length" class="muted nohover">No postings yet.</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Location } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const route = useRoute()
const company = ref({})
const loading = ref(false)
const initial = computed(() => (company.value.name || '?').trim().charAt(0).toUpperCase())

onMounted(async () => {
  loading.value = true
  try {
    company.value = await api.get(`/companies/${route.params.id}`)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.back {
  display: inline-flex; align-items: center; gap: 6px; margin-bottom: 18px;
  background: transparent; border: none; cursor: pointer; font-family: inherit;
  color: var(--ink-500); font-size: 13.5px; font-weight: 550; padding: 0; transition: color 0.15s;
}
.back:hover { color: var(--brand); }

.detail-layout { display: grid; grid-template-columns: 1fr 360px; gap: 18px; align-items: start; }
.hero { display: flex; align-items: center; gap: 16px; margin-bottom: 18px; }
.co-avatar {
  width: 56px; height: 56px; flex-shrink: 0;
  display: grid; place-items: center; font-family: var(--serif); font-weight: 600; font-size: 26px; color: var(--surface);
  background: var(--ink-900);
}
.co-name { font-family: var(--serif); font-size: 25px; font-weight: 600; letter-spacing: -0.01em; color: var(--ink-900); margin: 0; }
.co-loc { display: flex; align-items: center; gap: 5px; margin: 6px 0 0; }

.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 22px; }
.stat-box {
  background: var(--surface-2); border: 1px solid var(--line); border-radius: var(--r-sm);
  padding: 14px 16px; display: flex; flex-direction: column; gap: 2px;
}
.stat-box b { font-family: var(--mono); font-size: 21px; font-weight: 600; color: var(--ink-900); }
.stat-box span { font-family: var(--mono); color: var(--ink-400); font-size: 10.5px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; }

.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.desc { line-height: 1.7; color: var(--ink-700); max-height: 280px; overflow-y: auto; font-size: 14px; }

.postings { list-style: none; padding: 0; margin: 0; }
.postings li {
  display: flex; flex-direction: column; gap: 2px;
  padding: 11px 12px; margin: 0 -12px; border-radius: 9px; cursor: pointer; transition: background 0.14s;
}
.postings li:hover:not(.nohover) { background: var(--surface-2); }
.postings li:not(:last-child) { border-bottom: 1px solid var(--line); }
.p-title { font-weight: 600; color: var(--ink-800); font-size: 13.5px; }
.nohover { cursor: default; }

@media (max-width: 980px) { .detail-layout { grid-template-columns: 1fr; } }
</style>
