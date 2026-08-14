<template>
  <section class="workbench-formula-main-table">
    <div class="workbench-formula-main-table__head">
      <span>参数名称</span>
      <span>类型</span>
      <span>计算式</span>
      <span>计算值</span>
      <span>操作</span>
    </div>

    <div v-if="rows.length" ref="bodyRef" class="workbench-formula-main-table__body">
      <template v-for="row in rows" :key="row.key">
        <div
          v-if="row.rowType === 'group'"
          class="workbench-formula-main-table__group"
          :class="{ 'is-verify-scene': row.sceneType === 'verify' }"
          @dblclick="handleSceneHeaderDblClick(row)"
        >
          <div class="workbench-formula-main-table__group-main">
            <div class="workbench-formula-main-table__group-module">
              {{ row.moduleName || '当前模块' }}
            </div>
            <div class="workbench-formula-main-table__group-scene">
              <span class="workbench-formula-main-table__group-scene-label">计算块</span>
              <el-input
                v-if="editingSceneCode === row.sceneCode"
                v-model="sceneDraftName"
                size="small"
                placeholder="请输入计算块名称"
                @click.stop
                @keyup.enter="emit('confirm-rename-scene', { ...row, nextName: sceneDraftName })"
                @keyup.esc="emit('cancel-rename-scene')"
                @blur="emit('cancel-rename-scene')"
              />
              <span v-else class="workbench-formula-main-table__group-scene-name">{{ row.label }}</span>
            </div>
          </div>
          <div v-if="showSceneActions && editingSceneCode !== row.sceneCode" class="workbench-formula-main-table__group-actions">
            <el-tooltip content="添加公式" placement="top">
              <el-button class="action-btn" circle text size="small" type="primary" @click.stop="emit('create-formula', { moduleCode: row.moduleCode, sceneCode: row.sceneCode, moduleName: row.moduleName, sceneName: row.label })">
                <el-icon><Plus /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="删除计算块" placement="top">
              <el-button class="action-btn" circle text size="small" type="danger" @click.stop="emit('delete-scene', { moduleCode: row.moduleCode, sceneCode: row.sceneCode })">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </div>

        <div
          v-else
          :id="row.domId || undefined"
          :data-row-key="row.key"
          class="workbench-formula-main-table__row-container"
          v-click-outside="(e) => handleClickOutsideRow(row.key, e)"
        >
          <!-- Grid Row (Supports Inline Editing) -->
          <div
            class="workbench-formula-main-table__row"
            :class="{
              'is-active': activeKey === row.key || editingKey === row.key,
              'is-result': row.rowType === 'result',
              'is-editing': editingKey === row.key,
              'is-selection-param': row.metricType === 'selection',
              'is-focus-metric': row.metricType === 'focus'
            }"
            @click="emit('select-row', row)"
          >
            <div class="cell cell--name" @dblclick="handleEditFormula(row.raw, 'name')">
              <el-input 
                v-if="editingKey === row.key && (editingField === 'name' || row.raw?._isNewDraft)" 
                :model-value="activeFormulaDraft.name" 
                @input="emit('update-draft', { field: 'name', value: $event })" 
                size="small" 
                placeholder="公式名称"
                @click.stop 
                @keyup.enter="emit('save-formula')"
                @keyup.esc="emit('cancel-edit')"
              />
              <template v-else>
                <div class="cell__title">
                  <span class="cell__title-text">{{ (editingKey === row.key ? activeFormulaDraft.name : row.name) || '未命名公式' }}</span>
                  <span
                    v-if="row.metricType === 'selection' || row.metricType === 'focus'"
                    class="cell__metric-badge"
                    :class="{
                      'is-selection': row.metricType === 'selection',
                      'is-focus': row.metricType === 'focus'
                    }"
                  >
                    {{ row.metricType === 'selection' ? '选型' : '关键' }}
                  </span>
                  <el-tag v-if="row.is_output || row.raw?.is_output" size="small" type="success" effect="light" style="padding: 0 4px; height: 18px; line-height: 16px;">输出</el-tag>
                </div>
                <div v-if="row.meta" class="cell__meta">{{ row.meta }}</div>
              </template>
            </div>

            <div class="cell cell--type" @click.stop>
              <el-select
                :model-value="row.metricType || 'normal'"
                size="small"
                class="cell__type-select"
                @change="emit('metric-type-change', { row: row.raw || row, value: $event })"
              >
                <el-option label="普通参数" value="normal" />
                <el-option label="选型参数" value="selection" />
                <el-option label="关注指标" value="focus" />
              </el-select>
            </div>

            <div class="cell cell--expression" @dblclick="handleEditFormula(row.raw, 'expression')">
              <WorkbenchFormulaEditor
                v-if="isTemplateMode && editingKey === row.key && (editingField === 'expression' || row.raw?._isNewDraft)"
                :formula="activeFormulaDraft"
                :loading="loading"
                :autocomplete-sections="autocompleteSections"
                :argument-hint="argumentHint"
                @change="emit('update-draft', $event)"
                @selection-change="emit('selection-change', $event)"
                @save="emit('save-formula')"
                @cancel="emit('cancel-edit')"
              />
              <div v-else class="expression-display">
                <code>{{ (editingKey === row.key ? activeFormulaDraft.expression : row.expression) || '-' }}</code>
                <el-icon v-if="isTemplateMode" class="edit-icon"><Edit /></el-icon>
              </div>
            </div>

            <div class="cell cell--value" :class="{ 'is-pass': row.verificationStatus === 'pass', 'is-fail': row.verificationStatus === 'fail' }">
              {{ row.value || '-' }}
            </div>

            <div class="cell cell--action" @click.stop>
              <template v-if="editingKey === row.key">
                <el-tooltip content="保存 (Enter)" placement="top">
                  <el-button text size="small" type="primary" :loading="loading" @click="emit('save-formula')">
                    <el-icon><Check /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="取消 (Esc)" placement="top">
                  <el-button text size="small" @click="emit('cancel-edit')">
                    <el-icon><Close /></el-icon>
                  </el-button>
                </el-tooltip>
              </template>
              <template v-else>
                <el-tooltip v-if="showRowActions" content="删除公式" placement="right">
                  <el-button
                    text
                    size="small"
                    type="danger"
                    @click="emit('delete-formula', row.raw)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-tooltip>
              </template>
            </div>
          </div>
        </div>
      </template>
      <div v-if="showSceneActions" class="workbench-formula-main-table__add-scene">
        <el-tooltip content="新建计算块" placement="top">
          <el-button class="add-scene-btn" circle type="primary" plain @click="emit('create-scene')">
            <el-icon><Plus /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </div>

    <el-empty v-else description="当前模块暂无公式数据">
      <el-button v-if="showSceneActions" type="primary" @click="emit('create-scene')">
        <el-icon><Plus /></el-icon> 新建计算块
      </el-button>
    </el-empty>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ClickOutside as vClickOutside } from 'element-plus'
