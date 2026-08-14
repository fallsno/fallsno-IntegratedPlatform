<template>
  <div class="formula-flow-chart">
    <!-- 图表容器 -->
    <div ref="chartRef" class="formula-flow-chart__container"></div>
    
    <!-- 图例 -->
    <div v-if="showLegend" class="formula-flow-chart__legend">
      <div class="legend-item" v-for="item in legendItems" :key="item.type">
        <div class="legend-color" :style="{ backgroundColor: item.color }"></div>
        <span class="legend-label">{{ item.label }}</span>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-if="isEmpty" class="formula-flow-chart__empty">
      <div class="empty-icon">📊</div>
      <div class="empty-title">暂无设计链路数据</div>
      <div class="empty-description">当前模块暂无可展示的设计推理链路</div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  // 数据
  nodes: {
    type: Array,
    default: () => []
  },
  edges: {
    type: Array,
    default: () => []
  },
  
  // 配置
  showLegend: {
    type: Boolean,
    default: true
  },
  autoLayout: {
    type: Boolean,
    default: true
  },
  animation: {
    type: Boolean,
    default: true
  },
  
  // 交互
  selectedNodeId: {
    type: String,
    default: ''
  },
  zoom: {
    type: Number,
    default: 1
  },
  center: {
    type: Array,
    default: () => ['50%', '50%']
  }
})

const emit = defineEmits([
  'node-click',
  'node-dblclick',
  'edge-click',
  'zoom-change',
  'center-change'
])

const chartRef = ref(null)
let chartInstance = null

// 计算是否为空
const isEmpty = computed(() => {
  return !props.nodes || props.nodes.length === 0
})

// 图例项
const legendItems = computed(() => [
  { type: 'input', label: '输入条件', color: '#3b82f6' },
  { type: 'calculation', label: '计算节点', color: '#64748b' },
  { type: 'output', label: '输出结果', color: '#f97316' },
  { type: 'parameter', label: '关键参数', color: '#94a3b8' },
  { type: 'rule', label: '校验规则', color: '#ef4444' }
])

// 节点类型到颜色的映射
const nodeTypeColorMap = {
  input: '#3b82f6',
  calculation: '#64748b',
  output: '#f97316',
  parameter: '#94a3b8',
  rule: '#ef4444',
  result_anchor: '#f97316',
  step: '#64748b'
}

// 节点类型到形状的映射
const nodeTypeShapeMap = {
  input: 'roundRect',
  calculation: 'roundRect',
  output: 'roundRect',
  parameter: 'circle',
  rule: 'diamond',
  result_anchor: 'roundRect',
  step: 'roundRect'
}

