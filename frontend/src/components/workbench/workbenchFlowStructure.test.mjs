import assert from 'node:assert/strict'

import {
  buildFocusStructureState,
  buildStructureFlowModel,
  buildVisibleStructureEdges,
  buildVisibleStructureNodeIds
} from './workbenchFlowStructure.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

const createModel = () =>
  buildStructureFlowModel({
    nodes: [
      { id: 'input:滚筒重量', nodeType: 'input', layer: 'input', title: '滚筒重量', defaultVisible: true, resultKeys: ['formula:功率', 'formula:备用结果'], isShared: true },
      { id: 'input:摩擦系数', nodeType: 'input', layer: 'input', title: '摩擦系数', defaultVisible: true, resultKeys: ['formula:功率'], branchOwner: 'formula:功率' },
      { id: 'formula:总重', nodeType: 'formula', layer: 'calculation', title: '总重', defaultVisible: true, resultKeys: ['formula:功率', 'formula:备用结果'], isShared: true, isPrimarySpine: true },
      { id: 'formula:托轮摩擦力矩', nodeType: 'formula', layer: 'calculation', title: '托轮摩擦力矩', defaultVisible: true, resultKeys: ['formula:功率'], branchOwner: 'formula:功率', isPrimarySpine: true },
      { id: 'formula:功率', nodeType: 'formula', layer: 'output', title: '功率', defaultVisible: true, resultKeys: ['formula:功率'], isPrimaryResult: true },
      { id: 'formula:备用结果', nodeType: 'formula', layer: 'output', title: '备用结果', defaultVisible: true, resultKeys: ['formula:备用结果'] }
    ],
    edges: [
      { source: 'input:滚筒重量', target: 'formula:总重' },
      { source: 'input:摩擦系数', target: 'formula:托轮摩擦力矩' },
      { source: 'formula:总重', target: 'formula:托轮摩擦力矩' },
      { source: 'formula:托轮摩擦力矩', target: 'formula:功率' },
      { source: 'formula:总重', target: 'formula:备用结果' }
    ]
  })

run('默认态保留主干上下文而不是选中前裁成局部切片', () => {
  const model = createModel()
  const visibleNodeIds = buildVisibleStructureNodeIds(model)

  assert.equal(visibleNodeIds.has('formula:功率'), true)
  assert.equal(visibleNodeIds.has('formula:备用结果'), true)
  assert.equal(visibleNodeIds.has('formula:总重'), true)
  assert.equal(buildVisibleStructureEdges(model).some((edge) => edge.target === 'formula:功率'), true)
})

run('未选中节点时保持全图默认可读', () => {
  const model = createModel()
  const focus = buildFocusStructureState(model, '')

  assert.equal(focus.nodeStates.get('formula:总重'), 'default')
  assert.equal(focus.nodeStates.get('formula:功率'), 'default')
  assert.equal(focus.nodeStates.get('formula:备用结果'), 'default')
  assert.equal(focus.edgeStates.get('formula:总重->formula:备用结果'), 'default')
})

run('选中态只高亮当前计算链路的直接承接关系', () => {
  const model = createModel()
  const focus = buildFocusStructureState(model, 'formula:备用结果')

  assert.equal(focus.nodeStates.get('formula:备用结果'), 'selected')
  assert.equal(focus.nodeStates.get('formula:总重'), 'related')
  assert.equal(focus.nodeStates.get('formula:托轮摩擦力矩'), 'default')
  assert.equal(focus.edgeStates.get('formula:总重->formula:备用结果'), 'related')
  assert.equal(focus.edgeStates.get('formula:托轮摩擦力矩->formula:功率'), 'default')
})

run('选中态对非相关节点保留默认可读而不是 muted', () => {
  const model = createModel()
  const focus = buildFocusStructureState(model, 'formula:备用结果')

  assert.equal(focus.nodeStates.get('formula:托轮摩擦力矩'), 'default')
  assert.equal(focus.nodeStates.get('input:摩擦系数'), 'default')
  assert.equal(focus.edgeStates.get('formula:托轮摩擦力矩->formula:功率'), 'default')
})
