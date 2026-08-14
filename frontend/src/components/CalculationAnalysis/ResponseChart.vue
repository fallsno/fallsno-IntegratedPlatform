<template>
  <div class="rc-panel">
    <!-- 图表模式切换 -->
    <div class="rc-tabs">
      <div
        class="rc-tab"
        :class="{ 'is-active': tab === 'curve' }"
        @click="switchTab('curve')"
      >
        响应曲线
      </div>
      <div
        class="rc-tab"
        :class="{ 'is-active': tab === 'surface' }"
        @click="switchTab('surface')"
      >
        参数响应面
      </div>
    </div>

    <!-- 曲线参数 -->
    <div v-if="tab === 'curve'" class="rc-controls">
      <div class="rc-field">
        <span class="rc-field__label">X 参数</span>
        <el-select v-model="curveParam" size="small" popper-class="ca-popper">
          <el-option v-for="i in inputs" :key="i.name" :label="i.name" :value="i.name" />
        </el-select>
      </div>
      <div class="rc-field rc-field--num">
        <span class="rc-field__label">档位</span>
        <el-input v-model.number="curveSteps" type="number" size="small" min="5" max="41" />
      </div>
      <label class="rc-check">
        <el-checkbox v-model="showIntermediate" size="small" />中间节点
      </label>
      <el-button class="rc-btn" size="small" :loading="chartLoading" @click="loadCurve">
        生成
      </el-button>
    </div>

    <!-- 响应面参数 -->
    <div v-else class="rc-controls rc-controls--surface">
      <div class="rc-field">
        <span class="rc-field__label">X 参数</span>
        <el-select v-model="surfaceParam1" size="small" popper-class="ca-popper">
          <el-option v-for="i in inputs" :key="i.name" :label="i.name" :value="i.name" />
        </el-select>
      </div>
      <div class="rc-field">
        <span class="rc-field__label">Y 参数</span>
        <el-select v-model="surfaceParam2" size="small" popper-class="ca-popper">
          <el-option v-for="i in inputs" :key="i.name" :label="i.name" :value="i.name" />
        </el-select>
      </div>
      <div class="rc-field rc-field--num">
        <span class="rc-field__label">网格</span>
        <el-input v-model.number="surfaceGrid" type="number" size="small" min="5" max="25" />
      </div>
      <el-button class="rc-btn" size="small" :loading="chartLoading" @click="loadSurface">
        生成
      </el-button>
    </div>

    <!-- 图表容器 -->
    <div class="rc-chart-wrap">
      <div ref="chartRef" class="rc-chart" />
      <div v-if="chartLoading" class="rc-chart__loading">计算中…</div>
      <div v-if="!chartLoading && !hasChartData" class="rc-chart__empty">
        {{ emptyHint }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { fetchAnalysisCurve, fetchAnalysisSurface } from '../../api/calculationAnalysis'

const props = defineProps({
  modelId: { type: [String, Number], default: '' },
  moduleCode: { type: String, default: '' },
  targetNode: { type: String, default: '' },
  inputs: { type: Array, default: () => [] },
  targetUnit: { type: String, default: '' },
})

const tab = ref('curve')
const chartRef = ref(null)
let chart = null

const curveParam = ref('')
const curveSteps = ref(21)
const showIntermediate = ref(true)
const curveData = ref(null)

const surfaceParam1 = ref('')
const surfaceParam2 = ref('')
const surfaceGrid = ref(15)
const surfaceData = ref(null)

const chartLoading = ref(false)
const hasChartData = computed(() =>
  tab.value === 'curve' ? !!curveData.value : !!surfaceData.value
)
const emptyHint = computed(() =>
  tab.value === 'curve'
    ? '选择 X 参数后点击「生成」查看响应曲线'
    : '选择两个参数后点击「生成」查看响应面'
)

// 输入参数变化时同步默认选择
watch(
  () => props.inputs,
  (list) => {
    if (!list.length) return
    if (!curveParam.value || !list.find((i) => i.name === curveParam.value)) {
      curveParam.value = list[0].name
    }
    if (!surfaceParam1.value || !list.find((i) => i.name === surfaceParam1.value)) {
      surfaceParam1.value = list[0].name
    }
    const second = list.find((i) => i.name !== surfaceParam1.value) || list[1]
    if (!surfaceParam2.value || !list.find((i) => i.name === surfaceParam2.value)) {
      surfaceParam2.value = second ? second.name : ''
    }
  },
  { immediate: true, deep: true }
)

// 目标节点切换时清空图表
watch(
  () => props.targetNode,
  () => {
    curveData.value = null
    surfaceData.value = null
    renderChart()
  }
)

const ensureChart = async () => {
  await nextTick()
  if (!chart && chartRef.value) {
    chart = echarts.init(chartRef.value)
    chart.setOption({
      backgroundColor: 'transparent',
      textStyle: { color: '#8b98a8', fontSize: 10 },
    })
  }
  return chart
}

const DARK_TEXT = '#aeb9c9'
const AXIS_LINE = '#2a313c'

const baseGrid = () => ({ left: 44, right: 14, top: 30, bottom: 42, containLabel: true })

const loadCurve = async () => {
  if (!props.modelId || !props.targetNode || !curveParam.value) return
  chartLoading.value = true
  try {
    const inp = props.inputs.find((i) => i.name === curveParam.value)
    const data = await fetchAnalysisCurve(props.modelId, {
      target_node: props.targetNode,
      module_code: props.moduleCode,
      param: curveParam.value,
      min: inp?.min,
      max: inp?.max,
      steps: curveSteps.value,
      track_intermediate: showIntermediate.value,
    })
    curveData.value = data
    renderChart()
    setTimeout(() => { if (chart) chart.resize() }, 100)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '生成响应曲线失败')
  } finally {
    chartLoading.value = false
  }
}

