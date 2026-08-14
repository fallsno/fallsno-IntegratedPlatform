<template>
  <div class="model-parameter-matrix">
    <el-card v-if="!embeddedMode" class="matrix-hero" shadow="never">
      <div class="matrix-hero__content">
        <div>
          <div class="matrix-hero__eyebrow">Parameter Matrix</div>
          <h2>{{ matrix.family?.family_name || matrix.family?.family_code || '型号基础参数矩阵' }}</h2>
          <p>围绕系列维护不同型号的基础参数底稿，保留横向矩阵编辑习惯，同时把缺失值、参考复制和工作台联动收口到平台内。</p>
        </div>
        <div class="matrix-hero__stats">
          <div class="hero-stat">
            <div class="hero-stat__label">系列</div>
            <div class="hero-stat__value">{{ matrix.family?.family_code || '-' }}</div>
          </div>
          <div class="hero-stat">
            <div class="hero-stat__label">型号数</div>
            <div class="hero-stat__value">{{ matrix.versions?.length || 0 }}</div>
          </div>
          <div class="hero-stat">
            <div class="hero-stat__label">参数行</div>
            <div class="hero-stat__value">{{ matrix.rows?.length || 0 }}</div>
          </div>
        </div>
      </div>
    </el-card>

    <el-empty
      v-if="embeddedMode && !highlightParameterId"
      description="先在参数中心选择一个基础参数，再查看各型号初始值"
    />

    <div v-else class="matrix-layout" :class="{ 'matrix-layout--embedded': embeddedMode }">
      <el-card v-if="!embeddedMode" class="matrix-pane matrix-pane--tree" shadow="never">
        <DrumCategoryTree
          :tree-data="treeData"
          :current-node-id="selectedNodeId"
          title="选择系列或型号"
          description="矩阵按系列维护，型号用于快速预览列值"
          @select="handleTreeSelect"
        />
      </el-card>

      <el-card class="matrix-pane matrix-pane--table" shadow="never">
        <template #header>
          <div class="page-header">
            <div>
              <div class="page-title">{{ embeddedMode ? '各型号初始值编辑' : '系列型号矩阵' }}</div>
              <div class="page-subtitle">{{ embeddedMode ? embeddedSubtitle : headerSubtitle }}</div>
            </div>
            <div class="page-actions">
              <el-button v-if="!embeddedMode" @click="goToVersions" :disabled="!selectedFamilyId">版本管理</el-button>
              <el-button @click="loadMatrix" :disabled="!selectedFamilyId">刷新</el-button>
              <el-button v-if="!embeddedMode" @click="copyDialogVisible = true" :disabled="matrix.versions.length < 2">复制参考型号</el-button>
              <el-button type="primary" :loading="saving" :disabled="!selectedFamilyId" @click="saveMatrixRows">
                {{ embeddedMode ? '保存初始值' : '保存矩阵' }}
              </el-button>
            </div>
          </div>
        </template>

        <div class="matrix-toolbar">
          <el-input
            v-model="matrixKeyword"
            :placeholder="embeddedMode ? '搜索参数名称' : '搜索参数名称或编码'"
            clearable
          />
        </div>

        <el-empty v-if="!loading && !(matrix.versions || []).length" description="当前系列暂无型号版本" />
        <el-table
          v-else
          v-loading="loading"
          :data="filteredRows"
          stripe
          highlight-current-row
          :row-class-name="rowClassName"
          @current-change="handleCurrentRowChange"
        >
          <el-table-column prop="param_name" label="参数名称" min-width="180" fixed="left" />
          <el-table-column v-if="!embeddedMode" prop="param_code" label="参数编码" min-width="160" />
          <el-table-column prop="unit_code" label="单位" width="100" />
          <el-table-column
            v-for="ver in matrix.versions || []"
            :key="ver.id"
            :label="ver.version_code"
            min-width="150"
          >
            <template #header>
              <div class="column-header" :class="{ 'column-header--active': Number(selectedVersionId) === Number(ver.id) }">
                <span>{{ ver.version_code }}</span>
                <el-tag v-if="Number(selectedVersionId) === Number(ver.id)" size="small" type="success" effect="plain">
                  当前
                </el-tag>
              </div>
            </template>
            <template #default="{ row }">
              <el-input v-model="row.values[ver.id]" size="small" />
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card v-if="!embeddedMode" class="matrix-pane matrix-pane--insight" shadow="never">
        <template #header>
          <div class="page-title">矩阵提示</div>
        </template>

        <div class="insight-section">
          <div class="section-caption">当前型号预览</div>
          <div class="preview-list">
            <div v-for="item in previewRows" :key="item.parameterId || item.paramCode" class="preview-item">
              <div class="preview-item__name">{{ item.paramName }}</div>
              <div class="preview-item__value">{{ item.value || '未填写' }} {{ item.unitCode || '' }}</div>
            </div>
          </div>
        </div>

        <div class="insight-section">
          <div class="section-caption">当前参数分布</div>
          <el-skeleton v-if="distributionLoading" :rows="3" animated />
          <el-empty
            v-else-if="!distributionRows.length"
            description="选中参数后，可在这里查看该参数的型号分布"
          />
          <div v-else class="preview-list">
            <div
              v-for="item in distributionRows"
              :key="`${item.versionId}-${item.versionCode}`"
              class="preview-item"
            >
              <div class="preview-item__name">{{ item.versionCode }}</div>
              <div class="preview-item__value">{{ item.value || '未填写' }}</div>
            </div>
          </div>
        </div>

        <div class="insight-section">
          <div class="section-caption">缺失与异常</div>
          <el-empty v-if="!matrixWarnings.length" description="当前列没有明显缺口" />
          <ul v-else class="warning-list">
            <li v-for="warning in matrixWarnings" :key="warning.key">{{ warning.message }}</li>
          </ul>
        </div>

        <div class="insight-section">
          <div class="section-caption">快捷入口</div>
          <div class="quick-actions">
            <el-button type="primary" plain :disabled="!selectedVersionId" @click="goToWorkbench">
              用当前型号进入工作台
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <el-dialog v-model="copyDialogVisible" title="复制参考型号参数" width="520px">
      <el-form label-width="88px">
        <el-form-item label="来源型号">
          <el-select v-model="copyForm.sourceVersionId" placeholder="选择来源型号">
            <el-option
              v-for="item in matrix.versions"
              :key="item.id"
              :label="item.version_code"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标型号">
          <el-select v-model="copyForm.targetVersionId" placeholder="选择目标型号">
            <el-option
              v-for="item in matrix.versions"
              :key="item.id"
              :label="item.version_code"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="copyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="copyReferenceColumn">确认复制</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import DrumCategoryTree from '@/components/DrumCategoryTree.vue'
