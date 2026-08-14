import assert from 'node:assert/strict'

import {
  buildWorkbenchProcessFlowGraph,
  buildWorkbenchProcessPanelContext,
  buildWorkbenchCalculationPanelContext,
  applyWorkbenchExplanationDraft,
  buildImpactCompactCards,
  buildImpactDefaultSelection,
  buildImpactRangeRows,
  buildImpactSensitivityRows,
  buildImpactStateSummaryCards,
  buildImpactStateTableRows,
  buildImpactTrendSeries,
  buildFormulaAutocompleteSections,
  buildFormulaAutocompleteItems,
  buildWorkbenchCalculationFlow,
  buildExecutionIntermediateRows,
  buildFormulaShortcutItems,
  buildCurveFormulaExpression,
  buildCurveUpgradeHint,
  buildFormulaResultMap,
  buildFormulaSyncPreviewViewModel,
  buildWorkbenchFlowVisibleGraph,
  filterImpactSamplesByMultiValues,
  filterImpactSamplesByRange,
  filterImpactSamplesBySingleValue,
  normalizeFormulaImpactPayload,
  parseCurveFormulaExpression,
  resolveFormulaAutocompleteInsertion,
  resolveFormulaArgumentHint,
  resolveImpactStateChartMode,
  resolveWorkbenchProcessSelectedNode,
  resolveWorkbenchFlowExpandedFormulaKeys,
  resolveWorkbenchFlowSelectedNode,
  resolveNextFocusAfterFormulaDelete,
  resolveNextFocusAfterFormulaBatchDelete,
  toggleFormulaBatchSelection
} from './drumDesign.helpers.mjs'

const impactFixture = {
  formula_name: '滚筒转速',
  target_parameter: '电机转速',
  baseline_parameter_value: '980',
  samples: [
    {
      parameter_value: '882',
      input_delta_percent: '-10',
      results: [
        { result_name: '滚筒转速', current_value: '8.82', baseline_value: '9.8', delta_value: '-0.98', delta_percent: '-10', unit_code: 'r/min' },
        { result_name: '推荐电机功率', current_value: '12.1', baseline_value: '13.4', delta_value: '-1.3', delta_percent: '-9.7', unit_code: 'kW' }
      ]
    },
    {
      parameter_value: '980',
      input_delta_percent: '0',
      results: [
        { result_name: '滚筒转速', current_value: '9.8', baseline_value: '9.8', delta_value: '0', delta_percent: '0', unit_code: 'r/min' },
        { result_name: '推荐电机功率', current_value: '13.4', baseline_value: '13.4', delta_value: '0', delta_percent: '0', unit_code: 'kW' }
      ]
    },
    {
      parameter_value: '1078',
      input_delta_percent: '10',
      results: [
        { result_name: '滚筒转速', current_value: '10.78', baseline_value: '9.8', delta_value: '0.98', delta_percent: '10', unit_code: 'r/min' },
        { result_name: '推荐电机功率', current_value: '14.8', baseline_value: '13.4', delta_value: '1.4', delta_percent: '10.4', unit_code: 'kW' }
      ]
    }
  ],
  result_summary: [
    { result_name: '推荐电机功率', baseline_value: '13.4', min_value: '12.1', max_value: '14.8', trend: 'positive', sensitivity: '1.04', impact_level: 'high', unit_code: 'kW' },
    { result_name: '滚筒转速', baseline_value: '9.8', min_value: '8.82', max_value: '10.78', trend: 'positive', sensitivity: '1.00', impact_level: 'high', unit_code: 'r/min' },
    { result_name: '托轮摩擦力矩', baseline_value: '4.1', min_value: '4.0', max_value: '4.2', trend: 'flat', sensitivity: '0.05', impact_level: 'low', unit_code: 'N.m' }
  ]
}

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('buildFormulaAutocompleteItems 包含查表附录候选', () => {
  const items = buildFormulaAutocompleteItems({
    keyword: '电机扭',
    parameterRows: [{ paramName: '电机频率', displayName: '电机频率', source: 'matrix' }],
    lookupItems: [{ lookup_name: '电机扭矩参数' }]
  })

  assert.ok(items.some((item) => item.group === '查表附录' && item.value === '电机扭矩参数!B:C'))
})


run('normalizeFormulaImpactPayload 补齐默认字段', () => {
  const normalized = normalizeFormulaImpactPayload({})
  assert.deepEqual(normalized.samples, [])
  assert.deepEqual(normalized.result_summary, [])
  assert.equal(normalized.formula_name, '')
})

run('buildImpactDefaultSelection 优先当前公式并按敏感度截断', () => {
  const normalized = normalizeFormulaImpactPayload(impactFixture)
  assert.deepEqual(buildImpactDefaultSelection(normalized, '滚筒转速', 2), ['推荐电机功率', '滚筒转速'])
})

run('buildImpactTrendSeries 只返回选中结果的数值点', () => {
  const normalized = normalizeFormulaImpactPayload(impactFixture)
  const series = buildImpactTrendSeries(normalized, ['滚筒转速'])
  assert.equal(series.length, 1)
  assert.deepEqual(series[0].data, [[882, 8.82], [980, 9.8], [1078, 10.78]])
})

run('buildImpactSensitivityRows 按绝对敏感度倒序输出', () => {
  const normalized = normalizeFormulaImpactPayload(impactFixture)
  const rows = buildImpactSensitivityRows(normalized)
  assert.deepEqual(rows.map((item) => item.resultName), ['推荐电机功率', '滚筒转速', '托轮摩擦力矩'])
})

run('buildImpactRangeRows 生成区间条图所需的数值结构', () => {
  const normalized = normalizeFormulaImpactPayload(impactFixture)
  const rows = buildImpactRangeRows(normalized)
  assert.deepEqual(rows[0], {
    resultName: '推荐电机功率',
    min: 12.1,
    max: 14.8,
    baseline: 13.4,
    span: 2.7,
    unitCode: 'kW'
  })
})

run('buildImpactCompactCards 只返回当前选中结果并保留趋势标签', () => {
  const normalized = normalizeFormulaImpactPayload(impactFixture)
  const cards = buildImpactCompactCards(normalized, ['滚筒转速'])
  assert.deepEqual(cards[0], {
    resultName: '滚筒转速',
    baselineText: '9.8 r/min',
    trendLabel: '正相关',
    sensitivityText: '1.00',
    rangeText: '8.82 - 10.78',
    impactLevel: 'high'
  })
})

