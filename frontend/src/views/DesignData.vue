<template>
  <div class="design-platform">
    <!-- 顶部统一标题与全局动作 -->
    <div class="platform-header-v2">
      <div class="header-left">
        <el-button link @click="$router.push('/dashboard')" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <div class="breadcrumb">
          <span class="root">设计协同中心</span>
          <el-icon class="sep"><ArrowRight /></el-icon>
          <span v-if="selectedItem" class="current">
            {{ selectedItem.model_code || selectedItem.code }} - {{ selectedItem.name || selectedItem.type_name }}
          </span>
        </div>
        <el-tag v-if="selectedItem?.type === 'product'" size="small" effect="plain" class="type-tag">产品</el-tag>
        <el-tag v-if="selectedItem?.type === 'component'" size="small" type="success" effect="plain" class="type-tag">部件</el-tag>
      </div>

      <div class="header-right">
        <div class="shortcut-hints">
          <span class="hint-item"><kbd>Ctrl+S</kbd> 保存</span>
          <span class="hint-item"><kbd>Ctrl+Enter</kbd> 计算</span>
        </div>
        <el-divider direction="vertical" />
        <div class="header-actions-v3">
          <el-tooltip content="撤销上一步 (Ctrl+Z)" placement="bottom">
            <el-button link @click="handleUndo" :disabled="!canUndo" class="action-icon-btn">
              <el-icon><RefreshLeft /></el-icon>
            </el-button>
          </el-tooltip>
          
          <el-tooltip content="Excel 智能导入" placement="bottom">
            <el-upload action="" :auto-upload="false" :show-file-list="false" @change="handleExcelImport" accept=".xlsx, .xls">
              <el-button link class="action-icon-btn">
                <el-icon><Upload /></el-icon>
              </el-button>
            </el-upload>
          </el-tooltip>

          <el-tooltip content="执行推演 (Ctrl+Enter)" placement="bottom">
            <el-button type="primary" link @click="manualCalculate" class="action-icon-btn calc-symbol">
              <el-icon><Cpu /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>
    </div>

    <div class="platform-body-v2" v-if="selectedItem">
      <!-- 流程导航区 (极简 Tab 风格) -->
      <div class="flow-nav-v2">
        <div class="flow-tabs">
          <div 
            v-for="flow in flows" 
            :key="flow.id" 
            class="flow-tab-v2" 
            :class="{ active: activeFlowId === String(flow.id) }"
            @click="handleFlowSelect(String(flow.id))"
          >
            <span class="tab-text">{{ flow.flow_name }}</span>
            <el-dropdown trigger="click" @command="(cmd) => handleFlowCommand(cmd, flow)">
              <el-icon class="tab-more"><ArrowDown /></el-icon>
              <template #dropdown>
                <el-dropdown-menu class="compact-dropdown">
                  <el-dropdown-item command="edit" icon="Edit">重命名</el-dropdown-item>
                  <el-dropdown-item command="delete" icon="Delete" style="color: #f56c6c">移除流程</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <el-button class="add-flow-btn-v2" link @click="handleAddFlow">
            <el-icon><Plus /></el-icon>
            <span>新增流程</span>
          </el-button>
        </div>
      </div>

      <div class="design-scroll-area" v-loading="loading">
        <!-- 核心设计区 -->
        <div class="design-workspace-v2" v-if="activeFlow">
          <el-collapse v-model="activeStepIds" @change="handleStepCollapseChange" class="step-collapse-v2">
            <el-collapse-item v-for="(step, sIdx) in activeFlow.steps" :key="step.id" :name="step.id">
              <template #title>
                <div class="step-title">
                  <span class="step-order">{{ sIdx + 1 }}</span>
                  <span class="step-name">{{ step.step_name }}</span>
                  <div class="step-ops">
                    <el-button type="primary" link @click.stop="handleEditStep(step)">编辑名称</el-button>
                    <el-button type="danger" link @click.stop="handleDeleteStep(step.id)">删除</el-button>
                  </div>
                </div>
              </template>

              <!-- Excel 风格表格 -->
              <div class="calculation-table">
                <el-table :data="step.calculation_content?.rows || []" border stripe size="small" class="design-table">
                  <el-table-column label="参数名称" width="200">
                    <template #default="{ row }">
                      <div class="param-name-cell">
                        <el-input v-model="row.name" size="small" placeholder="参数名" @change="onRowChange" />
                        <el-tooltip content="关联其他参数" placement="top">
                          <el-button type="primary" link size="small" @click="openLinkDialog(row)">
                            <el-icon><Link /></el-icon>
                          </el-button>
                        </el-tooltip>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column label="计算式 / 输入值" width="350">
                    <template #default="{ row, $index }">
                      <div class="expression-cell">
                        <el-autocomplete
                          v-model="row.expression"
                          :fetch-suggestions="querySearch"
                          size="small"
                          placeholder="100 或 =A1*2"
                          @select="(item) => handleSelectParam(row, item)"
                          @input="onRowChange"
                          :trigger-on-focus="false"
                          class="expr-input"
                        >
                          <template #default="{ item }">
                            <div class="suggestion-item">
                              <span class="s-val">{{ item.display || item.value }}</span>
                              <span class="s-desc">{{ item.desc }}</span>
                            </div>
                          </template>
                        </el-autocomplete>
                        <el-tooltip content="从公式库引入" placement="top">
                          <el-button type="primary" link size="small" @click="openFormulaDialog(row)">
                            <el-icon><Connection /></el-icon>
                          </el-button>
                        </el-tooltip>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column label="当前值" width="160">
                    <template #default="{ row }">
                      <div class="value-cell" :class="{ 'has-error': row.error }">
                        <span class="val-text">{{ row.value }}</span>
                        <div class="val-actions">
                          <el-icon v-if="row.error" class="error-icon"><Warning /></el-icon>
                          <el-tooltip content="参数对比" placement="top">
                            <el-button type="primary" link size="small" @click="$router.push({ name: 'Compare', query: { designPoint: row.name } })">
                              <el-icon><DataAnalysis /></el-icon>
                            </el-button>
                          </el-tooltip>
                        </div>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column label="单位" width="90">
                    <template #default="{ row }">
                      <el-input v-model="row.unit" size="small" placeholder="单位" />
                    </template>
                  </el-table-column>
                  <el-table-column label="备注信息">
                    <template #default="{ row }">
                      <div class="note-cell">
                        <el-input v-model="row.note" size="small" placeholder="备注信息" />
                        <el-upload
                          action=""
                          :auto-upload="false"
                          :show-file-list="false"
                          class="note-upload"
                        >
                          <el-button type="primary" link size="small">
                            <el-icon><Upload /></el-icon>
                          </el-button>
                        </el-upload>
                        <el-tag v-if="row.formula_name" size="small" type="info" closable @close="removeLinkedFormula(row)">
                          {{ row.formula_name }}
                        </el-tag>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="60" align="center">
                    <template #default="{ $index }">
                      <el-button type="danger" link @click="removeRow(step, $index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <div class="table-footer">
                  <el-button type="primary" link @click="addRow(step)">
                    <el-icon><Plus /></el-icon>添加参数行
                  </el-button>
                  <el-button type="success" size="small" @click="saveStep(step)">保存步骤数据</el-button>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
          
          <div v-if="activeFlow.steps.length === 0" class="empty-steps">
             <el-empty description="该流程暂无设计步骤">
               <div class="empty-actions">
                 <el-button type="primary" @click="handleAddStep">立即添加步骤</el-button>
                 <el-button type="danger" plain @click="handleDeleteFlow(activeFlow)">删除此流程</el-button>
               </div>
             </el-empty>
           </div>
           <div v-else class="workspace-footer">
             <el-button type="primary" plain @click="handleAddStep">
               <el-icon><Plus /></el-icon>新增设计步骤
             </el-button>
           </div>
        </div>
        <el-empty v-else-if="!loading" description="请选择或创建一个设计流程" />
      </div>
    </div>
    <el-empty v-else description="请从左侧产品树选择一个产品或部件开始设计" />

    <!-- 流程对话框 -->
    <el-dialog v-model="showFlowDialog" :title="editingFlowId ? '编辑设计流程' : '新增设计流程'" width="400px">
      <el-form :model="flowForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="flowForm.flow_name" placeholder="例如: 电机功率计算" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFlowDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFlow">确定</el-button>
      </template>
    </el-dialog>

    <!-- 步骤对话框 -->
    <el-dialog v-model="showStepDialog" :title="editingStepId ? '编辑设计步骤' : '新增设计步骤'" width="400px">
      <el-form :model="stepForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="stepForm.step_name" placeholder="例如: 基础参数输入" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showStepDialog = false">取消</el-button>
        <el-button type="primary" @click="saveNewStep">确定</el-button>
      </template>
    </el-dialog>

    <!-- 公式库关联对话框 -->
    <el-dialog v-model="showFormulaDialog" title="从公式库引入计算标准" width="650px" custom-class="formula-dialog">
      <div class="formula-dialog-body">
        <div class="dialog-section">
          <label class="section-label">选择标准公式</label>
          <el-select v-model="selectedFormulaId" placeholder="搜索公式..." filterable @change="onFormulaChange" style="width: 100%">
            <el-option v-for="f in formulaLibrary" :key="f.id" :label="f.name" :value="f.id">
              <span style="float: left">{{ f.name }}</span>
              <span style="float: right; color: #94a3b8; font-size: 12px">{{ f.category }}</span>
            </el-option>
          </el-select>
        </div>
        
        <div v-if="selectedFormula" class="variable-mapping-card">
          <div class="formula-preview">
            <span class="expr-label">公式预览:</span>
            <code class="expr-code">{{ selectedFormula.canonical_expression || selectedFormula.expression }}</code>
          </div>
          <el-divider />
          <div v-if="formulaTargetOptions.length > 1" class="dialog-section">
            <label class="section-label">选择目标参数</label>
            <el-select
              v-model="selectedFormulaTargetKey"
              placeholder="请选择目标参数"
              style="width: 100%"
              @change="resetMappingsForSelectedTarget"
            >
              <el-option
                v-for="target in formulaTargetOptions"
                :key="target.key"
                :label="target.description ? `${target.key} - ${target.description}` : target.key"
                :value="target.key"
              />
            </el-select>
          </div>
          <div class="mapping-title">参数映射 (绑定现有参数)</div>
          <div class="mapping-grid">
            <div v-for="varName in selectedFormulaRequiredMappings" :key="varName" class="mapping-row">
              <div class="var-info">
                <span class="var-name">{{ varName }}</span>
                <span class="var-desc">{{ selectedFormula.variables?.[varName] || '必填变量' }}</span>
              </div>
              <el-autocomplete
                v-model="varMappings[varName]"
                :fetch-suggestions="queryParamSuggestions"
                placeholder="搜索参数..."
                size="small"
                class="mapping-input"
              />
            </div>
          </div>
          <el-empty
            v-if="selectedFormulaRequiredMappings.length === 0"
            description="当前目标参数不需要额外映射"
          />
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showFormulaDialog = false" plain>取消</el-button>
          <el-button type="primary" @click="applyFormulaLink" :disabled="!selectedFormula">引入计算</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 关联其他参数对话框 (复用原有逻辑) -->
    <el-dialog v-model="showLinkDialog" title="关联其他流程参数" width="900px">
       <div class="link-dialog-body">
         <el-row :gutter="20">
           <el-col :span="8">
             <el-input v-model="ptSearch" placeholder="搜索产品..." size="small" prefix-icon="Search" />
             <el-table :data="filteredPTs" height="400px" @current-change="onPTChange" highlight-current-row>
               <el-table-column prop="model_code" label="产品代号" />
             </el-table>
           </el-col>
           <el-col :span="16">
             <el-input v-model="paramSearch" placeholder="搜索参数..." size="small" prefix-icon="Search" />
             <el-table :data="filteredRemoteParams" height="400px">
               <el-table-column prop="name" label="参数名" />
               <el-table-column prop="value" label="当前值" width="80" />
               <el-table-column prop="component_name" label="所属部件" />
               <el-table-column label="操作" width="60">
                 <template #default="{ row }">
                   <el-button type="primary" link @click="applyParamLink(row)">选择</el-button>
                 </template>
               </el-table-column>
             </el-table>
           </el-col>
         </el-row>
       </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick, inject, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, ArrowDown, Plus, MoreFilled, RefreshLeft, Refresh, Link, Connection, Delete, DocumentAdd, Upload, Memo, More, Cpu, Setting, ChatLineRound, InfoFilled, DataAnalysis, Warning, Edit } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { evaluateFormulaRows } from '../utils/formulaEngine.mjs'
