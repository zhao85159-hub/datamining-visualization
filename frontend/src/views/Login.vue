<template>
  <div class="auth-wrap">
    <div class="auth-card rise">
      <div class="auth-brand">
        <div class="logo">G</div>
        <div>
          <div class="auth-word">Graduate Recruitment</div>
          <div class="auth-kicker">LinkedIn job data · analytics &amp; management</div>
        </div>
      </div>

      <h2 class="auth-title">{{ mode === 'login' ? 'Sign in' : 'Register' }}</h2>

      <el-form @submit.prevent="submit" class="form">
        <label class="fld-label">Username</label>
        <el-input v-model="form.username" placeholder="Enter your username" :prefix-icon="User" size="large" />
        <label class="fld-label">Password</label>
        <el-input v-model="form.password" type="password" placeholder="Enter your password" :prefix-icon="Lock"
                  size="large" show-password @keyup.enter="submit" />
        <el-button type="primary" size="large" class="submit" :loading="loading" @click="submit">
          {{ mode === 'login' ? 'Sign in' : 'Create account' }}
        </el-button>
      </el-form>

      <div class="switch">
        <span v-if="mode === 'login'">Don't have an account? <a @click="mode = 'register'">Register</a></span>
        <span v-else>Already have an account? <a @click="mode = 'login'">Back to sign in</a></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const mode = ref('login')
const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function submit() {
  if (!form.username || !form.password) return ElMessage.warning('Please enter a username and password')
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(form.username, form.password)
      ElMessage.success('Signed in — welcome back')
      const redirect = route.query.redirect
      router.push(redirect || (auth.isAdmin ? '/admin/overview' : '/dashboard'))
    } else {
      await auth.register(form.username, form.password)
      ElMessage.success('Registered successfully, please sign in')
      mode.value = 'login'
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap { min-height: 100vh; display: grid; place-items: center; padding: 24px; background: linear-gradient(135deg, #e8f1ff 0%, #f0f2f5 60%); }
.auth-card { width: 100%; max-width: 410px; background: #fff; border-radius: 12px; box-shadow: 0 12px 40px rgba(0, 21, 41, 0.14); padding: 34px 32px 28px; }

.auth-brand { display: flex; align-items: center; gap: 12px; justify-content: center; margin-bottom: 8px; }
.auth-brand .logo { width: 42px; height: 42px; border-radius: 10px; background: linear-gradient(135deg, #409eff, #764ba2); color: #fff; display: grid; place-items: center; font-size: 22px; font-weight: 700; }
.auth-word { font-size: 17px; font-weight: 700; color: var(--ink-900); }
.auth-kicker { font-size: 11px; color: var(--ink-400); margin-top: 2px; }

.auth-title { text-align: center; font-size: 26px; font-weight: 700; color: var(--ink-900); margin: 14px 0 22px; }

.form { display: flex; flex-direction: column; }
.fld-label { font-size: 13px; color: var(--ink-600); margin: 0 0 7px; }
.form .el-input { margin-bottom: 18px; }
.submit { width: 100%; margin-top: 8px; height: 44px; font-weight: 600; letter-spacing: 2px; }

.switch { margin-top: 18px; text-align: center; color: var(--ink-500); font-size: 13.5px; }
.switch a { cursor: pointer; font-weight: 600; }
</style>
