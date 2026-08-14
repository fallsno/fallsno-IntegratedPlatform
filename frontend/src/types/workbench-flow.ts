/**
 * 工作台计算链路类型定义
 * 用于支持设计推理图的生成和展示
 */

// ==================== 节点类型枚举 ====================

/**
 * 工作台节点类型枚举
 */
export enum WorkbenchNodeType {
  /** 主步骤节点 - 设计过程的主要步骤 */
  STEP = 'step',
  /** 结果锚点节点 - 步骤中的核心计算结果 */
  RESULT_ANCHOR = 'result_anchor',
  /** 参数挂点节点 - 输入、中间或查表参数 */
  PARAMETER = 'parameter',
  /** 规则节点 - 校验规则和决策规则 */
  RULE = 'rule',
  /** 终局输出节点 - 最终设计结果 */
  OUTPUT = 'output'
}

/**
 * 节点层级类型枚举 - 用于垂直布局分类
 */
export enum NodeLayerType {
  /** 输入层 - 基础参数、边界条件、用户设定 */
  INPUT = 'input',
  /** 计算层 - 计算公式、中间变量、逻辑判断 */
  CALCULATION = 'calculation',
  /** 输出层 - 最终计算结果、设计建议、校验结论 */
  OUTPUT = 'output'
}

/**
 * 参数角色枚举
 */
export enum ParameterRole {
  /** 基础输入参数 - 用户直接输入的参数 */
  INPUT = 'input',
  /** 中间量 - 计算过程中产生的中间结果 */
  INTERMEDIATE = 'intermediate',
  /** 查表来源 - 从查表或经验公式获取的参数 */
  LOOKUP = 'lookup'
}

/**
 * 规则类型枚举
 */
export enum RuleType {
  /** 阈值判断 - 参数必须满足的阈值条件 */
  THRESHOLD = 'threshold',
  /** 比较判断 - 两个参数之间的比较关系 */
  COMPARE = 'compare',
  /** 范围判断 - 参数必须在指定范围内 */
  RANGE = 'range',
  /** 决策判断 - 基于条件的决策分支 */
  DECISION = 'decision'
}

/**
 * 节点状态枚举
 */
export enum NodeStatus {
  /** 正常状态 */
  NORMAL = 'normal',
  /** 警告状态 - 需要关注但未违反规则 */
  WARNING = 'warning',
  /** 错误状态 - 违反规则或计算失败 */
  ERROR = 'error',
  /** 成功状态 - 规则校验通过 */
  SUCCESS = 'success'
}

// ==================== 核心数据结构 ====================

/**
 * 基础节点接口
 */
export interface BaseNode {
  /** 节点唯一标识 */
  id: string;
  /** 节点类型 */
  type: WorkbenchNodeType;
  /** 节点层级 - 用于垂直布局分类 */
  layer?: NodeLayerType;
  /** 节点标签（显示名称） */
  label: string;
  /** 节点状态 */
  status?: NodeStatus;
  /** 节点描述信息 */
  description?: string;
  /** 节点位置信息（用于布局） */
  position?: {
    x: number;
    y: number;
  };
  /** 节点样式配置 */
  style?: {
    /** 节点颜色 */
    color?: string;
    /** 边框颜色 */
    borderColor?: string;
    /** 边框宽度 */
    borderWidth?: number;
    /** 节点大小 */
    size?: number;
  };
}

/**
 * 主步骤节点
 */
export interface StepNode extends BaseNode {
  type: WorkbenchNodeType.STEP;
  /** 步骤序号 */
  stepNumber: number;
  /** 步骤目的描述 */
  purpose: string;
  /** 关联的结果锚点ID列表 */
  resultAnchorIds: string[];
  /** 关联的参数ID列表 */
  parameterIds: string[];
  /** 关联的规则ID列表 */
  ruleIds: string[];
  /** 是否展开显示详细参数 */
  expanded?: boolean;
}

/**
 * 结果锚点节点
 */