import { createWorkbenchSnapshots, fetchFamilyMatrix } from '../api/designPlatform'
import {
  buildFormulaLinkPayload,
  getFormulaTargetOptions,
  getRequiredMappings
} from '../utils/formulaTemplateMapping.mjs'

const props = defineProps({
  selectedTypeId: {
    type: [String, Number],
    default: null
  },
  selectedFamilyId: {
    type: [String, Number],
    default: null
  },
  selectedVersionId: {
    type: [String, Number],
    default: null
  },
  autoLoadSignal: {
    type: Number,
    default: 0
  }
})

const route = useRoute()
const router = useRouter()

// 基础状态
const activeMainTab = ref('design_flow')
const selectedItem = ref(null)
const loading = ref(false)
const flows = ref([])
const activeFlowId = ref('')
const activeStepIds = ref([])
const allProductParams = ref([])
const baseProductParams = ref([])
const externalMatrixParams = ref([])
const currentWorkbenchRunKey = ref('')
const historyStack = ref([])

// 公式库关联
const showFormulaDialog = ref(false)
const formulaLibrary = ref([])
const selectedFormulaId = ref(null)
const selectedFormula = computed(() => formulaLibrary.value.find(f => f.id === selectedFormulaId.value))
const selectedFormulaTargetKey = ref(null)
const varMappings = ref({})
const activeFormulaRow = ref(null)
const formulaTargetOptions = computed(() => getFormulaTargetOptions(selectedFormula.value))
const selectedFormulaRequiredMappings = computed(() => (
  selectedFormula.value
    ? getRequiredMappings(selectedFormula.value, selectedFormulaTargetKey.value)
    : []
))

