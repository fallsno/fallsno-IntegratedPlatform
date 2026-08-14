import assert from 'node:assert/strict'

import {
  buildOrientationOptions,
  normalizeMatrixPreview
} from './parameterMatrixImport.helpers.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('normalizeMatrixPreview 保留方向与预览行', () => {
  const preview = normalizeMatrixPreview({
    orientation: 'parameters_in_rows',
    version_headers: ['RT80', 'RT130'],
    rows: [{ param_name: '传动比', unit_code: '-', values: { RT80: '8', RT130: '10' } }]
  })

  assert.equal(preview.orientation, 'parameters_in_rows')
  assert.equal(preview.rows[0].values.RT80, '8')
})

run('normalizeMatrixPreview 保留分类字段和警告', () => {
  const preview = normalizeMatrixPreview({
    orientation: 'parameters_in_rows',
    version_headers: ['RT80'],
    warnings: ['存在未命中系统型号的表头值，已跳过'],
    rows: [
      {
        param_name: '粘料高度',
        unit_code: 'm',
        category_name: '滚筒粘料计算',
        values: { RT80: '0' }
      }
    ]
  })

  assert.equal(preview.rows[0].categoryName, '滚筒粘料计算')
  assert.equal(preview.warnings[0], '存在未命中系统型号的表头值，已跳过')
})

run('buildOrientationOptions 输出自动识别与手动切换选项', () => {
  assert.deepEqual(buildOrientationOptions(), [
    { label: '自动识别', value: 'auto' },
    { label: '参数在行', value: 'parameters_in_rows' },
    { label: '参数在列', value: 'parameters_in_columns' }
  ])
})

run('normalizeMatrixPreview 为参数中心矩阵表保留型号列顺序', () => {
  const preview = normalizeMatrixPreview({
    version_headers: ['RT80', 'RT130'],
    rows: [{ param_name: '传动比', values: { RT80: '8', RT130: '10' } }]
  })

  assert.deepEqual(preview.versionHeaders, ['RT80', 'RT130'])
})
