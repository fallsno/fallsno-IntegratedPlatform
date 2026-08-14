const HIGHLIGHT_RESULTS = ['推荐电机功率', '电机所需功率', '电流', '托轮摩擦力矩']
const HIGHLIGHT_PRIORITY = HIGHLIGHT_RESULTS.reduce((accumulator, name, index) => {
  accumulator[name] = index
  return accumulator
}, {})
const FORMULA_AUTOCOMPLETE_TRIGGER_PATTERN = /(?:^|[=+\-*/(),\s])([^=+\-*/(),\s]*)$/
const FORMULA_PARAMETER_ALIASES = {
  滚筒重量: ['筒体重量']
}
const COMMON_FORMULA_SHORTCUT_ITEMS = [
  { label: 'IF()', value: 'IF()', cursorOffset: -1 },
  { label: 'IFERROR()', value: 'IFERROR()', cursorOffset: -1 },
  { label: 'π', value: 'π' },
  { label: 'e', value: 'e' },
  { label: 'sin()', value: 'sin()', cursorOffset: -1 },
  { label: 'cos()', value: 'cos()', cursorOffset: -1 },
  { label: 'tan()', value: 'tan()', cursorOffset: -1 },
  { label: 'sqrt()', value: 'sqrt()', cursorOffset: -1 },
  { label: 'ln()', value: 'ln()', cursorOffset: -1 },
  { label: 'log()', value: 'log()', cursorOffset: -1 },
  { label: 'abs()', value: 'abs()', cursorOffset: -1 },
  { label: 'pow()', value: 'pow()', cursorOffset: -1 }
]
const FORMULA_FUNCTION_ITEMS = [
  { label: 'VLOOKUP()', value: 'VLOOKUP()', group: '函数', description: '从附录中按键值查结果' },
  { label: 'CURVE2D()', value: 'CURVE2D()', group: '函数', description: '按附录图表做曲线查值/插值' },
  { label: 'HLOOKUP()', value: 'HLOOKUP()', group: '函数', description: '从附录中按键值查结果' },
  { label: 'SELECT_EQUIP()', value: 'SELECT_EQUIP()', group: '函数', description: '根据计算结果自动匹配选型库' },
  { label: 'IF()', value: 'IF()', group: '函数', description: '按条件返回不同结果' },
  { label: 'IFERROR()', value: 'IFERROR()', group: '函数', description: '出错时返回兜底结果' }
]
const FORMULA_GROUP_ORDER = {
  函数: 0,
  基础参数: 1,
  中间参数: 2,
  查表附录: 3
}
const FUNCTION_ARGUMENT_HINTS = {
  VLOOKUP: [
    ['查找值', '这里填写查找值，例如 电机频率'],
    ['附录范围', '这里填写附录范围，例如 电机扭矩参数!B:C'],
    ['返回列', '这里填写返回列，当前首期只支持 2'],
    ['精确匹配', '这里填写精确匹配标记，当前首期只支持 0']
  ],
  CURVE2D: [
    ['曲线表', '这里填写曲线表名，例如 电机扭矩参数'],
    ['输入值', '这里填写当前公式使用的输入参数，例如 电机频率'],
    ['曲线系列', '这里填写曲线系列，例如 DRN'],
    ['查值方向', '这里填写 X2Y 或 Y2X'],
    ['查值方式', '这里填写 LINEAR']
  ],
  SELECT_EQUIP: [
    ['分类代码', '这里填写设备分类代码，例如 "motor"'],
    ['匹配属性', '这里填写要匹配的设备属性，例如 "power"'],
    ['目标值', '这里填写计算出的目标值，例如 所需功率']
  ],
  IF: [
    ['判断条件', '这里填写判断条件'],
    ['成立值', '这里填写条件成立时返回的值'],
    ['不成立值', '这里填写条件不成立时返回的值']
  ]
}
const CURVE_EXPRESSION_RE = /^=?\s*(?:(?<multiplier>[-+]?\d+(?:\.\d+)?)\s*\*\s*)?CURVE2D\((?<lookupName>[^,]+),(?<inputName>[^,]+),(?<seriesKey>[^,]+),(?<direction>[^,]+),(?<lookupMode>[^)]+)\)\s*$/i
const VLOOKUP_UPGRADE_RE = /^=?\s*(?:(?<multiplier>[-+]?\d+(?:\.\d+)?)\s*\*\s*)?VLOOKUP\((?<inputName>[^,]+),(?<lookupName>[^!]+)!B:C,2,0\)\s*$/i

export function normalizeDrumTree(rows = []) {
  return rows.map((type) => ({
    id: `type-${type.id}`,
    label: type.type_name || '',
    level: 'type',
    raw: type,
    children: (type.families || []).map((family) => ({
      id: `family-${family.id}`,
      label: family.family_code || family.family_name || '',
      level: 'family',
      raw: family,
      children: (family.versions || []).map((version) => ({
        id: `version-${version.id}`,
        label: version.version_code || version.display_name || '',
        level: 'version',
        raw: version,
        children: []
      }))
    }))
  }))
}

export function normalizeAnalysisSeries(payload = {}) {
  return {
    labels: Array.isArray(payload.x_axis) ? payload.x_axis.map((item) => String(item)) : [],
    values: Array.isArray(payload.values) ? payload.values.map((item) => Number(item || 0)) : [],
    resultName: payload.result_name || '',
    targetParameter: payload.target_parameter || ''
  }
}