// 关联参数
const showLinkDialog = ref(false)
const activeLinkRow = ref(null)
const allProductTypes = ref([])
const ptSearch = ref('')
const paramSearch = ref('')
const selectedPTId = ref(null)
const remoteParams = ref([])

// Mock 数据
const mockDrawings = ref([
  { name: '总装结构图', code: 'NFLG-DR-001', version: 'V1.0', date: '2026-05-10 14:30' },
  { name: '核心部件加工图', code: 'NFLG-DR-002', version: 'V1.2', date: '2026-05-12 09:15' }
])
const mockReports = ref([
  { name: '结构强度计算分析报告', status: '已批准', date: '2026-05-11 16:20' },
  { name: '滚筒热平衡计算书', status: '审核中', date: '2026-05-13 10:05' }
])

// 计算属性
const activeFlow = computed(() => flows.value.find(f => String(f.id) === activeFlowId.value))
const canUndo = computed(() => historyStack.value.length > 0)
const filteredPTs = computed(() => allProductTypes.value.filter(pt => pt.model_code?.includes(ptSearch.value)))
const filteredRemoteParams = computed(() => remoteParams.value.filter(p => p.name?.includes(paramSearch.value)))

// 核心逻辑：获取数据
const updateSelection = async () => {
  const { typeId, componentId } = route.query
  if (componentId) {
    loading.value = true
    try {
      const [resComp, resFlows] = await Promise.all([
        axios.get(`/product-components/${componentId}`),
        axios.get(`/product-components/${componentId}/flows`)
      ])
      selectedItem.value = { ...resComp.data, type: 'component' }
      flows.value = resFlows.data
      if (flows.value.length > 0 && !activeFlowId.value) {
        activeFlowId.value = String(flows.value[0].id)
      }
      await fetchProductParams(resComp.data.product_type_id)
      manualCalculate()
    } catch (err) {
      console.error(err)
    } finally {
      loading.value = false
    }
  } else if (typeId) {
    loading.value = true
    try {
      const res = await axios.get(`/product-types/${typeId}`)
      selectedItem.value = { ...res.data, type: 'product' }
      flows.value = []
    } catch (err) {
      console.error(err)
    } finally {
      loading.value = false
    }
  } else {
    selectedItem.value = null
  }
}