run('filterImpactSamplesBySingleValue 返回最接近的单状态样本', () => {
  const normalized = normalizeFormulaImpactPayload(impactFixture)
  const rows = filterImpactSamplesBySingleValue(normalized, '980')
  assert.equal(rows.length, 1)
  assert.equal(rows[0].parameter_value, '980')
})

run('filterImpactSamplesBySingleValue 在没有完全相等采样点时命中最近样本', () => {
  const normalized = normalizeFormulaImpactPayload({
    ...impactFixture,
    samples: [
      { parameter_value: '39.8', results: [] },
      { parameter_value: '45.0', results: [] }
    ]
  })
  const rows = filterImpactSamplesBySingleValue(normalized, '40')
  assert.equal(rows.length, 1)
  assert.equal(rows[0].parameter_value, '39.8')
})

run('filterImpactSamplesByMultiValues 按输入顺序返回多个状态样本', () => {
  const normalized = normalizeFormulaImpactPayload(impactFixture)
  const rows = filterImpactSamplesByMultiValues(normalized, ['1078', '882'])
  assert.deepEqual(rows.map((item) => item.parameter_value), ['1078', '882'])
})

run('filterImpactSamplesByRange 返回区间内全部状态', () => {
  const normalized = normalizeFormulaImpactPayload(impactFixture)
  const rows = filterImpactSamplesByRange(normalized, { min: '900', max: '1100' })
  assert.deepEqual(rows.map((item) => item.parameter_value), ['980', '1078'])
})

run('filterImpactSamplesByRange 在非法区间时返回空数组', () => {
  const normalized = normalizeFormulaImpactPayload(impactFixture)
  const rows = filterImpactSamplesByRange(normalized, { min: '50', max: '40' })
  assert.deepEqual(rows, [])
})

run('resolveImpactStateChartMode 在单状态时返回 single-bar', () => {
  assert.equal(resolveImpactStateChartMode([{ parameter_value: '980', results: [] }]), 'single-bar')
})

run('resolveImpactStateChartMode 在少量多状态时返回 grouped-bar', () => {
  assert.equal(
    resolveImpactStateChartMode([
      { parameter_value: '882', results: [] },
      { parameter_value: '980', results: [] },
      { parameter_value: '1078', results: [] }
    ]),
    'grouped-bar'
  )
})

run('resolveImpactStateChartMode 在较多状态时返回 heatmap', () => {
  const rows = Array.from({ length: 7 }, (_, index) => ({
    parameter_value: String(40 + index),
    results: []
  }))
  assert.equal(resolveImpactStateChartMode(rows), 'heatmap')
})

run('buildImpactStateSummaryCards 在多状态下输出摘要型卡片', () => {
  const normalized = normalizeFormulaImpactPayload(impactFixture)
  const samples = filterImpactSamplesByMultiValues(normalized, ['882', '980', '1078'])
  const cards = buildImpactStateSummaryCards(samples, normalized.result_summary, {
    filterType: 'multi',
    filterValue: ['882', '980', '1078']
  })
  assert.deepEqual(cards[0], {
    title: '命中状态',
    value: '3',
    meta: '多值筛选'
  })
})

run('buildImpactStateTableRows 在单状态下输出读值表格', () => {
  const normalized = normalizeFormulaImpactPayload(impactFixture)
  const sample = filterImpactSamplesBySingleValue(normalized, '980')[0]
  const rows = buildImpactStateTableRows([sample], normalized.result_summary, 'single')
  assert.deepEqual(rows[0], {
    resultName: '滚筒转速',
    currentValue: '9.8',
    baselineValue: '9.8',
    deltaValue: '0',
    deltaPercent: '0',
    unitCode: 'r/min',
    sensitivity: '1.00',
    impactLevel: 'high'
  })
})

run('buildFormulaShortcutItems 默认隐藏复杂函数', () => {
  const labels = buildFormulaShortcutItems().map((item) => item.label)

  assert.deepEqual(labels, ['IF()', 'IFERROR()', 'π', 'e', 'sin()', 'cos()', 'tan()', 'sqrt()', 'ln()', 'log()', 'abs()', 'pow()'])
  assert.equal(labels.includes('VLOOKUP()'), false)
  assert.equal(labels.includes('CURVE2D()'), false)
})

run('buildFormulaAutocompleteSections 对函数关键字优先展示函数组', () => {
  const sections = buildFormulaAutocompleteSections({
    keyword: 'VLO',
    parameterRows: [{ paramName: '电机频率', displayName: '电机频率', source: 'matrix' }],
    lookupItems: [{ id: 9, lookup_name: '电机扭矩参数' }]
  })

  assert.equal(sections[0].label, '函数')
  assert.equal(sections[0].items[0].value, 'VLOOKUP()')
  assert.equal(sections[1].label, '基础参数')
})

run('resolveFormulaArgumentHint 返回当前参数位中文提示', () => {
  assert.deepEqual(
    resolveFormulaArgumentHint({
      expression: '=142*VLOOKUP(电机频率,电机扭矩参数!B:C,2,0)',
      selectionStart: '=142*VLOOKUP(电机频率,'.length
    }),
    {
      functionName: 'VLOOKUP',
      argumentIndex: 1,
      label: '附录范围',
      description: '这里填写附录范围，例如 电机扭矩参数!B:C'
    }
  )
})

run('resolveFormulaAutocompleteInsertion 插入 CURVE2D 后光标落在括号内', () => {
  assert.deepEqual(
    resolveFormulaAutocompleteInsertion({
      expression: '=',
      selectionStart: 1,
      selectionEnd: 1,
      insertedValue: 'CURVE2D()'
    }),
    {
      nextValue: '=CURVE2D()',
      nextSelectionStart: 9,
      nextSelectionEnd: 9
    }
  )
})

run('buildFormulaResultMap 保留 lookup_detail 用于查表结果展示', () => {
  const result = buildFormulaResultMap([
    {
      result_name: 'MN',
      result_value: '142',
      source_formula: 'MN',
      lookup_detail: {
        lookup_name: '电机扭矩参数',
        lookup_key: '50',
        result_value: '1',
        base_factor: '142'
      }
    }
  ])

  assert.equal(result.MN.lookupDetail.lookup_name, '电机扭矩参数')
})

