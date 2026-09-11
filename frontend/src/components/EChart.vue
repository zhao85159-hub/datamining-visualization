<template>
  <div ref="el" class="chart"></div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { atlasTheme } from '../echartsTheme'

let registered = false
if (!registered) { echarts.registerTheme('atlas', atlasTheme); registered = true }

const props = defineProps({
  option: { type: Object, required: true },
  loading: { type: Boolean, default: false }
})
const el = ref(null)
let chart = null
let ro = null

function render() {
  if (!chart && el.value) {
    chart = echarts.init(el.value, 'atlas', { renderer: 'canvas' })
  }
  if (chart) {
    chart.setOption(props.option, true)
    props.loading
      ? chart.showLoading({ text: '', maskColor: 'rgba(255,255,255,0.6)', spinnerRadius: 8, lineWidth: 2, color: '#409eff' })
      : chart.hideLoading()
  }
}
function resize() { chart && chart.resize() }

onMounted(() => {
  render()
  window.addEventListener('resize', resize)
  if (window.ResizeObserver && el.value) {
    ro = new ResizeObserver(() => nextTick(resize))
    ro.observe(el.value)
  }
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  ro && ro.disconnect()
  chart && chart.dispose()
})
watch(() => props.option, render, { deep: true })
watch(() => props.loading, render)
</script>
