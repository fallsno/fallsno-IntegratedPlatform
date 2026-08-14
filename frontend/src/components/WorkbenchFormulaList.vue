<template>
  <draggable
    v-if="rows.length"
    class="formula-list"
    tag="div"
    :model-value="rows"
    item-key="_rowKey"
    handle=".formula-row__drag-handle"
    ghost-class="formula-row--ghost"
    drag-class="formula-row--dragging"
    :disabled="moving || batchMode"
    :animation="180"
    @update:model-value="handleListReorder"
  >
    <template #item="{ element: row }">
      <div
        :id="row.domId"
        class="formula-row"
        :class="{
          'is-active': !batchMode && row._rowKey === activeFormulaKey,
          'is-highlighted': Boolean(highlightMap?.[row.name]),
          'is-batch-selected': batchMode && isSelectedRow(row)
        }"
      >
        <div v-if="batchMode || row._rowKey !== editingFormulaKey" class="formula-row__surface">
          <label v-if="batchMode" class="formula-row__checkbox" @click.stop>
            <input
              type="checkbox"
              :checked="isSelectedRow(row)"
              @change="emit('toggle-select', row)"
            >
          </label>
          <button
            type="button"
            class="formula-row__button"
            @click="batchMode ? emit('toggle-select', row) : emit('select', row)"
          >
            <div class="formula-row__top">
              <div class="formula-row__meta">
                <div class="formula-row__headline">
                  <span class="formula-row__name">{{ row.displayName || row.name || '未命名公式' }}</span>
                </div>
                <div class="formula-row__tags">
                  <el-tag v-if="row._isNewDraft" size="small" type="warning">编辑中</el-tag>
                  <el-tag v-if="highlightMap?.[row.name]" size="small" type="success" effect="plain">被引用</el-tag>
                </div>
              </div>
            </div>
            <div class="formula-row__expr">
              <span class="formula-row__expr-text">{{ row.expression || '点击当前行开始录入表达式' }}</span>
              <span v-if="row.expression" class="formula-row__result-inline">= {{ getResultText(row) }}</span>
            </div>
          </button>
          <div v-if="!batchMode" class="formula-row__tools">
            <button
              v-if="!row._isNewDraft"
              type="button"
              class="formula-row__drag-handle"
              :disabled="moving"
              title="拖动排序"
              aria-label="拖动排序"
            >
              <el-icon><Rank /></el-icon>
            </button>
            <button
              v-if="!row._isNewDraft"
              type="button"
              class="formula-row__delete-button"
              :disabled="moving"
              title="删除公式"
              aria-label="删除公式"
              @click.stop="emit('delete', row)"
            >
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>

        <div v-else class="formula-row__editor">
          <div class="formula-row__surface formula-row__surface--editor">
            <button type="button" class="formula-row__button formula-row__button--active" @click="emit('select', row)">
              <div class="formula-row__top">
                <div class="formula-row__meta">
                  <div class="formula-row__headline">
                    <span class="formula-row__name">{{ row.displayName || row.name || '未命名公式' }}</span>
                  </div>
                  <div class="formula-row__tags">
                    <el-tag v-if="row._isNewDraft" size="small" type="warning">编辑中</el-tag>
                    <el-tag v-if="highlightMap?.[row.name]" size="small" type="success" effect="plain">被引用</el-tag>
                  </div>
                </div>
              </div>
              <div class="formula-row__expr">
                <span class="formula-row__expr-text">{{ row.expression || '点击当前行开始录入表达式' }}</span>
                <span v-if="row.expression" class="formula-row__result-inline">= {{ getResultText(row) }}</span>
              </div>
            </button>
            <div class="formula-row__tools">
              <button
                v-if="!row._isNewDraft"
                type="button"
                class="formula-row__drag-handle"
                :disabled="moving"
                title="拖动排序"
                aria-label="拖动排序"
              >
                <el-icon><Rank /></el-icon>
              </button>
              <button
                v-if="!row._isNewDraft"
                type="button"
                class="formula-row__delete-button"
                :disabled="moving"
                title="删除公式"
                aria-label="删除公式"
                @click.stop="emit('delete', row)"
              >
                <el-icon><Delete /></el-icon>
              </button>
            </div>
          </div>
          <slot name="inline-editor" :row="row" />
        </div>
      </div>
    </template>
  </draggable>
</template>

<script setup>
import { Delete, Rank } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'

