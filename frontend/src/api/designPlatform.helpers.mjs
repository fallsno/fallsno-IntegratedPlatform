const PINYIN_FALLBACK = {
  滚: 'GUN',
  筒: 'TONG',
  重: 'ZHONG',
  量: 'LIANG',
  进: 'JIN',
  料: 'LIAO',
  摩: 'MO',
  擦: 'CA',
  系: 'XI',
  数: 'SHU',
  转: 'ZHUAN',
  速: 'SU'
}

export function normalizeParameterForm(form = {}) {
  return {
    param_code: form.param_code || '',
    param_name: form.param_name || '',
    display_name: form.display_name || form.param_name || '',
    category_code: form.category_code || 'uncategorized',
    value_type: form.value_type || 'basic',
    data_type: form.data_type || 'number',
    unit_code: form.unit_code || '',
    precision: Number(form.precision ?? 2),
    default_value: form.default_value == null ? '' : String(form.default_value),
    description: form.description || '',
    status: form.status || 'active'
  }
}

export function buildParameterCode(paramName = '') {
  const normalized = String(paramName || '').trim()
  if (!normalized) return 'PARAM_UNNAMED'
  const tokens = [...normalized].map((char) => PINYIN_FALLBACK[char] || char.charCodeAt(0))
  return `PARAM_${tokens.join('_')}`.toUpperCase()
}

export function buildParameterQuery(filters = {}) {
  const query = {}
  if (filters.keyword) query.keyword = filters.keyword
  if (filters.category_code) query.category_code = filters.category_code
  if (filters.module_code) query.module_code = filters.module_code
  return query
}

export function buildParameterDistributionRows(distribution = {}) {
  return (Array.isArray(distribution.values) ? distribution.values : []).map((item) => ({
    versionId: Number(item.version_id || item.versionId || 0),
    versionCode: item.version_code || item.versionCode || '',
    value: item.param_value == null ? '' : String(item.param_value)
  }))
}

export function buildFamilyMatrixPayload(rows = []) {
  return {
    rows: (Array.isArray(rows) ? rows : []).flatMap((row) => {
      const values = row?.values && typeof row.values === 'object' ? row.values : {}
      return Object.entries(values).map(([versionId, paramValue]) => ({
        version_id: Number(versionId),
        parameter_id: Number(row.parameter_id || 0),
        param_value: paramValue == null ? '' : String(paramValue)
      }))
    })
  }
}

export function buildWorkbenchSnapshotPayload(runKey, rows = []) {
  const normalizedRunKey = String(runKey || '').trim()
  if (!normalizedRunKey) {
    throw new Error('runKey is required')
  }
  return {
    run_key: normalizedRunKey,
    rows: (Array.isArray(rows) ? rows : []).map((row) => ({
      version_id: row?.version_id ?? null,
      parameter_id: Number(row?.parameter_id || 0),
      snapshot_value: row?.snapshot_value == null ? '' : String(row.snapshot_value)
    }))
  }
}

export function mergeWorkbenchCatalogRows({ catalogRows = [], matrixRows = [], snapshotMap = new Map() } = {}) {
  const catalogByName = new Map(
    (Array.isArray(catalogRows) ? catalogRows : []).map((row) => [row.param_name, row])
  )

  return (Array.isArray(matrixRows) ? matrixRows : []).map((row) => {
    if (row?.dirty || row?.source === 'draft') {
      return row
    }

    const catalog = catalogByName.get(row.paramName)
    const parameterId = Number(catalog?.id || row.parameterId || 0)
    const paramCode = catalog?.param_code || row.paramCode || buildParameterCode(row.paramName)
    const defaultValue = catalog?.default_value == null ? '' : String(catalog.default_value)

    if (snapshotMap instanceof Map && snapshotMap.has(parameterId)) {
      return {
        ...row,
        parameterId,
        paramCode,
        value: String(snapshotMap.get(parameterId) ?? ''),
        defaultValue,
        source: 'snapshot'
      }
    }

    if (defaultValue) {
      return {
        ...row,
        parameterId,
        paramCode,
        value: defaultValue,
        defaultValue,
        source: 'catalog'
      }
    }

    return {
      ...row,
      parameterId,
      paramCode,
      defaultValue
    }
  })
}

