<template>
  <!-- Admin console: standalone management frame -->
  <AdminLayout v-if="layout === 'admin'" />

  <!-- Login page: full screen, no frame -->
  <router-view v-else-if="layout === 'bare'" />

  <!-- Public / user tier: top blue bar + left menu -->
  <div v-else class="app-shell">
    <header class="topbar">
      <div class="flex" style="gap:0">
        <button class="menu-toggle" aria-label="Menu" @click="sideOpen = !sideOpen">☰</button>
        <div class="brand" @click="$router.push('/dashboard')">
          <div class="logo">G</div>
          <div class="wordmark">Graduate Recruitment</div>
        </div>
        <nav class="top-nav">
          <router-link to="/dashboard">Dashboard</router-link>
          <router-link to="/postings">Jobs</router-link>
        </nav>
      </div>

      <div class="account">
        <template v-if="auth.isAuthenticated">
          <button v-if="auth.isAdmin" class="top-btn" @click="$router.push('/admin')">Admin</button>
          <div class="who">
            <span class="avatar">{{ initial }}</span>
            <span class="who-name">{{ auth.user?.username }}</span>
          </div>
          <button class="top-btn" @click="logout">Sign out</button>
        </template>
        <button v-else class="top-btn" @click="$router.push('/login')">Sign in</button>
      </div>
    </header>

    <aside class="sidebar" :class="{ open: sideOpen }" @click="sideOpen = false">
      <div class="side-group">Navigation</div>
      <router-link
        v-for="t in tabs" :key="t.to" :to="t.to"
        class="side-link" :class="{ active: activeTab === t.to }">
        <el-icon><component :is="t.icon" /></el-icon><span>{{ t.label }}</span>
      </router-link>
      <template v-if="auth.isAdmin">
        <div class="side-group">Management</div>
        <router-link to="/admin" class="side-link">
          <el-icon><Setting /></el-icon><span>Admin Console</span>
        </router-link>
      </template>
    </aside>

    <main class="app-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in"><component :is="Component" /></transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Histogram, Briefcase, OfficeBuilding, DataAnalysis, Setting } from '@element-plus/icons-vue'
import { useAuthStore } from './store/auth'
import AdminLayout from './views/admin/AdminLayout.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const sideOpen = ref(false)

const layout = computed(() => {
  if (route.path.startsWith('/admin')) return 'admin'
  if (route.name === 'login') return 'bare'
  return 'public'
})

const tabs = [
  { to: '/dashboard', label: 'Dashboard', icon: Histogram },
  { to: '/postings', label: 'Job Postings', icon: Briefcase },
  { to: '/companies', label: 'Companies', icon: OfficeBuilding },
  { to: '/skills', label: 'Skills & Analytics', icon: DataAnalysis }
]
const activeTab = computed(() => '/' + (route.path.split('/')[1] || 'dashboard'))
const initial = computed(() => (auth.user?.username || 'G').charAt(0).toUpperCase())

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
