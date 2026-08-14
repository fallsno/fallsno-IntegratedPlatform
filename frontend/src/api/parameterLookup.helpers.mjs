export function normalizeParameterLookupForm(form = {}) {
  return {
    lookup_code: String(form.lookup_code || '').trim(),
    lookup_name: String(form.lookup_name || '').trim(),
    description: String(form.description || '').trim(),
    status: String(form.status || 'active').trim() || 'active'
  }
}

export function normalizeParameterLookupRows(rows = []) {
  return (Array.isArray(rows) ? rows : [])
    .filter((row) => String(row?.lookup_key || '').trim() || String(row?.result_value || '').trim())
    .map((row, index) => ({
      lookup_key: String(row.lookup_key || '').trim(),
      result_value: String(row.result_value || '').trim(),
      sort_order: index,
      remark: String(row.remark || '').trim()
    }))
}

export function normalizeParameterLookupPreview(payload = {}) {
  return {
    rows: normalizeParameterLookupRows(payload.rows || []),
    errors: Array.isArray(payload.errors) ? payload.errors : [],
    table_columns: normalizeUniqueTextList(payload.table_columns || []),
    table_rows: (Array.isArray(payload.table_rows) ? payload.table_rows : []).map((row) =>
      Object.entries(row || {}).reduce((accumulator, [key, value]) => {
        const normalizedKey = normalizeText(key)
        if (!normalizedKey) return accumulator
        accumulator[normalizedKey] = normalizeText(value)
        return accumulator
      }, {})
    )
  }
}

const normalizeText = (value) => String(value || '').trim()

const normalizeUniqueTextList = (items = []) => {
  const seen = new Set()
  return (Array.isArray(items) ? items : []).reduce((accumulator, item) => {
    const text = normalizeText(item)
    if (!text || seen.has(text)) return accumulator
    seen.add(text)
    accumulator.push(text)
    return accumulator
  }, [])
}

export function normalizeParameterLookupCurveProfile(form = {}) {
  return {
    profile_name: normalizeText(form.profile_name),
    x_axis_column: normalizeText(form.x_axis_column),
    table_columns: normalizeUniqueTextList(form.table_columns || []),
    table_rows: (Array.isArray(form.table_rows) ? form.table_rows : []).map((row) =>
      Object.entries(row || {}).reduce((accumulator, [key, value]) => {
        const normalizedKey = normalizeText(key)
        if (!normalizedKey) return accumulator
        accumulator[normalizedKey] = normalizeText(value)
        return accumulator
      }, {})
    ),
    series_columns: (Array.isArray(form.series_columns) ? form.series_columns : [])
      .map((item) => ({
        series_key: normalizeText(item?.series_key),
        source_column: normalizeText(item?.source_column),
        reverse_lookup_enabled: Boolean(item?.reverse_lookup_enabled)
      }))
      .filter((item) => item.series_key && item.source_column),
    note_columns: normalizeUniqueTextList(form.note_columns || []),
    default_lookup_mode: normalizeText(form.default_lookup_mode) || 'LINEAR',
    allow_interpolation: form.allow_interpolation !== false
  }
}

export function normalizeParameterLookupCurvePreview(payload = {}) {
  return {
    lookup_id: Number(payload.lookup_id || 0),
    lookup_name: normalizeText(payload.lookup_name),
    profile_name: normalizeText(payload.profile_name),
    x_axis_column: normalizeText(payload.x_axis_column),
    warnings: Array.isArray(payload.warnings) ? payload.warnings.map((item) => normalizeText(item)).filter(Boolean) : [],
    series: (Array.isArray(payload.series) ? payload.series : []).map((item) => ({
      series_key: normalizeText(item?.series_key),
      source_column: normalizeText(item?.source_column),
      reverse_lookup_enabled: Boolean(item?.reverse_lookup_enabled),
      is_monotonic: Boolean(item?.is_monotonic),
      points: (Array.isArray(item?.points) ? item.points : [])
        .map((point) => ({
          x: Number(point?.x),
          y: Number(point?.y)
        }))
        .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y))
    }))
  }
}

