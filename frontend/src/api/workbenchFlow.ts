/**
 * 工作台设计推理图生成助手
 * 基于新的类型定义生成可解释的设计推理图
 */

import type {
  WorkbenchFlowGraph,
  StepNode,
  ResultAnchorNode,
  ParameterNode,
  RuleNode,
  OutputNode,
  Edge,
  WorkbenchNodeType,
  ParameterRole,
  RuleType,
  NodeStatus,
  FlowGenerationOptions,
  NodeFilter,
  ColorSemantics,
  DEFAULT_COLOR_SEMANTICS
} from '../types/workbench-flow'

// ==================== 工具函数 ====================

/**
 * 生成节点唯一ID
 */
function generateNodeId(type: WorkbenchNodeType, name: string, suffix?: string): string {
  const normalizedType = String(type).toLowerCase().replace(/_/g, '-')
  const normalizedName = String(name).toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
  const id = `${normalizedType}-${normalizedName}`
  return suffix ? `${id}-${suffix}` : id
}

/**
 * 生成边唯一ID
 */
function generateEdgeId(sourceId: string, targetId: string): string {
  return `edge-${sourceId}-${targetId}`
}

/**
 * 获取节点颜色
 */
function getNodeColor(
  nodeType: WorkbenchNodeType,
  role?: ParameterRole,
  ruleType?: RuleType,
  status?: NodeStatus,
  colorSemantics: ColorSemantics = DEFAULT_COLOR_SEMANTICS
): string {
  // 优先使用状态颜色
  if (status && colorSemantics.nodeStatusColors[status]) {
    return colorSemantics.nodeStatusColors[status]
  }

  // 参数节点使用角色颜色
  if (nodeType === WorkbenchNodeType.PARAMETER && role && colorSemantics.parameterRoleColors[role]) {
    return colorSemantics.parameterRoleColors[role]
  }

  // 规则节点使用规则类型颜色
  if (nodeType === WorkbenchNodeType.RULE && ruleType && colorSemantics.ruleTypeColors[ruleType]) {
    return colorSemantics.ruleTypeColors[ruleType]
  }

  // 默认使用节点类型颜色
  return colorSemantics.nodeTypeColors[nodeType] || '#95A5A6'
}

/**
 * 计算节点位置
 */
function calculateNodePositions(
  stepCount: number,
  stepIndex: number,
  options: FlowGenerationOptions
): { x: number; y: number } {
  const baseX = 200
  const baseY = 150
  const stepSpacing = 300
  const parameterOffset = 100

  // 主链节点位置
  const x = baseX + stepIndex * stepSpacing
  const y = baseY

  return { x, y }
}

// ==================== 节点构建函数 ====================

/**
 * 构建主步骤节点
 */
function buildStepNode(
  stepNumber: number,
  stepName: string,
  purpose: string,
  options: FlowGenerationOptions
): StepNode {
  const id = generateNodeId(WorkbenchNodeType.STEP, stepName, String(stepNumber))
  const position = calculateNodePositions(stepNumber, stepNumber - 1, options)

  return {
    id,
    type: WorkbenchNodeType.STEP,
    label: `${stepNumber}. ${stepName}`,
    stepNumber,
    purpose,
    resultAnchorIds: [],
    parameterIds: [],
    ruleIds: [],
    expanded: options.showDetailedParameters,
    position,
    style: {
      color: getNodeColor(WorkbenchNodeType.STEP),
      borderColor: '#4A90E2',
      borderWidth: 2,
      size: 80
    }
  }
}

/**
 * 构建结果锚点节点
 */
