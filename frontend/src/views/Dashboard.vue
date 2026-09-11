<template>
  <div class="page">
    <div v-if="showWelcome" class="alert-success">
      <span>Signed in successfully. Welcome to the Graduate Recruitment analytics platform.</span>
      <button class="close" @click="dismissWelcome">×</button>
    </div>

    <div class="page-head">
      <div class="eyebrow">Dashboard</div>
      <h1 class="page-title">Recruitment Market Overview</h1>
      <p class="page-sub">Built on the LinkedIn 2023–2024 job-postings dataset — hiring demand, pay and skills at a glance, computed live across the full dataset.</p>
    </div>

    <div class="stat-strip" v-loading="loading">
      <StatCard label="Total postings" :value="summary.total_postings" color="#5b8ff9" hint="Jobs indexed" />
      <StatCard label="Companies" :value="summary.total_companies" color="#9270ca" hint="Hiring now" />
      <StatCard label="Skills" :value="summary.total_skills" color="#2bc4b6" hint="Skill graph" />
      <StatCard label="Remote roles" :value="summary.remote_postings" color="#f7944d" :hint="remoteShare" />
      <StatCard label="Avg. salary" :value="avgSalary" color="#ef6a9a" hint="Annual · USD" />
    </div>

    <div class="section-title">Key charts</div>
    <div class="chart-grid" v-loading="loading">
      <div class="card"><h3><span class="idx">Fig 1</span> Top 15 Skills in Demand</h3><EChart :option="skillsOption" :loading="loading" /></div>
      <div class="card"><h3><span class="idx">Fig 2</span> Job Category Mix</h3><EChart :option="categoryOption" :loading="loading" /></div>
      <div class="card"><h3><span class="idx">Fig 3</span> Work-type Distribution</h3><EChart :option="workTypeOption" :loading="loading" /></div>
      <div class="card"><h3><span class="idx">Fig 4</span> Experience-level Distribution</h3><EChart :option="expOption" :loading="loading" /></div>
      <div class="card"><h3><span class="idx">Fig 5</span> Top Hiring Cities</h3><EChart :option="locationOption" :loading="loading" /></div>
      <div class="card"><h3><span class="idx">Fig 6</span> Top 10 Hiring Companies</h3><EChart :option="companyOption" :loading="loading" /></div>
    </div>

    <div class="section-title">Data mining · trend insights</div>
    <div class="chart-grid" v-loading="miningLoading">
      <div class="card wide">
        <h3>
          <span class="idx">Fig 7</span> Hiring trend by {{ trendDim === 'location' ? 'location' : 'job category' }}
          <el-radio-group v-model="trendDim" size="small" class="dim-toggle">
            <el-radio-button value="location">By location</el-radio-button>
            <el-radio-button value="category">By category</el-radio-button>
          </el-radio-group>
        </h3>
        <p class="fig-note">Window 2024-03-24 – 2024-04-20, aggregated by day; each line is one {{ trendDim === 'location' ? 'location' : 'job category' }}, showing its own distinct hiring trend.</p>
        <EChart :option="positionTrendOption" :loading="miningLoading" style="height: 360px" />
      </div>
      <div class="card wide">
        <h3><span class="idx">Fig 8</span> Category Market Map · avg salary × applicant interest × scale</h3>
        <p class="fig-note">X-axis is average salary, Y-axis is average applications, and bubble size is the number of postings — spot high-pay/high-competition and blue-ocean tracks at a glance.</p>
        <EChart :option="marketOption" :loading="miningLoading" style="height: 360px" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'
import EChart from '../components/EChart.vue'
import StatCard from '../components/StatCard.vue'
import { useAuthStore } from '../store/auth'
import { PALETTE } from '../echartsTheme'

const auth = useAuthStore()
const loading = ref(true)
const miningLoading = ref(true)
const summary = ref({})
const data = ref({})
const mining = ref({})
const trendDim = ref('location')

const showWelcome = ref(auth.isAuthenticated && sessionStorage.getItem('welcomed') !== '1')
function dismissWelcome() {
  showWelcome.value = false
  sessionStorage.setItem('welcomed', '1')
}

const avgSalary = computed(() =>
  summary.value.avg_salary ? '$' + Math.round(summary.value.avg_salary).toLocaleString() : '—'
)
const remoteShare = computed(() => {
  const t = summary.value.total_postings, r = summary.value.remote_postings
  return t && r != null ? `${Math.round((r / t) * 100)}% remote` : 'Remote-friendly'
})

const fmtK = (v) => (v >= 1e6 ? (v / 1e6).toFixed(v % 1e6 ? 1 : 0) + 'M' : v >= 1e3 ? Math.round(v / 1e3) + 'k' : v)