import { Edit, Check, Plus, Delete, Close } from '@element-plus/icons-vue'
import WorkbenchFormulaEditor from '@/components/WorkbenchFormulaEditor.vue'

const props = defineProps({
  rows: {
    type: Array,
    default: () => []
  },
  activeKey: {
    type: String,
    default: ''
  },
  editingKey: {
    type: String,
    default: ''
  },
  editingField: {
    type: String,
    default: ''
  },
  activeFormulaDraft: {
    type: Object,
    default: () => ({})
  },
  autocompleteSections: {
    type: Array,
    default: () => []
  },
  argumentHint: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  isTemplateMode: {
    type: Boolean,
    default: true
  },
  editingSceneCode: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'select-row', 
  'edit-formula',
  'open-explanation', 
  'create-formula',
  'delete-formula',
  'update-draft',
  'save-formula',
  'cancel-edit',
  'selection-change',
  'open-curve-builder',
  'import-library',
  'create-scene',
  'delete-scene',
  'blur-row',
  'start-rename-scene',
  'confirm-rename-scene',
  'cancel-rename-scene',
  'metric-type-change'
])
const bodyRef = ref(null)
const sceneDraftName = ref('')
const showSceneActions = computed(() => props.isTemplateMode)
const showRowActions = computed(() => props.isTemplateMode)

watch(
  () => props.editingSceneCode,
  (newVal) => {
    if (newVal) {
      const groupRow = props.rows.find(r => r.rowType === 'group' && r.sceneCode === newVal)
      if (groupRow) {
        sceneDraftName.value = groupRow.label || ''
      }
    } else {
      sceneDraftName.value = ''
    }
  },
  { immediate: true }
)

const handleClickOutsideRow = (rowKey, event) => {
  // If the click is on a parameter or result card, don't blur because we might want to insert it
  if (event && event.target) {
    const target = event.target
    if (
      target.closest('.equipment-param-item') || 
      target.closest('.summary-card') || 
      target.closest('.workbench-input-table__row') || // input parameters table row
      target.closest('.workbench-formula-main-table__row') // other formula rows
    ) {
      return
    }
  }

  if (props.editingKey === rowKey) {
    emit('blur-row', rowKey)
  }
}

const handleEditFormula = (row, field) => {
  if (!props.isTemplateMode) {
    return
  }
  emit('edit-formula', row, field)
}

const handleSceneHeaderDblClick = (row) => {
  if (!props.isTemplateMode) {
    return
  }
  emit('start-rename-scene', {
    moduleCode: row.moduleCode,
    sceneCode: row.sceneCode,
    sceneName: row.sceneName
  })
}

