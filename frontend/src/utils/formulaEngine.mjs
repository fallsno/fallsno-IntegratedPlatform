import { create, all } from 'mathjs'

const math = create(all)

const SYMBOL_REPLACEMENTS = [
  [/（/g, '('],
  [/）/g, ')'],
  [/【/g, '('],
  [/】/g, ')'],
  [/［/g, '('],
  [/］/g, ')'],
  [/｛/g, '('],
  [/｝/g, ')'],
  [/，/g, ','],
  [/、/g, ','],
  [/；/g, ';'],
  [/：/g, ':'],
  [/＋/g, '+'],
  [/－/g, '-'],
  [/–/g, '-'],
  [/—/g, '-'],
  [/×/g, '*'],
  [/÷/g, '/'],
  [/％/g, '%'],
  [/π/g, 'pi']
]

const FUNCTION_ALIASES = {
  COS: 'cos',
  SIN: 'sin',
  TAN: 'tan',
  ACOS: 'acos',
  ASIN: 'asin',
  ATAN: 'atan',
  ABS: 'abs',
  SQRT: 'sqrt',
  LOG: 'log10',
  LN: 'log',
  EXP: 'exp',
  POW: 'pow',
  MIN: 'min',
  MAX: 'max',
  ROUND: 'round',
  FLOOR: 'floor',
  CEIL: 'ceil'
}

const RESERVED_IDENTIFIERS = new Set([
  'pi',
  'e',
  ...Object.keys(FUNCTION_ALIASES),
  ...Object.values(FUNCTION_ALIASES)
])
const EXCEL_FUNCTION_NAMES = ['VLOOKUP', 'HLOOKUP', 'IF', 'IFERROR']
const CURVE_FUNCTION_NAMES = ['CURVE2D', 'DRN', 'LINEAR', 'X2Y', '电机扭矩']
const EQUIP_FUNCTION_NAMES = ['SELECT_EQUIP']
const SPECIAL_FUNCTION_NAMES = [...EXCEL_FUNCTION_NAMES, ...CURVE_FUNCTION_NAMES, ...EQUIP_FUNCTION_NAMES, '参数表']

export const ALL_RESERVED_IDENTIFIERS = new Set([
  ...RESERVED_IDENTIFIERS,
  ...SPECIAL_FUNCTION_NAMES,
  ...EXCEL_FUNCTION_NAMES,
  ...CURVE_FUNCTION_NAMES,
  ...EQUIP_FUNCTION_NAMES
])

export class FormulaEngineError extends Error {
  constructor(code, message, details = {}) {
    super(message)
    this.name = 'FormulaEngineError'
    this.code = code
    this.details = details
  }
}

const formatNumber = (value, precision) => Number(Number(value).toFixed(precision)).toString()
const isNumberLiteral = (token) => {
  const normalized = String(token ?? '').trim()
  if (!normalized) return false
  return Number.isFinite(Number(normalized))
}

const formatLookupKey = (value) => {
  const numericValue = Number(value)
  if (Number.isInteger(numericValue)) {
    return String(numericValue)
  }
  return Number(numericValue).toString()
}

const replaceSegment = (expression, start, end, replacement) => (
  `${expression.slice(0, start)}${replacement}${expression.slice(end)}`
)

const splitFunctionArgs = (text = '') => {
  const args = []
  let current = ''
  let depth = 0
  for (const char of String(text || '')) {
    if (char === ',' && depth === 0) {
      args.push(current.trim())
      current = ''
      continue
    }
    if (char === '(') {
      depth += 1
    } else if (char === ')') {
      depth -= 1
    }
    current += char
  }
  if (current) {
    args.push(current.trim())
  }
  return args
}