export function buildCurveProfileDraftFromLookupRows(rows = [], base = {}) {
  const safeRows = normalizeParameterLookupRows(rows || [])
  const table_columns = ['查找值', '结果值', '备注']
  const table_rows = safeRows.map((row) => ({
    查找值: String(row.lookup_key || '').trim(),
    结果值: String(row.result_value || '').trim(),
    备注: String(row.remark || '')
  }))
  const series_columns = Array.isArray(base.series_columns)
    ? base.series_columns
        .map((item) => ({
          series_key: normalizeText(item?.series_key),
          source_column: normalizeText(item?.source_column),
          reverse_lookup_enabled: Boolean(item?.reverse_lookup_enabled)
        }))
        .filter((item) => item.series_key && item.source_column)
    : []
  return {
    profile_name: normalizeText(base.profile_name),
    x_axis_column: '查找值',
    table_columns,
    table_rows,
    series_columns,
    note_columns: ['备注'],
    default_lookup_mode: 'LINEAR',
    allow_interpolation: true
  }
}

export function buildCurveProfileDraftFromImportPreview(preview = {}, base = {}) {
  const normalizedPreview = normalizeParameterLookupPreview(preview)
  if (!normalizedPreview.table_columns.length || !normalizedPreview.table_rows.length) {
    return buildCurveProfileDraftFromLookupRows(normalizedPreview.rows || [], base)
  }
  const x_axis_column = normalizeText(base.x_axis_column) || normalizedPreview.table_columns[0] || ''
  const note_columns = normalizedPreview.table_columns.filter((column) => column.includes('备注'))
  const series_columns = Array.isArray(base.series_columns)
    ? base.series_columns
        .map((item) => ({
          series_key: normalizeText(item?.series_key),
          source_column: normalizeText(item?.source_column),
          reverse_lookup_enabled: Boolean(item?.reverse_lookup_enabled)
        }))
        .filter((item) => item.series_key && item.source_column)
    : []
  return {
    profile_name: normalizeText(base.profile_name),
    x_axis_column,
    table_columns: normalizedPreview.table_columns,
    table_rows: normalizedPreview.table_rows.map((row) => ({ ...row })),
    series_columns,
    note_columns,
    default_lookup_mode: normalizeText(base.default_lookup_mode) || 'LINEAR',
    allow_interpolation: base.allow_interpolation !== false
  }
}

export function buildAppendixChartTableModel(rows = [], profile = {}) {
  const normalizedProfile = normalizeParameterLookupCurveProfile(profile || {})
  if (normalizedProfile.table_columns.length && normalizedProfile.table_rows.length) {
    return {
      columns: [...normalizedProfile.table_columns],
      rows: normalizedProfile.table_rows.map((row) => ({ ...row })),
      mode: 'table'
    }
  }

  const fallback = buildCurveProfileDraftFromLookupRows(rows || [], {})
  return {
    columns: [...fallback.table_columns],
    rows: fallback.table_rows.map((row) => ({ ...row })),
    mode: 'rows'
  }
}

export function hasMeaningfulCurveProfileChange(nextProfile = {}, currentProfile = {}) {
  return JSON.stringify(normalizeParameterLookupCurveProfile(nextProfile || {})) !== JSON.stringify(normalizeParameterLookupCurveProfile(currentProfile || {}))
}

export function buildLookupCurveChartOption(preview = {}) {
  const normalizedPreview = normalizeParameterLookupCurvePreview(preview)
  return {
    animation: false,
    tooltip: {
      trigger: 'axis',
      confine: true
    },
    legend: {
      top: 0,
      itemWidth: 12,
      itemHeight: 8
    },
    grid: {
      left: 12,
      right: 18,
      top: 40,
      bottom: 14,
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: normalizedPreview.x_axis_column || 'X',
      scale: true,
      axisLabel: {
        hideOverlap: true
      }
    },
    yAxis: {
      type: 'value',
      name: 'Y',
      scale: true,
      axisLabel: {
        hideOverlap: true
      }
    },
    series: normalizedPreview.series.map((item) => ({
      name: item.series_key || item.source_column || '未命名曲线',
      type: 'line',
      smooth: false,
      showSymbol: true,
      symbolSize: 7,
      data: item.points.map((point) => [point.x, point.y])
    }))
  }
}