function buildResultAnchorNode(
  stepId: string,
  resultName: string,
  value?: number | string,
  unit?: string,
  formula?: string
): ResultAnchorNode {
  const id = generateNodeId(WorkbenchNodeType.RESULT_ANCHOR, resultName)

  return {
    id,
    type: WorkbenchNodeType.RESULT_ANCHOR,
    label: resultName,
    stepId,
    value,
    unit,
    formula,
    downstreamStepIds: [],
    relatedParameterIds: [],
    relatedRuleIds: [],
    style: {
      color: getNodeColor(WorkbenchNodeType.RESULT_ANCHOR),
      borderColor: '#FF6B6B',
      borderWidth: 3,
      size: 70
    }
  }
}

/**
 * 构建参数节点
 */
function buildParameterNode(
  parameterName: string,
  role: ParameterRole,
  value?: number | string,
  unit?: string,
  source?: string,
  stepId?: string,
  resultAnchorId?: string,
  isCore: boolean = false
): ParameterNode {
  const id = generateNodeId(WorkbenchNodeType.PARAMETER, parameterName)

  return {
    id,
    type: WorkbenchNodeType.PARAMETER,
    label: parameterName,
    role,
    value,
    unit,
    source,
    stepId,
    resultAnchorId,
    isCore,
    style: {
      color: getNodeColor(WorkbenchNodeType.PARAMETER, role),
      borderColor: isCore ? '#E74C3C' : '#BDC3C7',
      borderWidth: isCore ? 2 : 1,
      size: isCore ? 60 : 50
    }
  }
}

/**
 * 构建规则节点
 */
function buildRuleNode(
  ruleName: string,
  ruleType: RuleType,
  expression: string,
  ruleDescription: string,
  relatedParameterIds: string[] = [],
  relatedResultAnchorId?: string,
  priority: number = 5
): RuleNode {
  const id = generateNodeId(WorkbenchNodeType.RULE, ruleName)

  return {
    id,
    type: WorkbenchNodeType.RULE,
    label: ruleName,
    ruleType,
    expression,
    ruleDescription,
    relatedParameterIds,
    relatedResultAnchorId,
    priority,
    style: {
      color: getNodeColor(WorkbenchNodeType.RULE, undefined, ruleType),
      borderColor: '#FF9F43',
      borderWidth: 2,
      size: 60
    }
  }
}

/**
 * 构建输出节点
 */
function buildOutputNode(
  outputName: string,
  value: number | string,
  description: string,
  resultAnchorId: string,
  allChecksPassed: boolean = true,
  failedRuleIds: string[] = []
): OutputNode {
  const id = generateNodeId(WorkbenchNodeType.OUTPUT, outputName)
  const status = allChecksPassed ? NodeStatus.SUCCESS : NodeStatus.ERROR

  return {
    id,
    type: WorkbenchNodeType.OUTPUT,
    label: outputName,
    value,
    description,
    resultAnchorId,
    allChecksPassed,
    failedRuleIds,
    status,
    style: {
      color: getNodeColor(WorkbenchNodeType.OUTPUT, undefined, undefined, status),
      borderColor: '#9B59B6',
      borderWidth: 3,
      size: 80
    }
  }
}

// ==================== 图生成函数 ====================

/**
 * 从设计数据生成设计推理图
 */