import {
  buildParameterDistributionRows,
  fetchFamilyMatrix,
  fetchParameterDistribution,
  saveFamilyMatrix
} from '@/api/designPlatform'
import { fetchDrumTree } from '@/api/drumDesign'
import { buildWorkbenchParameterRows } from '@/api/drumDesign.helpers.mjs'

const route = useRoute()
const router = useRouter()
const props = defineProps({
  familyId: {
    type: [String, Number],
    default: null
  },
  highlightParameterId: {
    type: [String, Number],
    default: null
  },
  highlightParameterName: {
    type: String,
    default: ''
  }
})

const loading = ref(false)
const saving = ref(false)
const treeData = ref([])
const selectedNodeId = ref('')
const selectedFamilyId = ref(props.familyId ? Number(props.familyId) : null)
const selectedVersionId = ref(null)
const selectedTypeRaw = ref(null)
const selectedFamilyRaw = ref(null)
const selectedVersionRaw = ref(null)
const currentRow = ref(null)
const copyDialogVisible = ref(false)
const matrixKeyword = ref('')
const distributionLoading = ref(false)
const parameterDistribution = ref({ values: [] })
const copyForm = ref({
  sourceVersionId: null,
  targetVersionId: null
})
const matrix = ref({
  family: null,
  versions: [],
  rows: []
})

const normalizeMatrix = (payload = {}) => ({
  family: payload.family || null,
  versions: Array.isArray(payload.versions) ? payload.versions : [],
  rows: Array.isArray(payload.rows)
    ? payload.rows.map((row) => ({
        ...row,
        values: { ...(row.values || {}) }
      }))
    : []
})

const embeddedMode = computed(() => route.name === 'ParameterCenter')
const effectiveKeyword = computed(() => {
  const keyword = String(matrixKeyword.value || props.highlightParameterName || '').trim()
  return keyword
})

