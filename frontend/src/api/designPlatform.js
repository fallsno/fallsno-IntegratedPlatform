import axios from 'axios'

import {
  buildParameterCode,
  buildFamilyMatrixPayload,
  buildGuidanceActionUpdatePayload,
  buildParameterDistributionRows,
  buildTemplateSyncPayload,
  buildParameterQuery,
  buildWorkbenchSnapshotPayload,
  getGuidanceActionStatusMeta,
  mergeWorkbenchModelRows,
  normalizeGuidanceHit,
  normalizeParameterForm,
  normalizeParameterImportRows,
  normalizeParameterStats,
  normalizeGuidanceSummary,
  normalizeTemplateDiffStats
} from './designPlatform.helpers.mjs'
import {
  buildOrientationOptions,
  buildMatrixPreviewTableRows,
  normalizeMatrixPreview
} from './parameterMatrixImport.helpers.mjs'
import {
  buildLookupCurveChartOption,
  normalizeParameterLookupCurvePreview,
  normalizeParameterLookupCurveProfile,
  normalizeParameterLookupForm,
  normalizeParameterLookupPreview,
  normalizeParameterLookupRows
} from './parameterLookup.helpers.mjs'

export {
  buildParameterCode,
  buildFamilyMatrixPayload,
  buildGuidanceActionUpdatePayload,
  buildParameterDistributionRows,
  buildTemplateSyncPayload,
  buildParameterQuery,
  buildWorkbenchSnapshotPayload,
  getGuidanceActionStatusMeta,
  mergeWorkbenchModelRows,
  normalizeGuidanceHit,
  normalizeGuidanceSummary,
  normalizeParameterForm,
  normalizeParameterImportRows,
  normalizeParameterStats,
  normalizeTemplateDiffStats,
  buildOrientationOptions,
  buildMatrixPreviewTableRows,
  normalizeMatrixPreview,
  normalizeParameterLookupForm,
  normalizeParameterLookupCurvePreview,
  normalizeParameterLookupCurveProfile,
  buildLookupCurveChartOption,
  normalizeParameterLookupPreview,
  normalizeParameterLookupRows
}

export async function fetchParameters(filters = {}) {
  const { data } = await axios.get('/parameters/', { params: buildParameterQuery(filters) })
  return Array.isArray(data) ? data : []
}

export async function createParameter(form = {}) {
  const payload = normalizeParameterForm(form)
  const { data } = await axios.post('/parameters/', payload)
  return data
}

export async function updateParameter(parameterId, form = {}) {
  const payload = normalizeParameterForm(form)
  const { data } = await axios.put(`/parameters/${parameterId}`, payload)
  return data || null
}

export async function importParameters(rows = []) {
  const { data } = await axios.post('/parameters/import', { rows })
  return data || { created_count: 0, errors: [] }
}

export async function previewParameterMatrixImport(form = {}) {
  const { data } = await axios.post('/parameters/matrix-import/preview', form)
  return normalizeMatrixPreview(data || {})
}

export async function commitParameterMatrixImport(form = {}) {
  const { data } = await axios.post('/parameters/matrix-import/commit', form)
  return data || { imported_parameter_count: 0, saved_value_count: 0, warnings: [] }
}

export async function fetchParameterCenterMatrix(filters = {}) {
  const { data } = await axios.get('/parameters/matrix', { params: buildParameterQuery(filters) })
  return data || { versions: [], rows: [] }
}

export async function fetchParameterLookups() {
  const { data } = await axios.get('/parameter-lookups')
  return Array.isArray(data) ? data : []
}

export async function createParameterLookup(form = {}) {
  const { data } = await axios.post('/parameter-lookups', normalizeParameterLookupForm(form))
  return data || null
}

export async function updateParameterLookup(lookupId, form = {}) {
  const { data } = await axios.put(`/parameter-lookups/${lookupId}`, normalizeParameterLookupForm(form))
  return data || null
}

export async function deleteParameterLookup(lookupId) {
  const { data } = await axios.delete(`/parameter-lookups/${lookupId}`)
  return data || { lookup_id: Number(lookupId || 0), deleted: false }
}

export async function fetchParameterLookupRows(lookupId) {
  if (!lookupId) return []
  const { data } = await axios.get(`/parameter-lookups/${lookupId}/rows`)
  return Array.isArray(data) ? normalizeParameterLookupRows(data) : []
}

