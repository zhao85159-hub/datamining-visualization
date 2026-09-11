<template>
  <div class="page" v-loading="loading">
    <div class="page-head">
      <div class="eyebrow">Admin · 01</div>
      <h1 class="page-title">Console Overview</h1>
      <p class="page-sub">Live counts for the management tier — accounts and catalogue content you can administer.</p>
    </div>

    <section class="stat-band">
      <div class="stat" v-for="s in stats" :key="s.label">
        <div class="stat-no tnum">{{ s.value.toLocaleString() }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </section>

    <div class="cols">
      <div class="card recent">
        <h3><span class="idx">A</span> Recently registered users</h3>
        <el-table :data="recent" style="width: 100%">
          <el-table-column prop="user_id" label="ID" width="72" />
          <el-table-column prop="username" label="Username" min-width="160" />
          <el-table-column label="Role" width="120">
            <template #default="{ row }">
              <el-tag :type="row.role === 'admin' ? 'primary' : 'info'" effect="plain" size="small" round>
                {{ row.role }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Joined" min-width="170">
            <template #default="{ row }"><span class="muted">{{ fmt(row.created_at) }}</span></template>
          </el-table-column>
          <template #empty><div class="empty">No users yet.</div></template>
        </el-table>
      </div>

      <div class="card jumps">
        <h3><span class="idx">B</span> Quick actions</h3>
        <router-link to="/admin/users" class="jump">
          <el-icon><User /></el-icon>
          <div><b>Manage users</b><span>Promote, demote or remove accounts</span></div>
          <el-icon class="chev"><ArrowRight /></el-icon>
        </router-link>
        <router-link to="/admin/postings" class="jump">
          <el-icon><Briefcase /></el-icon>
          <div><b>Manage postings</b><span>Create, edit and delete job postings</span></div>
          <el-icon class="chev"><ArrowRight /></el-icon>
        </router-link>
        <router-link to="/admin/companies" class="jump">
          <el-icon><OfficeBuilding /></el-icon>
          <div><b>Manage companies</b><span>Maintain the hiring-organisation directory</span></div>
          <el-icon class="chev"><ArrowRight /></el-icon>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { User, Briefcase, OfficeBuilding, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../../api'

const loading = ref(false)
const data = ref({ users: {}, content: {} })
const recent = ref([])

const stats = computed(() => [
  { label: 'Total users', value: data.value.users.total || 0 },
  { label: 'Administrators', value: data.value.users.admins || 0 },
  { label: 'Regular users', value: data.value.users.regular || 0 },
  { label: 'Job postings', value: data.value.content.postings || 0 },
  { label: 'Companies', value: data.value.content.companies || 0 },
  { label: 'Skills', value: data.value.content.skills || 0 }
])

function fmt(s) {
  if (!s) return '—'
  return new Date(s).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/overview')
    data.value = res
    recent.value = res.recent_users || []
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stat-band {
  display: grid; grid-template-columns: repeat(6, 1fr); gap: 1px;
  background: var(--line); border: 1px solid var(--line); margin-bottom: 26px;
}
.stat { background: var(--surface); padding: 20px 18px; }
.stat-no { font-size: 30px; font-weight: 600; color: var(--ink-900); line-height: 1; letter-spacing: -0.01em; }
.stat-label { margin-top: 8px; font-family: var(--mono); font-size: 10.5px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-500); }

.cols { display: grid; grid-template-columns: 1.6fr 1fr; gap: 20px; }
.empty { padding: 24px; color: var(--ink-400); }

.jumps { display: flex; flex-direction: column; }
.jump {
  display: flex; align-items: center; gap: 14px; padding: 16px 14px;
  border: 1px solid var(--line); border-radius: var(--r-sm); margin-bottom: 10px;
  color: var(--ink-800); transition: border-color 0.14s, background 0.14s;
}
.jump:hover { border-color: var(--accent); background: var(--accent-soft); }
.jump > .el-icon:first-child { font-size: 22px; color: var(--accent); }
.jump div { display: flex; flex-direction: column; flex: 1; }
.jump b { font-size: 14.5px; }
.jump span { font-size: 12.5px; color: var(--ink-500); }
.jump .chev { color: var(--ink-300); font-size: 16px; }
.jump:hover .chev { color: var(--accent); }

@media (max-width: 1080px) { .stat-band { grid-template-columns: repeat(3, 1fr); } .cols { grid-template-columns: 1fr; } }
</style>
