import assert from 'node:assert/strict'

import {
  resolveFormulaVariablesFromExpression,
  resolveParameterInsertionDraft
} from './drumDesign.helpers.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('resolveFormulaVariablesFromExpression 按表达式提取变量并保持字符串映射', () => {
  const variables = resolveFormulaVariablesFromExpression('=1*2*3+存料量+滚筒转速', {
    存料量: 'kg',
    无关参数: 'm'
  })

  assert.deepEqual(variables, {
    存料量: 'kg',
    滚筒转速: ''
  })
})

run('resolveParameterInsertionDraft 在编辑态按光标位置插入参数', () => {
  const result = resolveParameterInsertionDraft({
    row: { paramName: '存料量' },
    editingFormulaKey: 'row-1',
    editingFormulaField: 'expression',
    activeFormulaDraft: { expression: '=1+2' },
    formulaCursorStart: 1
  })

  assert.equal(result.inserted, true)
  assert.equal(result.nextExpression, '=存料量1+2')
  assert.equal(result.nextCursorStart, 4)
})

run('resolveParameterInsertionDraft 在光标缺失时回退到末尾追加', () => {
  const result = resolveParameterInsertionDraft({
    row: { paramName: '存料量' },
    editingFormulaKey: 'row-1',
    editingFormulaField: 'expression',
    activeFormulaDraft: { expression: '=1+2' },
    formulaCursorStart: null
  })

  assert.equal(result.inserted, true)
  assert.equal(result.nextExpression, '=1+2存料量')
  assert.equal(result.nextCursorStart, 7)
})

run('resolveParameterInsertionDraft 非公式编辑态时不执行插入', () => {
  const result = resolveParameterInsertionDraft({
    row: { paramName: '存料量' },
    editingFormulaKey: '',
    editingFormulaField: '',
    activeFormulaDraft: { expression: '=1+2' },
    formulaCursorStart: 2
  })

  assert.equal(result.inserted, false)
  assert.equal(result.nextExpression, '=1+2')
  assert.equal(result.nextCursorStart, 2)
})

run('selectParameter 在编辑态插入后不会触发即时解析', () => {
  const before = {
    expression: '=1+2',
    editingFormulaKey: 'row-1',
    editingFormulaField: 'expression',
    formulaCursorStart: 2
  }
  const insertion = resolveParameterInsertionDraft({
    row: { paramName: '存料量' },
    editingFormulaKey: before.editingFormulaKey,
    editingFormulaField: before.editingFormulaField,
    activeFormulaDraft: { expression: before.expression },
    formulaCursorStart: before.formulaCursorStart
  })

  assert.equal(insertion.inserted, true)
  assert.equal(insertion.nextExpression, '=1存料量+2')
})
