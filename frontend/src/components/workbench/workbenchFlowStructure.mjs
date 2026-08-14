const INPUT_NODE_TYPES = new Set(['input', 'parameter'])
const GROUP_NODE_TYPE_PRIORITY = new Map([
  ['step', 0],
  ['calculation', 1],
  ['result_anchor', 2],
  ['rule', 3]
])
const TRAVERSAL_NODE_TYPE_PRIORITY = new Map([
  ['step', 0],
  ['calculation', 1],
  ['result_anchor', 2],
  ['input', 3],
  ['parameter', 3],
  ['rule', 4],
  ['output', 5]
])
const BAND_ORDER = new Map([
  ['input', 0],
  ['calculation', 1],
  ['output', 2]
])

function compareNodeOrder(left = {}, right = {}) {
  const leftOrder = Number(left.sortOrder ?? left.order ?? left.groupOrder ?? 0)
  const rightOrder = Number(right.sortOrder ?? right.order ?? right.groupOrder ?? 0)
  if (leftOrder !== rightOrder) {
    return leftOrder - rightOrder
  }
  const leftPriority = GROUP_NODE_TYPE_PRIORITY.get(String(left.nodeType || '')) ?? 99
  const rightPriority = GROUP_NODE_TYPE_PRIORITY.get(String(right.nodeType || '')) ?? 99
  if (leftPriority !== rightPriority) {
    return leftPriority - rightPriority
  }
  return String(left.id || '').localeCompare(String(right.id || ''), 'zh-CN')
}

function compareTraversalNodeOrder(left = {}, right = {}) {
  const leftPriority = TRAVERSAL_NODE_TYPE_PRIORITY.get(String(left.nodeType || '')) ?? 99
  const rightPriority = TRAVERSAL_NODE_TYPE_PRIORITY.get(String(right.nodeType || '')) ?? 99
  if (leftPriority !== rightPriority) {
    return leftPriority - rightPriority
  }
  const leftLayerPriority = left.layer === 'calculation' ? 0 : left.layer === 'input' ? 1 : 2
  const rightLayerPriority = right.layer === 'calculation' ? 0 : right.layer === 'input' ? 1 : 2
  if (leftLayerPriority !== rightLayerPriority) {
    return leftLayerPriority - rightLayerPriority
  }
  return String(left.id || '').localeCompare(String(right.id || ''), 'zh-CN')
}

function compareBandOrder(left = '', right = '') {
  return (BAND_ORDER.get(String(left || '')) ?? 99) - (BAND_ORDER.get(String(right || '')) ?? 99)
}

function resolveGroupKey(node = {}) {
  if (node.group || node.module || node.step) {
    return String(node.group || node.module || node.step)
  }
  if (node.stepCode) {
    return `step:${node.stepCode}`
  }
  if (node.sceneName) {
    return `scene:${node.sceneName}`
  }
  return ''
}

function resolveGroupTitle(node = {}, fallbackIndex = 0) {
  return String(node.groupTitle || node.sceneName || node.title || `计算分组 ${fallbackIndex + 1}`)
}

function buildNodeDegrees(nodes = [], edges = []) {
  const inDegree = new Map()
  const outDegree = new Map()

  nodes.forEach((node) => {
    inDegree.set(node.id, 0)
    outDegree.set(node.id, 0)
  })

  edges.forEach((edge) => {
    if (outDegree.has(edge.source)) {
      outDegree.set(edge.source, outDegree.get(edge.source) + 1)
    }
    if (inDegree.has(edge.target)) {
      inDegree.set(edge.target, inDegree.get(edge.target) + 1)
    }
  })

  return { inDegree, outDegree }
}

export function buildStructureFlowModel(graph = {}) {
  const rawNodes = Array.isArray(graph?.nodes) ? graph.nodes : []
  const rawEdges = Array.isArray(graph?.edges) ? graph.edges : []
  const { outDegree } = buildNodeDegrees(rawNodes, rawEdges)

  const nodes = rawNodes.map((node) => {
    const nodeType = String(node.nodeType || '')
    const isInput = INPUT_NODE_TYPES.has(nodeType)
    const inferredLayer = isInput ? 'input' : (outDegree.get(node.id) || 0) === 0 ? 'output' : 'calculation'
    const layer = String(node.layer || inferredLayer)
    return {
      ...node,
      nodeType,
      semanticRole: String(node.semanticRole || ''),
      layer,
      defaultVisible: node.defaultVisible !== false,
      isMainline: node.isMainline !== false,
      hasExplicitVisibility:
        Object.prototype.hasOwnProperty.call(node, 'defaultVisible') ||
        Object.prototype.hasOwnProperty.call(node, 'isMainline'),
      groupKey: layer === 'calculation' ? resolveGroupKey(node) : '',
      groupTitle: layer === 'calculation' ? resolveGroupTitle(node) : '',
      order: Number(node.sortOrder ?? node.order ?? 0),
      depth: node.depth ?? 0,
      resultKeys: node.resultKeys ?? [],
      isPrimarySpine: node.isPrimarySpine ?? false,
      isShared: node.isShared ?? false,
      isPrimaryResult: node.isPrimaryResult ?? false,
      branchOwner: node.branchOwner ?? ''
    }
  })

  const nodeMap = new Map(nodes.map((node) => [node.id, node]))
  const upstreamMap = new Map(nodes.map((node) => [node.id, []]))
  const downstreamMap = new Map(nodes.map((node) => [node.id, []]))

  const edges = rawEdges
    .filter((edge) => nodeMap.has(edge.source) && nodeMap.has(edge.target))
    .map((edge, index) => {
      upstreamMap.get(edge.target).push(edge.source)
      downstreamMap.get(edge.source).push(edge.target)
      return {
        ...edge,
        id: String(edge.id || `${edge.source}-${edge.target}-${index}`),
        sourceLayer: nodeMap.get(edge.source).layer,
        targetLayer: nodeMap.get(edge.target).layer
      }
    })

  const groupedMap = new Map()
  let fallbackIndex = 0

  nodes
    .filter((node) => node.layer === 'calculation')
    .sort(compareNodeOrder)
    .forEach((node) => {
      let groupKey = node.groupKey
      if (!groupKey) {
        groupKey = `fallback:${fallbackIndex}`
        fallbackIndex += 1
      }

      if (!groupedMap.has(groupKey)) {
        groupedMap.set(groupKey, {
          key: groupKey,
          title: node.groupTitle || resolveGroupTitle(node, groupedMap.size),
          order: Number(node.order || groupedMap.size),
          nodes: []
        })
      }

      groupedMap.get(groupKey).nodes.push(node)
    })

  const calculationGroups = [...groupedMap.values()]
    .sort((left, right) => Number(left.order || 0) - Number(right.order || 0))
    .map((group) => ({
      ...group,
      summary: group.nodes
        .map((node) => String(node.summary || node.title || node.name || ''))
        .filter(Boolean)
        .slice(0, 2)
        .join(' / ')
    }))

  const bandOrder = [...new Set(nodes.map((node) => node.visualBand || node.layer || 'unknown'))]
    .sort(compareBandOrder)

  return {
    nodes,
    edges,
    nodeMap,
    upstreamMap,
    downstreamMap,
    calculationGroups,
    bandOrder
  }
}