const syncAllProductParams = () => {
  const merged = new Map()
  ;[...(baseProductParams.value || []), ...(externalMatrixParams.value || [])].forEach((item) => {
    if (!item?.name) return
    merged.set(item.name, item)
  })
  allProductParams.value = Array.from(merged.values())
}

const fetchProductParams = async (typeId) => {
  if (!typeId) return
  try {
    const res = await axios.get(`/product-components/all-params-by-type/${typeId}`)
    baseProductParams.value = Array.isArray(res.data) ? res.data : []
    syncAllProductParams()
  } catch (err) {
    console.error(err)
  }
}

const persistWorkbenchSnapshot = async () => {
  if (!externalMatrixParams.value.length) return
  if (!currentWorkbenchRunKey.value) {
    currentWorkbenchRunKey.value = `wb-${Date.now()}`
  }
  await createWorkbenchSnapshots(
    currentWorkbenchRunKey.value,
    externalMatrixParams.value.map((row) => ({
      version_id: row.version_id,
      parameter_id: row.parameter_id,
      snapshot_value: row.value
    }))
  )
}

const applyModelParameters = async () => {
  if (!props.selectedFamilyId || !props.selectedVersionId) return
  try {
    const matrix = await fetchFamilyMatrix(props.selectedFamilyId)
    externalMatrixParams.value = (Array.isArray(matrix.rows) ? matrix.rows : []).map((row) => ({
      name: row.param_name,
      value: row.values?.[props.selectedVersionId] ?? row.values?.[String(props.selectedVersionId)] ?? '',
      parameter_id: row.parameter_id,
      version_id: Number(props.selectedVersionId),
      unit: row.unit_code || ''
    }))
    currentWorkbenchRunKey.value = `wb-${Date.now()}`
    syncAllProductParams()
    await persistWorkbenchSnapshot()
    manualCalculate()
    ElMessage.success(`已自动带入 ${externalMatrixParams.value.length} 条型号参数`)
  } catch (error) {
    ElMessage.error('自动带参失败')
  }
}