run('buildExecutionIntermediateRows 合并查表结果并标记为已计算', () => {
  const rows = buildExecutionIntermediateRows({
    formulaRows: [
      {
        name: '推荐电机功率',
        unit_code: 'kW',
        scene_name: '转速与功率'
      }
    ],
    latestResults: [
      {
        result_name: 'MN',
        result_value: '142',
        unit_code: 'N.m',
        source_formula: 'MN',
        scene_name: '查表附录'
      }
    ],
    latestScope: {
      MN: 142,
      推荐电机功率: 18.6
    }
  })

  const mnRow = rows.find((item) => item.paramName === 'MN')
  const powerRow = rows.find((item) => item.paramName === '推荐电机功率')

  assert.equal(rows.length, 2)
  assert.deepEqual(
    {
      paramName: mnRow?.paramName,
      value: mnRow?.value,
      status: mnRow?.status,
      sourceFormula: mnRow?.sourceFormula,
      sceneName: mnRow?.sceneName
    },
    {
      paramName: 'MN',
      value: '142',
      status: '已计算',
      sourceFormula: 'MN',
      sceneName: '查表附录'
    }
  )
  assert.deepEqual(
    {
      paramName: powerRow?.paramName,
      value: powerRow?.value,
      status: powerRow?.status,
      sourceFormula: powerRow?.sourceFormula,
      sceneName: powerRow?.sceneName
    },
    {
      paramName: '推荐电机功率',
      value: '18.6',
      status: '已计算',
      sourceFormula: '推荐电机功率',
      sceneName: '转速与功率'
    }
  )
})

run('buildWorkbenchCalculationFlow 按变量依赖生成工作台计算链路图', () => {
  const graph = buildWorkbenchCalculationFlow({
    moduleCode: 'power_calc',
    formulaRows: [
      {
        _rowKey: 'id:11',
        module_code: 'power_calc',
        scene_code: 'storage_load',
        scene_name: '存料与载荷',
        sort_order: 1,
        name: '总重',
        expression: '=滚筒重量+筒内料重',
        variables: { 滚筒重量: '', 筒内料重: '' },
        unit_code: 'kg'
      },
      {
        _rowKey: 'id:15',
        module_code: 'power_calc',
        scene_code: 'friction_torque',
        scene_name: '摩擦与力矩',
        sort_order: 2,
        name: '托轮摩擦力矩',
        expression: '=总重*摩擦系数',
        variables: { 总重: '', 摩擦系数: '' },
        unit_code: 'N.m'
      },
      {
        _rowKey: 'id:18',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 3,
        name: '推荐电机功率',
        expression: '=托轮摩擦力矩*滚筒转速/9550',
        variables: { 托轮摩擦力矩: '', 滚筒转速: '' },
        unit_code: 'kW'
      }
    ],
    parameterRows: [
      { paramName: '滚筒重量', displayName: '筒体重量', value: '2800', unitCode: 'kg' },
      { paramName: '筒内料重', value: '1200', unitCode: 'kg' },
      { paramName: '摩擦系数', value: '0.12', unitCode: '' },
      { paramName: '滚筒转速', value: '9.8', unitCode: 'rpm' }
    ],
    latestResults: [
      { source_formula: '总重', result_name: '总重', result_value: '4000', unit_code: 'kg', scene_code: 'storage_load', scene_name: '存料与载荷' },
      { source_formula: '托轮摩擦力矩', result_name: '托轮摩擦力矩', result_value: '480', unit_code: 'N.m', scene_code: 'friction_torque', scene_name: '摩擦与力矩' },
      { source_formula: '推荐电机功率', result_name: '推荐电机功率', result_value: '18.6', unit_code: 'kW', scene_code: 'power', scene_name: '转速与功率' }
    ],
    latestScope: {
      总重: 4000,
      托轮摩擦力矩: 480,
      推荐电机功率: 18.6
    }
  })

  assert.equal(graph.sceneCount, 3)
  assert.equal(graph.formulaCount, 3)
  assert.equal(graph.nodes.some((item) => item.id === 'formula:推荐电机功率'), true)
  assert.equal(graph.nodes.some((item) => item.id === 'input:滚筒重量'), true)
  assert.equal(
    graph.edges.some((item) => item.source === 'formula:托轮摩擦力矩' && item.target === 'formula:推荐电机功率'),
    true
  )
  assert.equal(
    graph.edges.some((item) => item.source === 'input:滚筒转速' && item.target === 'formula:推荐电机功率'),
    true
  )
  assert.equal(graph.nodes.find((item) => item.id === 'input:滚筒重量')?.title, '筒体重量')
})

run('buildWorkbenchCalculationFlow 按模块内部角色生成基础参数/依据参数/中间变量/结果量', () => {
  const graph = buildWorkbenchCalculationFlow({
    moduleCode: 'power_calc',
    formulaRows: [
      {
        _rowKey: 'id:11',
        module_code: 'power_calc',
        scene_code: 'storage_load',
        scene_name: '存料与载荷',
        sort_order: 1,
        name: '总重',
        expression: '=滚筒重量+筒内料重',
        variables: { 滚筒重量: '', 筒内料重: '' },
        unit_code: 'kg'
      },
      {
        _rowKey: 'id:15',
        module_code: 'power_calc',
        scene_code: 'friction_torque',
        scene_name: '摩擦与力矩',
        sort_order: 2,
        name: '托轮摩擦力矩',
        expression: '=总重*摩擦系数',
        variables: { 总重: '', 摩擦系数: '' },
        unit_code: 'N.m'
      },
      {
        _rowKey: 'id:18',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 3,
        name: '功率',
        expression: '=托轮摩擦力矩*滚筒转速/9550',
        variables: { 托轮摩擦力矩: '', 滚筒转速: '' },
        unit_code: 'kW'
      }
    ],
    parameterRows: [
      { paramName: '滚筒重量', value: '2800', unitCode: 'kg', source: 'matrix' },
      { paramName: '筒内料重', value: '1200', unitCode: 'kg', source: 'matrix' },
      { paramName: '摩擦系数', value: '0.12', unitCode: '', source: 'matrix' },
      { paramName: '滚筒转速', value: '9.8', unitCode: 'rpm', source: 'matrix' }
    ],
    latestResults: [
      { source_formula: '总重', result_name: '总重', result_value: '4000', unit_code: 'kg', scene_code: 'storage_load', scene_name: '存料与载荷' },
      { source_formula: '托轮摩擦力矩', result_name: '托轮摩擦力矩', result_value: '480', unit_code: 'N.m', scene_code: 'friction_torque', scene_name: '摩擦与力矩' },
      { source_formula: '功率', result_name: '功率', result_value: '18.6', unit_code: 'kW', scene_code: 'power', scene_name: '转速与功率' }
    ]
  })

  const byId = Object.fromEntries(graph.nodes.map((node) => [node.id, node]))

  assert.equal(byId['input:滚筒重量'].semanticRole, 'base')
  assert.equal(byId['input:摩擦系数'].semanticRole, 'reference')
  assert.equal(byId['formula:总重'].semanticRole, 'intermediate')
  assert.equal(byId['formula:功率'].semanticRole, 'result')
  assert.equal(byId['formula:总重'].layer, 'calculation')
  assert.equal(byId['formula:功率'].layer, 'output')
  assert.equal(byId['formula:功率'].isMainline, true)
})