export interface ResultAnchorNode extends BaseNode {
  type: WorkbenchNodeType.RESULT_ANCHOR;
  /** 所属步骤ID */
  stepId: string;
  /** 结果值（计算值） */
  value?: number | string;
  /** 结果单位 */
  unit?: string;
  /** 计算公式或推导逻辑 */
  formula?: string;
  /** 影响的下游步骤ID列表 */
  downstreamStepIds: string[];
  /** 关联的参数ID列表（用于计算此结果的参数） */
  relatedParameterIds: string[];
  /** 关联的规则ID列表（校验此结果的规则） */
  relatedRuleIds: string[];
}

/**
 * 参数节点
 */
export interface ParameterNode extends BaseNode {
  type: WorkbenchNodeType.PARAMETER;
  /** 参数角色 */
  role: ParameterRole;
  /** 参数值 */
  value?: number | string;
  /** 参数单位 */
  unit?: string;
  /** 参数来源描述 */
  source?: string;
  /** 所属步骤ID */
  stepId?: string;
  /** 关联的结果锚点ID */
  resultAnchorId?: string;
  /** 是否为核心参数（需要突出显示） */
  isCore?: boolean;
  /** 参数取值范围 */
  range?: {
    min?: number;
    max?: number;
    recommended?: number;
  };
}

/**
 * 规则节点
 */
export interface RuleNode extends BaseNode {
  type: WorkbenchNodeType.RULE;
  /** 规则类型 */
  ruleType: RuleType;
  /** 规则表达式 */
  expression: string;
  /** 规则描述（用户可读） */
  ruleDescription: string;
  /** 规则校验结果 */
  checkResult?: {
    /** 是否通过 */
    passed: boolean;
    /** 实际值 */
    actualValue?: number | string;
    /** 期望值或阈值 */
    expectedValue?: number | string;
    /** 错误信息（如果不通过） */
    errorMessage?: string;
  };
  /** 关联的参数ID列表 */
  relatedParameterIds: string[];
  /** 关联的结果锚点ID */
  relatedResultAnchorId?: string;
  /** 规则优先级（1-10，越高越重要） */
  priority: number;
}

/**
 * 终局输出节点
 */
export interface OutputNode extends BaseNode {
  type: WorkbenchNodeType.OUTPUT;
  /** 输出值 */
  value: number | string;
  /** 输出单位 */
  unit?: string;
  /** 输出描述 */
  description: string;
  /** 关联的最终结果锚点ID */
  resultAnchorId: string;
  /** 是否通过所有校验 */
  allChecksPassed: boolean;
  /** 未通过的规则ID列表 */
  failedRuleIds: string[];
}

// ==================== 图结构定义 ====================

/**
 * 边类型枚举 - 根据设计规范定义
 */
export enum EdgeType {
  /** 计算流转 - 公式计算依赖关系 */
  CALCULATION_FLOW = 'calculation_flow',
  /** 物理承接 - 物理量传递关系 */
  PHYSICAL_CONNECTION = 'physical_connection',
  /** 反馈回环 - 反馈调节关系 */
  FEEDBACK_LOOP = 'feedback_loop',
  /** 规则校验 - 规则判断关系 */
  RULE_CHECK = 'rule_check',
  /** 错误路径 - 错误或无效路径 */
  ERROR_PATH = 'error_path',
  /** 默认类型 */
  DEFAULT = 'default'
}

/**
 * 边连接关系
 */
export interface Edge {
  /** 边唯一标识 */
  id: string;
  /** 源节点ID */
  source: string;
  /** 目标节点ID */
  target: string;
  /** 边类型 */
  type?: EdgeType;
  /** 边标签 */
  label?: string;
  /** 边样式 */
  style?: {
    /** 边颜色 */
    color?: string;
    /** 边宽度 */
    width?: number;
    /** 边类型：实线、虚线等 */
    lineStyle?: 'solid' | 'dashed' | 'dotted';
  };
}

/**
 * 工作台流程图数据结构
 */