function barOption(items, color = PALETTE[0], horizontal = true) {
  const names = items.map((i) => i.name)
  const values = items.map((i) => i.value)
  const valueAxis = { type: 'value', splitNumber: 3, axisLabel: { formatter: fmtK } }
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 8, right: 16, top: 12, bottom: 8, containLabel: true },
    xAxis: horizontal ? valueAxis : { type: 'category', data: names, axisLabel: { interval: 0, rotate: 24 } },
    yAxis: horizontal ? { type: 'category', data: [...names].reverse() } : valueAxis,
    series: [{
      type: 'bar',
      barMaxWidth: 20,
      data: horizontal ? [...values].reverse() : values,
      itemStyle: { color },
      emphasis: { itemStyle: { color: shade(color, -0.16) } }
    }]
  }
}
function pieOption(items) {
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      type: 'scroll', orient: 'vertical', right: 0, top: 'center', itemGap: 7,
      textStyle: { fontSize: 10 }, formatter: (n) => (n.length > 15 ? n.slice(0, 14) + '…' : n)
    },
    series: [{
      type: 'pie', radius: ['48%', '70%'], center: ['32%', '50%'],
      avoidLabelOverlap: true, itemStyle: { borderColor: '#ffffff', borderWidth: 2 },
      label: { show: false }, labelLine: { show: false }, data: items
    }]
  }
}
function shade(hex, amt) {
  const c = hex.replace('#', '')
  const f = (i) => {
    const v = Math.round(parseInt(c.slice(i, i + 2), 16) * (1 + amt))
    return Math.max(0, Math.min(255, v)).toString(16).padStart(2, '0')
  }
  return `#${f(0)}${f(2)}${f(4)}`
}

const skillsOption = computed(() => barOption(data.value.top_skills || [], PALETTE[0]))
const categoryOption = computed(() => pieOption(data.value.categories || []))
const workTypeOption = computed(() => pieOption(data.value.work_type || []))
const expOption = computed(() => barOption(data.value.experience || [], PALETTE[4], false))
const locationOption = computed(() => barOption(data.value.top_locations || [], PALETTE[2]))
const companyOption = computed(() => barOption(data.value.top_companies || [], PALETTE[1]))

const positionTrendOption = computed(() => {
  const pt = mining.value.position_trends || {}
  const days = (pt.days || []).map((d) => d.slice(5))
  const series = (trendDim.value === 'location' ? pt.by_location : pt.by_category) || []
  return {
    tooltip: { trigger: 'axis' },
    legend: { type: 'scroll', top: 0, textStyle: { fontSize: 11 } },
    grid: { left: 8, right: 18, top: 40, bottom: 8, containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: days },
    yAxis: { type: 'value', splitNumber: 4, axisLabel: { formatter: fmtK } },
    series: series.map((s, i) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: s.data,
      itemStyle: { color: PALETTE[i % PALETTE.length] },
      lineStyle: { width: 2 },
      areaStyle: { opacity: 0.05 }
    }))
  }
})

const marketOption = computed(() => {
  const items = (mining.value.market || []).filter((m) => m.avg_salary != null && m.avg_applies != null)
  const maxCount = Math.max(1, ...items.map((m) => m.count))
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const d = p.data
        return `<b>${d.category}</b><br/>Avg salary: $${Math.round(d.avg_salary).toLocaleString()}<br/>`
          + `Avg applies: ${d.avg_applies}<br/>Avg views: ${d.avg_views}<br/>Postings: ${d.count.toLocaleString()}`
      }
    },
    grid: { left: 8, right: 28, top: 18, bottom: 44, containLabel: true },
    xAxis: {
      type: 'value', name: 'Avg salary', nameLocation: 'middle', nameGap: 30,
      axisLabel: { formatter: (v) => '$' + Math.round(v / 1000) + 'k' }
    },
    yAxis: { type: 'value', name: 'Avg applications', nameGap: 16 },
    series: [{
      type: 'scatter',
      symbolSize: (val, params) => 16 + 46 * Math.sqrt(params.data.count / maxCount),
      data: items.map((m, i) => ({
        value: [m.avg_salary, m.avg_applies], ...m,
        itemStyle: { color: PALETTE[i % PALETTE.length], opacity: 0.82 }
      })),
      label: { show: true, formatter: (p) => p.data.category, position: 'top', fontSize: 10, color: '#606266' }
    }]
  }
})

onMounted(async () => {
  try {
    const res = await api.get('/analytics/dashboard')
    data.value = res
    summary.value = res.summary
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
  try {
    mining.value = await api.get('/analytics/mining')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    miningLoading.value = false
  }
})
</script>

<style scoped>
.stat-strip {
  display: grid; grid-template-columns: repeat(5, 1fr);
  gap: 16px; margin-bottom: 30px;
}
@media (max-width: 1100px) { .stat-strip { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 560px) { .stat-strip { grid-template-columns: 1fr; } }

.chart-grid .wide { grid-column: 1 / -1; }
.dim-toggle { margin-left: auto; }
.fig-note { margin: 0 0 6px; color: var(--ink-500); font-size: 12.5px; line-height: 1.6; }
</style>
