<template>
  <div class="page">
    <div class="page-head">
      <div class="eyebrow">Admin · 04</div>
      <h1 class="page-title">Company Management</h1>
      <p class="page-sub">Maintain the directory of hiring organisations referenced by postings.</p>
    </div>

    <div class="card toolbar">
      <el-input v-model="q" placeholder="Search company name" clearable style="width: 280px"
                :prefix-icon="Search" @keyup.enter="reload" />
      <el-button type="primary" :icon="Search" @click="reload">Search</el-button>
      <div class="spacer"></div>
      <el-button type="primary" :icon="Plus" @click="openCreate">New company</el-button>
    </div>

    <div class="card" v-loading="loading">
      <el-table :data="rows" style="width: 100%" :row-style="{ height: '54px' }">
        <el-table-column prop="company_id" label="ID" width="110" />
        <el-table-column prop="name" label="Name" min-width="240" show-overflow-tooltip>
          <template #default="{ row }"><span class="title-cell">{{ row.name }}</span></template>
        </el-table-column>
        <el-table-column label="Location" min-width="180">
          <template #default="{ row }">{{ [row.city, row.country].filter(Boolean).join(', ') || '—' }}</template>
        </el-table-column>
        <el-table-column label="Employees" width="120" align="right">
          <template #default="{ row }"><span class="tnum">{{ row.employee_count ? row.employee_count.toLocaleString() : '—' }}</span></template>
        </el-table-column>
        <el-table-column label="Followers" width="120" align="right">
          <template #default="{ row }"><span class="tnum">{{ row.follower_count ? row.follower_count.toLocaleString() : '—' }}</span></template>
        </el-table-column>
        <el-table-column label="Actions" width="150" align="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Edit" @click="openEdit(row)" />
            <el-button size="small" type="danger" plain :icon="Delete" @click="remove(row)" />
          </template>
        </el-table-column>
        <template #empty><div class="empty">No companies match.</div></template>
      </el-table>
      <el-pagination
        class="pager" layout="total, sizes, prev, pager, next"
        :total="total" :current-page="page" :page-size="size" :page-sizes="[12, 24, 50]"
        @current-change="(p) => { page = p; load() }"
        @size-change="(s) => { size = s; page = 1; load() }" />
    </div>

    <el-dialog v-model="dialog" :title="editing ? 'Edit company' : 'New company'" width="640px" @closed="resetForm">
      <el-form label-position="top" class="grid-form">
        <el-form-item label="Name" required class="full">
          <el-input v-model="form.name" placeholder="e.g. Acme Corp" />
        </el-form-item>
        <el-form-item label="Country">
          <el-input v-model="form.country" placeholder="e.g. United States" />
        </el-form-item>
        <el-form-item label="State / Region">
          <el-input v-model="form.state" placeholder="e.g. California" />
        </el-form-item>
        <el-form-item label="City">
          <el-input v-model="form.city" placeholder="e.g. San Francisco" />
        </el-form-item>
        <el-form-item label="Company size (code)">
          <el-input v-model.number="form.company_size" type="number" placeholder="1–7" />
        </el-form-item>
        <el-form-item label="Employee count">
          <el-input v-model.number="form.employee_count" type="number" placeholder="e.g. 5000" />
        </el-form-item>
        <el-form-item label="Follower count">
          <el-input v-model.number="form.follower_count" type="number" placeholder="e.g. 12000" />
        </el-form-item>
        <el-form-item label="Address" class="full">
          <el-input v-model="form.address" placeholder="Street address" />
        </el-form-item>
        <el-form-item label="Website URL" class="full">
          <el-input v-model="form.url" placeholder="https://…" />
        </el-form-item>
        <el-form-item label="Description" class="full">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="About the company" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ editing ? 'Save changes' : 'Create company' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Search, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const q = ref('')
const page = ref(1)
const size = ref(24)

const dialog = ref(false)
const editing = ref(false)
const saving = ref(false)
const blank = () => ({
  company_id: null, name: '', country: '', state: '', city: '', address: '',
  url: '', company_size: null, employee_count: null, follower_count: null, description: ''
})
const form = reactive(blank())

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

function resetForm() { Object.assign(form, blank()) }

function openCreate() {
  resetForm()
  editing.value = false
  dialog.value = true
}

async function openEdit(row) {
  editing.value = true
  dialog.value = true
  try {
    const d = await api.get(`/companies/${row.company_id}`)
    Object.assign(form, blank(), {
      company_id: d.company_id, name: d.name, country: d.country, state: d.state,
      city: d.city, address: d.address, url: d.url, company_size: d.company_size,
      employee_count: d.employee_count, follower_count: d.follower_count, description: d.description
    })
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function save() {
  if (!form.name.trim()) return ElMessage.warning('Name is required')
  saving.value = true
  try {
    const payload = {
      name: form.name, country: form.country, state: form.state, city: form.city,
      address: form.address, url: form.url, company_size: form.company_size,
      employee_count: form.employee_count, follower_count: form.follower_count,
      description: form.description
    }
    if (editing.value) {
      await api.put(`/admin/companies/${form.company_id}`, payload)
      ElMessage.success('Company updated')
    } else {
      await api.post('/admin/companies', payload)
      ElMessage.success('Company created')
    }
    dialog.value = false
    load()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`Delete company "${row.name}"?`, 'Delete company', { type: 'warning', confirmButtonText: 'Delete', confirmButtonClass: 'el-button--danger' })
  } catch { return }
  try {
    await api.delete(`/admin/companies/${row.company_id}`)
    ElMessage.success('Company deleted')
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
.title-cell { font-weight: 600; color: var(--ink-800); }
.pager { margin-top: 16px; justify-content: flex-end; }
.empty { padding: 30px; color: var(--ink-400); }
:deep(.el-table .el-table__row) { cursor: default; }
.grid-form { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }
.grid-form .full { grid-column: 1 / -1; }
.grid-form :deep(.el-form-item) { margin-bottom: 16px; }
</style>