run('buildWorkbenchCalculationFlow 默认模块图保留模块内承接公式，避免参数支路被折断', () => {
  const graph = buildWorkbenchCalculationFlow({
    moduleCode: 'power_calc',
    formulaRows: [
      {
        _rowKey: 'id:11',
        module_code: 'power_calc',
        scene_code: 'storage_load',
        scene_name: '存料与载荷',
        sort_order: 1,
        name: '总重',
        variables: { 滚筒重量: '', 筒内料重: '' },
        unit_code: 'kg'
      },
      {
        _rowKey: 'id:12',
        module_code: 'power_calc',
        scene_code: 'storage_load',
        scene_name: '存料与载荷',
        sort_order: 2,
        name: '总重换算值',
        variables: { 总重: '' },
        unit_code: 'kg'
      },
      {
        _rowKey: 'id:18',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 3,
        name: '功率',
        variables: { 总重换算值: '', 滚筒转速: '' },
        unit_code: 'kW'
      }
    ],
    parameterRows: [
      { paramName: '滚筒重量', value: '2800', unitCode: 'kg', source: 'matrix' },
      { paramName: '筒内料重', value: '1200', unitCode: 'kg', source: 'matrix' },
      { paramName: '滚筒转速', value: '9.8', unitCode: 'rpm', source: 'matrix' }
    ],
    latestResults: []
  })

  const bridgeNode = graph.nodes.find((node) => node.id === 'formula:总重换算值')
  const resultNode = graph.nodes.find((node) => node.id === 'formula:功率')
  assert.equal(bridgeNode.defaultVisible, true)
  assert.equal(resultNode.defaultVisible, true)
})

run('buildWorkbenchCalculationFlow 在聚焦单条公式时仍可折叠纯承接公式', () => {
  const graph = buildWorkbenchCalculationFlow({
    moduleCode: 'power_calc',
    focusedFormulaName: '功率',
    formulaRows: [
      {
        _rowKey: 'id:11',
        module_code: 'power_calc',
        scene_code: 'storage_load',
        scene_name: '存料与载荷',
        sort_order: 1,
        name: '总重',
        variables: { 滚筒重量: '', 筒内料重: '' },
        unit_code: 'kg'
      },
      {
        _rowKey: 'id:12',
        module_code: 'power_calc',
        scene_code: 'storage_load',
        scene_name: '存料与载荷',
        sort_order: 2,
        name: '总重换算值',
        variables: { 总重: '' },
        unit_code: 'kg'
      },
      {
        _rowKey: 'id:18',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 3,
        name: '功率',
        variables: { 总重换算值: '', 滚筒转速: '' },
        unit_code: 'kW'
      }
    ],
    parameterRows: [
      { paramName: '滚筒重量', value: '2800', unitCode: 'kg', source: 'matrix' },
      { paramName: '筒内料重', value: '1200', unitCode: 'kg', source: 'matrix' },
      { paramName: '滚筒转速', value: '9.8', unitCode: 'rpm', source: 'matrix' }
    ],
    latestResults: []
  })

  const bridgeNode = graph.nodes.find((node) => node.id === 'formula:总重换算值')
  const resultNode = graph.nodes.find((node) => node.id === 'formula:功率')
  assert.equal(bridgeNode.defaultVisible, false)
  assert.equal(resultNode.defaultVisible, true)
})

run('buildWorkbenchCalculationFlow 可按当前设计公式收窄到真实引用链路', () => {
  const graph = buildWorkbenchCalculationFlow({
    moduleCode: 'power_calc',
    focusedFormulaName: '功率',
    formulaRows: [
      {
        _rowKey: 'id:11',
        module_code: 'power_calc',
        scene_code: 'storage_load',
        scene_name: '存料与载荷',
        sort_order: 1,
        name: '总重',
        variables: { 滚筒重量: '', 筒内料重: '' },
        unit_code: 'kg'
      },
      {
        _rowKey: 'id:15',
        module_code: 'power_calc',
        scene_code: 'friction_torque',
        scene_name: '摩擦与力矩',
        sort_order: 2,
        name: '托轮摩擦力矩',
        variables: { 总重: '', 摩擦系数: '' },
        unit_code: 'N.m'
      },
      {
        _rowKey: 'id:18',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 3,
        name: '功率',
        variables: { 托轮摩擦力矩: '', 滚筒转速: '' },
        unit_code: 'kW'
      },
      {
        _rowKey: 'id:19',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 4,
        name: '备用结果',
        variables: { 总重: '' },
        unit_code: 'kW'
      }
    ],
    parameterRows: [
      { paramName: '滚筒重量', value: '2800', unitCode: 'kg', source: 'matrix' },
      { paramName: '筒内料重', value: '1200', unitCode: 'kg', source: 'matrix' },
      { paramName: '摩擦系数', value: '0.12', unitCode: '', source: 'matrix' },
      { paramName: '滚筒转速', value: '9.8', unitCode: 'rpm', source: 'matrix' },
      { paramName: '备用系数', value: '1.1', unitCode: '', source: 'matrix' }
    ],
    latestResults: []
  })

  assert.equal(graph.nodes.some((node) => node.id === 'formula:功率'), true)
  assert.equal(graph.nodes.some((node) => node.id === 'formula:托轮摩擦力矩'), true)
  assert.equal(graph.nodes.some((node) => node.id === 'formula:总重'), true)
  assert.equal(graph.nodes.some((node) => node.id === 'input:滚筒转速'), true)
  assert.equal(graph.nodes.some((node) => node.id === 'input:摩擦系数'), true)
  assert.equal(graph.nodes.some((node) => node.id === 'formula:备用结果'), false)
  assert.equal(graph.nodes.some((node) => node.id === 'input:备用系数'), false)
})

