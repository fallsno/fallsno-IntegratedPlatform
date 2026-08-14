import assert from 'node:assert/strict'

import {
  hasMeaningfulCurveProfileChange,
  buildAppendixChartTableModel,
  buildCurveProfileDraftFromImportPreview,
  buildCurveProfileDraftFromLookupRows,
  buildLookupCurveChartOption,
  normalizeParameterLookupCurveProfile,
  normalizeParameterLookupForm,
  normalizeParameterLookupPreview,
  normalizeParameterLookupRows
} from './parameterLookup.helpers.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('normalizeParameterLookupForm 补齐默认字段', () => {
  assert.deepEqual(normalizeParameterLookupForm({ lookup_code: 'MOTOR_TORQUE', lookup_name: '电机扭矩参数' }), {
    lookup_code: 'MOTOR_TORQUE',
    lookup_name: '电机扭矩参数',
    description: '',
    status: 'active'
  })
})

run('normalizeParameterLookupRows 过滤空行并保留顺序', () => {
  assert.deepEqual(
    normalizeParameterLookupRows([
      { lookup_key: '50', result_value: '1' },
      { lookup_key: '', result_value: '' },
      { lookup_key: '51', result_value: '0.988' }
    ]),
    [
      { lookup_key: '50', result_value: '1', sort_order: 0, remark: '' },
      { lookup_key: '51', result_value: '0.988', sort_order: 1, remark: '' }
    ]
  )
})

run('normalizeParameterLookupPreview 标准化错误结构', () => {
  assert.deepEqual(
    normalizeParameterLookupPreview({
      rows: [{ lookup_key: '50', result_value: '1' }],
      errors: [{ row_no: 2, message: 'lookup_key 重复: 50' }],
      table_columns: ['电机扭矩', 'DRN', 'DRE', '备注'],
      table_rows: [{ 电机扭矩: '50', DRN: '1', DRE: '1', 备注: '' }]
    }),
    {
      rows: [{ lookup_key: '50', result_value: '1', sort_order: 0, remark: '' }],
      errors: [{ row_no: 2, message: 'lookup_key 重复: 50' }],
      table_columns: ['电机扭矩', 'DRN', 'DRE', '备注'],
      table_rows: [{ 电机扭矩: '50', DRN: '1', DRE: '1', 备注: '' }]
    }
  )
})

run('normalizeParameterLookupCurveProfile 规范化系列配置', () => {
  assert.deepEqual(
    normalizeParameterLookupCurveProfile({
      profile_name: ' 电机扭矩参数 ',
      x_axis_column: ' 电机频率 ',
      table_columns: ['电机频率', 'DRN', 'DRE', '备注', ''],
      table_rows: [
        { 电机频率: '30', DRN: '1', DRE: '0.904', 备注: '说明' }
      ],
      series_columns: [
        { series_key: ' DRN ', source_column: ' DRN ', reverse_lookup_enabled: false },
        { series_key: ' DRE ', source_column: ' DRE ', reverse_lookup_enabled: true }
      ],
      note_columns: ['备注', '备注', ''],
      default_lookup_mode: ' LINEAR ',
      allow_interpolation: true
    }),
    {
      profile_name: '电机扭矩参数',
      x_axis_column: '电机频率',
      table_columns: ['电机频率', 'DRN', 'DRE', '备注'],
      table_rows: [
        { 电机频率: '30', DRN: '1', DRE: '0.904', 备注: '说明' }
      ],
      series_columns: [
        { series_key: 'DRN', source_column: 'DRN', reverse_lookup_enabled: false },
        { series_key: 'DRE', source_column: 'DRE', reverse_lookup_enabled: true }
      ],
      note_columns: ['备注'],
      default_lookup_mode: 'LINEAR',
      allow_interpolation: true
    }
  )
})

run('buildLookupCurveChartOption 生成多曲线配置', () => {
  const option = buildLookupCurveChartOption({
    x_axis_column: '电机频率',
    series: [
      {
        series_key: 'DRN',
        source_column: 'DRN',
        reverse_lookup_enabled: false,
        is_monotonic: false,
        points: [{ x: 30, y: 1 }, { x: 31, y: 1 }]
      },
      {
        series_key: 'DRE',
        source_column: 'DRE',
        reverse_lookup_enabled: true,
        is_monotonic: true,
        points: [{ x: 30, y: 0.904 }, { x: 31, y: 0.908 }]
      }
    ]
  })

  assert.equal(option.xAxis.name, '电机频率')
  assert.equal(option.xAxis.scale, true)
  assert.equal(option.yAxis.scale, true)
  assert.equal(option.grid.containLabel, true)
  assert.equal(option.series.length, 2)
  assert.equal(option.series[0].name, 'DRN')
  assert.deepEqual(option.series[1].data, [[30, 0.904], [31, 0.908]])
})