export function generateDesignReasoningFlow(
  designData: any,
  options: FlowGenerationOptions = {
    showDetailedParameters: true,
    showRuleNodes: true,
    parameterExpandLevel: 1,
    ruleDisplayMode: 'inline',
    fixedMainChain: true
  }
): WorkbenchFlowGraph {
  const nodes: (StepNode | ResultAnchorNode | ParameterNode | RuleNode | OutputNode)[] = []
  const edges: Edge[] = []
  const mainChainNodeIds: string[] = []

  // 示例：构建设计步骤
  const designSteps = [
    { number: 1, name: '输入条件', purpose: '承接型号、工况和基础输入' },
    { number: 2, name: '功率计算', purpose: '计算电机所需功率' },
    { number: 3, name: '扭矩校核', purpose: '校核扭矩是否满足要求' },
    { number: 4, name: '结果输出', purpose: '输出最终设计结果' }
  ]

  // 构建主步骤节点
  designSteps.forEach(step => {
    const stepNode = buildStepNode(step.number, step.name, step.purpose, options)
    nodes.push(stepNode)
    mainChainNodeIds.push(stepNode.id)

    // 为每个步骤添加结果锚点
    let resultAnchorNode: ResultAnchorNode | null = null
    
    switch (step.number) {
      case 1:
        // 输入条件步骤
        resultAnchorNode = buildResultAnchorNode(
          stepNode.id,
          '基础输入汇总',
          undefined,
          undefined,
          '汇总所有输入参数'
        )
        break
      case 2:
        // 功率计算步骤
        resultAnchorNode = buildResultAnchorNode(
          stepNode.id,
          '电机所需功率',
          designData?.power?.requiredPower || 0,
          'kW',
          'P = F × v / η'
        )
        break
      case 3:
        // 扭矩校核步骤
        resultAnchorNode = buildResultAnchorNode(
          stepNode.id,
          '扭矩校核结果',
          designData?.torque?.checkResult || '待计算',
          undefined,
          'T_required > T_friction'
        )
        break
      case 4:
        // 结果输出步骤
        resultAnchorNode = buildResultAnchorNode(
          stepNode.id,
          '最终设计结果',
          designData?.finalResult || '待完成',
          undefined,
          '综合所有计算结果'
        )
        break
    }

    if (resultAnchorNode) {
      nodes.push(resultAnchorNode)
      stepNode.resultAnchorIds.push(resultAnchorNode.id)
      
      // 添加步骤到结果锚点的边
      edges.push({
        id: generateEdgeId(stepNode.id, resultAnchorNode.id),
        source: stepNode.id,
        target: resultAnchorNode.id,
        type: 'result',
        label: '产生',
        style: {
          color: '#FF6B6B',
          width: 2,
          lineStyle: 'solid'
        }
      })
    }

    // 添加步骤之间的边（主链）
    if (step.number > 1) {
      const prevStepId = mainChainNodeIds[step.number - 2]
      const currentStepId = stepNode.id
      
      edges.push({
        id: generateEdgeId(prevStepId, currentStepId),
        source: prevStepId,
        target: currentStepId,
        type: 'default',
        label: '下一步',
        style: {
          color: '#4A90E2',
          width: 3,
          lineStyle: 'solid'
        }
      })
    }
  })

  // 添加参数节点（如果显示详细参数）
  if (options.showDetailedParameters) {
    // 输入参数
    const inputParameters = [
      { name: '滚筒直径', value: designData?.inputs?.drumDiameter || 0, unit: 'mm', role: ParameterRole.INPUT, isCore: true },
      { name: '滚筒长度', value: designData?.inputs?.drumLength || 0, unit: 'mm', role: ParameterRole.INPUT },
      { name: '物料密度', value: designData?.inputs?.materialDensity || 0, unit: 'kg/m³', role: ParameterRole.INPUT },
      { name: '输送速度', value: designData?.inputs?.conveyorSpeed || 0, unit: 'm/s', role: ParameterRole.INPUT, isCore: true }
    ]

    inputParameters.forEach(param => {
      const paramNode = buildParameterNode(
        param.name,
        param.role,
        param.value,
        param.unit,
        '用户输入',
        mainChainNodeIds[0], // 第一步：输入条件
        undefined,
        param.isCore
      )
      nodes.push(paramNode)

      // 连接到第一步的结果锚点
      const step1ResultAnchorId = nodes.find(n => 
        n.type === WorkbenchNodeType.RESULT_ANCHOR && 
        (n as ResultAnchorNode).stepId === mainChainNodeIds[0]
      )?.id

      if (step1ResultAnchorId) {
        edges.push({
          id: generateEdgeId(paramNode.id, step1ResultAnchorId),
          source: paramNode.id,
          target: step1ResultAnchorId,
          type: 'parameter',
          label: '输入',
          style: {
            color: '#3498DB',
            width: 1,
            lineStyle: 'dashed'
          }
        })
      }
    })

    // 中间参数
    const intermediateParameters = [
      { name: '滚筒重量', value: designData?.intermediate?.drumWeight || 0, unit: 'kg', role: ParameterRole.INTERMEDIATE },
      { name: '物料重量', value: designData?.intermediate?.materialWeight || 0, unit: 'kg', role: ParameterRole.INTERMEDIATE, isCore: true },
      { name: '总负载', value: designData?.intermediate?.totalLoad || 0, unit: 'kg', role: ParameterRole.INTERMEDIATE, isCore: true }
    ]

    intermediateParameters.forEach(param => {
      const paramNode = buildParameterNode(
        param.name,
        param.role,
        param.value,
        param.unit,
        '计算得出',
        mainChainNodeIds[1], // 第二步：功率计算
        undefined,
        param.isCore
      )
      nodes.push(paramNode)

      // 连接到第二步的结果锚点
      const step2ResultAnchorId = nodes.find(n => 
        n.type === WorkbenchNodeType.RESULT_ANCHOR && 
        (n as ResultAnchorNode).stepId === mainChainNodeIds[1]
      )?.id

      if (step2ResultAnchorId) {
        edges.push({
          id: generateEdgeId(paramNode.id, step2ResultAnchorId),
          source: paramNode.id,
          target: step2ResultAnchorId,
          type: 'parameter',
          label: '计算',
          style: {
            color: '#F39C12',
            width: 1,
            lineStyle: 'dashed'
          }
        })
      }
    })
  }

  // 添加规则节点（如果显示规则节点）
  if (options.showRuleNodes) {
    const rules = [
      {
        name: '功率安全系数',
        type: RuleType.THRESHOLD,
        expression: 'P_required * 1.2 <= P_rated',
        description: '电机额定功率需大于所需功率的1.2倍',
        parameters: ['电机所需功率', '电机额定功率'],
        resultAnchor: '电机所需功率',
        priority: 8
      },
      {
        name: '扭矩校验',
        type: RuleType.COMPARE,
        expression: 'T_required > T_friction',
        description: '所需扭矩必须大于摩擦力矩',
        parameters: ['所需扭矩', '摩擦力矩'],
        resultAnchor: '扭矩校核结果',
        priority: 9
      },
      {
        name: '转速范围',
        type: RuleType.RANGE,
        expression: '0 <= n <= 50',
        description: '电机转速必须在0-50Hz范围内',
        parameters: ['电机转速'],
        resultAnchor: '扭矩校核结果',
        priority: 6
      }
    ]

    rules.forEach(rule => {
      // 查找相关参数ID
      const relatedParameterIds = rule.parameters.map(paramName => 
        nodes.find(n => 
          n.type === WorkbenchNodeType.PARAMETER && 
          n.label === paramName
        )?.id
      ).filter(Boolean) as string[]

      // 查找相关结果锚点ID
      const relatedResultAnchorId = nodes.find(n => 
        n.type === WorkbenchNodeType.RESULT_ANCHOR && 
        n.label === rule.resultAnchor
      )?.id

      const ruleNode = buildRuleNode(
        rule.name,
        rule.type,
        rule.expression,
        rule.description,
        relatedParameterIds,
        relatedResultAnchorId,
        rule.priority
      )
      nodes.push(ruleNode)

      // 连接到相关结果锚点
      if (relatedResultAnchorId) {
        edges.push({
          id: generateEdgeId(ruleNode.id, relatedResultAnchorId),
          source: ruleNode.id,
          target: relatedResultAnchorId,
          type: 'rule',
          label: '校验',
          style: {
            color: '#FF9F43',
            width: 2,
            lineStyle: 'dotted'
          }
        })
      }
    })
  }

  // 添加输出节点
  const finalResultAnchor = nodes.find(n => 
    n.type === WorkbenchNodeType.RESULT_ANCHOR && 
    n.label === '最终设计结果'
  ) as ResultAnchorNode | undefined

  if (finalResultAnchor) {
    const outputNode = buildOutputNode(
      '设计完成',
      finalResultAnchor.value || '待完成',
      '所有设计步骤已完成',
      finalResultAnchor.id,
      true,
      []
    )
    nodes.push(outputNode)

    // 连接到最终结果锚点
    edges.push({
      id: generateEdgeId(finalResultAnchor.id, outputNode.id),
      source: finalResultAnchor.id,
      target: outputNode.id,
      type: 'default',
      label: '输出',
      style: {
        color: '#9B59B6',
        width: 3,
        lineStyle: 'solid'
      }
    })
  }

  // 构建完整的图结构
  const flowGraph: WorkbenchFlowGraph = {
    id: `design-flow-${Date.now()}`,
    nodes,
    edges,
    layout: {
      mainChainNodeIds,
      fixedMainChain: options.fixedMainChain,
      parameterExpandLevel: options.parameterExpandLevel,
      ruleDisplayMode: options.ruleDisplayMode
    },
    metadata: {
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      designScenarioId: designData?.scenarioId,
      designPointId: designData?.pointId
    }
  }

  return flowGraph
}

