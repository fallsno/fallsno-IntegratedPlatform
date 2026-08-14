const CATEGORY_ORDER = ['virgin', 'recycled', 'drymix', 'unknown']

const CATEGORY_LABELS = {
  virgin: '原生滚筒',
  recycled: '再生滚筒',
  drymix: '干混滚筒',
  unknown: '其他型号'
}

const MODEL_RULES = [
  {
    key: 'AT',
    familyCodes: ['AT'],
    match: /^AT(\d+)$/i,
    categoryKey: 'virgin',
    categoryLabel: '原生滚筒',
    subtypeLabel: '原生',
    namingLabel: '新版',
    capacityMap: { 120: 1500, 160: 2000, 240: 3000, 320: 4000, 400: 5000 }
  },
  {
    key: 'GT',
    familyCodes: ['GT'],
    match: /^GT(\d+)$/i,
    categoryKey: 'virgin',
    categoryLabel: '原生滚筒',
    subtypeLabel: '原生',
    namingLabel: '旧版',
    capacityMap: { 120: 1500, 160: 2000, 240: 3000, 320: 4000, 400: 5000 }
  },
  {
    key: 'RT',
    familyCodes: ['RT'],
    match: /^RT(\d+)$/i,
    categoryKey: 'recycled',
    categoryLabel: '再生滚筒',
    subtypeLabel: '顺流再生',
    namingLabel: '新版',
    capacityMap: { 80: 1500, 130: 2000, 200: 3000, 300: 4000 }
  },
  {
    key: 'GTR',
    familyCodes: ['GTR'],
    match: /^GTR(\d+)$/i,
    categoryKey: 'recycled',
    categoryLabel: '再生滚筒',
    subtypeLabel: '顺流再生',
    namingLabel: '旧版',
    capacityMap: { 80: 1500, 130: 2000, 200: 3000, 300: 4000 }
  },
  {
    key: 'HTS',
    familyCodes: ['HTS'],
    match: /^HTS(\d+)$/i,
    categoryKey: 'recycled',
    categoryLabel: '再生滚筒',
    subtypeLabel: '逆流全再生',
    namingLabel: '新版',
    capacityMap: { 200: 3000, 300: 4000 }
  },
  {
    key: 'GTRQ',
    familyCodes: ['GTRQ'],
    match: /^GTRQ(\d+)$/i,
    categoryKey: 'recycled',
    categoryLabel: '再生滚筒',
    subtypeLabel: '逆流全再生',
    namingLabel: '旧版',
    capacityMap: { 200: 3000, 300: 4000 }
  },
  {
    key: 'CTD',
    familyCodes: ['CTD'],
    match: /^CTD(\d+)$/i,
    categoryKey: 'drymix',
    categoryLabel: '干混滚筒',
    subtypeLabel: '干混',
    namingLabel: '新版'
  },
  {
    key: 'GFT',
    familyCodes: ['GFT'],
    match: /^GFT(\d+)$/i,
    categoryKey: 'drymix',
    categoryLabel: '干混滚筒',
    subtypeLabel: '干混',
    namingLabel: '旧版'
  }
]

function normalizeToken(value = '') {
  return String(value || '').trim().toUpperCase()
}

function extractNumber(value = '') {
  const matched = String(value || '').match(/(\d+(?:\.\d+)?)/)
  if (!matched) return null
  const parsed = Number(matched[1])
  return Number.isFinite(parsed) ? parsed : null
}

function findRule(versionCode = '', familyCode = '') {
  const normalizedVersionCode = normalizeToken(versionCode)
  const normalizedFamilyCode = normalizeToken(familyCode)

  return (
    MODEL_RULES.find((rule) => rule.match.test(normalizedVersionCode)) ||
    MODEL_RULES.find((rule) => rule.familyCodes.includes(normalizedFamilyCode)) ||
    null
  )
}

function resolveCapacity(rule, version = {}, rawNumber = null) {
  if (rule?.capacityMap && rawNumber != null && Object.prototype.hasOwnProperty.call(rule.capacityMap, rawNumber)) {
    return rule.capacityMap[rawNumber]
  }
  if (Number.isFinite(Number(version.capacity_value))) {
    return Number(version.capacity_value)
  }
  if (Number.isFinite(Number(version.machine_model))) {
    return Number(version.machine_model)
  }
  return rawNumber
}

function buildCapacityLabel(rule, capacityValue) {
  if (!Number.isFinite(Number(capacityValue))) return '产量待补充'
  if (rule?.categoryKey === 'drymix') {
    return `${Number(capacityValue)}吨型`
  }
  return `${Number(capacityValue)}型`
}

export function getParameterCenterCategoryOrder() {
  return [...CATEGORY_ORDER]
}

export function getParameterCenterCategoryLabel(categoryKey = '') {
  return CATEGORY_LABELS[categoryKey] || CATEGORY_LABELS.unknown
}

export function resolveParameterCenterModelMeta(version = {}) {
  const versionCode = String(version.version_code || version.display_name || '').trim()
  const familyCode = String(version.family_code || '').trim()
  const rule = findRule(versionCode, familyCode)
  const rawNumber = extractNumber(versionCode) ?? extractNumber(version.display_name) ?? extractNumber(version.machine_model)
  const capacityValue = resolveCapacity(rule, version, rawNumber)
  const categoryKey = rule?.categoryKey || (String(version.family_category || '').includes('原生') ? 'virgin' : String(version.family_category || '').includes('再生') ? 'recycled' : String(version.family_category || '').includes('干混') ? 'drymix' : 'unknown')
  const categoryLabel = rule?.categoryLabel || version.family_category || getParameterCenterCategoryLabel(categoryKey)
  const subtypeLabel = rule?.subtypeLabel || version.product_type_name || ''
  const namingLabel = rule?.namingLabel || ''
  const capacityLabel = buildCapacityLabel(rule, capacityValue)
  const familyLabel = [categoryLabel, subtypeLabel, familyCode].filter(Boolean).join(' / ')
  const meaning = [categoryLabel, subtypeLabel, namingLabel, capacityLabel].filter(Boolean).join(' / ')

  return {
    ...version,
    categoryKey,
    categoryLabel,
    subtypeLabel,
    namingLabel,
    capacityValue: Number.isFinite(Number(capacityValue)) ? Number(capacityValue) : null,
    capacityLabel,
    familyLabel,
    meaning,
    sortValue: Number.isFinite(Number(capacityValue)) ? Number(capacityValue) : Number.MAX_SAFE_INTEGER,
    sortRank: CATEGORY_ORDER.indexOf(categoryKey),
    isKnownModel: Boolean(rule)
  }
}

export function detectParameterTrendAnomalies(rows = []) {
  const numericRows = rows
    .map((item, index) => ({
      ...item,
      numericValue: Number(item.value),
      sourceIndex: index
    }))
    .filter((item) => Number.isFinite(item.numericValue))

  const anomalies = new Set()
  if (numericRows.length < 3) return anomalies

  for (let index = 1; index < numericRows.length - 1; index += 1) {
    const prev = numericRows[index - 1]
    const current = numericRows[index]
    const next = numericRows[index + 1]
    const expected = (prev.numericValue + next.numericValue) / 2
    const delta = Math.abs(current.numericValue - expected)
    const tolerance = Math.max(Math.abs(expected) * 0.18, 1e-6)
    if (delta > tolerance) {
      anomalies.add(current.sourceIndex)
    }
  }

  return anomalies
}
