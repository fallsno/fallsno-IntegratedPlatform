import axios from 'axios'

import {
  buildCompareRouteQuery,
  buildImpactCompactCards,
  buildImpactDefaultSelection,
  buildImpactRangeRows,
  buildImpactSensitivityRows,
  buildImpactStateSummaryCards,
  buildImpactStateTableRows,
  buildImpactTrendSeries,
  buildFormulaSyncPreviewViewModel,
  extractFormulaParameterRows,
  filterImpactSamplesByMultiValues,
  filterImpactSamplesByRange,
  filterImpactSamplesBySingleValue,
  markWorkbenchParameterDirty,
  normalizeAnalysisSeries,
  normalizeCompareRows,
  normalizeDrumTree,
  normalizeFormulaImpactPayload,
  resolveImpactStateChartMode
} from './drumDesign.helpers.mjs'

export {
  buildCompareRouteQuery,
  buildImpactCompactCards,
  buildImpactDefaultSelection,
  buildImpactRangeRows,
  buildImpactSensitivityRows,
  buildImpactStateSummaryCards,
  buildImpactStateTableRows,
  buildImpactTrendSeries,
  extractFormulaParameterRows,
  filterImpactSamplesByMultiValues,
  filterImpactSamplesByRange,
  filterImpactSamplesBySingleValue,
  markWorkbenchParameterDirty,
  normalizeAnalysisSeries,
  normalizeCompareRows,
  normalizeDrumTree,
  normalizeFormulaImpactPayload,
  resolveImpactStateChartMode
}

export async function fetchDrumTree() {
  const { data } = await axios.get('/drum-catalog/tree')
  return normalizeDrumTree(Array.isArray(data) ? data : [])
}

export async function generateFamilyVersions(familyId) {
  const { data } = await axios.post(`/drum-catalog/families/${familyId}/generate-versions`)
  return data || { family_id: Number(familyId || 0), created_count: 0, versions: [] }
}

export async function executeDrumDesign(payload = {}) {
  const { data } = await axios.post('/drum-design/execute', payload)
  return data || { results: [], scope: {} }
}

export async function fetchModelWorkbenchInstance(modelId, parameters = {}, options = {}) {
  if (!modelId) {
    return {
      template_id: null,
      template_name: '',
      template_structure: { modules: [] },
      computed_results: {},
      latest_results: [],
      scope: {}
    }
  }

  const params = options.moduleCode ? { module_code: String(options.moduleCode) } : {}
  const hasOverrides = Object.keys(parameters || {}).length > 0
  const request = hasOverrides
    ? axios.post(`/workbench/models/${modelId}/execute`, { parameters }, { params })
    : axios.get(`/workbench/models/${modelId}/execute`, { params })
  const { data } = await request
  return data?.data || {
    template_id: null,
    template_name: '',
    template_structure: { modules: [] },
    computed_results: {},
    latest_results: [],
    scope: {}
  }
}

export async function fetchFormulaTemplates() {
  const { data } = await axios.get('/formula-templates/')
  return Array.isArray(data) ? data : []
}

export async function createFormulaTemplate(form = {}) {
  const { data } = await axios.post('/formula-templates/', form)
  return data || null
}

export async function fetchFormulaTemplateStructure(templateId) {
  if (!templateId) {
    return { modules: [] }
  }
  const { data } = await axios.get(`/formula-templates/${templateId}/structure`)
  return data || { modules: [] }
}

export async function saveFormulaTemplateStructure(templateId, payload = {}) {
  const { data } = await axios.put(`/formula-templates/${templateId}/structure`, payload)
  return data || { modules: [] }
}

export async function analyzeDrumDesign(payload = {}) {
  const { data } = await axios.post('/drum-design/analyze', payload)
  return normalizeAnalysisSeries(data || {})
}

export async function analyzeDrumDesignImpact(payload = {}) {
  const { data } = await axios.post('/drum-design/analyze-impact', payload)
  return data || { target_result_name: '', impacts: [] }
}

export async function compareDrumDesign(payload = {}) {
  const { data } = await axios.post('/drum-design/compare', payload)
  return normalizeCompareRows(Array.isArray(data?.rows) ? data.rows : [])
}

export async function fetchWorkbenchFormulas(modelId) {
  const { data } = await axios.get(`/drum-design/models/${modelId}/formulas`)
  return Array.isArray(data?.rows) ? data.rows : []
}

export async function fetchWorkbenchFormulaModules(modelId) {
  const { data } = await axios.get(`/drum-design/models/${modelId}/formula-modules`)
  return Array.isArray(data?.modules) ? data.modules : []
}

export async function fetchTypeModuleEntries(typeId, options = {}) {
  const params = {}
  if (options.versionId) {
    params.version_id = Number(options.versionId)
  }
  const { data } = await axios.get(`/drum-design/product-types/${typeId}/module-entries`, { params })
  return Array.isArray(data?.modules) ? data.modules : []
}

