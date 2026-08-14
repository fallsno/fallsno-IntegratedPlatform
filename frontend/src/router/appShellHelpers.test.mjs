import assert from 'node:assert/strict'

import {
  getRouteShellMode,
  shouldUseGlobalDesignChrome
} from './appShell.helpers.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('新工作台默认使用页面自管布局，不再叠加旧全局壳层', () => {
  assert.equal(
    getRouteShellMode({ name: 'DesignWorkbench' }),
    'page-managed'
  )
  assert.equal(
    shouldUseGlobalDesignChrome({ name: 'DesignWorkbench' }),
    false
  )
})

run('显式声明 legacy-design 的路由仍可启用旧全局壳层', () => {
  assert.equal(
    getRouteShellMode({ name: 'LegacyWorkbench', meta: { shellMode: 'legacy-design' } }),
    'legacy-design'
  )
  assert.equal(
    shouldUseGlobalDesignChrome({ name: 'LegacyWorkbench', meta: { shellMode: 'legacy-design' } }),
    true
  )
})