const loadSurface = async () => {
  if (!props.modelId || !props.targetNode || !surfaceParam1.value || !surfaceParam2.value) {
    ElMessage.warning('请选择两个不同的参数')
    return
  }
  if (surfaceParam1.value === surfaceParam2.value) {
    ElMessage.warning('响应面的两个参数不能相同')
    return
  }
  chartLoading.value = true
  try {
    const p1 = props.inputs.find((i) => i.name === surfaceParam1.value)
    const p2 = props.inputs.find((i) => i.name === surfaceParam2.value)
    const data = await fetchAnalysisSurface(props.modelId, {
      target_node: props.targetNode,
      module_code: props.moduleCode,
      param1: surfaceParam1.value,
      param2: surfaceParam2.value,
      range1: { min: p1?.min, max: p1?.max },
      range2: { min: p2?.min, max: p2?.max },
      grid: surfaceGrid.value,
    })
    surfaceData.value = data
    renderChart()
    // 弹窗动画完成后 resize，确保 canvas 有实际尺寸
    setTimeout(() => { if (chart) chart.resize() }, 150)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '生成响应面失败')
  } finally {
    chartLoading.value = false
  }
}

const axisStyle = () => ({
  axisLine: { lineStyle: { color: AXIS_LINE } },
  axisLabel: { color: DARK_TEXT, fontSize: 10 },
  splitLine: { lineStyle: { color: '#1f2833' } },
})

const renderChart = async () => {
  const inst = await ensureChart()
  if (!inst) return

  const unit = props.targetUnit
  const suffix = unit ? ` ${unit}` : ''

  if (tab.value === 'curve') {
    if (!curveData.value) {
      inst.clear()
      return
    }
    const d = curveData.value
    const series = [
      {
        name: d.target_node + suffix,
        type: 'line',
        data: d.x.map((x, i) => [x, d.y[i]]),
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2, color: '#e23b3b' },
        itemStyle: { color: '#e23b3b' },
        z: 3,
      },
    ]
    const colors = ['#3b82f6', '#22c55e', '#eab308', '#a855f7', '#06b6d4', '#f97316']
    ;(d.series || []).forEach((s, idx) => {
      series.push({
        name: s.name,
        type: 'line',
        data: d.x.map((x, i) => [x, s.values[i]]),
        symbol: 'none',
        lineStyle: { width: 1, color: colors[idx % colors.length], type: 'dashed', opacity: 0.7 },
        itemStyle: { color: colors[idx % colors.length] },
        z: 1,
      })
    })
    inst.setOption(
      {
        animation: false,
        color: ['#e23b3b'],
        tooltip: {
          trigger: 'axis',
          backgroundColor: '#141b26',
          borderColor: '#2a313c',
          textStyle: { color: '#d6deeb', fontSize: 11 },
          valueFormatter: (v) => (v === null || v === undefined ? '—' : Number(v).toPrecision(5)),
        },
        legend: {
          show: series.length > 1,
          type: 'scroll',
          top: 0,
          textStyle: { color: DARK_TEXT, fontSize: 10 },
          pageTextStyle: { color: DARK_TEXT },
        },
        grid: baseGrid(),
        xAxis: {
          type: 'value',
          name: `${d.param}`,
          ...axisStyle(),
          nameTextStyle: { color: DARK_TEXT, fontSize: 10 },
        },
        yAxis: {
          type: 'value',
          name: d.target_node + suffix,
          scale: true,
          ...axisStyle(),
          nameTextStyle: { color: DARK_TEXT, fontSize: 10 },
        },
        series,
      },
      true
    )
    return
  }

  // 响应面（heatmap）
  if (!surfaceData.value) {
    inst.clear()
    return
  }
  const d = surfaceData.value
  const data = []
  for (let i = 0; i < d.x.length; i += 1) {
    for (let j = 0; j < d.y.length; j += 1) {
      const v = d.z?.[i]?.[j]
      data.push([d.x[i], d.y[j], v])
    }
  }
  const values = data.map((item) => item[2]).filter((v) => typeof v === 'number')
  const vMin = Math.min(...values)
  const vMax = Math.max(...values)
  inst.setOption(
    {
      animation: false,
      tooltip: {
        position: 'top',
        backgroundColor: '#141b26',
        borderColor: '#2a313c',
        textStyle: { color: '#d6deeb', fontSize: 11 },
        formatter: (params) => {
          const [x, y, z] = params.value
          return `${d.param1}=${Number(x).toPrecision(4)}<br/>${d.param2}=${Number(y).toPrecision(4)}<br/><b style="color:#ff5a5a">${d.target_node} = ${Number(z).toPrecision(5)}</b>${suffix}`
        },
      },
      grid: baseGrid(),
      xAxis: {
        type: 'value',
        name: d.param1,
        ...axisStyle(),
        nameTextStyle: { color: DARK_TEXT, fontSize: 10 },
      },
      yAxis: {
        type: 'value',
        name: d.param2,
        ...axisStyle(),
        nameTextStyle: { color: DARK_TEXT, fontSize: 10 },
      },
      visualMap: {
        min: vMin,
        max: vMax,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: 2,
        itemWidth: 10,
        itemHeight: 60,
        textStyle: { color: DARK_TEXT, fontSize: 9 },
        inRange: { color: ['#0d47a1', '#00bcd4', '#4caf50', '#ffeb3b', '#ff5722'] },
      },
      series: [
        {
          name: d.target_node,
          type: 'heatmap',
          data,
          progressive: 2000,
          emphasis: { itemStyle: { borderColor: '#e23b3b', borderWidth: 1 } },
        },
      ],
    },
    true
  )
}