run('buildCurveProfileDraftFromLookupRows 直接复用附录行作为曲线源数据', () => {
  assert.deepEqual(
    buildCurveProfileDraftFromLookupRows(
      [
        { lookup_key: '30', result_value: '1', remark: '默认值' },
        { lookup_key: '31', result_value: '0.988', remark: '' }
      ],
      { profile_name: '电机扭矩参数曲线', series_columns: [{ series_key: 'DRN', source_column: '结果值', reverse_lookup_enabled: false }] }
    ),
    {
      profile_name: '电机扭矩参数曲线',
      x_axis_column: '查找值',
      table_columns: ['查找值', '结果值', '备注'],
      table_rows: [
        { 查找值: '30', 结果值: '1', 备注: '默认值' },
        { 查找值: '31', 结果值: '0.988', 备注: '' }
      ],
      series_columns: [{ series_key: 'DRN', source_column: '结果值', reverse_lookup_enabled: false }],
      note_columns: ['备注'],
      default_lookup_mode: 'LINEAR',
      allow_interpolation: true
    }
  )
})

run('buildCurveProfileDraftFromImportPreview 保留原表格列结构', () => {
  assert.deepEqual(
    buildCurveProfileDraftFromImportPreview({
      table_columns: ['电机扭矩', 'DRN电机扭矩参数参考数值', 'DRE电机扭矩参数参考数值', '备注'],
      table_rows: [
        { 电机扭矩: '30', DRN电机扭矩参数参考数值: '1', DRE电机扭矩参数参考数值: '0.904', 备注: 'DRE型号使用' }
      ]
    }),
    {
      profile_name: '',
      x_axis_column: '电机扭矩',
      table_columns: ['电机扭矩', 'DRN电机扭矩参数参考数值', 'DRE电机扭矩参数参考数值', '备注'],
      table_rows: [
        { 电机扭矩: '30', DRN电机扭矩参数参考数值: '1', DRE电机扭矩参数参考数值: '0.904', 备注: 'DRE型号使用' }
      ],
      series_columns: [],
      note_columns: ['备注'],
      default_lookup_mode: 'LINEAR',
      allow_interpolation: true
    }
  )
})

run('buildAppendixChartTableModel 优先返回原表结构', () => {
  assert.deepEqual(
    buildAppendixChartTableModel(
      [{ lookup_key: '30', result_value: '1', remark: '默认值' }],
      {
        table_columns: ['电机扭矩', 'DRN', 'DRE', '备注'],
        table_rows: [{ 电机扭矩: '30', DRN: '1', DRE: '0.904', 备注: 'DRE型号使用' }]
      }
    ),
    {
      columns: ['电机扭矩', 'DRN', 'DRE', '备注'],
      rows: [{ 电机扭矩: '30', DRN: '1', DRE: '0.904', 备注: 'DRE型号使用' }],
      mode: 'table'
    }
  )
})

run('buildAppendixChartTableModel 在无原表时回退到旧附录行', () => {
  assert.deepEqual(
    buildAppendixChartTableModel([{ lookup_key: '30', result_value: '1', remark: '默认值' }], {}),
    {
      columns: ['查找值', '结果值', '备注'],
      rows: [{ 查找值: '30', 结果值: '1', 备注: '默认值' }],
      mode: 'rows'
    }
  )
})

run('hasMeaningfulCurveProfileChange 在归一化后相同的 profile 上返回 false', () => {
  assert.equal(
    hasMeaningfulCurveProfileChange(
      {
        profile_name: ' 电机扭矩参数 ',
        x_axis_column: ' 电机扭矩 ',
        table_columns: ['电机扭矩', 'DRN', '备注'],
        table_rows: [{ 电机扭矩: '30', DRN: '1', 备注: '' }],
        series_columns: [{ series_key: ' DRN ', source_column: ' DRN ', reverse_lookup_enabled: false }],
        note_columns: ['备注', '备注'],
        default_lookup_mode: ' LINEAR ',
        allow_interpolation: true
      },
      {
        profile_name: '电机扭矩参数',
        x_axis_column: '电机扭矩',
        table_columns: ['电机扭矩', 'DRN', '备注'],
        table_rows: [{ 电机扭矩: '30', DRN: '1', 备注: '' }],
        series_columns: [{ series_key: 'DRN', source_column: 'DRN', reverse_lookup_enabled: false }],
        note_columns: ['备注'],
        default_lookup_mode: 'LINEAR',
        allow_interpolation: true
      }
    ),
    false
  )
})