function resolveLookupReference(token = '') {
  const matched = String(token).trim().match(/^([\u00C0-\uFFFFA-Za-z0-9_]+)!(\$?[A-Z]+\$?(?::\$?[A-Z]+\$?)?)$/)
  if (!matched) {
    throw new FormulaEngineError('FUNCTION_ARGUMENT_INVALID', `非法附录引用: ${token}`)
  }
  return { lookupName: matched[1], rangeRef: matched[2] }
}

export function normalizeFormulaExpression(input) {
  let expression = String(input ?? '').trim()
  if (expression.startsWith('=')) {
    expression = expression.slice(1).trim()
  }

  for (const [pattern, replacement] of SYMBOL_REPLACEMENTS) {
    expression = expression.replace(pattern, replacement)
  }

  expression = expression.replace(/\bPI\b/gi, 'pi')

  for (const [alias, canonical] of Object.entries(FUNCTION_ALIASES)) {
    const matcher = new RegExp(`\\b${alias}\\b(?=\\s*\\()`, 'gi')
    expression = expression.replace(matcher, canonical)
  }

  expression = expression.replace(/\s*([+\-*/^%,()])\s*/g, '$1')
  return expression.trim()
}

export function resolveVariables(expression, scope, options = {}) {
  const availableVariableNames = options.availableVariableNames || []
  const explicitVariables = Array.from(new Set([
    ...availableVariableNames.filter(Boolean),
    ...Object.keys(scope)
  ]))

  let processedExpression = expression
  const mappedScope = {}
  let index = 0

  const extractedTokens = []
  const tokenRegex = /([A-Za-z_\u00C0-\uFFFF][A-Za-z0-9_\u00C0-\uFFFF]*)\s*(\()?/g
  let match
  while ((match = tokenRegex.exec(processedExpression)) !== null) {
    if (!match[2]) {
      extractedTokens.push(match[1])
    }
  }

  const allVariableTokens = Array.from(new Set(
    extractedTokens.filter(token => !RESERVED_IDENTIFIERS.has(token) && !/^__var_\d+__$/.test(token))
  ))

  const variableNames = Array.from(new Set([...explicitVariables, ...allVariableTokens]))
    .sort((left, right) => right.length - left.length)

  const variableMap = new Map()
  for (const variableName of variableNames) {
    if (!processedExpression.includes(variableName)) {
      continue
    }

    if (!(variableName in scope)) {
      // 隐式注册：凡是合法的可用变量，若作用域缺失，自动补齐默认值 0
      scope[variableName] = options.defaultMissingValue ?? 0
    }

    const safeIdentifier = `__var_${index}__`
    processedExpression = processedExpression.split(variableName).join(safeIdentifier)
    mappedScope[safeIdentifier] = scope[variableName]
    index += 1
  }

  return { processedExpression, mappedScope, extractedVariableNames: variableNames.filter(v => expression.includes(v)) }
}

function mapEvaluationError(error) {
  const message = error?.message || '公式计算失败'

  if (/Undefined function/i.test(message)) {
    throw new FormulaEngineError('FUNCTION_UNKNOWN', `未知函数: ${message}`, { cause: error })
  }

  if (/Parenthesis|Value expected|Unexpected part|Unexpected end of expression/i.test(message)) {
    throw new FormulaEngineError('SYNTAX_ERROR', `表达式格式错误: ${message}`, { cause: error })
  }

  throw new FormulaEngineError('EVALUATION_ERROR', message, { cause: error })
}

function resolveTokenValue(token, scope, options = {}) {
  const normalized = String(token ?? '').trim()
  if (isNumberLiteral(normalized)) {
    return Number(normalized)
  }
  const normalizedUpper = normalized.toUpperCase()
  if (normalizedUpper === 'TRUE') {
    return 'TRUE'
  }
  if (normalizedUpper === 'FALSE') {
    return 'FALSE'
  }
  if (Object.prototype.hasOwnProperty.call(scope, normalized)) {
    return scope[normalized]
  }
  return evaluateFormulaExpression(normalized, scope, {
    ...options,
    availableVariableNames: options.availableVariableNames || Object.keys(scope || {})
  }).value
}

function evaluateCondition(expression, scope, options = {}) {
  const condition = String(expression ?? '').trim()
  for (const operator of ['>=', '<=', '<>', '>', '<', '=']) {
    if (!condition.includes(operator)) {
      continue
    }
    const [leftText, rightText] = condition.split(operator, 2)
    const left = resolveTokenValue(leftText, scope, options)
    const right = resolveTokenValue(rightText, scope, options)
    if (operator === '>=') return left >= right
    if (operator === '<=') return left <= right
    if (operator === '<>') return left !== right
    if (operator === '>') return left > right
    if (operator === '<') return left < right
    return left === right
  }
  return Boolean(resolveTokenValue(condition, scope, options))
}

function replaceOneExcelFunction(expression, scope, options = {}) {
  for (let index = 0; index < expression.length; index += 1) {
    if (expression[index] !== '(') {
      continue
    }
    let nameStart = index - 1
    while (nameStart >= 0 && /[A-Za-z0-9_]/.test(expression[nameStart])) {
      nameStart -= 1
    }
    const functionName = expression.slice(nameStart + 1, index).toUpperCase()
    if (!SPECIAL_FUNCTION_NAMES.includes(functionName)) {
      continue
    }

    let depth = 1
    let closeIndex = index
    while (closeIndex + 1 < expression.length && depth > 0) {
      closeIndex += 1
      if (expression[closeIndex] === '(') {
        depth += 1
      } else if (expression[closeIndex] === ')') {
        depth -= 1
      }
    }
    if (depth !== 0) {
      throw new FormulaEngineError('SYNTAX_ERROR', `${functionName} 括号未闭合`)
    }

    const functionStart = nameStart + 1
    const args = splitFunctionArgs(expression.slice(index + 1, closeIndex))

    if (functionName === 'CURVE2D') {
      if (args.length !== 5) {
        throw new FormulaEngineError('FUNCTION_ARGUMENT_INVALID', 'CURVE2D 需要 5 个参数')
      }
      const lookupName = String(args[0] || '').trim()
      const inputValue = resolveTokenValue(args[1], scope, options)
      const seriesKey = String(args[2] || '').trim()
      const direction = String(args[3] || '').trim().toUpperCase()
      const lookupMode = String(args[4] || '').trim().toUpperCase()
      if (!['X2Y', 'Y2X'].includes(direction)) {
        throw new FormulaEngineError('CURVE_DIRECTION_INVALID', `CURVE2D 不支持的查值方向: ${direction}`)
      }
      if (lookupMode !== 'LINEAR') {
        throw new FormulaEngineError('CURVE_LOOKUP_MODE_INVALID', `CURVE2D 不支持的查值方式: ${lookupMode}`)
      }
      if (typeof options.curveResolver !== 'function') {
        throw new FormulaEngineError('CURVE_PROFILE_MISSING', `曲线表“${lookupName}”不可用`)
      }
      const resolved = options.curveResolver(lookupName, inputValue, seriesKey, direction, lookupMode)
      const resolvedValue = typeof resolved === 'object' && resolved !== null ? resolved.value : resolved
      return replaceSegment(expression, functionStart, closeIndex + 1, String(Number(resolvedValue)))
    }

    if (functionName === 'SELECT_EQUIP') {
      if (args.length !== 3) {
        throw new FormulaEngineError('FUNCTION_ARGUMENT_INVALID', 'SELECT_EQUIP 需要 3 个参数')
      }
      const categoryCode = String(args[0] || '').trim().replace(/^['"]|['"]$/g, '')
      const matchProperty = String(args[1] || '').trim().replace(/^['"]|['"]$/g, '')
      const targetValue = resolveTokenValue(args[2], scope, options)
      
      // 前端公式引擎在计算时，SELECT_EQUIP 实际上返回的是目标值本身，
      // 真正的选型推荐逻辑在组件层通过 fetchEquipmentRecommendations 处理。
      // 这样可以保证公式计算的连贯性，同时触发 UI 层的推荐。
      return replaceSegment(expression, functionStart, closeIndex + 1, String(Number(targetValue)))
    }

    if (functionName === 'VLOOKUP' || functionName === 'HLOOKUP') {
      if (args.length !== 4) {
        throw new FormulaEngineError('FUNCTION_ARGUMENT_INVALID', `${functionName} 需要 4 个参数`)
      }
      const lookupValue = resolveTokenValue(args[0], scope, options)
      const { lookupName } = resolveLookupReference(args[1])
      const resultIndex = Number(resolveTokenValue(args[2], scope, options))
      const rangeModeValue = resolveTokenValue(args[3], scope, options)
      const rangeMode = typeof rangeModeValue === 'number'
        ? (rangeModeValue === 0 ? '0' : String(rangeModeValue))
        : String(rangeModeValue).trim().toUpperCase()
      if (resultIndex !== 2) {
        throw new FormulaEngineError('LOOKUP_COLUMN_INVALID', `${functionName} 首期只支持第 2 列`)
      }
      if (!['0', 'FALSE'].includes(rangeMode)) {
        throw new FormulaEngineError('LOOKUP_RANGE_MODE_INVALID', `${functionName} 首期只支持精确匹配 0/FALSE`)
      }
      if (typeof options.lookupResolver !== 'function') {
        throw new FormulaEngineError('LOOKUP_NOT_FOUND', `附录“${lookupName}”不可用`)
      }
      const resolved = Number(options.lookupResolver(lookupName, formatLookupKey(lookupValue), 2, true))
      return replaceSegment(expression, functionStart, closeIndex + 1, String(resolved))
    }

    if (functionName === 'IF') {
      if (args.length !== 3) {
        throw new FormulaEngineError('FUNCTION_ARGUMENT_INVALID', 'IF 需要 3 个参数')
      }
      const branch = evaluateCondition(args[0], scope, options) ? args[1] : args[2]
      const value = resolveTokenValue(branch, scope, options)
      if (typeof value === 'string' && !isNumberLiteral(value)) {
        throw new FormulaEngineError('RESULT_INVALID', `IF 返回的结果不是有效数字: ${value}`)
      }
      return replaceSegment(expression, functionStart, closeIndex + 1, String(Number(value)))
    }

    if (args.length !== 2) {
      throw new FormulaEngineError('FUNCTION_ARGUMENT_INVALID', 'IFERROR 需要 2 个参数')
    }
    let value
    try {
      value = resolveTokenValue(args[0], scope, options)
    } catch {
      value = resolveTokenValue(args[1], scope, options)
    }
    return replaceSegment(expression, functionStart, closeIndex + 1, String(Number(value)))
  }
  return expression
}

function resolveExcelFunctions(expression, scope, options = {}) {
  let resolved = expression
  while (SPECIAL_FUNCTION_NAMES.some((name) => resolved.toUpperCase().includes(`${name}(`))) {
    const nextExpression = replaceOneExcelFunction(resolved, scope, options)
    if (nextExpression === resolved) {
      break
    }
    resolved = nextExpression
  }
  return resolved
}

export function evaluateFormulaExpression(input, scope = {}, options = {}) {
  const normalizedExpression = normalizeFormulaExpression(input)
  if (!normalizedExpression) {
    return {
      value: null,
      formattedValue: '',
      normalizedExpression: '',
      processedExpression: '',
      mappedScope: {}
    }
  }

  const excelReadyExpression = resolveExcelFunctions(normalizedExpression, scope, options)
  const { processedExpression, mappedScope, extractedVariableNames } = resolveVariables(
    excelReadyExpression,
    scope,
    options
  )

  if (typeof options.onVariableExtracted === 'function') {
    extractedVariableNames.forEach(name => options.onVariableExtracted(name))
  }

  try {
    const value = math.evaluate(processedExpression, mappedScope)
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      throw new FormulaEngineError('RESULT_INVALID', '计算结果不是有效数字', { value })
    }

    return {
      value,
      formattedValue: formatNumber(value, options.precision ?? 4),
      normalizedExpression,
      processedExpression,
      mappedScope,
      extractedVariableNames
    }
  } catch (error) {
    if (error instanceof FormulaEngineError) {
      throw error
    }
    mapEvaluationError(error)
  }
}

export function evaluateFormulaRows(rows = [], options = {}) {
  const precision = options.precision ?? 4
  const baseScope = { ...(options.baseScope || {}) }
  const formulaMap = new Map()
  const resolvedValues = {}

  rows.forEach((row) => {
    const rowName = String(row?.name || '').trim()
    if (rowName) {
      formulaMap.set(rowName, row)
    }
    row.value = ''
    row.error = false
    row.errorMessage = ''

    if (!row?.expression) {
      return
    }

    const exprStr = String(row.expression).trim()
    if (!exprStr.startsWith('=')) {
      row.value = exprStr
      row.error = false
      row.errorMessage = ''

      const numericValue = Number(exprStr)
      if (row.name && Number.isFinite(numericValue)) {
        resolvedValues[row.name] = numericValue
      }
      return
    }
  })

  const inferDependencyNames = (rowName, expression) => {
    const explicitVariables = Object.keys(options.variableMap?.[rowName] || {})
    if (explicitVariables.length) {
      return explicitVariables
    }
    return Array.from(formulaMap.keys())
      .filter((name) => name && name !== rowName && expression.includes(name))
      .sort((left, right) => right.length - left.length)
  }

  const resolveRow = (row, stack = []) => {
    const rowName = String(row?.name || '').trim()
    if (rowName && Object.prototype.hasOwnProperty.call(resolvedValues, rowName)) {
      return resolvedValues[rowName]
    }
    if (rowName && stack.includes(rowName)) {
      throw new FormulaEngineError(
        'CIRCULAR_DEPENDENCY',
        `公式存在循环依赖: ${[...stack, rowName].join(' -> ')}`
      )
    }

    const expression = String(row?.expression || '').trim()
    if (!expression) {
      return null
    }
    if (!expression.startsWith('=')) {
      const numericValue = Number(expression)
      if (rowName && Number.isFinite(numericValue)) {
        resolvedValues[rowName] = numericValue
      }
      return numericValue
    }

    const variableNames = inferDependencyNames(rowName, expression)
    const scope = { ...baseScope, ...resolvedValues }
    for (const variableName of variableNames) {
      if (Object.prototype.hasOwnProperty.call(scope, variableName)) {
        continue
      }
      if (formulaMap.has(variableName)) {
        scope[variableName] = resolveRow(formulaMap.get(variableName), [...stack, rowName])
      }
    }

    const fallbackVariableNames = Array.from(new Set([
      ...Object.keys(baseScope),
      ...formulaMap.keys()
    ])).sort((left, right) => right.length - left.length)
    const result = evaluateFormulaExpression(expression, scope, {
      availableVariableNames: variableNames.length ? variableNames : fallbackVariableNames,
      precision
    })
    row.value = result.formattedValue
    row.error = false
    row.errorMessage = ''
    if (rowName) {
      resolvedValues[rowName] = result.value
    }
    return result.value
  }

  for (const row of rows) {
    const exprStr = String(row?.expression || '').trim()
    if (!exprStr || !exprStr.startsWith('=')) {
      continue
    }
    try {
      resolveRow(row, [])
    } catch (error) {
      row.value = 'Error'
      row.error = true
      row.errorMessage = error?.message || '公式计算失败'
    }
  }

  return {
    rows,
    resolvedValues,
    availableVariableNames: Array.from(new Set([
      ...Object.keys(baseScope),
      ...formulaMap.keys()
    ]))
  }
}
