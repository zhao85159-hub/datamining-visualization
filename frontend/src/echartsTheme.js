/* Shared ECharts theme — a bright, colourful "dashboard" look (Element-UI
   style): white cards, soft dashed gridlines, colourful series and a
   light-bordered tooltip with a subtle shadow, echoing the blue admin
   reference design. The export keeps the name atlasTheme for compatibility. */

const TEXT = '#606266'
const MUTED = '#909399'
const AXIS = '#dcdfe6'
const SPLIT = '#ebeef5'
const SURFACE = '#ffffff'
const SANS = "'Inter',system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Helvetica,Arial,sans-serif"

export const PALETTE = ['#5b8ff9', '#5ad8a6', '#9270ca', '#f6bd16', '#e8684a', '#6dc8ec', '#ff9d4d', '#5d7092']

export const atlasTheme = {
  color: PALETTE,
  textStyle: { fontFamily: SANS, color: TEXT },
  title: { textStyle: { color: '#303133', fontFamily: SANS } },
  legend: { textStyle: { color: TEXT, fontFamily: SANS, fontSize: 12 }, icon: 'roundRect', itemWidth: 12, itemHeight: 8 },
  grid: { left: 12, right: 16, top: 24, bottom: 12, containLabel: true },
  tooltip: {
    backgroundColor: SURFACE,
    borderColor: SPLIT,
    borderWidth: 1,
    padding: [10, 14],
    textStyle: { color: '#303133', fontFamily: SANS, fontSize: 13 },
    extraCssText: 'border-radius:8px; box-shadow:0 4px 16px rgba(0,21,41,0.12);',
    axisPointer: { type: 'line', lineStyle: { color: '#c0c4cc', width: 1, type: 'dashed' } }
  },
  categoryAxis: {
    axisLine: { lineStyle: { color: AXIS } },
    axisTick: { show: false },
    axisLabel: { color: MUTED, fontFamily: SANS, fontSize: 11 },
    splitLine: { show: false }
  },
  valueAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: MUTED, fontFamily: SANS, fontSize: 11 },
    splitLine: { lineStyle: { color: SPLIT, type: 'dashed' } }
  },
  bar: { itemStyle: { borderRadius: [4, 4, 0, 0] } }
}
