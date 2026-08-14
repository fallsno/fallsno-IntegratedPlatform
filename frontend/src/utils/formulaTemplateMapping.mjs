const cloneRequiredVariables = (value) => (
  Array.isArray(value) ? value.filter(Boolean).map(item => String(item)) : []
)

const LEGACY_TARGET_KEY = '__default__'

const normalizeTargetConfig = (targetKey, targetConfig) => {
  const config = targetConfig && typeof targetConfig === 'object' ? targetConfig : {}
  return {
    key: String(targetKey),
    expression: String(config.expression ?? '').trim(),
    requiredVariables: cloneRequiredVariables(config.required_variables),
    description: String(config.description ?? '').trim()
  }
}

const getSolveTargets = (formula) => {
  if (!formula?.solve_targets || typeof formula.solve_targets !== 'object') {
    const requiredVariables = formula?.variables && typeof formula.variables === 'object'
      ? Object.keys(formula.variables)
      : []

    if (!String(formula?.expression ?? '').trim()) {
      return []
    }

    return [{
      key: LEGACY_TARGET_KEY,
      expression: String(formula.expression).trim(),
      requiredVariables,
      description: ''
    }]
  }

  return Object.entries(formula.solve_targets)
    .map(([targetKey, config]) => normalizeTargetConfig(targetKey, config))
    .filter(target => target.expression)
}

const replaceVariableToken = (expression, variableName, mappedName) => {
  if (!variableName) {
    return expression
  }

  return expression.split(variableName).join(mappedName)
}

export function getFormulaTargetOptions(formula) {
  return getSolveTargets(formula)
}

export function getRequiredMappings(formula, targetKey) {
  const target = getSolveTargets(formula).find(item => item.key === String(targetKey))
  if (!target) {
    return []
  }
  return [...target.requiredVariables]
}

export function buildFormulaLinkPayload({ formula, targetKey, mappings = {}, rowName = '' }) {
  const normalizedTargetKey = targetKey == null ? LEGACY_TARGET_KEY : String(targetKey)
  const target = getSolveTargets(formula).find(item => item.key === normalizedTargetKey)
  if (!target) {
    throw new Error(`未找到目标参数: ${targetKey}`)
  }

  const missingVariables = target.requiredVariables.filter(variableName => !String(mappings[variableName] ?? '').trim())
  if (missingVariables.length > 0) {
    throw new Error(`缺少必填变量映射: ${missingVariables.join(', ')}`)
  }

  let materializedExpression = target.expression
  const cleanMappings = {}

  target.requiredVariables.forEach((variableName) => {
    const mappedName = String(mappings[variableName]).trim()
    cleanMappings[variableName] = mappedName
    materializedExpression = replaceVariableToken(materializedExpression, variableName, mappedName)
  })

  const payload = {
    expression: `=${materializedExpression}`,
    formula_name: formula?.name ?? '',
    formula_id: formula?.id ?? null,
    formula_target: target.key,
    formula_source_expression: target.expression,
    formula_mappings: cleanMappings,
    note: `公式: ${formula?.name ?? ''}${target.description ? ` (${target.description})` : ''}`
  }

  if (rowName) {
    payload.name = rowName
  }

  return payload
}
