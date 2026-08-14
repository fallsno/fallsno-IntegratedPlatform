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

run('ParameterLookupCurvePanel 在跳转进入后仍会监听容器尺寸变化', () => {
  const source = read('../components/ParameterLookupCurvePanel.vue')
  assert.match(source, /ResizeObserver/)
})

run('ParameterCenter 移除顶部参数中心说明区', () => {
  const source = read('./ParameterCenter.vue')
  assert.doesNotMatch(source, /主视图直接维护“参数名 \+ 各型号值”的参数矩阵/)
  assert.doesNotMatch(source, /page-actions/)
})

run('ParameterCenter 将基础参数操作放回基础参数页内部', () => {
  const source = read('./ParameterCenter.vue')
  assert.match(source, /matrix-toolbar__actions/)
  assert.match(source, /新增参数/)
  assert.match(source, /新增型号/)
  assert.match(source, /批量导入/)
  assert.match(source, /保存矩阵/)
})
