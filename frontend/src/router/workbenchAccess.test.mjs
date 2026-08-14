import assert from 'node:assert/strict'

import {
  canEnterExistingDesignWorkbench
} from './workbenchAccess.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('每个产品大类下的每个计算模块都可以进入自己的工作台', () => {
  assert.equal(canEnterExistingDesignWorkbench({ typeId: '62', moduleCode: 'power_calc' }), true)
  assert.equal(canEnterExistingDesignWorkbench({ typeId: '62', moduleCode: 'leg_calc' }), true)
  assert.equal(canEnterExistingDesignWorkbench({ typeId: '6', moduleCode: 'power_calc' }), true)
  assert.equal(canEnterExistingDesignWorkbench({ typeId: '67', moduleCode: 'structure_calc' }), true)
})

run('缺少产品大类或模块编码时禁止直接打开工作台', () => {
  assert.equal(canEnterExistingDesignWorkbench({ typeId: '62' }), false)
  assert.equal(canEnterExistingDesignWorkbench({ moduleCode: 'power_calc' }), false)
})