const fetchFormulaLibrary = async () => {
  try {
    const res = await axios.get('/formulas/')
    formulaLibrary.value = res.data
  } catch (err) {
    console.error(err)
  }
}

// 流程与步骤操作
const handleFlowSelect = (id) => {
  activeFlowId.value = id
  if (activeFlow.value && activeFlow.value.steps) {
    activeStepIds.value = activeFlow.value.steps.map(s => s.id)
  }
}

const handleAddFlow = () => {
  editingFlowId.value = null
  flowForm.value = { flow_name: '', component_id: route.query.componentId }
  showFlowDialog.value = true
}

const editingFlowId = ref(null)
const flowForm = ref({ flow_name: '', component_id: null })
const showFlowDialog = ref(false)

const saveFlow = async () => {
  if (!flowForm.value.flow_name) return
  try {
    if (editingFlowId.value) {
      await axios.put(`/product-components/flows/${editingFlowId.value}`, flowForm.value)
    } else {
      await axios.post('/product-components/flows', flowForm.value)
    }
    showFlowDialog.value = false
    updateSelection()
  } catch (err) {
    ElMessage.error('保存失败')
  }
}

const handleFlowCommand = (cmd, flow) => {
  if (cmd === 'edit') {
    editingFlowId.value = flow.id
    flowForm.value = { flow_name: flow.flow_name, component_id: flow.component_id }
    showFlowDialog.value = true
  } else if (cmd === 'delete') {
    handleDeleteFlow(flow)
  }
}

const handleDeleteFlow = (flow) => {
  ElMessageBox.confirm(`确认删除流程 "${flow.flow_name}" 吗？`, '警告', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await axios.delete(`/product-components/flows/${flow.id}`)
      ElMessage.success('流程已移除')
      activeFlowId.value = ''
      updateSelection()
    } catch (err) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const showStepDialog = ref(false)
const editingStepId = ref(null)
const stepForm = ref({ step_name: '', flow_id: null })

const handleAddStep = () => {
  editingStepId.value = null
  stepForm.value = { step_name: '', flow_id: activeFlowId.value }
  showStepDialog.value = true
}

const handleEditStep = (step) => {
  editingStepId.value = step.id
  stepForm.value = { step_name: step.step_name, flow_id: activeFlowId.value }
  showStepDialog.value = true
}

const saveNewStep = async () => {
  try {
    if (editingStepId.value) {
      await axios.put(`/product-components/steps/${editingStepId.value}`, stepForm.value)
    } else {
      await axios.post('/product-components/steps', { ...stepForm.value, calculation_content: { rows: [] } })
    }
    showStepDialog.value = false
    updateSelection()
  } catch (err) {
    ElMessage.error('保存失败')
  }
}

const handleDeleteStep = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该设计步骤吗？此操作不可恢复。', '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      confirmButtonClass: 'el-button--danger'
    })
    await axios.delete(`/product-components/steps/${id}`)
    updateSelection()
    ElMessage.success('步骤已删除')
  } catch (err) {
    if (err !== 'cancel') console.error(err)
  }
}

