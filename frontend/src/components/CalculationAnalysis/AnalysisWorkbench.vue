<template>
  <Teleport to="body">
    <div v-if="visible" class="ca-mask" @click.self="handleClose">
      <div class="ca-dialog">
        <!-- 顶部工具栏 -->
        <header class="ca-header">
          <div class="ca-brand">
            <span class="ca-brand__logo">CALC</span>
            <div class="ca-brand__text">
              <div class="ca-brand__main">计算链智能分析</div>
              <div class="ca-brand__sub">Calculation Chain Analysis</div>
            </div>
          </div>

          <div class="ca-target">
            <span class="ca-target__label">目标结果节点</span>
            <el-select
              v-model="targetNode"
              size="small"
              class="ca-target__select"
              popper-class="ca-popper"
              :loading="loadingChain"
              @change="handleTargetChange"
            >
              <el-option
                v-for="t in availableTargets"
                :key="t.name"
                :label="`${t.name}${t.unit ? ' [' + t.unit + ']' : ''}`"
                :value="t.name"
              />
            </el-select>
          </div>

          <div class="ca-header-actions">
            <el-button
              class="ca-btn-run"
              type="primary"
              size="small"
              :loading="loadingRun"
              @click="runAnalysis"
            >
              <el-icon class="ca-btn-run__icon"><VideoPlay /></el-icon>
              执行分析
            </el-button>
            <el-button class="ca-btn-ghost" size="small" @click="handleClose">关闭</el-button>
          </div>
        </header>

        <!-- 三栏布局 -->
        <div class="ca-body">
          <aside class="ca-col ca-col--left">
            <ParameterScenario
              :inputs="inputs"
              :scenarios="scenarios"
              :active-key="activeKey"
              :loading="loadingRun"
              @update:scenario="handleScenarioUpdate"
              @select="activeKey = $event"
              @add="addScenario"
              @copy="copyScenario"
              @delete="deleteScenario"
              @run="runAnalysis"
            />
          </aside>

          <main class="ca-col ca-col--center">
            <div class="ca-graph-wrapper">
              <CalculationGraph
                :nodes="chain?.nodes || []"
                :edges="chain?.edges || []"
                :values="displayValues"
                :target-node="targetNode"
                :loading="loadingChain || loadingRun"
                :active-scene-name="activeSceneName"
                :error="chainError"
              />
            </div>
            <!-- 数学趋势分析图：放在中央栏下方，获得更大空间 -->
            <div class="ca-chart-section">
              <ResponseChart
                :model-id="modelId"
                :module-code="moduleCode"
                :target-node="targetNode"
                :inputs="inputs"
                :target-unit="targetUnit"
              />
            </div>
          </main>

          <aside class="ca-col ca-col--right">
            <SensitivityPanel
              :target-node="targetNode"
              :target-unit="targetUnit"
              :sensitivity="sensitivity"
              :scenario-results="sceneResults"
              :loading="loadingRun"
              :active-scene-name="activeSceneName"
              @reload="runAnalysis"
            />
          </aside>
        </div>

        <!-- 底部状态栏 -->
        <footer class="ca-footer">
          <span>目标：{{ targetNode || '—' }}</span>
          <span>输入参数：{{ inputs.length }} 项</span>
          <span>场景：{{ scenarios.length }} 个</span>
          <span class="ca-footer__hint">Esc 关闭 · 参数范围在左侧编辑，影响链与图表自动联动</span>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'
import {
  fetchAnalysisChain,
  fetchAnalysisScenarios,
  fetchAnalysisSensitivity,
} from '../../api/calculationAnalysis'
import ParameterScenario from './ParameterScenario.vue'
import CalculationGraph from './CalculationGraph.vue'
import SensitivityPanel from './SensitivityPanel.vue'
import ResponseChart from './ResponseChart.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  modelId: { type: [String, Number], default: '' },
  moduleCode: { type: String, default: '' },
  baseParams: { type: Object, default: () => ({}) },
  initialTarget: { type: String, default: '' },
})
const emit = defineEmits(['update:visible'])

const targetNode = ref('')
const chain = ref(null)
const inputs = ref([])
const scenarios = ref([])
const activeKey = ref('')
const sceneResults = ref([])
const sensitivity = ref(null)
const loadingChain = ref(false)
const loadingRun = ref(false)
const chainError = ref('')

const availableTargets = computed(() => chain.value?.available_targets || [])

const activeSceneName = computed(
  () => scenarios.value.find((s) => s.key === activeKey.value)?.name || ''
)

const targetUnit = computed(() => {
  const node = chain.value?.nodes?.find((n) => n.name === targetNode.value)
  return node?.unit || ''
})

