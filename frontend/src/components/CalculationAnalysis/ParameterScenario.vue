<template>
  <div class="ps-panel">
    <div class="ps-section ps-section--scenes">
      <div class="ps-section__head">
        <span class="ps-section__title">参数场景管理</span>
        <span class="ps-section__meta">{{ scenarios.length }} 个方案</span>
      </div>

      <div class="ps-scenes">
        <div
          v-for="scene in scenarios"
          :key="scene.key"
          class="ps-scene"
          :class="{ 'is-active': scene.key === activeKey }"
          @click="$emit('select', scene.key)"
        >
          <span class="ps-scene__dot" />
          <span class="ps-scene__name">{{ scene.name }}</span>
          <span class="ps-scene__actions" @click.stop>
            <el-tooltip content="复制场景" placement="top">
              <el-button link size="small" class="ps-icon-btn" @click="$emit('copy', scene.key)">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="删除场景" placement="top">
              <el-button link size="small" class="ps-icon-btn ps-icon-btn--danger" @click="$emit('delete', scene.key)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </span>
        </div>
      </div>

      <div class="ps-actions">
        <el-button class="ps-btn-add" size="small" @click="$emit('add')">
          <el-icon><Plus /></el-icon>新增场景
        </el-button>
      </div>
    </div>

    <!-- 场景参数编辑（当前激活场景） -->
    <div class="ps-section ps-section--params">
      <div class="ps-section__head">
        <span class="ps-section__title">设计参数</span>
        <span class="ps-section__meta">{{ activeSceneName }}</span>
      </div>

      <div class="ps-param-rows">
        <div v-for="inp in inputs" :key="inp.name" class="ps-param">
          <div class="ps-param__name">
            <span class="ps-param__name-text">{{ inp.name }}</span>
            <span class="ps-param__unit">{{ inp.unit }}</span>
          </div>
          <div class="ps-param__value">
            <el-input-number
              v-model="activeParams[inp.name]"
              size="small"
              :controls="false"
              :precision="4"
              class="ps-num"
              @change="syncParams"
            />
          </div>
        </div>
      </div>
      <div v-if="!inputs.length" class="ps-empty">当前目标节点下未发现输入参数</div>
    </div>

    <!-- 参数范围（影响敏感性 / 曲线 / 响应面） -->
    <div class="ps-section ps-section--range">
      <div class="ps-section__head">
        <span class="ps-section__title">扫描范围</span>
        <span class="ps-section__meta">min – max</span>
      </div>
      <div class="ps-range-rows">
        <div v-for="inp in inputs" :key="inp.name" class="ps-range">
          <span class="ps-range__name">{{ inp.name }}</span>
          <div class="ps-range__editors">
            <el-input-number
              v-model="inp.min"
              size="small"
              :controls="false"
              :precision="6"
              class="ps-num ps-num--min"
            />
            <span class="ps-range__sep">~</span>
            <el-input-number
              v-model="inp.max"
              size="small"
              :controls="false"
              :precision="6"
              class="ps-num ps-num--max"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="ps-footer">
      <el-button class="ps-btn-run" type="primary" size="small" :loading="loading" @click="$emit('run')">
        <el-icon><VideoPlay /></el-icon>
        执行分析
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { CopyDocument, Delete, Plus, VideoPlay } from '@element-plus/icons-vue'

const props = defineProps({
  inputs: { type: Array, default: () => [] },
  scenarios: { type: Array, default: () => [] },
  activeKey: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})
const emit = defineEmits(['update:scenario', 'select', 'add', 'copy', 'delete', 'run'])

const activeSceneName = computed(
  () => props.scenarios.find((s) => s.key === props.activeKey)?.name || ''
)
const activeParams = ref({})

// 当前激活场景的参数 -> 本地可编辑副本
watch(
  [() => props.activeKey, () => props.scenarios],
  () => {
    const scene = props.scenarios.find((s) => s.key === props.activeKey)
    activeParams.value = scene ? { ...scene.parameters } : {}
  },
  { immediate: true, deep: true }
)

