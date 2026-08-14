import assert from 'node:assert/strict'

import { resolveWorkbenchTreeGroup } from './newDesignWorkbenchTreeGrouping.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('resolveWorkbenchTreeGroup 在选型树中将电机参数归入电机选型参数组', () => {
  assert.deepEqual(
    resolveWorkbenchTreeGroup(
      { paramName: '电机_额定功率', displayName: '电机额定功率', valueType: 'equipment' },
      'selection'
    ),
    { key: 'motor', label: '电机选型参数' }
  )
})

run('resolveWorkbenchTreeGroup 在选型树中将减速机参数归入减速机选型参数组', () => {
  assert.deepEqual(
    resolveWorkbenchTreeGroup(
      { paramName: '减速机_减速比', displayName: '减速机减速比', valueType: 'equipment' },
      'selection'
    ),
    { key: 'reducer', label: '减速机选型参数' }
  )
})

run('resolveWorkbenchTreeGroup 在输入树中保持结构参数归组', () => {
  assert.deepEqual(
    resolveWorkbenchTreeGroup(
      { paramName: '滚圈外径', displayName: '滚圈外径', valueType: 'product' },
      'input'
    ),
    { key: 'structure', label: '滚筒结构' }
  )
})

run('resolveWorkbenchTreeGroup 在输入树中保持工况参数归组', () => {
  assert.deepEqual(
    resolveWorkbenchTreeGroup(
      { paramName: '摩擦系数', displayName: '摩擦系数', valueType: 'environment' },
      'input'
    ),
    { key: 'condition', label: '工况参数' }
  )
})

run('resolveWorkbenchTreeGroup 在输入树中优先采用人工重分类结果', () => {
  assert.deepEqual(
    resolveWorkbenchTreeGroup(
      {
        paramName: '筒体重量',
        displayName: '筒体重量',
        provenance: {
          custom_group_key: 'structure',
          custom_group_label: '滚筒结构'
        }
      },
      'input'
    ),
    { key: 'structure', label: '滚筒结构' }
  )
})
