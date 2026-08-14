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

run('NewDesignWorkbench 左侧使用输入参数树与选型参数树双区结构', () => {
  const source = read('./NewDesignWorkbench.vue')

  assert.match(source, /<strong>输入参数树<\/strong>/)
  assert.match(source, /<strong>选型参数树<\/strong>/)
  assert.match(source, /当前型号尚未完成选型，暂无选型参数/)
  assert.doesNotMatch(source, /leftPanelTab/)
  assert.doesNotMatch(source, /已选型设备/)
})

run('NewDesignWorkbench 主工作区切为计算工作台、计算流程图、设备模型预览三种模式', () => {
  const source = read('./NewDesignWorkbench.vue')

  assert.match(source, /<el-radio-button value="list"[^>]*>计算工作台<\/el-radio-button>/)
  assert.match(source, /<el-radio-button value="flow"[^>]*>计算流程图<\/el-radio-button>/)
  assert.match(source, /<el-radio-button value="model"[^>]*>设备模型预览<\/el-radio-button>/)
  assert.match(source, /v-else-if="workspaceMode === 'model'"/)
  assert.doesNotMatch(source, /class="panel-card model-preview-card"/)
})

run('NewDesignWorkbench 顶部状态卡改为输出在上参考在下，右栏只保留设计说明', () => {
  const source = read('./NewDesignWorkbench.vue')

  assert.match(source, /summary-card__actual/)
  assert.match(source, /summary-card__reference/)
  assert.doesNotMatch(source, /compare-item actual/)
  assert.doesNotMatch(source, /compare-item theory/)
  assert.doesNotMatch(source, /rightPanelTab/)
  assert.doesNotMatch(source, /关键指标校核/)
  assert.doesNotMatch(source, /参数影响入口/)
})

run('WorkbenchInputTable 支持自定义标题和空态文案，并接入树分组帮助器', () => {
  const source = read('../components/WorkbenchInputTable.vue')

  assert.match(source, /import \{ resolveWorkbenchTreeGroup \} from/)
  assert.match(source, /title:/)
  assert.match(source, /emptyDescription:/)
  assert.match(source, /allowAdd:/)
  assert.match(source, /props\.title \|\| '输入参数树'/)
})
