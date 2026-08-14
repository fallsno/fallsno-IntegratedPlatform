import assert from 'node:assert/strict'
import fs from 'node:fs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

const read = (filePath) => fs.readFileSync(new URL(filePath, import.meta.url), 'utf8')

run('WorkbenchFormulaSceneGroup 使用双击标题进入场景重命名', () => {
  const source = read('../components/WorkbenchFormulaSceneGroup.vue')
  assert.match(source, /@dblclick/)
  assert.match(source, /scene-focus-group__title-input/)
  assert.doesNotMatch(source, /content="重命名场景"/)
})

run('WorkbenchFormulaSceneGroup 仅为删除场景保留 hover 危险入口', () => {
  const source = read('../components/WorkbenchFormulaSceneGroup.vue')
  assert.match(source, /scene-focus-group__actions--danger/)
  assert.match(source, /scene-focus-group__delete-button/)
})

run('WorkbenchFormulaList 为工具区加入公式单删按钮并在批量模式隐藏', () => {
  const source = read('../components/WorkbenchFormulaList.vue')
  assert.match(source, /formula-row__delete-button/)
  assert.match(source, /v-if="!batchMode"/)
  assert.match(source, /emit\('delete', row\)/)
})
