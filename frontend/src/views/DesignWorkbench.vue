<template>
  <div class="design-workbench-page">
    <el-card class="workbench-summary" shadow="never">
      <div class="summary-header">
        <div class="summary-tags">
          <el-tag effect="plain" size="small">{{ selectedType?.type_name || '-' }}</el-tag>
          <el-tag type="warning" effect="plain" size="small">{{ selectedFamily?.family_code || '-' }}</el-tag>
          <el-tag type="success" effect="plain" size="small">{{ selectedVersion?.version_code || '-' }}</el-tag>
        </div>

        <div class="workbench-view-switch">
          <el-segmented
            v-model="workbenchViewMode"
            :options="[
              { label: '设计公式', value: 'formula' },
              { label: '计算链路', value: 'flow' },
              { label: '智能选型', value: 'smart_select' }
            ]"
          />
        </div>

        <div class="summary-actions">
          <el-tooltip content="新增计算模块" placement="bottom" v-if="workbenchViewMode === 'formula'">
            <el-button type="primary" :disabled="!selectedVersion" @click="handleModuleCreate" size="small"><el-icon><Plus /></el-icon></el-button>
          </el-tooltip>
          <el-tooltip content="基础参数管理" placement="bottom">
            <el-button :disabled="!selectedVersion" @click="openAllParametersDrawer" size="small"><el-icon><Setting /></el-icon></el-button>
          </el-tooltip>
          <el-tooltip content="重载型号初值" placement="bottom">
            <el-button :disabled="!selectedVersion" @click="reloadMatrixParameters" size="small"><el-icon><Refresh /></el-icon></el-button>
          </el-tooltip>
          <el-tooltip content="执行计算" placement="bottom">
            <el-button type="primary" :loading="executing" :disabled="!selectedVersion" @click="runDesign" size="small">
              <el-icon><VideoPlay /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="参数影响分析" placement="bottom">
            <el-button :disabled="!selectedVersion" @click="openCompare" size="small"><el-icon><DataLine /></el-icon></el-button>
          </el-tooltip>
        </div>
      </div>

      <div class="summary-path" v-if="workbenchViewMode === 'formula' && (activePath.moduleName || activePath.sceneName || activePath.formulaName)">
        <el-tooltip content="模块" placement="top" v-if="activePath.moduleName">
          <el-tag effect="plain" size="small">{{ activePath.moduleName }}</el-tag>
        </el-tooltip>
        <el-tooltip content="场景" placement="top" v-if="activePath.sceneName">
          <el-tag effect="plain" size="small" type="success" style="margin-left: 6px;">{{ activePath.sceneName }}</el-tag>
        </el-tooltip>
        <el-tooltip content="公式" placement="top" v-if="activePath.formulaName">
          <el-tag effect="plain" size="small" type="info" style="margin-left: 6px;">{{ activePath.formulaName }}</el-tag>
        </el-tooltip>
      </div>

    </el-card>

    <div v-if="workbenchViewMode === 'formula'" class="formula-workbench">
      <el-card class="formula-workbench__input" shadow="never">
        <WorkbenchInputTable
          :rows="moduleInputRows"
          :active-key="activeExplanationTargetKey"
          @change="handleParameterChange"
          @select="handleInputFocus"
          @add="handleAddParameter"
          @delete="handleDeleteParameter"
        />
      </el-card>

      <div class="formula-workbench__main">
        <div class="formula-module-strip" v-if="displayFormulaModules.length">
          <button
            v-for="module in displayFormulaModules"
            :key="module.moduleCode"
            type="button"
            class="formula-module-strip__item"
            :class="{ 'is-active': module.moduleCode === activeModuleCode }"
            @click="handleModuleSelect(module)"
          >
            <span class="formula-module-strip__name">{{ module.moduleName }}</span>
            <span class="formula-module-strip__meta">{{ buildModuleSummary(module).formulaCount }} 条</span>
          </button>
        </div>

        <WorkbenchFormulaMainTable
          ref="mainTableRef"
          :rows="mainTableRows"
          :active-key="activeExplanationTargetKey"
          :editing-key="editingFormulaKey"
          :active-formula-draft="activeFormulaDraft"
          :autocomplete-sections="autocompleteSections"
          :argument-hint="activeFormulaArgumentHint"
          :loading="formulaSaving"
          @select-row="handleMainTableRowSelect"
          @edit-formula="handleFormulaEdit"
          @open-explanation="handleOpenExplanation"
          @update-draft="handleFormulaDraftChange"
          @save-formula="handleFormulaSave"
          @cancel-edit="handleFormulaCancel"
          @selection-change="handleFormulaEditorSelectionChange"
          @open-curve-builder="openCurveFormulaDialog"
          @import-library="openFormulaLibraryDialog"
          @delete-formula="handleFormulaDelete"
          @create-formula="handleFormulaCreate"
          @create-scene="handleSceneCreate(activeModule || displayFormulaModules[0])"
          @delete-scene="handleSceneDelete"
        />
      </div>
    </div>

    <div v-else-if="workbenchViewMode === 'flow'" class="flow-panel-container">
      <div class="workbench-flow-actions">
        <el-tooltip content="显示全部链路" placement="bottom">
          <el-button size="small" @click="showAllFlowChains"><el-icon><Connection /></el-icon></el-button>
        </el-tooltip>
        <el-tooltip content="重置视图" placement="bottom">
          <el-button size="small" type="primary" @click="resetFlowView"><el-icon><Aim /></el-icon></el-button>
        </el-tooltip>
      </div>
      <WorkbenchCalculationFlowPanel
        :graph="activeFlowGraph"
        :selected-node-id="activeFlowNodeId"
        :viewport-state="flowViewportState"
        :display-mode="flowDisplayMode"
        :viewport-reset-token="flowViewportResetToken"
        @select-node="handleFlowNodeSelect"
        @drag-node="handleFlowNodeDrag"
        @viewport-change="handleFlowViewportChange"
      />
    </div>

    <div v-else-if="workbenchViewMode === 'smart_select'" class="smart-select-panel">
      <SmartSelectionPanel
        :mapped-params="{ power: 0, speed: 0, torque: 0, fb: 0 }"
        :current-equipment="currentEquipment"
        @apply-equipment="handleApplyEquipment"
        @clear-equipment="handleClearEquipment"
      />
    </div>

    <div v-if="workbenchViewMode === 'formula'" class="workbench-range-tabs">
      <div class="workbench-range-tabs__section">
        <div class="workbench-range-tabs__label">系列</div>
        <el-segmented
          :model-value="selectedFamilyRangeId"
          :options="familyRangeOptions"
          @change="handleFamilyRangeChange"
        />
      </div>
      <div class="workbench-range-tabs__section">
        <div class="workbench-range-tabs__label">型号</div>
        <el-segmented
          :model-value="selectedVersionRangeId"
          :options="versionRangeOptions"
          @change="handleVersionRangeChange"
        />
      </div>
    </div>

    <WorkbenchExplanationDrawer
      v-model="explanationDrawerVisible"
      :title="explanationPanel.title"
      :summary="explanationPanel.summary"
      :details="explanationPanel.details"
      :resources="explanationPanel.resources"
      :editable="true"
      @update:explanation="handleExplanationUpdate"
    />

    <el-dialog
      v-model="compareDialogVisible"
      title="参数影响分析"
      width="800px"
      destroy-on-close
    >
      <div v-if="impactAnalyzing" style="padding: 40px 0; text-align: center;">
        <el-icon class="is-loading" :size="32" color="#409eff"><Loading /></el-icon>
        <div style="margin-top: 16px; color: #606266;">正在分析参数影响，请稍候...</div>
      </div>
      <div v-else-if="impactResults.length > 0">
        <div style="margin-bottom: 16px; font-weight: bold;">
          目标指标：<span style="color: #409eff;">{{ impactTargetResultName }}</span>
        </div>
        <el-table :data="impactResults" border stripe height="400px">
          <el-table-column type="index" label="排名" width="60" align="center" />
          <el-table-column prop="parameter_name" label="影响参数" min-width="150" />
          <el-table-column prop="parameter_type" label="参数类型" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.parameter_type === 'input' ? 'success' : (row.parameter_type === 'constant' ? 'info' : 'warning')">
                {{ row.parameter_type === 'input' ? '输入参数' : (row.parameter_type === 'constant' ? '常量' : '计算参数') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="impact_level" label="影响程度" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.impact_level === 'high' ? 'danger' : (row.impact_level === 'medium' ? 'warning' : 'info')">
                {{ row.impact_level === 'high' ? '高' : (row.impact_level === 'medium' ? '中' : '低') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="direction" label="影响方向" min-width="180">
            <template #default="{ row }">
              <span :style="{ color: row.direction === 'positive' ? '#f56c6c' : '#67c23a' }">
                <el-icon><component :is="row.direction === 'positive' ? 'TopRight' : 'BottomRight'" /></el-icon>
                {{ row.direction === 'positive' ? '增加导致指标增加' : '增加导致指标降低' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="优化建议" min-width="150">
            <template #default="{ row }">
              <span v-if="row.impact_level === 'high'" style="color: #e6a23c; font-size: 12px;">
                建议优先调整此参数
              </span>
              <span v-else style="color: #909399; font-size: 12px;">
                影响较小，可按需调整
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else style="padding: 40px 0; text-align: center; color: #909399;">
        未分析出有影响的参数
      </div>
      <template #footer>
        <el-button @click="compareDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <WorkbenchFormulaSyncDialog
      v-if="syncDialogVisible"
      v-model="syncDialogVisible"
      :model-id="selectedVersion?.id"
      :module-code="syncModuleCode"
      @sync-success="handleSyncSuccess"
    />

    <WorkbenchFormulaMappingDialog
      v-if="mappingDialogVisible"
      v-model="mappingDialogVisible"
      :model-id="selectedVersion?.id"
      :module-code="activeModuleCode"
      :mappings="activeMappings"
      @saved="handleMappingSaved"
    />

    <WorkbenchCurveFormulaDialog
      v-model="curveFormulaDialogVisible"
      :lookup-items="lookupItems"
      :parameter-rows="[...parameterRows, ...allIntermediateSourceRows]"
      :initial-expression="activeFormulaDraft.expression || activeFormula.value?.expression || ''"
      @apply="applyCurveFormulaExpression"
    />


    <el-drawer
      v-model="allParametersDrawerVisible"
      title="基础参数管理"
      size="600px"
      destroy-on-close
    >
      <div class="all-parameters-drawer-content">
        <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center;">
          <el-button type="primary" @click="handleAddParameter">新增参数</el-button>
          <el-input v-model="parameterSearchKeyword" placeholder="搜索参数名称或编码" clearable style="width: 240px;" />
        </div>
        <el-table :data="filteredParameterRows" border stripe height="calc(100vh - 230px)">
          <el-table-column prop="paramName" label="参数名称" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">
              <el-input v-if="row.pendingCreate" v-model="row.paramName" size="small" placeholder="参数名称" @input="row.displayName = row.paramName" />
              <span v-else>{{ row.paramName }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="paramCode" label="参数编码" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <el-input v-if="row.pendingCreate" v-model="row.paramCode" size="small" placeholder="参数编码" />
              <span v-else>{{ row.paramCode }}</span>
            </template>
          </el-table-column>
          <el-table-column label="值类型" width="120">
            <template #default="{ row }">
              <el-select v-model="row.valueType" size="small" placeholder="请选择" @change="row.dirty = true">
                <el-option label="基础参数" value="basic" />
                <el-option label="产品参数" value="product" />
                <el-option label="环境参数" value="environment" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="参数值" min-width="150">
            <template #default="{ row }">
              <el-input
                v-model="row.value"
                size="small"
                placeholder="请输入"
                @change="row.dirty = true"
              />
            </template>
          </el-table-column>
          <el-table-column prop="unitCode" label="单位" width="80">
            <template #default="{ row }">
              <el-input v-if="row.pendingCreate" v-model="row.unitCode" size="small" placeholder="单位" />
              <span v-else>{{ row.unitCode }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" link @click="handleDeleteParameter(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <div style="flex: auto">
          <el-button @click="allParametersDrawerVisible = false">取消</el-button>
          <el-button type="primary" :loading="parameterSyncing" @click="handleParameterSync">保存并同步</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'

import { Plus, Setting, Refresh, VideoPlay, DataLine, Connection, Aim, TopRight, BottomRight, Loading } from '@element-plus/icons-vue'
import WorkbenchCalculationFlowPanel from '@/components/WorkbenchCalculationFlowPanel.vue'
import WorkbenchCurveFormulaDialog from '@/components/WorkbenchCurveFormulaDialog.vue'
import WorkbenchExplanationDrawer from '@/components/WorkbenchExplanationDrawer.vue'
import WorkbenchFormulaMainTable from '@/components/WorkbenchFormulaMainTable.vue'
import WorkbenchFormulaSyncDialog from '@/components/WorkbenchFormulaSyncDialog.vue'
import WorkbenchFormulaMappingDialog from '@/components/WorkbenchFormulaMappingDialog.vue'
import WorkbenchInputTable from '@/components/WorkbenchInputTable.vue'
import SmartSelectionPanel from '@/components/SmartSelectionPanel.vue'
import {
  fetchFamilyMatrix,
  fetchParameterLookups,
  fetchLatestWorkbenchSnapshot,
  saveWorkbenchParameters,
  fetchParameters,
  deleteModelParameterValue
} from '@/api/designPlatform'
import { mergeWorkbenchModelRows } from '@/api/designPlatform.helpers.mjs'
import {
  createWorkbenchFormulaModule,
  deleteWorkbenchFormula,
  createWorkbenchFormulaScene,
  deleteWorkbenchFormulasBatch,
  deleteWorkbenchFormulaModule,
  deleteWorkbenchFormulaScene,
  executeDrumDesign,
  fetchDrumTree,
  fetchWorkbenchFormulaModules,
  reorderWorkbenchFormulas,
  renameWorkbenchFormulaModule,
  renameWorkbenchFormulaScene,
  saveWorkbenchFormula,
  fetchFormulaParamMappings,
  saveFormulaParamMappings,
  analyzeDrumDesignImpact
} from '@/api/drumDesign'
import {
  applyWorkbenchExplanationDraft,
  buildModuleSummary,
  buildFormulaAutocompleteSections,
  buildExecutionIntermediateRows,
  buildCurveUpgradeHint,
  buildFormulaResultMap,
  buildWorkbenchCalculationFlow,
  buildWorkbenchCalculationPanelContext,
  buildCompareTargetOptions,
  buildVisibleWorkbenchBaseRows,
  buildWorkbenchParameterRows,
  buildWorkbenchParameterSavePayload,
  collectFormulaHighlights,
  groupWorkbenchFormulaModules,
  reorderFormulaRowsWithinScene,
  resolveActiveModuleSceneFormula,
  resolveFormulaAutocompleteKeyword,
  resolveFormulaArgumentHint,
  resolveFormulaInteractionState,
  resolveFormulaViewportTargetScrollTop,
  resolveNextFocusAfterFormulaDelete,
  resolveNextFocusAfterFormulaBatchDelete,
  resolveNextFocusAfterModuleDelete,
  resolveNextFocusAfterSceneDelete,
  toggleFormulaBatchSelection,
  extractFormulaParameterRows,
  splitFormulaParameterRows,
  updateWorkbenchParameterDraft
} from '@/api/drumDesign.helpers.mjs'
import { buildLookupSourceRows, buildLookupTargetQuery } from '@/api/drumDesignLookup.helpers.mjs'
import { evaluateFormulaExpression, FormulaEngineError } from '@/utils/formulaEngine.mjs'

const route = useRoute()
const router = useRouter()

const treeData = ref([])
const selectedNodeId = ref('')
const selectedType = ref(null)
const selectedFamily = ref(null)
const selectedVersion = ref(null)
const parameterRows = ref([])
const parameterSearchKeyword = ref('')
const filteredParameterRows = computed(() => {
  if (!parameterSearchKeyword.value) return parameterRows.value
  const keyword = parameterSearchKeyword.value.toLowerCase()
  return parameterRows.value.filter(row => 
    (row.paramName && row.paramName.toLowerCase().includes(keyword)) ||
    (row.paramCode && row.paramCode.toLowerCase().includes(keyword))
  )
})
const lookupItems = ref([])
const formulaModules = ref([])
const activeModuleCode = ref('')
const activeSceneCode = ref('')
const selectedFormulaKey = ref('')
const editingFormulaKey = ref('')
const moduleLastSceneMap = ref({})
const activeFormulaDraft = ref({})
const formulaCursorStart = ref(0)
const formulaCompositionActive = ref(false)
const latestResults = ref([])
const latestScope = ref({})
const executing = ref(false)
const formulaSaving = ref(false)
const formulaReordering = ref(false)
const formulaBatchDeleting = ref(false)
const editingSceneCode = ref('')
const sceneSaving = ref(false)
const formulaDeleting = ref(false)
const formulaBatchModeModuleCode = ref('')
const formulaBatchModeSceneCode = ref('')
const selectedFormulaBatchKeys = ref([])
const parameterSyncing = ref(false)
const compareTargetParam = ref('')
const compareDialogVisible = ref(false)
const impactAnalyzing = ref(false)
const impactResults = ref([])
const impactTargetResultName = ref('')
const syncDialogVisible = ref(false)
const syncModuleCode = ref('')
const activeMappings = ref([])
const mappingDialogVisible = ref(false)
const curveFormulaDialogVisible = ref(false)
const allParametersDrawerVisible = ref(false)
const workbenchViewMode = ref('formula')
const explanationDrawerVisible = ref(false)
const explanationTarget = ref({ type: 'module', key: '' })

const openAllParametersDrawer = () => {
  allParametersDrawerVisible.value = true
}
const activeFlowNodeId = ref('')
const flowDisplayMode = ref('all')
const flowViewportResetToken = ref(0)
const flowViewportState = ref({
  zoom: 1,
  center: ['50%', '50%']
})
const flowExplanationDraftMap = ref({})
const mainTableRef = ref(null)
let autoRunTimer = null
let designRequestSequence = 0

const formatMetric = (value, unitCode = '', paramName = '') => {
  const text = String(value ?? '').trim()
  if (!text) return '-'
  
  let formattedText = text
  if (!isNaN(parseFloat(text)) && ['功率', '输出扭矩', '输出转速'].some(name => paramName.includes(name))) {
    formattedText = parseFloat(text).toFixed(1)
  }
  
  return unitCode ? `${formattedText} ${unitCode}` : formattedText
}

const resolveSourceLabel = (source = '') => {
  const labels = {
    model: '型号矩阵',
    snapshot: '工作台快照',
    draft: '手动调整',
    catalog: '默认值',
    empty: '待补参数',
    formula: '计算结果'
  }
  return labels[String(source || '').trim()] || '待补参数'
}

// 智能选型持久化状态
const currentEquipment = ref(null)

const handleClearEquipment = () => {
  currentEquipment.value = null
  localStorage.removeItem('workbench_current_equipment')
}

const handleApplyEquipment = (equipment) => {
  console.log('应用设备选型:', equipment)
  
  currentEquipment.value = equipment
  if (equipment) {
    localStorage.setItem('workbench_current_equipment', JSON.stringify(equipment))
  }
  
  const motor = equipment.motor_params || equipment.item?.motor_params || {}
  const reducer = equipment.reducer_params || equipment.item?.reducer_params || {}
  
  let motorFreq = ''
  if (motor.voltage) {
    const freqMatch = String(motor.voltage).match(/(\d+)Hz/i)
    if (freqMatch) motorFreq = freqMatch[1]
  }

  const mapping = [
    { name: '电机_型号', val: motor.model, type: 'product' },
    { name: '电机_额定功率', val: motor.power, type: 'product' },
    { name: '电机_额定转速', val: motor.speed, type: 'product' },
    { name: '电机_频率', val: motorFreq, type: 'product' },
    { name: '电机_防护等级', val: motor.protection, type: 'product' },
    { name: '减速机_型号', val: reducer.model, type: 'product' },
    { name: '减速机_最大允许扭矩', val: reducer.max_torque, type: 'product' },
    { name: '减速机_减速比', val: reducer.ratio, type: 'product' },
    { name: '减速机_传动效率', val: reducer.efficiency, type: 'product' },
    { name: '减速机_输出转矩', val: equipment.torque || equipment.item?.torque || reducer.max_torque, type: 'product' }
  ]

  let modified = false
  mapping.forEach(p => {
    if (p.val !== undefined && p.val !== null && p.val !== '-') {
      const existing = parameterRows.value.find(r => r.paramName === p.name)
      if (existing) {
        if (existing.value !== String(p.val)) {
          existing.value = String(p.val)
          existing.dirty = true
          modified = true
        }
      } else {
        parameterRows.value.unshift({
          parameterId: 0,
          paramCode: '',
          paramName: p.name,
          displayName: p.name,
          unitCode: '',
          valueType: p.type,
          value: String(p.val),
          dirty: true,
          source: 'draft',
          pendingCreate: true
        })
        modified = true
      }
    }
  })

  if (modified) {
    ElMessage.success('选型参数已作为基础参数加入，请前往保存并可用于校核公式')
  } else {
    ElMessage.success('已应用选型型号，参数无变化')
  }
}

const buildFormulaRowKey = (row = {}) => {
  if (row?._rowKey) {
    return row._rowKey
  }
  if (row?._isNewDraft) {
    return `draft:new:${row?.module_code || ''}:${row?.scene_code || ''}`
  }
  const normalizedId = Number(row?.id || 0)
  if (normalizedId > 0) {
    return `id:${normalizedId}`
  }
  if (!row?.module_code && !row?.scene_code && !row?.name) {
    return ''
  }
  return `${row?.module_code || ''}::${row?.scene_code || ''}::${row?.name || ''}`
}

const buildFormulaDomId = (row = {}) => `workbench-formula-${encodeURIComponent(buildFormulaRowKey(row))}`

const formulaRows = computed(() =>
  formulaModules.value.flatMap((module) => module.scenes.flatMap((scene) => scene.rows || []))
)

const serializeModuleShells = (modules = formulaModules.value) =>
  (Array.isArray(modules) ? modules : []).map((module) => ({
    module_code: module.moduleCode,
    module_name: module.moduleName,
    scenes: (module.scenes || []).map((scene) => ({
      scene_code: scene.sceneCode,
      scene_name: scene.sceneName
    }))
  }))

const decorateFormulaRow = (row = {}, rows = formulaRows.value) => {
  const sceneRows = (Array.isArray(rows) ? rows : [])
    .filter((item) =>
      String(item.module_code || '') === String(row.module_code || '') &&
      String(item.scene_code || '') === String(row.scene_code || '')
    )
    .sort((left, right) => {
      const orderDiff = Number(left.sort_order || 0) - Number(right.sort_order || 0)
      return orderDiff || Number(left.id || 0) - Number(right.id || 0)
    })
  const sceneIndex = sceneRows.findIndex((item) => buildFormulaRowKey(item) === buildFormulaRowKey(row))
  return {
    ...row,
    _rowKey: buildFormulaRowKey(row),
    domId: buildFormulaDomId(row),
    _disableMoveUp: sceneIndex <= 0,
    _disableMoveDown: sceneIndex < 0 || sceneIndex >= sceneRows.length - 1
  }
}

const syncActiveFormulaDraft = (row = {}) => {
  activeFormulaDraft.value = decorateFormulaRow(row)
}

const setSelectedFormula = (row = {}) => {
  selectedFormulaKey.value = buildFormulaRowKey(row)
}

const clearFormulaDraft = () => {
  activeFormulaDraft.value = {}
}

const resetFormulaBatchDeleteState = () => {
  formulaBatchModeModuleCode.value = ''
  formulaBatchModeSceneCode.value = ''
  selectedFormulaBatchKeys.value = []
}

const stopFormulaEditing = () => {
  editingFormulaKey.value = ''
  clearFormulaDraft()
}

const cancelSceneEditing = () => {
  editingSceneCode.value = ''
}

const beginFormulaEditing = (row = {}) => {
  const decorated = decorateFormulaRow(row)
  activeFormulaDraft.value = decorated
  const rowKey = buildFormulaRowKey(decorated)
  selectedFormulaKey.value = rowKey
  editingFormulaKey.value = rowKey
}

const activeFormulaKey = computed(() => selectedFormulaKey.value)

const activeFormula = computed(() => {
  const matched = formulaRows.value.find((row) => buildFormulaRowKey(row) === activeFormulaKey.value)
  if (matched) {
    return matched
  }
  return activeFormulaDraft.value?._isNewDraft ? activeFormulaDraft.value : {}
})

const displayFormulaModules = computed(() => {
  const rows = formulaRows.value.map((row) => decorateFormulaRow(row, formulaRows.value))
  const displayRows = activeFormulaDraft.value?._isNewDraft
    ? [
        decorateFormulaRow({
          ...activeFormulaDraft.value,
          displayName: activeFormulaDraft.value.name || '未命名公式'
        }, formulaRows.value),
        ...rows
      ]
    : rows
  return groupWorkbenchFormulaModules(displayRows, serializeModuleShells())
})

const activeModule = computed(() =>
  displayFormulaModules.value.find((module) => module.moduleCode === activeModuleCode.value) || null
)

const currentTypeTreeNode = computed(() =>
  treeData.value.find((node) => String(node.raw?.id || '') === String(selectedType.value?.id || '')) || null
)

const currentFamilyTreeNode = computed(() =>
  (currentTypeTreeNode.value?.children || []).find((node) => String(node.raw?.id || '') === String(selectedFamily.value?.id || '')) || null
)

const selectedFamilyRangeId = computed(() => String(selectedFamily.value?.id || ''))
const selectedVersionRangeId = computed(() => String(selectedVersion.value?.id || ''))

const familyRangeOptions = computed(() =>
  (currentTypeTreeNode.value?.children || []).map((node) => ({
    label: node.raw?.family_code || node.label || '未命名系列',
    value: String(node.raw?.id || '')
  }))
)

const versionRangeOptions = computed(() =>
  (currentFamilyTreeNode.value?.children || []).map((node) => ({
    label: node.raw?.version_code || node.label || '未命名型号',
    value: String(node.raw?.id || '')
  }))
)

const activeScene = computed(() =>
  activeModule.value?.scenes?.find((scene) => scene.sceneCode === activeSceneCode.value) || null
)

const activePath = computed(() => ({
  moduleName: activeModule.value?.moduleName || '',
  sceneName: activeScene.value?.sceneName || '',
  formulaName: activeFormulaContext.value?.name || ''
}))

const activeModuleFormulaRows = computed(() =>
  (activeModule.value?.scenes || []).flatMap((scene, index) =>
    (scene.rows || []).map((row, rowIndex) => ({
      ...row,
      sceneCode: scene.sceneCode || '',
      sceneName: scene.sceneName || '未命名场景',
      _rowKey: row._rowKey || `${activeModule.value?.moduleCode || 'module'}:${scene.sceneCode || 'scene'}:${row.id || row.name || `${index}-${rowIndex}`}`
    }))
  )
)

const activeExplanationTargetKey = computed(() =>
  String(explanationTarget.value?.key || activeFormulaKey.value || '')
)

const moduleInputRows = computed(() => {
  const baseMap = new Map();
  
  // 始终显示用户手动添加或修改过的参数（包括通过选型进入的 draft/pendingCreate 参数）
  parameterRows.value.forEach((row) => {
    if (row.pendingCreate || row.source === 'draft') {
      baseMap.set(row.paramName || String(Math.random()), row);
    }
  });

  if (visibleBaseRows.value.length) {
    visibleBaseRows.value.forEach((row) => {
      baseMap.set(row.paramName, row);
    });
  } else {
    const scopedRows = (activeScene.value?.rows || activeModuleFormulaRows.value || []).filter(Boolean)
    if (scopedRows.length) {
      const mergedVariables = scopedRows.reduce((accumulator, row) => {
        Object.entries(row?.variables || {}).forEach(([name, unitCode]) => {
          const normalizedName = String(name || '').trim()
          if (!normalizedName || accumulator[normalizedName] !== undefined) {
            return
          }
          accumulator[normalizedName] = String(unitCode || '').trim()
        })
        return accumulator
      }, {})
      const derivedRows = buildVisibleWorkbenchBaseRows({ variables: mergedVariables }, parameterRows.value)
      derivedRows.forEach((row) => baseMap.set(row.paramName, row));
    } else {
      parameterRows.value.slice(0, 20).forEach((row) => baseMap.set(row.paramName, row));
    }
  }

  return Array.from(baseMap.values()).sort((left, right) => {
    // 尚未命名的参数放在最前面
    if (!left.paramName) return -1;
    if (!right.paramName) return 1;
    return String(left.paramName || '').localeCompare(String(right.paramName || ''), 'zh-CN');
  });
})

const upsertFormulaModules = (modules = []) => {
  formulaModules.value = groupWorkbenchFormulaModules([], modules)
}

const replaceFormulaRows = (rows = [], moduleShells = serializeModuleShells()) => {
  formulaModules.value = groupWorkbenchFormulaModules(rows, moduleShells)
}

const syncWorkbenchFocus = () => {
  const resolved = resolveActiveModuleSceneFormula({
    modules: displayFormulaModules.value,
    activeModuleCode: activeModuleCode.value,
    activeSceneCode: activeSceneCode.value,
    activeFormulaKey: activeFormulaKey.value,
    lastSceneMap: moduleLastSceneMap.value
  })
  activeModuleCode.value = resolved.activeModuleCode
  activeSceneCode.value = resolved.activeSceneCode
  if (resolved.activeModuleCode && resolved.activeSceneCode) {
    moduleLastSceneMap.value = {
      ...moduleLastSceneMap.value,
      [resolved.activeModuleCode]: resolved.activeSceneCode
    }
  }
  setSelectedFormula(resolved.activeFormula || {})
  if (editingFormulaKey.value && editingFormulaKey.value !== buildFormulaRowKey(resolved.activeFormula || {})) {
    stopFormulaEditing()
  }
}

const applyModuleNameLocally = (moduleCode, moduleName) => {
  formulaModules.value = formulaModules.value.map((module) => {
    if (module.moduleCode !== moduleCode) {
      return module
    }
    return {
      ...module,
      moduleName,
      scenes: module.scenes.map((scene) => ({
        ...scene,
        moduleName
      }))
    }
  })
  if (String(activeFormulaDraft.value?.module_code || '') === String(moduleCode || '')) {
    activeFormulaDraft.value = {
      ...activeFormulaDraft.value,
      module_name: moduleName
    }
  }
}

const applySceneNameLocally = (moduleCode, sceneCode, sceneName) => {
  formulaModules.value = formulaModules.value.map((module) => {
    if (module.moduleCode !== moduleCode) {
      return module
    }
    return {
      ...module,
      scenes: module.scenes.map((scene) => {
        if (scene.sceneCode !== sceneCode) {
          return scene
        }
        return {
          ...scene,
          sceneName,
          rows: (scene.rows || []).map((row) => ({
            ...row,
            scene_name: sceneName,
            sceneName
          }))
        }
      })
    }
  })
  if (
    String(activeFormulaDraft.value?.module_code || '') === String(moduleCode || '') &&
    String(activeFormulaDraft.value?.scene_code || '') === String(sceneCode || '')
  ) {
    activeFormulaDraft.value = {
      ...activeFormulaDraft.value,
      scene_name: sceneName,
      sceneName
    }
  }
}

const formulaResultMap = computed(() => buildFormulaResultMap(latestResults.value))

const activeCalculationFlow = computed(() =>
  buildWorkbenchCalculationFlow({
    moduleCode: activeModuleCode.value,
    focusedFormulaName: activeFormulaContext.value?.name || '',
    formulaRows: formulaRows.value,
    parameterRows: parameterRows.value,
    latestResults: latestResults.value,
    latestScope: latestScope.value
  })
)

const activeFlowGraph = computed(() => activeCalculationFlow.value)
const activeFlowNodeMap = computed(() => {
  const map = new Map()
  ;(activeCalculationFlow.value?.nodes || []).forEach((node) => {
    if (String(node?.formulaKey || '').trim()) {
      map.set(String(node.formulaKey).trim(), node)
    }
    if (String(node?.name || '').trim()) {
      map.set(`name:${String(node.name).trim()}`, node)
    }
  })
  return map
})
const activeFlowPanelContext = computed(() => {
  const baseContext = buildWorkbenchCalculationPanelContext(activeCalculationFlow.value, activeFlowNodeId.value)
  const nodeId = String(activeFlowNodeId.value || '')
  const draft = flowExplanationDraftMap.value[nodeId] || {}
  return {
    ...baseContext,
    explanation: baseContext.explanation ? applyWorkbenchExplanationDraft(baseContext.explanation, draft) : null
  }
})

const hasDirtyParameters = computed(() => parameterRows.value.some((row) => row.dirty))

const buildParameterPayload = () => {
  return parameterRows.value.reduce((payload, row) => {
    const value = String(row.value || '').trim()
    if (value) {
      payload[row.paramName] = value
    }
    return payload
  }, {})
}

const buildFormulaVariables = (expression = '', fallbackVariables = {}) => {
  const normalizedExpression = String(expression || '')
  const candidates = [
    ...parameterRows.value.map((row) => ({ name: row.paramName, unitCode: row.unitCode || '' })),
    ...allIntermediateSourceRows.value.map((row) => ({ name: row.paramName, unitCode: row.unitCode || '' }))
  ]
  const matched = {}
  for (const candidate of candidates) {
    if (!candidate.name || !normalizedExpression.includes(candidate.name)) continue
    matched[candidate.name] = candidate.unitCode || fallbackVariables?.[candidate.name] || ''
  }
  return Object.keys(matched).length ? matched : { ...(fallbackVariables || {}) }
}

const activeFormulaContext = computed(() => {
  const base = activeFormula.value || {}
  const draft = activeFormulaDraft.value || {}
  const expression = draft.expression ?? base.expression ?? ''
  return {
    ...base,
    ...draft,
    variables: buildFormulaVariables(expression, draft.variables || base.variables || {})
  }
})

const visibleBaseSourceRows = computed(() => extractFormulaParameterRows(activeFormulaContext.value, parameterRows.value))

const allIntermediateSourceRows = computed(() =>
  buildExecutionIntermediateRows({
    formulaRows: formulaRows.value,
    latestResults: latestResults.value,
    latestScope: latestScope.value
  })
)

const visibleIntermediateSourceRows = computed(() =>
  extractFormulaParameterRows(activeFormulaContext.value, allIntermediateSourceRows.value)
)

const groupedParameterRows = computed(() =>
  splitFormulaParameterRows(activeFormulaContext.value, [
    ...visibleBaseSourceRows.value,
    ...visibleIntermediateSourceRows.value
  ])
)

const hasActiveFormula = computed(() => Boolean(activeFormulaKey.value))

const visibleBaseRows = computed(() => {
  if (!hasActiveFormula.value) {
    return []
  }
  return buildVisibleWorkbenchBaseRows(activeFormulaContext.value, parameterRows.value)
})

const visibleIntermediateRows = computed(() => {
  if (!hasActiveFormula.value) {
    return []
  }
  return groupedParameterRows.value.intermediateRows
})

const visibleLookupSourceRows = computed(() =>
  buildLookupSourceRows({
    activeFormula: activeFormulaContext.value,
    formulaResultMap: formulaResultMap.value,
    lookupItems: lookupItems.value
  })
)

const activeFormulaPanelContext = computed(() => ({
  title: String(activeFormulaContext.value?.name || '').trim() || '公式参数区',
  nodeType: 'formula-panel',
  explanation: null,
  summary: [],
  parameters: visibleBaseRows.value,
  lookups: visibleLookupSourceRows.value,
  constraints: []
}))

const activeParameterPanelContext = computed(() =>
  workbenchViewMode.value === 'flow'
    ? activeFlowPanelContext.value
    : activeFormulaPanelContext.value
)

const formulaHighlightMap = computed(() => collectFormulaHighlights(activeFormulaContext.value, formulaRows.value))

const autocompleteKeyword = computed(() => {
  if (formulaCompositionActive.value) {
    return ''
  }
  return resolveFormulaAutocompleteKeyword({
    expression: String(activeFormulaContext.value?.expression || ''),
    selectionStart: formulaCursorStart.value
  })
})

const autocompleteSections = computed(() =>
  buildFormulaAutocompleteSections({
    keyword: autocompleteKeyword.value,
    parameterRows: [...parameterRows.value, ...allIntermediateSourceRows.value],
    lookupItems: lookupItems.value
  })
)

const activeFormulaArgumentHint = computed(() =>
  resolveFormulaArgumentHint({
    expression: String(activeFormulaContext.value?.expression || ''),
    selectionStart: formulaCursorStart.value
  })
)

const canOpenCompare = computed(() => {
  return Boolean(selectedVersion.value?.id && activeFormulaContext.value?.name && visibleBaseRows.value.length)
})

const compareTargetOptions = computed(() => buildCompareTargetOptions(groupedParameterRows.value.baseRows, compareTargetParam.value))
const activeCurveUpgradeHint = computed(() => buildCurveUpgradeHint(activeFormulaContext.value?.expression || ''))

const mainTableRows = computed(() => {
  const modules = activeModule.value ? [activeModule.value] : displayFormulaModules.value.slice(0, 1)
  return modules.flatMap((module) =>
    (module.scenes || []).flatMap((scene) => {
      const sceneRows = (scene.rows || []).map((row) => {
        const flowNode =
          activeFlowNodeMap.value.get(String(row?._rowKey || '').trim()) ||
          activeFlowNodeMap.value.get(`name:${String(row?.name || '').trim()}`)
        const resultInfo = formulaResultMap.value[String(row?.name || '').trim()] || {}
        const rawValue = resultInfo.displayText || formatMetric(
          latestScope.value?.[String(row?.name || '').trim()] ?? resultInfo.value,
          resultInfo.unitCode || row?.unit_code || row?.unitCode || '',
          row?.name || ''
        )
        const dependencyCount = Object.keys(row?.variables || {}).length
        return {
          rowType: flowNode?.semanticRole === 'result' ? 'result' : 'formula',
          key: row._rowKey,
          domId: row.domId,
          name: row.displayName || row.name || '未命名公式',
          expression: row.expression || '',
          value: rawValue || '-',
          meta: '',
          raw: row
        }
      })
      return [
        {
          rowType: 'group',
          key: `group:${module.moduleCode}:${scene.sceneCode}`,
          label: scene.sceneName || module.moduleName || '未命名分组',
          moduleCode: module.moduleCode,
          sceneCode: scene.sceneCode,
          moduleName: module.moduleName,
          sceneName: scene.sceneName
        },
        ...sceneRows
      ]
    })
  )
})

const buildExplanationResources = (formulaRow = {}, explanation = null) => {
  const resources = []
  const directResources = explanation?.resources || formulaRow?.resources || {}
  if (Array.isArray(directResources)) {
    directResources.forEach((item) => {
      if (!item) return
      resources.push({
        type: String(item.type || 'resource'),
        typeLabel: String(item.typeLabel || item.type || '资源'),
        title: String(item.title || '说明资源'),
        content: String(item.content || item.url || '')
      })
    })
  } else if (directResources && typeof directResources === 'object') {
    const labelMap = {
      image: '图片',
      video: '视频',
      document: '文档'
    }
    Object.entries(directResources).forEach(([type, value]) => {
      const content = String(value || '').trim()
      if (!content) return
      resources.push({
        type,
        typeLabel: labelMap[type] || '资源',
        title: `${labelMap[type] || '资源'}入口`,
        content
      })
    })
  }
  buildLookupSourceRows({
    activeFormula: formulaRow,
    formulaResultMap: formulaResultMap.value,
    lookupItems: lookupItems.value
  }).forEach((row) => {
    resources.push({
      type: 'lookup',
      typeLabel: '查表附录',
      title: row.lookupName || '附录资源',
      content: [row.rangeText, row.detailText].filter(Boolean).join(' | ')
    })
  })
  return resources
}

const explanationPanel = computed(() => {
  if (String(explanationTarget.value?.type || '') === 'input') {
    const targetRow = moduleInputRows.value.find(
      (row) => String(row?.paramName || '').trim() === String(explanationTarget.value?.key || '').trim()
    )
    const matchedNode = (activeCalculationFlow.value?.nodes || []).find((node) =>
      ['input', 'parameter', 'lookup'].includes(String(node?.nodeType || '')) &&
      String(node?.name || '').trim() === String(targetRow?.paramName || '').trim()
    )
    const explanation = matchedNode?.panelContext?.explanation || null
    const currentValue = formatMetric(targetRow?.value, targetRow?.unitCode || '', targetRow?.paramName || '')
    const details = [
      currentValue !== '-' ? `当前值：${currentValue}` : '',
      targetRow?.source ? `来源：${resolveSourceLabel(targetRow.source)}` : '',
      explanation?.derivation || '',
      explanation?.impact || ''
    ].filter(Boolean)
    return {
      title: targetRow?.displayName || targetRow?.paramName || '输入参数说明',
      summary: explanation?.purpose || '当前输入项会参与主表公式计算。',
      details,
      resources: []
    }
  }

  const targetKey = String(explanationTarget.value?.key || activeFormulaKey.value || '').trim()
  const formulaRow = formulaRows.value.find((row) => String(row?._rowKey || '').trim() === targetKey) || activeFormulaContext.value
  const flowNode =
    activeFlowNodeMap.value.get(targetKey) ||
    activeFlowNodeMap.value.get(`name:${String(formulaRow?.name || '').trim()}`)
  const explanation = flowNode?.panelContext?.explanation || null
  const detailTexts = [
    explanation?.keyInputs?.length
      ? `关键输入：${explanation.keyInputs.map((item) => `${item.paramName}${item.value ? `=${item.value}${item.unit ? ` ${item.unit}` : ''}` : ''}`).join('；')}`
      : '',
    explanation?.derivation || '',
    explanation?.impact || ''
  ].filter(Boolean)
  return {
    title: formulaRow?.displayName || formulaRow?.name || '公式说明',
    summary: explanation?.purpose || String(formulaRow?.expression || '').trim() || '当前暂无补充说明。',
    details: detailTexts,
    resources: buildExplanationResources(formulaRow, explanation)
  }
})

const loadModelFormulas = async (preferredRow = null) => {
  if (!selectedVersion.value?.id) {
    formulaModules.value = []
    activeModuleCode.value = ''
    activeSceneCode.value = ''
    cancelSceneEditing()
    setSelectedFormula({})
    stopFormulaEditing()
    scheduleParameterPanelPosition()
    return
  }
  const modules = await fetchWorkbenchFormulaModules(selectedVersion.value.id)
  upsertFormulaModules(modules)
  if (preferredRow?.module_code) {
    activeModuleCode.value = preferredRow.module_code
    activeSceneCode.value = preferredRow.scene_code || ''
  }
  syncWorkbenchFocus()
  scheduleAutoDesign()
  scheduleParameterPanelPosition()
}

const reloadMatrixParameters = async () => {
  if (!selectedFamily.value?.id || !selectedVersion.value?.id) return
  const matrix = await fetchFamilyMatrix(selectedFamily.value.id)
  const modelRows = buildWorkbenchParameterRows(matrix, selectedVersion.value.id).map((row) => ({
    ...row,
    dirty: false,
    source: row.value ? 'model' : 'empty'
  }))
  parameterRows.value = mergeWorkbenchModelRows({
    modelRows,
    snapshotMap: new Map()
  })
  ElMessage.success('已按型号矩阵重载基础参数')
}

const loadParametersWithPriority = async () => {
  if (!selectedFamily.value?.id || !selectedVersion.value?.id) return
  const [matrix, allParams] = await Promise.all([
    fetchFamilyMatrix(selectedFamily.value.id),
    fetchParameters()
  ])
  
  const modelRows = buildWorkbenchParameterRows(matrix, selectedVersion.value.id).map((row) => ({
    ...row,
    dirty: false,
    source: row.value ? 'model' : 'empty'
  }))
  
  const existingIds = new Set(modelRows.map(r => r.parameterId))
  const existingNames = new Set(modelRows.map(r => r.paramName))
  
  const extraRows = allParams
    .filter(p => !existingIds.has(p.id) && !existingNames.has(p.param_name))
    .map(p => ({
      parameterId: p.id,
      paramCode: p.param_code || '',
      paramName: p.param_name || '',
      displayName: p.display_name || p.param_name || '',
      unitCode: p.unit_code || '',
      valueType: p.value_type || 'basic',
      value: '',
      dirty: false,
      source: 'empty'
    }))
    
  const snapshot = await fetchLatestWorkbenchSnapshot(selectedVersion.value.id)
  const snapshotMap = new Map((snapshot.rows || []).map((row) => [row.parameter_id, row.snapshot_value]))
  parameterRows.value = mergeWorkbenchModelRows({
    modelRows: [...modelRows, ...extraRows],
    snapshotMap
  })
}

const loadLookupItems = async () => {
  try {
    lookupItems.value = await fetchParameterLookups()
  } catch {
    lookupItems.value = []
  }
}

const normalizeRouteQueryValue = (value) => {
  if (Array.isArray(value)) {
    return String(value[0] || '')
  }
  return String(value || '')
}

const buildWorkbenchRouteQuery = ({
  typeId,
  familyId,
  versionId,
  moduleCode
} = {}) => {
  const query = {}
  const normalizedTypeId = normalizeRouteQueryValue(typeId)
  const normalizedFamilyId = normalizeRouteQueryValue(familyId)
  const normalizedVersionId = normalizeRouteQueryValue(versionId)
  const normalizedModuleCode = normalizeRouteQueryValue(moduleCode)

  if (normalizedTypeId) {
    query.typeId = normalizedTypeId
  }
  if (normalizedFamilyId) {
    query.familyId = normalizedFamilyId
  }
  if (normalizedVersionId) {
    query.versionId = normalizedVersionId
  }
  if (normalizedModuleCode) {
    query.moduleCode = normalizedModuleCode
  }

  return query
}

const syncWorkbenchRouteQuery = async (overrides = {}) => {
  const nextQuery = buildWorkbenchRouteQuery({
    typeId: overrides.typeId ?? selectedType.value?.id ?? route.query.typeId,
    familyId: overrides.familyId ?? selectedFamily.value?.id ?? route.query.familyId,
    versionId: overrides.versionId ?? selectedVersion.value?.id ?? route.query.versionId,
    moduleCode: overrides.moduleCode ?? activeModuleCode.value ?? route.query.moduleCode
  })
  const currentQuery = buildWorkbenchRouteQuery({
    typeId: route.query.typeId,
    familyId: route.query.familyId,
    versionId: route.query.versionId,
    moduleCode: route.query.moduleCode
  })

  if (JSON.stringify(nextQuery) === JSON.stringify(currentQuery)) {
    return
  }

  await router.replace({
    name: 'DesignWorkbench',
    query: nextQuery
  })
}

const resolveTreeSelection = (typeId, familyId, versionId) => {
  const normalizedTypeId = normalizeRouteQueryValue(typeId)
  const normalizedFamilyId = normalizeRouteQueryValue(familyId)
  const normalizedVersionId = normalizeRouteQueryValue(versionId)

  if (normalizedVersionId) {
    for (const typeNode of treeData.value) {
      for (const familyNode of typeNode.children || []) {
        const versionNode = (familyNode.children || []).find(
          (item) => String(item.raw?.id || '') === normalizedVersionId
        )
        if (versionNode) {
          return {
            data: versionNode,
            type: typeNode.raw,
            family: familyNode.raw,
            version: versionNode.raw
          }
        }
      }
    }
  }

  if (normalizedFamilyId) {
    for (const typeNode of treeData.value) {
      for (const familyNode of typeNode.children || []) {
        if (String(familyNode.raw?.id || '') === normalizedFamilyId) {
          const versionNode = familyNode.children?.[0] || null
          return {
            data: versionNode || familyNode,
            type: typeNode.raw,
            family: familyNode.raw,
            version: versionNode?.raw || null
          }
        }
      }
    }
  }

  if (normalizedTypeId) {
    const typeNode = treeData.value.find((item) => String(item.raw?.id || '') === normalizedTypeId)
    if (typeNode) {
      const familyNode = typeNode.children?.[0] || null
      const versionNode = familyNode?.children?.[0] || null
      return {
        data: versionNode || familyNode || typeNode,
        type: typeNode.raw,
        family: familyNode?.raw || null,
        version: versionNode?.raw || null
      }
    }
  }

  for (const typeNode of treeData.value) {
    for (const familyNode of typeNode.children || []) {
      const versionNode = familyNode.children?.[0] || null
      return {
        data: versionNode || familyNode,
        type: typeNode.raw,
        family: familyNode.raw,
        version: versionNode?.raw || null
      }
    }
  }
  return null
}

const pickDefaultSelection = () => {
  const firstType = treeData.value[0]
  const firstFamily = firstType?.children?.[0]
  const firstVersion = firstFamily?.children?.[0]
  if (!firstType) return null
  return {
    data: firstVersion || firstFamily || firstType,
    type: firstType.raw,
    family: firstFamily?.raw || null,
    version: firstVersion?.raw || null
  }
}

const applyResolvedSelection = async ({ data, type, family, version }) => {
  selectedNodeId.value = data?.id || ''
  selectedType.value = type || null
  selectedFamily.value = family || null
  selectedVersion.value = version || null
  resetFormulaBatchDeleteState()
  cancelSceneEditing()
  latestResults.value = []
  latestScope.value = {}
  compareDialogVisible.value = false
  compareTargetParam.value = ''
  explanationDrawerVisible.value = false
  explanationTarget.value = { type: 'module', key: '' }
  activeFlowNodeId.value = ''
  flowDisplayMode.value = 'all'
  flowViewportResetToken.value = 0
  flowViewportState.value = {
    zoom: 1,
    center: ['50%', '50%']
  }

  if (family?.id && version?.id) {
    const preferredModuleCode = activeModuleCode.value || normalizeRouteQueryValue(route.query.moduleCode)
    await syncWorkbenchRouteQuery({
      typeId: type?.id,
      familyId: family.id,
      versionId: version.id,
      moduleCode: preferredModuleCode
    })
    await Promise.all([
      loadParametersWithPriority(),
      loadModelFormulas({
        module_code: preferredModuleCode,
        scene_code: activeSceneCode.value
      })
    ])
    scheduleAutoDesign()
  } else {
    await syncWorkbenchRouteQuery({
      typeId: type?.id,
      familyId: '',
      versionId: '',
      moduleCode: activeModuleCode.value || route.query.moduleCode
    })
    parameterRows.value = []
    formulaModules.value = []
    activeModuleCode.value = ''
    activeSceneCode.value = ''
    setSelectedFormula({})
    stopFormulaEditing()
  }
}

const loadTree = async () => {
  treeData.value = await fetchDrumTree()
  const target =
    resolveTreeSelection(route.query.typeId, route.query.familyId, route.query.versionId) ||
    pickDefaultSelection()
  if (target?.data) {
    await applyResolvedSelection(target)
  }
}

const handleTreeSelect = async ({ data, node }) => {
  if (data?.level === 'version') {
    await applyResolvedSelection({
      data,
      type: node?.parent?.parent?.data?.raw,
      family: node?.parent?.data?.raw,
      version: data.raw
    })
    return
  }
  if (data?.level === 'family') {
    const versionNode = data.children?.[0] || null
    await applyResolvedSelection({
      data: versionNode || data,
      type: node?.parent?.data?.raw,
      family: data.raw,
      version: versionNode?.raw || null
    })
    return
  }
  const familyNode = data.children?.[0] || null
  const versionNode = familyNode?.children?.[0] || null
  await applyResolvedSelection({
    data: versionNode || familyNode || data,
    type: data.raw,
    family: familyNode?.raw || null,
    version: versionNode?.raw || null
  })
}

const handleFamilyRangeChange = async (familyId) => {
  const targetNode = (currentTypeTreeNode.value?.children || []).find(
    (node) => String(node.raw?.id || '') === String(familyId || '')
  )
  if (!targetNode) {
    return
  }
  const versionNode = targetNode.children?.[0] || null
  await applyResolvedSelection({
    data: versionNode || targetNode,
    type: currentTypeTreeNode.value?.raw || selectedType.value,
    family: targetNode.raw,
    version: versionNode?.raw || null
  })
}

const handleVersionRangeChange = async (versionId) => {
  const targetNode = (currentFamilyTreeNode.value?.children || []).find(
    (node) => String(node.raw?.id || '') === String(versionId || '')
  )
  if (!targetNode) {
    return
  }
  await applyResolvedSelection({
    data: targetNode,
    type: currentTypeTreeNode.value?.raw || selectedType.value,
    family: currentFamilyTreeNode.value?.raw || selectedFamily.value,
    version: targetNode.raw
  })
}

const handleFormulaSelect = (row) => {
  if (row?._isNewDraft) {
    return
  }
  activeModuleCode.value = row?.module_code || activeModuleCode.value
  activeSceneCode.value = row?.scene_code || activeSceneCode.value
  const interaction = resolveFormulaInteractionState({
    currentSelectedKey: selectedFormulaKey.value,
    currentEditingKey: editingFormulaKey.value,
    nextSelectedKey: buildFormulaRowKey(row)
  })
  selectedFormulaKey.value = interaction.selectedKey
  if (interaction.editingKey) {
    beginFormulaEditing(row)
  } else {
    stopFormulaEditing()
  }
  explanationTarget.value = {
    type: 'formula',
    key: buildFormulaRowKey(row)
  }
  void scrollToFormula(row)
  scheduleParameterPanelPosition()
}

const handleInputFocus = (row = {}) => {
  explanationTarget.value = {
    type: 'input',
    key: String(row?.paramName || '').trim()
  }
}

const handleMainTableRowSelect = (row = {}) => {
  if (row?.rowType === 'group' || !row?.raw) {
    return
  }
  
  if (row.raw?._isNewDraft) {
    return
  }

  activeModuleCode.value = row.raw?.module_code || activeModuleCode.value
  activeSceneCode.value = row.raw?.scene_code || activeSceneCode.value
  
  const nextKey = buildFormulaRowKey(row.raw)
  selectedFormulaKey.value = nextKey
  
  explanationTarget.value = {
    type: 'formula',
    key: nextKey
  }
  void scrollToFormula(row.raw)
  scheduleParameterPanelPosition()
}

const handleFormulaEdit = (row = {}) => {
  if (row?._isNewDraft) {
    return
  }
  handleMainTableRowSelect({ rowType: 'formula', raw: row })
  beginFormulaEditing(row)
}

const handleOpenExplanation = (row = {}) => {
  handleMainTableRowSelect(row)
  explanationDrawerVisible.value = true
}

const resolveDefaultFlowNodeId = (graph = activeCalculationFlow.value) => {
  const nodes = Array.isArray(graph?.nodes) ? graph.nodes : []
  const resultNode = nodes.find((node) => node.semanticRole === 'result')
  if (resultNode?.id) {
    return String(resultNode.id)
  }
  const activeFormulaNode = nodes.find((node) => String(node?.formulaKey || '') === String(activeFormulaKey.value || ''))
  if (activeFormulaNode?.id) {
    return String(activeFormulaNode.id)
  }
  return String(nodes[0]?.id || '')
}

const syncFlowSelectionFromFormula = () => {
  flowDisplayMode.value = 'all'
  activeFlowNodeId.value = ''
  flowViewportResetToken.value += 1
}

const showAllFlowChains = () => {
  flowDisplayMode.value = 'all'
  activeFlowNodeId.value = ''
  flowViewportResetToken.value += 1
}

const resetFlowView = () => {
  flowDisplayMode.value = 'all'
  activeFlowNodeId.value = ''
  flowViewportResetToken.value += 1
}

const handleFlowNodeSelect = (node = {}) => {
  flowDisplayMode.value = 'default'
  activeFlowNodeId.value = String(node?.id || '')
}

const handleFlowNodeDrag = ({ nodeId, x, y }) => {
  const node = activeFlowGraph.value.nodes.find(n => n.id === nodeId)
  if (node) {
    node.x = x
    node.y = y
  }
}

const handleFlowViewportChange = (nextViewport = {}) => {
  flowViewportState.value = {
    zoom: Number(nextViewport?.zoom || 1),
    center: Array.isArray(nextViewport?.center) ? [...nextViewport.center] : ['50%', '50%']
  }
}

const handleExplanationUpdate = (data) => {
  if (explanationTarget.value?.type === 'formula') {
    const key = explanationTarget.value.key
    let row = mainTableRows.value.find((r) => r.key === key)?.raw
    if (!row) return
    
    if (editingFormulaKey.value !== key) {
      beginFormulaEditing(row)
    }
    
    if (activeFormulaDraft.value) {
      activeFormulaDraft.value = {
        ...activeFormulaDraft.value,
        description: data.summary,
        resources: data.resources
      }
    }
  }
}

const handleExplanationChange = ({ field, value } = {}) => {
  const nodeId = String(activeFlowNodeId.value || '')
  if (workbenchViewMode.value !== 'flow' || !nodeId || !['purpose', 'impact'].includes(field)) {
    return
  }
  flowExplanationDraftMap.value = {
    ...flowExplanationDraftMap.value,
    [nodeId]: {
      ...(flowExplanationDraftMap.value[nodeId] || {}),
      [field]: String(value ?? '')
    }
  }
}

const handleModuleCreate = async () => {
  if (!selectedVersion.value?.id) {
    return
  }
  try {
    cancelSceneEditing()
    const created = await createWorkbenchFormulaModule(selectedVersion.value.id, { module_name: '新计算模块' })
    formulaModules.value = [
      ...formulaModules.value,
      {
        moduleCode: created.module_code,
        moduleName: created.module_name,
        scenes: []
      }
    ]
    activeModuleCode.value = created.module_code
    activeSceneCode.value = ''
    setSelectedFormula({})
    stopFormulaEditing()
    ElMessage.success('已新增计算模块')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '新增计算模块失败')
  }
}

const loadActiveMappings = async () => {
  if (selectedVersion.value?.id && activeModuleCode.value) {
    try {
      activeMappings.value = await fetchFormulaParamMappings(selectedVersion.value.id, activeModuleCode.value)
    } catch (e) {
      activeMappings.value = []
    }
  } else {
    activeMappings.value = []
  }
}

const handleMappingSaved = async () => {
  await loadActiveMappings()
  
  // also refresh modules to update the module card sync state
  if (selectedVersion.value?.id) {
    const data = await fetchWorkbenchFormulaModules(selectedVersion.value.id)
    replaceFormulaRows(data?.rows || [], data?.modules || [])
  }
  
  runDesign()
}

watch(activeModuleCode, () => {
  loadActiveMappings()
  if (selectedVersion.value?.id) {
    void syncWorkbenchRouteQuery({
      moduleCode: activeModuleCode.value
    })
  }
})

watch(
  () => workbenchViewMode.value,
  (value) => {
    if (value === 'flow') {
      syncFlowSelectionFromFormula()
      return
    }
    flowDisplayMode.value = 'default'
  }
)

const handleModuleSelect = (module) => {
  resetFormulaBatchDeleteState()
  cancelSceneEditing()
  activeModuleCode.value = module?.moduleCode || ''
  activeSceneCode.value = moduleLastSceneMap.value?.[module?.moduleCode] || ''
  syncWorkbenchFocus()
  scheduleParameterPanelPosition()
  loadActiveMappings()
}

const handleModuleSync = (module) => {
  syncModuleCode.value = module.moduleCode
  syncDialogVisible.value = true
}

const handleSyncSuccess = async () => {
  if (selectedVersion.value?.id) {
    const data = await fetchWorkbenchFormulaModules(selectedVersion.value.id)
    replaceFormulaRows(data?.rows || [], data?.modules || [])
    syncWorkbenchFocus()
    runDesign()
  }
}

const handleModuleRename = async (module, nextName) => {
  if (!selectedVersion.value?.id || !String(nextName || '').trim()) {
    return
  }
  try {
    const renamed = await renameWorkbenchFormulaModule(selectedVersion.value.id, module.moduleCode, {
      module_name: String(nextName).trim()
    })
    applyModuleNameLocally(module.moduleCode, renamed?.module_name || String(nextName).trim())
    ElMessage.success('模块名称已更新')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '模块改名失败')
  }
}

const handleSceneCreate = async (module) => {
  if (!selectedVersion.value?.id) {
    return
  }
  if (!module) {
    await handleModuleCreate()
    module = formulaModules.value[formulaModules.value.length - 1]
    if (!module) return
  }
  try {
    cancelSceneEditing()
    resetFormulaBatchDeleteState()
    const created = await createWorkbenchFormulaScene(selectedVersion.value.id, {
      module_code: module.moduleCode,
      scene_name: '未命名场景'
    })
    formulaModules.value = formulaModules.value.map((item) => {
      if (item.moduleCode !== module.moduleCode) {
        return item
      }
      return {
        ...item,
        scenes: [
          ...item.scenes,
          {
            moduleCode: created.module_code,
            moduleName: created.module_name,
            sceneCode: created.scene_code,
            sceneName: created.scene_name,
            rows: []
          }
        ]
      }
    })
    activeModuleCode.value = module.moduleCode
    activeSceneCode.value = created.scene_code
    moduleLastSceneMap.value = {
      ...moduleLastSceneMap.value,
      [module.moduleCode]: created.scene_code
    }
    setSelectedFormula({})
    stopFormulaEditing()
    editingSceneCode.value = created.scene_code
    scheduleParameterPanelPosition()
    ElMessage.success('计算块创建成功')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '创建计算块失败')
  }
}

const handleSceneSelect = (scene) => {
  resetFormulaBatchDeleteState()
  cancelSceneEditing()
  activeModuleCode.value = scene?.moduleCode || ''
  activeSceneCode.value = scene?.sceneCode || ''
  if (scene?.moduleCode && scene?.sceneCode) {
    moduleLastSceneMap.value = {
      ...moduleLastSceneMap.value,
      [scene.moduleCode]: scene.sceneCode
    }
  }
  syncWorkbenchFocus()
  scheduleParameterPanelPosition()
}

const beginSceneEditing = (scene = {}) => {
  if (!scene?.sceneCode) {
    return
  }
  resetFormulaBatchDeleteState()
  stopFormulaEditing()
  activeModuleCode.value = scene.moduleCode || activeModuleCode.value
  activeSceneCode.value = scene.sceneCode || activeSceneCode.value
  editingSceneCode.value = String(scene.sceneCode || '')
  scheduleParameterPanelPosition()
}

const handleSceneRenameConfirm = async (scene, nextName) => {
  if (!selectedVersion.value?.id || !scene?.sceneCode) {
    cancelSceneEditing()
    return
  }
  const resolvedSceneName = String(nextName || '').trim() || '未命名场景'
  sceneSaving.value = true
  try {
    const renamed = await renameWorkbenchFormulaScene(
      selectedVersion.value.id,
      scene.moduleCode,
      scene.sceneCode,
      { scene_name: resolvedSceneName }
    )
    const nextSceneName = renamed?.scene_name || resolvedSceneName
    applySceneNameLocally(scene.moduleCode, scene.sceneCode, nextSceneName)
    await loadModelFormulas({
      module_code: scene.moduleCode,
      scene_code: scene.sceneCode
    })
    cancelSceneEditing()
    ElMessage.success('场景名称已更新')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '场景改名失败')
  } finally {
    sceneSaving.value = false
  }
}

const handleModuleDelete = async (module) => {
  if (!selectedVersion.value?.id) {
    return
  }
  try {
    await ElMessageBox.confirm(
      '删除后将同时移除该模块下的全部场景和公式，且不可恢复。是否继续？',
      '删除计算模块',
      { type: 'warning' }
    )
  } catch {
    return
  }

  try {
    cancelSceneEditing()
    await deleteWorkbenchFormulaModule(selectedVersion.value.id, module.moduleCode)
    const nextModules = formulaModules.value.filter((item) => item.moduleCode !== module.moduleCode)
    formulaModules.value = nextModules
    const resolved = resolveNextFocusAfterModuleDelete({
      modules: groupWorkbenchFormulaModules(formulaRows.value, serializeModuleShells(nextModules)),
      deletedModuleCode: module.moduleCode,
      activeModuleCode: activeModuleCode.value
    })
    activeModuleCode.value = resolved.activeModuleCode
    activeSceneCode.value = resolved.activeSceneCode
    setSelectedFormula(resolved.activeFormula || {})
    stopFormulaEditing()
    ElMessage.success('模块已删除')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '删除模块失败')
  }
}

const handleSceneDelete = async (scene) => {
  if (!selectedVersion.value?.id) {
    return
  }
  try {
    await ElMessageBox.confirm(
      '删除后将同时移除该场景中的全部公式，且不可恢复。是否继续？',
      '删除计算场景',
      { type: 'warning' }
    )
  } catch {
    return
  }

  try {
    cancelSceneEditing()
    await deleteWorkbenchFormulaScene(selectedVersion.value.id, scene.moduleCode, scene.sceneCode)
    resetFormulaBatchDeleteState()
    const nextModules = formulaModules.value.map((module) => {
      if (module.moduleCode !== scene.moduleCode) {
        return module
      }
      return {
        ...module,
        scenes: (module.scenes || []).filter((item) => item.sceneCode !== scene.sceneCode)
      }
    })
    formulaModules.value = nextModules
    const resolved = resolveNextFocusAfterSceneDelete({
      modules: groupWorkbenchFormulaModules(formulaRows.value, serializeModuleShells(nextModules)),
      deletedModuleCode: scene.moduleCode,
      deletedSceneCode: scene.sceneCode,
      activeModuleCode: activeModuleCode.value,
      activeSceneCode: activeSceneCode.value,
      lastSceneMap: moduleLastSceneMap.value
    })
    activeModuleCode.value = resolved.activeModuleCode
    activeSceneCode.value = resolved.activeSceneCode
    setSelectedFormula(resolved.activeFormula || {})
    stopFormulaEditing()
    ElMessage.success('场景已删除')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '删除场景失败')
  }
}

const handleEnterFormulaBatchDelete = (scene) => {
  if (!scene?.sceneCode) {
    return
  }
  if (formulaReordering.value) {
    ElMessage.warning('正在调整公式顺序，请稍后再试')
    return
  }
  cancelSceneEditing()
  formulaBatchModeModuleCode.value = String(scene.moduleCode || '')
  formulaBatchModeSceneCode.value = String(scene.sceneCode || '')
  selectedFormulaBatchKeys.value = []
  stopFormulaEditing()
  setSelectedFormula({})
  scheduleParameterPanelPosition()
}

const handleCancelFormulaBatchDelete = () => {
  cancelSceneEditing()
  resetFormulaBatchDeleteState()
  scheduleParameterPanelPosition()
}

const handleFormulaBatchToggle = (row) => {
  selectedFormulaBatchKeys.value = toggleFormulaBatchSelection(
    selectedFormulaBatchKeys.value,
    row?._rowKey
  )
}

const handleFormulaBatchDelete = async (scene = {}) => {
  if (!selectedVersion.value?.id || !selectedFormulaBatchKeys.value.length) {
    return
  }

  try {
    await ElMessageBox.confirm(
      `将永久删除当前场景下已选的 ${selectedFormulaBatchKeys.value.length} 条公式，且不可恢复。是否继续？`,
      '批量删除公式',
      { type: 'warning' }
    )
  } catch {
    return
  }

  const targetRows = (scene?.rows || []).filter((row) => selectedFormulaBatchKeys.value.includes(row._rowKey))
  const formulaIds = targetRows.map((row) => Number(row?.id || 0)).filter((id) => id > 0)
  if (!formulaIds.length) {
    ElMessage.warning('请选择需要删除的公式')
    return
  }

  const deletedKeys = [...selectedFormulaBatchKeys.value]
  formulaBatchDeleting.value = true
  try {
    const result = await deleteWorkbenchFormulasBatch(selectedVersion.value.id, { formula_ids: formulaIds })
    await loadModelFormulas({
      module_code: scene.moduleCode,
      scene_code: scene.sceneCode
    })
    const resolved = resolveNextFocusAfterFormulaBatchDelete({
      modules: displayFormulaModules.value,
      activeModuleCode: activeModuleCode.value,
      activeSceneCode: activeSceneCode.value,
      deletedFormulaKeys: deletedKeys
    })
    activeModuleCode.value = resolved.activeModuleCode
    activeSceneCode.value = resolved.activeSceneCode
    setSelectedFormula(resolved.activeFormula || {})
    stopFormulaEditing()
    resetFormulaBatchDeleteState()
    scheduleParameterPanelPosition()
    ElMessage.success(`已删除 ${result.deleted_count} 条公式`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '批量删除公式失败')
  } finally {
    formulaBatchDeleting.value = false
  }
}

const handleFormulaCreate = (scene = {}) => {
  cancelSceneEditing()
  resetFormulaBatchDeleteState()
  activeModuleCode.value = scene.moduleCode || activeModuleCode.value
  activeSceneCode.value = scene.sceneCode || activeSceneCode.value
  if (scene.moduleCode && scene.sceneCode) {
    moduleLastSceneMap.value = {
      ...moduleLastSceneMap.value,
      [scene.moduleCode]: scene.sceneCode
    }
  }
  
  const targetScene = displayFormulaModules.value
    .find(m => m.moduleCode === activeModuleCode.value)?.scenes
    .find(s => s.sceneCode === activeSceneCode.value)
  const maxSortOrder = Math.max(0, ...(targetScene?.rows || []).map(r => Number(r.sort_order || 0)))
  
  beginFormulaEditing({
    id: 0,
    model_id: selectedVersion.value?.id || 0,
    module_code: scene.moduleCode || activeFormula.value?.module_code || 'power_calc',
    module_name: scene.moduleName || activeFormula.value?.module_name || '功率计算',
    scene_code: scene.sceneCode || activeFormula.value?.scene_code || 'power',
    scene_name: scene.sceneName || activeFormula.value?.scene_name || '转速与功率',
    name: '',
    expression: '',
    variables: {},
    source_type: 'manual',
    sort_order: maxSortOrder + 10,
    _isNewDraft: true
  })
  scheduleParameterPanelPosition()
  
  // scroll to the new formula row so user can see it
  void scrollToFormula({
    module_code: scene.moduleCode || activeFormula.value?.module_code || 'power_calc',
    scene_code: scene.sceneCode || activeFormula.value?.scene_code || 'power',
    _isNewDraft: true
  })
}

const handleFormulaDelete = async (row = {}) => {
  if (!selectedVersion.value?.id || !row?.id || row?._isNewDraft || formulaDeleting.value) {
    return
  }
  try {
    await ElMessageBox.confirm(
      `将永久删除公式“${row.displayName || row.name || '未命名公式'}”，且不可恢复。是否继续？`,
      '删除公式',
      { type: 'warning' }
    )
  } catch {
    return
  }

  cancelSceneEditing()
  const resolved = resolveNextFocusAfterFormulaDelete({
    modules: displayFormulaModules.value,
    activeModuleCode: activeModuleCode.value,
    activeSceneCode: activeSceneCode.value,
    activeFormulaKey: activeFormulaKey.value,
    deletedFormulaKey: row?._rowKey
  })

  formulaDeleting.value = true
  try {
    await deleteWorkbenchFormula(selectedVersion.value.id, row.id)
    await loadModelFormulas({
      module_code: row.module_code,
      scene_code: row.scene_code
    })
    activeModuleCode.value = resolved.activeModuleCode
    activeSceneCode.value = resolved.activeSceneCode
    if (resolved.activeModuleCode && resolved.activeSceneCode) {
      moduleLastSceneMap.value = {
        ...moduleLastSceneMap.value,
        [resolved.activeModuleCode]: resolved.activeSceneCode
      }
    }
    setSelectedFormula(resolved.activeFormula || {})
    stopFormulaEditing()
    scheduleParameterPanelPosition()
    ElMessage.success('公式已删除')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '删除公式失败')
  } finally {
    formulaDeleting.value = false
  }
}

const handleFormulaDraftChange = ({ field, value }) => {
  activeFormulaDraft.value = {
    ...activeFormulaDraft.value,
    [field]: value
  }
}

const openCurveFormulaDialog = () => {
  curveFormulaDialogVisible.value = true
}

const applyCurveFormulaExpression = (expression = '') => {
  activeFormulaDraft.value = {
    ...activeFormulaDraft.value,
    expression: String(expression || '').trim()
  }
}

const handleFormulaEditorSelectionChange = ({ start = 0, isComposing = false } = {}) => {
  formulaCursorStart.value = Number(start || 0)
  formulaCompositionActive.value = Boolean(isComposing)
}

const handleFormulaReorder = async ({ moduleCode, sceneCode, orderedIds } = {}) => {
  if (!selectedVersion.value?.id || formulaReordering.value) {
    return
  }
  const previousRows = formulaRows.value.map((item) => ({ ...item }))
  const previousShells = serializeModuleShells()
  const moved = reorderFormulaRowsWithinScene(previousRows, moduleCode, sceneCode, orderedIds)
  if (!moved.payload.length) {
    return
  }

  replaceFormulaRows(moved.rows, previousShells)
  formulaReordering.value = true
  try {
    const rows = await reorderWorkbenchFormulas(selectedVersion.value.id, { rows: moved.payload })
    const mergedRows = [
      ...previousRows.filter((row) =>
        !(
          String(row.module_code || '') === String(moduleCode || '') &&
          String(row.scene_code || '') === String(sceneCode || '')
        )
      ),
      ...(Array.isArray(rows) ? rows : moved.rows)
    ]
    replaceFormulaRows(mergedRows, previousShells)
    await nextTick()
    scheduleParameterPanelPosition()
  } catch (error) {
    replaceFormulaRows(previousRows, previousShells)
    ElMessage.error(error?.response?.data?.detail || '调整公式顺序失败')
  } finally {
    formulaReordering.value = false
  }
}

const applyExecutionResult = (result = {}) => {
  latestResults.value = Array.isArray(result.results) ? result.results : []
  latestScope.value = result.scope || {}
}

const executeDesignCalculation = async ({ silent = false, showSuccess = false } = {}) => {
  if (!selectedVersion.value?.id) {
    if (!silent) {
      ElMessage.warning('请先选择具体型号')
    }
    return
  }

  const requestId = ++designRequestSequence
  if (!silent) {
    executing.value = true
  }

  try {
    const result = await executeDrumDesign({
      model_id: selectedVersion.value.id,
      parameters: buildParameterPayload()
    })
    if (requestId !== designRequestSequence) {
      return
    }
    applyExecutionResult(result)
    if (showSuccess) {
      ElMessage.success('多场景计算完成')
    }
  } catch (error) {
    if (requestId !== designRequestSequence) {
      return
    }
    if (!silent) {
      ElMessage.error(error?.response?.data?.detail || '执行计算失败')
    }
  } finally {
    if (!silent && requestId === designRequestSequence) {
      executing.value = false
    }
  }
}

const scheduleAutoDesign = () => {
  if (autoRunTimer) {
    clearTimeout(autoRunTimer)
  }
  if (!selectedVersion.value?.id) {
    return
  }
  autoRunTimer = setTimeout(() => {
    autoRunTimer = null
    executeDesignCalculation({ silent: true, showSuccess: false })
  }, 400)
}

const handleFormulaCancel = () => {
  if (activeFormulaDraft.value?._isNewDraft) {
    setSelectedFormula({})
    stopFormulaEditing()
    scheduleParameterPanelPosition()
    return
  }
  stopFormulaEditing()
  scheduleParameterPanelPosition()
}

const handleFormulaSave = async () => {
  if (!selectedVersion.value?.id) {
    ElMessage.warning('请先选择具体型号')
    return
  }
  if (!String(activeFormulaDraft.value?.name || '').trim()) {
    ElMessage.warning('请填写公式名称')
    return
  }
  if (!String(activeFormulaDraft.value?.expression || '').trim()) {
    ElMessage.warning('请填写公式表达式')
    return
  }

  formulaSaving.value = true
  try {
    const payload = {
      id: activeFormulaDraft.value.id && activeFormulaDraft.value.id > 0 ? activeFormulaDraft.value.id : null,
      model_id: selectedVersion.value.id,
      module_code: String(activeFormulaDraft.value.module_code || activeFormula.value?.module_code || 'power_calc').trim(),
      module_name: String(activeFormulaDraft.value.module_name || activeFormula.value?.module_name || '功率计算').trim(),
      scene_code: String(activeFormulaDraft.value.scene_code || activeFormula.value?.scene_code || 'power').trim(),
      scene_name: String(activeFormulaDraft.value.scene_name || activeFormula.value?.scene_name || '转速与功率').trim(),
      name: String(activeFormulaDraft.value.name || '').trim(),
      expression: String(activeFormulaDraft.value.expression || '').trim(),
      canonical_expression: String(activeFormula.value?.canonical_expression || '').trim(),
      variables: activeFormulaContext.value.variables,
      source_type: 'manual'
    }
    const sampleScope = {}
    const localLookupResolver = (lookupName, _lookupKey, _colIndex, _exact) => {
      const matched = lookupItems.value.find((item) => String(item.lookup_name || '') === String(lookupName || ''))
      if (!matched) {
        throw new FormulaEngineError('LOOKUP_NOT_FOUND', `附录“${lookupName}”不存在`)
      }
      return 1
    }
    const localCurveResolver = (lookupName) => {
      const matched = lookupItems.value.find((item) => String(item.lookup_name || '') === String(lookupName || ''))
      if (!matched) {
        throw new FormulaEngineError('CURVE_PROFILE_MISSING', `曲线表“${lookupName}”不存在`)
      }
      return 1
    }
    evaluateFormulaExpression(payload.expression, sampleScope, {
      availableVariableNames: Object.keys(payload.variables || {}),
      lookupResolver: localLookupResolver,
      curveResolver: localCurveResolver,
      defaultMissingValue: 1
    })
    const saved = await saveWorkbenchFormula(selectedVersion.value.id, payload)
    await loadModelFormulas(saved || payload)
    
    stopFormulaEditing()
    
    try {
      await executeDesignCalculation({ silent: true, showSuccess: false })
      ElMessage.success('公式已保存')
    } catch (calcError) {
      ElMessage.warning(`公式已保存，但重算失败: ${calcError?.response?.data?.detail || calcError.message}`)
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存公式失败')
  } finally {
    formulaSaving.value = false
  }
}

const handleParameterChange = (row, nextValue) => {
  const exists = parameterRows.value.some((item) => {
    const itemId = Number(item?.parameterId || 0)
    const rowId = Number(row?.parameterId || 0)
    if (itemId > 0 && rowId > 0) {
      return itemId === rowId
    }
    return String(item?.paramName || '').trim() === String(row?.paramName || '').trim()
  })

  if (!exists) {
    parameterRows.value = [
      ...parameterRows.value,
      {
        parameterId: 0,
        paramCode: '',
        paramName: String(row?.paramName || '').trim(),
        unitCode: String(row?.unitCode || '').trim(),
        value: String(nextValue ?? ''),
        dirty: true,
        source: 'draft',
        pendingCreate: true
      }
    ]
    return
  }

  parameterRows.value = updateWorkbenchParameterDraft(parameterRows.value, row, nextValue)
}

const handleAddParameter = () => {
  parameterRows.value.unshift({
    parameterId: 0,
    paramCode: '',
    paramName: '',
    displayName: '',
    unitCode: '',
    valueType: 'basic',
    value: '',
    dirty: true,
    source: 'draft',
    pendingCreate: true,
    _nameConfirmed: false
  })
}

const handleDeleteParameter = async (row) => {
  const index = parameterRows.value.findIndex(r => r === row)
  if (index === -1) return

  if (row.pendingCreate || !row.parameterId) {
    parameterRows.value.splice(index, 1)
    return
  }
  
  try {
    await ElMessageBox.confirm(`确定要删除参数 "${row.paramName}" 吗？`, '提示', {
      type: 'warning'
    })
    await deleteModelParameterValue(selectedVersion.value.id, row.parameterId)
    parameterRows.value.splice(index, 1)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleParameterSync = async () => {
  if (!selectedFamily.value?.id || !selectedVersion.value?.id) {
    ElMessage.info('请先选择型号')
    return
  }

  const payload = buildWorkbenchParameterSavePayload({
    familyId: selectedFamily.value.id,
    versionId: selectedVersion.value.id,
    rows: parameterRows.value
  })

  if (!payload.rows.length) {
    ElMessage.info('当前没有可保存的型号参数')
    return
  }

  try {
    await ElMessageBox.confirm(
      '本次操作会把当前工作台里的基础参数写回为该型号的初始值，参数中心会同步看到更新。是否继续？',
      '保存为型号初始值',
      { type: 'warning' }
    )
  } catch {
    return
  }

  parameterSyncing.value = true
  try {
    const result = await saveWorkbenchParameters(payload)
    await loadParametersWithPriority()
    ElMessage.success(`已同步到参数中心，共保存 ${result.saved_count} 项，新增参数 ${result.created_parameter_count} 项`)
    allParametersDrawerVisible.value = false
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存型号初始值失败')
  } finally {
    parameterSyncing.value = false
  }
}

const scrollToFormula = async (row) => {
  await nextTick()
  mainTableRef.value?.scrollToRow(buildFormulaRowKey(row))
}

const scheduleParameterPanelPosition = () => {
  // 废弃：右侧参数面板不再随滚动移动
}

const handleIntermediateJump = async (row) => {
  const matched = formulaRows.value.find((item) => item.name === row.sourceFormula)
  if (!matched) return
  setSelectedFormula(matched)
  stopFormulaEditing()
  await scrollToFormula(matched)
  scheduleParameterPanelPosition()
}

const handleLookupJump = async (row) => {
  const query = buildLookupTargetQuery({
    lookupDetail: row?.lookupDetail,
    lookupItems: lookupItems.value,
    sourceFormulaName: activeFormulaContext.value?.name || ''
  })
  if (!query) {
    ElMessage.warning('当前附录来源暂时无法定位')
    return
  }
  await router.push({ name: 'ParameterCenter', query })
}

const runDesign = async () => {
  await executeDesignCalculation({ silent: false, showSuccess: true })
}

const openCompare = async () => {
  if (!activeFormula.value?.name) {
    ElMessage.warning('请先在公式列表中选择一个计算结果作为目标指标')
    return
  }
  
  impactTargetResultName.value = activeFormula.value.name
  compareDialogVisible.value = true
  impactAnalyzing.value = true
  impactResults.value = []
  
  try {
    const payload = {
      model_id: selectedVersion.value.id,
      target_result_name: impactTargetResultName.value,
      parameters: buildWorkbenchParameterSavePayload(parameterRows.value)
    }
    const res = await analyzeDrumDesignImpact(payload)
    impactResults.value = res.impacts || []
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '参数影响分析失败')
  } finally {
    impactAnalyzing.value = false
  }
}

const confirmOpenCompare = async () => {
  if (!compareTargetParam.value) {
    ElMessage.warning('请先选择一个基础参数')
    return
  }
  ElMessage.info('旧版趋势分析已移除，请在新设计工作台使用校核扫描分析。')
  compareDialogVisible.value = false
}

const openFormulaLibraryDialog = async () => {
  await router.push({ name: 'Formulas' })
}

onBeforeRouteLeave(async () => {
  if (!hasDirtyParameters.value) return true
  try {
    await ElMessageBox.confirm(
      '当前参数已修改，尚未保存到当前型号。是否继续离开？',
      '离开确认',
      {
        confirmButtonText: '继续离开',
        cancelButtonText: '留在当前页',
        type: 'warning'
      }
    )
    return true
  } catch {
    return false
  }
})

watch(
  () => parameterRows.value.map((row) => `${row.parameterId}:${row.paramName}:${row.value}`),
  () => {
    scheduleAutoDesign()
  }
)

watch(
  () => activeFormulaKey.value,
  (value) => {
    if (value && String(explanationTarget.value?.type || '') !== 'input') {
      explanationTarget.value = {
        type: 'formula',
        key: value
      }
    }
    syncFlowSelectionFromFormula()
    scheduleAutoDesign()
    scheduleParameterPanelPosition()
  }
)

watch(
  () => workbenchViewMode.value,
  async (value) => {
    if (value === 'flow') {
      flowDisplayMode.value = 'all'
      activeFlowNodeId.value = ''
      await nextTick()
      flowViewportResetToken.value += 1
      return
    }
    scheduleParameterPanelPosition()
  }
)

watch(
  () => activeCalculationFlow.value,
  (graph) => {
    const hasSelectedNode = (graph?.nodes || []).some((node) => String(node?.id || '') === String(activeFlowNodeId.value || ''))
    if (!hasSelectedNode) {
      activeFlowNodeId.value = resolveDefaultFlowNodeId(graph)
    }
  },
  { deep: true }
)

watch(
  () => formulaModules.value,
  () => {
    syncWorkbenchFocus()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (autoRunTimer) {
    clearTimeout(autoRunTimer)
  }
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', scheduleParameterPanelPosition)
  }
})

onMounted(async () => {
  await loadTree()
  await loadLookupItems()
  scheduleParameterPanelPosition()
  window.addEventListener('resize', scheduleParameterPanelPosition)
  
  // 从 localStorage 恢复智能选型的持久化数据
  const savedEquipment = localStorage.getItem('workbench_current_equipment')
  if (savedEquipment) {
    try {
      currentEquipment.value = JSON.parse(savedEquipment)
    } catch (e) {
      console.error('Failed to parse saved equipment:', e)
    }
  }
  
  // Check if there are injected motor parameters from CatalogExplorer
  const injectedMotorData = localStorage.getItem('selected_motor_for_workbench')
  if (injectedMotorData) {
    try {
      const motor = JSON.parse(injectedMotorData)
      // Map motor specs to workbench parameters
      if (motor.specs) {
        // Schedule update after the initial components load
        setTimeout(() => {
          const paramMap = {
            'motor_power': motor.specs.power_kw,
            'motor_speed': motor.specs.speed_rpm,
            'motor_torque': motor.specs.torque_nm,
            'motor_inertia': motor.specs.inertia_10_4_kgm2 ? motor.specs.inertia_10_4_kgm2 / 10000 : undefined
          }
          
          Object.entries(paramMap).forEach(([key, value]) => {
            if (value !== undefined) {
              handleParameterChange({ paramName: key }, value)
            }
          })
          
          ElMessage.success(`已成功加载电机 ${motor.model_name} 的技术参数以进行校核计算`)
          localStorage.removeItem('selected_motor_for_workbench')
        }, 1000)
      }
    } catch (e) {
      console.error('Failed to parse injected motor data:', e)
    }
  }
})

watch(
  () => [visibleBaseRows.value.length, visibleIntermediateRows.value.length],
  () => {
    scheduleParameterPanelPosition()
  }
)
</script>

<style scoped>
.design-workbench-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 60px);
  margin: -20px;
  padding: 20px 20px 0 20px;
}

.workbench-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 340px;
  gap: 12px;
  min-height: 0;
  align-items: start;
  height: 100%;
}

