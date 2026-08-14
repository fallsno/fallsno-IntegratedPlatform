import axios from 'axios'

/**
 * 计算链智能分析 API
 * 后端路由：/api/calculation-analysis/models/{model_id}/...
 */
export async function fetchAnalysisChain(modelId, payload) {
  const { data } = await axios.post(`/calculation-analysis/models/${modelId}/chain`, payload)
  return data
}

export async function fetchAnalysisScenarios(modelId, payload) {
  const { data } = await axios.post(`/calculation-analysis/models/${modelId}/scenarios`, payload)
  return data
}

export async function fetchAnalysisSensitivity(modelId, payload) {
  const { data } = await axios.post(`/calculation-analysis/models/${modelId}/sensitivity`, payload)
  return data
}

export async function fetchAnalysisCurve(modelId, payload) {
  const { data } = await axios.post(`/calculation-analysis/models/${modelId}/curve`, payload)
  return data
}

export async function fetchAnalysisSurface(modelId, payload) {
  const { data } = await axios.post(`/calculation-analysis/models/${modelId}/surface`, payload)
  return data
}
