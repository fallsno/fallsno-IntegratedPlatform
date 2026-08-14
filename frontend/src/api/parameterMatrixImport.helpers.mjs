export function normalizeMatrixPreview(payload = {}) {
  return {
    orientation: payload.orientation || 'parameters_in_rows',
    parameterHeaders: Array.isArray(payload.parameter_headers) ? payload.parameter_headers : [],
    versionHeaders: Array.isArray(payload.version_headers) ? payload.version_headers : [],
    rows: Array.isArray(payload.rows)
      ? payload.rows.map((row) => ({
          paramName: row?.param_name || '',
          unitCode: row?.unit_code || '',
          categoryName: row?.category_name || '',
          values: { ...(row?.values || {}) }
        }))
      : [],
    warnings: Array.isArray(payload.warnings) ? payload.warnings : []
  }
}

export function buildOrientationOptions() {
  return [
    { label: '自动识别', value: 'auto' },
    { label: '参数在行', value: 'parameters_in_rows' },
    { label: '参数在列', value: 'parameters_in_columns' }
  ]
}

export function buildMatrixPreviewTableRows(preview = {}) {
  const normalized = normalizeMatrixPreview(preview)
  return normalized.rows.map((row) => ({
    ...row,
    values: normalized.versionHeaders.reduce((acc, versionCode) => {
      acc[versionCode] = row.values?.[versionCode] ?? ''
      return acc
    }, {})
  }))
}
