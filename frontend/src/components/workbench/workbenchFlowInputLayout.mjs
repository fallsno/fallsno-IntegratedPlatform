const ISLAND_PATTERN = [0, -1, 1, -2, 2, -3, 3]
const COMPACT_ISLAND_PATTERN = [1, -1, 2, -2, 3, -3, 4]
const ROLE_PRIORITY = {
  base: 0,
  reference: 1
}

function compareInputPriority(left = {}, right = {}) {
  const leftPriority = Number(Boolean(left.isShared || left.isPrimarySpine || (left.resultKeys || []).length > 1))
  const rightPriority = Number(Boolean(right.isShared || right.isPrimarySpine || (right.resultKeys || []).length > 1))
  if (leftPriority !== rightPriority) {
    return rightPriority - leftPriority
  }

  const leftRole = ROLE_PRIORITY[String(left.semanticRole || 'base')] ?? 9
  const rightRole = ROLE_PRIORITY[String(right.semanticRole || 'base')] ?? 9
  if (leftRole !== rightRole) {
    return leftRole - rightRole
  }

  return String(left.title || left.name || '').localeCompare(String(right.title || right.name || ''), 'zh-CN')
}

function resolveIslandKey(node = {}) {
  const firstHopTargetId = String(node.firstHopTargetId || '').trim()
  if (node.isShared || node.isPrimarySpine || (node.resultKeys || []).length > 1) {
    return `shared:${firstHopTargetId || 'main'}`
  }
  if (firstHopTargetId) {
    return `target:${firstHopTargetId}`
  }
  return `fallback:${String(node.title || node.name || '').trim()}`
}

function buildInputIslands(group = []) {
  const islandMap = new Map()

  group
    .slice()
    .sort(compareInputPriority)
    .forEach((node) => {
      const key = resolveIslandKey(node)
      const island = islandMap.get(key) || {
        key,
        nodes: [],
        isShared: key.startsWith('shared:'),
        firstHopTargetTitle: String(node.firstHopTargetTitle || '').trim()
      }
      island.nodes.push(node)
      islandMap.set(key, island)
    })

  return [...islandMap.values()].sort((left, right) => {
    if (left.isShared !== right.isShared) {
      return left.isShared ? -1 : 1
    }
    return String(left.firstHopTargetTitle || left.key).localeCompare(String(right.firstHopTargetTitle || right.key), 'zh-CN')
  })
}

function positionRow(rowNodes = [], laneCenterX = 0, y = 0, inputGap = 44) {
  const rowWidth = measureRowWidth(rowNodes, inputGap)
  let cursor = laneCenterX - rowWidth / 2
  rowNodes.forEach((node) => {
    node.x = cursor
    node.y = y
    cursor += node.width + inputGap
  })
}

function measureRowWidth(rowNodes = [], inputGap = 44) {
  return rowNodes.reduce((sum, node) => sum + node.width, 0) + Math.max(rowNodes.length - 1, 0) * inputGap
}

function splitBalancedRows(nodes = [], options = {}) {
  const {
    inputGap = 44,
    maxIslandRows = 2,
    islandTargetRowWidth = 420,
    rowWidthBalanceTolerance = 132
  } = options

  if (nodes.length <= 1 || maxIslandRows <= 1) {
    return [nodes.slice()]
  }

  const singleRowWidth = measureRowWidth(nodes, inputGap)
  if (singleRowWidth <= islandTargetRowWidth || nodes.length <= 2) {
    return [nodes.slice()]
  }

  let bestRows = [nodes.slice(0, Math.ceil(nodes.length / 2)), nodes.slice(Math.ceil(nodes.length / 2))]
  let bestScore = Number.POSITIVE_INFINITY

  for (let splitIndex = 1; splitIndex < nodes.length; splitIndex += 1) {
    const topRow = nodes.slice(0, splitIndex)
    const bottomRow = nodes.slice(splitIndex)
    if (!topRow.length || !bottomRow.length) {
      continue
    }

    const topWidth = measureRowWidth(topRow, inputGap)
    const bottomWidth = measureRowWidth(bottomRow, inputGap)
    const widthDelta = Math.abs(topWidth - bottomWidth)
    const widestRow = Math.max(topWidth, bottomWidth)
    const overflowPenalty = Math.max(0, widestRow - islandTargetRowWidth)
    const tolerancePenalty = Math.max(0, widthDelta - rowWidthBalanceTolerance)
    const score = overflowPenalty * 10 + tolerancePenalty * 5 + widthDelta

    if (score < bestScore) {
      bestScore = score
      bestRows = [topRow, bottomRow]
    }
  }

  return bestRows
}

function layoutInputIsland(island = {}, options = {}) {
  const {
    centerX = 0,
    baseTop = 0,
    inputGap = 44,
    inputRowGap = 122,
    maxIslandRows = 2,
    islandTargetRowWidth = 420,
    rowWidthBalanceTolerance = 132
  } = options

  let maxBottom = baseTop
  const rows = splitBalancedRows(island.nodes, {
    inputGap,
    maxIslandRows,
    islandTargetRowWidth,
    rowWidthBalanceTolerance
  })

  rows.forEach((rowNodes, rowIndex) => {
    const y = baseTop + rowIndex * inputRowGap
    positionRow(rowNodes, centerX, y, inputGap)
    rowNodes.forEach((node) => {
      maxBottom = Math.max(maxBottom, node.y + node.height)
    })
  })
  return maxBottom
}

export function layoutInputLaneGroup(group = [], options = {}) {
  const {
    laneCenterX = 0,
    baseTop = 0,
    inputGap = 44,
    inputRowGap = 122,
    islandGap = 88,
    islandColumnGap = 176,
    cleanZoneHalfWidth = 84,
    maxIslandRows = 2,
    islandTargetRowWidth = 420,
    rowWidthBalanceTolerance = 132
  } = options

  if (!group.length) {
    return baseTop
  }

  const islands = buildInputIslands(group)
  let maxBottom = baseTop
  let compactIndex = 0

  islands.forEach((island, index) => {
    const laneOffset = island.isShared
      ? 0
      : (COMPACT_ISLAND_PATTERN[compactIndex] ?? (compactIndex + 1))
    const protectedDistance = cleanZoneHalfWidth + islandGap
    let islandCenterX = laneCenterX + laneOffset * islandColumnGap

    if (!island.isShared && Math.abs(islandCenterX - laneCenterX) < protectedDistance) {
      islandCenterX = laneCenterX + (laneOffset < 0 ? -protectedDistance : protectedDistance)
    }

    maxBottom = Math.max(maxBottom, layoutInputIsland(island, {
      centerX: islandCenterX,
      baseTop: baseTop,
      inputGap,
      inputRowGap,
      maxIslandRows,
      islandTargetRowWidth,
      rowWidthBalanceTolerance
    }))

    if (!island.isShared) {
      compactIndex += 1
    }
  })

  return maxBottom
}
