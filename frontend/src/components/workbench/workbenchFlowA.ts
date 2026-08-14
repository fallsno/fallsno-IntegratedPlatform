// A 风格流程图布局和渲染辅助函数
// 基于 mindmap-visual-hts200-hierarchical-multi-result-a.html 的设计

import type { ComputedRef } from 'vue'

// 节点类型映射
const TYPE_LABEL = {
  base: '基础参数',
  reference: '依据参数',
  calc: '计算节点',
  result: '结果量'
} as const

// 颜色定义
const CSS_COLORS = {
  baseFill: '#739cf2',
  baseStroke: '#4e7fe8',
  refFill: '#a683ef',
  refStroke: '#8358dd',
  calcFill: '#6cdcb7',
  calcStroke: '#31bf95',
  sharedFill: '#56c9c4',
  sharedStroke: '#209d9f',
  resultFill: '#ffc857',
  resultStroke: '#ebaa14',
  resultSoftFill: '#fde68