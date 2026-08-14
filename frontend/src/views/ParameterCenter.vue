<template>
  <div class="parameter-center">
    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="输入参数" name="matrix">
          <div class="matrix-toolbar">
            <div class="toolbar toolbar--structure">
              <el-segmented v-model="activeProductCategory" :options="productCategoryOptions" />
              <el-select v-model="activeFamilyId" placeholder="选择系列" style="width: 240px">
                <el-option
                  v-for="item in familyOptions"
                  :key="item.familyId"
                  :label="item.label"
                  :value="item.familyId"
                />
              </el-select>
              <span v-if="currentFamilySummary" class="toolbar-tip toolbar-tip--family">
                {{ currentFamilySummary }}
              </span>
            </div>
            <div class="toolbar">
              <el-input v-model="filters.keyword" placeholder="搜索参数名或编码" clearable @keyup.enter="loadMatrix" />
              <el-button type="primary" @click="loadMatrix">查询</el-button>
              <el-button :disabled="!filters.keyword" @click="resetFilters">重置</el-button>
              <span class="toolbar-tip">
                已识别 {{ versions.length }} 个型号列，当前显示 {{ visibleVersions.length }} 个；工作台与参数中心共用同一套输入参数值
              </span>
            </div>
            <div class="matrix-toolbar__actions">
              <span class="toolbar-tip toolbar-tip--readonly">参数来源：工作台输入参数自动同步</span>
              <el-button
                type="success"
                :loading="savingMatrix"
                :disabled="!dirtyCellKeys.size"
                @click="saveMatrixChanges"
              >
                保存矩阵
              </el-button>
            </div>
          </div>

          <el-table
            :data="matrixRows"
            stripe
            border
            row-key="parameterId"
            v-loading="loading"
            highlight-current-row
            max-height="640"
            @current-change="handleCurrentRowChange"
          >
            <el-table-column prop="categoryCode" label="分类" min-width="140" />
            <el-table-column prop="paramName" label="参数名" min-width="180" fixed="left" />
            <el-table-column prop="unitCode" label="单位" width="90" />
            <el-table-column
              v-for="version in visibleVersions"
              :key="version.id"
              min-width="140"
            >
              <template #header>
                <div class="matrix-header">
                  <div class="matrix-header__main">
                    <span>{{ version.version_code }}</span>
                    <span class="matrix-header__meta">{{ getVersionMeta(version).capacityLabel }}</span>
                    <span class="matrix-header__meta matrix-header__meta--weak">
                      {{ getVersionMeta(version).namingLabel || getVersionMeta(version).subtypeLabel || '待识别' }}
                    </span>
                  </div>
                  <el-button link type="danger" size="small" @click.stop="confirmDeleteVersion(version)">删</el-button>
                </div>
              </template>
              <template #default="{ row }">
                <el-input
                  v-model="row.values[version.id]"
                  size="small"
                  @input="markCellDirty(row, version.id)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="danger" @click="confirmDeleteParameter(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-card shadow="never" class="trend-panel">
            <div class="trend-panel__header">
              <div>
                <div class="trend-panel__title">参数产量趋势</div>
                <div class="trend-panel__subtitle">{{ trendSubtitle }}</div>
              </div>
              <el-segmented v-model="trendViewMode" :options="trendViewOptions" />
            </div>

            <el-skeleton v-if="distributionLoading" :rows="4" animated />
            <el-empty
              v-else-if="!trendRows.length"
              description="选择参数后，可按当前系列查看不同产量档的变化趋势"
            />
            <div v-else-if="trendViewMode === 'chart'" ref="trendChartRef" class="trend-panel__chart"></div>
            <el-table v-else :data="trendRows" stripe border max-height="320">
              <el-table-column prop="capacityLabel" label="产量档" width="110" />
              <el-table-column prop="versionCode" label="型号" width="140" />
              <el-table-column prop="meaning" label="型号含义" min-width="220" />
              <el-table-column label="参数值" min-width="140">
                <template #default="{ row }">
                  <span :class="['trend-value', { 'trend-value--danger': row.isAnomaly }]">
                    {{ row.value || '未填写' }} {{ currentRow?.unitCode || '' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="90">
                <template #default="{ row }">
                  <span :class="['trend-flag', { 'trend-flag--danger': row.isAnomaly }]">
                    {{ row.isAnomaly ? '异常' : '正常' }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="附录图表" name="lookup">
          <ParameterLookupPanel
            v-if="lookupPanelReady"
            :lookups="lookupItems"
            :rows="lookupRows"
            :active-lookup-id="activeLookupId"
            :active-lookup-name="activeLookupName"
            :curve-profile="lookupCurveProfile"
            :curve-saving="lookupCurveSaving"
            :panel-visible="activeTab === 'lookup'"
            @create="openLookupCreate"
            @edit="openLookupEdit"
            @delete="confirmDeleteLookup"
            @select="handleLookupSelect"
            @add-row="handleLookupAddRow"
            @remove-row="handleLookupRemoveRow"
            @import="showLookupImport = true"
            @save-rows="handleLookupRowSave"
            @save-curve-profile="handleLookupCurveProfileSave"
            @update-curve-profile="lookupCurveProfile = $event"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="showVersionDialog" title="新增型号" width="420px">
      <el-form :model="versionForm" label-width="88px">
        <el-form-item label="所属系列">
          <el-select v-model="versionForm.family_id">
            <el-option
              v-for="item in familyOptions"
              :key="item.familyId"
              :label="item.label"
              :value="item.familyId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="型号编码">
          <el-input v-model="versionForm.version_code" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="versionForm.display_name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showVersionDialog = false">取消</el-button>
          <el-button type="primary" :loading="versionSaving" @click="saveVersion">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <ParameterImportDialog v-model="showImport" @done="loadParameters" />
    <ParameterLookupImportDialog
      v-model="showLookupImport"
      :previewer="previewParameterLookupImport"
      @apply="applyLookupImportRows"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'

import ParameterImportDialog from '@/components/ParameterImportDialog.vue'
import ParameterLookupImportDialog from '@/components/ParameterLookupImportDialog.vue'
import ParameterLookupPanel from '@/components/ParameterLookupPanel.vue'
import {
  buildParameterDistributionRows,
  buildParameterCode,
  createParameter,
  createParameterLookup,
  deleteParameterLookup,
  deleteParameterDefinition,
  createFamilyVersion,
  deleteVersionDefinition,
  fetchParameterCenterMatrix,
  fetchParameterDistribution,
  fetchParameterLookupCurveProfile,
  fetchParameterLookups,
  fetchParameterLookupRows,
  previewParameterLookupImport,
  saveFamilyMatrix,
  saveParameterLookupCurveProfile,
  saveParameterLookupRows,
  updateParameterLookup,
  updateParameter
} from '@/api/designPlatform.js'
import { resolveLookupFocusFromQuery } from '@/api/drumDesignLookup.helpers.mjs'
import { buildCurveProfileDraftFromImportPreview, normalizeParameterLookupCurveProfile } from '@/api/parameterLookup.helpers.mjs'
import {
  detectParameterTrendAnomalies,
  getParameterCenterCategoryLabel,
  getParameterCenterCategoryOrder,
  resolveParameterCenterModelMeta
} from '@/views/parameterCenterModelMeta.mjs'

const route = useRoute()
const router = useRouter()
const activeTab = ref('matrix')
const activeProductCategory = ref('virgin')
const activeFamilyId = ref(null)
const loading = ref(false)
const savingMatrix = ref(false)
const matrixRows = ref([])
const versions = ref([])
const currentRow = ref(null)
const showImport = ref(false)
const detailVisible = ref(false)
const detailMode = ref('edit')
const detailSaving = ref(false)
const detailForm = ref({
  id: null,
  param_code: '',
  param_name: '',
  unit_code: '',
  category_code: 'basic',
  value_type: 'basic'
})
const showVersionDialog = ref(false)
const versionSaving = ref(false)
const versionForm = ref({
  family_id: null,
  version_code: '',
  display_name: ''
})
const filters = ref({
  keyword: '',
  module_code: String(route.query.moduleCode || '')
})
const trendViewMode = ref('chart')
const originalCellValues = ref(new Map())
const dirtyCellKeys = ref(new Set())
const lookupItems = ref([])
const lookupRows = ref([])
const activeLookupId = ref(0)
const showLookupImport = ref(false)
const lookupCurveProfile = ref(normalizeParameterLookupCurveProfile({}))
const lookupCurveSaving = ref(false)
const lookupLoaded = ref(false)
const parameterDistribution = ref({ values: [] })
const distributionLoading = ref(false)
const trendChartRef = ref(null)
let trendChartInstance = null

const trendViewOptions = [
  { label: '趋势图', value: 'chart' },
  { label: '表格', value: 'table' }
]

const versionMetaMap = computed(() => {
  const result = new Map()
  versions.value.forEach((version) => {
    result.set(Number(version.id || 0), resolveParameterCenterModelMeta(version))
  })
  return result
})

const productCategoryOptions = computed(() => {
  const available = new Set(
    versions.value.map((version) => resolveParameterCenterModelMeta(version).categoryKey)
  )
  return getParameterCenterCategoryOrder()
    .filter((key) => available.has(key))
    .map((key) => ({
      label: getParameterCenterCategoryLabel(key),
      value: key
    }))
})

const visibleVersions = computed(() => {
  const selectedFamilyId = Number(activeFamilyId.value || 0)
  if (!selectedFamilyId) {
    return []
  }
  return versions.value
    .filter((item) => Number(item.family_id || 0) === selectedFamilyId)
    .sort((left, right) => {
      const leftMeta = versionMetaMap.value.get(Number(left.id || 0))
      const rightMeta = versionMetaMap.value.get(Number(right.id || 0))
      const leftSort = Number(leftMeta?.sortValue ?? Number.MAX_SAFE_INTEGER)
      const rightSort = Number(rightMeta?.sortValue ?? Number.MAX_SAFE_INTEGER)
      if (leftSort !== rightSort) return leftSort - rightSort
      return String(left.version_code || '').localeCompare(String(right.version_code || ''), 'zh-CN')
    })
})
const lookupPanelReady = computed(() => activeTab.value === 'lookup' || lookupLoaded.value)
const activeLookupName = computed(() => {
  const matched = lookupItems.value.find((item) => Number(item.id) === Number(activeLookupId.value || 0))
  return matched?.lookup_name || ''
})

const familyOptions = computed(() => {
  const seen = new Map()
  versions.value.forEach((item) => {
    const meta = resolveParameterCenterModelMeta(item)
    if (meta.categoryKey !== activeProductCategory.value) return
    const familyId = Number(item.family_id || 0)
    if (!familyId) return
    const entry = seen.get(familyId)
    if (entry) {
      entry.count += 1
      return
    }
    seen.set(familyId, {
      familyId,
      count: 1,
      label: `${item.family_code || meta.categoryLabel} · ${meta.subtypeLabel || meta.namingLabel || '型号组'}`
    })
  })
  return [...seen.values()].map((item) => ({
    familyId: item.familyId,
    label: `${item.label} (${item.count})`
  }))
})

const currentFamilyMeta = computed(() => {
  const version = visibleVersions.value[0]
  return version ? versionMetaMap.value.get(Number(version.id || 0)) || null : null
})

const currentFamilySummary = computed(() => {
  const familyMeta = currentFamilyMeta.value
  if (!familyMeta) return ''
  return [familyMeta.categoryLabel, familyMeta.subtypeLabel, familyMeta.namingLabel].filter(Boolean).join(' / ')
})

const trendRows = computed(() => {
  const visibleVersionMap = new Map(
    visibleVersions.value.map((item) => [Number(item.id || 0), item])
  )
  const baseRows = buildParameterDistributionRows(parameterDistribution.value)
    .filter((item) => visibleVersionMap.has(Number(item.versionId || 0)))
    .map((item) => {
      const meta = versionMetaMap.value.get(Number(item.versionId || 0))
      return {
        ...item,
        capacityLabel: meta?.capacityLabel || '产量待补充',
        meaning: meta?.meaning || item.versionCode,
        sortValue: Number(meta?.sortValue ?? Number.MAX_SAFE_INTEGER)
      }
    })
    .sort((left, right) => {
      if (left.sortValue !== right.sortValue) return left.sortValue - right.sortValue
      return String(left.versionCode || '').localeCompare(String(right.versionCode || ''), 'zh-CN')
    })

  const anomalyIndexes = detectParameterTrendAnomalies(baseRows)
  return baseRows.map((item, index) => ({
    ...item,
    isAnomaly: anomalyIndexes.has(index)
  }))
})

const trendSubtitle = computed(() => {
  if (!currentRow.value?.paramName) {
    return '当前页只保留输入参数，选中参数后可按产量档查看趋势与异常点'
  }
  const familyLabel = currentFamilyMeta.value?.familyLabel || currentFamilySummary.value || '当前系列'
  return `${currentRow.value.paramName} 在 ${familyLabel} 下的产量分布`
})

const createEmptyDetailForm = () => ({
  id: null,
  param_code: '',
  param_name: '',
  unit_code: '',
  category_code: 'basic'
})

const buildCellKey = (parameterId, versionId) => `${Number(parameterId || 0)}:${Number(versionId || 0)}`

const snapshotOriginalValues = (rows = []) => {
  const nextMap = new Map()
  rows.forEach((row) => {
    versions.value.forEach((version) => {
      nextMap.set(buildCellKey(row.parameterId, version.id), String(row.values?.[version.id] ?? ''))
    })
  })
  originalCellValues.value = nextMap
  dirtyCellKeys.value = new Set()
}

const normalizeMatrixRows = (payload = {}) => {
  versions.value = Array.isArray(payload.versions) ? payload.versions : []
  syncActiveProductCategory()
  syncActiveFamily()
  const rows = Array.isArray(payload.rows)
    ? payload.rows.map((row) => {
        const values = { ...(row?.values || {}) }
        versions.value.forEach((version) => {
          if (!(version.id in values)) {
            values[version.id] = ''
          }
        })
        return {
          parameterId: Number(row.parameter_id || 0),
          paramCode: row.param_code || '',
          paramName: row.param_name || '',
          displayName: row.display_name || '',
          unitCode: row.unit_code || '',
          categoryCode: row.category_code || 'basic',
          defaultValue: row.default_value == null ? '' : String(row.default_value),
          values
        }
      })
    : []
  matrixRows.value = rows
  snapshotOriginalValues(rows)
}

const getVersionMeta = (version) => versionMetaMap.value.get(Number(version?.id || 0)) || resolveParameterCenterModelMeta(version || {})

const syncActiveProductCategory = () => {
  const availableCategoryKeys = productCategoryOptions.value.map((item) => item.value)
  if (!availableCategoryKeys.length) {
    activeProductCategory.value = 'virgin'
    return
  }
  if (availableCategoryKeys.includes(activeProductCategory.value)) {
    return
  }
  activeProductCategory.value = availableCategoryKeys[0]
}

const syncActiveFamily = () => {
  const availableFamilyIds = familyOptions.value.map((item) => Number(item.familyId || 0)).filter(Boolean)
  if (!availableFamilyIds.length) {
    activeFamilyId.value = null
    return
  }
  const currentFamilyId = Number(activeFamilyId.value || 0)
  if (availableFamilyIds.includes(currentFamilyId)) {
    return
  }
  const queryFamilyId = Number(route.query.familyId || 0)
  if (availableFamilyIds.includes(queryFamilyId)) {
    activeFamilyId.value = queryFamilyId
    return
  }
  activeFamilyId.value = availableFamilyIds[0]
}

const loadParameterDistribution = async (parameterId) => {
  const normalizedParameterId = Number(parameterId || 0)
  if (!normalizedParameterId) {
    parameterDistribution.value = { values: [] }
    return
  }
  distributionLoading.value = true
  try {
    parameterDistribution.value = await fetchParameterDistribution(
      normalizedParameterId,
      String(filters.value.module_code || '')
    )
  } catch (error) {
    console.error(error)
    parameterDistribution.value = { values: [] }
  } finally {
    distributionLoading.value = false
  }
}

const loadParameterContext = async (row) => {
  currentRow.value = row || null
  await loadParameterDistribution(row?.parameterId)
}

const loadMatrix = async () => {
  loading.value = true
  try {
    const payload = await fetchParameterCenterMatrix(filters.value)
    normalizeMatrixRows(payload)
    if (!matrixRows.value.length) {
      currentRow.value = null
      return
    }
    const nextRow =
      matrixRows.value.find((item) => Number(item.parameterId) === Number(currentRow.value?.parameterId || 0)) ||
      matrixRows.value[0]
    await loadParameterContext(nextRow)
  } catch (error) {
    console.error(error)
    ElMessage.error('加载参数矩阵失败')
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  detailMode.value = 'create'
  detailForm.value = createEmptyDetailForm()
  detailVisible.value = true
}

const openDetail = (row) => {
  loadParameterContext(row)
  detailMode.value = 'edit'
  detailForm.value = {
    id: row.parameterId,
    param_code: row.paramCode,
    param_name: row.paramName,
    unit_code: row.unitCode,
    category_code: row.categoryCode || 'basic',
    value_type: row.valueType || 'basic'
  }
  detailVisible.value = true
}

const markCellDirty = (row, versionId) => {
  const cellKey = buildCellKey(row.parameterId, versionId)
  const currentValue = String(row.values?.[versionId] ?? '')
  const originalValue = String(originalCellValues.value.get(cellKey) ?? '')
  const nextKeys = new Set(dirtyCellKeys.value)
  if (currentValue === originalValue) {
    nextKeys.delete(cellKey)
  } else {
    nextKeys.add(cellKey)
  }
  dirtyCellKeys.value = nextKeys
}

const saveMatrixChanges = async () => {
  if (!dirtyCellKeys.value.size) {
    ElMessage.info('当前没有需要保存的矩阵改动')
    return
  }

  const versionMap = new Map(versions.value.map((item) => [Number(item.id), item]))
  const groups = new Map()
  const changedCount = dirtyCellKeys.value.size

  matrixRows.value.forEach((row) => {
    versions.value.forEach((version) => {
      const cellKey = buildCellKey(row.parameterId, version.id)
      if (!dirtyCellKeys.value.has(cellKey) || !version.family_id) return
      if (!groups.has(version.family_id)) {
        groups.set(version.family_id, new Map())
      }
      const familyRows = groups.get(version.family_id)
      if (!familyRows.has(row.parameterId)) {
        familyRows.set(row.parameterId, { parameter_id: row.parameterId, values: {} })
      }
      familyRows.get(row.parameterId).values[version.id] = String(row.values?.[version.id] ?? '')
    })
  })

  savingMatrix.value = true
  try {
    for (const [familyId, familyRows] of groups.entries()) {
      await saveFamilyMatrix(familyId, Array.from(familyRows.values()))
    }
    await loadMatrix()
    ElMessage.success(`矩阵已保存，共回写 ${changedCount} 处真实改动`)
  } catch (error) {
    console.error(error)
    const firstVersion = versionMap.get(Number(String([...dirtyCellKeys.value][0] || '0:0').split(':')[1]))
    const versionHint = firstVersion?.version_code ? `（含型号 ${firstVersion.version_code}）` : ''
    ElMessage.error(error?.response?.data?.detail || `保存参数矩阵失败${versionHint}`)
  } finally {
    savingMatrix.value = false
  }
}

const saveDetail = async () => {
  detailSaving.value = true
  try {
    const payload = {
      param_code: detailForm.value.param_code || buildParameterCode(detailForm.value.param_name),
      param_name: detailForm.value.param_name,
      display_name: detailForm.value.param_name,
      category_code: detailForm.value.category_code || 'basic',
      unit_code: detailForm.value.unit_code || '',
      value_type: 'basic',
      data_type: 'number',
      precision: 2,
      default_value: '',
      description: '',
      status: 'active'
    }
    if (detailMode.value === 'create') {
      await createParameter(payload)
    } else {
      await updateParameter(detailForm.value.id, payload)
    }
    detailVisible.value = false
    await loadMatrix()
    ElMessage.success('参数补充信息已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.detail || '保存参数补充信息失败')
  } finally {
    detailSaving.value = false
  }
}

const handleCurrentRowChange = async (row) => {
  if (!row?.parameterId) return
  await loadParameterContext(row)
}

const resetFilters = async () => {
  filters.value.keyword = ''
  await loadMatrix()
}

const loadParameters = loadMatrix

const applyLookupFocusQuery = async () => {
  const focus = resolveLookupFocusFromQuery(route.query)
  if (!focus) {
    return
  }
  if (focus.activeTab === 'lookup') {
    await ensureLookupPanelReady()
  }
  activeTab.value = focus.activeTab
  const matchedLookup = lookupItems.value.find((item) => Number(item.id) === focus.lookupId)
  if (matchedLookup) {
    await handleLookupSelect(matchedLookup)
  } else {
    activeLookupId.value = focus.lookupId
  }
  await router.replace({ name: 'ParameterCenter', query: {} })
  if (focus.fromFormula) {
    ElMessage.success(`已定位到附录图表：${focus.lookupName || activeLookupName.value || '目标附录'}`)
  }
}

const loadLookupItems = async () => {
  try {
    lookupItems.value = await fetchParameterLookups()
    lookupLoaded.value = true
    if (!lookupItems.value.length) {
      activeLookupId.value = 0
      lookupRows.value = []
      lookupCurveProfile.value = normalizeParameterLookupCurveProfile({})
      return
    }
    const existing = lookupItems.value.find((item) => Number(item.id) === Number(activeLookupId.value || 0))
    if (!existing) {
      await handleLookupSelect(lookupItems.value[0])
    }
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.detail || '加载查表附录失败')
  }
}

const ensureLookupPanelReady = async () => {
  if (lookupLoaded.value) {
    return
  }
  await loadLookupItems()
}

const handleLookupSelect = async (lookup) => {
  activeLookupId.value = Number(lookup?.id || 0)
  if (!activeLookupId.value) {
    lookupRows.value = []
    lookupCurveProfile.value = normalizeParameterLookupCurveProfile({})
    return
  }
  try {
    const [rows, curveProfile] = await Promise.all([fetchParameterLookupRows(activeLookupId.value), fetchParameterLookupCurveProfile(activeLookupId.value)])
    lookupRows.value = rows
    lookupCurveProfile.value = curveProfile
  } catch (error) {
    console.error(error)
    lookupRows.value = []
    lookupCurveProfile.value = normalizeParameterLookupCurveProfile({})
    ElMessage.error(error?.response?.data?.detail || '加载附录明细失败')
  }
}

const openLookupCreate = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入附录名称', '新增查表附录', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：电机扭矩参数'
    })
    const lookup = await createParameterLookup({
      lookup_code: buildParameterCode(value),
      lookup_name: value
    })
    ElMessage.success('查表附录已新增')
    await loadLookupItems()
    await handleLookupSelect(lookup)
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.detail || '新增查表附录失败')
    }
  }
}

