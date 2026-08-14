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

run('DesignWorkbench 移除顶部摘要统计与当前公式说明', () => {
  const source = read('./DesignWorkbench.vue')
  assert.doesNotMatch(source, /summary-subtitle/)
  assert.doesNotMatch(source, /summary-metrics/)
  assert.doesNotMatch(source, /当前公式 \{\{ activeFormulaContext\.name \}\}/)
})

run('WorkbenchFormulaModuleCard 移除常驻模块统计文案', () => {
  const source = read('../components/WorkbenchFormulaModuleCard.vue')
  assert.doesNotMatch(source, /module-card__meta/)
  assert.doesNotMatch(source, />当前模块</)
})

run('WorkbenchFormulaSceneGroup 移除常驻场景统计文案', () => {
  const source = read('../components/WorkbenchFormulaSceneGroup.vue')
  assert.doesNotMatch(source, /scene-focus-group__tab-meta/)
  assert.doesNotMatch(source, /scene-focus-group__meta/)
  assert.doesNotMatch(source, />当前场景 /)
})

run('WorkbenchFormulaPathBar 使用极简占位而不是说明式占位', () => {
  const source = read('../components/WorkbenchFormulaPathBar.vue')
  assert.doesNotMatch(source, /未选模块/)
  assert.doesNotMatch(source, /未选场景/)
  assert.doesNotMatch(source, /未选公式/)
})

run('DrumCategoryTree 移除副标题与层级统计文案', () => {
  const source = read('../components/DrumCategoryTree.vue')
  assert.doesNotMatch(source, /tree-subtitle/)
  assert.doesNotMatch(source, /levelMeta/)
  assert.doesNotMatch(source, /buildNodeMeta/)
  assert.doesNotMatch(source, /按分类、系列、型号浏览滚筒对象/)
})

run('WorkbenchParameterPanel 移除常驻状态标签与来源说明', () => {
  const source = read('../components/WorkbenchParameterPanel.vue')
  assert.doesNotMatch(source, /subtitle/)
  assert.doesNotMatch(source, /parameter-row__tags/)
  assert.doesNotMatch(source, /当前公式引用/)
  assert.doesNotMatch(source, /参数库默认值/)
  assert.doesNotMatch(source, /待保存/)
  assert.doesNotMatch(source, /sourceLabelMap/)
  assert.doesNotMatch(source, /intermediate-row__meta/)
})

run('WorkbenchFormulaEditor 使用精简快捷区与参数位提示', () => {
  const source = read('../components/WorkbenchFormulaEditor.vue')
  assert.doesNotMatch(source, /label:\s*'VLOOKUP\(\)'/)
  assert.doesNotMatch(source, /label:\s*'CURVE2D\(\)'/)
  assert.match(source, /autocompleteSections/)
  assert.match(source, /argumentHint/)
  assert.match(source, /formula-argument-hint/)
})

run('DesignWorkbench 向行内编辑器传入分组联想与参数位提示', () => {
  const source = read('./DesignWorkbench.vue')
  assert.match(source, /:autocomplete-sections="autocompleteSections"/)
  assert.match(source, /:argument-hint="activeFormulaArgumentHint"/)
})

run('DesignWorkbench 提供公式视图与计算链路视图切换', () => {
  const source = read('./DesignWorkbench.vue')
  assert.match(source, /workbenchViewMode/)
  assert.match(source, /label: '设计公式'/)
  assert.match(source, /label: '计算链路'/)
  assert.match(source, /WorkbenchCalculationFlowPanel/)
})