run('buildWorkbenchCalculationFlow 为聚焦链路输出主干语义字段', () => {
  const graph = buildWorkbenchCalculationFlow({
    moduleCode: 'power_calc',
    formulaRows: [
      {
        _rowKey: 'id:11',
        module_code: 'power_calc',
        scene_code: 'storage_load',
        scene_name: '存料与载荷',
        sort_order: 1,
        name: '总重',
        variables: { 滚筒重量: '', 筒内料重: '' },
        unit_code: 'kg'
      },
      {
        _rowKey: 'id:15',
        module_code: 'power_calc',
        scene_code: 'friction_torque',
        scene_name: '摩擦与力矩',
        sort_order: 2,
        name: '托轮摩擦力矩',
        variables: { 总重: '', 摩擦系数: '' },
        unit_code: 'N.m'
      },
      {
        _rowKey: 'id:18',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 3,
        name: '功率',
        variables: { 托轮摩擦力矩: '', 滚筒转速: '' },
        unit_code: 'kW'
      },
      {
        _rowKey: 'id:19',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 4,
        name: '备用结果',
        variables: { 总重: '' },
        unit_code: 'kW'
      }
    ],
    parameterRows: [
      { paramName: '滚筒重量', value: '2800', unitCode: 'kg', source: 'matrix' },
      { paramName: '筒内料重', value: '1200', unitCode: 'kg', source: 'matrix' },
      { paramName: '摩擦系数', value: '0.12', unitCode: '', source: 'matrix' },
      { paramName: '滚筒转速', value: '9.8', unitCode: 'rpm', source: 'matrix' }
    ],
    latestResults: []
  })

  const byId = Object.fromEntries(graph.nodes.map((node) => [node.id, node]))
  assert.deepEqual(byId['formula:总重'].resultKeys, ['formula:功率', 'formula:备用结果'])
  assert.equal(byId['formula:总重'].isShared, true)
  assert.equal(byId['formula:功率'].isPrimaryResult, true)
  assert.equal(byId['formula:托轮摩擦力矩'].isPrimarySpine, true)
  assert.equal(byId['input:滚筒转速'].branchOwner, 'formula:功率')
})

run('buildWorkbenchCalculationFlow 为 A 视图输出稳定的显示元数据', () => {
  const graph = buildWorkbenchCalculationFlow({
    moduleCode: 'power_calc',
    formulaRows: [
      {
        _rowKey: 'id:11',
        module_code: 'power_calc',
        scene_code: 'storage_load',
        scene_name: '存料与载荷',
        sort_order: 1,
        name: '总重',
        expression: '=滚筒重量+筒内料重',
        variables: { 滚筒重量: '', 筒内料重: '' },
        unit_code: 'kg'
      },
      {
        _rowKey: 'id:15',
        module_code: 'power_calc',
        scene_code: 'friction_torque',
        scene_name: '摩擦与力矩',
        sort_order: 2,
        name: '托轮摩擦力矩',
        expression: '=总重*摩擦系数',
        variables: { 总重: '', 摩擦系数: '' },
        unit_code: 'N.m'
      },
      {
        _rowKey: 'id:18',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 3,
        name: '功率',
        expression: '=托轮摩擦力矩*滚筒转速/9550',
        variables: { 托轮摩擦力矩: '', 滚筒转速: '' },
        unit_code: 'kW'
      }
    ],
    parameterRows: [
      { paramName: '滚筒重量', value: '2800', unitCode: 'kg', source: 'matrix' },
      { paramName: '筒内料重', value: '1200', unitCode: 'kg', source: 'matrix' },
      { paramName: '摩擦系数', value: '0.12', unitCode: '', source: 'matrix' },
      { paramName: '滚筒转速', value: '9.8', unitCode: 'rpm', source: 'matrix' }
    ],
    latestResults: []
  })

  const byId = Object.fromEntries(graph.nodes.map((node) => [node.id, node]))
  assert.equal(byId['input:滚筒重量'].visualBand, 'input')
  assert.equal(byId['input:摩擦系数'].visualCategory, 'reference')
  assert.equal(byId['formula:托轮摩擦力矩'].visualBand, 'calculation')
  assert.equal(byId['formula:托轮摩擦力矩'].layoutGroup, 'scene:摩擦与力矩')
  assert.equal(byId['formula:功率'].visualBand, 'output')
  assert.equal(byId['formula:功率'].emphasis, 'result')
})

run('buildWorkbenchCalculationFlow 为公式节点生成简短说明初稿', () => {
  const graph = buildWorkbenchCalculationFlow({
    moduleCode: 'power_calc',
    formulaRows: [
      {
        _rowKey: 'id:18',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 3,
        name: '功率',
        expression: '=托轮摩擦力矩*滚筒转速/9550',
        variables: { 托轮摩擦力矩: '', 滚筒转速: '' },
        unit_code: 'kW'
      }
    ],
    parameterRows: [{ paramName: '滚筒转速', value: '9.8', unitCode: 'rpm', source: 'matrix' }],
    latestResults: []
  })

  const panel = buildWorkbenchCalculationPanelContext(graph, 'formula:功率')
  assert.equal(panel.explanation.purpose, '用于输出当前公式结果')
  assert.equal(panel.explanation.impact, '结果会继续给下游节点使用或直接输出')
})

