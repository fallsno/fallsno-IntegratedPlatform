import assert from 'node:assert/strict'

import {
  buildEmptyOnlyMatrixImportRows,
  detectRt300WorkbookSheets
} from './parameterLookupWorkbook.helpers.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('detectRt300WorkbookSheets 识别 RT300 关键工作表', () => {
  assert.deepEqual(
    detectRt300WorkbookSheets(['SEW电机核算', '电机扭矩参数', '滚筒电机核算']),
    {
      workbookType: 'rt300',
      lookupSheetName: '电机扭矩参数',
      matrixSheetName: '滚筒电机核算'
    }
  )
})

run('buildEmptyOnlyMatrixImportRows 只保留平台当前为空的值', () => {
  const result = buildEmptyOnlyMatrixImportRows(
    [
      {
        paramName: '滚筒产量',
        unitCode: 't/h',
        categoryName: '滚筒粘料计算',
        values: {
          '再生80': '80',
          '再生130': '130'
        }
      },
      {
        paramName: '新增参数',
        unitCode: '',
        categoryName: '未分类',
        values: {
          '再生80': '10'
        }
      }
    ],
    [
      {
        paramName: '滚筒产量',
        values: {
          11: '80',
          12: ''
        }
      }
    ],
    [
      { id: 11, version_code: '再生80' },
      { id: 12, version_code: '再生130' }
    ]
  )

  assert.deepEqual(result, {
    parameterRows: [
      {
        paramName: '滚筒产量',
        unitCode: 't/h',
        categoryName: '滚筒粘料计算',
        values: {
          '再生130': '130'
        }
      },
      {
        paramName: '新增参数',
        unitCode: '',
        categoryName: '未分类',
        values: {
          '再生80': '10'
        }
      }
    ],
    keptValueCount: 2,
    skippedValueCount: 1
  })
})
