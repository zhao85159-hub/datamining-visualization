<template>
  <div class="page" v-loading="loading">
    <div class="page-head">
      <div class="eyebrow">Analytics</div>
      <h1 class="page-title">Skills &amp; Analytics</h1>
      <p class="page-sub">Skill-demand rankings, pay by category and a skill co-occurrence map, plus live NLP skill extraction and ML job classification.</p>
    </div>

    <div class="section-title">Charts</div>
    <div class="chart-grid">
      <div class="card"><h3><span class="idx">Fig 1</span> Skill Demand Ranking</h3><EChart :option="rankingOption" :loading="loading" /></div>
      <div class="card"><h3><span class="idx">Fig 2</span> Average Salary by Category</h3><EChart :option="salaryOption" :loading="loading" /></div>
      <div class="card" style="grid-column: 1 / -1"><h3><span class="idx">Fig 3</span> Skill Co-occurrence Heatmap</h3><EChart :option="heatmapOption" :loading="loading" style="height: 440px" /></div>
    </div>

    <div class="section-title" style="margin-top: 28px">Live services</div>
    <div class="services">
      <div class="card svc">
        <div class="svc-head">
          <div class="svc-badge">NLP</div>
          <div>
            <h3 class="svc-title">Skill extraction</h3>
            <span class="muted">Automatically detect and extract a normalised skill set from a job description.</span>
          </div>
        </div>
        <el-input v-model="demoText" type="textarea" :rows="4" resize="none" placeholder="Paste a job description…" />
        <el-button type="primary" class="svc-btn" @click="runExtract" :loading="extracting">Extract skills</el-button>
        <div class="tags" v-if="extracted.length">
          <el-tag v-for="s in extracted" :key="s" type="primary" effect="light">{{ s }}</el-tag>
        </div>
        <p v-else-if="ranExtract" class="muted">No skills detected in the text.</p>
      </div>

      <div class="card svc">
        <div class="svc-head">
          <div class="svc-badge clay">ML</div>
          <div>
            <h3 class="svc-title">Job classification</h3>
            <span class="muted">Predict the category a role belongs to from its job title.</span>
          </div>
        </div>
        <el-input v-model="demoTitle" size="large" placeholder="e.g. Senior Data Engineer" @keyup.enter="runClassify" />
        <el-button type="primary" class="svc-btn" @click="runClassify" :loading="classifying">Classify</el-button>
        <div v-if="classification.category" class="verdict">
          <span class="section-title" style="margin: 0 0 8px">Predicted category</span>
          <div class="verdict-row">
            <el-tag size="large" effect="plain">{{ classification.category }}</el-tag>
            <div class="conf">
              <div class="conf-bar"><span :style="{ width: (classification.confidence * 100) + '%' }" /></div>
              <span class="conf-num tnum">{{ (classification.confidence * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'
import EChart from '../components/EChart.vue'
import { PALETTE } from '../echartsTheme'

const loading = ref(true)
const ranking = ref([])
const salary = ref([])
const matrix = ref({ skills: [], matrix: [] })

const demoText = ref('We are hiring a backend engineer with strong Python, Flask, SQL and AWS experience. Knowledge of Docker and Kubernetes is a plus.')
const demoTitle = ref('Senior Machine Learning Engineer')
const extracted = ref([])
const ranExtract = ref(false)
const classification = ref({})
const extracting = ref(false)
const classifying = ref(false)

const fmtK = (v) => (v >= 1e6 ? (v / 1e6).toFixed(v % 1e6 ? 1 : 0) + 'M' : v >= 1e3 ? Math.round(v / 1e3) + 'k' : v)

const rankingOption = computed(() => {
  const items = [...ranking.value].slice(0, 15)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 8, right: 18, top: 12, bottom: 8, containLabel: true },
    xAxis: { type: 'value', splitNumber: 3, axisLabel: { formatter: fmtK } },
    yAxis: { type: 'category', data: items.map((i) => i.name).reverse() },
    series: [{ type: 'bar', barMaxWidth: 16, data: items.map((i) => i.value).reverse(), itemStyle: { color: PALETTE[0] } }]
  }
})
const salaryOption = computed(() => {
  const items = salary.value
  return {
    tooltip: { trigger: 'axis', valueFormatter: (v) => '$' + Math.round(v).toLocaleString() },
    grid: { left: 8, right: 24, top: 12, bottom: 8, containLabel: true },
    xAxis: { type: 'value', splitNumber: 4, axisLabel: { formatter: (v) => '$' + Math.round(v / 1000) + 'k' } },
    yAxis: { type: 'category', data: items.map((i) => i.category).reverse() },
    series: [{ type: 'bar', barMaxWidth: 16, data: items.map((i) => Math.round(i.avg_salary)).reverse(), itemStyle: { color: PALETTE[2] } }]
  }
})
const heatmapOption = computed(() => {
  const skills = matrix.value.skills || []
  const m = matrix.value.matrix || []
  const data = []
  let max = 1
  for (let i = 0; i < skills.length; i++) {
    for (let j = 0; j < skills.length; j++) {
      const v = (m[i] && m[i][j]) || 0
      data.push([j, i, v])
      if (i !== j && v > max) max = v
    }
  }
  return {
    tooltip: { position: 'top' },
    grid: { left: 8, right: 20, top: 16, bottom: 96, containLabel: true },
    xAxis: { type: 'category', data: skills, axisLabel: { rotate: 45, fontSize: 10 }, splitArea: { show: true } },
    yAxis: { type: 'category', data: skills, axisLabel: { fontSize: 10 }, splitArea: { show: true } },
    visualMap: { min: 0, max, calculable: true, orient: 'horizontal', left: 'center', bottom: 12, itemWidth: 12, inRange: { color: ['#ecf5ff', '#a0cfff', '#409eff', '#1f6fcc'] } },
    series: [{ type: 'heatmap', data, label: { show: false }, itemStyle: { borderColor: '#ffffff', borderWidth: 1 } }]
  }
})

async function runExtract() {
  extracting.value = true
  try { extracted.value = (await api.post('/skills/extract', { text: demoText.value })).skills; ranExtract.value = true }
  catch (e) { ElMessage.error(e.message) } finally { extracting.value = false }
}
async function runClassify() {
  classifying.value = true
  try { classification.value = await api.post('/analytics/classify', { title: demoTitle.value }) }
  catch (e) { ElMessage.error(e.message) } finally { classifying.value = false }
}

onMounted(async () => {
  try {
    ranking.value = await api.get('/skills', { params: { limit: 20 } })
    const sal = await api.get('/analytics/salary')
    salary.value = sal.by_category
    matrix.value = await api.get('/skills/cooccurrence', { params: { top: 12 } })
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.chart-grid { grid-template-columns: 1fr 1fr; }
.services { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: var(--line); border: 1px solid var(--line); }
.svc { border: none; border-radius: 0; }
.svc-head { display: flex; align-items: flex-start; gap: 13px; margin-bottom: 16px; }
.svc-badge {
  width: 42px; height: 42px; flex-shrink: 0; display: grid; place-items: center;
  background: var(--accent); color: #fff; font-family: var(--mono); font-weight: 600; font-size: 13px;
}
.svc-badge.clay { background: var(--clay); }
.svc-title { font-family: var(--serif); margin: 0 0 2px; font-size: 17px; font-weight: 600; color: var(--ink-900); }
.svc-title::before { display: none; }
.svc-btn { margin: 13px 0; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; }

.verdict { margin-top: 6px; }
.verdict-row { display: flex; align-items: center; gap: 16px; }
.conf { display: flex; align-items: center; gap: 10px; flex: 1; }
.conf-bar { flex: 1; height: 8px; background: var(--surface-2); border: 1px solid var(--line); overflow: hidden; max-width: 220px; }
.conf-bar span { display: block; height: 100%; background: var(--accent); transition: width 0.5s ease; }
.conf-num { font-weight: 600; color: var(--ink-800); font-size: 14px; }

@media (max-width: 860px) { .services { grid-template-columns: 1fr; } }
</style>