// 同步回父组件（场景参数）
const syncParams = () => {
  emit('update:scenario', props.activeKey, { ...activeParams.value })
}
</script>

<style scoped>
.ps-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0d1219;
  min-height: 0;
  overflow: hidden;
}
.ps-section {
  padding: 10px 12px;
  border-bottom: 1px solid #1f2833;
  flex-shrink: 0;
}
.ps-section--params {
  flex: 1;
  min-height: 120px;
  overflow-y: auto;
  flex-shrink: 1;
}
.ps-section--range {
  max-height: 38%;
  overflow-y: auto;
}
.ps-section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.ps-section__title {
  font-size: 12px;
  font-weight: 600;
  color: #d6deeb;
  letter-spacing: 0.5px;
}
.ps-section__meta {
  font-size: 10px;
  color: #5d6a7c;
}

/* 场景列表 */
.ps-scenes {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ps-scene {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: #141b26;
  border: 1px solid #223041;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.12s;
}
.ps-scene:hover {
  border-color: #33445a;
}
.ps-scene.is-active {
  border-color: #e23b3b;
  background: #1d1216;
}
.ps-scene.is-active .ps-scene__name {
  color: #ffd7d7;
  font-weight: 600;
}
.ps-scene__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3d4a5c;
  flex-shrink: 0;
}
.ps-scene.is-active .ps-scene__dot {
  background: #e23b3b;
  box-shadow: 0 0 6px rgba(226, 59, 59, 0.8);
}
.ps-scene__name {
  flex: 1;
  font-size: 12px;
  color: #aeb9c9;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ps-scene__actions {
  display: flex;
  opacity: 0;
  transition: opacity 0.12s;
}
.ps-scene:hover .ps-scene__actions {
  opacity: 1;
}
.ps-icon-btn {
  color: #7c8a99;
  padding: 2px;
}
.ps-icon-btn--danger:hover {
  color: #e23b3b;
}

/* 底部操作按钮 */
.ps-actions {
  margin-top: 8px;
}
.ps-btn-add {
  width: 100%;
  background: #161e2a;
  border: 1px dashed #33445a;
  color: #aeb9c9;
}
.ps-btn-add:hover {
  border-color: #e23b3b;
  color: #ffd7d7;
  background: #1d1216;
}

/* 参数编辑行 */
.ps-param-rows {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.ps-param {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  background: #111722;
  border: 1px solid #1f2833;
  border-radius: 4px;
}
.ps-param__name {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.ps-param__name-text {
  font-size: 12px;
  color: #d6deeb;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ps-param__unit {
  font-size: 10px;
  color: #5d6a7c;
  flex-shrink: 0;
}
.ps-param__value {
  flex-shrink: 0;
}

/* 范围编辑行 */
.ps-range-rows {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.ps-range {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ps-range__name {
  flex: 1;
  font-size: 11px;
  color: #8b98a8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ps-range__editors {
  display: flex;
  align-items: center;
  gap: 4px;
}
.ps-range__sep {
  font-size: 11px;
  color: #4d5a6d;
}
.ps-num {
  width: 82px;
}
.ps-num--min {
  --el-input-hover-border-color: #e23b3b;
}
.ps-num--max {
  --el-input-hover-border-color: #e23b3b;
}
.ps-num :deep(.el-input__inner) {
  text-align: center;
  font-size: 11px;
  padding: 0 4px;
}

.ps-empty {
  padding: 16px 0;
  text-align: center;
  font-size: 11px;
  color: #4d5a6d;
}

.ps-footer {
  margin-top: auto;
  padding: 10px 12px;
  border-top: 1px solid #1f2833;
  flex-shrink: 0;
}
.ps-btn-run {
  width: 100%;
  background: #e23b3b;
  border-color: #e23b3b;
  font-weight: 600;
  letter-spacing: 1px;
}
</style>