run('applyWorkbenchExplanationDraft 用本地草稿覆盖 purpose 和 impact', () => {
  assert.deepEqual(
    applyWorkbenchExplanationDraft(
      { purpose: '自动初稿', derivation: 'A', impact: '自动影响' },
      { purpose: '手动改写', impact: '手动影响' }
    ),
    { purpose: '手动改写', derivation: 'A', impact: '手动影响' }
  )
})

run('buildWorkbenchCalculationPanelContext 为结果量返回可解释追溯信息', () => {
  const graph = {
    nodes: [
      {
        id: 'formula:功率',
        name: '功率',
        title: '功率',
        nodeType: 'formula',
        semanticRole: 'result',
        panelContext: {
          explanation: {
            nodeId: 'formula:功率',
            nodeType: 'formula',
            purpose: '用于输出当前公式结果',
            keyInputs: [{ paramName: '托轮摩擦力矩', value: '480', unit: 'N.m', source: '模块内中间变量' }],
            derivation: '由托轮摩擦力矩和滚筒转速推导当前功率结果',
            impact: '结果会继续给下游节点使用或直接输出'
          }
        }
      }
    ]
  }

  assert.deepEqual(buildWorkbenchCalculationPanelContext(graph, 'formula:功率'), {
    title: '功率',
    nodeType: 'formula',
    explanation: {
      nodeId: 'formula:功率',
      nodeType: 'formula',
      purpose: '用于输出当前公式结果',
      keyInputs: [{ paramName: '托轮摩擦力矩', value: '480', unit: 'N.m', source: '模块内中间变量' }],
      derivation: '由托轮摩擦力矩和滚筒转速推导当前功率结果',
      impact: '结果会继续给下游节点使用或直接输出'
    },
    summary: [],
    parameters: [],
    lookups: [],
    constraints: []
  })
})

run('buildWorkbenchCalculationFlow 在依赖缺失时标记链路不完整但不返回空图', () => {
  const graph = buildWorkbenchCalculationFlow({
    moduleCode: 'power_calc',
    formulaRows: [
      {
        _rowKey: 'id:21',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 1,
        name: '功率',
        variables: { 不存在的中间量: '', 滚筒转速: '' },
        unit_code: 'kW'
      }
    ],
    parameterRows: [{ paramName: '滚筒转速', value: '9.8', unitCode: 'rpm', source: 'matrix' }],
    latestResults: []
  })

  assert.equal(graph.nodes.length > 0, true)
  assert.equal(graph.nodes.find((node) => node.id === 'formula:功率')?.lineageIncomplete, true)
})

run('buildWorkbenchFlowVisibleGraph 默认只保留当前公式主链', () => {
  const fullGraph = buildWorkbenchCalculationFlow({
    moduleCode: 'power_calc',
    formulaRows: [
      {
        _rowKey: 'id:11',
        module_code: 'power_calc',
        scene_code: 'storage_load',
        scene_name: '存料与载荷',
        sort_order: 1,
        name: '总重',
        variables: { 滚筒重量: '', 筒内料重: '' },
        unit_code: 'kg'
      },
      {
        _rowKey: 'id:15',
        module_code: 'power_calc',
        scene_code: 'friction_torque',
        scene_name: '摩擦与力矩',
        sort_order: 2,
        name: '托轮摩擦力矩',
        variables: { 总重: '', 摩擦系数: '' },
        unit_code: 'N.m'
      },
      {
        _rowKey: 'id:18',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 3,
        name: '推荐电机功率',
        variables: { 托轮摩擦力矩: '', 滚筒转速: '' },
        unit_code: 'kW'
      }
    ],
    parameterRows: [
      { paramName: '滚筒重量', value: '2800', unitCode: 'kg' },
      { paramName: '筒内料重', value: '1200', unitCode: 'kg' },
      { paramName: '摩擦系数', value: '0.12', unitCode: '' },
      { paramName: '滚筒转速', value: '9.8', unitCode: 'rpm' }
    ],
    latestResults: [],
    latestScope: {}
  })

  const focused = buildWorkbenchFlowVisibleGraph({
    graph: fullGraph,
    activeFormulaKey: 'id:18',
    expandedFormulaKeys: []
  })

  assert.deepEqual(
    focused.nodes.map((item) => item.id).sort(),
    [
      'formula:总重',
      'formula:托轮摩擦力矩',
      'formula:推荐电机功率',
      'input:滚筒重量',
      'input:筒内料重',
      'input:摩擦系数',
      'input:滚筒转速'
    ].sort()
  )
})

run('resolveWorkbenchFlowSelectedNode 返回公式节点动作能力', () => {
  const graph = {
    nodes: [
      {
        id: 'formula:推荐电机功率',
        name: '推荐电机功率',
        nodeType: 'formula',
        formulaKey: 'id:18',
        formulaRow: { _rowKey: 'id:18', name: '推荐电机功率' },
        value: '18.6',
        unitCode: 'kW'
      }
    ],
    edges: []
  }

  const selected = resolveWorkbenchFlowSelectedNode(graph, 'formula:推荐电机功率')

  assert.deepEqual(selected, {
    nodeId: 'formula:推荐电机功率',
    nodeType: 'formula',
    name: '推荐电机功率',
    metricText: '18.6 kW',
    formulaKey: 'id:18',
    canOpenFormula: true,
    formulaRow: { _rowKey: 'id:18', name: '推荐电机功率' }
  })
})

run('resolveWorkbenchFlowExpandedFormulaKeys 切换公式时将当前公式并入主展开集合', () => {
  assert.deepEqual(
    resolveWorkbenchFlowExpandedFormulaKeys({
      previousExpandedFormulaKeys: ['id:15'],
      nextFormulaKey: 'id:18'
    }),
    ['id:18']
  )
})

