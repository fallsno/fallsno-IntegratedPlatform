const containsAny = (text = '', keywords = []) => keywords.some((keyword) => text.includes(keyword))

const INPUT_GROUP_LABELS = Object.freeze({
  condition: '工况参数',
  structure: '滚筒结构',
  selection: '选型输入参数',
  general: '基础参数',
  custom: '自定义参数'
})

const normalizeCustomGroup = (row = {}) => {
  const directKey = String(row.customGroupKey || '').trim()
  const directLabel = String(row.customGroupLabel || '').trim()
  if (directKey) {
    return {
      key: directKey,
      label: directLabel || INPUT_GROUP_LABELS[directKey] || '自定义分组'
    }
  }

  let provenance = row.provenance
  if (!provenance && row.remark) {
    try {
      provenance = JSON.parse(String(row.remark || ''))
    } catch (_error) {
      provenance = null
    }
  }

  const provenanceKey = String(provenance?.custom_group_key || '').trim()
  const provenanceLabel = String(provenance?.custom_group_label || '').trim()
  if (provenanceKey) {
    return {
      key: provenanceKey,
      label: provenanceLabel || INPUT_GROUP_LABELS[provenanceKey] || '自定义分组'
    }
  }

  return null
}

export function resolveWorkbenchTreeGroup(row = {}, treeKind = 'input') {
  const normalizedTreeKind = String(treeKind || 'input').trim()
  const paramName = String(row.paramName || '').trim()
  const categoryCode = String(row.categoryCode || '').trim().toLowerCase()
  const valueType = String(row.valueType || '').trim().toLowerCase()
  const displayName = String(row.displayName || row.paramName || '').trim()
  const lookupText = `${paramName} ${categoryCode} ${valueType} ${displayName}`.toLowerCase()

  if (normalizedTreeKind === 'selection') {
    if (lookupText.startsWith('电机_') || containsAny(lookupText, ['电机', 'motor'])) {
      return { key: 'motor', label: '电机选型参数' }
    }
    if (lookupText.startsWith('减速机_') || containsAny(lookupText, ['减速机', '减速', 'gear', 'reducer'])) {
      return { key: 'reducer', label: '减速机选型参数' }
    }
    if (containsAny(lookupText, ['轴承', 'bearing'])) {
      return { key: 'bearing', label: '轴承选型参数' }
    }
    return { key: 'selection-general', label: '当前型号选型参数' }
  }

  const customGroup = normalizeCustomGroup(row)
  if (customGroup) {
    return customGroup
  }

  if (row.pendingCreate || row.source === 'draft') {
    return { key: 'custom', label: '自定义参数' }
  }

  if (containsAny(lookupText, ['condition', '工况', '产量', '角度', '摩擦', '粘料', '时间'])) {
    return { key: 'condition', label: '工况参数' }
  }
  if (containsAny(lookupText, ['structure', '滚筒', '筒体', '滚圈', 'shell', 'barrel'])) {
    return { key: 'structure', label: '滚筒结构' }
  }
  if (containsAny(lookupText, ['selection', '选型'])) {
    return { key: 'selection', label: '选型输入参数' }
  }

  return { key: categoryCode || valueType || 'general', label: '基础参数' }
}