// 构建图表选项
const buildChartOption = () => {
  // 处理节点数据
  const processedNodes = props.nodes.map(node => {
    const nodeType = node.nodeType || 'calculation'
    const isSelected = node.id === props.selectedNodeId

    return {
      ...node,
      category: nodeType, // ECharts required mapping
      symbol: nodeTypeShapeMap[nodeType] || 'roundRect',
      symbolSize: getNodeSize(nodeType, isSelected),
      itemStyle: {
        color: nodeTypeColorMap[nodeType] || '#64748b',
        borderColor: isSelected ? '#3b82f6' : '#ffffff',
        borderWidth: isSelected ? 3 : 2,
        shadowColor: isSelected ? 'rgba(59, 130, 246, 0.25)' : 'rgba(15, 23, 42, 0.1)',
        shadowBlur: isSelected ? 12 : 8,
        shadowOffsetY: isSelected ? 4 : 2
      },
      label: {
        show: true,
        position: getLabelPosition(nodeType),
        distance: getLabelDistance(nodeType),
        formatter: getLabelFormatter(node),
        fontSize: getLabelFontSize(nodeType),
        fontWeight: '500',
        color: '#0f172a',
        backgroundColor: 'rgba(255, 255, 255, 0.85)',
        padding: [2, 6],
        borderRadius: 4,
        borderWidth: 1,
        borderColor: 'rgba(226, 232, 240, 0.5)'
      }
    }
  })

  // 处理边数据
  const processedEdges = props.edges.map(edge => {
    const sourceNode = props.nodes.find(n => n.id === edge.source)
    const targetNode = props.nodes.find(n => n.id === edge.target)
    const sourceType = sourceNode?.nodeType || 'calculation'
    const targetType = targetNode?.nodeType || 'calculation'
    
    // 如果边关联的节点不存在，ECharts 会报错，这里增加容错
    if (!sourceNode || !targetNode) {
      console.warn(`[FormulaFlowChart] Edge missing node: source=${edge.source}, target=${edge.target}`)
    }

    return {
      ...edge,
      lineStyle: getEdgeStyle(sourceType, targetType, edge),
      label: getEdgeLabel(edge)
    }
  }).filter(edge => {
    // 过滤掉因为节点缺失导致无效的边，防止 ECharts 渲染崩溃
    return props.nodes.some(n => n.id === edge.source) && props.nodes.some(n => n.id === edge.target)
  })

  // 计算节点位置（三层垂直布局）
  const positionedNodes = props.autoLayout 
    ? calculateNodePositions(processedNodes, processedEdges)
    : processedNodes

  return {
    animation: props.animation,
    animationDuration: 300,
    animationEasing: 'cubicOut',
    
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: {
        color: '#0f172a',
        fontSize: 12
      },
      formatter: function(params) {
        if (params.dataType === 'edge') {
          const source = params.data.source || ''
          const target = params.data.target || ''
          const label = params.data.label || ''
          return `<div style="font-weight: 500; margin-bottom: 4px;">${source} → ${target}</div>
                  <div style="color: #64748b; font-size: 11px;">${label}</div>`
        } else {
          const node = params.data
          let html = `<div style="font-weight: 600; margin-bottom: 6px;">${node.title || node.name || '未命名节点'}</div>`
          
          if (node.summary) {
            html += `<div style="color: #475569; font-size: 12px; margin-bottom: 4px;">${node.summary}</div>`
          }
          
          if (node.nodeType) {
            const typeMap = {
              input: '输入条件',
              calculation: '计算节点',
              output: '输出结果',
              parameter: '关键参数',
              rule: '校验规则',
              result_anchor: '结果锚点',
              step: '设计步骤'
            }
            html += `<div style="color: #64748b; font-size: 11px;">类型: ${typeMap[node.nodeType] || node.nodeType}</div>`
          }
          
          return html
        }
      }
    },
    
    series: [
      {
        type: 'graph',
        layout: 'none',
        coordinateSystem: null,
        roam: true,
        center: props.center,
        zoom: props.zoom,
        draggable: true,
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 12],
        edgeLabel: {
          show: false
        },
        emphasis: {
          focus: 'adjacency',
          scale: false,
          itemStyle: {
            shadowBlur: 16,
            shadowColor: 'rgba(0, 0, 0, 0.15)'
          }
        },
        data: positionedNodes,
        links: processedEdges,
        categories: [
          { name: 'input', itemStyle: { color: '#3b82f6' } },
          { name: 'calculation', itemStyle: { color: '#64748b' } },
          { name: 'output', itemStyle: { color: '#f97316' } },
          { name: 'parameter', itemStyle: { color: '#94a3b8' } },
          { name: 'rule', itemStyle: { color: '#ef4444' } },
          { name: 'result_anchor', itemStyle: { color: '#f97316' } },
          { name: 'step', itemStyle: { color: '#64748b' } }
        ]
      }
    ],
    
    grid: {
      top: 20,
      right: 20,
      bottom: 20,
      left: 20
    }
  }
}

// 辅助函数：获取节点大小
function getNodeSize(nodeType, isSelected) {
  const baseSize = {
    input: 50,
    calculation: 60,
    output: 70,
    parameter: 40,
    rule: 45,
    result_anchor: 65,
    step: 60
  }[nodeType] || 50
  
  return isSelected ? baseSize * 1.2 : baseSize
}

// 辅助函数：获取标签位置
function getLabelPosition(nodeType) {
  const positionMap = {
    input: 'inside',
    calculation: 'inside',
    output: 'inside',
    parameter: 'bottom',
    rule: 'top',
    result_anchor: 'inside',
    step: 'inside'
  }
  
  return positionMap[nodeType] || 'inside'
}

// 辅助函数：获取标签距离
function getLabelDistance(nodeType) {
  const distanceMap = {
    input: 0,
    calculation: 0,
    output: 0,
    parameter: 10,
    rule: 10,
    result_anchor: 0,
    step: 0
  }
  
  return distanceMap[nodeType] || 0
}