/**
 * 过滤图中的节点
 */
export function filterFlowGraph(
  graph: WorkbenchFlowGraph,
  filter: NodeFilter
): WorkbenchFlowGraph {
  const filteredNodes = graph.nodes.filter(node => {
    // 节点类型过滤
    if (filter.nodeTypes && filter.nodeTypes.length > 0) {
      if (!filter.nodeTypes.includes(node.type)) {
        return false
      }
    }

    // 参数角色过滤
    if (node.type === WorkbenchNodeType.PARAMETER && filter.parameterRoles && filter.parameterRoles.length > 0) {
      const paramNode = node as ParameterNode
      if (!filter.parameterRoles.includes(paramNode.role)) {
        return false
      }
    }

    // 规则类型过滤
    if (node.type === WorkbenchNodeType.RULE && filter.ruleTypes && filter.ruleTypes.length > 0) {
      const ruleNode = node as RuleNode
      if (!filter.ruleTypes.includes(ruleNode.ruleType)) {
        return false
      }
    }

    // 节点状态过滤
    if (filter.nodeStatuses && filter.nodeStatuses.length > 0) {
      if (!filter.nodeStatuses.includes(node.status || NodeStatus.NORMAL)) {
        return false
      }
    }

    // 核心节点过滤
    if (filter.coreOnly) {
      if (node.type === WorkbenchNodeType.PARAMETER) {
        const paramNode = node as ParameterNode
        if (!paramNode.isCore) {
          return false
        }
      }
    }

    return true
  })

  // 过滤边：只保留两个端点都在过滤后节点中的边
  const filteredNodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredEdges = graph.edges.filter(edge => 
    filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)
  )

  return {
    ...graph,
    nodes: filteredNodes,
    edges: filteredEdges
  }
}

