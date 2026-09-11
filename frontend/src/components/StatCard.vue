
<template>
  <div class="stat-cell" :style="{ background: gradient }">
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value tnum">{{ display }}</div>
    <div class="stat-foot">
      <span class="stat-hint">{{ hint || '—' }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  label: String,
  value: [Number, String],
  color: { type: String, default: '#409eff' },
  hint: { type: String, default: '' }
})
const display = computed(() => {
  if (typeof props.value !== 'number') return props.value ?? '—'
  return props.value >= 1000 ? props.value.toLocaleString() : props.value
})
function shade(hex, amt) {
  const c = hex.replace('#', '')
  const f = (i) => {
    const v = Math.round(parseInt(c.slice(i, i + 2), 16) * (1 + amt))
    return Math.max(0, Math.min(255, v)).toString(16).padStart(2, '0')
  }
  return `#${f(0)}${f(2)}${f(4)}`
}
const gradient = computed(() => `linear-gradient(135deg, ${props.color}, ${shade(props.color, -0.26)})`)
</script>

<style scoped>
.stat-cell {
  padding: 20px 22px; border-radius: var(--r); display: flex; flex-direction: column; gap: 10px;
  color: #fff; position: relative; overflow: hidden; box-shadow: 0 4px 14px rgba(0, 21, 41, 0.12);
}
.stat-cell::after {
  content: ""; position: absolute; right: -18px; top: -18px; width: 86px; height: 86px;
  border-radius: 50%; background: rgba(255, 255, 255, 0.14);
}
.stat-label { font-size: 13px; font-weight: 500; color: rgba(255, 255, 255, 0.92); }
.stat-value { font-size: 30px; font-weight: 700; color: #fff; line-height: 1.05; letter-spacing: -0.01em; }
.stat-foot { display: flex; align-items: center; gap: 8px; }
.stat-hint { font-size: 12px; color: rgba(255, 255, 255, 0.85); }
</style>
