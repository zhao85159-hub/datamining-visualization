<template>
  <div class="page">
    <div class="page-head">
      <div class="eyebrow">Admin · 03</div>
      <h1 class="page-title">Posting Management</h1>
      <p class="page-sub">Create, edit and remove job postings in the catalogue.</p>
    </div>

    <div class="card toolbar">
      <el-input v-model="q" placeholder="Search title / location" clearable style="width: 260px"
                :prefix-icon="Search" @keyup.enter="reload" />
      <el-select v-model="category" placeholder="Category" clearable style="width: 200px" @change="reload">
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="reload">Search</el-button>
      <div class="spacer"></div>
      <el-button type="primary" :icon="Plus" @click="openCreate">New posting</el-button>
    </div>

    <div class="card" v-loading="loading">
      <el-table :data="rows" style="width: 100%" :row-style="{ height: '54px' }">
        <el-table-column prop="job_id" label="ID" width="92" />
        <el-table-column prop="title" label="Title" min-width="240" show-overflow-tooltip>
          <template #default="{ row }"><span class="title-cell">{{ row.title }}</span></template>
        </el-table-column>
        <el-table-column prop="company_name" label="Company" min-width="150" show-overflow-tooltip />
        <el-table-column prop="location" label="Location" min-width="140" show-overflow-tooltip />
        <el-table-column label="Category" min-width="150">
          <template #default="{ row }"><el-tag size="small" effect="plain" round>{{ row.job_category || '—' }}</el-tag></template>
        </el-table-column>
        <el-table-column label="Salary" width="116" align="right">
          <template #default="{ row }">
            <span class="tnum">{{ row.normalized_salary ? '$' + Math.round(row.normalized_salary).toLocaleString() : '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="150" align="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Edit" @click="openEdit(row)" />
            <el-button size="small" type="danger" plain :icon="Delete" @click="remove(row)" />
          </template>
        </el-table-column>
        <template #empty><div class="empty">No postings match.</div></template>
      </el-table>
      <el-pagination
        class="pager" layout="total, sizes, prev, pager, next"
        :total="total" :current-page="page" :page-size="size" :page-sizes="[10, 20, 50]"
        @current-change="(p) => { page = p; load() }"
        @size-change="(s) => { size = s; page = 1; load() }" />
    </div>

    <el-dialog v-model="dialog" :title="editing ? 'Edit posting' : 'New posting'" width="640px" @closed="resetForm">
      <el-form label-position="top" class="grid-form">
        <el-form-item label="Title" required class="full">
          <el-input v-model="form.title" placeholder="e.g. Senior Software Engineer" />
        </el-form-item>
        <el-form-item label="Company ID">
          <el-input v-model.number="form.company_id" type="number" placeholder="Numeric company id" />
        </el-form-item>
        <el-form-item label="Location">
          <el-input v-model="form.location" placeholder="e.g. New York, NY" />
        </el-form-item>
        <el-form-item label="Category">
          <el-select v-model="form.job_category" placeholder="Select" clearable filterable allow-create style="width: 100%">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="Work type">
          <el-select v-model="form.formatted_work_type" placeholder="Select" clearable style="width: 100%">
            <el-option v-for="w in workTypes" :key="w" :label="w" :value="w" />
          </el-select>
        </el-form-item>
        <el-form-item label="Experience level">
          <el-select v-model="form.formatted_experience_level" placeholder="Select" clearable style="width: 100%">
            <el-option v-for="x in expLevels" :key="x" :label="x" :value="x" />
          </el-select>
        </el-form-item>
        <el-form-item label="Annual salary (USD)">
          <el-input v-model.number="form.normalized_salary" type="number" placeholder="e.g. 120000" />
        </el-form-item>
        <el-form-item label="Remote allowed">
          <el-switch v-model="form.remote_allowed" />
        </el-form-item>
        <el-form-item label="Description" class="full">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="Role description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ editing ? 'Save changes' : 'Create posting' }}</el-button>
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
const category = ref('')
const categories = ref([])
const page = ref(1)
const size = ref(20)

const workTypes = ['Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship', 'Volunteer']
const expLevels = ['Internship', 'Entry level', 'Associate', 'Mid-Senior level', 'Director', 'Executive']

const dialog = ref(false)
const editing = ref(false)
const saving = ref(false)
const blank = () => ({
  job_id: null, title: '', company_id: null, location: '', job_category: '',
  formatted_work_type: '', formatted_experience_level: '', normalized_salary: null,
  remote_allowed: false, description: ''
})
const form = reactive(blank())

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (q.value) params.q = q.value
    if (category.value) params.category = category.value
    const res = await api.get('/postings', { params })
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
    const d = await api.get(`/postings/${row.job_id}`)
    Object.assign(form, blank(), {
      job_id: d.job_id, title: d.title, company_id: d.company_id, location: d.location,
      job_category: d.job_category, formatted_work_type: d.formatted_work_type,
      formatted_experience_level: d.formatted_experience_level,
      normalized_salary: d.normalized_salary, remote_allowed: !!d.remote_allowed,
      description: d.description
    })
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function save() {
  if (!form.title.trim()) return ElMessage.warning('Title is required')
  saving.value = true
  try {
    const payload = {
      title: form.title, company_id: form.company_id || null, location: form.location,
      job_category: form.job_category, formatted_work_type: form.formatted_work_type,
      formatted_experience_level: form.formatted_experience_level,
      normalized_salary: form.normalized_salary, remote_allowed: form.remote_allowed,
      description: form.description
    }
    if (editing.value) {
      await api.put(`/admin/postings/${form.job_id}`, payload)
      ElMessage.success('Posting updated')
    } else {
      await api.post('/admin/postings', payload)
      ElMessage.success('Posting created')
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
    await ElMessageBox.confirm(`Delete posting "${row.title}"?`, 'Delete posting', { type: 'warning', confirmButtonText: 'Delete', confirmButtonClass: 'el-button--danger' })
  } catch { return }
  try {
    await api.delete(`/admin/postings/${row.job_id}`)
    ElMessage.success('Posting deleted')
    if (rows.value.length === 1 && page.value > 1) page.value -= 1
    load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(async () => {
  load()
  try {
    const dash = await api.get('/analytics/dashboard')
    categories.value = (dash.categories || []).map((c) => c.name)
  } catch { /* non-fatal */ }
})
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
