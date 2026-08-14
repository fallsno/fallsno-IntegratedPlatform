import assert from 'node:assert/strict'

import {
  buildFamilyMatrixPayload,
  buildParameterCode,
  buildParameterDistributionRows,
  buildParameterQuery,
  buildWorkbenchSnapshotPayload,
  mergeWorkbenchModelRows,
  mergeWorkbenchCatalogRows,
  normalizeParameterStats,
  normalizeParameterForm,
  normalizeTemplateDiffStats
} from './designPlatform.helpers.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('normalizeParameterForm 填充参数默认值', () => {
  assert.deepEqual(
    normalizeParameterForm({ param_code: 'ROLLER_DIAMETER', param_name: '滚筒直径' }),
    {
      param_code: 'ROLLER_DIAMETER',
      param_name: '滚筒直径',
      display_name: '滚筒直径',
      category_code: 'uncategorized',
      unit_code: '',
      value_type: 'basic',
      data_type: 'number',
      precision: 2,
      default_value: '',
      description: '',
      status: 'active'
    }
  )
})

run('normalizeParameterForm 保留可编辑字段并补齐默认值', () => {
  assert.deepEqual(
    normalizeParameterForm({
      param_code: 'ROLLER_WEIGHT',
      param_name: '滚筒重量',
      display_name: '滚筒重量',
      unit_code: 'kg',
      default_value: '8200',
      description: '参数中心维护'
    }),
    {
      param_code: 'ROLLER_WEIGHT',
      param_name: '滚筒重量',
      display_name: '滚筒重量',
      category_code: 'uncategorized',
      unit_code: 'kg',
      value_type: 'basic',
      data_type: 'number',
      precision: 2,
      default_value: '8200',
      description: '参数中心维护',
      status: 'active'
    }
  )
})

run('buildParameterCode 从中文名称生成稳定编码', () => {
  assert.equal(buildParameterCode('滚筒重量'), 'PARAM_GUN_TONG_ZHONG_LIANG')
})

run('mergeWorkbenchCatalogRows 按 草稿/快照/参数中心/矩阵 优先级合并', () => {
  const rows = mergeWorkbenchCatalogRows({
    catalogRows: [
      { id: 1, param_code: 'ROLLER_WEIGHT', param_name: '滚筒重量', unit_code: 'kg', default_value: '8200' }
    ],
    matrixRows: [
      { parameterId: 1, paramCode: 'ROLLER_WEIGHT', paramName: '滚筒重量', unitCode: 'kg', value: '7800', dirty: false, source: 'matrix' }
    ],
    snapshotMap: new Map([[1, '8100']])
  })

  assert.equal(rows[0].value, '8100')
  assert.equal(rows[0].defaultValue, '8200')
  assert.equal(rows[0].source, 'snapshot')
})

run('buildParameterQuery 只保留有效筛选项', () => {
  assert.deepEqual(
    buildParameterQuery({ keyword: '滚筒', category_code: 'basic', extra: '' }),
    { keyword: '滚筒', category_code: 'basic' }
  )
})

run('normalizeTemplateDiffStats 生成统一摘要', () => {
  assert.deepEqual(
    normalizeTemplateDiffStats({ added_flows: 1, updated_steps: 2, affected_rows: 3 }),
    {
      added_flows: 1,
      updated_steps: 2,
      affected_rows: 3,
      summary: '新增流程 1，更新步骤 2，影响参数行 3'
    }
  )
})

run('buildFamilyMatrixPayload 扁平化矩阵单元格', () => {
  assert.deepEqual(
    buildFamilyMatrixPayload([
      { parameter_id: 1, values: { 11: '80', 12: '130' } }
    ]),
    {
      rows: [
        { version_id: 11, parameter_id: 1, param_value: '80' },
        { version_id: 12, parameter_id: 1, param_value: '130' }
      ]
    }
  )
})

run('buildWorkbenchSnapshotPayload 过滤空 runKey', () => {
  assert.throws(() => buildWorkbenchSnapshotPayload('', []))
})

run('buildWorkbenchSnapshotPayload 输出后端所需结构', () => {
  assert.deepEqual(
    buildWorkbenchSnapshotPayload('wb-001', [
      { version_id: 8, parameter_id: 1, snapshot_value: '80' }
    ]),
    {
      run_key: 'wb-001',
      rows: [{ version_id: 8, parameter_id: 1, snapshot_value: '80' }]
    }
  )
})

run('buildParameterDistributionRows 将分布结构转成矩阵侧栏列表', () => {
  assert.deepEqual(
    buildParameterDistributionRows({
      parameter_id: 1,
      param_name: '滚筒重量',
      values: [
        { version_id: 11, version_code: 'RT80', param_value: '7236.5' },
        { version_id: 12, version_code: 'RT130', param_value: '11963' }
      ]
    }),
    [
      { versionId: 11, versionCode: 'RT80', value: '7236.5' },
      { versionId: 12, versionCode: 'RT130', value: '11963' }
    ]
  )
})

run('mergeWorkbenchModelRows 按 草稿/型号值/快照/定义兜底 优先级合并', () => {
  const rows = mergeWorkbenchModelRows({
    modelRows: [
      { parameterId: 1, paramCode: 'ROLLER_WEIGHT', paramName: '滚筒重量', unitCode: 'kg', value: '7236.5', dirty: false, source: 'model' }
    ],
    snapshotMap: new Map([[1, '7000']]),
    catalogRows: [
      { id: 1, param_code: 'ROLLER_WEIGHT', param_name: '滚筒重量', default_value: '6800' }
    ]
  })

  assert.equal(rows[0].value, '7236.5')
  assert.equal(rows[0].source, 'model')
  assert.equal(rows[0].defaultValue, '6800')
})

run('normalizeParameterStats 生成统计卡片默认值', () => {
  assert.deepEqual(
    normalizeParameterStats({ min_value: '0', max_value: '240' }),
    {
      min_value: '0',
      max_value: '240',
      avg_value: '',
      sample_count: 0
    }
  )
})