const saveStep = async (step) => {
  await axios.put(`/product-components/steps/${step.id}`, step)
  ElMessage.success('保存成功')
}

// 计算逻辑
const calculateAll = () => {
  const baseScope = {}
  
  // 1. 放入外部产品基础参数
  allProductParams.value.forEach(p => {
    if (p.name) {
      const val = Number(p.value)
      if (Number.isFinite(val)) baseScope[p.name] = val
    }
  })

  // 2. 逐步骤多轮求值，允许后续行产出的参数回填前置行公式
  flows.value.forEach(flow => {
    flow.steps?.forEach(step => {
      if (!step.calculation_content?.rows) return

      const result = evaluateFormulaRows(step.calculation_content.rows, {
        baseScope,
        precision: 4
      })

      Object.assign(baseScope, result.resolvedValues)
    })
  })
}

const manualCalculate = () => {
  calculateAll()
}

const onRowChange = () => {
  saveToHistory()
  // 移除自动触发计算，仅在点击按钮或快捷键时执行
}

const addRow = (step) => {
  if (!step.calculation_content) step.calculation_content = { rows: [] }
  step.calculation_content.rows.push({ name: '', expression: '', value: '', unit: '', note: '' })
  onRowChange()
}

const removeRow = async (step, idx) => {
  try {
    await ElMessageBox.confirm('确定要删除该参数行吗？', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    saveToHistory()
    step.calculation_content.rows.splice(idx, 1)
    onRowChange()
  } catch (err) {
    // 用户取消删除
  }
}

// 自动补全
const allAvailableParamNames = computed(() => {
  const names = new Set()
  allProductParams.value.forEach(p => names.add(p.name))
  flows.value.forEach(f => f.steps?.forEach(s => s.calculation_content?.rows?.forEach(r => r.name && names.add(r.name))))
  return Array.from(names).map(n => ({ value: n, desc: '参数' }))
})

const querySearch = (queryString, cb) => {
  if (!queryString) {
    cb([])
    return
  }

  const operatorPattern = /^(.*[+\-*/^%(),=（），【】×÷])/
  // 如果包含数学运算符，提取最后一个变量名部分进行匹配
  const lastOpMatch = queryString.match(operatorPattern)
  const prefix = lastOpMatch ? lastOpMatch[1] : (queryString.startsWith('=') ? '=' : '')
  
  const match = queryString.match(/[^+\-*/^%(),=（），【】×÷]*$/)
  const term = match ? match[0].trim().toLowerCase() : ''
  
  const results = allAvailableParamNames.value
    .filter(p => p.value.toLowerCase().includes(term))
    .map(p => ({
      value: prefix + p.value,
      display: p.value,
      desc: p.desc
    }))
  
  cb(results)
}

const handleSelectParam = (row, item) => {
  onRowChange()
}

// 公式库引入逻辑
const openFormulaDialog = (row) => {
  activeFormulaRow.value = row
  selectedFormulaId.value = null
  selectedFormulaTargetKey.value = null
  varMappings.value = {}
  showFormulaDialog.value = true
  fetchFormulaLibrary()
}

const onFormulaChange = (id) => {
  const f = formulaLibrary.value.find(formula => formula.id === id)
  const [firstTarget] = getFormulaTargetOptions(f)
  selectedFormulaTargetKey.value = firstTarget?.key || null
  resetMappingsForSelectedTarget()
}

const resetMappingsForSelectedTarget = () => {
  const nextMappings = {}
  selectedFormulaRequiredMappings.value.forEach((variableName) => {
    nextMappings[variableName] = varMappings.value[variableName] || ''
  })
  varMappings.value = nextMappings
}

const queryParamSuggestions = (qs, cb) => {
  cb(allAvailableParamNames.value)
}

const applyFormulaLink = () => {
  if (!selectedFormula.value) return

  try {
    const payload = buildFormulaLinkPayload({
      formula: selectedFormula.value,
      targetKey: selectedFormulaTargetKey.value,
      mappings: varMappings.value,
      rowName: activeFormulaRow.value.name
    })

    Object.assign(activeFormulaRow.value, payload)
    showFormulaDialog.value = false
    onRowChange()
  } catch (error) {
    ElMessage.error(error.message || '引入公式失败')
  }
}

const removeLinkedFormula = (row) => {
  row.formula_name = null
  row.formula_id = null
  row.formula_target = null
  row.formula_source_expression = null
  row.formula_mappings = null
}

// 关联参数逻辑
const openLinkDialog = (row) => {
  activeLinkRow.value = row
  showLinkDialog.value = true
  fetchPTs()
}

const fetchPTs = async () => {
  const res = await axios.get('/product-types/')
  allProductTypes.value = res.data
}

const onPTChange = async (pt) => {
  if (!pt) return
  selectedPTId.value = pt.id
  const res = await axios.get(`/product-components/all-params-by-type/${pt.id}`)
  remoteParams.value = res.data
}

const applyParamLink = (p) => {
  activeLinkRow.value.expression = '=' + p.name
  activeLinkRow.value.note = `关联自: ${p.product_model}`
  showLinkDialog.value = false
  onRowChange()
}

// 撤回逻辑
const saveToHistory = () => {
  historyStack.value.push(JSON.parse(JSON.stringify(flows.value)))
  if (historyStack.value.length > 20) historyStack.value.shift()
}

const handleUndo = () => {
  if (historyStack.value.length > 0) {
    flows.value = historyStack.value.pop()
    manualCalculate()
  }
}

// Excel 导入
const handleExcelImport = (file) => {
  const reader = new FileReader()
  reader.onload = async (e) => {
    const data = new Uint8Array(e.target.result)
    const workbook = XLSX.read(data, { type: 'array' })
    const sheet = workbook.Sheets[workbook.SheetNames[0]]
    const jsonData = XLSX.utils.sheet_to_json(sheet)
    
    // 简单演示：只导入第一页
    const flowRes = await axios.post('/product-components/flows', {
      flow_name: workbook.SheetNames[0],
      component_id: route.query.componentId
    })
    
    const rows = jsonData.map(item => ({
      name: item['参数名称'] || item['名称'] || '',
      expression: String(item['计算式'] || item['值'] || ''),
      unit: item['单位'] || '',
      note: item['备注'] || ''
    }))
    
    await axios.post('/product-components/steps', {
      step_name: 'Excel 导入',
      flow_id: flowRes.data.id,
      calculation_content: { rows }
    })
    
    updateSelection()
  }
  reader.readAsArrayBuffer(file.raw)
}

const handleStepCollapseChange = (val) => {
  // 可以在这里持久化展开状态
}

// 上下文注入 (保持兼容)
const setContextData = inject('setContextData', () => {})
onMounted(() => {
  updateSelection()
  window.addEventListener('keydown', (e) => {
    // Ctrl + Z: 撤销
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
      e.preventDefault()
      handleUndo()
    }
    // Ctrl + Enter: 执行计算
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      manualCalculate()
    }
    // Ctrl + S: 保存
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      e.preventDefault()
      if (activeFlow.value?.steps?.[0]) {
        saveStep(activeFlow.value.steps[0])
      }
    }
  })
})