function toFiniteNumber(value, fallback = null) {
  const parsed = Number.parseFloat(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function formatMetricText(value, unitCode = '') {
  const text = String(value ?? '').trim()
  if (!text) return '-'
  return unitCode ? `${text} ${unitCode}` : text
}

export function normalizeFormulaImpactPayload(payload = {}) {
  const samples = (Array.isArray(payload?.samples) ? payload.samples : []).map((sample) => ({
    parameter_value: String(sample?.parameter_value ?? ''),
    input_delta_percent: String(sample?.input_delta_percent ?? ''),
    results: (Array.isArray(sample?.results) ? sample.results : []).map((result) => ({
      result_name: String(result?.result_name ?? ''),
      baseline_value: String(result?.baseline_value ?? ''),
      current_value: String(result?.current_value ?? ''),
      delta_value: String(result?.delta_value ?? ''),
      delta_percent: String(result?.delta_percent ?? ''),
      unit_code: String(result?.unit_code ?? '')
    }))
  }))
  const legacyPoints = Array.isArray(payload?.impact_rows)
    ? payload.impact_rows.map((row) => ({
        parameter_value: String(row?.parameter_value ?? ''),
        results: [{
          result_name: String(payload?.result_name ?? ''),
          baseline_value: String(row?.baseline_value ?? row?.baseline ?? ''),
          current_value: String(row?.result_value ?? row?.current_value ?? ''),
          delta_value: '',
          delta_percent: '',
          unit_code: ''
        }]
      }))
    : []
  const normalizedSamples = samples.length ? samples : legacyPoints
  return {
    formula_name: String(payload?.formula_name ?? ''),
    target_parameter: String(payload?.target_parameter ?? ''),
    baseline_parameter_value: String(payload?.baseline_parameter_value ?? ''),
    impact_path: Array.isArray(payload?.impact_path) ? payload.impact_path : [],
    points: normalizedSamples.map((sample) => ({
      parameter_value: sample.parameter_value,
      input_delta_percent: sample.input_delta_percent,
      results: sample.results
    })),
    unit_code: String((payload?.result_summary || [])[0]?.unit_code ?? payload?.unit_code ?? ''),
    samples: normalizedSamples.map((sample) => ({
      parameter_value: String(sample?.parameter_value ?? ''),
      input_delta_percent: String(sample?.input_delta_percent ?? ''),
      results: (Array.isArray(sample?.results) ? sample.results : []).map((result) => ({
        result_name: String(result?.result_name ?? ''),
        baseline_value: String(result?.baseline_value ?? ''),
        current_value: String(result?.current_value ?? ''),
        delta_value: String(result?.delta_value ?? ''),
        delta_percent: String(result?.delta_percent ?? ''),
        unit_code: String(result?.unit_code ?? '')
      }))
    })),
    result_summary: (Array.isArray(payload?.result_summary) ? payload.result_summary : []).map((row) => ({
      result_name: String(row?.result_name ?? ''),
      baseline_value: String(row?.baseline_value ?? ''),
      min_value: String(row?.min_value ?? ''),
      max_value: String(row?.max_value ?? ''),
      trend: String(row?.trend ?? ''),
      sensitivity: String(row?.sensitivity ?? ''),
      impact_level: String(row?.impact_level ?? ''),
      unit_code: String(row?.unit_code ?? ''),
      sensitivity_number: toFiniteNumber(row?.sensitivity, 0)
    })),
    warnings: Array.isArray(payload?.warnings) ? payload.warnings : []
  }
}

export function buildImpactDefaultSelection(payload = {}, preferredName = '', limit = 3) {
  const ranked = [...(payload?.result_summary || [])]
    .sort((left, right) => Math.abs(right.sensitivity_number || 0) - Math.abs(left.sensitivity_number || 0))
    .map((item) => item.result_name)
    .filter(Boolean)
  const picked = ranked.slice(0, Math.max(Number(limit || 3), 1))
  const normalizedPreferred = String(preferredName || '').trim()
  if (normalizedPreferred && !picked.includes(normalizedPreferred) && ranked.includes(normalizedPreferred)) {
    picked.push(normalizedPreferred)
  }
  return [...new Set(picked)]
}

export function buildImpactTrendSeries(payload = {}, selectedNames = []) {
  const chosen = new Set(
    (Array.isArray(selectedNames) ? selectedNames : [])
      .map((item) => String(item || '').trim())
      .filter(Boolean)
  )
  return (payload?.result_summary || [])
    .filter((row) => chosen.has(row.result_name))
    .map((summary) => ({
      name: summary.result_name,
      unitCode: summary.unit_code,
      sensitivity: summary.sensitivity,
      data: (payload?.samples || [])
        .map((sample) => {
          const result = (sample.results || []).find((row) => row.result_name === summary.result_name)
          const xValue = toFiniteNumber(sample.parameter_value)
          const yValue = toFiniteNumber(result?.current_value)
          return Number.isFinite(xValue) && Number.isFinite(yValue) ? [xValue, yValue] : null
        })
        .filter(Boolean)
    }))
    .filter((item) => item.data.length)
}

export function buildImpactSensitivityRows(payload = {}) {
  return [...(payload?.result_summary || [])]
    .map((row) => ({
      resultName: row.result_name,
      sensitivity: Number(row.sensitivity_number || 0),
      sensitivityText: row.sensitivity || '-',
      impactLevel: row.impact_level || 'low'
    }))
    .sort((left, right) => Math.abs(right.sensitivity) - Math.abs(left.sensitivity))
}

export function buildImpactRangeRows(payload = {}) {
  return [...(payload?.result_summary || [])]
    .map((row) => {
      const min = toFiniteNumber(row.min_value)
      const max = toFiniteNumber(row.max_value)
      const baseline = toFiniteNumber(row.baseline_value)
      if (![min, max, baseline].every(Number.isFinite)) {
        return null
      }
      return {
        resultName: row.result_name,
        min,
        max,
        baseline,
        span: Number((max - min).toFixed(4)),
        unitCode: row.unit_code || ''
      }
    })
    .filter(Boolean)
    .sort((left, right) => right.span - left.span)
}

export function buildImpactCompactCards(payload = {}, selectedNames = []) {
  const chosen = new Set(
    (Array.isArray(selectedNames) ? selectedNames : [])
      .map((item) => String(item || '').trim())
      .filter(Boolean)
  )
  const trendLabelMap = {
    positive: '正相关',
    negative: '负相关',
    flat: '无影响'
  }
  return (payload?.result_summary || [])
    .filter((row) => chosen.size === 0 || chosen.has(row.result_name))
    .map((row) => ({
      resultName: row.result_name,
      baselineText: formatMetricText(row.baseline_value, row.unit_code),
      trendLabel: trendLabelMap[row.trend] || '波动',
      sensitivityText: row.sensitivity || '-',
      rangeText: `${row.min_value || '-'} - ${row.max_value || '-'}`,
      impactLevel: row.impact_level || 'low'
    }))
}

function normalizeStateNumber(value) {
  const parsed = Number.parseFloat(value)
  return Number.isFinite(parsed) ? parsed : null
}

function findNearestImpactSample(samples = [], targetValue) {
  const normalizedTarget = normalizeStateNumber(targetValue)
  if (!Number.isFinite(normalizedTarget)) {
    return null
  }
  return [...samples]
    .map((sample) => ({
      sample,
      distance: Math.abs((normalizeStateNumber(sample?.parameter_value) ?? Number.POSITIVE_INFINITY) - normalizedTarget)
    }))
    .filter((item) => Number.isFinite(item.distance))
    .sort((left, right) => left.distance - right.distance)[0]?.sample || null
}

export function filterImpactSamplesBySingleValue(payload = {}, value = '') {
  const matched = findNearestImpactSample(payload?.samples || [], value)
  return matched ? [matched] : []
}

export function filterImpactSamplesByMultiValues(payload = {}, values = []) {
  const samples = payload?.samples || []
  return (Array.isArray(values) ? values : [])
    .map((value) => findNearestImpactSample(samples, value))
    .filter(Boolean)
    .filter((sample, index, list) => list.findIndex((item) => item.parameter_value === sample.parameter_value) === index)
}

export function filterImpactSamplesByRange(payload = {}, range = {}) {
  const min = normalizeStateNumber(range?.min)
  const max = normalizeStateNumber(range?.max)
  if (!Number.isFinite(min) || !Number.isFinite(max) || min > max) {
    return []
  }
  return (payload?.samples || []).filter((sample) => {
    const value = normalizeStateNumber(sample?.parameter_value)
    return Number.isFinite(value) && value >= min && value <= max
  })
}

export function resolveImpactStateChartMode(samples = []) {
  const count = Array.isArray(samples) ? samples.length : 0
  if (count <= 0) return 'empty'
  if (count === 1) return 'single-bar'
  if (count <= 6) return 'grouped-bar'
  return 'heatmap'
}

export function buildImpactStateSummaryCards(samples = [], summaries = [], filter = {}) {
  if ((samples || []).length <= 1) {
    const sample = samples?.[0]
    return (sample?.results || []).slice(0, 6).map((row) => {
      const summary = (summaries || []).find((item) => item.result_name === row.result_name) || {}
      return {
        title: row.result_name,
        value: formatMetricText(row.current_value, row.unit_code),
        meta: `敏感度 ${summary.sensitivity || '-'}`
      }
    })
  }

  const count = String(samples.length)
  const values = samples.map((item) => item.parameter_value).join(' / ')
  const mostSensitive = [...(summaries || [])]
    .sort((left, right) => Math.abs(Number(right.sensitivity_number || 0)) - Math.abs(Number(left.sensitivity_number || 0)))[0]

  return [
    { title: '命中状态', value: count, meta: filter.filterType === 'range' ? '区间筛选' : '多值筛选' },
    { title: '筛选范围', value: values || '-', meta: '目标参数状态' },
    { title: '结果数量', value: String(samples[0]?.results?.length || 0), meta: '当前视图结果' },
    { title: '最高敏感', value: mostSensitive?.result_name || '-', meta: `敏感度 ${mostSensitive?.sensitivity || '-'}` }
  ]
}

export function buildImpactStateTableRows(samples = [], summaries = [], mode = 'single') {
  if (mode === 'single') {
    const summaryMap = new Map((summaries || []).map((item) => [item.result_name, item]))
    return (samples?.[0]?.results || []).map((row) => {
      const summary = summaryMap.get(row.result_name) || {}
      return {
        resultName: row.result_name,
        currentValue: row.current_value,
        baselineValue: row.baseline_value,
        deltaValue: row.delta_value,
        deltaPercent: row.delta_percent,
        unitCode: row.unit_code || '',
        sensitivity: summary.sensitivity || '-',
        impactLevel: summary.impact_level || 'low'
      }
    })
  }

  const resultMap = new Map()
  for (const sample of samples || []) {
    for (const row of sample.results || []) {
      if (!resultMap.has(row.result_name)) {
        resultMap.set(row.result_name, {
          resultName: row.result_name,
          minValue: row.current_value,
          maxValue: row.current_value,
          stateCount: 0
        })
      }
      const bucket = resultMap.get(row.result_name)
      bucket[`state_${sample.parameter_value}`] = row.current_value
      bucket.stateCount += 1
      const currentNumber = normalizeStateNumber(row.current_value)
      const minNumber = normalizeStateNumber(bucket.minValue)
      const maxNumber = normalizeStateNumber(bucket.maxValue)
      if (Number.isFinite(currentNumber) && Number.isFinite(minNumber) && currentNumber < minNumber) {
        bucket.minValue = row.current_value
      }
      if (Number.isFinite(currentNumber) && Number.isFinite(maxNumber) && currentNumber > maxNumber) {
        bucket.maxValue = row.current_value
      }
    }
  }
  return [...resultMap.values()]
}

export function normalizeCompareRows(rows = []) {
  return [...rows].sort((left, right) => {
    const leftRank = HIGHLIGHT_RESULTS.includes(left.result_name) ? 0 : 1
    const rightRank = HIGHLIGHT_RESULTS.includes(right.result_name) ? 0 : 1
    if (leftRank !== rightRank) {
      return leftRank - rightRank
    }
    if (leftRank === 0 && rightRank === 0) {
      return HIGHLIGHT_PRIORITY[left.result_name] - HIGHLIGHT_PRIORITY[right.result_name]
    }
    return String(left.result_name || '').localeCompare(String(right.result_name || ''), 'zh-CN')
  })
}

export function buildFormulaSyncPreviewViewModel(backendPreview = {}) {
  const sourceInfo = backendPreview.source_module || backendPreview.source || {}
  const sourceModuleName = sourceInfo.module_name || ''
  const formulaCount = Number(sourceInfo.formula_count || backendPreview.formula_count || 0)

  const directMappings = Array.isArray(backendPreview.mappings_to_confirm) ? backendPreview.mappings_to_confirm : []
  const directAutoMappings = Array.isArray(backendPreview.auto_mappings) ? backendPreview.auto_mappings : []
  const targets = Array.isArray(backendPreview.targets) ? backendPreview.targets : []
  const targetMissingMappings = targets.flatMap((target) => target.missing_mappings || [])
  const targetAutoMappings = targets.flatMap((target) => target.auto_mappings || [])
  const allMissingMappings = [...directMappings, ...targetMissingMappings]
  const allAutoMappings = [...directAutoMappings, ...targetAutoMappings]
  const autoMappedNames = new Set(
    allAutoMappings.map((item) => String(item?.source_param_name || '').trim()).filter(Boolean)
  )

  const uniqueMissingMappings = []
  const missingKeys = new Set()
  for (const m of allMissingMappings) {
    const isResolved = Boolean(m.is_resolved) || Boolean(m.mapped_target_parameter_id) || Boolean(m.target_parameter_id)
    if (isResolved || !m.source_param_name) {
      continue
    }
    if (!missingKeys.has(m.source_param_name)) {
      missingKeys.add(m.source_param_name)
      uniqueMissingMappings.push({
        sourceName: m.source_param_name,
        targetId: m.target_parameter_id || m.mapped_target_parameter_id || null,
        targetName: m.target_param_name || m.mapped_target_parameter_name || '',
        isResolved: false,
        isAutoMapped: false
      })
    }
  }

  const uniqueResolvedMappings = []
  const resolvedKeys = new Set()
  for (const m of [...allMissingMappings, ...allAutoMappings]) {
    const isResolved = Boolean(m.is_resolved) || Boolean(m.mapped_target_parameter_id) || Boolean(m.target_parameter_id)
    if (!isResolved || !m.source_param_name) {
      continue
    }
    if (!resolvedKeys.has(m.source_param_name)) {
      resolvedKeys.add(m.source_param_name)
      uniqueResolvedMappings.push({
        sourceName: m.source_param_name,
        targetId: m.target_parameter_id || m.mapped_target_parameter_id || null,
        targetName: m.target_param_name || m.mapped_target_parameter_name || '',
        isResolved: true,
        isAutoMapped: Boolean(m.auto_mapped) || autoMappedNames.has(String(m.source_param_name || '').trim())
      })
    }
  }

  const syncStatus = uniqueMissingMappings.length > 0 ? 'partial' : 'ready'
  const canSync = uniqueMissingMappings.length === 0
  
  return {
    sourceModuleName,
    formulaCount,
    syncStatus,
    canSync,
    unresolvedMappings: uniqueMissingMappings,
    resolvedMappings: uniqueResolvedMappings
  }
}

export function buildWorkbenchParameterRows(matrix = {}, versionId = null) {
  const normalizedVersionId = Number(versionId || 0)
  return (Array.isArray(matrix.rows) ? matrix.rows : []).map((row) => ({
    parameterId: Number(row.parameter_id || 0),
    paramCode: row.param_code || '',
    paramName: row.param_name || '',
    displayName: row.display_name || row.param_name || '',
    unitCode: row.unit_code || '',
    categoryCode: row.category_code || '',
    valueType: row.value_type || 'basic',
    value: normalizedVersionId ? String((row.values || {})[normalizedVersionId] ?? '') : '',
    description: row.description || '',
    remark: normalizedVersionId ? String((row.remarks || {})[normalizedVersionId] ?? row.remark ?? '') : String(row.remark ?? ''),
    dirty: false,
    source: 'matrix'
  }))
}

export function extractFormulaParameterRows(formula = {}, parameterRows = []) {
  const variableNames = new Set(Object.keys(formula?.variables || {}))
  return (Array.isArray(parameterRows) ? parameterRows : []).filter((row) => {
    return variableNames.has(row.paramName)
  })
}

export function buildVisibleWorkbenchBaseRows(formula = {}, parameterRows = []) {
  const variableNames = Object.keys(formula?.variables || {})
  const allRows = Array.isArray(parameterRows) ? parameterRows : []
  const baseRows = allRows.filter((row) => row?.source !== 'formula')
  const matchedRows = extractFormulaParameterRows(formula, baseRows).map((row) => ({
    ...row,
    isReferenced: true,
    pendingCreate: Number(row?.parameterId || 0) <= 0
  }))

  const existingNames = new Set(matchedRows.map((row) => String(row?.paramName || '').trim()).filter(Boolean))
  const missingRows = variableNames
    .filter((name) => name && !existingNames.has(name) && !allRows.some((row) => String(row?.paramName || '').trim() === name))
    .map((name) => ({
      parameterId: 0,
      paramCode: '',
      paramName: name,
      unitCode: '',
      value: '',
      dirty: false,
      source: 'missing',
      isReferenced: true,
      pendingCreate: true
    }))

  return [...matchedRows, ...missingRows].sort((left, right) =>
    String(left?.paramName || '').localeCompare(String(right?.paramName || ''), 'zh-CN')
  )
}

function isSameParameterRow(left = {}, right = {}) {
  const leftId = Number(left.parameterId || 0)
  const rightId = Number(right.parameterId || 0)
  if (leftId > 0 && rightId > 0) {
    return leftId === rightId
  }
  return String(left.paramName || '') === String(right.paramName || '')
}

export function updateWorkbenchParameterDraft(rows = [], targetRow, nextValue) {
  return (Array.isArray(rows) ? rows : []).map((row) => {
    if (!isSameParameterRow(row, targetRow)) {
      return row
    }
    return {
      ...row,
      value: String(nextValue ?? ''),
      dirty: true,
      source: 'draft'
    }
  })
}

export function markWorkbenchParameterDirty(rows = [], targetRow, nextValue) {
  return updateWorkbenchParameterDraft(rows, targetRow, nextValue)
}

export function splitFormulaParameterRows(formula = {}, parameterRows = []) {
  const matchedRows = extractFormulaParameterRows(formula, parameterRows)
  return {
    baseRows: matchedRows.filter((row) => row.source !== 'formula'),
    intermediateRows: matchedRows.filter((row) => row.source === 'formula')
  }
}

export function buildExecutionIntermediateRows({
  formulaRows = [],
  latestResults = [],
  latestScope = {}
} = {}) {
  const scope = latestScope || {}
  const resultMap = new Map()
  for (const row of Array.isArray(latestResults) ? latestResults : []) {
    const name = String(row?.source_formula || row?.result_name || '').trim()
    if (!name) {
      continue
    }
    resultMap.set(name, row)
  }

  const mergedRows = new Map()
  const upsertRow = ({ name = '', unitCode = '', sceneName = '', value = '', sourceFormula = '' } = {}) => {
    const paramName = String(name || '').trim()
    if (!paramName) {
      return
    }
    const scopeValue = scope?.[paramName]
    const hasScopeValue = scopeValue !== undefined && scopeValue !== null && String(scopeValue).trim() !== ''
    const resolvedValue = hasScopeValue ? String(scopeValue) : String(value ?? '').trim()
    mergedRows.set(paramName, {
      parameterId: 0,
      paramCode: paramName,
      paramName,
      displayName: paramName,
      unitCode: String(unitCode || '').trim(),
      value: resolvedValue,
      dirty: false,
      source: 'formula',
      sourceFormula: String(sourceFormula || paramName).trim() || paramName,
      sceneName: String(sceneName || '').trim(),
      status: resolvedValue ? '已计算' : '未计算'
    })
  }

  for (const row of Array.isArray(formulaRows) ? formulaRows : []) {
    upsertRow({
      name: row?.name,
      unitCode: row?.unit_code || row?.unitCode || '',
      sceneName: row?.scene_name || row?.sceneName || '',
      sourceFormula: row?.name
    })
  }

  for (const row of Array.isArray(latestResults) ? latestResults : []) {
    const name = String(row?.source_formula || row?.result_name || '').trim()
    if (mergedRows.has(name)) {
      continue
    }
    upsertRow({
      name,
      unitCode: row?.unit_code || '',
      sceneName: row?.scene_name || '',
      value: row?.result_value,
      sourceFormula: row?.source_formula || row?.result_name || ''
    })
  }

  return [...mergedRows.values()].sort((left, right) =>
    String(left?.paramName || '').localeCompare(String(right?.paramName || ''), 'zh-CN')
  )
}

function resolveFlowNodeId(nodeType = '', name = '') {
  return `${String(nodeType || '').trim()}:${String(name || '').trim()}`
}

const REFERENCE_PARAMETER_HINT_RE = /(系数|修正|附录|查表|经验|折减|裕量)/u

function buildFlowNodeLabel(name = '', value = '', unitCode = '', sceneName = '') {
  const title = String(name || '').trim()
  const metricText = formatMetricText(value, unitCode)
  const metaText = String(sceneName || '').trim()
  return [title, metricText === '-' ? '' : metricText, metaText].filter(Boolean).join('\n')
}

function buildWorkbenchParameterLookupMap(parameterRows = []) {
  const lookupMap = new Map()
  const register = (key = '', row = null) => {
    const normalizedKey = String(key || '').trim()
    if (!normalizedKey || lookupMap.has(normalizedKey) || !row) {
      return
    }
    lookupMap.set(normalizedKey, row)
  }

  for (const row of Array.isArray(parameterRows) ? parameterRows : []) {
    const paramName = String(row?.paramName || '').trim()
    const displayName = String(row?.displayName || '').trim()
    register(paramName, row)
    register(displayName, row)
    for (const alias of FORMULA_PARAMETER_ALIASES[paramName] || []) {
      register(alias, row)
    }
  }

  return lookupMap
}

function buildWorkbenchInputSourceLabel(semanticRole, parameterInfo) {
  if (semanticRole === 'reference') return '查表/经验依据'
  if (semanticRole === 'product') return '产品参数'
  if (semanticRole === 'environment') return '环境参数'
  return parameterInfo?.source === 'matrix' ? '基础参数' : (parameterInfo?.source || '基础参数')
}

function resolveSemanticInputRole(paramName = '', resultInfo = {}, parameterInfo = null) {
  const normalizedName = String(paramName || '').trim()
  if (resultInfo?.lookupDetail) {
    return 'reference'
  }
  if (parameterInfo?.valueType === 'environment') {
    return 'environment'
  }
  if (parameterInfo?.valueType === 'product') {
    return 'product'
  }
  return REFERENCE_PARAMETER_HINT_RE.test(normalizedName) ? 'reference' : 'base'
}

function buildFormulaUsageMaps(formulaRows = []) {
  const formulaNames = new Set(
    (Array.isArray(formulaRows) ? formulaRows : [])
      .map((row) => String(row?.name || '').trim())
      .filter(Boolean)
  )
  const upstreamFormulaMap = new Map()
  const downstreamCountMap = new Map()
  const directInputCountMap = new Map()

  for (const formulaName of formulaNames) {
    upstreamFormulaMap.set(formulaName, [])
    downstreamCountMap.set(formulaName, 0)
    directInputCountMap.set(formulaName, 0)
  }

  for (const row of Array.isArray(formulaRows) ? formulaRows : []) {
    const formulaName = String(row?.name || '').trim()
    if (!formulaName) continue

    for (const dependencyName of Object.keys(row?.variables || {})) {
      const normalizedDependency = String(dependencyName || '').trim()
      if (!normalizedDependency) continue
      if (formulaNames.has(normalizedDependency)) {
        upstreamFormulaMap.get(formulaName).push(normalizedDependency)
        downstreamCountMap.set(
          normalizedDependency,
          Number(downstreamCountMap.get(normalizedDependency) || 0) + 1
        )
      } else {
        directInputCountMap.set(
          formulaName,
          Number(directInputCountMap.get(formulaName) || 0) + 1
        )
      }
    }
  }

  return { upstreamFormulaMap, downstreamCountMap, directInputCountMap }
}

function resolveFormulaSemanticRole(formulaName = '', downstreamCountMap = new Map()) {
  return Number(downstreamCountMap.get(String(formulaName || '').trim()) || 0) > 0 ? 'intermediate' : 'result'
}

function resolveFormulaDefaultVisible(formulaName = '', usageMaps = {}, options = {}) {
  if (!options?.focusedFormulaName) {
    return true
  }
  const semanticRole = resolveFormulaSemanticRole(formulaName, usageMaps?.downstreamCountMap)
  if (semanticRole === 'result') {
    return true
  }
  return Number(usageMaps?.directInputCountMap?.get(String(formulaName || '').trim()) || 0) > 0
}

function buildChildrenMap(nodes = [], edges = []) {
  const childrenMap = new Map(nodes.map((node) => [node.id, []]))
  for (const edge of edges) {
    if (childrenMap.has(edge.source)) {
      childrenMap.get(edge.source).push(edge.target)
    }
  }
  return childrenMap
}

function buildReachableResultMap(nodes = [], childrenMap = new Map()) {
  const resultIds = nodes.filter((node) => node.layer === 'output').map((node) => node.id)
  const resultSet = new Set(resultIds)
  const memo = new Map()

  const visit = (nodeId, visitingSet = new Set()) => {
    if (memo.has(nodeId)) {
      return memo.get(nodeId)
    }
    // 增加环检测，避免无限递归 (Maximum call stack size exceeded)
    if (visitingSet.has(nodeId)) {
      return []
    }
    
    if (resultSet.has(nodeId)) {
      const ownResult = [nodeId]
      memo.set(nodeId, ownResult)
      return ownResult
    }

    visitingSet.add(nodeId)
    const resultIdsForNode = []
    const resultIdSet = new Set()
    for (const childId of childrenMap.get(nodeId) || []) {
      for (const resultId of visit(childId, visitingSet)) {
        if (resultIdSet.has(resultId)) {
          continue
        }
        resultIdSet.add(resultId)
        resultIdsForNode.push(resultId)
      }
    }
    visitingSet.delete(nodeId)
    
    memo.set(nodeId, resultIdsForNode)
    return resultIdsForNode
  }

  for (const node of nodes) {
    visit(node.id)
  }

  return {
    resultIds,
    reachableResultMap: memo
  }
}

function decorateWorkbenchFocusSemantics(nodes = [], edges = []) {
  const nodeMap = new Map(nodes.map((node) => [node.id, node]))
  const childrenMap = buildChildrenMap(nodes, edges)
  const { resultIds, reachableResultMap } = buildReachableResultMap(nodes, childrenMap)
  const primaryResultId = resultIds[0] || ''
  const primarySpine = new Set()
  let cursor = primaryResultId

  // 构建上游依赖映射（用于 depth 计算）
  const upstreamMap = new Map()
  nodes.forEach((node) => {
    upstreamMap.set(node.id, [])
  })
  edges.forEach((edge) => {
    if (upstreamMap.has(edge.target)) {
      upstreamMap.get(edge.target).push(edge.source)
    }
  })

  // 计算每个节点的 depth
  const depthMemo = new Map()
  const computeDepth = (id, visited = new Set()) => {
    if (depthMemo.has(id)) return depthMemo.get(id)
    if (visited.has(id)) return 0 // Prevent infinite recursion on cycle
    
    visited.add(id)
    const node = nodeMap.get(id)
    if (!node) {
      visited.delete(id)
      return 0
    }
    const parents = upstreamMap.get(id) || []
    if (!parents.length) {
      depthMemo.set(id, 0)
      visited.delete(id)
      return 0
    }
    const value = 1 + Math.max(...parents.map(p => computeDepth(p, visited)))
    depthMemo.set(id, value)
    visited.delete(id)
    return value
  }

  while (cursor && nodeMap.has(cursor)) {
    primarySpine.add(cursor)
    const parentNodes = (nodeMap.get(cursor)?.depsForFocus || [])
      .map((parentId) => nodeMap.get(parentId))
      .filter(Boolean)
      .sort((left, right) => {
        const rightReachableCount = (reachableResultMap.get(right.id) || []).length
        const leftReachableCount = (reachableResultMap.get(left.id) || []).length
        if (rightReachableCount !== leftReachableCount) {
          return rightReachableCount - leftReachableCount
        }
        return String(left.id || '').localeCompare(String(right.id || ''), 'zh-CN')
      })
    cursor = parentNodes[0]?.id || ''
  }

  return nodes.map((node) => {
    const resultKeys = reachableResultMap.get(node.id) || []
    return {
      ...node,
      resultKeys,
      isPrimaryResult: node.id === primaryResultId,
      isPrimarySpine: primarySpine.has(node.id),
      isShared: node.layer !== 'output' && resultKeys.length > 1,
      branchOwner: resultKeys.length === 1 ? resultKeys[0] : '',
      depth: computeDepth(node.id)
    }
  })
}

function resolveVisualBand(layer = '') {
  const normalizedLayer = String(layer || '').trim()
  if (normalizedLayer === 'input') return 'input'
  if (normalizedLayer === 'calculation') return 'calculation'
  if (normalizedLayer === 'output') return 'output'
  return 'unknown'
}

function resolveVisualCategory(nodeType = '', semanticRole = '') {
  const normalizedRole = String(semanticRole || '').trim()
  if (normalizedRole === 'base') return 'base'
  if (normalizedRole === 'reference') return 'reference'
  if (normalizedRole === 'intermediate') return 'intermediate'
  if (normalizedRole === 'result') return 'result'
  return String(nodeType || '').trim() || 'unknown'
}

function resolveLayoutGroup({ layer = '', sceneName = '', semanticRole = '' } = {}) {
  const normalizedLayer = String(layer || '').trim()
  const normalizedRole = String(semanticRole || '').trim()
  if (normalizedLayer === 'input') {
    return `input:${normalizedRole || 'default'}`
  }
  if (normalizedLayer === 'output') {
    return 'output:result'
  }
  return `scene:${String(sceneName || '').trim() || 'default'}`
}

function resolveNodeEmphasis(semanticRole = '') {
  const normalizedRole = String(semanticRole || '').trim()
  if (normalizedRole === 'result') return 'result'
  if (normalizedRole === 'reference') return 'reference'
  return 'default'
}

function resolveFlowDependencyLevel(name = '', formulaMap = new Map(), cache = new Map(), stack = new Set()) {
  const normalizedName = String(name || '').trim()
  if (!normalizedName) {
    return 1
  }
  if (cache.has(normalizedName)) {
    return cache.get(normalizedName)
  }
  if (stack.has(normalizedName)) {
    return 1
  }
  const formula = formulaMap.get(normalizedName)
  if (!formula) {
    cache.set(normalizedName, 1)
    return 1
  }
  stack.add(normalizedName)
  const dependencyLevels = Object.keys(formula?.variables || {})
    .filter((dependencyName) => formulaMap.has(String(dependencyName || '').trim()))
    .map((dependencyName) => resolveFlowDependencyLevel(dependencyName, formulaMap, cache, stack))
  stack.delete(normalizedName)
  const level = dependencyLevels.length ? Math.max(...dependencyLevels) + 1 : 1
  cache.set(normalizedName, level)
  return level
}

const WORKBENCH_PROCESS_STEP_TITLES = {
  input: '输入条件',
  storage_load: '载荷确定',
  friction_torque: '结构尺寸确认',
  speed: '转速确定',
  power: '功率校核',
  output: '结果输出'
}

const WORKBENCH_PROCESS_STEP_GOALS = {
  input: '确定设计输入参数和边界条件',
  storage_load: '确定系统载荷和关键受力结果',
  friction_torque: '确定结构尺寸相关的摩擦力矩结果',
  speed: '确定转速是否满足设计要求',
  power: '确定驱动功率并完成校核',
  output: '汇总最终设计输出'
}

const WORKBENCH_PARAMETER_SOURCE_LABELS = {
  matrix: '矩阵参数',
  model: '型号参数',
  snapshot: '快照参数',
  draft: '当前草稿',
  missing: '缺失参数'
}

function resolveWorkbenchProcessStepTitle(sceneCode = '', sceneName = '', index = 0) {
  const normalizedSceneCode = String(sceneCode || '').trim()
  return WORKBENCH_PROCESS_STEP_TITLES[normalizedSceneCode] || String(sceneName || '').trim() || `步骤 ${index + 1}`
}

function buildWorkbenchProcessParameterRows(variableNames = [], parameterRows = []) {
  return (Array.isArray(variableNames) ? variableNames : [])
    .map((name) => String(name || '').trim())
    .filter(Boolean)
    .map((paramName) => {
      const matched = (Array.isArray(parameterRows) ? parameterRows : []).find(
        (row) => String(row?.paramName || '').trim() === paramName
      )
      return {
        paramName,
        value: matched?.value || '',
        unitCode: matched?.unitCode || '',
        source: matched?.source || 'missing'
      }
    })
}

function resolveWorkbenchParameterSourceLabel(source = '') {
  const normalizedSource = String(source || '').trim()
  return WORKBENCH_PARAMETER_SOURCE_LABELS[normalizedSource] || normalizedSource || '未知来源'
}

function buildWorkbenchReasoningExplanation({
  nodeId = '',
  nodeType = '',
  purpose = '',
  parameterItems = [],
  derivation = '',
  impact = ''
} = {}) {
  return {
    nodeId: String(nodeId || ''),
    nodeType: String(nodeType || ''),
    purpose: String(purpose || ''),
    keyInputs: (Array.isArray(parameterItems) ? parameterItems : []).map((item) => ({
      paramName: String(item?.paramName || ''),
      value: String(item?.value || '') || '-',
      unit: String(item?.unitCode || ''),
      source: resolveWorkbenchParameterSourceLabel(item?.source || '')
    })),
    derivation: String(derivation || ''),
    impact: String(impact || '')
  }
}

function buildWorkbenchFormulaPurposeDraft(semanticRole = '') {
  return semanticRole === 'result' ? '用于输出当前公式结果' : '用于承接上游结果并继续计算'
}

function buildWorkbenchFormulaImpactDraft() {
  return '结果会继续给下游节点使用或直接输出'
}

function buildWorkbenchInputPurposeDraft(semanticRole = '') {
  return semanticRole === 'reference' ? '作为当前计算的外部依据' : '作为当前模块的输入参数'
}

function buildWorkbenchInputImpactDraft() {
  return '会影响当前链路里的相关公式和结果'
}

export function applyWorkbenchExplanationDraft(explanation = {}, draft = {}) {
  return {
    ...explanation,
    purpose: draft?.purpose ?? explanation?.purpose ?? '',
    impact: draft?.impact ?? explanation?.impact ?? ''
  }
}

function buildWorkbenchReasoningPanelContext({
  title = '',
  nodeType = '',
  explanation = null,
  summary = [],
  parameters = [],
  lookups = [],
  constraints = []
} = {}) {
  return {
    title: String(title || ''),
    nodeType: String(nodeType || ''),
    explanation: explanation || null,
    summary: Array.isArray(summary) ? summary : [],
    parameters: Array.isArray(parameters) ? parameters : [],
    lookups: Array.isArray(lookups) ? lookups : [],
    constraints: Array.isArray(constraints) ? constraints : []
  }
}

function buildWorkbenchProcessStepNodes({
  rows = [],
  parameterRows = [],
  latestResults = []
} = {}) {
  const nodes = []
  const edges = []
  const resultMap = buildFormulaResultMap(latestResults)
  const pushNode = (node = {}) => {
    if (!node?.id || nodes.some((item) => item.id === node.id)) {
      return
    }
    nodes.push(node)
  }
  const pushEdge = (source = '', target = '') => {
    if (!source || !target || edges.some((item) => item.source === source && item.target === target)) {
      return
    }
    edges.push({ source, target })
  }

  pushNode({
    id: 'step:input',
    name: '输入条件',
    title: '输入条件',
    nodeType: 'step',
    stepCode: 'input',
    summary: '承接型号、工况和基础输入',
    panelContext: buildWorkbenchReasoningPanelContext({
      title: '输入条件',
      nodeType: 'step',
      explanation: buildWorkbenchReasoningExplanation({
        nodeId: 'step:input',
        nodeType: 'step',
        purpose: WORKBENCH_PROCESS_STEP_GOALS.input,
        parameterItems: [],
        derivation: '承接型号、工况和基础输入，为后续各设计步骤提供统一起点',
        impact: '这些输入将进入后续载荷、结构和功率校核步骤'
      })
    }),
    x: 140,
    y: 300,
    symbolSize: 58,
    itemStyle: {
      color: '#dbeafe',
      borderColor: '#ffffff',
      borderWidth: 2,
      shadowBlur: 12,
      shadowColor: 'rgba(15, 23, 42, 0.12)'
    }
  })

  rows.forEach((row, index) => {
    const sceneCode = String(row?.scene_code || '').trim()
    const stepId = `step:${sceneCode}`
    const resultId = `result:${sceneCode}`
    const resultInfo = resultMap[String(row?.name || '').trim()] || {}
    const stepTitle = resolveWorkbenchProcessStepTitle(sceneCode, row?.scene_name || row?.sceneName || '', index)
    const parameterItems = buildWorkbenchProcessParameterRows(Object.keys(row?.variables || {}), parameterRows)
      .filter((item) => item.source !== 'missing')
    const resultText = formatMetricText(resultInfo.value || resultInfo.result_value || '', resultInfo.unitCode || row?.unit_code || '')
    const stepSummary = resultText === '-' ? '尚未完成当前步骤' : `当前结果 ${resultText}`
    const baseX = 320 + index * 280
    const nextRow = rows[index + 1]
    const nextStepTitle = nextRow
      ? resolveWorkbenchProcessStepTitle(String(nextRow?.scene_code || '').trim(), nextRow?.scene_name || nextRow?.sceneName || '', index + 1)
      : '结果输出'
    const stepGoal = WORKBENCH_PROCESS_STEP_GOALS[sceneCode] || `完成${stepTitle}相关设计推理`
    const stepNode = {
      id: stepId,
      name: stepTitle,
      title: stepTitle,
      nodeType: 'step',
      stepCode: sceneCode,
      summary: stepSummary,
      panelContext: buildWorkbenchReasoningPanelContext({
        title: stepTitle,
        nodeType: 'step',
        explanation: buildWorkbenchReasoningExplanation({
          nodeId: stepId,
          nodeType: 'step',
          purpose: stepGoal,
          parameterItems,
          derivation: resultText === '-'
            ? `结合${parameterItems.map((item) => item.paramName).join('、') || '当前步骤参数'}推导 ${row?.name || stepTitle}`
            : `结合${parameterItems.map((item) => item.paramName).join('、') || '当前步骤参数'}推导 ${row?.name || stepTitle}，当前结果为 ${resultText}`,
          impact: `${row?.name || stepTitle} 将作为 ${nextStepTitle} 的输入依据`
        })
      }),
      x: baseX,
      y: 300,
      symbolSize: 58,
      itemStyle: {
        color: '#dbeafe',
        borderColor: '#ffffff',
        borderWidth: 2,
        shadowBlur: 12,
        shadowColor: 'rgba(15, 23, 42, 0.12)'
      }
    }
    pushNode(stepNode)
    pushEdge(index === 0 ? 'step:input' : `step:${rows[index - 1]?.scene_code || ''}`, stepId)

    pushNode({
      id: resultId,
      name: String(row?.name || '').trim() || `${stepTitle}结果`,
      title: String(row?.name || '').trim() || `${stepTitle}结果`,
      nodeType: 'result_anchor',
      stepCode: sceneCode,
      summary: resultText === '-' ? '结果待产出' : `锚点结果 ${resultText}`,
      value: String(resultInfo.value || resultInfo.result_value || ''),
      unitCode: String(resultInfo.unitCode || row?.unit_code || ''),
      panelContext: buildWorkbenchReasoningPanelContext({
        title: String(row?.name || '').trim() || `${stepTitle}结果`,
        nodeType: 'result_anchor',
        explanation: buildWorkbenchReasoningExplanation({
          nodeId: resultId,
          nodeType: 'result_anchor',
          purpose: '固定当前步骤的核心结果，作为设计链路中的结果锚点',
          parameterItems,
          derivation: resultText === '-'
            ? `该结果由 ${stepTitle} 步骤推导得到，当前尚未产出实际值`
            : `该结果由 ${stepTitle} 步骤推导得到，当前值为 ${resultText}`,
          impact: `${String(row?.name || '').trim() || stepTitle} 将被后续步骤继续引用`
        })
      }),
      x: baseX,
      y: 220,
      symbolSize: 50,
      itemStyle: {
        color: '#fde2e4',
        borderColor: '#ffffff',
        borderWidth: 2,
        shadowBlur: 12,
        shadowColor: 'rgba(15, 23, 42, 0.12)'
      }
    })
    pushEdge(stepId, resultId)

    const pushParameterNodes = () => {
      parameterItems.forEach((item, paramIndex) => {
        const paramId = `param:${sceneCode}:${item.paramName}`
        pushNode({
          id: paramId,
          name: item.paramName,
          title: item.paramName,
          nodeType: 'parameter',
          stepCode: sceneCode,
          summary: formatMetricText(item.value, item.unitCode),
          panelContext: buildWorkbenchReasoningPanelContext({
            title: item.paramName,
            nodeType: 'parameter',
            explanation: buildWorkbenchReasoningExplanation({
              nodeId: paramId,
              nodeType: 'parameter',
              purpose: `${item.paramName} 是 ${stepTitle} 需要关注的关键输入参数`,
              parameterItems: [item],
              derivation: `${item.paramName} 以 ${resolveWorkbenchParameterSourceLabel(item.source)} 形式进入当前步骤计算`,
              impact: `${item.paramName} 的变化会直接影响 ${String(row?.name || '').trim() || stepTitle} 的结果`
            })
          }),
          x: baseX - 90 + paramIndex * 90,
          y: 430,
          symbolSize: 34,
          itemStyle: {
            color: '#dbeafe',
            borderColor: '#ffffff',
            borderWidth: 1,
            shadowBlur: 8,
            shadowColor: 'rgba(15, 23, 42, 0.08)'
          }
        })
        pushEdge(paramId, stepId)
      })
    }

    if (sceneCode === 'power') {
      pushNode({
        id: 'rule:power:pass',
        name: '是否满足校核条件',
        title: '是否满足校核条件',
        nodeType: 'rule',
        stepCode: sceneCode,
        summary: resultText === '-' ? '待判断' : '当前校核通过',
        panelContext: buildWorkbenchReasoningPanelContext({
          title: '是否满足校核条件',
          nodeType: 'rule',
          explanation: buildWorkbenchReasoningExplanation({
            nodeId: 'rule:power:pass',
            nodeType: 'rule',
            purpose: '将功率校核规则直接嵌入链路，判断当前结果是否可进入下一步',
            parameterItems,
            derivation: '对推荐电机功率执行标准值比对和规则判断',
            impact: resultText === '-' ? '待规则判断完成后才能给出最终结论' : '规则通过后保留当前功率建议并进入结果输出'
          })
        }),
        x: baseX + 80,
        y: 150,
        symbolSize: 42,
        symbol: 'diamond',
        itemStyle: {
          color: '#fee2e2',
          borderColor: '#ffffff',
          borderWidth: 2,
          shadowBlur: 12,
          shadowColor: 'rgba(15, 23, 42, 0.12)'
        }
      })
      pushEdge(resultId, 'rule:power:pass')
      pushParameterNodes()
      return
    }

    pushParameterNodes()
  })

  return { nodes, edges }
}

export function buildWorkbenchProcessFlowGraph({
  moduleCode = '',
  formulaRows = [],
  parameterRows = [],
  latestResults = []
} = {}) {
  const normalizedModuleCode = String(moduleCode || '').trim()
  const rows = (Array.isArray(formulaRows) ? formulaRows : [])
    .filter((row) => !normalizedModuleCode || String(row?.module_code || '').trim() === normalizedModuleCode)
    .slice()
    .sort((left, right) => {
      const orderDiff = Number(left?.sort_order || 0) - Number(right?.sort_order || 0)
      if (orderDiff !== 0) {
        return orderDiff
      }
      return Number(left?.id || 0) - Number(right?.id || 0)
    })

  if (!rows.length) {
    return {
      nodes: [],
      edges: [],
      stepCount: 0,
      resultCount: 0,
      ruleCount: 0,
      paramCount: 0,
      queryCount: 0,
      decisionCount: 0
    }
  }

  const graph = buildWorkbenchProcessStepNodes({
    rows,
    parameterRows,
    latestResults
  })

  return {
    ...graph,
    stepCount: graph.nodes.filter((item) => item.nodeType === 'step').length,
    resultCount: graph.nodes.filter((item) => item.nodeType === 'result_anchor').length,
    ruleCount: graph.nodes.filter((item) => item.nodeType === 'rule').length,
    paramCount: graph.nodes.filter((item) => item.nodeType === 'parameter').length,
    queryCount: 0,
    decisionCount: 0
  }
}

export function resolveWorkbenchProcessSelectedNode(graph = {}, nodeId = '') {
  const matchedNode = (Array.isArray(graph?.nodes) ? graph.nodes : []).find(
    (node) => String(node?.id || '') === String(nodeId || '')
  )
  if (!matchedNode) {
    return null
  }
  return {
    nodeId: String(matchedNode.id || ''),
    nodeType: String(matchedNode.nodeType || ''),
    title: String(matchedNode.title || matchedNode.name || ''),
    summary: String(matchedNode.summary || ''),
    stepCode: String(matchedNode.stepCode || '')
  }
}

export function buildWorkbenchProcessPanelContext(graph = {}, nodeId = '') {
  const matchedNode = (Array.isArray(graph?.nodes) ? graph.nodes : []).find(
    (node) => String(node?.id || '') === String(nodeId || '')
  )
  if (!matchedNode?.panelContext) {
    return {
      title: '',
      nodeType: '',
      explanation: null,
      summary: [],
      parameters: [],
      lookups: [],
      constraints: []
    }
  }
  return {
    title: String(matchedNode.title || matchedNode.name || ''),
    nodeType: String(matchedNode.nodeType || ''),
    explanation: matchedNode.panelContext.explanation || null,
    summary: Array.isArray(matchedNode.panelContext.summary) ? matchedNode.panelContext.summary : [],
    parameters: Array.isArray(matchedNode.panelContext.parameters) ? matchedNode.panelContext.parameters : [],
    lookups: Array.isArray(matchedNode.panelContext.lookups) ? matchedNode.panelContext.lookups : [],
    constraints: Array.isArray(matchedNode.panelContext.constraints) ? matchedNode.panelContext.constraints : []
  }
}

export function buildWorkbenchCalculationPanelContext(graph = {}, nodeId = '') {
  const matchedNode = (Array.isArray(graph?.nodes) ? graph.nodes : []).find(
    (node) => String(node?.id || '') === String(nodeId || '')
  )
  if (!matchedNode?.panelContext) {
    return {
      title: '',
      nodeType: '',
      explanation: null,
      summary: [],
      parameters: [],
      lookups: [],
      constraints: []
    }
  }
  return {
    title: String(matchedNode.title || matchedNode.name || ''),
    nodeType: String(matchedNode.nodeType || ''),
    explanation: matchedNode.panelContext.explanation || null,
    summary: Array.isArray(matchedNode.panelContext.summary) ? matchedNode.panelContext.summary : [],
    parameters: Array.isArray(matchedNode.panelContext.parameters) ? matchedNode.panelContext.parameters : [],
    lookups: Array.isArray(matchedNode.panelContext.lookups) ? matchedNode.panelContext.lookups : [],
    constraints: Array.isArray(matchedNode.panelContext.constraints) ? matchedNode.panelContext.constraints : []
  }
}

export function buildWorkbenchCalculationFlow({
  moduleCode = '',
  focusedFormulaName = '',
  formulaRows = [],
  parameterRows = [],
  latestResults = [],
  latestScope = {}
} = {}) {
  const normalizedModuleCode = String(moduleCode || '').trim()
  let filteredFormulas = (Array.isArray(formulaRows) ? formulaRows : [])
    .filter((row) => !normalizedModuleCode || String(row?.module_code || row?.moduleCode || '').trim() === normalizedModuleCode)
    .slice()
    .sort((left, right) => compareFormulaRows(left, right))

  if (!filteredFormulas.length) {
    return {
      nodes: [],
      edges: [],
      sceneCount: 0,
      formulaCount: 0,
      dependencyCount: 0,
      inputCount: 0
    }
  }

  const resultMap = buildFormulaResultMap(latestResults)
  const baseParameterMap = buildWorkbenchParameterLookupMap(parameterRows)
  const formulaMap = new Map(filteredFormulas.map((row) => [String(row?.name || '').trim(), row]))
  const normalizedFocusedFormulaName = String(focusedFormulaName || '').trim()
  const hasFocusedFormula = Boolean(normalizedFocusedFormulaName && formulaMap.has(normalizedFocusedFormulaName))
  if (normalizedFocusedFormulaName && formulaMap.has(normalizedFocusedFormulaName)) {
    const reachableFormulaNames = new Set()
    const walkUpstreamFormulas = (formulaName) => {
      const normalizedFormulaName = String(formulaName || '').trim()
      if (!normalizedFormulaName || reachableFormulaNames.has(normalizedFormulaName)) {
        return
      }
      const formula = formulaMap.get(normalizedFormulaName)
      if (!formula) {
        return
      }
      reachableFormulaNames.add(normalizedFormulaName)
      Object.keys(formula?.variables || {}).forEach((dependencyName) => {
        const normalizedDependencyName = String(dependencyName || '').trim()
        if (formulaMap.has(normalizedDependencyName)) {
          walkUpstreamFormulas(normalizedDependencyName)
        }
      })
    }

    walkUpstreamFormulas(normalizedFocusedFormulaName)
    if (reachableFormulaNames.size) {
      filteredFormulas = filteredFormulas.filter((row) =>
        reachableFormulaNames.has(String(row?.name || '').trim())
      )
    }
  }

  if (!filteredFormulas.length) {
    return {
      nodes: [],
      edges: [],
      sceneCount: 0,
      formulaCount: 0,
      dependencyCount: 0,
      inputCount: 0
    }
  }

  const scopedFormulaMap = new Map(filteredFormulas.map((row) => [String(row?.name || '').trim(), row]))
  const usageMaps = buildFormulaUsageMaps(filteredFormulas)
  const levelCache = new Map()
  const sceneOrderMap = new Map()
  let sceneOrder = 0
  for (const row of filteredFormulas) {
    const sceneCode = String(row?.scene_code || '').trim()
    if (!sceneCode || sceneOrderMap.has(sceneCode)) {
      continue
    }
    sceneOrderMap.set(sceneCode, sceneOrder)
    sceneOrder += 1
  }

  const nodeMap = new Map()
  const edgeMap = new Map()
  const inputNames = new Set()

  const ensureNode = ({
    id = '',
    name = '',
    title = '',
    nodeType = 'input',
    value = '',
    unitCode = '',
    sceneName = '',
    level = 0,
    order = 0,
    color = '#94a3b8',
    formulaKey = '',
    formulaRow = null,
    semanticRole = '',
    layer = '',
    defaultVisible = true,
    isMainline = true,
    depsForFocus = [],
    panelContext = null,
    lineageIncomplete = false,
    missingDependencies = []
  } = {}) => {
    if (!id || nodeMap.has(id)) {
      return
    }
    nodeMap.set(id, {
      id,
      name,
      title: String(title || name || '').trim(),
      value: String(value ?? '').trim(),
      unitCode: String(unitCode || '').trim(),
      sceneName: String(sceneName || '').trim(),
      nodeType,
      formulaKey: String(formulaKey || '').trim(),
      formulaRow,
      semanticRole: String(semanticRole || '').trim(),
      layer: String(layer || '').trim(),
      visualBand: resolveVisualBand(layer),
      visualCategory: resolveVisualCategory(nodeType, semanticRole),
      layoutGroup: resolveLayoutGroup({ layer, sceneName, semanticRole }),
      emphasis: resolveNodeEmphasis(semanticRole),
      defaultVisible: defaultVisible !== false,
      isMainline: isMainline !== false,
      depsForFocus: Array.isArray(depsForFocus) ? depsForFocus : [],
      lineageIncomplete: Boolean(lineageIncomplete),
      missingDependencies: Array.isArray(missingDependencies) ? missingDependencies : [],
      group: String(formulaRow?.scene_code || '').trim(),
      groupTitle: String(sceneName || '').trim(),
      panelContext,
      category: nodeType,
      symbolSize: nodeType === 'formula' ? 76 : 56,
      draggable: false,
      label: {
        show: true,
        formatter: buildFlowNodeLabel(title || name, value, unitCode, sceneName),
        fontSize: 12,
        lineHeight: 16,
        color: '#0f172a'
      },
      itemStyle: {
        color,
        borderColor: '#ffffff',
        borderWidth: 2,
        shadowBlur: 12,
        shadowColor: 'rgba(15, 23, 42, 0.12)'
      },
      x: 120 + level * 240,
      y: 80 + order * 108
    })
  }

  const ensureEdge = (source = '', target = '', label = '') => {
    const edgeKey = `${source}->${target}`
    if (!source || !target || edgeMap.has(edgeKey)) {
      return
    }
    edgeMap.set(edgeKey, {
      source,
      target,
      value: String(label || '').trim(),
      lineStyle: {
        color: '#94a3b8',
        width: 2,
        curveness: 0.08,
        opacity: 0.9
      },
      label: {
        show: Boolean(label),
        formatter: String(label || '').trim(),
        color: '#64748b',
        fontSize: 11
      }
    })
  }

  filteredFormulas.forEach((row, index) => {
    const formulaName = String(row?.name || '').trim()
    const resultInfo = resultMap[formulaName] || {}
    const sceneCode = String(row?.scene_code || '').trim()
    const dependencyNames = Object.keys(row?.variables || {})
      .map((item) => String(item || '').trim())
      .filter(Boolean)
    const missingDependencies = dependencyNames.filter((dependencyName) => {
      return !scopedFormulaMap.has(dependencyName) && !baseParameterMap.has(dependencyName) && !resultMap[dependencyName]
    })
    const sceneIndex = sceneOrderMap.get(sceneCode) ?? 0
    const level = resolveFlowDependencyLevel(formulaName, scopedFormulaMap, levelCache)
    const semanticRole = resolveFormulaSemanticRole(formulaName, usageMaps.downstreamCountMap)
    const layer = semanticRole === 'result' ? 'output' : 'calculation'
    const parameterItems = buildWorkbenchProcessParameterRows(Object.keys(row?.variables || {}), parameterRows)
    const explanationPurpose = buildWorkbenchFormulaPurposeDraft(semanticRole)
    const impactText = buildWorkbenchFormulaImpactDraft(semanticRole)
    ensureNode({
      id: resolveFlowNodeId('formula', formulaName),
      name: formulaName,
      title: formulaName,
      nodeType: 'formula',
      value: resultInfo.value || latestScope?.[formulaName] || '',
      unitCode: resultInfo.unitCode || row?.unit_code || row?.unitCode || '',
      sceneName: row?.scene_name || row?.sceneName || '',
      level,
      order: sceneIndex * 6 + index,
      color: '#dbeafe',
      formulaKey: row?._rowKey || '',
      formulaRow: row,
      semanticRole,
      layer,
      defaultVisible: resolveFormulaDefaultVisible(formulaName, usageMaps, { focusedFormulaName: hasFocusedFormula ? normalizedFocusedFormulaName : '' }),
      isMainline: resolveFormulaDefaultVisible(formulaName, usageMaps, { focusedFormulaName: hasFocusedFormula ? normalizedFocusedFormulaName : '' }),
      depsForFocus: dependencyNames.filter((dependencyName) => scopedFormulaMap.has(dependencyName)).map((dependencyName) =>
        resolveFlowNodeId('formula', dependencyName)
      ),
      lineageIncomplete: missingDependencies.length > 0,
      missingDependencies,
      panelContext: buildWorkbenchReasoningPanelContext({
        title: formulaName,
        nodeType: 'formula',
        explanation: buildWorkbenchReasoningExplanation({
          nodeId: resolveFlowNodeId('formula', formulaName),
          nodeType: 'formula',
          purpose: explanationPurpose,
          parameterItems: parameterItems.map((item) => ({
            ...item,
            source: formulaMap.has(item.paramName) ? '模块内中间变量' : item.source
          })),
          derivation: String(row?.expression || '').trim() || `由 ${Object.keys(row?.variables || {}).join('、')} 推导`,
          impact: impactText
        })
      })
    })
  })

  filteredFormulas.forEach((row, index) => {
    const formulaName = String(row?.name || '').trim()
    const targetId = resolveFlowNodeId('formula', formulaName)
    const dependencies = Object.keys(row?.variables || {})
      .map((item) => String(item || '').trim())
      .filter(Boolean)

    dependencies.forEach((dependencyName, dependencyIndex) => {
      if (scopedFormulaMap.has(dependencyName)) {
        ensureEdge(resolveFlowNodeId('formula', dependencyName), targetId, dependencyName)
        return
      }

      const resultInfo = resultMap[dependencyName] || {}
      const parameterInfo = baseParameterMap.get(dependencyName) || {}
      const displayName = String(parameterInfo?.displayName || dependencyName).trim() || dependencyName
      const isLookupNode = Boolean(resultInfo.lookupDetail)
      const sourceType = isLookupNode ? 'lookup' : 'input'
      const sourceId = resolveFlowNodeId(sourceType, dependencyName)
      if (!isLookupNode) {
        inputNames.add(dependencyName)
      }
      ensureNode({
        id: sourceId,
        name: dependencyName,
        title: displayName,
        nodeType: sourceType,
        value: resultInfo.value || latestScope?.[dependencyName] || parameterInfo?.value || '',
        unitCode: resultInfo.unitCode || parameterInfo?.unitCode || '',
        sceneName: isLookupNode ? '查表附录' : '',
        level: 0,
        order: dependencyIndex + index * 3,
        color: isLookupNode ? '#fde68a' : '#dcfce7',
        semanticRole: resolveSemanticInputRole(dependencyName, resultInfo, parameterInfo),
        layer: 'input',
        defaultVisible: true,
        isMainline: true,
        panelContext: buildWorkbenchReasoningPanelContext({
          title: displayName,
          nodeType: sourceType,
          explanation: buildWorkbenchReasoningExplanation({
            nodeId: sourceId,
            nodeType: sourceType,
            purpose: buildWorkbenchInputPurposeDraft(resolveSemanticInputRole(dependencyName, resultInfo, parameterInfo)),
            parameterItems: [
              {
                paramName: displayName,
                value: resultInfo.value || latestScope?.[dependencyName] || parameterInfo?.value || '',
                unitCode: resultInfo.unitCode || parameterInfo?.unitCode || '',
                source: buildWorkbenchInputSourceLabel(resolveSemanticInputRole(dependencyName, resultInfo, parameterInfo), parameterInfo)
              }
            ],
            derivation: '该节点不是由当前模块内部公式推导得到，而是被后续链路直接引用',
            impact: buildWorkbenchInputImpactDraft(resolveSemanticInputRole(dependencyName, resultInfo, parameterInfo))
          })
        })
      })
      ensureEdge(sourceId, targetId, dependencyName)
    })
  })

  const rawNodes = [...nodeMap.values()]
  const rawEdges = [...edgeMap.values()]
  const nodes = decorateWorkbenchFocusSemantics(rawNodes, rawEdges)

  return {
    nodes,
    edges: rawEdges,
    sceneCount: sceneOrderMap.size,
    formulaCount: filteredFormulas.length,
    dependencyCount: edgeMap.size,
    inputCount: inputNames.size
  }
}

function buildWorkbenchFlowEdgeMaps(edges = []) {
  const upstreamMap = new Map()
  const downstreamMap = new Map()

  for (const edge of Array.isArray(edges) ? edges : []) {
    const source = String(edge?.source || '')
    const target = String(edge?.target || '')
    if (!source || !target) {
      continue
    }

    const upstream = upstreamMap.get(target) || new Set()
    upstream.add(source)
    upstreamMap.set(target, upstream)

    const downstream = downstreamMap.get(source) || new Set()
    downstream.add(target)
    downstreamMap.set(source, downstream)
  }

  return { upstreamMap, downstreamMap }
}

function collectWorkbenchFlowVisibleNodeIds({ graph = {}, activeNodeId = '' } = {}) {
  const visibleNodeIds = new Set()
  const normalizedActiveNodeId = String(activeNodeId || '')
  if (!normalizedActiveNodeId) {
    return visibleNodeIds
  }

  const { upstreamMap, downstreamMap } = buildWorkbenchFlowEdgeMaps(graph?.edges || [])

  const walkUpstream = (nodeId) => {
    const normalizedNodeId = String(nodeId || '')
    if (!normalizedNodeId || visibleNodeIds.has(normalizedNodeId)) {
      return
    }
    visibleNodeIds.add(normalizedNodeId)
    for (const parentId of upstreamMap.get(normalizedNodeId) || []) {
      walkUpstream(parentId)
    }
  }

  walkUpstream(normalizedActiveNodeId)
  for (const childId of downstreamMap.get(normalizedActiveNodeId) || []) {
    visibleNodeIds.add(String(childId || ''))
  }

  return visibleNodeIds
}

export function buildWorkbenchFlowVisibleGraph({
  graph = {},
  activeFormulaKey = '',
  selectedNodeId = ''
} = {}) {
  const nodes = Array.isArray(graph?.nodes) ? graph.nodes : []
  const edges = Array.isArray(graph?.edges) ? graph.edges : []
  const normalizedSelectedNodeId = String(selectedNodeId || '')
  const activeFormulaNode = nodes.find((node) => String(node?.formulaKey || '') === String(activeFormulaKey || '')) || null
  const activeNodeId = normalizedSelectedNodeId || String(activeFormulaNode?.id || '')

  if (!activeNodeId) {
    return {
      ...graph,
      nodes,
      edges
    }
  }

  const visibleNodeIds = collectWorkbenchFlowVisibleNodeIds({ graph, activeNodeId })
  return {
    ...graph,
    nodes: nodes.filter((node) => visibleNodeIds.has(String(node?.id || ''))),
    edges: edges.filter((edge) =>
      visibleNodeIds.has(String(edge?.source || '')) && visibleNodeIds.has(String(edge?.target || ''))
    )
  }
}

export function resolveWorkbenchFlowSelectedNode(graph = {}, nodeId = '') {
  const matchedNode = (Array.isArray(graph?.nodes) ? graph.nodes : []).find(
    (node) => String(node?.id || '') === String(nodeId || '')
  )
  if (!matchedNode) {
    return null
  }

  return {
    nodeId: String(matchedNode.id || ''),
    nodeType: String(matchedNode.nodeType || ''),
    name: String(matchedNode.name || ''),
    metricText: formatMetricText(matchedNode.value, matchedNode.unitCode),
    formulaKey: String(matchedNode.formulaKey || ''),
    canOpenFormula: String(matchedNode.nodeType || '') === 'formula' && Boolean(matchedNode.formulaRow),
    formulaRow: matchedNode.formulaRow || null
  }
}

export function resolveWorkbenchFlowExpandedFormulaKeys({
  previousExpandedFormulaKeys = [],
  nextFormulaKey = ''
} = {}) {
  const normalizedNextFormulaKey = String(nextFormulaKey || '')
  if (!normalizedNextFormulaKey) {
    return Array.isArray(previousExpandedFormulaKeys) ? [...previousExpandedFormulaKeys] : []
  }
  return [normalizedNextFormulaKey]
}

export function collectFormulaHighlights(formula = {}, allFormulas = []) {
  const variableNames = new Set(Object.keys(formula?.variables || {}))
  return (Array.isArray(allFormulas) ? allFormulas : []).reduce((accumulator, row) => {
    accumulator[row.name] = variableNames.has(row.name)
    return accumulator
  }, {})
}

export function buildFormulaAutocompleteItems({ keyword = '', parameterRows = [], lookupItems = [] } = {}) {
  const normalizedKeyword = String(keyword || '').trim()
  const parameterItems = (Array.isArray(parameterRows) ? parameterRows : [])
    .filter((row) => {
      const paramName = String(row.paramName || '')
      if (paramName === 'π' || paramName === 'pi') return false
      if (!normalizedKeyword) return true
      const displayName = String(row.displayName || '')
      const aliases = FORMULA_PARAMETER_ALIASES[paramName] || []
      return [paramName, displayName, ...aliases].some((candidate) => String(candidate || '').includes(normalizedKeyword))
    })
    .map((row) => ({
      label: row.displayName || row.paramName || '',
      value: row.paramName || '',
      group: row.source === 'formula' ? '中间参数' : '基础参数',
      sourceFormula: row.sourceFormula || ''
    }))

  const lookupCandidates = (Array.isArray(lookupItems) ? lookupItems : [])
    .filter((item) => {
      if (!normalizedKeyword) return true
      return String(item.lookup_name || '').includes(normalizedKeyword)
    })
    .map((item) => ({
      label: item.lookup_name || '',
      value: item.lookup_name ? `${item.lookup_name}!B:C` : '',
      group: '查表附录',
      sourceFormula: ''
    }))

  return [...parameterItems, ...lookupCandidates]
    .sort((left, right) => {
      if (left.group !== right.group) {
        const groupRank = {
          基础参数: 0,
          中间参数: 1,
          查表附录: 2
        }
        return (groupRank[left.group] ?? 99) - (groupRank[right.group] ?? 99)
      }
      return String(left.label || '').localeCompare(String(right.label || ''), 'zh-CN')
    })
}

export function buildFormulaShortcutItems() {
  return COMMON_FORMULA_SHORTCUT_ITEMS.map((item) => ({ ...item }))
}

export function buildFormulaAutocompleteSections({ keyword = '', parameterRows = [], lookupItems = [] } = {}) {
  const normalizedKeyword = String(keyword || '').trim().toUpperCase()
  const functionKeyword = /^(V|VL|VLO|C|CU|CUR|H|HL|HLO|I|IF|IFE)$/i.test(normalizedKeyword)
  const functionItems = FORMULA_FUNCTION_ITEMS
    .filter((item) => !normalizedKeyword || item.label.toUpperCase().includes(normalizedKeyword))
    .map((item) => ({ ...item }))
  const parameterItems = buildFormulaAutocompleteItems({
    keyword: functionKeyword ? '' : keyword,
    parameterRows,
    lookupItems
  })
  const groupedSections = new Map()

  if (functionItems.length) {
    groupedSections.set('函数', functionItems)
  }
  for (const item of parameterItems) {
    const group = String(item.group || '参数')
    const bucket = groupedSections.get(group) || []
    bucket.push(item)
    groupedSections.set(group, bucket)
  }

  const sections = [...groupedSections.entries()]
    .map(([label, items]) => ({ label, items }))
    .sort((left, right) => (FORMULA_GROUP_ORDER[left.label] ?? 99) - (FORMULA_GROUP_ORDER[right.label] ?? 99))

  if (functionKeyword) {
    return sections
  }
  return sections.sort((left, right) => {
    if (left.label === '函数') return 1
    if (right.label === '函数') return -1
    return (FORMULA_GROUP_ORDER[left.label] ?? 99) - (FORMULA_GROUP_ORDER[right.label] ?? 99)
  })
}

export function resolveFormulaArgumentHint({ expression = '', selectionStart = 0 } = {}) {
  const prefix = String(expression || '').slice(0, Math.max(0, Number(selectionStart || 0)))
  const matched = prefix.match(/(VLOOKUP|CURVE2D|IF)\(([^()]*)$/i)
  if (!matched) {
    return null
  }
  const functionName = String(matched[1] || '').toUpperCase()
  const argumentIndex = String(matched[2] || '').split(',').length - 1
  const hint = FUNCTION_ARGUMENT_HINTS[functionName]?.[argumentIndex]
  if (!hint) {
    return null
  }
  return {
    functionName,
    argumentIndex,
    label: hint[0],
    description: hint[1]
  }
}

export function resolveFormulaAutocompleteInsertion({
  expression = '',
  selectionStart = 0,
  selectionEnd = 0,
  insertedValue = ''
} = {}) {
  const current = String(expression || '')
  const safeStart = Math.max(0, Number(selectionStart || 0))
  const safeEnd = Math.max(safeStart, Number(selectionEnd || 0))
  const insertion = String(insertedValue || '')
  let replaceStart = safeStart

  if (safeStart === safeEnd) {
    const prefix = current.slice(0, safeStart)
    const matched = prefix.match(FORMULA_AUTOCOMPLETE_TRIGGER_PATTERN)
    const keyword = matched ? String(matched[1] || '') : ''
    replaceStart = Math.max(0, safeStart - keyword.length)
  }

  const nextValue = `${current.slice(0, replaceStart)}${insertion}${current.slice(safeEnd)}`
  const nextSelection = /\(\)$/.test(insertion)
    ? replaceStart + insertion.length - 1
    : replaceStart + insertion.length
  return {
    nextValue,
    nextSelectionStart: nextSelection,
    nextSelectionEnd: nextSelection
  }
}

import { ALL_RESERVED_IDENTIFIERS } from '@/utils/formulaEngine.mjs'

const FORMULA_VARIABLE_IDENTIFIER_PATTERN = /([A-Za-z_\u00C0-\uFFFF][A-Za-z0-9_\u00C0-\uFFFF]*)\s*(\()?/g
const FORMULA_RESERVED_IDENTIFIERS = new Set([...ALL_RESERVED_IDENTIFIERS].map(id => id.toUpperCase()))

export function resolveFormulaVariablesFromExpression(expression = '', fallbackVariables = {}) {
  const normalizedExpression = String(expression || '')
  const fallbackMap = Object.entries(fallbackVariables || {}).reduce((result, [name, value]) => {
    const normalizedName = String(name || '').trim()
    if (!normalizedName) {
      return result
    }
    result[normalizedName] = typeof value === 'string' ? value : ''
    return result
  }, {})
  const orderedNames = []
  let match
  while ((match = FORMULA_VARIABLE_IDENTIFIER_PATTERN.exec(normalizedExpression)) !== null) {
    const token = String(match[1] || '').trim()
    const isFunctionCall = Boolean(match[2])
    if (!token || isFunctionCall || FORMULA_RESERVED_IDENTIFIERS.has(token.toUpperCase()) || orderedNames.includes(token)) {
      continue
    }
    orderedNames.push(token)
  }

  return orderedNames.reduce((result, name) => {
    result[name] = fallbackMap[name] || ''
    return result
  }, {})
}

export function resolveParameterInsertionDraft({
  row = {},
  editingFormulaKey = '',
  editingFormulaField = '',
  activeFormulaDraft = {},
  formulaCursorStart = null
} = {}) {
  const paramName = String(row?.paramName || '').trim()
  const expression = String(activeFormulaDraft?.expression || '')
  const normalizedEditingKey = String(editingFormulaKey || '').trim()
  const normalizedEditingField = String(editingFormulaField || '').trim()
  const isFormulaEditing = Boolean(normalizedEditingKey) && ['expression', 'all'].includes(normalizedEditingField)

  if (!isFormulaEditing || !paramName) {
    return {
      inserted: false,
      nextExpression: expression,
      nextCursorStart: typeof formulaCursorStart === 'number' && Number.isFinite(formulaCursorStart)
        ? formulaCursorStart
        : expression.length
    }
  }

  const hasNumericCursor = typeof formulaCursorStart === 'number' && Number.isFinite(formulaCursorStart)
  const safeCursor = hasNumericCursor
    ? Math.max(0, Math.min(expression.length, formulaCursorStart))
    : expression.length
  const nextExpression = `${expression.slice(0, safeCursor)}${paramName}${expression.slice(safeCursor)}`

  return {
    inserted: true,
    nextExpression,
    nextCursorStart: safeCursor + paramName.length
  }
}

// ==================== 设计推理图生成函数 ====================

/**
 * 生成设计推理图（新版本）
 * 基于新的类型定义生成可解释的设计推理图
 */
export function generateDesignReasoningFlow({
  designData = {},
  options = {
    showDetailedParameters: true,
    showRuleNodes: true,
    parameterExpandLevel: 1,
    ruleDisplayMode: 'inline',
    fixedMainChain: true
  }
} = {}) {
  // 导入新的工作台流程图生成器
  // 注意：这里需要实际导入 generateDesignReasoningFlow 函数
  // 但由于模块系统限制，这里先提供接口定义
  
  // 临时实现 - 实际应该从 workbenchFlow.ts 导入
  const mockFlow = {
    id: `design-flow-${Date.now()}`,
    nodes: [],
    edges: [],
    layout: {
      mainChainNodeIds: [],
      fixedMainChain: options.fixedMainChain,
      parameterExpandLevel: options.parameterExpandLevel,
      ruleDisplayMode: options.ruleDisplayMode
    },
    metadata: {
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      designScenarioId: designData?.scenarioId,
      designPointId: designData?.pointId
    }
  }

  // 构建示例节点
  const designSteps = [
    { number: 1, name: '输入条件', purpose: '承接型号、工况和基础输入' },
    { number: 2, name: '功率计算', purpose: '计算电机所需功率' },
    { number: 3, name: '扭矩校核', purpose: '校核扭矩是否满足要求' },
    { number: 4, name: '结果输出', purpose: '输出最终设计结果' }
  ]

  designSteps.forEach(step => {
    const stepId = `step-${step.number}-${step.name.replace(/\s+/g, '-').toLowerCase()}`
    const resultAnchorId = `result-${step.number}-${step.name.replace(/\s+/g, '-').toLowerCase()}`

    // 添加步骤节点
    mockFlow.nodes.push({
      id: stepId,
      type: 'step',
      label: `${step.number}. ${step.name}`,
      stepNumber: step.number,
      purpose: step.purpose,
      resultAnchorIds: [resultAnchorId],
      parameterIds: [],
      ruleIds: [],
      expanded: options.showDetailedParameters,
      position: { x: 200 + (step.number - 1) * 300, y: 150 },
      style: {
        color: '#4A90E2',
        borderColor: '#4A90E2',
        borderWidth: 2,
        size: 80
      }
    })

    // 添加结果锚点节点
    mockFlow.nodes.push({
      id: resultAnchorId,
      type: 'result_anchor',
      label: `${step.name}结果`,
      stepId: stepId,
      value: step.number === 2 ? (designData?.power?.requiredPower || 0) : undefined,
      unit: step.number === 2 ? 'kW' : undefined,
      formula: step.number === 2 ? 'P = F × v / η' : undefined,
      downstreamStepIds: step.number < 4 ? [`step-${step.number + 1}-${designSteps[step.number].name.replace(/\s+/g, '-').toLowerCase()}`] : [],
      relatedParameterIds: [],
      relatedRuleIds: [],
      style: {
        color: '#FF6B6B',
        borderColor: '#FF6B6B',
        borderWidth: 3,
        size: 70
      }
    })

    mockFlow.layout.mainChainNodeIds.push(stepId)

    // 添加步骤之间的边
    if (step.number > 1) {
      const prevStepId = `step-${step.number - 1}-${designSteps[step.number - 2].name.replace(/\s+/g, '-').toLowerCase()}`
      mockFlow.edges.push({
        id: `edge-${prevStepId}-${stepId}`,
        source: prevStepId,
        target: stepId,
        type: 'default',
        label: '下一步',
        style: {
          color: '#4A90E2',
          width: 3,
          lineStyle: 'solid'
        }
      })
    }

    // 添加步骤到结果锚点的边
    mockFlow.edges.push({
      id: `edge-${stepId}-${resultAnchorId}`,
      source: stepId,
      target: resultAnchorId,
      type: 'result',
      label: '产生',
      style: {
        color: '#FF6B6B',
        width: 2,
        lineStyle: 'solid'
      }
    })
  })

  return mockFlow
}

/**
 * 获取设计推理图中节点的解释信息
 */
export function getDesignNodeExplanation(flowGraph = {}, nodeId = '') {
  const node = (Array.isArray(flowGraph?.nodes) ? flowGraph.nodes : []).find(
    (node) => String(node?.id || '') === String(nodeId || '')
  )
  
  if (!node) {
    return null
  }

  // 根据节点类型返回不同的解释信息
  switch (node.type) {
    case 'step':
      return {
        nodeId,
        nodeType: node.type,
        title: `步骤解释：${node.label}`,
        sections: [
          {
            title: '步骤目的',
            type: 'text',
            content: node.purpose || '无目的描述'
          },
          {
            title: '关键输入',
            type: 'parameters',
            content: []
          },
          {
            title: '产生结果',
            type: 'text',
            content: '待计算'
          }
        ]
      }
    
    case 'result_anchor':
      return {
        nodeId,
        nodeType: node.type,
        title: `结果解释：${node.label}`,
        sections: [
          {
            title: '结果值',
            type: 'text',
            content: `${node.value || '待计算'} ${node.unit || ''}`
          },
          {
            title: '计算公式',
            type: 'formula',
            content: node.formula || '无公式'
          },
          {
            title: '相关参数',
            type: 'parameters',
            content: []
          },
          {
            title: '校验规则',
            type: 'rules',
            content: []
          }
        ]
      }
    
    default:
      return {
        nodeId,
        nodeType: node.type,
        title: `节点解释：${node.label}`,
        sections: [
          {
            title: '基本信息',
            type: 'text',
            content: node.description || '无详细描述'
          }
        ]
      }
  }
}

/**
 * 向后兼容的包装函数
 * 将新的设计推理图转换为旧的流程图格式
 */
export function convertToLegacyFlowGraph(designFlowGraph = {}) {
  const legacyNodes = (Array.isArray(designFlowGraph?.nodes) ? designFlowGraph.nodes : [])
    .filter(node => node.type === 'step' || node.type === 'result_anchor')
    .map(node => {
      if (node.type === 'step') {
        return {
          id: node.id,
          name: node.label,
          title: node.label,
          nodeType: 'step',
          stepCode: `step${node.stepNumber}`,
          summary: node.purpose,
          panelContext: {
            summary: [node.purpose],
            parameters: [],
            lookups: [],
            constraints: []
          },
          x: node.position?.x || 0,
          y: node.position?.y || 0
        }
      } else if (node.type === 'result_anchor') {
        return {
          id: node.id,
          name: node.label,
          title: node.label,
          nodeType: 'result',
          stepCode: 'output',
          summary: `${node.value || '待计算'} ${node.unit || ''}`,
          panelContext: {
            summary: [`输出 ${node.value || '待计算'} ${node.unit || ''}`],
            parameters: [],
            lookups: [],
            constraints: []
          },
          x: node.position?.x || 0,
          y: node.position?.y || 0
        }
      }
      return null
    })
    .filter(Boolean)

  const legacyEdges = (Array.isArray(designFlowGraph?.edges) ? designFlowGraph.edges : [])
    .filter(edge => edge.type === 'default')
    .map(edge => ({
      source: edge.source,
      target: edge.target
    }))

  return {
    nodes: legacyNodes,
    edges: legacyEdges,
    stepCount: legacyNodes.filter(n => n.nodeType === 'step').length,
    queryCount: 0,
    decisionCount: 0,
    resultCount: legacyNodes.filter(n => n.nodeType === 'result').length
  }
}

export function resolveFormulaAutocompleteKeyword({ expression = '', selectionStart = 0 } = {}) {
  const current = String(expression || '')
  const safeStart = Math.max(0, Number(selectionStart || 0))
  const prefix = current.slice(0, safeStart)
  const matched = prefix.match(FORMULA_AUTOCOMPLETE_TRIGGER_PATTERN)
  return matched ? String(matched[1] || '') : ''
}

export function resolveFormulaInteractionState({
  currentSelectedKey = '',
  currentEditingKey = '',
  nextSelectedKey = ''
} = {}) {
  const selectedKey = String(currentSelectedKey || '')
  const editingKey = String(currentEditingKey || '')
  const nextKey = String(nextSelectedKey || '')

  if (!nextKey) {
    return { selectedKey: '', editingKey: '' }
  }
  if (nextKey !== selectedKey) {
    return { selectedKey: nextKey, editingKey: '' }
  }
  return {
    selectedKey: nextKey,
    editingKey: editingKey === nextKey ? '' : nextKey
  }
}

export function buildFormulaResultMap(results = []) {
  return (Array.isArray(results) ? results : []).reduce((accumulator, row) => {
    const formulaName = String(row?.source_formula || row?.result_name || '').trim()
    if (!formulaName) {
      return accumulator
    }
    const value = String(row?.result_value ?? '').trim()
    const unitCode = String(row?.unit_code || '').trim()
    accumulator[formulaName] = {
      value,
      unitCode,
      displayText: unitCode && value ? `${value} ${unitCode}` : value,
      lookupDetail: row?.lookup_detail || null
    }
    return accumulator
  }, {})
}

export function buildCurveFormulaExpression({
  lookupName = '',
  inputName = '',
  seriesKey = '',
  direction = 'X2Y',
  lookupMode = 'LINEAR',
  multiplier = ''
} = {}) {
  const curveBody = `CURVE2D(${String(lookupName || '').trim()},${String(inputName || '').trim()},${String(seriesKey || '').trim()},${String(direction || 'X2Y').trim().toUpperCase()},${String(lookupMode || 'LINEAR').trim().toUpperCase()})`
  const factor = String(multiplier || '').trim()
  return factor ? `=${factor}*${curveBody}` : `=${curveBody}`
}

export function parseCurveFormulaExpression(expression = '') {
  const matched = String(expression || '').trim().match(CURVE_EXPRESSION_RE)
  if (!matched?.groups) {
    return null
  }
  return {
    multiplier: String(matched.groups.multiplier || '').trim(),
    lookupName: String(matched.groups.lookupName || '').trim(),
    inputName: String(matched.groups.inputName || '').trim(),
    seriesKey: String(matched.groups.seriesKey || '').trim(),
    direction: String(matched.groups.direction || '').trim().toUpperCase(),
    lookupMode: String(matched.groups.lookupMode || '').trim().toUpperCase()
  }
}

export function buildCurveUpgradeHint(expression = '') {
  const matched = String(expression || '').trim().match(VLOOKUP_UPGRADE_RE)
  if (!matched?.groups) {
    return null
  }
  return {
    multiplier: String(matched.groups.multiplier || '').trim(),
    inputName: String(matched.groups.inputName || '').trim(),
    lookupName: String(matched.groups.lookupName || '').trim()
  }
}

export function resolveNextFormulaSelectionKey(currentKey = '', nextKey = '') {
  const normalizedCurrentKey = String(currentKey || '')
  const normalizedNextKey = String(nextKey || '')
  if (!normalizedNextKey) {
    return ''
  }
  return normalizedCurrentKey === normalizedNextKey ? '' : normalizedNextKey
}

function compareModuleRows(left = {}, right = {}) {
  const moduleDiff = String(left.module_code || '').localeCompare(String(right.module_code || ''), 'zh-CN')
  if (moduleDiff !== 0) {
    return moduleDiff
  }
  return compareFormulaRows(left, right)
}

export function groupWorkbenchFormulaModules(rows = [], emptyModules = []) {
  const modules = new Map()
  for (const module of Array.isArray(emptyModules) ? emptyModules : []) {
    const moduleCode = String(module?.module_code || '')
    if (!moduleCode) {
      continue
    }
    modules.set(moduleCode, {
      moduleCode,
      moduleName: module?.module_name || '功率计算',
      scenes: (Array.isArray(module?.scenes) ? module.scenes : []).map((scene) => ({
        moduleCode,
        moduleName: module?.module_name || '功率计算',
        sceneCode: scene?.scene_code || '',
        sceneName: scene?.scene_name || '未命名场景',
        rows: Array.isArray(scene?.formulas)
          ? [...scene.formulas]
          : (Array.isArray(scene?.rows) ? [...scene.rows] : [])
      }))
    })
  }

  for (const row of Array.isArray(rows) ? rows : []) {
    const moduleCode = String(row?.module_code || 'power_calc')
    const moduleName = row?.module_name || '功率计算'
    if (!modules.has(moduleCode)) {
      modules.set(moduleCode, {
        moduleCode,
        moduleName,
        scenes: []
      })
    }
    const module = modules.get(moduleCode)
    if (!module.moduleName && moduleName) {
      module.moduleName = moduleName
    }
    let scene = module.scenes.find((item) => item.sceneCode === String(row?.scene_code || ''))
    if (!scene) {
      scene = {
        moduleCode,
        moduleName: module.moduleName,
        sceneCode: row?.scene_code || '',
        sceneName: row?.scene_name || '未命名场景',
        rows: []
      }
      module.scenes.push(scene)
    }
    scene.rows.push(row)
  }

  for (const module of modules.values()) {
    module.scenes.sort((left, right) =>
      String(left.sceneName || '').localeCompare(String(right.sceneName || ''), 'zh-CN')
    )
    for (const scene of module.scenes) {
      scene.rows.sort((left, right) =>
        Number(left.sort_order || 0) - Number(right.sort_order || 0) ||
        Number(left.id || 0) - Number(right.id || 0)
      )
    }
  }

  return [...modules.values()]
}

export function buildModuleSummary(module = {}) {
  const scenes = Array.isArray(module?.scenes) ? module.scenes : []
  return {
    sceneCount: scenes.length,
    formulaCount: scenes.reduce((total, scene) => {
      return total + (Array.isArray(scene?.rows) ? scene.rows.length : 0)
    }, 0)
  }
}

export function resolveActiveModuleSceneFormula({
  modules = [],
  activeModuleCode = '',
  activeSceneCode = '',
  activeFormulaKey = '',
  lastSceneMap = {}
} = {}) {
  const safeModules = Array.isArray(modules) ? modules : []
  const module =
    safeModules.find((item) => String(item?.moduleCode || '') === String(activeModuleCode || '')) ||
    safeModules[0] ||
    null

  if (!module) {
    return { activeModuleCode: '', activeSceneCode: '', activeFormulaKey: '', activeFormula: null }
  }

  const scenes = Array.isArray(module?.scenes) ? module.scenes : []
  const preferredSceneCode = String(activeSceneCode || lastSceneMap?.[module.moduleCode] || '')
  const scene =
    scenes.find((item) => String(item?.sceneCode || '') === preferredSceneCode) ||
    scenes[0] ||
    null
  const rows = Array.isArray(scene?.rows) ? scene.rows : []
  const formula =
    rows.find((item) => String(item?._rowKey || '') === String(activeFormulaKey || '')) ||
    rows[0] ||
    null

  return {
    activeModuleCode: String(module?.moduleCode || ''),
    activeSceneCode: String(scene?.sceneCode || ''),
    activeFormulaKey: String(formula?._rowKey || ''),
    activeFormula: formula || null
  }
}

export function resolveNextFocusAfterModuleDelete({
  modules = [],
  deletedModuleCode = '',
  activeModuleCode = ''
} = {}) {
  const remained = (Array.isArray(modules) ? modules : []).filter((item) =>
    String(item?.moduleCode || '') !== String(deletedModuleCode || '')
  )
  return resolveActiveModuleSceneFormula({
    modules: remained,
    activeModuleCode: String(activeModuleCode || '') === String(deletedModuleCode || '') ? '' : activeModuleCode,
    activeSceneCode: '',
    activeFormulaKey: '',
    lastSceneMap: {}
  })
}

export function resolveNextFocusAfterSceneDelete({
  modules = [],
  deletedModuleCode = '',
  deletedSceneCode = '',
  activeModuleCode = '',
  activeSceneCode = '',
  lastSceneMap = {}
} = {}) {
  const nextModules = (Array.isArray(modules) ? modules : []).map((module) => {
    if (String(module?.moduleCode || '') !== String(deletedModuleCode || '')) {
      return module
    }
    return {
      ...module,
      scenes: (Array.isArray(module?.scenes) ? module.scenes : []).filter((scene) =>
        String(scene?.sceneCode || '') !== String(deletedSceneCode || '')
      )
    }
  })

  return resolveActiveModuleSceneFormula({
    modules: nextModules,
    activeModuleCode,
    activeSceneCode: String(activeSceneCode || '') === String(deletedSceneCode || '') ? '' : activeSceneCode,
    activeFormulaKey: '',
    lastSceneMap
  })
}

export function toggleFormulaBatchSelection(selectedKeys = [], rowKey = '') {
  const normalizedRowKey = String(rowKey || '')
  if (!normalizedRowKey) {
    return Array.isArray(selectedKeys) ? [...selectedKeys] : []
  }
  const current = Array.isArray(selectedKeys) ? [...selectedKeys] : []
  return current.includes(normalizedRowKey)
    ? current.filter((item) => item !== normalizedRowKey)
    : [...current, normalizedRowKey]
}

export function resolveNextFocusAfterFormulaBatchDelete({
  modules = [],
  activeModuleCode = '',
  activeSceneCode = '',
  deletedFormulaKeys = []
} = {}) {
  const deletedSet = new Set(
    (Array.isArray(deletedFormulaKeys) ? deletedFormulaKeys : []).map((item) => String(item || ''))
  )
  const nextModules = (Array.isArray(modules) ? modules : []).map((module) => ({
    ...module,
    scenes: (Array.isArray(module?.scenes) ? module.scenes : []).map((scene) => ({
      ...scene,
      rows: (Array.isArray(scene?.rows) ? scene.rows : []).filter(
        (row) => !deletedSet.has(String(row?._rowKey || ''))
      )
    }))
  }))

  return resolveActiveModuleSceneFormula({
    modules: nextModules,
    activeModuleCode,
    activeSceneCode,
    activeFormulaKey: '',
    lastSceneMap: {}
  })
}

export function resolveNextFocusAfterFormulaDelete({
  modules = [],
  activeModuleCode = '',
  activeSceneCode = '',
  activeFormulaKey = '',
  deletedFormulaKey = ''
} = {}) {
  const normalizedDeletedKey = String(deletedFormulaKey || '')
  const normalizedActiveKey = String(activeFormulaKey || '')
  const sourceModules = Array.isArray(modules) ? modules : []
  const sourceModule =
    sourceModules.find((module) => String(module?.moduleCode || '') === String(activeModuleCode || '')) || null
  const sourceScene =
    (Array.isArray(sourceModule?.scenes) ? sourceModule.scenes : []).find(
      (scene) => String(scene?.sceneCode || '') === String(activeSceneCode || '')
    ) || null
  const sourceRows = Array.isArray(sourceScene?.rows) ? sourceScene.rows : []
  const deletedIndex = sourceRows.findIndex((row) => String(row?._rowKey || '') === normalizedDeletedKey)
  const fallbackIndex =
    deletedIndex >= 0
      ? deletedIndex
      : sourceRows.findIndex((row) => String(row?._rowKey || '') === normalizedActiveKey)
  const nextModules = sourceModules.map((module) => ({
    ...module,
    scenes: (Array.isArray(module?.scenes) ? module.scenes : []).map((scene) => ({
      ...scene,
      rows: (Array.isArray(scene?.rows) ? scene.rows : []).filter(
        (row) => String(row?._rowKey || '') !== normalizedDeletedKey
      )
    }))
  }))
  const nextModule =
    nextModules.find((module) => String(module?.moduleCode || '') === String(activeModuleCode || '')) ||
    nextModules[0] ||
    null
  const nextScene =
    (Array.isArray(nextModule?.scenes) ? nextModule.scenes : []).find(
      (scene) => String(scene?.sceneCode || '') === String(activeSceneCode || '')
    ) ||
    (Array.isArray(nextModule?.scenes) ? nextModule.scenes[0] : null) ||
    null
  const nextRows = Array.isArray(nextScene?.rows) ? nextScene.rows : []
  const targetIndex = fallbackIndex >= 0 ? fallbackIndex : 0
  const nextFormula = nextRows[targetIndex] || nextRows[Math.max(targetIndex - 1, 0)] || null

  return {
    activeModuleCode: String(nextModule?.moduleCode || ''),
    activeSceneCode: String(nextScene?.sceneCode || ''),
    activeFormulaKey: String(nextFormula?._rowKey || ''),
    activeFormula: nextFormula || null
  }
}

function compareFormulaRows(left = {}, right = {}) {
  const sceneDiff = String(left.scene_code || '').localeCompare(String(right.scene_code || ''), 'zh-CN')
  if (sceneDiff !== 0) {
    return sceneDiff
  }
  const orderDiff = Number(left.sort_order || 0) - Number(right.sort_order || 0)
  if (orderDiff !== 0) {
    return orderDiff
  }
  return Number(left.id || 0) - Number(right.id || 0)
}

export function moveFormulaRowWithinScene(rows = [], rowId, direction = 'up') {
  const sourceRows = Array.isArray(rows) ? rows.map((row) => ({ ...row })) : []
  const currentIndex = sourceRows.findIndex((row) => Number(row.id || 0) === Number(rowId || 0))
  if (currentIndex < 0) {
    return { rows: sourceRows, payload: [] }
  }

  const currentRow = sourceRows[currentIndex]
  const sceneRows = sourceRows
    .filter((row) => String(row.scene_code || '') === String(currentRow.scene_code || ''))
    .sort(compareFormulaRows)
  const sceneIndex = sceneRows.findIndex((row) => Number(row.id || 0) === Number(currentRow.id || 0))
  const swapIndex = direction === 'up' ? sceneIndex - 1 : sceneIndex + 1
  if (sceneIndex < 0 || swapIndex < 0 || swapIndex >= sceneRows.length) {
    return { rows: sourceRows, payload: [] }
  }

  const currentSceneRow = sceneRows[sceneIndex]
  const targetSceneRow = sceneRows[swapIndex]
  const nextOrder = Number(targetSceneRow.sort_order || 0)
  const currentOrder = Number(currentSceneRow.sort_order || 0)

  for (const row of sourceRows) {
    if (Number(row.id || 0) === Number(currentSceneRow.id || 0)) {
      row.sort_order = nextOrder
    } else if (Number(row.id || 0) === Number(targetSceneRow.id || 0)) {
      row.sort_order = currentOrder
    }
  }

  sourceRows.sort(compareFormulaRows)
  return {
    rows: sourceRows,
    payload: [
      { id: Number(currentSceneRow.id || 0), sort_order: nextOrder },
      { id: Number(targetSceneRow.id || 0), sort_order: currentOrder }
    ]
  }
}

export function reorderFormulaRowsWithinScene(rows = [], moduleCode = '', sceneCode = '', orderedIds = []) {
  const sourceRows = Array.isArray(rows) ? rows.map((row) => ({ ...row })) : []
  const normalizedModuleCode = String(moduleCode || '')
  const normalizedSceneCode = String(sceneCode || '')
  const normalizedIds = Array.isArray(orderedIds) ? orderedIds.map((item) => Number(item || 0)).filter((item) => item > 0) : []
  const sceneRows = sourceRows.filter((row) =>
    String(row.module_code || '') === normalizedModuleCode &&
    String(row.scene_code || '') === normalizedSceneCode
  )

  if (!sceneRows.length || sceneRows.length !== normalizedIds.length) {
    return { rows: sourceRows, payload: [] }
  }

  const sceneIds = sceneRows.map((row) => Number(row.id || 0))
  const hasSameMembers = sceneIds.every((id) => normalizedIds.includes(id))
  if (!hasSameMembers) {
    return { rows: sourceRows, payload: [] }
  }

  const sortOrderById = new Map(normalizedIds.map((id, index) => [id, index]))
  const reorderedSceneRows = normalizedIds.map((id, index) => {
    const matched = sceneRows.find((row) => Number(row.id || 0) === id)
    return {
      ...matched,
      sort_order: index
    }
  })
  let sceneCursor = 0
  for (let index = 0; index < sourceRows.length; index += 1) {
    if (
      String(sourceRows[index].module_code || '') === normalizedModuleCode &&
      String(sourceRows[index].scene_code || '') === normalizedSceneCode
    ) {
      sourceRows[index] = reorderedSceneRows[sceneCursor]
      sceneCursor += 1
    }
  }

  return {
    rows: sourceRows.sort(compareModuleRows),
    payload: normalizedIds.map((id, index) => ({ id, sort_order: index }))
  }
}

export function resolveWorkbenchParameterPanelTopForContainer({
  activeRowDocumentTop = 0,
  columnDocumentTop = 0,
  panelHeight = 0,
  containerHeight = 0,
  rowOffset = 24
} = {}) {
  const rawTop = Math.max(
    Number(activeRowDocumentTop || 0) - Number(columnDocumentTop || 0) + Number(rowOffset || 0),
    0
  )
  const maxTop = Math.max(Number(containerHeight || 0) - Number(panelHeight || 0), 0)
  return Math.min(rawTop, maxTop)
}

export function resolveWorkbenchParameterPanelTop({
  activeRowViewportTop = 0,
  scrollTop = 0,
  columnTop = 0,
  panelHeight = 0,
  viewportHeight = 0,
  minTop = 16,
  viewportPadding = 16
} = {}) {
  const normalizedMinTop = Math.max(Number(minTop || 0), 0)
  const normalizedScrollTop = Math.max(Number(scrollTop || 0), 0)
  const normalizedColumnTop = Math.max(Number(columnTop || 0), 0)
  const normalizedPanelHeight = Math.max(Number(panelHeight || 0), 0)
  const normalizedViewportHeight = Math.max(Number(viewportHeight || 0), 0)
  const normalizedActiveRowTop = Math.max(Number(activeRowViewportTop || 0), 0)
  const normalizedViewportPadding = Math.max(Number(viewportPadding || 0), 0)
  const maxVisibleTop = Math.max(normalizedMinTop, normalizedViewportHeight - normalizedPanelHeight - normalizedViewportPadding)
  const targetVisibleTop = Math.min(Math.max(normalizedActiveRowTop, normalizedMinTop), maxVisibleTop)
  const targetDocumentTop = normalizedScrollTop + targetVisibleTop
  return Math.max(0, targetDocumentTop - normalizedColumnTop)
}

export function resolveFormulaViewportTargetScrollTop({
  currentScrollTop = 0,
  rowDocumentTop = 0,
  rowHeight = 0,
  viewportHeight = 0
} = {}) {
  const normalizedRowDocumentTop = Math.max(Number(rowDocumentTop || 0), 0)
  const normalizedRowHeight = Math.max(Number(rowHeight || 0), 0)
  const normalizedViewportHeight = Math.max(Number(viewportHeight || 0), 0)
  const targetScrollTop = normalizedRowDocumentTop - (normalizedViewportHeight - normalizedRowHeight) / 2
  return Math.max(0, targetScrollTop)
}

export function mergeWorkbenchParameterRows({ coreRows = [], snapshotMap = new Map() } = {}) {
  return (Array.isArray(coreRows) ? coreRows : []).map((row) => {
    if (row.dirty || row.source === 'draft') {
      return row
    }
    if (!snapshotMap.has(row.parameterId)) {
      return row
    }
    return {
      ...row,
      value: String(snapshotMap.get(row.parameterId) ?? ''),
      dirty: false,
      source: 'snapshot'
    }
  })
}

export function buildCompareRouteQuery({ modelId, formulaId, formulaName, targetParameter } = {}) {
  return {
    mode: 'formula-impact',
    modelId: String(modelId || ''),
    formulaId: String(formulaId || ''),
    formulaName: formulaName || '',
    targetParameter: targetParameter || ''
  }
}

export function buildWorkbenchParameterSavePayload({ familyId, versionId, rows = [] } = {}) {
  return {
    family_id: Number(familyId || 0),
    rows: (Array.isArray(rows) ? rows : [])
      .filter((row) => row?.dirty || row?.source === 'draft' || row?.pendingCreate)
      .map((row) => ({
        version_id: Number(versionId || 0),
        parameter_id: Number(row?.parameterId || 0),
        param_code: String(row?.paramCode || '').trim(),
        param_name: String(row?.paramName || '').trim(),
        unit_code: String(row?.unitCode || '').trim(),
        value_type: String(row?.valueType || 'basic').trim(),
        param_value: row?.value == null ? '' : String(row.value)
      }))
  }
}

export function buildCompareTargetOptions(baseRows = [], currentValue = '') {
  const values = new Set()
  if (currentValue) {
    values.add(String(currentValue))
  }

  for (const row of Array.isArray(baseRows) ? baseRows : []) {
    const paramName = String(row?.paramName || '').trim()
    if (paramName) {
      values.add(paramName)
    }
  }

  return [...values]
}

export function groupSceneResults(results = []) {
  const groups = new Map()
  for (const row of Array.isArray(results) ? results : []) {
    const sceneCode = row.scene_code || 'default'
    if (!groups.has(sceneCode)) {
      groups.set(sceneCode, {
        sceneCode,
        sceneName: row.scene_name || sceneCode,
        rows: []
      })
    }
    groups.get(sceneCode).rows.push(row)
  }
  return [...groups.values()]
}