export function mergeWorkbenchModelRows({ modelRows = [], snapshotMap = new Map(), catalogRows = [] } = {}) {
  const catalogById = new Map(
    (Array.isArray(catalogRows) ? catalogRows : []).map((row) => [Number(row.id || 0), row])
  )

  return (Array.isArray(modelRows) ? modelRows : []).map((row) => {
    if (row?.dirty || row?.source === 'draft') {
      return row
    }

    const catalog = catalogById.get(Number(row.parameterId || 0))
    const defaultValue = catalog?.default_value == null ? '' : String(catalog.default_value)
    const hasModelValue = String(row?.value ?? '').trim() !== ''
    const hasSnapshotValue = snapshotMap instanceof Map && snapshotMap.has(row.parameterId)

    if (hasModelValue) {
      return {
        ...row,
        value: String(row.value ?? ''),
        defaultValue,
        source: 'model'
      }
    }

    if (hasSnapshotValue) {
      return {
        ...row,
        value: String(snapshotMap.get(row.parameterId) ?? ''),
        defaultValue,
        source: 'snapshot'
      }
    }

    if (defaultValue) {
      return {
        ...row,
        value: defaultValue,
        defaultValue,
        source: 'catalog'
      }
    }

    return {
      ...row,
      value: '',
      defaultValue,
      source: 'empty'
    }
  })
}

export function normalizeParameterStats(stats = {}) {
  return {
    min_value: stats.min_value || '',
    max_value: stats.max_value || '',
    avg_value: stats.avg_value || '',
    sample_count: Number(stats.sample_count || 0)
  }
}

export function normalizeTemplateDiffStats(stats = {}) {
  const addedFlows = Number(stats.added_flows || 0)
  const updatedSteps = Number(stats.updated_steps || 0)
  const affectedRows = Number(stats.affected_rows || 0)

  return {
    added_flows: addedFlows,
    updated_steps: updatedSteps,
    affected_rows: affectedRows,
    summary: `新增流程 ${addedFlows}，更新步骤 ${updatedSteps}，影响参数行 ${affectedRows}`
  }
}

export function normalizeGuidanceSummary(summary = {}) {
  return {
    raw: summary,
    cards: [
      { key: 'total', label: '规则命中', value: Number(summary.total_hits || 0) },
      { key: 'open', label: '待处理命中', value: Number(summary.open_hits || 0) },
      { key: 'actionOpen', label: '待执行动作', value: Number(summary.action_open_count || 0) },
      { key: 'actionResolved', label: '已完成动作', value: Number(summary.action_resolved_count || 0) }
    ]
  }
}

export function getGuidanceActionStatusMeta(status = 'open') {
  const current = String(status || 'open')
  if (current === 'resolved') return { type: 'success', label: '已完成' }
  if (current === 'dismissed') return { type: 'info', label: '已忽略' }
  if (current === 'in_progress') return { type: 'warning', label: '处理中' }
  return { type: 'danger', label: '待处理' }
}

export function normalizeGuidanceHit(hit = {}) {
  const actions = Array.isArray(hit.actions) ? hit.actions : []
  return {
    ...hit,
    actions,
    action_count: actions.length,
    open_action_count: actions.filter((item) => ['open', 'in_progress'].includes(item.status)).length
  }
}

export function buildGuidanceActionUpdatePayload({ status = 'open', resultNote = '', resultSnapshot = null } = {}) {
  return {
    status,
    result_note: resultNote || null,
    result_snapshot: resultSnapshot || null
  }
}

export function normalizeParameterImportRows(text = '') {
  return String(text)
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [param_code = '', param_name = '', category_code = '', unit_code = ''] = line.split(',')
      return normalizeParameterForm({ param_code, param_name, category_code, unit_code })
    })
}

export function buildTemplateSyncPayload({ sourceComponentId, targetComponentId, syncMode = 'overwrite_template_scope' } = {}) {
  return {
    source_component_id: Number(sourceComponentId || 0),
    target_component_id: Number(targetComponentId || 0),
    sync_mode: syncMode
  }
}
