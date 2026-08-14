import assert from 'node:assert/strict'

import {
  buildLookupSourceRows,
  buildLookupTargetQuery,
  resolveLookupFocusFromQuery
} from './drumDesignLookup.helpers.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('buildLookupSourceRows 仅输出当前公式的附录来源', () => {
  const rows = buildLookupSourceRows({
    activeFormula: { name: 'MN', expression: '=142*VLOOKUP(电机频率,电机扭矩参数!B:C,2,0)' },
    formulaResultMap: {
      MN: {
        value: '142',
        lookupDetail: {
          lookup_type: 'lookup',
          lookup_name: '电机扭矩参数',
          lookup_key: '50',
          result_value: '1',
          base_factor: '142'
        }
      },
      其他公式: {
        value: '99',
        lookupDetail: {
          lookup_type: 'curve',
          lookup_name: '别的附录'
        }
      }
    },
    lookupItems: [{ id: 18, lookup_name: '电机扭矩参数' }]
  })

  assert.equal(rows.length, 1)
  assert.equal(rows[0].lookupName, '电机扭矩参数')
  assert.equal(rows[0].jumpable, true)
})

run('buildLookupTargetQuery 生成附录图表跳转参数', () => {
  assert.deepEqual(
    buildLookupTargetQuery({
      lookupDetail: { lookup_name: '电机扭矩参数', series_key: 'DRN' },
      lookupItems: [{ id: 18, lookup_name: '电机扭矩参数' }],
      sourceFormulaName: 'MN'
    }),
    {
      tab: 'lookup',
      lookupId: '18',
      lookupName: '电机扭矩参数',
      seriesKey: 'DRN',
      fromFormula: 'MN'
    }
  )
})

run('resolveLookupFocusFromQuery 只接受 lookup 页签参数', () => {
  assert.deepEqual(
    resolveLookupFocusFromQuery({ tab: 'lookup', lookupId: '18', lookupName: '电机扭矩参数' }),
    { activeTab: 'lookup', lookupId: 18, lookupName: '电机扭矩参数', seriesKey: '', fromFormula: '' }
  )
  assert.equal(resolveLookupFocusFromQuery({ tab: 'matrix', lookupId: '18' }), null)
})
