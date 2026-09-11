<template>
  <div class="page">
    <div class="page-head">
      <div class="eyebrow">Admin · 02</div>
      <h1 class="page-title">User Administration</h1>
      <p class="page-sub">Search accounts, grant or revoke administrator rights, and remove users.</p>
    </div>

    <div class="card toolbar">
      <el-input v-model="q" placeholder="Search username" clearable style="width: 260px"
                :prefix-icon="Search" @keyup.enter="reload" />
      <el-select v-model="role" placeholder="All roles" clearable style="width: 150px" @change="reload">
        <el-option label="Administrators" value="admin" />
        <el-option label="Regular users" value="user" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="reload">Search</el-button>
      <div class="spacer"></div>
      <span class="muted tnum">{{ total.toLocaleString() }} accounts</span>
    </div>

    <div class="card" v-loading="loading">
      <el-table :data="rows" style="width: 100%" :row-style="{ height: '56px' }">
        <el-table-column prop="user_id" label="ID" width="80" />
        <el-table-column prop="username" label="Username" min-width="180">
          <template #default="{ row }">
            <span class="uname">{{ row.username }}</span>
            <el-tag v-if="row.user_id === auth.user?.user_id" size="small" effect="plain" round class="you">you</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Role" width="130">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'primary' : 'info'" effect="plain" round>{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Joined" min-width="170">
          <template #default="{ row }"><span class="muted">{{ fmt(row.created_at) }}</span></template>
        </el-table-column>
        <el-table-column label="Actions" width="240" align="right">
          <template #default="{ row }">
            <el-button v-if="row.role === 'user'" size="small" @click="setRole(row, 'admin')">Make admin</el-button>
            <el-button v-else size="small" @click="setRole(row, 'user')">Revoke admin</el-button>
            <el-button size="small" type="danger" plain :icon="Delete" @click="remove(row)" />
          </template>
        </el-table-column>
        <template #empty><div class="empty">No users match.</div></template>
      </el-table>
      <el-pagination
        class="pager" layout="total, prev, pager, next"
        :total="total" :current-page="page" :page-size="size"
        @current-change="(p) => { page = p; load() }" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Search, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'
import { useAuthStore } from '../../store/auth'

const auth = useAuthStore()
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = ref('')
const role = ref('')
const page = ref(1)
const size = ref(20)

function fmt(s) {
  if (!s) return '—'
  return new Date(s).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (q.value) params.q = q.value
    if (role.value) params.role = role.value
    const res = await api.get('/admin/users', { params })
    rows.value = res.items
    total.value = res.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
function reload() { page.value = 1; load() }

async function setRole(row, next) {
  const verb = next === 'admin' ? 'grant administrator rights to' : 'revoke administrator rights from'
  try {
    await ElMessageBox.confirm(`Are you sure you want to ${verb} "${row.username}"?`, 'Change role', { type: 'warning' })
  } catch { return }
  try {
    await api.patch(`/admin/users/${row.user_id}`, { role: next })
    ElMessage.success('Role updated')
    load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`Delete user "${row.username}"? This cannot be undone.`, 'Delete user', { type: 'warning', confirmButtonText: 'Delete', confirmButtonClass: 'el-button--danger' })
  } catch { return }
  try {
    await api.delete(`/admin/users/${row.user_id}`)
    ElMessage.success('User deleted')
    if (rows.value.length === 1 && page.value > 1) page.value -= 1
    load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.toolbar .spacer { flex: 1; }
.uname { font-weight: 600; color: var(--ink-800); }
.you { margin-left: 8px; }
.pager { margin-top: 16px; justify-content: flex-end; }
.empty { padding: 30px; color: var(--ink-400); }
:deep(.el-table .el-table__row) { cursor: default; }
</style>