run('buildWorkbenchProcessFlowGraph 将公式链收口为设计推理主链、结果锚点、规则和参数挂点', () => {
  const graph = buildWorkbenchProcessFlowGraph({
    moduleCode: 'power_calc',
    formulaRows: [
      {
        _rowKey: 'id:11',
        module_code: 'power_calc',
        scene_code: 'storage_load',
        scene_name: '存料与载荷',
        sort_order: 1,
        name: '总重',
        variables: { 滚筒重量: '', 筒内料重: '' },
        unit_code: 'kg'
      },
      {
        _rowKey: 'id:15',
        module_code: 'power_calc',
        scene_code: 'friction_torque',
        scene_name: '摩擦与力矩',
        sort_order: 2,
        name: '托轮摩擦力矩',
        variables: { 总重: '', 摩擦系数: '' },
        unit_code: 'N.m'
      },
      {
        _rowKey: 'id:18',
        module_code: 'power_calc',
        scene_code: 'power',
        scene_name: '转速与功率',
        sort_order: 3,
        name: '推荐电机功率',
        variables: { 托轮摩擦力矩: '', 滚筒转速: '' },
        unit_code: 'kW'
      }
    ],
    parameterRows: [
      { paramName: '滚筒重量', value: '2800', unitCode: 'kg', source: 'matrix' },
      { paramName: '筒内料重', value: '1200', unitCode: 'kg', source: 'matrix' },
      { paramName: '摩擦系数', value: '0.12', unitCode: '', source: 'matrix' },
      { paramName: '滚筒转速', value: '9.8', unitCode: 'rpm', source: 'matrix' }
    ],
    latestResults: [
      { source_formula: '总重', result_name: '总重', result_value: '4000', unit_code: 'kg', scene_code: 'storage_load', scene_name: '存料与载荷' },
      { source_formula: '托轮摩擦力矩', result_name: '托轮摩擦力矩', result_value: '480', unit_code: 'N.m', scene_code: 'friction_torque', scene_name: '摩擦与力矩' },
      { source_formula: '推荐电机功率', result_name: '推荐电机功率', result_value: '18.6', unit_code: 'kW', scene_code: 'power', scene_name: '转速与功率' }
    ]
  })

  assert.equal(graph.stepCount, 4)
  assert.equal(graph.resultCount, 3)
  assert.equal(graph.ruleCount, 1)
  assert.equal(graph.paramCount, 4)
  assert.deepEqual(
    graph.nodes.map((item) => ({ id: item.id, nodeType: item.nodeType, title: item.title })),
    [
      { id: 'step:input', nodeType: 'step', title: '输入条件' },
      { id: 'step:storage_load', nodeType: 'step', title: '载荷确定' },
      { id: 'result:storage_load', nodeType: 'result_anchor', title: '总重' },
      { id: 'param:storage_load:滚筒重量', nodeType: 'parameter', title: '滚筒重量' },
      { id: 'param:storage_load:筒内料重', nodeType: 'parameter', title: '筒内料重' },
      { id: 'step:friction_torque', nodeType: 'step', title: '结构尺寸确认' },
      { id: 'result:friction_torque', nodeType: 'result_anchor', title: '托轮摩擦力矩' },
      { id: 'param:friction_torque:摩擦系数', nodeType: 'parameter', title: '摩擦系数' },
      { id: 'step:power', nodeType: 'step', title: '功率校核' },
      { id: 'result:power', nodeType: 'result_anchor', title: '推荐电机功率' },
      { id: 'rule:power:pass', nodeType: 'rule', title: '是否满足校核条件' },
      { id: 'param:power:滚筒转速', nodeType: 'parameter', title: '滚筒转速' }
    ]
  )

  const powerStep = graph.nodes.find((item) => item.id === 'step:power')
  const powerResult = graph.nodes.find((item) => item.id === 'result:power')
  const powerRule = graph.nodes.find((item) => item.id === 'rule:power:pass')
  const powerParam = graph.nodes.find((item) => item.id === 'param:power:滚筒转速')
  assert.equal(powerRule.y < powerResult.y, true)
  assert.equal(powerResult.y < powerStep.y, true)
  assert.equal(powerStep.y < powerParam.y, true)
})

run('resolveWorkbenchProcessSelectedNode 返回步骤摘要而不是公式能力', () => {
  const selected = resolveWorkbenchProcessSelectedNode(
    {
      nodes: [
        {
          id: 'step:power',
          nodeType: 'step',
          title: '功率校核',
          summary: '当前结果 18.6 kW',
          stepCode: 'power'
        }
      ]
    },
    'step:power'
  )

  assert.deepEqual(selected, {
    nodeId: 'step:power',
    nodeType: 'step',
    title: '功率校核',
    summary: '当前结果 18.6 kW',
    stepCode: 'power'
  })
})

run('buildWorkbenchProcessPanelContext 返回计算理由面板上下文', () => {
  const graph = {
    nodes: [
      {
        id: 'step:power',
        nodeType: 'step',
        title: '功率校核',
        stepCode: 'power',
        panelContext: {
          explanation: {
            nodeId: 'step:power',
            nodeType: 'step',
            purpose: '确定驱动系统所需功率是否满足设计要求',
            keyInputs: [{ paramName: '滚筒转速', value: '9.8', unit: 'rpm', source: '矩阵参数' }],
            derivation: '结合摩擦力矩和转速计算推荐电机功率，并引用标准值进行比对',
            impact: '校核通过后保留当前功率建议并进入结果输出'
          }
        }
      }
    ]
  }

  assert.deepEqual(buildWorkbenchProcessPanelContext(graph, 'step:power'), {
    title: '功率校核',
    nodeType: 'step',
    explanation: {
      nodeId: 'step:power',
      nodeType: 'step',
      purpose: '确定驱动系统所需功率是否满足设计要求',
      keyInputs: [{ paramName: '滚筒转速', value: '9.8', unit: 'rpm', source: '矩阵参数' }],
      derivation: '结合摩擦力矩和转速计算推荐电机功率，并引用标准值进行比对',
      impact: '校核通过后保留当前功率建议并进入结果输出'
    },
    summary: [],
    parameters: [],
    lookups: [],
    constraints: []
  })
})

run('buildCurveUpgradeHint 识别可迁移的旧 VLOOKUP 公式', () => {
  assert.deepEqual(
    buildCurveUpgradeHint('=142*VLOOKUP(电机频率,电机扭矩参数!B:C,2,0)'),
    {
      multiplier: '142',
      inputName: '电机频率',
      lookupName: '电机扭矩参数'
    }
  )
})

run('buildCurveFormulaExpression 生成 CURVE2D 公式', () => {
  assert.equal(
    buildCurveFormulaExpression({
      lookupName: '电机扭矩参数',
      inputName: '电机频率',
      seriesKey: 'DRE',
      direction: 'X2Y',
      lookupMode: 'LINEAR',
      multiplier: '142'
    }),
    '=142*CURVE2D(电机扭矩参数,电机频率,DRE,X2Y,LINEAR)'
  )
})