watch(() => route.query, updateSelection)
watch(
  () => props.autoLoadSignal,
  (value, oldValue) => {
    if (value && value !== oldValue) {
      applyModelParameters()
    }
  }
)
onUnmounted(() => {
  setContextData([], [])
})
</script>

<style scoped>
.design-platform { padding: 0; background: #fff; height: 100%; display: flex; flex-direction: column; overflow: hidden; }

/* 顶部统一标题栏 (V2) */
.platform-header-v2 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #eef2f6;
  flex-shrink: 0;
}

.header-left { display: flex; align-items: center; gap: 12px; }
.back-btn { padding: 0; height: auto; color: #64748b; font-size: 18px; }
.breadcrumb { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.breadcrumb .root { color: #94a3b8; }
.breadcrumb .sep { color: #cbd5e1; font-size: 12px; }
.breadcrumb .current { color: #1e293b; font-weight: 600; }
.type-tag { border-radius: 4px; }

.header-right { display: flex; align-items: center; gap: 20px; }
.shortcut-hints { display: flex; gap: 16px; color: #94a3b8; font-size: 12px; }
.shortcut-hints kbd {
  background: #f1f5f9;
  padding: 2px 4px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  font-family: inherit;
  color: #64748b;
}

.header-actions-v3 { display: flex; align-items: center; gap: 8px; }
.action-icon-btn { 
  font-size: 18px; 
  color: #64748b; 
  padding: 8px !important;
  transition: all 0.2s;
}
.action-icon-btn:hover { color: #3b82f6; background: #f1f5f9; }
.action-icon-btn.calc-symbol { color: #3b82f6; }
.action-icon-btn.calc-symbol:hover { background: #eff6ff; }

/* 流程导航栏 (V2) */
.platform-body-v2 { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.flow-nav-v2 {
  background: #f8fafc;
  border-bottom: 1px solid #eef2f6;
  padding: 0 20px;
  height: 40px;
  display: flex;
  align-items: center;
}

.flow-tabs { display: flex; align-items: center; gap: 4px; height: 100%; }
.flow-tab-v2 {
  height: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  cursor: pointer;
  font-size: 13px;
  color: #64748b;
  position: relative;
  transition: all 0.2s;
}

.flow-tab-v2:hover { color: #1e293b; background: #f1f5f9; }
.flow-tab-v2.active {
  color: #3b82f6;
  font-weight: 600;
}

.flow-tab-v2.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #3b82f6;
}

.tab-more { font-size: 12px; opacity: 0.5; margin-left: 4px; }
.add-flow-btn-v2 { margin-left: 12px; font-size: 13px; }

.design-scroll-area { flex: 1; overflow-y: auto; display: flex; flex-direction: column; background: #f1f5f9; }

/* 设计工作区 (V2) */
.design-workspace-v2 { padding: 16px 20px 40px; }

.step-collapse-v2 { border: none; background: transparent; }
.step-collapse-v2 :deep(.el-collapse-item) {
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}

.step-collapse-v2 :deep(.el-collapse-item__header) {
  padding: 0 20px;
  height: 48px;
  border-bottom: 1px solid #f1f5f9;
}

.step-collapse-v2 :deep(.el-collapse-item__content) {
  padding: 16px;
}

.step-title { display: flex; align-items: center; width: 100%; font-weight: 600; color: #1e293b; }
.step-order {
  background: #3b82f6;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  margin-right: 12px;
}
.step-ops { margin-left: auto; margin-right: 20px; }

/* 表格美化 (紧凑专业) */
.calculation-table { background: #fff; border-radius: 0; padding: 0; }
.design-table :deep(.el-table__header) th {
  background: #f8fafc;
  color: #64748b;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 0;
}

.param-name-cell { display: flex; align-items: center; gap: 4px; }
.expression-cell { display: flex; align-items: center; gap: 6px; }
.expr-input { flex: 1; }

.value-cell { 
  display: flex; 
  align-items: center; 
  justify-content: space-between;
  gap: 6px; 
  font-family: 'Consolas', monospace; 
  font-weight: 600; 
  color: #1e293b;
  width: 100%;
}
.value-cell.has-error { color: #ef4444; }

.note-cell { display: flex; align-items: center; gap: 8px; width: 100%; }
.table-footer { margin-top: 16px; display: flex; justify-content: space-between; align-items: center; }

.empty-steps {
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  border: 1px dashed #cbd5e1;
  margin-top: 10px;
}

.empty-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.workspace-footer {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  padding-bottom: 40px;
}

/* 弹窗样式补丁 */
.formula-dialog-body { display: flex; flex-direction: column; gap: 20px; }
.variable-mapping-card {
  background: #fff;
  border: 1px solid #3b82f620;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.05);
}
.formula-preview { background: #eff6ff; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #3b82f6; }
.expr-code { font-size: 15px; color: #1d4ed8; font-family: 'Consolas', monospace; }
.mapping-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  align-items: center;
  gap: 20px;
  padding: 10px;
  border-radius: 8px;
  transition: all 0.2s;
}
.mapping-row:hover { background: #f8fafc; }
.var-info { display: flex; flex-direction: column; }
.var-name { font-family: 'Consolas', monospace; font-weight: 600; color: #3b82f6; font-size: 13px; }
.var-desc { font-size: 11px; color: #94a3b8; }

.mapping-input { width: 100%; }

.suggestion-item { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.s-val { font-weight: 500; }
.s-desc { font-size: 11px; color: #94a3b8; margin-left: 10px; }

.submission-materials { margin-top: 30px; padding: 0 10px 40px; }
.material-card { border-radius: 8px; border: 1px solid #e2e8f0; }
.m-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; font-size: 14px; }

.note-upload { display: flex; align-items: center; }
.link-dialog-body { padding: 10px; }
</style>