const openLookupEdit = async () => {
  const currentLookup = lookupItems.value.find((item) => Number(item.id) === Number(activeLookupId.value || 0))
  if (!currentLookup) {
    ElMessage.warning('请先选择查表附录')
    return
  }
  try {
    const { value } = await ElMessageBox.prompt('请输入附录名称', '编辑查表附录', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: currentLookup.lookup_name,
      inputPlaceholder: '例如：电机扭矩参数'
    })
    await updateParameterLookup(currentLookup.id, {
      lookup_code: currentLookup.lookup_code,
      lookup_name: value,
      description: currentLookup.description || '',
      status: currentLookup.status || 'active'
    })
    ElMessage.success('查表附录已更新')
    await loadLookupItems()
    const refreshed = lookupItems.value.find((item) => Number(item.id) === Number(currentLookup.id))
    if (refreshed) {
      await handleLookupSelect(refreshed)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.detail || '编辑查表附录失败')
    }
  }
}

const confirmDeleteLookup = async () => {
  const currentLookup = lookupItems.value.find((item) => Number(item.id) === Number(activeLookupId.value || 0))
  if (!currentLookup) {
    ElMessage.warning('请先选择查表附录')
    return
  }
  try {
    await ElMessageBox.confirm(
      '确定删除当前附录吗？其明细和绑定关系会一起删除。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await deleteParameterLookup(currentLookup.id)
    lookupRows.value = []
    activeLookupId.value = 0
    lookupCurveProfile.value = normalizeParameterLookupCurveProfile({})
    await loadLookupItems()
    ElMessage.success('查表附录已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.detail || '删除查表附录失败')
    }
  }
}

const handleLookupAddRow = () => {
  const normalized = normalizeParameterLookupCurveProfile(lookupCurveProfile.value || {})
  if (normalized.table_columns.length) {
    lookupCurveProfile.value = {
      ...normalized,
      table_columns: [...normalized.table_columns],
      table_rows: [
        ...normalized.table_rows.map((row) => ({ ...row })),
        normalized.table_columns.reduce((accumulator, column) => {
          accumulator[column] = ''
          return accumulator
        }, {})
      ],
      series_columns: normalized.series_columns.map((item) => ({ ...item })),
      note_columns: [...normalized.note_columns]
    }
    return
  }

  const nextRows = [...lookupRows.value, { lookup_key: '', result_value: '', remark: '' }]
  lookupRows.value = nextRows
  lookupCurveProfile.value = normalizeParameterLookupCurveProfile(
    buildCurveProfileDraftFromImportPreview(
      { rows: nextRows },
      {
        profile_name: lookupCurveProfile.value?.profile_name || activeLookupName.value || '',
        series_columns: lookupCurveProfile.value?.series_columns || [],
        default_lookup_mode: lookupCurveProfile.value?.default_lookup_mode || 'LINEAR',
        allow_interpolation: lookupCurveProfile.value?.allow_interpolation !== false
      }
    )
  )
}

const handleLookupRemoveRow = (index) => {
  lookupRows.value = lookupRows.value.filter((_, rowIndex) => rowIndex !== index)
}

const applyLookupImportRows = async (payload = {}) => {
  const importedRows = Array.isArray(payload?.rows) ? payload.rows : []
  lookupRows.value = importedRows.map((item) => ({ ...item }))
  const nextCurveProfile = buildCurveProfileDraftFromImportPreview(payload, {
    profile_name: lookupCurveProfile.value?.profile_name || activeLookupName.value || '',
    series_columns: lookupCurveProfile.value?.series_columns || [],
    default_lookup_mode: lookupCurveProfile.value?.default_lookup_mode || 'LINEAR',
    allow_interpolation: lookupCurveProfile.value?.allow_interpolation !== false
  })
  if ((nextCurveProfile.table_columns || []).length) {
    lookupCurveProfile.value = normalizeParameterLookupCurveProfile(nextCurveProfile)
  }
  ElMessage.success(`已导入 ${lookupRows.value.length} 行附录预览数据`)
}

const handleLookupRowSave = async () => {
  if (!activeLookupId.value) {
    ElMessage.warning('请先选择查表附录')
    return
  }
  try {
    const nextProfile = normalizeParameterLookupCurveProfile(lookupCurveProfile.value || {})
    lookupCurveProfile.value = await saveParameterLookupCurveProfile(activeLookupId.value, nextProfile)
    lookupRows.value = await fetchParameterLookupRows(activeLookupId.value)
    ElMessage.success('附录图表已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.detail || '保存附录图表失败')
  }
}

const handleLookupCurveProfileSave = async (form = {}) => {
  if (!activeLookupId.value) {
    ElMessage.warning('请先选择查表附录')
    return
  }
  lookupCurveSaving.value = true
  try {
    lookupCurveProfile.value = await saveParameterLookupCurveProfile(activeLookupId.value, form)
    ElMessage.success('曲线配置已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.detail || '保存曲线配置失败')
  } finally {
    lookupCurveSaving.value = false
  }
}

const confirmDeleteParameter = async (row) => {
  try {
    await ElMessageBox.confirm(
      '确定删除当前参数及其全部型号值吗？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await deleteParameterDefinition(row.parameterId)
    await loadMatrix()
    ElMessage.success('参数已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.detail || '删除参数失败')
    }
  }
}

const saveVersion = async () => {
  if (!versionForm.value.family_id || !versionForm.value.version_code) {
    ElMessage.warning('请填写完整的型号信息')
    return
  }
  versionSaving.value = true
  try {
    await createFamilyVersion(versionForm.value.family_id, {
      version_code: versionForm.value.version_code,
      display_name: versionForm.value.display_name || versionForm.value.version_code
    })
    showVersionDialog.value = false
    versionForm.value = {
      family_id: null,
      version_code: '',
      display_name: ''
    }
    await loadMatrix()
    ElMessage.success('型号已新增')
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.detail || '新增型号失败')
  } finally {
    versionSaving.value = false
  }
}

const confirmDeleteVersion = async (version) => {
  try {
    await ElMessageBox.confirm(
      '确定删除当前型号及该列全部参数值吗？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await deleteVersionDefinition(version.id)
    await loadMatrix()
    ElMessage.success('型号已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.detail || '删除型号失败')
    }
  }
}

onMounted(async () => {
  try {
    await loadMatrix()
  } catch (e) {
    console.error('ParameterCenter loadMatrix failed', e)
  }
  try {
    await applyLookupFocusQuery()
  } catch (e) {
    console.error('ParameterCenter applyLookupFocusQuery failed', e)
  }
})

const renderTrendChart = async () => {
  if (activeTab.value !== 'matrix' || trendViewMode.value !== 'chart' || !trendRows.value.length) {
    return
  }
  await nextTick()
  if (!trendChartRef.value) return
  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChartRef.value)
  }
  trendChartInstance.setOption(
    {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        formatter: (params = []) => {
          const first = params[0]
          if (!first?.data) return ''
          const item = first.data.meta
          return [
            `${item.versionCode}`,
            `${item.capacityLabel}`,
            `${item.meaning}`,
            `${currentRow.value?.paramName || '参数'}: ${item.value || '未填写'} ${currentRow.value?.unitCode || ''}`,
            item.isAnomaly ? '<span style="color:#c45656">状态：异常</span>' : '状态：正常'
          ].join('<br/>')
        }
      },
      grid: { left: 56, right: 24, top: 24, bottom: 56 },
      xAxis: {
        type: 'category',
        axisLabel: {
          interval: 0,
          color: '#606266',
          formatter: (_value, index) => {
            const item = trendRows.value[index]
            return item ? `${item.capacityLabel}\n${item.versionCode}` : ''
          }
        },
        data: trendRows.value.map((item) => item.versionCode)
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#606266' },
        splitLine: { lineStyle: { color: '#ebeef5' } }
      },
      series: [
        {
          type: 'line',
          smooth: false,
          symbolSize: 10,
          lineStyle: { width: 2, color: '#409eff' },
          data: trendRows.value.map((item) => ({
            value: Number.isFinite(Number(item.value)) ? Number(item.value) : null,
            itemStyle: { color: item.isAnomaly ? '#f56c6c' : '#409eff' },
            meta: item
          }))
        }
      ]
    },
    true
  )
}

const resizeTrendChart = () => {
  trendChartInstance?.resize()
}

watch(
  activeTab,
  async (tab) => {
    if (tab !== 'lookup') {
      return
    }
    try {
      await ensureLookupPanelReady()
    } catch (e) {
      console.error('ParameterCenter ensureLookupPanelReady failed', e)
    }
  }
)

watch(activeProductCategory, () => {
  syncActiveFamily()
})

watch(
  () => trendRows.value,
  async () => {
    await renderTrendChart()
  },
  { deep: true }
)

watch(
  () => trendViewMode.value,
  async () => {
    await renderTrendChart()
  }
)

onMounted(() => {
  window.addEventListener('resize', resizeTrendChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeTrendChart)
  if (trendChartInstance) {
    trendChartInstance.dispose()
    trendChartInstance = null
  }
})

watch(
  () => route.query,
  async () => {
    await applyLookupFocusQuery()
  }
)
</script>

<style scoped>
.parameter-center {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar--structure {
  width: 100%;
  justify-content: flex-start;
}

.matrix-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: space-between;
  margin-bottom: 12px;
}

.matrix-toolbar__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.toolbar-tip {
  margin-left: auto;
  color: #64748b;
}

.toolbar-tip--family {
  margin-left: 0;
}

.drawer-footer,
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.matrix-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.matrix-header__main {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.matrix-header__meta {
  color: #606266;
  font-size: 12px;
  line-height: 1.2;
}

.matrix-header__meta--weak {
  color: #909399;
}

.matrix-readonly-value {
  display: inline-block;
  min-height: 20px;
  color: #1f2937;
}

.matrix-readonly-value--empty {
  color: #94a3b8;
}

.matrix-readonly-action {
  color: #64748b;
  font-size: 12px;
}

.trend-panel {
  margin-top: 12px;
}

.trend-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.trend-panel__title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.trend-panel__subtitle {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
}

.trend-panel__chart {
  width: 100%;
  height: 320px;
}

.trend-value--danger,
.trend-flag--danger {
  color: #f56c6c;
  font-weight: 600;
}
</style>