const switchTab = (next) => {
  tab.value = next
  renderChart()
  // 弹窗动画完成后 resize
  setTimeout(() => { if (chart) chart.resize() }, 100)
}

let resizeObserver = null

const handleResize = () => {
  if (chart) chart.resize()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  // 用 ResizeObserver 监控容器实际尺寸变化，替代 setTimeout 猜测
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      if (chart) chart.resize()
    })
    resizeObserver.observe(chartRef.value)
  }
  renderChart()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.rc-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
}
.rc-tabs {
  display: flex;
  border-bottom: 1px solid #1f2833;
  flex-shrink: 0;
}
.rc-tab {
  flex: 1;
  text-align: center;
  padding: 6px 0;
  font-size: 11px;
  color: #7c8a99;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  letter-spacing: 0.5px;
}
.rc-tab:hover {
  color: #aeb9c9;
}
.rc-tab.is-active {
  color: #ff5a5a;
  border-bottom-color: #e23b3b;
  font-weight: 600;
}

.rc-controls {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  padding: 6px 10px;
  border-bottom: 1px solid #1f2833;
  flex-shrink: 0;
}
.rc-controls--surface {
  flex-wrap: nowrap;
}
.rc-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 60px;
  max-width: 160px;
}
.rc-field--num {
  flex: 0 0 56px;
  max-width: 56px;
}
.rc-field__label {
  font-size: 9px;
  color: #5d6a7c;
}
.rc-field :deep(.el-select) {
  width: 100%;
}
.rc-field :deep(.el-input__inner) {
  font-size: 11px;
  text-align: center;
  padding: 0 4px;
}
/* 隐藏数字输入框的上下箭头，节省空间 */
.rc-field :deep(input[type="number"])::-webkit-inner-spin-button,
.rc-field :deep(input[type="number"])::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.rc-field :deep(input[type="number"]) {
  -moz-appearance: textfield;
}
.rc-check {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  color: #7c8a99;
  flex-shrink: 0;
  padding-bottom: 4px;
  padding-left: 4px;
  min-width: 72px;
}
.rc-check :deep(.el-checkbox__label) {
  font-size: 10px;
  color: #7c8a99;
}
.rc-btn {
  background: #1a2130;
  border-color: #3d4a5c;
  color: #d6deeb;
  flex-shrink: 0;
}
.rc-btn:hover {
  border-color: #e23b3b;
  color: #ff8a8a;
  background: #241216;
}

.rc-chart-wrap {
  flex: 1;
  position: relative;
  min-height: 180px;
}
.rc-chart {
  position: absolute;
  inset: 0;
}
.rc-chart__loading,
.rc-chart__empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #4d5a6d;
  pointer-events: none;
}
</style>
