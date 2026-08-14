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

const source = fs.readFileSync(new URL('./WorkbenchCalculationFlowPanel.vue', import.meta.url), 'utf8')

run('WorkbenchCalculationFlowPanel 去掉顶部大卡片与常驻状态图例文字', () => {
  assert.doesNotMatch(source, /显示全部链路/)
  assert.doesNotMatch(source, /重置视图/)
  assert.doesNotMatch(source, /基础参数/)
  assert.doesNotMatch(source, /依据参数/)
  assert.doesNotMatch(source, /结果量/)
})

run('WorkbenchCalculationFlowPanel 节点卡片只保留名称和值', () => {
  assert.match(source, /flow-node__title/)
  assert.match(source, /flow-node__value/)
  assert.doesNotMatch(source, /flow-node__kicker/)
  assert.doesNotMatch(source, /flow-node__badge/)
})

run('WorkbenchCalculationFlowPanel 保留画布和缩放能力但不再有顶部工具卡', () => {
  assert.match(source, /workbench-flow__viewport/)
  assert.match(source, /workbench-flow__zoom-controls/)
  assert.doesNotMatch(source, /a-flow-view__topbar/)
  assert.doesNotMatch(source, /当前聚焦/)
  assert.doesNotMatch(source, /info-panel/)
  assert.doesNotMatch(source, /popup-card/)
})

run('WorkbenchCalculationFlowPanel 使用 A 页三带标签而不是旧的三层标签', () => {
  assert.match(source, /输入带/)
  assert.match(source, /共享主干/)
  assert.match(source, /结果带/)
  assert.doesNotMatch(source, /default: '输入条件'/)
  assert.doesNotMatch(source, /default: '计算与转换'/)
  assert.doesNotMatch(source, /default: '输出结果'/)
})

run('WorkbenchCalculationFlowPanel 使用 focus-state 保留上下文且空白点击不改变当前聚焦', () => {
  assert.match(source, /buildFocusStructureState/)
  assert.match(source, /@click\.self="handleSurfaceBlankClick"/)
  assert.match(source, /focusState\.value\.edgeStates/)
  assert.doesNotMatch(source, /emit\('select-node', \{\}\)/)
  assert.doesNotMatch(source, /selectedLineageNodeIds/)
})

run('WorkbenchCalculationFlowPanel 不再在 displayMode === all 时把整图打成 muted', () => {
  assert.doesNotMatch(source, /if \(props\.displayMode === 'all'\)/)
  assert.doesNotMatch(source, /nodeStates\.set\(node\.id, 'muted'\)/)
  assert.doesNotMatch(source, /edgeStates\.set\(`\$\{edge\.source\}->\$\{edge\.target\}`, 'muted'\)/)
})

run('WorkbenchCalculationFlowPanel 点击节点时不会误触发画布拖拽', () => {
  assert.match(source, /@pointerdown\.stop/)
  assert.match(source, /event\.target\?\.(closest)\?\.\('\.flow-node'\)/)
})

run('WorkbenchCalculationFlowPanel 共享主干内优先采用纵向承接布局', () => {
  assert.match(source, /label: props\.calculationLayerTitle/)
  assert.match(source, /node\.y = y/)
})

run('WorkbenchCalculationFlowPanel 输入带按第一跳目标分组，而不是按语义分类切成纵向列', () => {
  assert.match(source, /firstHopTargetId/)
  assert.match(source, /firstHopTargetTitle/)
  assert.match(source, /cleanZoneHalfWidth/)
  assert.match(source, /maxIslandRows:\s*2/)
  assert.match(source, /islandTargetRowWidth:\s*compact \? 360 : 420/)
  assert.match(source, /rowWidthBalanceTolerance:\s*132/)
  assert.match(source, /islandGap:\s*compact \? 72 : 88/)
  assert.match(source, /islandColumnGap:\s*compact \? 156 : 176/)
  assert.match(source, /cleanZoneHalfWidth:\s*compact \? 72 : 84/)
  assert.match(source, /const key = `lane:\$\{node\.lane\}`/)
  assert.doesNotMatch(source, /const key = `\$\{node\.semanticRole \|\| 'base'\}:\$\{node\.lane\}`/)
})

run('WorkbenchCalculationFlowPanel 所有节点卡片统一放大标题和值字体', () => {
  assert.match(source, /\.flow-node__title\s*\{[\s\S]*font-size:\s*24px;/)
  assert.match(source, /\.flow-node__value\s*\{[\s\S]*font-size:\s*22px;/)
  assert.match(source, /\.flow-node__title\s*\{[\s\S]*line-height:\s*1\.3;/)
  assert.match(source, /\.flow-node__value\s*\{[\s\S]*line-height:\s*1\.2;/)
})

run('WorkbenchCalculationFlowPanel 轻加强选中节点和上下游反应层级', () => {
  assert.match(source, /\.workbench-flow__connector\.is-active\s*\{[\s\S]*stroke-width:\s*4\.2;/)
  assert.match(source, /\.workbench-flow__connector\.is-active\s*\{[\s\S]*opacity:\s*1;/)
  assert.match(source, /\.flow-node\.is-selected\s*\{[\s\S]*scale\(1\.035\)/)
  assert.match(source, /\.flow-node\.is-selected\s*\{[\s\S]*0 0 0 6px rgba\(255, 255, 255, 0\.82\)/)
  assert.match(source, /\.flow-node\.is-related\s*\{[\s\S]*translateY\(-1px\) scale\(1\.01\)/)
  assert.match(source, /\.flow-node\.is-related\s*\{[\s\S]*0 18px 38px rgba\(37, 55, 76, 0\.2\)/)
})