// 辅助函数：获取标签格式化器
function getLabelFormatter(node) {
  return function() {
    const title = node.title || node.name || '未命名'
    
    // 对于参数节点，显示更简洁
    if (node.nodeType === 'parameter') {
      return title.length > 8 ? title.substring(0, 8) + '...' : title
    }
    
    // 对于其他节点，可以换行显示
    if (title.length > 10) {
      const words = title.split(' ')
      if (words.length > 1) {
        return words.join('\n')
      }
    }
    
    return title
  }
}

// 辅助函数：获取标签字体大小
function getLabelFontSize(nodeType) {
  const sizeMap = {
    input: 12,
    calculation: 12,
    output: 13,
    parameter: 10,
    rule: 11,
    result_anchor: 12,
    step: 12
  }
  
  return sizeMap[nodeType] || 12
}

// 辅助函数：获取边样式 - 根据设计规范优化
function getEdgeStyle(sourceType, targetType, edge) {
  // 首先检查边类型，如果有明确的edge.type，优先使用
  if (edge?.type) {
    const edgeType = edge.type
    
    // 根据边类型返回对应的样式
    const edgeStyleMap = {
      // 计算流转：灰色虚线，中等弯曲
      calculation_flow: {
        color: '#94A3B8',
        width: 1.5,
        type: 'dashed',
        curveness: 0.16,
        opacity: 0.7
      },
      // 物理承接：蓝色实线，轻微弯曲
      physical_connection: {
        color: '#63B3ED',
        width: 2,
        type: 'solid',
        curveness: 0.03,
        opacity: 0.85
      },
      // 反馈回环：橙色虚线，较大弯曲
      feedback_loop: {
        color: '#ED8936',
        width: 1.5,
        type: 'dashed',
        curveness: 0.25,
        opacity: 0.6
      },
      // 规则校验：红色实线，较小弯曲
      rule_check: {
        color: '#F56565',
        width: 2,
        type: 'solid',
        curveness: 0.1,
        opacity: 0.9
      },
      // 错误路径：红色点线，中等弯曲
      error_path: {
        color: '#DC2626',
        width: 1.5,
        type: 'dotted',
        curveness: 0.15,
        opacity: 0.8
      },
      // 默认：浅灰色实线，轻微弯曲
      default: {
        color: '#CBD5E1',
        width: 2,
        type: 'solid',
        curveness: 0.05,
        opacity: 0.7
      }
    }
    
    return edgeStyleMap[edgeType] || edgeStyleMap.default
  }
  
  // 如果没有明确的edge.type，根据节点类型推断
  // 1. 主流程边（物理承接）
  if ((sourceType === 'step' && targetType === 'step') || 
      (sourceType === 'calculation' && targetType === 'calculation')) {
    return {
      color: '#63B3ED',      // 物理承接：蓝色实线
      width: 2,
      type: 'solid',
      curveness: 0.03,       // 主流程：轻微弯曲
      opacity: 0.85
    }
  }
  
  // 2. 参数边（计算流转）
  if (sourceType === 'parameter' || targetType === 'parameter') {
    return {
      color: '#94A3B8',      // 计算流转：灰色虚线
      width: 1.5,
      type: 'dashed',
      curveness: 0.16,       // 计算流转：中等弯曲
      opacity: 0.7
    }
  }
  
  // 3. 规则边（规则校验）
  if (sourceType === 'rule' || targetType === 'rule') {
    return {
      color: '#F56565',      // 规则校验：红色实线
      width: 2,
      type: 'solid',
      curveness: 0.1,        // 规则校验：较小弯曲
      opacity: 0.9
    }
  }
  
  // 4. 反馈回环边（从输出层指向输入层或计算层）
  if ((sourceType === 'output' || sourceType === 'result_anchor') && 
      (targetType === 'input' || targetType === 'calculation' || targetType === 'step')) {
    return {
      color: '#ED8936',      // 反馈回环：橙色虚线
      width: 1.5,
      type: 'dashed',
      curveness: 0.25,       // 反馈回环：较大弯曲
      opacity: 0.6
    }
  }
  
  // 5. 错误路径边（根据节点状态判断）
  // 获取源节点和目标节点
  const sourceNode = props.nodes.find(n => n.id === edge?.source)
  const targetNode = props.nodes.find(n => n.id === edge?.target)
  
  // 如果源节点或目标节点的状态为错误，使用错误路径样式
  if ((sourceNode?.status === 'error' || targetNode?.status === 'error') ||
      (sourceNode?.isValid === false || targetNode?.isValid === false)) {
    return {
      color: '#DC2626',      // 错误路径：红色点线
      width: 1.5,
      type: 'dotted',
      curveness: 0.15,
      opacity: 0.8
    }
  }
  
  // 默认边（其他情况）
  return {
    color: '#CBD5E1',        // 默认：浅灰色实线
    width: 2,
    type: 'solid',
    curveness: 0.05,
    opacity: 0.7
  }
}