const filteredRows = computed(() => {
  const keyword = effectiveKeyword.value
  const highlightParameterId = Number(props.highlightParameterId || 0)
  return (matrix.value.rows || []).filter((row) => {
    if (highlightParameterId > 0 && Number(row.parameter_id || 0) === highlightParameterId) {
      return true
    }
    if (!keyword) {
      return true
    }
    return (
      String(row.param_name || '').includes(keyword) ||
      String(row.param_code || '').includes(keyword)
    )
  })
})

const distributionRows = computed(() => buildParameterDistributionRows(parameterDistribution.value))
const highlightParameterId = computed(() => Number(props.highlightParameterId || 0))

const headerSubtitle = computed(() => {
  const tName = selectedTypeRaw.value?.type_name || '未选择分类'
  const fName = selectedFamilyRaw.value?.family_name || selectedFamilyRaw.value?.family_code || matrix.value.family?.family_name || '未选择系列'
  const vCode = selectedVersionRaw.value?.version_code || matrix.value.versions.find((item) => Number(item.id) === Number(selectedVersionId.value))?.version_code
  
  if (vCode) {
    return `${tName} / ${fName} / ${vCode}`
  }
  return `${tName} / ${fName}`
})

const embeddedSubtitle = computed(() => {
  if (!props.highlightParameterName) {
    return '选择参数后可按型号查看和编辑初始值'
  }
  const familyName = selectedFamilyRaw.value?.family_name || selectedFamilyRaw.value?.family_code || matrix.value.family?.family_name || matrix.value.family?.family_code || '当前系列'
  return `当前参数：${props.highlightParameterName}，正在编辑 ${familyName} 下各型号的初始值`
})

const previewRows = computed(() => buildWorkbenchParameterRows(matrix.value, selectedVersionId.value).slice(0, 8))

const matrixWarnings = computed(() => {
  const warnings = []
  if (!selectedVersionId.value) {
    return warnings
  }
  const emptyRows = (matrix.value.rows || []).filter((row) => !String((row.values || {})[selectedVersionId.value] || '').trim())
  if (emptyRows.length) {
    warnings.push({
      key: 'empty',
      message: `${emptyRows.length} 个参数在当前型号下仍为空值，建议优先补齐关键输入项。`
    })
  }
  const invalidRows = (matrix.value.rows || []).filter((row) => {
    const value = String((row.values || {})[selectedVersionId.value] || '').trim()
    return value && Number.isNaN(Number(value))
  })
  if (invalidRows.length) {
    warnings.push({
      key: 'invalid',
      message: `${invalidRows.length} 个参数不是数值，后续工作台计算时可能无法参与公式求解。`
    })
  }
  if (currentRow.value?.param_name) {
    warnings.push({
      key: 'focus',
      message: `当前关注参数：${currentRow.value.param_name}，可结合右侧预览检查不同型号差异。`
    })
  }
  return warnings
})

const rowClassName = ({ row }) => {
  return Number(row?.parameter_id || 0) === Number(props.highlightParameterId || 0)
    ? 'is-highlighted-row'
    : ''
}

const pickDefaultNode = (rows = []) => {
  const firstType = rows[0]
  const firstFamily = firstType?.children?.[0]
  const firstVersion = firstFamily?.children?.[0]
  if (!firstType) return null
  return { 
    node: firstVersion || firstFamily || firstType,
    typeRaw: firstType.raw,
    familyRaw: firstFamily?.raw || null,
    versionRaw: firstVersion?.raw || null
  }
}

const findTreeNodeByIds = (familyId, versionId) => {
  for (const typeNode of treeData.value) {
    for (const familyNode of typeNode.children || []) {
      if (versionId) {
        const versionNode = (familyNode.children || []).find((item) => Number(item.raw?.id) === Number(versionId))
        if (versionNode) {
          return { node: versionNode, typeRaw: typeNode.raw, familyRaw: familyNode.raw, versionRaw: versionNode.raw }
        }
      }
      if (Number(familyNode.raw?.id) === Number(familyId)) {
        return { node: familyNode, typeRaw: typeNode.raw, familyRaw: familyNode.raw, versionRaw: null }
      }
    }
  }
  return null
}

const syncSelectedVersion = () => {
  const currentVersion = matrix.value.versions.find((item) => Number(item.id) === Number(selectedVersionId.value))
  if (currentVersion) return
  selectedVersionId.value = matrix.value.versions[0]?.id || null
}

