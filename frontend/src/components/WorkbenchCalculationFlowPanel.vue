<template>
  <div class="a-flow-view workbench-flow">
    <div v-if="hasGraph" ref="viewportRef" class="workbench-flow__viewport">
      <div class="workbench-flow__zoom-controls">
        <button type="button" class="workbench-flow__zoom-btn" @click="zoomIn">+</button>
        <div class="workbench-flow__zoom-level">{{ Math.round(viewState.scale * 100) }}%</div>
        <button type="button" class="workbench-flow__zoom-btn" @click="zoomOut">-</button>
        <button type="button" class="workbench-flow__zoom-btn" @click="fitViewport">o</button>
      </div>

      <div
        ref="surfaceRef"
        class="workbench-flow__surface"
        :class="{ 'is-dragging': dragState.active }"
        @click.self="handleSurfaceBlankClick"
        @pointerdown="handleSurfacePointerDown"
        @wheel.prevent="handleWheel"
      >
        <div
          class="workbench-flow__scene"
          :style="sceneTransformStyle"
        >
          <div
            v-for="band in layoutState.bands"
            :key="band.key"
            class="workbench-flow__band"
            :class="`is-${band.key}`"
            :style="resolveBandStyle(band)"
          >
            <span class="workbench-flow__band-label">{{ band.label }}</span>
          </div>

          <svg
            v-if="layoutState.edges.length"
            class="workbench-flow__connectors"
            :viewBox="`0 0 ${layoutState.width} ${layoutState.height}`"
          >
            <defs>
              <marker
                id="workbench-flow-arrow"
                markerWidth="12"
                markerHeight="12"
                refX="9"
                refY="6"
                orient="auto"
                markerUnits="strokeWidth"
              >
                <path d="M 0 0 L 12 6 L 0 12 z" fill="context-stroke" />
              </marker>
            </defs>

            <path
              v-for="edge in layoutState.edges"
              :key="edge.id"
              class="workbench-flow__connector"
              :class="{
                'is-active': edge.isActive,
                'is-muted': edge.isMuted,
                'is-input': edge.sourceLayer === 'input',
                'is-result': edge.targetLayer === 'output'
              }"
              :d="edge.d"
              :style="{ stroke: edge.color }"
              marker-end="url(#workbench-flow-arrow)"
            />
          </svg>

          <button
            v-for="node in layoutState.nodes"
            :key="node.id"
            type="button"
            class="flow-node"
            :class="[
              `is-${node.visualClass}`,
              getNodeStateClass(node),
              {
                'is-main-spine': node.isPrimarySpine,
                'is-shared-node': node.isShared,
                'is-primary-result': node.isPrimaryResult
              }
            ]"
            :style="resolveNodeStyle(node)"
            @pointerdown.stop
            @click.stop="handleNodeClick(node)"
          >
            <div class="flow-node__title">{{ node.title || node.name || '未命名节点' }}</div>
            <div class="flow-node__value">{{ formatMetricText(node.value, node.unitCode) }}</div>
          </button>
        </div>
      </div>
    </div>

    <div v-else class="workbench-flow__empty">
      <div class="empty-icon">链路</div>
      <div class="empty-title">暂无设计链路数据</div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  buildFocusStructureState,
  buildStructureFlowModel,
  buildVisibleStructureEdges,
  buildVisibleStructureNodeIds
} from '@/components/workbench/workbenchFlowStructure.mjs'

const props = defineProps({
  graph: {
    type: Object,
    default: () => ({
      nodes: [],
      edges: [],
      stepCount: 0,
      resultCount: 0,
      ruleCount: 0,
      paramCount: 0
    })
  },
  selectedNodeId: {
    type: String,
    default: ''
  },
  viewportState: {
    type: Object,
    default: () => ({
      zoom: 1,
      center: ['50%', '50%']
    })
  },
  displayMode: {
    type: String,
    default: 'default'
  },
  viewportResetToken: {
    type: Number,
    default: 0
  },
  showInputLayer: {
    type: Boolean,
    default: true
  },
  showCalculationLayer: {
    type: Boolean,
    default: true
  },
  showOutputLayer: {
    type: Boolean,
    default: true
  },
  inputLayerTitle: {
    type: String,
    default: '输入带 / 外部条件'
  },
  calculationLayerTitle: {
    type: String,
    default: '共享主干 / 关键承接'
  },
  outputLayerTitle: {
    type: String,
    default: '结果带 / 模块终点'
  }
})

const emit = defineEmits(['select-node', 'viewport-change'])

const viewportRef = ref(null)
const surfaceRef = ref(null)
const viewportSize = ref({ width: 0, height: 0 })
const viewState = ref({ scale: 1, x: 0, y: 0 })
const dragState = ref({
  active: false,
  startPointerX: 0,
  startPointerY: 0,
  startX: 0,
  startY: 0
})

let resizeObserver = null
let lastLayoutSignature = ''

const NODE_SIZE_MAP = {
  base: { width: 152, height: 78 },
  product: { width: 152, height: 78 },
  environment: { width: 152, height: 78 },
  reference: { width: 152, height: 78 },
  shared: { width: 186, height: 94 },
  calculation: { width: 176, height: 90 },
  result: { width: 204, height: 108 }
}

