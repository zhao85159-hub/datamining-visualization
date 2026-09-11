import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

const routes = [
  { path: '/', redirect: '/dashboard' },

  // ----- Public / user tier (browse + analytics, read-only) -----
  { path: '/dashboard', name: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: 'Dashboard' } },
  { path: '/postings', name: 'postings', component: () => import('../views/Postings.vue'), meta: { title: 'Job Postings' } },
  { path: '/postings/:id', name: 'posting-detail', component: () => import('../views/PostingDetail.vue'), meta: { title: 'Posting Detail' } },
  { path: '/companies', name: 'companies', component: () => import('../views/Companies.vue'), meta: { title: 'Companies' } },
  { path: '/companies/:id', name: 'company-detail', component: () => import('../views/CompanyDetail.vue'), meta: { title: 'Company Detail' } },
  { path: '/skills', name: 'skills', component: () => import('../views/Skills.vue'), meta: { title: 'Skills & Analytics' } },
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { title: 'Sign in' } },

  // ----- Admin / management tier (CRUD + user administration) -----
  { path: '/admin', redirect: '/admin/overview' },
  { path: '/admin/overview', name: 'admin-overview', component: () => import('../views/admin/AdminOverview.vue'), meta: { title: 'Admin · Overview', requiresAdmin: true } },
  { path: '/admin/users', name: 'admin-users', component: () => import('../views/admin/AdminUsers.vue'), meta: { title: 'Admin · Users', requiresAdmin: true } },
  { path: '/admin/postings', name: 'admin-postings', component: () => import('../views/admin/AdminPostings.vue'), meta: { title: 'Admin · Postings', requiresAdmin: true } },
  { path: '/admin/companies', name: 'admin-companies', component: () => import('../views/admin/AdminCompanies.vue'), meta: { title: 'Admin · Companies', requiresAdmin: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Gate the management tier: only administrators may enter /admin/*.
router.beforeEach((to) => {
  if (to.meta.requiresAdmin) {
    const auth = useAuthStore()
    if (!auth.isAuthenticated) return { name: 'login', query: { redirect: to.fullPath } }
    if (!auth.isAdmin) return { name: 'dashboard' }
  }
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} | Graduate Recruitment Platform` : 'Graduate Recruitment Platform'
})

export default router