const loadTree = async () => {
  treeData.value = await fetchDrumTree()
  const target = findTreeNodeByIds(selectedFamilyId.value, selectedVersionId.value)
  if (target) {
    selectedNodeId.value = target.node.id
    selectedTypeRaw.value = target.typeRaw
    selectedFamilyRaw.value = target.familyRaw
    selectedVersionRaw.value = target.versionRaw
    return
  }
  if (!selectedNodeId.value) {
    const fallbackNode = pickDefaultNode(treeData.value)
    if (fallbackNode) {
      selectedNodeId.value = fallbackNode.node.id
      selectedTypeRaw.value = fallbackNode.typeRaw
      selectedFamilyRaw.value = fallbackNode.familyRaw
      selectedVersionRaw.value = fallbackNode.versionRaw
    }
  }
}

const loadParameterDistribution = async (parameterId) => {
  const normalizedParameterId = Number(parameterId || 0)
  if (!normalizedParameterId) {
    parameterDistribution.value = { values: [] }
    return null
  }
  distributionLoading.value = true
  try {
    const distribution = await fetchParameterDistribution(normalizedParameterId)
    parameterDistribution.value = distribution || { values: [] }
    return distribution
  } catch (error) {
    parameterDistribution.value = { values: [] }
    return null
  } finally {
    distributionLoading.value = false
  }
}

const loadDistributionContext = async () => {
  const highlightParameterId = Number(props.highlightParameterId || 0)
  if (!highlightParameterId) {
    parameterDistribution.value = { values: [] }
    return
  }
  const distribution = await loadParameterDistribution(highlightParameterId)
  if (!selectedFamilyId.value && distribution?.family_id) {
    selectedFamilyId.value = Number(distribution.family_id)
  }
  if (!selectedVersionId.value) {
    const firstVersion = buildParameterDistributionRows(distribution || {})[0]
    if (firstVersion?.versionId) {
      selectedVersionId.value = firstVersion.versionId
    }
  }
}

const loadMatrix = async () => {
  if (!selectedFamilyId.value) return
  loading.value = true
  try {
    matrix.value = normalizeMatrix(await fetchFamilyMatrix(selectedFamilyId.value))
    syncSelectedVersion()
  } catch (error) {
    ElMessage.error('加载矩阵失败')
  } finally {
    loading.value = false
  }
}

const applyFamilySelection = async (familyId, versionId = null, typeRaw = null, familyRaw = null, versionRaw = null) => {
  if (!familyId) return
  selectedFamilyId.value = Number(familyId)
  selectedVersionId.value = versionId ? Number(versionId) : null
  selectedTypeRaw.value = typeRaw
  selectedFamilyRaw.value = familyRaw
  selectedVersionRaw.value = versionRaw
  if (!embeddedMode.value) {
    await router.replace({ name: 'ModelParameterMatrix', params: { familyId: Number(familyId) } })
  }
  await loadMatrix()
  // await loadTree() // no need to load tree again
}

const handleTreeSelect = async ({ data, node }) => {
  selectedNodeId.value = data?.id || ''
  if (data?.level === 'version') {
    await applyFamilySelection(node?.parent?.data?.raw?.id, data.raw?.id, node?.parent?.parent?.data?.raw, node?.parent?.data?.raw, data.raw)
    return
  }
  if (data?.level === 'family') {
    await applyFamilySelection(data.raw?.id, null, node?.parent?.data?.raw, data.raw, null)
    return
  }
  const firstFamily = data?.children?.[0]
  if (firstFamily?.raw?.id) {
    const firstVersion = firstFamily.children?.[0]
    await applyFamilySelection(firstFamily.raw.id, firstVersion?.raw?.id || null, data.raw, firstFamily.raw, firstVersion?.raw || null)
  }
}

const saveMatrixRows = async () => {
  saving.value = true
  try {
    const result = await saveFamilyMatrix(selectedFamilyId.value, matrix.value.rows || [])
    ElMessage.success(`已保存 ${result.saved_count || 0} 条矩阵数据`)
    await loadMatrix()
  } catch (error) {
    ElMessage.error(embeddedMode.value ? '保存各型号初始值失败' : '保存矩阵失败')
  } finally {
    saving.value = false
  }
}