const LANE_PATTERN = [0, -1, 1, -2, 2, -3, 3]

const hasGraph = computed(() =>
  Array.isArray(props.graph?.nodes) && props.graph.nodes.length > 0 && Array.isArray(props.graph?.edges)
)

const processedGraph = computed(() => buildStructureFlowModel(props.graph))
const focusState = computed(() => buildFocusStructureState(processedGraph.value, props.selectedNodeId))

function isLayerVisible(layer) {
  if (layer === 'input') return props.showInputLayer
  if (layer === 'calculation') return props.showCalculationLayer
  if (layer === 'output') return props.showOutputLayer
  return true
}

const visibleNodeIds = computed(() => buildVisibleStructureNodeIds(processedGraph.value))

const visibleNodes = computed(() =>
  processedGraph.value.nodes.filter((node) => visibleNodeIds.value.has(node.id) && isLayerVisible(node.layer))
)

const visibleEdges = computed(() =>
  buildVisibleStructureEdges(processedGraph.value)
    .filter((edge) => isLayerVisible(edge.sourceLayer) && isLayerVisible(edge.targetLayer))
)

function formatMetricText(value = '', unitCode = '') {
  const text = String(value ?? '').trim()
  if (!text) {
    return unitCode ? `- ${unitCode}` : '-'
  }
  return unitCode ? `${text} ${unitCode}` : text
}

function getNodeStateClass(node) {
  const state = focusState.value.nodeStates.get(node.id) || 'default'
  return state === 'default' ? '' : `is-${state}`
}

function resolveNodeVisualClass(node = {}) {
  if (node.layer === 'output') {
    return 'result'
  }
  if (node.layer === 'input' && node.semanticRole === 'reference') {
    return 'reference'
  }
  if (node.layer === 'input' && node.semanticRole === 'product') {
    return 'product'
  }
  if (node.layer === 'input' && node.semanticRole === 'environment') {
    return 'environment'
  }
  if (node.layer === 'input') {
    return 'base'
  }
  if (node.isPrimarySpine || node.isShared) {
    return 'shared'
  }
  return 'calculation'
}

function resolveNodePalette(visualClass = '') {
  if (visualClass === 'base') {
    return {
      fill: '#739cf2',
      stroke: '#4e7fe8',
      text: '#ffffff'
    }
  }
  if (visualClass === 'product') {
    return {
      fill: '#3b82f6', // Blue for product
      stroke: '#2563eb',
      text: '#ffffff'
    }
  }
  if (visualClass === 'environment') {
    return {
      fill: '#10b981', // Green for environment
      stroke: '#059669',
      text: '#ffffff'
    }
  }
  if (visualClass === 'reference') {
    return {
      fill: '#a683ef',
      stroke: '#8358dd',
      text: '#ffffff'
    }
  }
  if (visualClass === 'shared') {
    return {
      fill: '#56c9c4',
      stroke: '#209d9f',
      text: '#ffffff'
    }
  }
  if (visualClass === 'result') {
    return {
      fill: '#ffc857',
      stroke: '#ebaa14',
      text: '#5e3a00'
    }
  }
  return {
    fill: '#6cdcb7',
    stroke: '#31bf95',
    text: '#ffffff'
  }
}

function buildNodeMetrics(node = {}) {
  const visualClass = resolveNodeVisualClass(node)
  const preset = NODE_SIZE_MAP[visualClass] || NODE_SIZE_MAP.calculation
  const title = String(node.title || node.name || '')
  const value = formatMetricText(node.value, node.unitCode)
  const widthFromTitle = title.length * (visualClass === 'result' ? 13 : 11) + 72
  const widthFromValue = value.length * (visualClass === 'result' ? 10 : 9) + 60
  const width = Math.max(preset.width, Math.min(widthFromTitle > widthFromValue ? widthFromTitle : widthFromValue, 260))
  const height = visualClass === 'result' ? 108 : visualClass === 'shared' ? 96 : preset.height
  return {
    width,
    height,
    visualClass,
    palette: resolveNodePalette(visualClass)
  }
}

function buildAdjacency(nodes = [], edges = []) {
  const upstreamMap = new Map()
  const downstreamMap = new Map()
  nodes.forEach((node) => {
    upstreamMap.set(node.id, [])
    downstreamMap.set(node.id, [])
  })
  edges.forEach((edge) => {
    if (!upstreamMap.has(edge.target) || !downstreamMap.has(edge.source)) {
      return
    }
    upstreamMap.get(edge.target).push(edge.source)
    downstreamMap.get(edge.source).push(edge.target)
  })
  return { upstreamMap, downstreamMap }
}

function buildDepthMap(nodeMap, upstreamMap) {
  const memo = new Map()

  const visit = (nodeId) => {
    if (memo.has(nodeId)) {
      return memo.get(nodeId)
    }
    const parents = upstreamMap.get(nodeId) || []
    if (!parents.length) {
      memo.set(nodeId, 0)
      return 0
    }
    const depth = Math.max(...parents.map((parentId) => visit(parentId))) + 1
    memo.set(nodeId, depth)
    return depth
  }

  for (const nodeId of nodeMap.keys()) {
    visit(nodeId)
  }

  return memo
}