/**
 * 获取节点的解释信息
 */
export function getNodeExplanation(
  graph: WorkbenchFlowGraph,
  nodeId: string
): any {
  const node = graph.nodes.find(n => n.id === nodeId)
  if (!node) {
    return null
  }

  switch (node.type) {
    case WorkbenchNodeType.STEP:
      const stepNode = node as StepNode
      return {
        nodeId,
        nodeType: node.type,
        title: `步骤解释：${stepNode.label}`,
        sections: [
          {
            title: '步骤目的',
            type: 'text',
            content: stepNode.purpose
          },
          {
            title: '关键输入',
            type: 'parameters',
            content: stepNode.parameterIds.map(paramId => {
              const paramNode = graph.nodes.find(n => n.id === paramId) as ParameterNode
              return paramNode ? {
                parameterId: paramNode.id,
                name: paramNode.label,
                value: paramNode.value,
                unit: paramNode.unit,
                role: paramNode.role,
                impactDescription: `用于计算${stepNode.label}`
              } : null
            }).filter(Boolean)
          },
          {
            title: '产生结果',
            type: 'text',
            content: stepNode.resultAnchorIds.map(resultId => {
              const resultNode = graph.nodes.find(n => n.id === resultId) as ResultAnchorNode
              return resultNode ? `${resultNode.label}: ${resultNode.value || '待计算'} ${resultNode.unit || ''}` : null
            }).filter(Boolean).join('；')
          }
        ]
      }

    case WorkbenchNodeType.RESULT_ANCHOR:
      const resultNode = node as ResultAnchorNode
      return {
        nodeId,
        nodeType: node.type,
        title: `结果解释：${resultNode.label}`,
        sections: [
          {
            title: '结果值',
            type: 'text',
            content: `${resultNode.value || '待计算'} ${resultNode.unit || ''}`
          },
          {
            title: '计算公式',
            type: 'formula',
            content: resultNode.formula || '无公式'
          },
          {
            title: '相关参数',
            type: 'parameters',
            content: resultNode.relatedParameterIds.map(paramId => {
              const paramNode = graph.nodes.find(n => n.id === paramId) as ParameterNode
              return paramNode ? {
                parameterId: paramNode.id,
                name: paramNode.label,
                value: paramNode.value,
                unit: paramNode.unit,
                role: paramNode.role,
                impactDescription: `影响${resultNode.label}的计算`
              } : null
            }).filter(Boolean)
          },
          {
            title: '校验规则',
            type: 'rules',
            content: resultNode.relatedRuleIds.map(ruleId => {
              const ruleNode = graph.nodes.find(n => n.id === ruleId) as RuleNode
              return ruleNode ? {
                ruleId: ruleNode.id,
                description: ruleNode.ruleDescription,
                expression: ruleNode.expression,
                checkResult: ruleNode.checkResult || { passed: false }
              } : null
            }).filter(Boolean)
          }
        ]
      }

    case WorkbenchNodeType.PARAMETER:
      const paramNode = node as ParameterNode
      return {
        nodeId,
        nodeType: node.type,
        title: `参数解释：${paramNode.label}`,
        sections: [
          {
            title: '参数值',
            type: 'text',
            content: `${paramNode.value || '未设置'} ${paramNode.unit || ''}`
          },
          {
            title: '参数角色',
            type: 'text',
            content: paramNode.role === ParameterRole.INPUT ? '输入参数' :
                    paramNode.role === ParameterRole.INTERMEDIATE ? '中间参数' : '查表参数'
          },
          {
            title: '参数来源',
            type: 'text',
            content: paramNode.source || '未知来源'
          },
          {
            title: '是否核心',
            type: 'text',
            content: paramNode.isCore ? '是（关键控制参数）' : '否'
          }
        ]
      }

    case WorkbenchNodeType.RULE:
      const ruleNode = node as RuleNode
      return {
        nodeId,
        nodeType: node.type,
        title: `规则解释：${ruleNode.label}`,
        sections: [
          {
            title: '规则描述',
            type: 'text',
            content: ruleNode.ruleDescription
          },
          {
            title: '规则表达式',
            type: 'formula',
            content: ruleNode.expression
          },
          {
            title: '校验结果',
            type: 'text',
            content: ruleNode.checkResult?.passed ? '通过' : '未通过'
          },
          {
            title: '规则优先级',
            type: 'text',
            content: `优先级：${ruleNode.priority}/10`
          }
        ]
      }

    default:
      return {
        nodeId,
        nodeType: node.type,
        title: `节点解释：${node.label}`,
        sections: [
          {
            title: '基本信息',
            type: 'text',
            content: node.description || '无详细描述'
          }
        ]
      }
  }
}

/**
 * 导出所有函数
 */
export default {
  generateDesignReasoningFlow,
  filterFlowGraph,
  getNodeExplanation
}