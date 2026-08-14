<template>
  <section class="workbench-input-table" :class="`is-${props.treeKind}`">
    <div class="workbench-input-table__header">
      <div class="workbench-input-table__header-main">
        <span>{{ props.title || '输入参数树' }}</span>
      </div>
      <el-button v-if="props.allowAdd" type="primary" link size="small" @click="emit('add')">
        <el-icon><Plus /></el-icon> 新增参数
      </el-button>
    </div>

    <div v-if="rows.length" class="workbench-input-table__body">
      <section
        v-for="group in groupedRows"
        :key="group.key"
        class="workbench-input-table__group"
        :class="`is-${props.treeKind}`"
      >
        <div class="workbench-input-table__group-header">
          <button
            type="button"
            class="workbench-input-table__group-toggle-button"
            @click="toggleGroup(group.key)"
          >
            <span class="workbench-input-table__group-toggle">{{ isCollapsed(group.key) ? '>' : 'v' }}</span>
            <span class="workbench-input-table__group-title">{{ group.label }}</span>
            <span class="workbench-input-table__group-count">{{ group.rows.length }}</span>
          </button>

          <div class="workbench-input-table__group-actions" @click.stop>
            <el-tooltip
              v-if="props.allowGroupRename && group.rows.length"
              :content="`重命名参数集合 ${group.label}`"
              placement="top"
            >
              <el-button type="primary" link size="small" @click="emit('rename-group', group)">
                <el-icon><EditPen /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip
              v-if="props.allowGroupDelete && group.rows.length"
              :content="`删除参数集合 ${group.label}`"
              placement="top"
            >
              <el-button type="danger" link size="small" @click="emit('delete-group', group)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </div>

        <div v-if="!isCollapsed(group.key)" class="workbench-input-table__group-body">
          <div
            v-for="row in group.rows"
            :key="resolveRowKey(row)"
            class="workbench-input-table__row"
            :class="{
              'is-active': activeKey === String(row.paramName || ''),
              'is-editing': isRowEditing(row),
              'is-selection-tree': props.treeKind === 'selection'
            }"
            @click="emit('select', row)"
          >
            <div class="workbench-input-table__name" @dblclick.stop="startEdit(row, 'name')">
              <el-input
                v-if="isEditing(row, 'name')"
                :ref="(el) => setEditorRef(row, 'name', el)"
                v-model="editDraft"
                size="small"
                placeholder="参数名称"
                @click.stop
                @blur="commitEdit(row, 'name')"
                @keyup.enter="commitEdit(row, 'name')"
                @keyup.esc="cancelEdit"
              />
              <template v-else>
                <div class="workbench-input-table__name-content">
                  <div
                    class="workbench-input-table__title"
                    :title="row.displayName || row.paramName || '未命名参数'"
                  >
                    {{ row.displayName || row.paramName || '未命名参数' }}
                  </div>
                  <div
                    v-if="resolveMetaText(row)"
                    class="workbench-input-table__meta"
                    :title="resolveMetaText(row)"
                  >
                    {{ resolveMetaText(row) }}
                  </div>
                </div>
              </template>
            </div>

            <div class="workbench-input-table__value" @dblclick.stop="startEdit(row, 'value')">
              <el-input
                v-if="isEditing(row, 'value')"
                :ref="(el) => setEditorRef(row, 'value', el)"
                v-model="editDraft"
                size="small"
                placeholder="输入值"
                @click.stop
                @blur="commitEdit(row, 'value')"
                @keyup.enter="commitEdit(row, 'value')"
                @keyup.esc="cancelEdit"
              />
              <template v-else>
                <div
                  class="workbench-input-table__value-text"
                  :title="String(row.value ?? '').trim() || '未填写'"
                >
                  {{ String(row.value ?? '').trim() || '-' }}
                </div>
              </template>
            </div>

            <div class="workbench-input-table__unit" @dblclick.stop="startEdit(row, 'unit')">
              <el-input
                v-if="isEditing(row, 'unit')"
                :ref="(el) => setEditorRef(row, 'unit', el)"
                v-model="editDraft"
                size="small"
                placeholder="单位"
                @click.stop
                @blur="commitEdit(row, 'unit')"
                @keyup.enter="commitEdit(row, 'unit')"
                @keyup.esc="cancelEdit"
              />
              <template v-else>
                <span
                  class="workbench-input-table__unit-badge"
                  :class="{ 'is-empty': !String(row.unitCode || '').trim() }"
                  :title="String(row.unitCode || '').trim() || '无单位'"
                >
                  {{ String(row.unitCode || '').trim() || '无单位' }}
                </span>
              </template>
            </div>

            <div class="workbench-input-table__actions" @click.stop>
              <el-tooltip v-if="props.treeKind === 'input'" content="重新归类" placement="top">
                <el-button type="primary" link size="small" @click="emit('reclassify', row)">
                  <el-icon><EditPen /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="删除参数" placement="top">
                <el-button v-if="props.allowDelete && row.allowDelete !== false" type="danger" link size="small" @click="emit('delete', row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>
        </div>
      </section>
    </div>

    <el-empty v-else :description="props.emptyDescription || '当前模块暂无输入项'" />
  </section>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { Plus, Delete, EditPen } from '@element-plus/icons-vue'