.workbench-pane--tree {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.workbench-pane--tree :deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 20px;
}

.workbench-center {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  height: 100%;
}

.module-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 20px;
}

.smart-select-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.workbench-right {
  min-width: 0;
  height: 100%;
  overflow-y: auto;
  padding-bottom: 20px;
}

.workbench-right__panel {
}

.summary-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.summary-path {
  margin-top: 12px;
  display: flex;
  gap: 6px;
  align-items: center;
}

.workbench-view-switch {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
}

.summary-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.summary-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  min-width: 0;
  align-items: center;
}

.summary-alert {
  margin-top: 10px;
}

.formula-workbench {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 12px;
  min-height: 0;
  flex: 1;
}

.formula-workbench__input,
.formula-workbench__main {
  min-height: 0;
}

.formula-workbench__input :deep(.el-card__body) {
  height: 100%;
  padding: 8px 12px;
}

.formula-workbench__main {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.formula-module-strip {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.formula-module-strip__item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  min-width: 120px;
  padding: 10px 12px;
  border: 1px solid #dbe3ef;
  border-radius: 12px;
  background: #fff;
  color: #334155;
  cursor: pointer;
}

.formula-module-strip__item.is-active {
  border-color: #2563eb;
  background: rgba(37, 99, 235, 0.06);
}

.formula-module-strip__name {
  font-size: 13px;
  font-weight: 600;
}

.formula-module-strip__meta {
  font-size: 11px;
  color: #64748b;
}

.workbench-range-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  padding: 8px 0 12px;
  border-top: 1px solid #e2e8f0;
}

.workbench-range-tabs__section {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.workbench-range-tabs__label {
  flex: none;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.workbench-flow-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.compare-dialog-copy {
  margin-bottom: 12px;
  color: #475569;
  line-height: 1.6;
}

@media (max-width: 1440px) {
  .workbench-layout {
    grid-template-columns: 260px minmax(0, 1fr) 320px;
    gap: 10px;
  }
}

@media (max-width: 1200px) {
  .formula-workbench {
    grid-template-columns: 240px minmax(0, 1fr);
  }
}

@media (max-width: 1024px) {
  .formula-workbench {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .summary-header {
    flex-direction: column;
    align-items: stretch;
  }

  .summary-actions {
    justify-content: flex-start;
  }

  .workbench-right__panel {
    margin-top: 0;
  }
}
</style>
