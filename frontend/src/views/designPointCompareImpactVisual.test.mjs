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

run('DesignPointCompare 影响分析页签使用结果多选和三图布局', () => {
  const source = read('./DesignPointCompare.vue')
  assert.match(source, /v-model="selectedImpactResults"/)
  assert.match(source, /ref="impactTrendChartRef"/)
  assert.match(source, /ref="impactSensitivityChartRef"/)
  assert.match(source, /ref="impactRangeChartRef"/)
  assert.match(source, /impact-summary-tile/)
})

run('DesignPointCompare 移除旧的大摘要卡布局', () => {
  const source = read('./DesignPointCompare.vue')
  assert.doesNotMatch(source, /class="result-summary"/)
  assert.doesNotMatch(source, /class="summary-card"/)
  assert.doesNotMatch(source, /summary-content/)
})

run('DesignPointCompare 影响分析页签包含趋势分析和状态查看双模式', () => {
  const source = read('./DesignPointCompare.vue')
  assert.match(source, /impactViewMode/)
  assert.match(source, /label:\s*'趋势分析'/)
  assert.match(source, /label:\s*'状态查看'/)
})

run('DesignPointCompare 状态查看包含筛选类型和自动切图容器', () => {
  const source = read('./DesignPointCompare.vue')
  assert.match(source, /v-model="impactStateFilterType"/)
  assert.match(source, /impactStateChartMode/)
  assert.match(source, /ref="impactStatePrimaryChartRef"/)
  assert.match(source, /impact-state-summary-grid/)
  assert.match(source, /impact-state-table/)
})

run('DesignPointCompare 状态查看包含最近命中提示和空态文案', () => {
  const source = read('./DesignPointCompare.vue')
  assert.match(source, /impactStateMatchedSample/)
  assert.match(source, /实际命中/)
  assert.match(source, /当前筛选没有命中任何状态，请调整筛选条件/)
})