export async function createWorkbenchFormulaModule(modelId, form = {}) {
  const { data } = await axios.post(`/drum-design/models/${modelId}/formula-modules`, form)
  return data || null
}

export async function renameWorkbenchFormulaModule(modelId, moduleCode, form = {}) {
  const { data } = await axios.patch(`/drum-design/models/${modelId}/formula-modules/${moduleCode}`, form)
  return data || null
}

export async function createWorkbenchFormulaScene(modelId, form = {}) {
  const { data } = await axios.post(`/workbench/models/${modelId}/formula-scenes`, form)
  return data || null
}

export async function renameWorkbenchFormulaScene(modelId, moduleCode, sceneCode, form = {}) {
  const { data } = await axios.patch(
    `/workbench/models/${modelId}/formula-modules/${moduleCode}/formula-scenes/${sceneCode}`,
    form
  )
  return data || null
}

export async function deleteWorkbenchFormulaModule(modelId, moduleCode) {
  const { data } = await axios.delete(`/drum-design/models/${modelId}/formula-modules/${moduleCode}`)
  return data || {
    success: false,
    deleted_module_code: moduleCode,
    deleted_scene_count: 0,
    deleted_formula_count: 0
  }
}

export async function deleteWorkbenchFormulaScene(modelId, moduleCode, sceneCode) {
  const { data } = await axios.delete(
    `/workbench/models/${modelId}/formula-modules/${moduleCode}/formula-scenes/${sceneCode}`
  )
  return data || {
    success: false,
    deleted_module_code: moduleCode,
    deleted_scene_code: sceneCode,
    deleted_formula_count: 0
  }
}

export async function saveWorkbenchFormula(modelId, form = {}) {
  const { data } = await axios.post(`/workbench/models/${modelId}/formulas`, form)
  return data || null
}

export async function deleteWorkbenchFormula(modelId, formulaId) {
  const { data } = await axios.delete(`/workbench/models/${modelId}/formulas/${formulaId}`)
  return data || { success: false, deleted_formula_id: Number(formulaId || 0) }
}

export async function deleteWorkbenchFormulasBatch(modelId, form = {}) {
  const { data } = await axios.post(`/drum-design/models/${modelId}/formulas/batch-delete`, form)
  return data || { success: false, deleted_count: 0, deleted_ids: [] }
}

export async function reorderWorkbenchFormulas(modelId, form = {}) {
  const { data } = await axios.post(`/drum-design/models/${modelId}/formulas/reorder`, form)
  return Array.isArray(data?.rows) ? data.rows : []
}

export async function analyzeVerificationScan(form = {}, config = {}) {
  const { data } = await axios.post('/drum-design/compare/verification-scan', form, {
    timeout: 20000,
    ...config
  })
  return data || {}
}

export async function getFormulaSyncTargets(modelId, params = {}) {
  const { data } = await axios.get(`/drum-design/models/${modelId}/formula-sync-targets`, { params })
  return data?.targets || []
}

export async function previewFormulaSync(modelId, moduleCode, targetVersionIds) {
  const { data } = await axios.post(`/drum-design/models/${modelId}/formula-modules/${moduleCode}/sync-preview`, {
    target_version_ids: Array.isArray(targetVersionIds) ? targetVersionIds : [targetVersionIds]
  })
  return data || null
}

export async function executeFormulaSync(modelId, moduleCode, payload) {
  const { data } = await axios.post(`/drum-design/models/${modelId}/formula-modules/${moduleCode}/sync`, payload)
  return data || null
}

export async function fetchFormulaParamMappings(modelId, moduleCode) {
  const { data } = await axios.get(`/drum-design/models/${modelId}/formula-modules/${moduleCode}/param-mappings`)
  return Array.isArray(data) ? data : []
}

export async function saveFormulaParamMappings(modelId, moduleCode, mappings) {
  const { data } = await axios.post(`/drum-design/models/${modelId}/formula-modules/${moduleCode}/param-mappings`, {
    mappings
  })
  return data || { success: false }
}

export async function fetchEquipmentRecommendations(categoryCode, matchProperty, targetValue) {
  try {
    const { data } = await axios.get('/equipment/items', {
      params: { category_code: categoryCode }
    })
    
    // 前端简单模拟匹配逻辑：找到属性值大于等于目标值的设备，按该属性升序排列
    const items = Array.isArray(data) ? data : []
    const targetNum = Number(targetValue)
    
    if (isNaN(targetNum)) return []
    
    const matched = items.filter(item => {
      const specVal = Number(item.specs?.[matchProperty])
      return !isNaN(specVal) && specVal >= targetNum
    }).sort((a, b) => {
      return Number(a.specs[matchProperty]) - Number(b.specs[matchProperty])
    })
    
    return matched.slice(0, 3) // 返回 Top 3
  } catch (error) {
    console.error('获取设备推荐失败:', error)
    return []
  }
}