function buildDownstreamCountMap(nodeMap, downstreamMap) {
  const memo = new Map()

  const visit = (nodeId) => {
    if (memo.has(nodeId)) {
      return memo.get(nodeId)
    }
    const children = downstreamMap.get(nodeId) || []
    if (!children.length) {
      memo.set(nodeId, 0)
      return 0
    }
    const count = children.length + Math.max(...children.map((childId) => visit(childId)), 0)
    memo.set(nodeId, count)
    return count
  }

  for (const nodeId of nodeMap.keys()) {
    visit(nodeId)
  }

  return memo
}

function choosePrimaryResult(outputNodes = []) {
  return outputNodes[0]?.id || ''
}

function buildLaneMap({
  nodes = [],
  outputNodes = [],
  primaryResultId = '',
  primarySpine = new Set()
} = {}) {
  const outputLaneMap = new Map()
  const orderedOutputs = [...outputNodes].sort((left, right) => {
    if (left.id === primaryResultId) return -1
    if (right.id === primaryResultId) return 1
    return String(left.title || left.name || '').localeCompare(String(right.title || right.name || ''), 'zh-CN')
  })

  orderedOutputs.forEach((node, index) => {
    outputLaneMap.set(node.id, LANE_PATTERN[index] ?? index)
  })

  const laneMap = new Map()
  nodes.forEach((node) => {
    const reachableResults = Array.isArray(node.resultKeys) ? node.resultKeys : []
    if (node.id === primaryResultId || primarySpine.has(node.id) || node.isShared) {
      laneMap.set(node.id, 0)
      return
    }
    if (node.layer === 'output') {
      laneMap.set(node.id, outputLaneMap.get(node.id) ?? 0)
      return
    }
    const ownerId = node.branchOwner || reachableResults[0] || ''
    laneMap.set(node.id, outputLaneMap.get(ownerId) ?? 0)
  })

  return { laneMap, outputLaneMap }
}

function resolveAnchorPoints(source = {}, target = {}) {
  const sourceCenterX = source.x + source.width / 2
  const sourceCenterY = source.y + source.height / 2
  const targetCenterX = target.x + target.width / 2
  const targetCenterY = target.y + target.height / 2
  const horizontalGap = targetCenterX - sourceCenterX
  const verticalGap = targetCenterY - sourceCenterY
  const sameRow = Math.abs(verticalGap) < 84

  if (sameRow) {
    if (horizontalGap >= 0) {
      return {
        x1: source.x + source.width,
        y1: sourceCenterY,
        x2: target.x,
        y2: targetCenterY,
        sameRow
      }
    }
    return {
      x1: source.x,
      y1: sourceCenterY,
      x2: target.x + target.width,
      y2: targetCenterY,
      sameRow
    }
  }

  return {
    x1: sourceCenterX,
    y1: source.y + source.height,
    x2: targetCenterX,
    y2: target.y,
    sameRow
  }
}

function buildConnectorPath({ x1, y1, x2, y2, sameRow }) {
  const dx = x2 - x1
  const dy = y2 - y1

  if (sameRow) {
    const offset = Math.max(Math.abs(dx) * 0.38, 44)
    const c1x = x1 + (dx >= 0 ? offset : -offset)
    const c2x = x2 - (dx >= 0 ? offset : -offset)
    return `M ${x1} ${y1} C ${c1x} ${y1}, ${c2x} ${y2}, ${x2} ${y2}`
  }

  // 增大垂直方向的控制点延伸系数，让连线在遇到大跨度时呈现更深的“下垂”或“上抛”弧度，避免平行拥挤感
  const verticalRatio = Math.min(Math.abs(dx) / (Math.abs(dy) + 1), 3) // 根据宽高比动态调整
  const offsetY = Math.max(Math.abs(dy) * (0.42 + verticalRatio * 0.2), 62)
  return `M ${x1} ${y1} C ${x1} ${y1 + offsetY}, ${x2} ${y2 - offsetY}, ${x2} ${y2}`
}

function boxesOverlap(left = {}, right = {}, padding = 18) {
  return !(
    left.x + left.width + padding < right.x ||
    right.x + right.width + padding < left.x ||
    left.y + left.height + padding < right.y ||
    right.y + right.height + padding < left.y
  )
}

function resolveGlobalOverlaps(nodes = [], options = {}) {
  const {
    horizontalGap = 42,
    verticalGap = 38,
    sameRowThreshold = 72,
    padding = 12,
    maxPasses = 40
  } = options

  for (let pass = 0; pass < maxPasses; pass += 1) {
    let moved = false

    for (let index = 0; index < nodes.length; index += 1) {
      for (let inner = index + 1; inner < nodes.length; inner += 1) {
        const left = nodes[index]
        const right = nodes[inner]
        if (!boxesOverlap(left, right, padding)) {
          continue
        }

        moved = true
        const centerXLeft = left.x + left.width / 2
        const centerXRight = right.x + right.width / 2
        const centerYLeft = left.y + left.height / 2
        const centerYRight = right.y + right.height / 2
        const deltaX = centerXRight - centerXLeft
        const deltaY = centerYRight - centerYLeft
        const sameRow = Math.abs(deltaY) < sameRowThreshold
        const requiredX = left.width / 2 + right.width / 2 + horizontalGap
        const requiredY = left.height / 2 + right.height / 2 + verticalGap

        if (sameRow || Math.abs(requiredX - Math.abs(deltaX)) <= Math.abs(requiredY - Math.abs(deltaY))) {
          const shift = Math.max((requiredX - Math.abs(deltaX)) / 2, 10)
          const direction = deltaX >= 0 ? 1 : -1
          left.x -= shift * direction
          right.x += shift * direction
        } else {
          const shift = Math.max((requiredY - Math.abs(deltaY)) / 2, 10)
          const direction = deltaY >= 0 ? 1 : -1
          left.y -= shift * direction
          right.y += shift * direction
        }
      }
    }

    if (!moved) {
      break
    }
  }
}