export function buildVisibleStructureNodeIds(model = {}) {
  const visibleNodes = (model?.nodes || []).filter((node) => node.defaultVisible !== false)
  if (visibleNodes.length > 0) {
    return new Set(visibleNodes.map((node) => node.id))
  }

  return new Set((model?.nodes || []).map((node) => node.id))
}

export function buildSelectedLineageNodeIds(model = {}, selectedNodeId = '') {
  if (!selectedNodeId || !model?.nodeMap?.has(selectedNodeId)) {
    return new Set()
  }

  const lineageNodeIds = new Set([selectedNodeId])

  const visitDirectional = (startId, resolver) => {
    const stack = [startId]
    const visited = new Set([startId])

    while (stack.length) {
      const currentId = stack.pop()
      const relatedIds = [...(resolver(currentId) || [])]
        .sort((leftId, rightId) =>
          compareTraversalNodeOrder(model.nodeMap.get(leftId), model.nodeMap.get(rightId))
        )

      relatedIds.forEach((relatedId) => {
        if (!visited.has(relatedId)) {
          visited.add(relatedId)
          lineageNodeIds.add(relatedId)
          stack.push(relatedId)
        }
      })
    }
  }

  visitDirectional(selectedNodeId, (nodeId) => model.upstreamMap.get(nodeId))
  visitDirectional(selectedNodeId, (nodeId) => model.downstreamMap.get(nodeId))

  return lineageNodeIds
}



export function buildFocusStructureState(model = {}, selectedNodeId = '') {
  const nodeStates = new Map()
  const edgeStates = new Map()
  const selectedNode = model?.nodeMap?.get(selectedNodeId)
  const relatedNodeIds = new Set(selectedNodeId ? [selectedNodeId] : [])
  const relatedEdgeIds = new Set()

  for (const node of model?.nodes || []) {
    nodeStates.set(node.id, 'default')
  }
  for (const edge of model?.edges || []) {
    edgeStates.set(`${edge.source}->${edge.target}`, 'default')
  }

  if (!selectedNode) {
    return { nodeStates, edgeStates, relatedNodeIds, relatedEdgeIds }
  }

  const visitedUpstream = new Set()
  function visitUpstream(nodeId) {
    if (visitedUpstream.has(nodeId)) return
    visitedUpstream.add(nodeId)
    const node = model?.nodeMap?.get(nodeId)
    if (!node) return
    relatedNodeIds.add(nodeId)
    const upstream = model?.upstreamMap?.get(nodeId) || []
    upstream.forEach((depId) => {
      relatedNodeIds.add(depId)
      relatedEdgeIds.add(`${depId}->${nodeId}`)
      visitUpstream(depId)
    })
  }

  const visitedDownstream = new Set()
  function visitDownstream(nodeId) {
    if (visitedDownstream.has(nodeId)) return
    visitedDownstream.add(nodeId)
    relatedNodeIds.add(nodeId)
    const downstream = model?.downstreamMap?.get(nodeId) || []
    downstream.forEach((childId) => {
      relatedNodeIds.add(childId)
      relatedEdgeIds.add(`${nodeId}->${childId}`)
      visitDownstream(childId)
    })
  }

  visitUpstream(selectedNodeId)
  visitDownstream(selectedNodeId)

  for (const node of model?.nodes || []) {
    nodeStates.set(
      node.id,
      node.id === selectedNodeId ? 'selected' : relatedNodeIds.has(node.id) ? 'related' : 'default'
    )
  }

  for (const edge of model?.edges || []) {
    const edgeKey = `${edge.source}->${edge.target}`
    const isRelatedEdge = relatedEdgeIds.has(edgeKey)
    edgeStates.set(edgeKey, isRelatedEdge ? 'related' : 'default')
  }

  return { nodeStates, edgeStates, relatedNodeIds, relatedEdgeIds }
}

export function buildVisibleStructureEdges(model = {}) {
  const visibleNodeIds = buildVisibleStructureNodeIds(model)

  return (model.edges || []).filter((edge) => {
    return visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
  })
}