export async function saveParameterLookupRows(lookupId, rows = []) {
  const { data } = await axios.put(`/parameter-lookups/${lookupId}/rows`, {
    rows: normalizeParameterLookupRows(rows)
  })
  return data || { lookup_id: Number(lookupId || 0), saved_count: 0 }
}

export async function fetchParameterLookupCurveProfile(lookupId) {
  if (!lookupId) return normalizeParameterLookupCurveProfile({})
  const { data } = await axios.get(`/parameter-lookups/${lookupId}/curve-profile`)
  return normalizeParameterLookupCurveProfile(data || {})
}

export async function saveParameterLookupCurveProfile(lookupId, form = {}) {
  const { data } = await axios.put(
    `/parameter-lookups/${lookupId}/curve-profile`,
    normalizeParameterLookupCurveProfile(form)
  )
  return normalizeParameterLookupCurveProfile(data || {})
}

export async function fetchParameterLookupCurvePreview(lookupId) {
  if (!lookupId) return normalizeParameterLookupCurvePreview({})
  const { data } = await axios.get(`/parameter-lookups/${lookupId}/curve-preview`)
  return normalizeParameterLookupCurvePreview(data || {})
}

export async function previewParameterLookupImport(form = {}) {
  const { data } = await axios.post('/parameter-lookups/import/preview', form)
  return normalizeParameterLookupPreview(data || {})
}

export async function fetchParameterReferences(componentId) {
  if (!componentId) return []
  const { data } = await axios.get('/parameters/references', { params: { comp_id: componentId } })
  return Array.isArray(data) ? data : []
}

export async function fetchFamilyMatrix(familyId, moduleCode = '') {
  const { data } = await axios.get(`/model-parameters/families/${familyId}/matrix`, {
    params: moduleCode ? { module_code: moduleCode } : {}
  })
  return data || { family: null, versions: [], rows: [] }
}

export async function saveFamilyMatrix(familyId, rows = []) {
  const { data } = await axios.put(
    `/model-parameters/families/${familyId}/matrix`,
    buildFamilyMatrixPayload(rows)
  )
  return data || { family_id: Number(familyId || 0), saved_count: 0 }
}

export async function createWorkbenchSnapshots(runKey, rows = []) {
  const { data } = await axios.post(
    '/model-parameters/workbench/snapshots',
    buildWorkbenchSnapshotPayload(runKey, rows)
  )
  return data || { run_key: runKey, saved_count: 0 }
}

export async function saveWorkbenchParameters(form = {}) {
  const { data } = await axios.post('/model-parameters/workbench/parameters', form)
  return data || {
    family_id: Number(form.family_id || 0),
    saved_count: 0,
    created_parameter_count: 0
  }
}

export async function fetchLatestWorkbenchSnapshot(versionId) {
  if (!versionId) return { run_key: null, rows: [] }
  const { data } = await axios.get(`/model-parameters/workbench/snapshots/${versionId}/latest`)
  return data || { run_key: null, rows: [] }
}

export async function fetchParameterDistribution(parameterId, moduleCode = '') {
  if (!parameterId) return { parameter_id: 0, values: [] }
  const { data } = await axios.get(`/model-parameters/parameters/${parameterId}/distribution`, {
    params: moduleCode ? { module_code: moduleCode } : {}
  })
  return data || { parameter_id: Number(parameterId || 0), values: [] }
}

export async function deleteModelParameterValue(versionId, parameterId) {
  const { data } = await axios.delete(`/model-parameters/versions/${versionId}/parameters/${parameterId}`)
  return data || {
    version_id: Number(versionId || 0),
    parameter_id: Number(parameterId || 0),
    deleted: false
  }
}

export async function fetchParameterStats(parameterId) {
  const { data } = await axios.get(`/parameters/${parameterId}/stats`)
  return normalizeParameterStats(data || {})
}

export async function updateParameterDefaultValue(parameterId, form = {}) {
  const { data } = await axios.patch(`/parameters/${parameterId}/default`, form)
  return data || null
}

export async function deleteParameterDefinition(parameterId) {
  const { data } = await axios.delete(`/parameters/${parameterId}`)
  return data || { parameter_id: Number(parameterId || 0), deleted: false }
}

