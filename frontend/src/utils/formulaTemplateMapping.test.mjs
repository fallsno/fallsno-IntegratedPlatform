import assert from 'node:assert/strict'

import {
  getFormulaTargetOptions,
  getRequiredMappings,
  buildFormulaLinkPayload
} from './formulaTemplateMapping.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

const sampleFormula = {
  id: 12,
  name: '电机功率公式',
  expression: '1.732 * U * I * cosΦ * η',
  canonical_expression: 'P = 1.732 * U * I * cosΦ * η',
  solve_targets: {
    P: {
      expression: '1.732 * U * I * cosΦ * η',
      required_variables: ['U', 'I', 'cosΦ', 'η'],
      description: '求功率'
    },
    I: {
      expression: 'P / (1.732 * U * cosΦ * η)',
      required_variables: ['P', 'U', 'cosΦ', 'η'],
      description: '求电流'
    }
  }
}

const legacyFormula = {
  id: 13,
  name: '旧版面积公式',
  expression: '长度 * 宽度',
  variables: {
    长度: '长度',
    宽度: '宽度'
  }
}

run('返回显式配置的目标参数选项', () => {
  assert.deepEqual(getFormulaTargetOptions(sampleFormula), [
    { key: 'P', expression: '1.732 * U * I * cosΦ * η', requiredVariables: ['U', 'I', 'cosΦ', 'η'], description: '求功率' },
    { key: 'I', expression: 'P / (1.732 * U * cosΦ * η)', requiredVariables: ['P', 'U', 'cosΦ', 'η'], description: '求电流' }
  ])
})

run('目标参数不参与待映射变量列表', () => {
  assert.deepEqual(getRequiredMappings(sampleFormula, 'I'), ['P', 'U', 'cosΦ', 'η'])
})

run('生成落地表达式与公式元数据', () => {
  const payload = buildFormulaLinkPayload({
    formula: sampleFormula,
    targetKey: 'I',
    mappings: {
      P: '电机功率P',
      U: '电压V',
      'cosΦ': '功率因数',
      'η': '效率'
    },
    rowName: '电机电流 A'
  })

  assert.equal(payload.expression, '=电机功率P / (1.732 * 电压V * 功率因数 * 效率)')
  assert.equal(payload.formula_name, '电机功率公式')
  assert.equal(payload.formula_id, 12)
  assert.equal(payload.formula_target, 'I')
  assert.equal(payload.formula_source_expression, 'P / (1.732 * U * cosΦ * η)')
  assert.deepEqual(payload.formula_mappings, {
    P: '电机功率P',
    U: '电压V',
    'cosΦ': '功率因数',
    'η': '效率'
  })
  assert.match(payload.note, /电机功率公式/)
})

run('缺少必填变量映射时抛出明确错误', () => {
  assert.throws(
    () => buildFormulaLinkPayload({
      formula: sampleFormula,
      targetKey: 'I',
      mappings: {
        P: '电机功率P'
      }
    }),
    /缺少必填变量映射/
  )
})

run('旧公式在没有 solve_targets 时保持默认引入能力', () => {
  const options = getFormulaTargetOptions(legacyFormula)
  assert.equal(options.length, 1)
  assert.equal(options[0].key, '__default__')

  const payload = buildFormulaLinkPayload({
    formula: legacyFormula,
    targetKey: '__default__',
    mappings: {
      长度: '滚筒长度 mm',
      宽度: '滚筒宽度 mm'
    }
  })

  assert.equal(payload.expression, '=滚筒长度 mm * 滚筒宽度 mm')
  assert.equal(payload.formula_target, '__default__')
})