function resolveEdgeColor(source = {}, target = {}, isActive = false) {
  if (target.layer === 'output') {
    return isActive ? 'rgba(235, 170, 20, 0.96)' : 'rgba(212, 175, 99, 0.44)'
  }
  if (source.isShared || target.isShared || source.isPrimarySpine || target.isPrimarySpine) {
    return isActive ? 'rgba(32, 157, 159, 0.94)' : 'rgba(72, 181, 163, 0.42)'
  }
  return isActive ? 'rgba(90, 110, 128, 0.84)' : 'rgba(148, 163, 184, 0.34)'
}

function buildLayout(nodes = [], edges = [], viewportWidth = 0) {
  if (!nodes.length) {
    return {
      nodes: [],
      edges: [],
      bands: [],
      width: 1200,
      height: 720,
      primaryResultId: '',
      signature: ''
    }
  }

  const clonedNodes = nodes.map((node) => {
    const metrics = buildNodeMetrics(node)
    return {
      ...node,
      ...metrics,
      x: 0,
      y: 0,
      lane: 0,
      isShared: Boolean(node.isShared),
      isPrimarySpine: Boolean(node.isPrimarySpine),
      isPrimaryResult: Boolean(node.isPrimaryResult),
      depth: node.depth ?? 0
    }
  })

  const nodeMap = new Map(clonedNodes.map((node) => [node.id, node]))
  const directInputTargetMap = new Map()
  edges.forEach((edge) => {
    const sourceNode = nodeMap.get(edge.source)
    const targetNode = nodeMap.get(edge.target)
    if (sourceNode?.layer !== 'input' || !targetNode || targetNode.layer === 'input') {
      return
    }
    const targets = directInputTargetMap.get(edge.source) || []
    targets.push(targetNode.id)
    directInputTargetMap.set(edge.source, targets)
  })
  clonedNodes.forEach((node) => {
    if (node.layer !== 'input') {
      return
    }
    const firstHopTargetId = (directInputTargetMap.get(node.id) || [])[0] || ''
    const firstHopTarget = nodeMap.get(firstHopTargetId)
    node.firstHopTargetId = firstHopTargetId
    node.firstHopTargetTitle = String(firstHopTarget?.title || firstHopTarget?.name || '').trim()
  })
  const outputNodes = clonedNodes.filter((node) => node.layer === 'output')
  const helperPrimaryResultId = clonedNodes.find((node) => node.isPrimaryResult)?.id || ''
  const primaryResultId = helperPrimaryResultId || choosePrimaryResult(outputNodes)
  const primarySpine = new Set(
    clonedNodes.filter((node) => node.isPrimarySpine).map((node) => node.id)
  )
  const { laneMap } = buildLaneMap({
    nodes: clonedNodes,
    outputNodes,
    primaryResultId,
    primarySpine
  })

  clonedNodes.forEach((node) => {
    node.lane = laneMap.get(node.id) ?? 0
  })

  const compact = viewportWidth > 0 && viewportWidth < 1320
  const centerX = 820
  const columnGap = compact ? 340 : 420
  const inputGap = compact ? 36 : 44
  const depthGap = compact ? 220 : 260
  const inputTop = 112
  const inputRowGap = compact ? 220 : 260

  const calculationNodes = clonedNodes
    .filter((node) => node.layer === 'calculation')
    .sort((left, right) => {
      const depthDiff = (left.depth || 0) - (right.depth || 0)
      if (depthDiff !== 0) {
        return depthDiff
      }
      return String(left.title || left.name || '').localeCompare(String(right.title || right.name || ''), 'zh-CN')
    })

  const calcGroupMap = new Map()
  calculationNodes.forEach((node) => {
    const key = `${Math.max(node.depth || 1, 1)}:${node.lane}`
    const group = calcGroupMap.get(key) || []
    group.push(node)
    calcGroupMap.set(key, group)
  })

  const calculationTop = inputTop + inputRowGap

  calcGroupMap.forEach((group, key) => {
    const [depthText, laneText] = key.split(':')
    const depth = Number(depthText || 1)
    const lane = Number(laneText || 0)
    const laneCenterX = centerX + lane * columnGap
    const y = calculationTop + (depth - 1) * depthGap
    const rowWidth = group.reduce((sum, node) => sum + node.width, 0) + Math.max(group.length - 1, 0) * (lane === 0 ? 52 : 40)
    let cursor = laneCenterX - rowWidth / 2
    group.forEach((node) => {
      node.x = cursor
      node.y = y
      cursor += node.width + (lane === 0 ? 52 : 40)
    })
  })

  // 解决计算节点的重叠
  resolveGlobalOverlaps(calculationNodes, {
    horizontalGap: 68,
    verticalGap: 28,
    sameRowThreshold: 160,
    padding: 18,
    maxPasses: 36
  })

  // === 优化方案：让连线看起来更顺滑，而不是死板的居中 ===
  // 我们不需要改变计算节点的物理位置，我们改变“连线路径的绘制方式”。
  // 贝塞尔曲线在连接很长水平距离时会显得平，我们可以调整贝塞尔控制点（Control Points）的垂直延伸比例。
  // 这部分在 `buildConnectorPath` 或相关地方处理。但在此处，我们可以将输入节点分组尽量往中间靠拢，减少水平极值。

  const inputNodes = clonedNodes.filter((node) => node.layer === 'input')
  
  const roleGroups = new Map()
  inputNodes.forEach((node) => {
    const role = node.semanticRole || 'base'
    const group = roleGroups.get(role) || []
    group.push(node)
    roleGroups.set(role, group)
  })

  const roleOrder = ['product', 'environment', 'reference', 'base']
  const roleLabels = {
    product: '产品参数',
    environment: '环境参数',
    reference: '查表/经验依据',
    base: '基础参数'
  }

  const inputGroupsLayout = []
  roleOrder.forEach(role => {
    const group = roleGroups.get(role)
    if (!group || !group.length) return
    
    let sumTargetX = 0
    let validTargets = 0
    group.forEach(node => {
      const targetNode = nodeMap.get(node.firstHopTargetId)
      if (targetNode) {
        sumTargetX += targetNode.x + targetNode.width / 2
        validTargets += 1
      }
    })
    
    const avgTargetX = validTargets > 0 ? sumTargetX / validTargets : centerX
    const groupWidth = group.reduce((sum, node) => sum + node.width, 0) + Math.max(group.length - 1, 0) * inputGap
    
    inputGroupsLayout.push({
      role,
      label: roleLabels[role],
      nodes: group,
      avgTargetX,
      width: groupWidth
    })
  })

  // 按 avgTargetX 排序组
  inputGroupsLayout.sort((a, b) => a.avgTargetX - b.avgTargetX)

  // 为每个组分配 x，避免重叠
  const groupGap = 48
  inputGroupsLayout.forEach(g => {
    g.x = g.avgTargetX - g.width / 2
  })

  const maxInputWidth = Math.max(...calculationNodes.map(n => n.width)) * 3 + 200 // 限制输入层的总宽度不要比计算层宽太多
  const totalInputWidth = inputGroupsLayout.reduce((sum, g) => sum + g.width, 0) + (inputGroupsLayout.length - 1) * groupGap
  
  if (totalInputWidth > maxInputWidth && inputGroupsLayout.length > 0) {
    // 如果总宽度超标，对组的X坐标进行整体压缩
    const scale = maxInputWidth / totalInputWidth
    const centerGroupX = inputGroupsLayout[Math.floor(inputGroupsLayout.length / 2)].x
    inputGroupsLayout.forEach(g => {
      g.x = centerGroupX + (g.x - centerGroupX) * scale
    })
  }

  // 解决组之间的重叠
  for (let pass = 0; pass < 30; pass++) {
    let moved = false
    for (let i = 0; i < inputGroupsLayout.length - 1; i++) {
      const left = inputGroupsLayout[i]
      const right = inputGroupsLayout[i+1]
      const overlap = (left.x + left.width + groupGap) - right.x
      if (overlap > 0) {
        left.x -= overlap / 2
        right.x += overlap / 2
        moved = true
      }
    }
    if (!moved) break
  }

  // 计算完组位置后，分配节点坐标并收集 bands
  const inputBands = []
  inputGroupsLayout.forEach(g => {
    let cursor = g.x
    // 组内节点也按目标 X 排序
    g.nodes.sort((a, b) => {
      const ta = nodeMap.get(a.firstHopTargetId)
      const tb = nodeMap.get(b.firstHopTargetId)
      const xa = ta ? (ta.x + ta.width / 2) : centerX
      const xb = tb ? (tb.x + tb.width / 2) : centerX
      if (Math.abs(xa - xb) > 10) return xa - xb
      return String(a.title || a.name || '').localeCompare(String(b.title || b.name || ''), 'zh-CN')
    })

    g.nodes.forEach(node => {
      node.x = cursor
      node.y = inputTop
      cursor += node.width + inputGap
    })

    inputBands.push({
      key: g.role,
      label: g.label,
      top: inputTop - 38,
      height: 78 + 38 + 20, // 节点高度78，上间距38留给标题，下间距20
      left: g.x - 24,
      width: g.width + 48
    })
  })

  // 重新确保所有的输入节点都在同一行（消除垂直偏移）
  inputNodes.forEach((node) => {
    node.y = inputTop
  })

  // 根据实际的计算节点高度来计算 resultTop
  const actualCalcBottom = calculationNodes.reduce((max, node) => Math.max(max, node.y + node.height), calculationTop)
  const resultTop = actualCalcBottom + 260

  const orderedOutputs = [...outputNodes].sort((left, right) => {
    if (left.id === primaryResultId) return -1
    if (right.id === primaryResultId) return 1
    return String(left.title || left.name || '').localeCompare(String(right.title || right.name || ''), 'zh-CN')
  })

  orderedOutputs.forEach((node) => {
    node.x = centerX + node.lane * columnGap - node.width / 2
    node.y = resultTop
  })

  resolveGlobalOverlaps(outputNodes, {
    horizontalGap: 72,
    verticalGap: 36,
    sameRowThreshold: 88,
    padding: 26,
    maxPasses: 32
  })

  resolveGlobalOverlaps(clonedNodes, {
    horizontalGap: 56,
    verticalGap: 52,
    sameRowThreshold: 96,
    padding: 28,
    maxPasses: 48
  })

  const minX = Math.min(...clonedNodes.map((node) => node.x), centerX - 420) - 220
  const maxX = Math.max(...clonedNodes.map((node) => node.x + node.width), centerX + 420) + 220
  const minY = Math.min(...clonedNodes.map((node) => node.y), inputTop) - 70
  const maxY = Math.max(...clonedNodes.map((node) => node.y + node.height), resultTop + 120) + 120

  const normalizedNodes = clonedNodes.map((node) => ({
    ...node,
    x: node.x - minX + 40,
    y: node.y - minY
  }))

  const normalizedNodeMap = new Map(normalizedNodes.map((node) => [node.id, node]))
  const height = Math.max(maxY - minY, 720)
  const width = Math.max(maxX - minX + 80, 1280)

  const edgesWithPaths = edges
    .map((edge) => {
      const sourceNode = normalizedNodeMap.get(edge.source)
      const targetNode = normalizedNodeMap.get(edge.target)
      if (!sourceNode || !targetNode) {
        return null
      }
      const points = resolveAnchorPoints(sourceNode, targetNode)
      const edgeState = focusState.value.edgeStates.get(`${edge.source}->${edge.target}`) || 'default'
      const isActive = edgeState === 'related'
      const isMuted = edgeState === 'muted'
      return {
        ...edge,
        d: buildConnectorPath(points),
        isActive,
        isMuted,
        color: resolveEdgeColor(sourceNode, targetNode, isActive)
      }
    })
    .filter(Boolean)

  const inputBottom = normalizedNodes
    .filter((node) => node.layer === 'input')
    .reduce((max, node) => Math.max(max, node.y + node.height), 0)
  const calculationBottom = normalizedNodes
    .filter((node) => node.layer === 'calculation')
    .reduce((max, node) => Math.max(max, node.y + node.height), inputBottom + 180)
  const outputBottom = normalizedNodes
    .filter((node) => node.layer === 'output')
    .reduce((max, node) => Math.max(max, node.y + node.height), calculationBottom + 180)

  return {
    nodes: normalizedNodes,
    edges: edgesWithPaths,
    width,
    height: Math.max(actualCalcBottom + 120 - minY, height),
      primaryResultId,
      bands: [
        ...inputBands.map(b => ({ ...b, left: b.left - minX + 40, top: b.top - minY })),
        {
          key: 'calculation',
          label: props.calculationLayerTitle,
          top: calculationTop - 46 - minY,
          height: Math.max(actualCalcBottom - calculationTop + 86, 220),
          left: Math.min(...calculationNodes.map(n => n.x - minX + 40)) - 40,
          width: Math.max(...calculationNodes.map(n => n.x - minX + 40 + n.width)) - Math.min(...calculationNodes.map(n => n.x - minX + 40)) + 80
        },
        {
          key: 'output',
          label: props.outputLayerTitle,
          top: resultTop - 46 - minY,
          height: 180,
          left: Math.min(...outputNodes.map(n => n.x - minX + 40)) - 40,
          width: Math.max(...outputNodes.map(n => n.x - minX + 40 + n.width)) - Math.min(...outputNodes.map(n => n.x - minX + 40)) + 80
        }
      ],
    signature: `${normalizedNodes.map((node) => node.id).join('|')}::${edges.map((edge) => edge.id).join('|')}`
  }
}