// 当前展示的节点值：优先取激活场景的计算结果，否则展示基准值
const displayValues = computed(() => {
  const match = sceneResults.value.find((s) => s.name === activeSceneName.value)
  if (match && match.nodes) return match.nodes
  const base = {}
  for (const n of chain.value?.nodes || []) {
    base[n.name] = { value: n.value, unit: n.unit }
  }
  return base
})

const handleClose = () => emit('update:visible', false)

const handleScenarioUpdate = (key, parameters) => {
  const found = scenarios.value.find((s) => s.key === key)
  if (found) found.parameters = parameters
}

const ensureUniqueName = (name) => {
  const names = scenarios.value.map((s) => s.name)
  if (!names.includes(name)) return name
  let i = 2
  while (names.includes(`${name}${i}`)) i += 1
  return `${name}${i}`
}

const addScenario = () => {
  const template = scenarios.value.find((s) => s.key === activeKey.value) || scenarios.value[0]
  const parameters = {}
  for (const inp of inputs.value) {
    parameters[inp.name] = template?.parameters?.[inp.name] ?? inp.value
  }
  const item = {
    key: `sc-${Date.now()}`,
    name: ensureUniqueName('新方案'),
    parameters,
  }
  scenarios.value.push(item)
  activeKey.value = item.key
}

const copyScenario = (key) => {
  const src = scenarios.value.find((s) => s.key === key)
  if (!src) return
  const item = {
    key: `sc-${Date.now()}`,
    name: ensureUniqueName(`${src.name} 副本`),
    parameters: { ...src.parameters },
  }
  scenarios.value.push(item)
  activeKey.value = item.key
}

const deleteScenario = (key) => {
  if (scenarios.value.length <= 1) {
    ElMessage.warning('至少保留一个设计场景')
    return
  }
  const index = scenarios.value.findIndex((s) => s.key === key)
  if (index === -1) return
  scenarios.value.splice(index, 1)
  if (activeKey.value === key) {
    activeKey.value = scenarios.value[Math.min(index, scenarios.value.length - 1)].key
  }
}

const buildDefaultScenarios = () => {
  const base = {}
  const opt = {}
  const lim = {}
  for (const inp of inputs.value) {
    base[inp.name] = inp.value
    opt[inp.name] = inp.max
    lim[inp.name] = inp.max
  }
  scenarios.value = [
    { key: 'sc-base', name: '当前设计', parameters: base },
    { key: 'sc-opt', name: '优化方案', parameters: opt },
    { key: 'sc-lim', name: '极限工况', parameters: lim },
  ]
  activeKey.value = scenarios.value[0].key
}

const loadChain = async () => {
  if (!props.modelId) {
    chainError.value = '未选择计算型号，请先在工作台选择型号'
    return false
  }
  loadingChain.value = true
  chainError.value = ''
  try {
    const res = await fetchAnalysisChain(props.modelId, {
      target_node: targetNode.value || props.initialTarget,
      module_code: props.moduleCode,
    })
    chain.value = res
    if (!targetNode.value && res.target_node) targetNode.value = res.target_node
    inputs.value = (res.inputs || []).map((i) => ({ ...i }))
    buildDefaultScenarios()
    sceneResults.value = []
    sensitivity.value = null
    return true
  } catch (error) {
    chain.value = null
    chainError.value = error?.response?.data?.detail || error?.message || '加载分析模型失败'
    ElMessage.error(chainError.value)
    return false
  } finally {
    loadingChain.value = false
  }
}

const runAnalysis = async () => {
  if (!props.modelId || !targetNode.value) {
    ElMessage.warning('请先选择目标结果节点')
    return
  }
  loadingRun.value = true
  try {
    const [scRes, sensRes] = await Promise.all([
      fetchAnalysisScenarios(props.modelId, {
        target_node: targetNode.value,
        module_code: props.moduleCode,
        scenarios: scenarios.value.map((s) => ({ name: s.name, parameters: s.parameters })),
      }),
      fetchAnalysisSensitivity(props.modelId, {
        target_node: targetNode.value,
        module_code: props.moduleCode,
        inputs: inputs.value.map((i) => ({ name: i.name, min: i.min, max: i.max })),
      }),
    ])
    sceneResults.value = scRes.scenarios || []
    sensitivity.value = sensRes
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '执行分析失败')
  } finally {
    loadingRun.value = false
  }
}

// 选择目标结果节点后：自动重新加载影响链，并自动执行场景/敏感性分析
const handleTargetChange = async () => {
  sceneResults.value = []
  sensitivity.value = null
  const ok = await loadChain()
  if (ok) runAnalysis()
}

const handleKeydown = (e) => {
  if (e.key === 'Escape' && props.visible) handleClose()
}