const props = defineProps({
  rows: {
    type: Array,
    default: () => []
  },
  activeFormulaKey: {
    type: String,
    default: ''
  },
  editingFormulaKey: {
    type: String,
    default: ''
  },
  highlightMap: {
    type: Object,
    default: () => ({})
  },
  resultMap: {
    type: Object,
    default: () => ({})
  },
  moving: {
    type: Boolean,
    default: false
  },
  batchMode: {
    type: Boolean,
    default: false
  },
  selectedRowKeys: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['select', 'reorder', 'toggle-select', 'delete'])

const getResultText = (row) => {
  return row?.name && String(row.name).trim()
    ? props.resultMap?.[row.name]?.displayText || '未计算'
    : '未计算'
}

const isSelectedRow = (row = {}) => {
  return (Array.isArray(props.selectedRowKeys) ? props.selectedRowKeys : []).includes(String(row?._rowKey || ''))
}

const handleListReorder = (nextRows = []) => {
  if (props.batchMode) {
    return
  }
  const orderedIds = nextRows
    .map((row) => Number(row?.id || 0))
    .filter((id) => id > 0)
  const currentIds = props.rows
    .map((row) => Number(row?.id || 0))
    .filter((id) => id > 0)
  if (!orderedIds.length || currentIds.length !== orderedIds.length) {
    return
  }
  const unchanged = currentIds.every((id, index) => id === orderedIds[index])
  if (!unchanged) {
    emit('reorder', { orderedIds })
  }
}
</script>

<style scoped>
.formula-list {
  display: grid;
  gap: 10px;
  max-height: 420px;
  overflow: auto;
  padding-right: 4px;
}

.formula-row {
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: #fff;
  transition: all 0.2s ease;
}

.formula-row.is-highlighted {
  border-color: #22c55e;
  box-shadow: 0 10px 24px rgba(34, 197, 94, 0.1);
}

.formula-row.is-active {
  border-color: #3b82f6;
  box-shadow: 0 14px 28px rgba(59, 130, 246, 0.14);
}

.formula-row.is-batch-selected {
  border-color: #f59e0b;
  box-shadow: 0 12px 24px rgba(245, 158, 11, 0.14);
}

.formula-row__button {
  width: 100%;
  padding: 12px 14px;
  border: none;
  border-radius: 16px;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.formula-row__surface {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.formula-row__checkbox {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  min-height: 62px;
  padding-left: 10px;
}

.formula-row__checkbox input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.formula-row__surface--editor {
  margin-bottom: 12px;
}

.formula-row__button:hover {
  background: rgba(59, 130, 246, 0.04);
}

.formula-row__button--active {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.formula-row__top {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.formula-row__meta {
  display: grid;
  gap: 8px;
  width: 100%;
}

.formula-row__name {
  font-weight: 700;
  color: #0f172a;
}

.formula-row__headline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.formula-row__tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.formula-row__expr {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
  line-height: 1.5;
  color: #64748b;
  word-break: break-word;
}

.formula-row__expr-text {
  min-width: 0;
  flex: 0 0 auto;
}

.formula-row__result-inline {
  flex-shrink: 0;
  white-space: nowrap;
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
}

.formula-row__tools {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  align-items: center;
  gap: 8px;
  padding-top: 12px;
  padding-right: 12px;
}

.formula-row__drag-handle,
.formula-row__delete-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  background: #f8fafc;
  color: #475569;
  cursor: grab;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.formula-row:hover .formula-row__drag-handle,
.formula-row:hover .formula-row__delete-button,
.formula-row.is-active .formula-row__drag-handle,
.formula-row.is-active .formula-row__delete-button {
  opacity: 1;
  pointer-events: auto;
}

.formula-row__drag-handle:hover:not(:disabled) {
  border-color: #94a3b8;
  background: #f1f5f9;
}

.formula-row__drag-handle:disabled {
  cursor: not-allowed;
  opacity: 0.35;
  pointer-events: none;
}

.formula-row__delete-button {
  border: 1px solid #fecaca;
  border-radius: 12px;
  background: #fff5f5;
  color: #b91c1c;
  cursor: pointer;
}

.formula-row__delete-button:hover:not(:disabled) {
  border-color: #fca5a5;
  background: #fee2e2;
}

.formula-row__delete-button:disabled {
  opacity: 0.35;
  pointer-events: none;
  cursor: not-allowed;
}

.formula-row__editor {
  padding: 0 14px 12px;
  border-top: 1px solid #eff6ff;
}

.formula-row--ghost {
  opacity: 0.45;
}

.formula-row--dragging {
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.12);
}
</style>