const layoutState = computed(() =>
  buildLayout(visibleNodes.value, visibleEdges.value, viewportSize.value.width)
)

const sceneTransformStyle = computed(() => ({
  width: `${layoutState.value.width}px`,
  height: `${layoutState.value.height}px`,
  transform: `translate(${viewState.value.x}px, ${viewState.value.y}px) scale(${viewState.value.scale})`,
  transition: dragState.value.active ? 'none' : 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)'
}))

function resolveBandStyle(band = {}) {
  const style = {
    top: `${band.top}px`,
    height: `${band.height}px`
  }
  if (band.left !== undefined) {
    style.left = `${band.left}px`
    style.right = 'auto'
  }
  if (band.width !== undefined) {
    style.width = `${band.width}px`
  }
  return style
}

function resolveNodeStyle(node = {}) {
  const palette = node.palette || resolveNodePalette(node.visualClass)
  return {
    left: `${node.x}px`,
    top: `${node.y}px`,
    width: `${node.width}px`,
    minHeight: `${node.height}px`,
    '--flow-node-fill': palette.fill,
    '--flow-node-stroke': palette.stroke,
    '--flow-node-text': palette.text
  }
}

function emitViewportChange() {
  emit('viewport-change', {
    zoom: Number(viewState.value.scale.toFixed(3)),
    center: [
      Number((viewportSize.value.width / 2 - viewState.value.x).toFixed(2)),
      Number((viewportSize.value.height / 2 - viewState.value.y).toFixed(2))
    ]
  })
}

