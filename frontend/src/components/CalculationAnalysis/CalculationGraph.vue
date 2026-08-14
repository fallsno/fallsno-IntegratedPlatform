<template>
  <div class="cg-panel">
    <!-- 顶部：目标结果 -->
    <div class="cg-header">
      <div class="cg-target">
        <span class="cg-target__name">{{ targetNode || '—' }}</span>
        <span class="cg-target__num">{{ fmtValue(targetValue) }}</span>
        <span class="cg-target__unit">{{ targetUnit }}</span>
      </div>
      <div class="cg-scene">
        <span class="cg-scene__label">当前场景</span>
        <span class="cg-scene__value">{{ activeSceneName || '基准值' }}</span>
      </div>
    </div>

    <!-- 计算链节点流 -->
    <div v-if="loading" class="cg-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>分析计算中…</span>
    </div>
    <div v-else-if="!groupedNodeLevels.length" class="cg-empty">
      <template v-if="error">
        <el-icon class="cg-empty__icon"><WarningFilled /></el-icon>
        <div class="cg-empty__title">计算链加载失败</div>
        <div class="cg-empty__detail">{{ error }}</div>
      </template>
      <template v-else>
        <div class="cg-empty__title">未获取到计算链</div>
        <div class="cg-empty__detail">在顶部选择目标结果节点后自动加载影响链</div>
      </template>
    </div>
    <div v-else class="cg-chain">
      <div
        v-for="(group, level) in groupedNodes"
        :key="level"
        class="cg-level"
        :class="{ 'cg-level--target': level === maxLevel }"
      >
        <div class="cg-level__rail">
          <span v-if="level > 0" class="cg-level__arrow">▼</span>
          <span class="cg-level__tag">L{{ level }}</span>
        </div>
        <div class="cg-level__nodes">
          <div
            v-for="node in group"
            :key="node.name"
            class="cg-node"
            :class="nodeClass(node)"
          >
            <div class="cg-node__head">
              <span class="cg-node__kind">{{ node.kind === 'input' ? '输入' : '节点' }}</span>
              <span class="cg-node__name" :title="node.name">{{ node.name }}</span>
            </div>
            <div v-if="node.kind === 'formula'" class="cg-node__expr" :title="node.expression">
              {{ node.expression }}
            </div>
            <div class="cg-node__value">
              <span class="cg-node__num">{{ fmtValue(nodeValue(node)) }}</span>
              <span class="cg-node__unit">{{ node.unit }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Loading, WarningFilled } from '@element-plus/icons-vue'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  values: { type: Object, default: () => ({}) },
  targetNode: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  activeSceneName: { type: String, default: '' },
  error: { type: String, default: '' },
})

const groupedNodes = computed(() => {
  const groups = {}
  for (const node of props.nodes) {
    const level = node.level ?? 0
    if (!groups[level]) groups[level] = []
    groups[level].push(node)
  }
  return groups
})

const groupedNodeLevels = computed(() => Object.keys(groupedNodes.value))

const maxLevel = computed(() => Math.max(0, ...groupedNodeLevels.value.map(Number)))

const targetValue = computed(() => {
  const v = props.values[props.targetNode]
  return v ? v.value : undefined
})
const targetUnit = computed(() => {
  const node = props.nodes.find((n) => n.name === props.targetNode)
  return node?.unit || props.values[props.targetNode]?.unit || ''
})

const fmtValue = (v) => {
  if (v === null || v === undefined || v === '') return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return '—'
  if (!Number.isFinite(n)) return '∞'
  if (n !== 0 && (Math.abs(n) >= 1e6 || Math.abs(n) < 1e-4)) return n.toExponential(3)
  return String(Math.round(n * 10000) / 10000)
}

const nodeValue = (node) => {
  const detail = props.values[node.name]
  return detail ? detail.value : node.value
}

const nodeClass = (node) => ({
  'is-input': node.kind === 'input',
  'is-target': node.name === props.targetNode,
})
</script>

<style scoped>
.cg-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0d1219;
  min-height: 0;
  position: relative;
}