const copyReferenceColumn = () => {
  const sourceVersionId = Number(copyForm.value.sourceVersionId || 0)
  const targetVersionId = Number(copyForm.value.targetVersionId || 0)
  if (!sourceVersionId || !targetVersionId || sourceVersionId === targetVersionId) {
    ElMessage.warning('请选择不同的来源型号和目标型号')
    return
  }
  matrix.value.rows = (matrix.value.rows || []).map((row) => ({
    ...row,
    values: {
      ...(row.values || {}),
      [targetVersionId]: (row.values || {})[sourceVersionId] ?? ''
    }
  }))
  selectedVersionId.value = targetVersionId
  copyDialogVisible.value = false
  ElMessage.success('已复制参考型号参数')
}

const goToVersions = () => {
  if (!selectedFamilyId.value) return
  router.push({ name: 'Versions', params: { familyId: selectedFamilyId.value } })
}

const goToWorkbench = () => {
  if (!selectedFamilyId.value || !selectedVersionId.value) return
  router.push({
    name: 'DesignWorkbench',
    query: {
      familyId: selectedFamilyId.value,
      versionId: selectedVersionId.value
    }
  })
}

const handleCurrentRowChange = (row) => {
  currentRow.value = row || null
  loadParameterDistribution(row?.parameter_id)
}

watch(
  () => props.familyId,
  async (value) => {
    const nextFamilyId = Number(value || route.params.familyId || selectedFamilyId.value || 0)
    if (nextFamilyId) {
      selectedFamilyId.value = nextFamilyId
      await loadMatrix()
    }
  },
  { immediate: true }
)

watch(
  () => [props.highlightParameterId, props.highlightParameterName],
  async () => {
    matrixKeyword.value = String(props.highlightParameterName || '').trim()
    await loadDistributionContext()
    if (selectedFamilyId.value) {
      await loadTree()
      await loadMatrix()
    }
  },
  { immediate: true }
)

onMounted(async () => {
  matrixKeyword.value = String(props.highlightParameterName || '').trim()
  await loadDistributionContext()
  await loadTree()
  if (selectedFamilyId.value) {
    await loadMatrix()
  }
})
</script>

<style scoped>
.model-parameter-matrix {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.matrix-hero {
  border: none;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.16), transparent 28%),
    linear-gradient(135deg, #0f172a, #1e293b 58%, #155e75);
  color: #e2e8f0;
}

.matrix-hero :deep(.el-card__body) {
  padding: 24px;
}

.matrix-hero__content {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.matrix-hero__eyebrow {
  margin-bottom: 8px;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #67e8f9;
}

.matrix-hero h2 {
  margin: 0;
  color: #f8fafc;
}

.matrix-hero p {
  margin-top: 10px;
  max-width: 760px;
  color: rgba(226, 232, 240, 0.84);
  line-height: 1.7;
}

.matrix-hero__stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(88px, 1fr));
  gap: 12px;
  min-width: 280px;
}

.hero-stat {
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.35);
}

.hero-stat__label {
  font-size: 12px;
  color: #94a3b8;
}

.hero-stat__value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 700;
  color: #f8fafc;
}

.matrix-layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr) 320px;
  gap: 16px;
  min-height: 720px;
}

.matrix-layout--embedded {
  grid-template-columns: minmax(0, 1fr);
  min-height: auto;
}

.matrix-pane {
  min-height: 0;
}

.matrix-layout--embedded .matrix-pane--table {
  min-width: 0;
}

.matrix-pane--tree :deep(.el-card__body),
.matrix-pane--insight :deep(.el-card__body) {
  height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
}

.page-subtitle {
  margin-top: 4px;
  color: #64748b;
}

.page-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.matrix-toolbar {
  margin-bottom: 16px;
}

.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.column-header--active {
  color: #0f766e;
}

.insight-section + .insight-section {
  margin-top: 18px;
}

.section-caption {
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}

.preview-list {
  display: grid;
  gap: 10px;
}

.preview-item {
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.preview-item__name {
  font-size: 12px;
  color: #64748b;
}

.preview-item__value {
  margin-top: 6px;
  font-weight: 700;
  color: #0f172a;
}

.warning-list {
  padding-left: 18px;
  color: #475569;
  line-height: 1.8;
}

.quick-actions {
  display: grid;
  gap: 10px;
}

.matrix-pane--table :deep(.is-highlighted-row) {
  --el-table-tr-bg-color: #eff6ff;
}

@media (max-width: 1440px) {
  .matrix-layout {
    grid-template-columns: 280px minmax(0, 1fr);
  }

  .matrix-pane--insight {
    grid-column: 1 / -1;
  }
}
</style>