function fitViewport() {
  const viewportWidth = viewportSize.value.width
  const viewportHeight = viewportSize.value.height
  if (!viewportWidth || !viewportHeight || !layoutState.value.width || !layoutState.value.height) {
    return
  }
  const safePadding = 32
  const scaleX = (viewportWidth - safePadding * 2) / layoutState.value.width
  const scaleY = (viewportHeight - safePadding * 2) / layoutState.value.height
  // 增加最小缩放比例，即使图再大也能看清全貌
  const targetScale = Math.max(0.2, Math.min(Math.min(scaleX, scaleY), 1))
  const targetX = (viewportWidth - layoutState.value.width * targetScale) / 2
  const targetY = Math.max((viewportHeight - layoutState.value.height * targetScale) / 2, 18)
  
  // 如果之前没有渲染过，直接跳过动画
  if (viewState.value.scale <= 0) {
    viewState.value = { scale: targetScale, x: targetX, y: targetY }
  } else {
    // 设置新状态，通过 CSS transition 处理平滑过渡
    viewState.value = { scale: targetScale, x: targetX, y: targetY }
  }
  
  emitViewportChange()
}

function handleNodeClick(node = {}) {
  emit('select-node', node)
}

function handleSurfaceBlankClick() {
  return
}

function zoomTo(scale, pivotX = viewportSize.value.width / 2, pivotY = viewportSize.value.height / 2) {
  const nextScale = Math.max(0.34, Math.min(scale, 2.2))
  const factor = nextScale / viewState.value.scale
  viewState.value = {
    scale: nextScale,
    x: pivotX - (pivotX - viewState.value.x) * factor,
    y: pivotY - (pivotY - viewState.value.y) * factor
  }
  emitViewportChange()
}