run('parseCurveFormulaExpression 解析已存在公式用于回显', () => {
  assert.deepEqual(
    parseCurveFormulaExpression('=142*CURVE2D(电机扭矩参数,电机频率,DRE,X2Y,LINEAR)'),
    {
      multiplier: '142',
      lookupName: '电机扭矩参数',
      inputName: '电机频率',
      seriesKey: 'DRE',
      direction: 'X2Y',
      lookupMode: 'LINEAR'
    }
  )
})

run('toggleFormulaBatchSelection 在未选中时加入、已选中时移除', () => {
  assert.deepEqual(toggleFormulaBatchSelection([], 'id:11'), ['id:11'])
  assert.deepEqual(toggleFormulaBatchSelection(['id:11', 'id:15'], 'id:11'), ['id:15'])
})

run('resolveNextFocusAfterFormulaDelete 删除当前行后优先聚焦下一条', () => {
  const resolved = resolveNextFocusAfterFormulaDelete({
    modules: [
      {
        moduleCode: 'power_calc',
        scenes: [
          {
            sceneCode: 'power',
            rows: [
              { _rowKey: 'id:11', module_code: 'power_calc', scene_code: 'power' },
              { _rowKey: 'id:15', module_code: 'power_calc', scene_code: 'power' },
              { _rowKey: 'id:18', module_code: 'power_calc', scene_code: 'power' }
            ]
          }
        ]
      }
    ],
    activeModuleCode: 'power_calc',
    activeSceneCode: 'power',
    activeFormulaKey: 'id:15',
    deletedFormulaKey: 'id:15'
  })

  assert.equal(resolved.activeModuleCode, 'power_calc')
  assert.equal(resolved.activeSceneCode, 'power')
  assert.equal(resolved.activeFormulaKey, 'id:18')
})

run('resolveNextFocusAfterFormulaDelete 删除场景最后一条公式时清空公式焦点', () => {
  const resolved = resolveNextFocusAfterFormulaDelete({
    modules: [
      {
        moduleCode: 'power_calc',
        scenes: [
          {
            sceneCode: 'power',
            rows: [
              { _rowKey: 'id:11', module_code: 'power_calc', scene_code: 'power' }
            ]
          }
        ]
      }
    ],
    activeModuleCode: 'power_calc',
    activeSceneCode: 'power',
    activeFormulaKey: 'id:11',
    deletedFormulaKey: 'id:11'
  })

  assert.equal(resolved.activeModuleCode, 'power_calc')
  assert.equal(resolved.activeSceneCode, 'power')
  assert.equal(resolved.activeFormulaKey, '')
  assert.equal(resolved.activeFormula, null)
})

run('buildFormulaSyncPreviewViewModel 构造前端弹窗视图模型', () => {
  const backendPreview = {
    source_module: {
      module_code: "DRUM_DRIVE",
      module_name: "滚筒驱动",
      formula_count: 5
    },
    target_model_id: 2,
    sync_status: "ready",
    mappings_to_confirm: [
      { source_param_name: "L1", is_resolved: true, mapped_target_parameter_id: 101, mapped_target_parameter_name: "长度", auto_mapped: false },
      { source_param_name: "W1", is_resolved: false, mapped_target_parameter_id: null, mapped_target_parameter_name: null, auto_mapped: false }
    ],
    auto_mappings: [
      { source_param_name: "电机转速", mapped_target_parameter_id: 102, mapped_target_parameter_name: "电机转速" }
    ]
  }

  const viewModel = buildFormulaSyncPreviewViewModel(backendPreview)
  
  assert.equal(viewModel.sourceModuleName, "滚筒驱动")
  assert.equal(viewModel.formulaCount, 5)
  assert.equal(viewModel.canSync, false)
  
  assert.equal(viewModel.unresolvedMappings.length, 1)
  assert.equal(viewModel.unresolvedMappings[0].sourceName, "W1")
  
  assert.equal(viewModel.resolvedMappings.length, 2)
  const l1 = viewModel.resolvedMappings.find(m => m.sourceName === "L1")
  assert.equal(l1.targetName, "长度")
  const auto = viewModel.resolvedMappings.find(m => m.sourceName === "电机转速")
  assert.equal(auto.isAutoMapped, true)
})

run('resolveNextFocusAfterFormulaBatchDelete 在当前场景保留第一条剩余公式为焦点', () => {
  const resolved = resolveNextFocusAfterFormulaBatchDelete({
    modules: [
      {
        moduleCode: 'power_calc',
        scenes: [
          {
            sceneCode: 'power',
            rows: [
              { _rowKey: 'id:11', module_code: 'power_calc', scene_code: 'power' },
              { _rowKey: 'id:15', module_code: 'power_calc', scene_code: 'power' },
              { _rowKey: 'id:18', module_code: 'power_calc', scene_code: 'power' }
            ]
          }
        ]
      }
    ],
    activeModuleCode: 'power_calc',
    activeSceneCode: 'power',
    deletedFormulaKeys: ['id:11', 'id:15']
  })

  assert.equal(resolved.activeModuleCode, 'power_calc')
  assert.equal(resolved.activeSceneCode, 'power')
  assert.equal(resolved.activeFormulaKey, 'id:18')
})

run('resolveNextFocusAfterFormulaBatchDelete 在场景删空时清空公式焦点', () => {
  const resolved = resolveNextFocusAfterFormulaBatchDelete({
    modules: [
      {
        moduleCode: 'power_calc',
        scenes: [
          {
            sceneCode: 'power',
            rows: [
              { _rowKey: 'id:11', module_code: 'power_calc', scene_code: 'power' }
            ]
          }
        ]
      }
    ],
    activeModuleCode: 'power_calc',
    activeSceneCode: 'power',
    deletedFormulaKeys: ['id:11']
  })

  assert.equal(resolved.activeModuleCode, 'power_calc')
  assert.equal(resolved.activeSceneCode, 'power')
  assert.equal(resolved.activeFormulaKey, '')
  assert.equal(resolved.activeFormula, null)
})
