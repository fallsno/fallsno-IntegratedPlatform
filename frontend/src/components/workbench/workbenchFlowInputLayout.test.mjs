import assert from 'node:assert/strict'

import { layoutInputLaneGroup } from './workbenchFlowInputLayout.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

function createNode(overrides = {}) {
  return {
    id: '',
    width: 152,
    height: 78,
    x: 0,
    y: 0,
    isShared: false,
    isPrimarySpine: false,
    resultKeys: [],
    semanticRole: 'base',
    firstHopTargetId: '',
    firstHopTargetTitle: '',
    title: '',
    name: '',
    ...overrides
  }
}

function getCenter(node) {
  return node.x + node.width / 2
}

function getRowWidth(nodes) {
  if (!nodes.length) {
    return 0
  }
  const left = Math.min(...nodes.map((node) => node.x))
  const right = Math.max(...nodes.map((node) => node.x + node.width))
  return right - left
}

run('同一第一跳的输入在同一输入岛内横向优先展开', () => {
  const materialWeight = createNode({
    id: 'input:筒内料重',
    title: '筒内料重',
    firstHopTargetId: 'formula:总重换算值',
    firstHopTargetTitle: '总重换算值'
  })
  const drumWeight = createNode({
    id: 'input:滚筒重量',
    title: '筒体重量',
    firstHopTargetId: 'formula:总重换算值',
    firstHopTargetTitle: '总重换算值'
  })

  layoutInputLaneGroup([materialWeight, drumWeight], {
    laneCenterX: 820,
    baseTop: 112,
    inputGap: 44,
    inputRowGap: 122,
    islandGap: 104,
    islandColumnGap: 220,
    cleanZoneHalfWidth: 96
  })

  assert.equal(materialWeight.y, 112)
  assert.equal(drumWeight.y, 112)
  assert.ok(Math.abs((materialWeight.x + materialWeight.width / 2) - (drumWeight.x + drumWeight.width / 2)) >= 160)
})

run('不同第一跳的输入拆成不同输入岛，并避开主干入口清洁区', () => {
  const branchA = createNode({
    id: 'input:摩擦系数',
    title: '摩擦系数',
    firstHopTargetId: 'formula:托轮摩擦力矩',
    firstHopTargetTitle: '托轮摩擦力矩'
  })
  const branchB = createNode({
    id: 'input:胶带速度',
    title: '胶带速度',
    firstHopTargetId: 'formula:圆周力',
    firstHopTargetTitle: '圆周力'
  })

  layoutInputLaneGroup([branchA, branchB], {
    laneCenterX: 820,
    baseTop: 112,
    inputGap: 44,
    inputRowGap: 122,
    islandGap: 104,
    islandColumnGap: 220,
    cleanZoneHalfWidth: 96
  })

  const centerA = branchA.x + branchA.width / 2
  const centerB = branchB.x + branchB.width / 2
  assert.ok(centerA < 724 || centerA > 916)
  assert.ok(centerB < 724 || centerB > 916)
  assert.ok(Math.abs(centerA - centerB) >= 180)
})

run('共享输入优先靠近共享入口，普通输入按去向分散', () => {
  const sharedInput = createNode({
    id: 'input:滚筒重量',
    title: '筒体重量',
    isShared: true,
    resultKeys: ['formula:功率', 'formula:备用结果'],
    firstHopTargetId: 'formula:总重换算值',
    firstHopTargetTitle: '总重换算值'
  })
  const branchInput = createNode({
    id: 'input:摩擦系数',
    title: '摩擦系数',
    firstHopTargetId: 'formula:托轮摩擦力矩',
    firstHopTargetTitle: '托轮摩擦力矩'
  })

  const bottom = layoutInputLaneGroup([sharedInput, branchInput], {
    laneCenterX: 820,
    baseTop: 112,
    inputGap: 44,
    inputRowGap: 122,
    islandGap: 104,
    islandColumnGap: 220,
    cleanZoneHalfWidth: 96
  })

  const sharedCenter = sharedInput.x + sharedInput.width / 2
  const branchCenter = branchInput.x + branchInput.width / 2
  assert.ok(Math.abs(sharedCenter - 820) <= 52)
  assert.ok(Math.abs(branchCenter - 820) >= 140)
  assert.ok(bottom >= Math.max(sharedInput.y + sharedInput.height, branchInput.y + branchInput.height))
})