function zoomIn() {
  zoomTo(viewState.value.scale * 1.12)
}

function zoomOut() {
  zoomTo(viewState.value.scale / 1.12)
}

function handleWheel(event) {
  const rect = surfaceRef.value?.getBoundingClientRect()
  if (!rect) {
    return
  }
  const pivotX = event.clientX - rect.left
  const pivotY = event.clientY - rect.top
  const factor = event.deltaY > 0 ? 0.92 : 1.08
  zoomTo(viewState.value.scale * factor, pivotX, pivotY)
}

function handleSurfacePointerDown(event) {
  if (event.button !== 0) {
    return
  }
  if (event.target?.closest?.('.flow-node')) {
    return
  }
  dragState.value = {
    active: true,
    startPointerX: event.clientX,
    startPointerY: event.clientY,
    startX: viewState.value.x,
    startY: viewState.value.y
  }
  surfaceRef.value?.setPointerCapture?.(event.pointerId)
}

function handleWindowPointerMove(event) {
  if (!dragState.value.active) {
    return
  }
  viewState.value = {
    ...viewState.value,
    x: dragState.value.startX + (event.clientX - dragState.value.startPointerX),
    y: dragState.value.startY + (event.clientY - dragState.value.startPointerY)
  }
  emitViewportChange()
}

function stopDragging() {
  if (!dragState.value.active) {
    return
  }
  dragState.value = {
    active: false,
    startPointerX: 0,
    startPointerY: 0,
    startX: viewState.value.x,
    startY: viewState.value.y
  }
}

function updateViewportSize() {
  const rect = viewportRef.value?.getBoundingClientRect()
  viewportSize.value = {
    width: Math.max(rect?.width || 0, 1),
    height: Math.max(rect?.height || 0, 1)
  }
}

watch(
  () => [layoutState.value.signature, viewportSize.value.width, viewportSize.value.height],
  ([signature]) => {
    if (!signature) {
      return
    }
    if (signature !== lastLayoutSignature || viewState.value.scale <= 0) {
      lastLayoutSignature = signature
      fitViewport()
    }
  },
  { immediate: true }
)

watch(
  () => [props.displayMode, props.viewportResetToken],
  async () => {
    await nextTick()
    // 等待可能的 DOM 更新
    setTimeout(() => {
      fitViewport()
    }, 50)
  }
)

onMounted(() => {
  updateViewportSize()
  if (typeof ResizeObserver === 'function') {
    resizeObserver = new ResizeObserver(() => {
      updateViewportSize()
    })
    if (viewportRef.value) {
      resizeObserver.observe(viewportRef.value)
    }
  }
  window.addEventListener('pointermove', handleWindowPointerMove)
  window.addEventListener('pointerup', stopDragging)
  window.addEventListener('pointercancel', stopDragging)
  window.addEventListener('resize', updateViewportSize)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect?.()
  window.removeEventListener('pointermove', handleWindowPointerMove)
  window.removeEventListener('pointerup', stopDragging)
  window.removeEventListener('pointercancel', stopDragging)
  window.removeEventListener('resize', updateViewportSize)
})
</script>

<style scoped>
@import '@/assets/styles/workbench-formula-flow.css';