import { resolveWorkbenchTreeGroup } from '@/views/newDesignWorkbenchTreeGrouping.mjs'

const props = defineProps({
  rows: {
    type: Array,
    default: () => []
  },
  activeKey: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: ''
  },
  emptyDescription: {
    type: String,
    default: ''
  },
  allowAdd: {
    type: Boolean,
    default: true
  },
  allowDelete: {
    type: Boolean,
    default: true
  },
  allowGroupRename: {
    type: Boolean,
    default: false
  },
  allowGroupDelete: {
    type: Boolean,
    default: true
  },
  treeKind: {
    type: String,
    default: 'input'
  }
})

const emit = defineEmits([
  'change',
  'update-name',
  'update-unit',
  'select',
  'add',
  'delete',
  'delete-group',
  'rename-group',
  'reclassify',
  'blur'
])

const collapsedGroups = ref({})
const editingCell = ref({ rowKey: '', field: '' })
const editDraft = ref('')
const editorRefs = new Map()

const groupedRows = computed(() => {
  const groups = []
  const groupMap = new Map()
  for (const row of props.rows || []) {
    const groupInfo = resolveWorkbenchTreeGroup(row, props.treeKind)
    if (!groupMap.has(groupInfo.key)) {
      const group = { ...groupInfo, rows: [] }
      groupMap.set(groupInfo.key, group)
      groups.push(group)
    }
    groupMap.get(groupInfo.key).rows.push(row)
  }
  return groups
})

const resolveRowKey = (row = {}) => String(row._tempId || row.paramName || row.parameterId || '')

const resolveMetaText = (row = {}) => {
  const paramName = String(row.paramName || '').trim()
  const displayName = String(row.displayName || '').trim()
  // 仅当参数已重命名时显示原参数名（有信息量）；
  // 不再展示“待命名参数，保存后参与计算”等冗余提示，避免遮挡参数名称
  if (paramName && displayName && paramName !== displayName) {
    return paramName
  }
  return ''
}

const isCollapsed = (groupKey) => Boolean(collapsedGroups.value[groupKey])

const toggleGroup = (groupKey) => {
  collapsedGroups.value = {
    ...collapsedGroups.value,
    [groupKey]: !collapsedGroups.value[groupKey]
  }
}

const buildEditorKey = (row, field) => `${resolveRowKey(row)}:${field}`

const resolveDraftValue = (row, field) => {
  if (field === 'name') return String(row.displayName || row.paramName || '')
  if (field === 'unit') return String(row.unitCode || '')
  return String(row.value ?? '')
}

const setEditorRef = (row, field, editor) => {
  const key = buildEditorKey(row, field)
  if (editor) {
    editorRefs.set(key, editor)
  } else {
    editorRefs.delete(key)
  }
}

const focusEditor = (row, field) => {
  const editor = editorRefs.get(buildEditorKey(row, field))
  const input = editor?.input || editor?.textarea || editor?.$el?.querySelector?.('input,textarea')
  if (input && typeof input.focus === 'function') {
    input.focus()
    if (typeof input.select === 'function') {
      input.select()
    }
  }
}

const startEdit = (row, field) => {
  editingCell.value = { rowKey: resolveRowKey(row), field }
  editDraft.value = resolveDraftValue(row, field)
  nextTick(() => focusEditor(row, field))
}

const cancelEdit = () => {
  editingCell.value = { rowKey: '', field: '' }
  editDraft.value = ''
}

const isEditing = (row, field) => {
  return editingCell.value.rowKey === resolveRowKey(row) && editingCell.value.field === field
}

const isRowEditing = (row) => editingCell.value.rowKey === resolveRowKey(row)

const commitEdit = (row, field) => {
  if (!isEditing(row, field)) {
    return
  }
  const nextValue = String(editDraft.value ?? '')
  if (field === 'name') {
    emit('update-name', row, nextValue)
  } else if (field === 'unit') {
    emit('update-unit', row, nextValue)
  } else {
    emit('change', row, nextValue)
  }
  emit('blur', row)
  cancelEdit()
}
</script>

<style scoped>
.workbench-input-table {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid #dbe3ef;
  border-radius: 12px;
  background: #ffffff;
  overflow: hidden;
}

.workbench-input-table__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 12px;
  border-bottom: 1px solid #eef2f7;
  background: #f8fafc;
}

.workbench-input-table__header-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}

.workbench-input-table__header-main small {
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
}

