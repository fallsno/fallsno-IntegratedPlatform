export const createPendingParameterRow = (tempId) => ({
  parameterId: 0,
  paramCode: '',
  paramName: '',
  displayName: '',
  unitCode: '',
  valueType: 'basic',
  value: '',
  dirty: true,
  source: 'draft',
  pendingCreate: true,
  _nameConfirmed: false,
  _tempId: String(tempId || '')
})

const normalizeParameterName = (value) => String(value ?? '').trim()

const isSelectionEquipmentParameterName = (value) => {
  const name = normalizeParameterName(value)
  return name.startsWith('电机_') || name.startsWith('减速机_')
}

const resolveParameterRowIdentity = (row = {}) => {
  const tempId = String(row._tempId ?? '').trim()
  if (tempId) {
    return { type: 'tempId', value: tempId }
  }

  const paramName = normalizeParameterName(row.paramName)
  if (paramName) {
    return { type: 'paramName', value: paramName }
  }

  const parameterId = Number(row.parameterId || 0)
  if (Number.isFinite(parameterId) && parameterId > 0) {
    return { type: 'parameterId', value: String(parameterId) }
  }

  return { type: 'none', value: '' }
}

export const isSameParameterRow = (left = {}, right = {}) => {
  const leftIdentity = resolveParameterRowIdentity(left)
  const rightIdentity = resolveParameterRowIdentity(right)

  return leftIdentity.type !== 'none' &&
    leftIdentity.type === rightIdentity.type &&
    leftIdentity.value === rightIdentity.value
}

export const findParameterRowIndex = (rows = [], row = {}) => rows.findIndex((candidate) => isSameParameterRow(candidate, row))

export const removeParameterRow = (rows = [], row = {}) => {
  const targetIndex = findParameterRowIndex(rows, row)
  if (targetIndex < 0) {
    return [...rows]
  }
  return rows.filter((_, index) => index !== targetIndex)
}

export const resolveParameterDisplayName = (row = {}, fallbackName = '') => {
  const explicitDisplayName = String(row.displayName ?? '').trim()
  if (explicitDisplayName) {
    return explicitDisplayName
  }

  const explicitParamName = String(row.paramName ?? '').trim()
  if (explicitParamName) {
    return explicitParamName
  }

  if (row.pendingCreate || row._tempId) {
    return ''
  }

  return String(fallbackName ?? '').trim()
}

export const shouldPersistParameterRow = (row = {}) => {
  const paramName = normalizeParameterName(row.paramName)
  if (!paramName) return false
  if (String(row.valueType || '').trim() === 'equipment') return false
  if (isSelectionEquipmentParameterName(paramName)) return false
  return true
}