export interface WorkbenchFlowGraph {
  /** 图唯一标识 */
  id: string;
  /** 所有节点 */
  nodes: (StepNode | ResultAnchorNode | ParameterNode | RuleNode | OutputNode)[];
  /** 所有边 */
  edges: Edge[];
  /** 布局配置 */
  layout: {
    /** 主链节点ID顺序 */
    mainChainNodeIds: string[];
    /** 是否固定主链位置 */
    fixedMainChain: boolean;
    /** 参数展开层级 */
    parameterExpandLevel: number;
    /** 规则显示模式：inline（内联）或 side（侧边） */
    ruleDisplayMode: 'inline' | 'side';
  };
  /** 元数据 */
  metadata: {
    /** 创建时间 */
    createdAt: string;
    /** 更新时间 */
    updatedAt: string;
    /** 设计场景ID */
    designScenarioId?: string;
    /** 设计点ID */
    designPointId?: string;
  };
}

// ==================== 右侧面板数据结构 ====================

/**
 * 节点解释信息
 */
export interface NodeExplanation {
  /** 节点ID */
  nodeId: string;
  /** 节点类型 */
  nodeType: WorkbenchNodeType;
  /** 解释标题 */
  title: string;
  /** 解释内容结构 */
  sections: ExplanationSection[];
}

/**
 * 解释部分
 */
export interface ExplanationSection {
  /** 部分标题 */
  title: string;
  /** 部分类型 */
  type: 'text' | 'formula' | 'parameters' | 'rules' | 'impact';
  /** 内容 */
  content: string | ParameterReference[] | RuleReference[] | ImpactAnalysis[];
}

/**
 * 参数引用
 */
export interface ParameterReference {
  /** 参数ID */
  parameterId: string;
  /** 参数名称 */
  name: string;
  /** 参数值 */
  value: number | string;
  /** 参数单位 */
  unit?: string;
  /** 参数角色 */
  role: ParameterRole;
  /** 对当前节点的影响描述 */
  impactDescription?: string;
}

/**
 * 规则引用
 */
export interface RuleReference {
  /** 规则ID */
  ruleId: string;
  /** 规则描述 */
  description: string;
  /** 规则表达式 */
  expression: string;
  /** 校验结果 */
  checkResult: {
    passed: boolean;
    actualValue?: number | string;
    expectedValue?: number | string;
  };
  /** 对设计的影响 */
  designImpact?: string;
}

/**
 * 影响分析
 */
export interface ImpactAnalysis {
  /** 影响类型：upstream（上游）或 downstream（下游） */
  type: 'upstream' | 'downstream';
  /** 影响的节点ID */
  nodeId: string;
  /** 影响描述 */
  description: string;
  /** 影响程度：low, medium, high */
  severity: 'low' | 'medium' | 'high';
}

/**
 * 右侧面板上下文
 */
export interface PanelContext {
  /** 当前选中的节点ID */
  selectedNodeId: string | null;
  /** 当前选中的节点类型 */
  selectedNodeType: WorkbenchNodeType | null;
  /** 面板显示模式 */
  displayMode: 'explanation' | 'parameters' | 'rules' | 'impact';
  /** 是否展开所有部分 */
  expandAll: boolean;
}

// ==================== 颜色语义系统 ====================

/**
 * 颜色语义配置
 */
export interface ColorSemantics {
  /** 节点类型颜色映射 */
  nodeTypeColors: Record<WorkbenchNodeType, string>;
  /** 参数角色颜色映射 */
  parameterRoleColors: Record<ParameterRole, string>;
  /** 规则类型颜色映射 */
  ruleTypeColors: Record<RuleType, string>;
  /** 节点状态颜色映射 */
  nodeStatusColors: Record<NodeStatus, string>;
}

/**
 * 默认颜色语义配置
 */
