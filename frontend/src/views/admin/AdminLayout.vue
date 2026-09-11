<template>
  <div class="admin-shell">
    <aside class="side">
      <div class="side-brand">
        <div class="mono-mark">LM</div>
        <div>
          <div class="side-word">Admin Console</div>
          <div class="side-kicker">Management tier</div>
        </div>
      </div>

      <nav class="side-nav">
        <div class="nav-group">Operations</div>
        <router-link
          v-for="l in links" :key="l.to" :to="l.to" class="nav-link"
          :class="{ active: route.path === l.to }">
          <el-icon class="nav-ico"><component :is="l.icon" /></el-icon>
          <span>{{ l.label }}</span>
        </router-link>
      </nav>

      <div class="side-foot">
        <router-link to="/dashboard" class="back-link">
          <el-icon><Back /></el-icon> View public site
        </router-link>
        <div class="user-card">
          <div class="uc-avatar">{{ initial }}</div>
          <div class="uc-meta">
            <span class="uc-name">{{ auth.user?.username }}</span>
            <span class="uc-role">{{ auth.user?.role }}</span>
          </div>
          <button class="uc-out" title="Sign out" @click="logout"><el-icon><SwitchButton /></el-icon></button>
        </div>
      </div>
    </aside>

    <div class="admin-main">
      <div class="admin-top">
        <div class="crumb">
          <span class="crumb-root">Admin</span>
          <span class="crumb-sep">/</span>
          <span class="crumb-leaf">{{ current }}</span>
        </div>
        <div class="env-note"><span class="dot"></span> Management session</div>
      </div>
      <main class="admin-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in"><component :is="Component" /></transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataLine, User, Briefcase, OfficeBuilding, Back, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '../../store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const links = [
  { to: '/admin/overview', label: 'Overview', icon: DataLine },
  { to: '/admin/users', label: 'Users', icon: User },
  { to: '/admin/postings', label: 'Job Postings', icon: Briefcase },
  { to: '/admin/companies', label: 'Companies', icon: OfficeBuilding }
]

const current = computed(() => links.find((l) => l.to === route.path)?.label || 'Overview')
const initial = computed(() => (auth.user?.username || '?').charAt(0).toUpperCase())

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-shell { display: flex; height: 100vh; overflow: hidden; background: var(--canvas); }

/* ---------- Sidebar: flat ink panel ---------- */
.side {
  width: 248px; flex-shrink: 0; height: 100%;
  background: var(--ink-900); color: #e8e4d8;
  display: flex; flex-direction: column;
  border-right: 3px solid var(--clay);
}
.side-brand { display: flex; align-items: center; gap: 12px; padding: 22px 22px 20px; border-bottom: 1px solid rgba(255,255,255,0.08); }
.mono-mark {
  width: 40px; height: 40px; flex-shrink: 0; display: grid; place-items: center;
  background: #e8e4d8; color: var(--ink-900);
  font-family: var(--serif); font-weight: 600; font-size: 18px;
}
.side-word { font-family: var(--serif); font-size: 18px; font-weight: 600; color: #fbfaf6; line-height: 1.1; }
.side-kicker { font-family: var(--mono); font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase; color: #9a9384; margin-top: 3px; }

.side-nav { padding: 18px 14px; flex: 1; overflow-y: auto; }
.nav-group { font-family: var(--mono); font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase; color: #7c7666; padding: 0 10px 10px; }
.nav-link {
  display: flex; align-items: center; gap: 11px;
  padding: 10px 12px; margin-bottom: 2px; border-radius: var(--r-sm);
  color: #c2bbab; font-size: 14px; font-weight: 500;
  border-left: 2px solid transparent; transition: background 0.14s, color 0.14s;
}
.nav-link:hover { background: rgba(255,255,255,0.05); color: #fbfaf6; }
.nav-link.active { background: rgba(255,255,255,0.08); color: #fff; border-left-color: var(--clay); }
.nav-ico { font-size: 16px; }

.side-foot { padding: 14px; border-top: 1px solid rgba(255,255,255,0.08); }
.back-link {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px; margin-bottom: 12px;
  color: #9a9384; font-family: var(--mono); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase;
  border: none; transition: color 0.14s;
}
.back-link:hover { color: #fbfaf6; border-bottom-color: transparent; }
.user-card { display: flex; align-items: center; gap: 10px; padding: 10px; background: rgba(255,255,255,0.04); border-radius: var(--r-sm); }
.uc-avatar { width: 34px; height: 34px; flex-shrink: 0; display: grid; place-items: center; background: var(--clay); color: #fff; font-weight: 600; font-size: 15px; border-radius: 50%; }
.uc-meta { display: flex; flex-direction: column; line-height: 1.25; min-width: 0; flex: 1; }
.uc-name { font-weight: 600; color: #fbfaf6; font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.uc-role { font-family: var(--mono); font-size: 9.5px; letter-spacing: 0.1em; text-transform: uppercase; color: #9a9384; }
.uc-out { background: none; border: none; color: #9a9384; cursor: pointer; font-size: 16px; display: grid; place-items: center; padding: 4px; }
.uc-out:hover { color: var(--clay); }

/* ---------- Main ---------- */
.admin-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.admin-top {
  flex-shrink: 0; height: 56px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 32px; background: var(--surface); border-bottom: 1px solid var(--line-strong);
}
.crumb { font-family: var(--mono); font-size: 12px; display: flex; align-items: center; gap: 8px; }
.crumb-root { color: var(--ink-400); text-transform: uppercase; letter-spacing: 0.08em; }
.crumb-sep { color: var(--ink-300); }
.crumb-leaf { color: var(--ink-800); font-weight: 600; }
.env-note { display: flex; align-items: center; gap: 7px; font-family: var(--mono); font-size: 11px; color: var(--ink-400); letter-spacing: 0.04em; }
.env-note .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ok); }

.admin-content { flex: 1; overflow-y: auto; }

@media (max-width: 860px) {
  .side { width: 64px; }
  .side-word, .side-kicker, .nav-group, .nav-link span, .uc-meta, .back-link span { display: none; }
  .nav-link { justify-content: center; }
}
</style>