run('输入岛在收横向后仍避开主干入口且整体跨度明显小于旧版', () => {
  const branchA = createNode({
    id: 'input:摩擦系数',
    title: '摩擦系数',
    firstHopTargetId: 'formula:托轮摩擦力矩',
    firstHopTargetTitle: '托轮摩擦力矩'
  })
  const branchB = createNode({
    id: 'input:胶带速度',
    title: '胶带速度',
    firstHopTargetId: 'formula:圆周力',
    firstHopTargetTitle: '圆周力'
  })
  const branchC = createNode({
    id: 'input:倾角',
    title: '倾角',
    firstHopTargetId: 'formula:附加功率',
    firstHopTargetTitle: '附加功率'
  })

  layoutInputLaneGroup([branchA, branchB, branchC], {
    laneCenterX: 820,
    baseTop: 112,
    inputGap: 44,
    inputRowGap: 122,
    islandGap: 88,
    islandColumnGap: 176,
    cleanZoneHalfWidth: 84,
    maxIslandRows: 2,
    islandTargetRowWidth: 420,
    rowWidthBalanceTolerance: 132
  })

  const centers = [branchA, branchB, branchC].map(getCenter).sort((left, right) => left - right)
  assert.ok(centers[0] < 736 || centers[0] > 904)
  assert.ok(centers[1] < 736 || centers[1] > 904)
  assert.ok(centers[2] < 736 || centers[2] > 904)
  assert.ok(centers[1] - centers[0] >= 160)
  assert.ok(centers[2] - centers[1] >= 160)
  assert.ok(centers[2] - centers[0] <= 560)
})

run('同一输入岛需要拆层时最多两层且两层宽度尽量齐平', () => {
  const nodes = [
    createNode({
      id: 'input:筒内料重',
      title: '筒内料重',
      firstHopTargetId: 'formula:总重换算值',
      firstHopTargetTitle: '总重换算值'
    }),
    createNode({
      id: 'input:滚筒重量',
      title: '筒体重量',
      firstHopTargetId: 'formula:总重换算值',
      firstHopTargetTitle: '总重换算值'
    }),
    createNode({
      id: 'input:物料速度',
      title: '物料速度',
      firstHopTargetId: 'formula:总重换算值',
      firstHopTargetTitle: '总重换算值'
    }),
    createNode({
      id: 'input:倾角',
      title: '倾角',
      firstHopTargetId: 'formula:总重换算值',
      firstHopTargetTitle: '总重换算值'
    })
  ]

  layoutInputLaneGroup(nodes, {
    laneCenterX: 820,
    baseTop: 112,
    inputGap: 44,
    inputRowGap: 122,
    islandGap: 88,
    islandColumnGap: 176,
    cleanZoneHalfWidth: 84,
    maxIslandRows: 2,
    islandTargetRowWidth: 420,
    rowWidthBalanceTolerance: 132
  })

  const rowMap = new Map()
  nodes.forEach((node) => {
    const row = rowMap.get(node.y) || []
    row.push(node)
    rowMap.set(node.y, row)
  })

  const rows = [...rowMap.values()].sort((left, right) => left[0].y - right[0].y)
  assert.equal(rows.length, 2)
  assert.equal(rows[0].length, 2)
  assert.equal(rows[1].length, 2)
  assert.ok(Math.abs(getRowWidth(rows[0]) - getRowWidth(rows[1])) <= 132)
})

run('共享输入岛也遵守紧凑约束，不因共享角色横向膨胀', () => {
  const sharedNodes = [
    createNode({
      id: 'input:滚筒重量',
      title: '筒体重量',
      isShared: true,
      resultKeys: ['formula:功率', 'formula:备用结果'],
      firstHopTargetId: 'formula:总重换算值',
      firstHopTargetTitle: '总重换算值'
    }),
    createNode({
      id: 'input:筒内料重',
      title: '筒内料重',
      isShared: true,
      resultKeys: ['formula:功率', 'formula:备用结果'],
      firstHopTargetId: 'formula:总重换算值',
      firstHopTargetTitle: '总重换算值'
    }),
    createNode({
      id: 'input:倾角',
      title: '倾角',
      isShared: true,
      resultKeys: ['formula:功率', 'formula:备用结果'],
      firstHopTargetId: 'formula:总重换算值',
      firstHopTargetTitle: '总重换算值'
    }),
    createNode({
      id: 'input:填充率',
      title: '填充率',
      isShared: true,
      resultKeys: ['formula:功率', 'formula:备用结果'],
      firstHopTargetId: 'formula:总重换算值',
      firstHopTargetTitle: '总重换算值'
    })
  ]

  layoutInputLaneGroup(sharedNodes, {
    laneCenterX: 820,
    baseTop: 112,
    inputGap: 44,
    inputRowGap: 122,
    islandGap: 88,
    islandColumnGap: 176,
    cleanZoneHalfWidth: 84,
    maxIslandRows: 2,
    islandTargetRowWidth: 420,
    rowWidthBalanceTolerance: 132
  })

  const rowCount = new Set(sharedNodes.map((node) => node.y)).size
  const maxCenterOffset = Math.max(...sharedNodes.map((node) => Math.abs(getCenter(node) - 820)))
  assert.ok(rowCount <= 2)
  assert.ok(maxCenterOffset <= 220)
})
