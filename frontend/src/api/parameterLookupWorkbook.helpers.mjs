const normalizeText = (value) => String(value || '').trim()

const buildNormalizedMap = (items = [], keyGetter) =>
  (Array.isArray(items) ? items : []).reduce((accumulator, item) => {
    const normalizedKey = normalizeText(keyGetter(item)).toLowerCase()
    if (normalizedKey) {
      accumulator.set(normalizedKey, item)
    }
    return accumulator
  }, new Map())

export function detectRt300WorkbookSheets(sheetNames = []) {
  const normalizedMap = buildNormalizedMap(sheetNames, (item) => item)
  const lookupSheet = normalizedMap.get('电机扭矩参数')
  const matrixSheet = normalizedMap.get('滚筒电机核算') || normalizedMap.get('sew电机核算')

  return {
    workbookType: lookupSheet && matrixSheet ? 'rt300' : 'generic',
    lookupSheetName: lookupSheet || '',
    matrixSheetName: matrixSheet || ''
  }
}

export function buildEmptyOnlyMatrixImportRows(previewRows = [], existingMatrixRows = [], versions = []) {
  const existingRowsByName = buildNormalizedMap(existingMatrixRows, (item) => item?.paramName)
  const versionsByCode = buildNormalizedMap(versions, (item) => item?.version_code)

  let keptValueCount = 0
  let skippedValueCount = 0

  const parameterRows = (Array.isArray(previewRows) ? previewRows : []).reduce((accumulator, row) => {
    const existingRow = existingRowsByName.get(normalizeText(row?.paramName).toLowerCase())
    const nextValues = Object.entries(row?.values || {}).reduce((valueAccumulator, [versionCode, rawValue]) => {
      const normalizedValue = normalizeText(rawValue)
      if (!normalizedValue) {
        return valueAccumulator
      }

      const matchedVersion = versionsByCode.get(normalizeText(versionCode).toLowerCase())
      const existingValue = matchedVersion
        ? normalizeText(existingRow?.values?.[matchedVersion.id])
        : ''

      if (existingValue) {
        skippedValueCount += 1
        return valueAccumulator
      }

      valueAccumulator[versionCode] = normalizedValue
      keptValueCount += 1
      return valueAccumulator
    }, {})

    if (!Object.keys(nextValues).length) {
      return accumulator
    }

    accumulator.push({
      paramName: normalizeText(row?.paramName),
      unitCode: normalizeText(row?.unitCode),
      categoryName: normalizeText(row?.categoryName),
      values: nextValues
    })
    return accumulator
  }, [])

  return {
    parameterRows,
    keptValueCount,
    skippedValueCount
  }
}
