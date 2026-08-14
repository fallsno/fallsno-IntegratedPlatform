import { parseCurveFormulaExpression } from './drumDesign.helpers.mjs'

export function buildLookupSourceRows({ activeFormula = {}, formulaResultMap = {}, lookupItems = [] } = {}) {
  const formulaName = String(activeFormula?.name || '').trim()
  if (!formulaName) {
    return []
  }
  const resultDetail = formulaResultMap?.[formulaName]?.lookupDetail || null
  const parsedCurve = parseCurveFormulaExpression(activeFormula?.expression || '')
  const lookupName = String(resultDetail?.lookup_name || parsedCurve?.lookupName || '').trim()
  if (!lookupName) {
    return []
  }
  const matchedLookup = (Array.isArray(lookupItems) ? lookupItems : []).find(
    (item) => String(item?.lookup_name || '').trim() === lookupName
  )
  const lookupType = String(resultDetail?.lookup_type || (parsedCurve ? 'curve' : 'lookup')).trim().toLowerCase()
  const seriesKey = String(resultDetail?.series_key || parsedCurve?.seriesKey || '').trim()
  const direction = String(resultDetail?.direction || parsedCurve?.direction || '').trim()
  const lookupMode = String(resultDetail?.lookup_mode || parsedCurve?.lookupMode || '').trim()
  const rangeText = lookupType === 'curve'
    ? [seriesKey, direction].filter(Boolean).join(' · ')
    : (resultDetail?.table_range || 'B:C')
  const detailText = lookupType === 'curve'
    ? [lookupMode || 'LINEAR', resultDetail?.hit_type === 'interpolated' ? '线性插值' : '命中点'].filter(Boolean).join(' · ')
    : [resultDetail?.lookup_key, resultDetail?.result_value].filter(Boolean).join(' -> ')

  return [{
    key: `${formulaName}:${lookupName}`,
    paramName: formulaName,
    lookupName,
    rangeText: rangeText || '-',
    detailText: detailText || '-',
    lookupId: Number(matchedLookup?.id || 0),
    jumpable: Number(matchedLookup?.id || 0) > 0,
    lookupDetail: resultDetail || {
      lookup_type: lookupType || 'lookup',
      lookup_name: lookupName,
      series_key: seriesKey,
      direction,
      lookup_mode: lookupMode
    }
  }]
}

export function buildLookupTargetQuery({ lookupDetail = {}, lookupItems = [], sourceFormulaName = '' } = {}) {
  const lookupName = String(lookupDetail?.lookup_name || '').trim()
  if (!lookupName) {
    return null
  }
  const matchedLookup = (Array.isArray(lookupItems) ? lookupItems : []).find(
    (item) => String(item?.lookup_name || '').trim() === lookupName
  )
  if (!matchedLookup?.id) {
    return null
  }
  return {
    tab: 'lookup',
    lookupId: String(matchedLookup.id),
    lookupName,
    seriesKey: String(lookupDetail?.series_key || '').trim(),
    fromFormula: String(sourceFormulaName || '').trim()
  }
}

export function resolveLookupFocusFromQuery(query = {}) {
  if (String(query?.tab || '') !== 'lookup') {
    return null
  }
  const lookupId = Number(query?.lookupId || 0)
  if (!lookupId) {
    return null
  }
  return {
    activeTab: 'lookup',
    lookupId,
    lookupName: String(query?.lookupName || '').trim(),
    seriesKey: String(query?.seriesKey || '').trim(),
    fromFormula: String(query?.fromFormula || '').trim()
  }
}