.workbench-flow {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.workbench-flow__viewport {
  position: relative;
  flex: 1;
  min-height: 0;
  border: 1px solid #dbe4ea;
  border-radius: 24px;
  overflow: hidden;
  background:
    radial-gradient(circle at 12% 10%, rgba(221, 228, 234, 0.72), transparent 18%),
    radial-gradient(circle at 84% 14%, rgba(233, 224, 214, 0.58), transparent 16%),
    linear-gradient(180deg, #f4f7f8 0%, #e5ebee 100%);
}

.workbench-flow__surface {
  position: absolute;
  inset: 0;
  overflow: hidden;
  cursor: grab;
}

.workbench-flow__surface.is-dragging {
  cursor: grabbing;
}

.workbench-flow__scene {
  position: absolute;
  top: 0;
  left: 0;
  transform-origin: 0 0;
}

.workbench-flow__band {
  position: absolute;
  left: 24px;
  right: 24px;
  border-radius: 24px;
  pointer-events: none;
}

.workbench-flow__band.is-input {
  background: rgba(110, 129, 162, 0.08);
}

.workbench-flow__band.is-product {
  background: rgba(59, 130, 246, 0.06);
  border: 1px dashed rgba(59, 130, 246, 0.2);
}

.workbench-flow__band.is-environment {
  background: rgba(16, 185, 129, 0.06);
  border: 1px dashed rgba(16, 185, 129, 0.2);
}

.workbench-flow__band.is-reference {
  background: rgba(245, 158, 11, 0.06);
  border: 1px dashed rgba(245, 158, 11, 0.2);
}

.workbench-flow__band.is-base {
  background: rgba(115, 156, 242, 0.06);
  border: 1px dashed rgba(115, 156, 242, 0.2);
}

.workbench-flow__band.is-calculation {
  background: rgba(72, 181, 163, 0.08);
}

.workbench-flow__band.is-output {
  background: rgba(236, 185, 73, 0.1);
}

.workbench-flow__band-label {
  position: absolute;
  top: 14px;
  left: 18px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: rgba(74, 89, 104, 0.76);
}

.workbench-flow__connectors {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
}

.workbench-flow__connector {
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  opacity: 0.92;
  transition: opacity 0.18s ease, stroke-width 0.18s ease;
}

.workbench-flow__connector.is-input {
  stroke-dasharray: 6 6;
}

.workbench-flow__connector.is-active {
  stroke-width: 4.2;
  opacity: 1;
}

.workbench-flow__connector.is-muted {
  opacity: 0.56;
}

.flow-node {
  position: absolute;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 18px;
  border: 2px solid rgba(255, 255, 255, 0.76);
  background: var(--flow-node-fill);
  color: var(--flow-node-text);
  text-align: left;
  box-shadow: 0 10px 24px rgba(37, 55, 76, 0.14);
  cursor: pointer;
  transition: transform 0.18s ease, opacity 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.flow-node:hover {
  transform: translateY(-2px);
}

.flow-node.is-selected {
  transform: translateY(-4px) scale(1.035);
  border-color: var(--flow-node-stroke);
  box-shadow: 0 0 0 6px rgba(255, 255, 255, 0.82), 0 28px 56px rgba(37, 55, 76, 0.28);
}

.flow-node.is-related {
  transform: translateY(-1px) scale(1.01);
  border-color: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 38px rgba(37, 55, 76, 0.2);
}

.flow-node.is-muted {
  opacity: 0.56;
  box-shadow: none;
}

.flow-node.is-primary-result {
  box-shadow: 0 18px 40px rgba(212, 170, 20, 0.24);
}

.flow-node.is-shared-node,
.flow-node.is-main-spine {
  box-shadow: 0 14px 32px rgba(32, 157, 159, 0.18);
}

.flow-node__title {
  font-size: 24px;
  font-weight: 800;
  line-height: 1.3;
}

.flow-node__value {
  font-size: 22px;
  font-weight: 800;
  line-height: 1.2;
}

.workbench-flow__zoom-controls {
  position: absolute;
  z-index: 3;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  box-shadow: 0 12px 32px rgba(26, 35, 48, 0.12);
}

.workbench-flow__zoom-controls {
  right: 20px;
  bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  border-radius: 16px;
}

.workbench-flow__zoom-btn {
  width: 40px;
  height: 40px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  font-size: 20px;
  color: #344454;
  cursor: pointer;
}

.workbench-flow__zoom-btn:hover {
  background: #eef2f4;
}

.workbench-flow__zoom-level {
  padding: 4px 0;
  font-size: 11px;
  font-weight: 800;
  text-align: center;
  color: #6b7581;
}

.workbench-flow__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 90px 24px;
  border: 1px solid #dbe4ea;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 248, 250, 0.98) 100%);
  text-align: center;
}

.empty-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 68px;
  height: 68px;
  border-radius: 20px;
  background: rgba(226, 232, 240, 0.8);
  font-size: 18px;
  font-weight: 800;
  color: #475569;
}

.empty-title {
  font-size: 20px;
  font-weight: 800;
  color: #334155;
}

@media (max-width: 960px) {

  .workbench-flow__zoom-controls {
    right: 14px;
    bottom: 14px;
  }
}
</style>