export const DEFAULT_COLOR_SEMANTICS: ColorSemantics = {
  nodeTypeColors: {
    [WorkbenchNodeType.STEP]: '#4A90E2',        // 蓝色 - 主步骤
    [WorkbenchNodeType.RESULT_ANCHOR]: '#FF6B6B', // 红色 - 结果锚点
    [WorkbenchNodeType.PARAMETER]: '#36B37E',   // 绿色 - 参数
    [WorkbenchNodeType.RULE]: '#FF9F43',        // 橙色 - 规则
    [WorkbenchNodeType.OUTPUT]: '#9B59B6'       // 紫色 - 输出
  },
  parameterRoleColors: {
    [ParameterRole.INPUT]: '#3498DB',           // 蓝色 - 输入参数
    [ParameterRole.INTERMEDIATE]: '#F39C12',    // 橙色 - 中间参数
    [ParameterRole.LOOKUP]: '#2ECC71'           // 绿色 - 查表参数
  },
  ruleTypeColors: {
    [RuleType.THRESHOLD]: '#E74C3C',           // 红色 - 阈值规则
    [RuleType.COMPARE]: '#F1C40F',             // 黄色 - 比较规则
    [RuleType.RANGE]: '#1ABC9C',               // 青色 - 范围规则
    [RuleType.DECISION]: '#9B59B6'             // 紫色 - 决策规则
  },
  nodeStatusColors: {
    [NodeStatus.NORMAL]: '#95A5A6',            // 灰色 - 正常
    [NodeStatus.WARNING]: '#F39C12',           // 橙色 - 警告
    [NodeStatus.ERROR]: '#E74C3C',             // 红色 - 错误
    [NodeStatus.SUCCESS]: '#2ECC71'            // 绿色 - 成功
  }
};

// ==================== 工具函数类型 ====================

/**
 * 流程图生成选项
 */
export interface FlowGenerationOptions {
  /** 是否显示详细参数 */
  showDetailedParameters: boolean;
  /** 是否显示规则节点 */
  showRuleNodes: boolean;
  /** 参数展开层级（0-3） */
  parameterExpandLevel: number;
  /** 规则显示模式 */
  ruleDisplayMode: 'inline' | 'side';
  /** 是否固定主链布局 */
  fixedMainChain: boolean;
  /** 颜色主题 */
  colorTheme?: 'default' | 'high-contrast' | 'color-blind';
}

/**
 * 节点过滤条件
 */
export interface NodeFilter {
  /** 节点类型过滤 */
  nodeTypes?: WorkbenchNodeType[];
  /** 参数角色过滤 */
  parameterRoles?: ParameterRole[];
  /** 规则类型过滤 */
  ruleTypes?: RuleType[];
  /** 节点状态过滤 */
  nodeStatuses?: NodeStatus[];
  /** 是否只显示核心节点 */
  coreOnly?: boolean;
}

// ==================== 事件类型 ====================

/**
 * 节点点击事件
 */
export interface NodeClickEvent {
  /** 节点ID */
  nodeId: string;
  /** 节点类型 */
  nodeType: WorkbenchNodeType;
  /** 事件类型 */
  eventType: 'click' | 'double-click' | 'context-menu';
  /** 原始事件 */
  originalEvent: MouseEvent;
}

/**
 * 节点展开/折叠事件
 */
export interface NodeExpandEvent {
  /** 节点ID */
  nodeId: string;
  /** 节点类型 */
  nodeType: WorkbenchNodeType;
  /** 是否展开 */
  expanded: boolean;
}

/**
 * 规则校验事件
 */
export interface RuleCheckEvent {
  /** 规则ID */
  ruleId: string;
  /** 规则类型 */
  ruleType: RuleType;
  /** 校验结果 */
  passed: boolean;
  /** 实际值 */
  actualValue?: number | string;
  /** 期望值 */
  expectedValue?: number | string;
}

// ==================== 导出所有类型 ====================

export type {
  BaseNode,
  StepNode,
  ResultAnchorNode,
  ParameterNode,
  RuleNode,
  OutputNode,
  Edge,
  WorkbenchFlowGraph,
  NodeExplanation,
  ExplanationSection,
  ParameterReference,
  RuleReference,
  ImpactAnalysis,
  PanelContext,
  ColorSemantics,
  FlowGenerationOptions,
  NodeFilter,
  NodeClickEvent,
  NodeExpandEvent,
  RuleCheckEvent
};