.workbench-input-table__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 10px 10px;
}

.workbench-input-table__group + .workbench-input-table__group {
  margin-top: 10px;
}

.workbench-input-table__group {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #ffffff;
  overflow: hidden;
}

.workbench-input-table__group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 34px;
  padding: 0 10px 0 8px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.workbench-input-table__group-toggle-button {
  flex: 1;
  min-width: 0;
  height: 34px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #1e293b;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  text-align: left;
}

.workbench-input-table__group-toggle {
  width: 12px;
  color: #64748b;
  text-transform: uppercase;
}

.workbench-input-table__group-title {
  flex: 1;
  min-width: 0;
  padding-left: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.workbench-input-table__group-count {
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

.workbench-input-table__group-actions {
  display: flex;
  align-items: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.workbench-input-table__group:hover .workbench-input-table__group-actions {
  opacity: 1;
}

.workbench-input-table__group-body {
  padding: 8px 8px 6px 14px;
  border-left: 2px solid #dbe3ef;
}

.workbench-input-table__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) fit-content(88px) fit-content(68px) max-content;
  gap: 6px;
  align-items: center;
  padding: 5px 6px 5px 10px;
  border-left: 2px solid transparent;
  border-bottom: 1px solid #eef2f7;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.workbench-input-table__row.is-active {
  background: rgba(37, 99, 235, 0.05);
}

.workbench-input-table__row.is-editing {
  background: rgba(59, 130, 246, 0.08);
}

.workbench-input-table__row.is-selection-tree {
  border-left-color: #0f766e;
  background: linear-gradient(90deg, rgba(20, 184, 166, 0.06) 0, rgba(20, 184, 166, 0.02) 92px, transparent 180px);
}

.workbench-input-table__row:hover {
  background: rgba(248, 250, 252, 0.85);
}

.workbench-input-table.is-input {
  box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.04);
}

.workbench-input-table.is-selection {
  box-shadow: inset 0 0 0 1px rgba(20, 184, 166, 0.06);
}

.workbench-input-table.is-input .workbench-input-table__header {
  border-top: 2px solid #2563eb;
}

.workbench-input-table.is-selection .workbench-input-table__header {
  border-top: 2px solid #0f766e;
  background: linear-gradient(180deg, rgba(20, 184, 166, 0.08), #f8fafc);
}

.workbench-input-table__group.is-input .workbench-input-table__group-header {
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.06), #f8fafc 70%);
}

.workbench-input-table__group.is-selection .workbench-input-table__group-header {
  background: linear-gradient(90deg, rgba(20, 184, 166, 0.09), #f8fafc 70%);
}

.workbench-input-table__group.is-input .workbench-input-table__group-body {
  border-left-color: #93c5fd;
}

.workbench-input-table__group.is-selection .workbench-input-table__group-body {
  border-left-color: #5eead4;
}

.workbench-input-table__name,
.workbench-input-table__value,
.workbench-input-table__unit {
  min-width: 0;
}

.workbench-input-table__name {
  overflow: hidden;
}

.workbench-input-table__name-content {
  display: flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
  width: 100%;
  overflow: hidden;
}

.workbench-input-table__title {
  flex: 1;
  min-width: 0;
  font-size: 12.5px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.workbench-input-table__meta {
  flex: 0 1 auto;
  min-width: 0;
  font-size: 10.5px;
  color: #94a3b8;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.workbench-input-table__value {
  text-align: right;
  justify-self: end;
  max-width: 88px;
}

.workbench-input-table__value-text {
  display: block;
  font-size: 12.5px;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.workbench-input-table__unit {
  display: flex;
  justify-content: flex-end;
  justify-self: end;
  max-width: 68px;
}

.workbench-input-table__unit-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  max-width: 100%;
  padding: 0 6px;
  height: 22px;
  border-radius: 999px;
  border: 1px solid #dbe3ef;
  background: #f8fafc;
  color: #475569;
  font-size: 10.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.workbench-input-table__unit-badge.is-empty {
  color: #94a3b8;
}

.workbench-input-table__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
  width: max-content;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.workbench-input-table__row:hover .workbench-input-table__actions,
.workbench-input-table__row.is-active .workbench-input-table__actions,
.workbench-input-table__row.is-editing .workbench-input-table__actions {
  opacity: 1;
}

.workbench-input-table :deep(.el-input__wrapper) {
  min-height: 28px;
  padding: 0 8px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: none;
}

.workbench-input-table :deep(.el-input__wrapper:hover),
.workbench-input-table :deep(.el-input__wrapper.is-focus) {
  border-color: #93c5fd;
  background: #ffffff;
}

.workbench-input-table :deep(.el-input__inner) {
  color: #334155;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.workbench-input-table__value :deep(.el-input__inner),
.workbench-input-table__unit :deep(.el-input__inner) {
  text-align: right;
}
</style>