const scrollToRow = (rowKey = '') => {
  const normalizedKey = String(rowKey || '').trim()
  if (!normalizedKey || !bodyRef.value) {
    return
  }
  const escapedKey = typeof CSS !== 'undefined' && typeof CSS.escape === 'function'
    ? CSS.escape(normalizedKey)
    : normalizedKey.replace(/"/g, '\\"')
  const rowElement = bodyRef.value.querySelector(`[data-row-key="${escapedKey}"]`)
  rowElement?.scrollIntoView({
    block: 'center',
    behavior: 'smooth'
  })
}

defineExpose({
  scrollToRow
})
</script>

<style scoped>
.workbench-formula-main-table {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid #dbe3ef;
  border-radius: 14px;
  background: #fff;
}

.workbench-formula-main-table__head {
  display: grid;
  grid-template-columns: 220px 120px minmax(0, 1fr) 140px 72px;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #dbe3ef;
  background: #f8fafc;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.workbench-formula-main-table__body {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.workbench-formula-main-table__group {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 16px 8px;
  border-top: 1px solid #eef2f7;
  background: linear-gradient(180deg, #f8fafc, #f1f5f9);
}

.workbench-formula-main-table__group.is-verify-scene {
  background: linear-gradient(180deg, #e0f2fe, #f0f9ff);
  border-top: 1px solid #bae6fd;
}

.workbench-formula-main-table__group-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.workbench-formula-main-table__group-module {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.workbench-formula-main-table__group-scene {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.workbench-formula-main-table__group-scene-label {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 700;
}

.workbench-formula-main-table__group-scene-name {
  min-width: 0;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.workbench-formula-main-table__group.is-verify-scene .workbench-formula-main-table__group-module {
  color: #0369a1;
}

.workbench-formula-main-table__group.is-verify-scene .workbench-formula-main-table__group-scene-label {
  background: rgba(2, 132, 199, 0.12);
  color: #075985;
}

.workbench-formula-main-table__group-actions {
  display: flex;
  gap: 8px;
  padding-top: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.workbench-formula-main-table__group:hover .workbench-formula-main-table__group-actions {
  opacity: 1;
}

.workbench-formula-main-table__row-container {
  border-bottom: 1px solid #eef2f7;
}

.workbench-formula-main-table__add-scene {
  padding: 16px;
  display: flex;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.workbench-formula-main-table__add-scene:hover,
.workbench-formula-main-table__add-scene:focus-within,
.workbench-formula-main-table:hover .workbench-formula-main-table__add-scene {
  opacity: 1;
}

.workbench-formula-main-table__row {
  display: grid;
  grid-template-columns: 220px 120px minmax(0, 1fr) 140px 72px;
  gap: 12px;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  border-left: 2px solid transparent;
  transition: background-color 0.2s, border-color 0.2s;
}

.workbench-formula-main-table__row:hover {
  background: rgba(241, 245, 249, 0.4);
}

.workbench-formula-main-table__row.is-active {
  background: rgba(37, 99, 235, 0.05);
}

.workbench-formula-main-table__row.is-editing {
  background: #fff;
  border-left: 2px solid #2563eb;
  box-shadow: 0 0 0 1px #2563eb;
  z-index: 1;
}

.workbench-formula-main-table__row.is-result {
  background: rgba(15, 23, 42, 0.03);
}

.workbench-formula-main-table__row.is-selection-param {
  border-left-color: #0f766e;
  background: linear-gradient(90deg, rgba(20, 184, 166, 0.08) 0, rgba(20, 184, 166, 0.03) 88px, transparent 180px);
}

.workbench-formula-main-table__row.is-focus-metric {
  border-left-color: #d97706;
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.1) 0, rgba(245, 158, 11, 0.04) 88px, transparent 180px);
}

.workbench-formula-main-table__row.is-selection-param.is-active {
  background: linear-gradient(90deg, rgba(20, 184, 166, 0.14) 0, rgba(20, 184, 166, 0.06) 110px, rgba(37, 99, 235, 0.03) 100%);
}

.workbench-formula-main-table__row.is-focus-metric.is-active {
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.16) 0, rgba(245, 158, 11, 0.06) 110px, rgba(37, 99, 235, 0.03) 100%);
}

.cell {
  min-width: 0;
}

.cell--name {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cell__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}

.cell__title-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.cell__metric-badge {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.cell__metric-badge.is-selection {
  color: #115e59;
  background: rgba(20, 184, 166, 0.14);
}

.cell__metric-badge.is-focus {
  color: #b45309;
  background: rgba(245, 158, 11, 0.16);
}

.cell__meta {
  font-size: 11px;
  color: #94a3b8;
}

.cell--expression {
  position: relative;
}

.cell__type-select {
  width: 100%;
}

.expression-display {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: text;
  padding: 4px 8px;
  margin: -4px -8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.expression-display:hover {
  background: rgba(0, 0, 0, 0.04);
}

.expression-display code {
  display: block;
  font-size: 12px;
  line-height: 1.5;
  color: #1e293b;
  background: transparent;
  white-space: pre-wrap;
  word-break: break-word;
  flex: 1;
}

.edit-icon {
  color: #94a3b8;
  opacity: 0;
  transition: opacity 0.2s;
}

.expression-display:hover .edit-icon {
  opacity: 1;
  color: #3b82f6;
}

.expression-edit {
  display: flex;
  align-items: center;
}

.cell--value {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}

.cell--value.is-pass {
  color: #059669;
}

.cell--value.is-fail {
  color: #dc2626;
}

.cell--action {
  display: flex;
  justify-content: flex-end;
}
</style>