export async function createFamilyVersion(familyId, form = {}) {
  const { data } = await axios.post(`/families/${familyId}/versions`, form)
  return data || null
}

export async function deleteVersionDefinition(versionId) {
  const { data } = await axios.delete(`/versions/${versionId}`)
  return data || { message: '' }
}

export async function fetchSelectionMappings(modelId) {
  if (!modelId) return {}
  const { data } = await axios.get(`/workbench/models/${modelId}/selection-mappings`)
  const mappings = {}
  if (data && Array.isArray(data.data)) {
    data.data.forEach(item => {
      const categoryKey = String(item.target_category || 'gearmotor').trim() || 'gearmotor'
      if (!mappings[categoryKey]) {
        mappings[categoryKey] = {}
      }
      mappings[categoryKey][item.target_field] = item.source_parameter
    })
  }
  return mappings
}

export async function saveSelectionMappings(modelId, mappings = {}) {
  const payload = []
  const entries = Object.entries(mappings || {})
  const isLegacyFlatMapping = entries.every(([, value]) => typeof value === 'string')

  if (isLegacyFlatMapping) {
    entries.forEach(([field, param]) => {
      if (!field || !param) return
      payload.push({
        target_category: 'gearmotor',
        target_field: field,
        source_parameter: param
      })
    })
  } else {
    entries.forEach(([categoryKey, categoryMappings]) => {
      Object.entries(categoryMappings || {}).forEach(([field, param]) => {
        if (!field || !param) return
        payload.push({
          target_category: categoryKey,
          target_field: field,
          source_parameter: param
        })
      })
    })
  }

  const { data } = await axios.post(`/workbench/models/${modelId}/selection-mappings`, payload)
  return data || {}
}

export async function fetchFocusMetricConfigs(modelId) {
  if (!modelId) return {}
  const { data } = await axios.get(`/workbench/models/${modelId}/focus-metric-configs`)
  const configs = {}
  if (data && Array.isArray(data.data)) {
    data.data.forEach((item) => {
      const name = String(item.metric_name || '').trim()
      if (!name) return
      configs[name] = item.config || {}
    })
  }
  return configs
}

export async function saveFocusMetricConfigs(modelId, configs = {}) {
  if (!modelId) return {}
  const payload = { configs: [] }
  Object.entries(configs || {}).forEach(([metricName, config]) => {
    const name = String(metricName || '').trim()
    if (!name) return
    payload.configs.push({ metric_name: name, config: config || {} })
  })
  const { data } = await axios.put(`/workbench/models/${modelId}/focus-metric-configs`, payload)
  return data || {}
}

export async function fetchTemplates() {
  const { data } = await axios.get('/templates/')
  return Array.isArray(data) ? data : []
}

export async function fetchTemplateTree() {
  const { data } = await axios.get('/templates/tree')
  return Array.isArray(data) ? data : []
}

export async function fetchTemplateLinks(componentId) {
  if (!componentId) return []
  const { data } = await axios.get('/templates/links', { params: { component_id: componentId } })
  return Array.isArray(data) ? data : []
}

export async function fetchTemplateDiffPreview(sourceComponentId, targetComponentId) {
  const { data } = await axios.get('/templates/diff-preview', {
    params: {
      source_component_id: sourceComponentId,
      target_component_id: targetComponentId
    }
  })
  return normalizeTemplateDiffStats(data)
}

export async function executeTemplateSync(form = {}) {
  const { data } = await axios.post('/templates/execute-sync', buildTemplateSyncPayload(form))
  return {
    ...data,
    summary: normalizeTemplateDiffStats((data || {}).summary || {})
  }
}

export async function fetchGuidanceSummary() {
  const { data } = await axios.get('/guidance/summary')
  return {
    summary: normalizeGuidanceSummary((data || {}).summary || {}),
    hits: Array.isArray((data || {}).hits) ? data.hits.map((item) => normalizeGuidanceHit(item)) : []
  }
}

export async function generateGuidanceActions(hitId) {
  const { data } = await axios.post(`/guidance/hits/${hitId}/actions/generate`)
  return Array.isArray(data) ? data : []
}

export async function updateGuidanceAction(actionId, form = {}) {
  const { data } = await axios.patch(
    `/guidance/actions/${actionId}`,
    buildGuidanceActionUpdatePayload(form)
  )
  return data || null
}