/* 顶部目标结果条 */
.cg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #1f2833;
  flex-shrink: 0;
}
.cg-target {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
}
.cg-target__name {
  font-size: 16px;
  font-weight: 700;
  color: #ff5a5a;
  letter-spacing: 0.5px;
}
.cg-target__num {
  font-size: 24px;
  font-weight: 700;
  color: #ffd7d7;
  font-variant-numeric: tabular-nums;
}
.cg-target__unit {
  font-size: 12px;
  color: #8b98a8;
}
.cg-scene {
  display: flex;
  align-items: center;
  gap: 6px;
}
.cg-scene__label {
  font-size: 10px;
  color: #5d6a7c;
}
.cg-scene__value {
  font-size: 12px;
  color: #d6deeb;
  padding: 2px 8px;
  background: #1a2130;
  border: 1px solid #2a313c;
  border-radius: 3px;
}

/* 计算链 */
.cg-chain {
  flex: 1;
  overflow: auto;
  padding: 14px 18px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.cg-level {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.cg-level__rail {
  display: flex;
  align-items: center;
  gap: 6px;
}
.cg-level__arrow {
  font-size: 9px;
  color: #e23b3b;
}
.cg-level__tag {
  font-size: 9px;
  letter-spacing: 1px;
  color: #4d5a6d;
  border: 1px solid #263041;
  border-radius: 2px;
  padding: 1px 5px;
}
.cg-level--target .cg-level__tag {
  color: #ff5a5a;
  border-color: #7a2b2b;
}
.cg-level__nodes {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 节点卡片 */
.cg-node {
  width: 236px;
  background: #141b26;
  border: 1px solid #263041;
  border-radius: 4px;
  padding: 7px 9px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.cg-node__head {
  display: flex;
  align-items: center;
  gap: 6px;
}
.cg-node__kind {
  font-size: 9px;
  color: #7c8a99;
  border: 1px solid #2a313c;
  border-radius: 2px;
  padding: 0 4px;
  flex-shrink: 0;
}
.cg-node__name {
  font-size: 12px;
  font-weight: 600;
  color: #d6deeb;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cg-node__expr {
  font-size: 10px;
  color: #7c8a99;
  background: #0f1520;
  border: 1px solid #1f2833;
  border-radius: 3px;
  padding: 4px 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'Consolas', 'Menlo', monospace;
}
.cg-node__value {
  display: flex;
  align-items: baseline;
  gap: 5px;
  border-top: 1px dashed #1f2833;
  padding-top: 4px;
}
.cg-node__num {
  font-size: 14px;
  font-weight: 600;
  color: #e8eef7;
  font-variant-numeric: tabular-nums;
}
.cg-node__unit {
  font-size: 10px;
  color: #5d6a7c;
}

/* 输入参数节点 */
.cg-node.is-input {
  background: #101a26;
  border-color: #1f3a55;
}
.cg-node.is-input .cg-node__kind {
  color: #3b82f6;
  border-color: #2a4a6e;
}
.cg-node.is-input .cg-node__num {
  color: #7db3f5;
}

/* 目标节点 */
.cg-node.is-target {
  background: #241216;
  border-color: #e23b3b;
  box-shadow: 0 0 0 1px rgba(226, 59, 59, 0.35), 0 4px 16px rgba(226, 59, 59, 0.12);
}
.cg-node.is-target .cg-node__kind {
  color: #ff5a5a;
  border-color: #7a2b2b;
}
.cg-node.is-target .cg-node__name,
.cg-node.is-target .cg-node__num {
  color: #ff8a8a;
}

/* 加载与空态 */
.cg-loading,
.cg-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #7c8a99;
  font-size: 12px;
}
.cg-empty {
  flex-direction: column;
  gap: 6px;
}
.cg-empty__icon {
  font-size: 20px;
  color: #eab308;
}
.cg-empty__title {
  font-size: 12px;
  font-weight: 600;
  color: #aeb9c9;
}
.cg-empty__detail {
  font-size: 11px;
  color: #5d6a7c;
  max-width: 320px;
  text-align: center;
  line-height: 1.6;
  word-break: break-all;
}
</style>