watch(
  () => props.visible,
  (v) => {
    if (v) {
      targetNode.value = ''
      loadChain().then((ok) => {
        if (ok) runAnalysis()
      })
      window.addEventListener('keydown', handleKeydown)
    } else {
      window.removeEventListener('keydown', handleKeydown)
    }
  }
)

onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown))
</script>

<style>
/* 下拉浮层深色主题（teleport 到 body，需全局样式）
   z-index 必须高于 .ca-mask (3000) 的，否则下拉被 mask 挡住不可见 */
.ca-popper {
  z-index: 3200 !important;
  --el-bg-color-overlay: #1a2130;
  --el-text-color-primary: #d6deeb;
  --el-text-color-regular: #aeb9c9;
  --el-border-color-light: #2a313c;
  --el-fill-color-blank: #1a2130;
}
.ca-popper .el-select-dropdown__item.is-hovering {
  background-color: #232c3d;
}
.ca-popper .el-select-dropdown__item.is-selected {
  color: #ff5a5a;
}
</style>

<style scoped>
.ca-mask {
  position: fixed;
  inset: 0;
  z-index: 3000;
  background: rgba(2, 4, 8, 0.72);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.ca-dialog {
  width: min(1540px, 94vw);
  height: min(880px, 92vh);
  background: #0b0f15;
  border: 1px solid #263041;
  border-radius: 8px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  overflow: hidden;

  /* 局部覆盖 Element Plus 主题变量（深色） */
  --el-bg-color: #111722;
  --el-bg-color-overlay: #1a2130;
  --el-text-color-primary: #d6deeb;
  --el-text-color-regular: #aeb9c9;
  --el-text-color-secondary: #7c8a99;
  --el-border-color: #2a313c;
  --el-border-color-light: #2a313c;
  --el-border-color-lighter: #232b38;
  --el-fill-color-blank: #111722;
  --el-fill-color-light: #1a2130;
  --el-input-bg-color: #111722;
  --el-input-border-color: #2a313c;
  --el-input-hover-border-color: #3d4a5c;
  --el-input-text-color: #d6deeb;
  --el-color-primary: #e23b3b;
  --el-color-primary-light-3: #f05a5a;
  --el-color-primary-light-5: #f47878;
  --el-color-primary-light-7: #5a4a4a;
  --el-color-primary-light-8: #332b2b;
  --el-color-primary-light-9: #221b1b;
  --el-color-primary-dark-2: #c22f2f;
  --el-font-size-base: 12px;
}

/* ---------- 头部 ---------- */
.ca-header {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 10px 14px;
  background: #10151d;
  border-bottom: 1px solid #263041;
  flex-shrink: 0;
}
.ca-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.ca-brand__logo {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  background: linear-gradient(135deg, #e23b3b, #7a1616);
  color: #fff;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ca-brand__main {
  font-size: 15px;
  font-weight: 600;
  color: #e8eef7;
  letter-spacing: 1px;
}
.ca-brand__sub {
  font-size: 10px;
  color: #66748a;
  letter-spacing: 2px;
  text-transform: uppercase;
}
.ca-target {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.ca-target__label {
  font-size: 11px;
  color: #7c8a99;
  white-space: nowrap;
}
.ca-target__select {
  max-width: 320px;
}
.ca-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.ca-btn-run {
  background: #e23b3b;
  border-color: #e23b3b;
  font-weight: 600;
  letter-spacing: 1px;
}
.ca-btn-run__icon {
  margin-right: 2px;
}
.ca-btn-ghost {
  background: transparent;
  border-color: #2a313c;
  color: #aeb9c9;
}

/* ---------- 三栏主体 ---------- */
.ca-body {
  flex: 1;
  display: flex;
  min-height: 0;
}
.ca-col {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.ca-col--left {
  width: 320px;
  flex-shrink: 0;
  border-right: 1px solid #263041;
}
.ca-col--center {
  flex: 1;
  min-width: 0;
  border-right: 1px solid #263041;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.ca-col--right {
  width: 360px;
  flex-shrink: 0;
}

/* 中央栏下部：趋势图区域 */
.ca-graph-wrapper {
  flex: 0 0 45%;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.ca-graph-wrapper > * {
  flex: 1;
  min-height: 0;
}
.ca-chart-section {
  flex: 1;
  min-height: 200px;
  border-top: 1px solid #263041;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.ca-chart-section > * {
  flex: 1;
  min-height: 0;
}

/* ---------- 底部状态栏 ---------- */
.ca-footer {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 6px 14px;
  background: #10151d;
  border-top: 1px solid #263041;
  font-size: 11px;
  color: #7c8a99;
  flex-shrink: 0;
}
.ca-footer__hint {
  margin-left: auto;
  color: #4d5a6d;
}
</style>
