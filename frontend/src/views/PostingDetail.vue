<template>
  <div class="page" v-loading="loading">
    <button class="back" @click="$router.back()"><el-icon><ArrowLeft /></el-icon> Back to list</button>

    <div v-if="posting.job_id" class="detail-layout">
      <div class="card main">
        <div class="hero">
          <h1 class="job-title">{{ posting.title }}</h1>
          <p class="company-line">
            <el-icon><OfficeBuilding /></el-icon>
            <router-link v-if="posting.company_id" :to="`/companies/${posting.company_id}`">{{ posting.company_name }}</router-link>
            <span v-else>{{ posting.company_name }}</span>
            <span class="dotsep">·</span>
            <el-icon><Location /></el-icon> {{ posting.location }}
          </p>
          <div class="tags">
            <el-tag effect="plain" round>{{ posting.job_category }}</el-tag>
            <el-tag type="info" effect="plain" round>{{ posting.formatted_work_type }}</el-tag>
            <el-tag type="info" effect="plain" round>{{ posting.formatted_experience_level }}</el-tag>
            <el-tag v-if="posting.remote_allowed" type="success" effect="light" round>Remote</el-tag>
            <el-tag v-if="posting.normalized_salary" type="warning" effect="light" round>
              ${{ Math.round(posting.normalized_salary).toLocaleString() }} / yr
            </el-tag>
          </div>
        </div>

        <h4 class="section-title">Skill extraction · NLP</h4>
        <div class="tags">
          <el-tag v-for="s in extractedSkills" :key="s" effect="light" round>{{ s }}</el-tag>
          <span v-if="!extractedSkills.length" class="muted">No skills detected.</span>
        </div>

        <h4 class="section-title" style="margin-top: 22px">Job description</h4>
        <div class="desc">{{ posting.description }}</div>
      </div>

      <div class="card side">
        <h4 class="section-title">Tagged skills</h4>
        <div class="tags">
          <el-tag v-for="s in posting.skills" :key="s.skill_abr" effect="plain" size="small" round>{{ s.skill_name }}</el-tag>
          <span v-if="!posting.skills?.length" class="muted">None.</span>
        </div>
        <h4 class="section-title" style="margin-top: 22px">Similar postings</h4>
        <ul class="similar">
          <li v-for="s in similar" :key="s.job_id" @click="$router.push(`/postings/${s.job_id}`)">
            <span class="sim-title">{{ s.title }}</span>
            <span class="muted">{{ s.company_name }}</span>
          </li>
          <li v-if="!similar.length" class="muted nohover">No similar postings yet.</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, OfficeBuilding, Location } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const route = useRoute()
const posting = ref({})
const similar = ref([])
const extractedSkills = ref([])
const loading = ref(false)

async function load(id) {
  loading.value = true
  try {
    posting.value = await api.get(`/postings/${id}`)
    similar.value = await api.get(`/postings/${id}/similar`)
    if (posting.value.description) {
      const r = await api.post('/skills/extract', { text: posting.value.description })
      extractedSkills.value = r.skills
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
onMounted(() => load(route.params.id))
watch(() => route.params.id, (id) => id && load(id))
</script>

<style scoped>
.back {
  display: inline-flex; align-items: center; gap: 6px; margin-bottom: 18px;
  background: transparent; border: none; cursor: pointer; font-family: inherit;
  color: var(--ink-500); font-size: 13.5px; font-weight: 550; padding: 0;
  transition: color 0.15s;
}
.back:hover { color: var(--brand); }

.detail-layout { display: grid; grid-template-columns: 1fr 332px; gap: 18px; align-items: start; }
.hero { border-bottom: 1px solid var(--line); padding-bottom: 18px; margin-bottom: 18px; }
.job-title { font-family: var(--serif); font-size: 26px; font-weight: 600; letter-spacing: -0.01em; color: var(--ink-900); margin: 0 0 10px; line-height: 1.2; }
.company-line { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; color: var(--ink-600); margin: 0 0 14px; font-size: 14px; }
.company-line :deep(.el-icon) { color: var(--ink-400); }
.dotsep { color: var(--ink-300); margin: 0 4px; }

.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.desc { white-space: pre-wrap; line-height: 1.7; color: var(--ink-700); max-height: 520px; overflow-y: auto; font-size: 14px; padding-right: 6px; }

.similar { list-style: none; padding: 0; margin: 0; }
.similar li {
  display: flex; flex-direction: column; gap: 2px;
  padding: 11px 12px; margin: 0 -12px; border-radius: 9px; cursor: pointer;
  transition: background 0.14s;
}
.similar li:hover:not(.nohover) { background: var(--surface-2); }
.similar li:not(:last-child) { border-bottom: 1px solid var(--line); border-radius: 9px; }
.sim-title { font-weight: 600; color: var(--ink-800); font-size: 13.5px; }
.nohover { cursor: default; }

@media (max-width: 980px) { .detail-layout { grid-template-columns: 1fr; } }
</style>
