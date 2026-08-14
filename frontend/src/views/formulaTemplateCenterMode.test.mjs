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

run('WorkbenchFormulaMainTable 支持模板模式与只读模式切换', () => {
  const source = read('../components/WorkbenchFormulaMainTable.vue')
  assert.match(source, /isTemplateMode/)
  assert.match(source, /showSceneActions/)
  assert.match(source, /showRowActions/)
})

run('NewDesignWorkbench 以只读模板执行模式使用主公式表', () => {
  const source = read('./NewDesignWorkbench.vue')
  assert.match(source, /:is-template-mode="false"/)
  assert.match(source, /fetchModelWorkbenchInstance/)
})

run('路由注册独立公式模板中心与编辑页', () => {
  const source = read('../router/index.js')
  assert.match(source, /\/formula-templates/)
  assert.match(source, /FormulaTemplateCenter/)
  assert.match(source, /TemplateEditor/)
})