// 辅助函数：获取边标签 - 根据设计规范优化
function getEdgeLabel(edge) {
  // 如果没有标签，返回null
  if (!edge.label) return null
  
  // 根据边类型确定标签样式
  const edgeType = edge.type || 'default'
  
  // 标签样式配置
  const labelStyles = {
    // 计算流转标签
    calculation_flow: {
      fontSize: 9,
      color: '#64748B',
      backgroundColor: 'rgba(248, 250, 252, 0.95)',
      borderColor: 'rgba(203, 213, 225, 0.6)',
      borderWidth: 1,
      padding: [1, 3],
      borderRadius: 2,
      fontWeight: 'normal'
    },
    // 物理承接标签
    physical_connection: {
      fontSize: 10,
      color: '#1E40AF',
      backgroundColor: 'rgba(219, 234, 254, 0.95)',
      borderColor: 'rgba(147, 197, 253, 0.6)',
      borderWidth: 1,
      padding: [2, 4],
      borderRadius: 3,
      fontWeight: '500'
    },
    // 反馈回环标签
    feedback_loop: {
      fontSize: 9,
      color: '#9A3412',
      backgroundColor: 'rgba(254, 243, 199, 0.95)',
      borderColor: 'rgba(253, 224, 71, 0.6)',
      borderWidth: 1,
      padding: [1, 3],
      borderRadius: 2,
      fontWeight: 'normal',
      fontStyle: 'italic'
    },
    // 规则校验标签
    rule_check: {
      fontSize: 9,
      color: '#991B1B',
      backgroundColor: 'rgba(254, 226, 226, 0.95)',
      borderColor: 'rgba(252, 165, 165, 0.6)',
      borderWidth: 1,
      padding: [1, 3],
      borderRadius: 2,
      fontWeight: '500'
    },
    // 错误路径标签
    error_path: {
      fontSize: 8,
      color: '#7F1D1D',
      backgroundColor: 'rgba(254, 202, 202, 0.95)',
      borderColor: 'rgba(252, 165, 165, 0.8)',
      borderWidth: 1,
      padding: [1, 2],
      borderRadius: 1,
      fontWeight: 'normal',
      fontStyle: 'italic'
    },
    // 默认标签
    default: {
      fontSize: 10,
      color: '#475569',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: 'rgba(226, 232, 240, 0.6)',
      borderWidth: 1,
      padding: [2, 4],
      borderRadius: 3,
      fontWeight: 'normal'
    }
  }
  
  // 获取对应类型的样式，如果不存在则使用默认样式
  const style = labelStyles[edgeType] || labelStyles.default
  
  return {
    show: true,
    formatter: edge.label,
    fontSize: style.fontSize,
    color: style.color,
    backgroundColor: style.backgroundColor,
    borderColor: style.borderColor,
    borderWidth: style.borderWidth,
    padding: style.padding,
    borderRadius: style.borderRadius,
    fontWeight: style.fontWeight,
    fontStyle: style.fontStyle || 'normal'
  }
}

// 辅助函数：计算节点位置（三层垂直布局）
function calculateNodePositions(nodes, edges) {
  const canvasWidth = 1200
  
  // 按动态层级分组，必须确保容错，如果有节点不在这三层里，统一放到 calculation 兜底
  const nodesByLayer = {
    input: nodes.filter(n => n.layer === 'input'),
    calculation: nodes.filter(n => n.layer === 'calculation' || !['input', 'output'].includes(n.layer)),
    output: nodes.filter(n => n.layer === 'output')
  }

  const positionedNodes = []
  
  // 辅助函数：在指定Y基础坐标区域内，将节点网格化排布
  const layoutLayerNodes = (layerNodes, baseY) => {
    const total = layerNodes.length
    if (total === 0) return
    
    // 如果节点太多，分多行排列，每行最多 8 个
    const maxPerRow = 8
    const rows = Math.ceil(total / maxPerRow)
    const rowHeight = 100 // 每行高度
    
    layerNodes.forEach((node, index) => {
      const rowIndex = Math.floor(index / maxPerRow)
      const colIndex = index % maxPerRow
      const countInThisRow = rowIndex === rows - 1 ? (total % maxPerRow || maxPerRow) : maxPerRow
      
      // 在这行内水平居中分布
      const x = canvasWidth * 0.1 + (canvasWidth * 0.8 / (countInThisRow + 1)) * (colIndex + 1)
      const y = baseY + rowIndex * rowHeight
      
      positionedNodes.push({
        ...node,
        x: x,
        y: y,
        fixed: true // ECharts none 布局强制需要
      })
    })
  }

  // 输入层从 y=100 开始
  layoutLayerNodes(nodesByLayer.input, 100)
  
  // 计算层，基于输入层的行数往下推
  const inputRows = Math.ceil(nodesByLayer.input.length / 8) || 1
  const calcBaseY = 100 + inputRows * 100 + 100
  layoutLayerNodes(nodesByLayer.calculation, calcBaseY)
  
  // 输出层，基于计算层的行数往下推
  const calcRows = Math.ceil(nodesByLayer.calculation.length / 8) || 1
  const outputBaseY = calcBaseY + calcRows * 100 + 100
  layoutLayerNodes(nodesByLayer.output, outputBaseY)

  return positionedNodes
}

// 渲染图表
const renderChart = async () => {
  await nextTick()
  
  if (!chartRef.value || isEmpty.value) {
    if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
    }
    return
  }
  
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
    
    // 绑定事件
    chartInstance.on('click', (params) => {
      if (params.dataType === 'node') {
        emit('node-click', params.data)
      } else if (params.dataType === 'edge') {
        emit('edge-click', params.data)
      }
    })
    
    chartInstance.on('dblclick', (params) => {
      if (params.dataType === 'node') {
        emit('node-dblclick', params.data)
      }
    })
    
    chartInstance.on('graphRoam', () => {
      if (chartInstance) {
        const series = chartInstance.getOption()?.series?.[0] || {}
        emit('zoom-change', Number(series.zoom || 1))
        emit('center-change', Array.isArray(series.center) ? [...series.center] : ['50%', '50%'])
      }
    })
  }
  
  chartInstance.setOption(buildChartOption(), true)
  chartInstance.resize()
}

// 监听数据变化
watch(
  () => [props.nodes, props.edges, props.selectedNodeId],
  () => {
    renderChart()
  },
  { deep: true }
)

// 监听窗口大小变化
const handleResize = () => {
  chartInstance?.resize()
}

// 生命周期
onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
@import '@/assets/styles/workbench-formula-flow.css';

.formula-flow-chart {
  position: relative;
  width: 100%;
  height: 100%;
}

.formula-flow-chart__container {
  width: 100%;
  height: 100%;
  min-height: 600px;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
}

.formula-flow-chart__legend {
  position: absolute;
  bottom: 20px;
  left: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 8px;
  backdrop-filter: blur(4px);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.08);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-label {
  font-size: 11px;
  color: #475569;
  font-weight: 500;
}

.formula-flow-chart__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #64748b;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #475569;
}

.empty-description {
  font-size: 14px;
  max-width: 400px;
  line-height: 1.5;
}

/* 响应式调整 */
@media (max-width: 1024px) {
  .formula-flow-chart__container {
    min-height: 500px;
  }

  .formula-flow-chart__legend {
    bottom: 16px;
    left: 16px;
    padding: 10px 12px;
    gap: 10px;
  }
}

@media (max-width: 768px) {
  .formula-flow-chart__container {
    min-height: 400px;
  }

  .formula-flow-chart__legend {
    position: static;
    margin-top: 16px;
    justify-content: center;
  }
}
</style>