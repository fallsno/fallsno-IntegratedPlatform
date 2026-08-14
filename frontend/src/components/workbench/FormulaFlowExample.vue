<template>
  <div class="formula-flow-example">
    <div class="example-header">
      <h2>公式工作台设计链路 - 组件使用示例</h2>
      <p>展示如何使用新的垂直布局组件和流程图组件</p>
    </div>
    
    <!-- 示例1：垂直流程容器 -->
    <div class="example-section">
      <h3>1. 垂直流程容器 (VerticalFlowContainer)</h3>
      <p class="section-description">用于展示三层垂直布局的设计链路</p>
      
      <VerticalFlowContainer
        :input-items="exampleInputItems"
        :calculation-items="exampleCalculationItems"
        :output-items="exampleOutputItems"
      >
        <!-- 自定义输入层内容 -->
        <template #input-layer>
          <FlowCard
            v-for="item in exampleInputItems"
            :key="item.id"
            :title="item.title"
            :content="item.content"
            type="input"
            :icon="item.icon"
          />
        </template>
        
        <!-- 自定义计算层内容 -->
        <template #calculation-layer>
          <FlowCard
            v-for="item in exampleCalculationItems"
            :key="item.id"
            :title="item.title"
            :content="item.content"
            type="calculation"
            :icon="item.icon"
          />
        </template>
        
        <!-- 自定义输出层内容 -->
        <template #output-layer>
          <FlowCard
            v-for="item in exampleOutputItems"
            :key="item.id"
            :title="item.title"
            :content="item.content"
            type="output"
            :icon="item.icon"
          />
        </template>
      </VerticalFlowContainer>
    </div>
    
    <!-- 示例2：流程图组件 -->
    <div class="example-section">
      <h3>2. 公式流程图 (FormulaFlowChart)</h3>
      <p class="section-description">使用ECharts实现的交互式设计链路图</p>
      
      <div class="chart-controls">
        <div class="control-group">
          <label>选择节点类型：</label>
          <select v-model="selectedNodeType" @change="filterNodes">
            <option value="all">全部节点</option>
            <option value="input">输入条件</option>
            <option value="calculation">计算节点</option>
            <option value="output">输出结果</option>
            <option value="parameter">关键参数</option>
            <option value="rule">校验规则</option>
          </select>
        </div>
        
        <div class="control-group">
          <label>缩放级别：</label>
          <input 
            type="range" 
            min="0.5" 
            max="2" 
            step="0.1" 
            v-model="zoomLevel"
            @input="updateZoom"
          >
          <span class="zoom-value">{{ zoomLevel.toFixed(1) }}x</span>
        </div>
      </div>
      
      <FormulaFlowChart
        :nodes="filteredNodes"
        :edges="exampleEdges"
        :selected-node-id="selectedNodeId"
        :zoom="zoomLevel"
        @node-click="handleChartNodeClick"
      />
      
      <div v-if="selectedNodeInfo" class="selected-node-info">
        <h4>选中节点信息</h4>
        <div class="info-content">
          <div class="info-item">
            <span class="info-label">名称：</span>
            <span class="info-value">{{ selectedNodeInfo.title }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">类型：</span>
            <span class="info-value">{{ getNodeTypeName(selectedNodeInfo.nodeType) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">描述：</span>
            <span class="info-value">{{ selectedNodeInfo.content }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 示例3：流程卡片组件 -->
    <div class="example-section">
      <h3>3. 流程卡片组件 (FlowCard)</h3>
      <p class="section-description">可独立使用的卡片组件，支持多种状态和交互</p>
      
      <div class="card-demo-grid">
        <FlowCard
          title="输入参数"
          content="用户设定的基础设计参数"
          type="input"
          icon="📥"
          :selected="selectedCardId === 'input1'"
          @click="selectCard('input1')"
        />
        
        <FlowCard
          title="计算过程"
          content="根据公式进行计算和转换"
          type="calculation"
          icon="⚙️"
          :selected="selectedCardId === 'calc1'"
          @click="selectCard('calc1')"
        />
        
        <FlowCard
          title="输出结果"
          content="最终的设计计算结果"
          type="output"
          icon="📤"
          :selected="selectedCardId === 'output1'"
          @click="selectCard('output1')"
        />
        
        <FlowCard
          title="关键参数"
          content="影响设计的关键变量"
          type="parameter"
          icon="🔑"
          :selected="selectedCardId === 'param1'"
          @click="selectCard('param1')"
        />
        
        <FlowCard
          title="校验规则"
          content="设计规范的校验条件"
          type="rule"
          icon="✅"
          :selected="selectedCardId === 'rule1'"
          @click="selectCard('rule1')"
        />
        
        <FlowCard
          title="禁用状态"
          content="此卡片已被禁用"
          type="calculation"
          icon="🚫"
          :disabled="true"
        />
      </div>
    </div>
    
    <!-- 使用说明 -->
    <div class="usage-instructions">
      <h3>使用说明</h3>
      <div class="instructions-content">
        <div class="instruction-item">
          <h4>安装与引入</h4>
          <pre><code>// 在Vue组件中引入
import VerticalFlowContainer from '@/components/workbench/VerticalFlowContainer.vue'
import FlowCard from '@/components/workbench/FlowCard.vue'
import FormulaFlowChart from '@/components/workbench/FormulaFlowChart.vue'</code></pre>
        </div>
        
        <div class="instruction-item">
          <h4>数据格式</h4>
          <pre><code>// 节点数据格式
{
  id: 'node1',
  title: '节点标题',
  content: '节点描述',
  nodeType: 'input', // input, calculation, output, parameter, rule
  icon: '📥'
}

// 边数据格式
{
  source: 'node1',
  target: 'node2',
  label: '计算得出'
}</code></pre>
        </div>
        
        <div class="instruction-item">
          <h4>样式引入</h4>
          <pre><code>// 在组件的style标签中引入
@import '@/assets/styles/workbench-formula-flow.css';</code></pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VerticalFlowContainer from './VerticalFlowContainer.vue'
import FlowCard from './FlowCard.vue'
import FormulaFlowChart from './FormulaFlowChart.vue'

// 示例数据
const exampleInputItems = ref([
  { id: 'input1', title: '基础参数', content: '用户设定的基础设计参数', icon: '📥' },
  { id: 'input2', title: '边界条件', content: '设计约束和限制条件', icon: '⚖️' },
  { id: 'input3', title: '查值依据', content: '参考标准和规范依据', icon: '📚' }
])

const exampleCalculationItems = ref([
  { id: 'calc1', title: '电机参数计算', content: '根据负载计算电机功率', icon: '⚙️' },
  { id: 'calc2', title: '筒体参数计算', content: '计算筒体尺寸和重量', icon: '📏' },
  { id: 'calc3', title: '传动系统计算', content: '计算传动比和扭矩', icon: '🔧' }
])

const exampleOutputItems = ref([
  { id: 'output1', title: '功率输出', content: '最终计算得到的功率值', icon: '📤' },
  { id: 'output2', title: '转速输出', content: '计算得到的滚筒转速', icon: '🌀' },
  { id: 'output3', title: '设计建议', content: '基于计算的设计优化建议', icon: '💡' }
])

// 流程图示例数据 - 更新为包含layer字段和状态
const exampleNodes = ref([
  { 
    id: 'node1', 
    title: '输入参数', 
    content: '基础设计参数', 
    nodeType: 'input', 
    layer: 'input',
    status: 'normal',
    x: 200, 
    y: 100 
  },
  { 
    id: 'node2', 
    title: '负载计算', 
    content: '计算负载大小', 
    nodeType: 'calculation', 
    layer: 'calculation',
    status: 'normal',
    x: 400, 
    y: 100 
  },
  { 
    id: 'node3', 
    title: '功率计算', 
    content: '计算所需功率', 
    nodeType: 'calculation', 
    layer: 'calculation',
    status: 'warning',
    x: 600, 
    y: 100 
  },
  { 
    id: 'node4', 
    title: '输出功率', 
    content: '最终功率值', 
    nodeType: 'output', 
    layer: 'output',
    status: 'success',
    x: 800, 
    y: 100 
  },
  { 
    id: 'node5', 
    title: '安全系数', 
    content: '安全系数参数', 
    nodeType: 'parameter', 
    layer: 'input',
    status: 'normal',
    x: 300, 
    y: 200 
  },
  { 
    id: 'node6', 
    title: '功率校验', 
    content: '校验功率范围', 
    nodeType: 'rule', 
    layer: 'calculation',
    status: 'error',
    x: 500, 
    y: 200 
  },
  { 
    id: 'node7', 
    title: '反馈调节', 
    content: '根据输出调整输入', 
    nodeType: 'calculation', 
    layer: 'calculation',
    status: 'normal',
    x: 700, 
    y: 200 
  }
])

const exampleEdges = ref([
  { 
    source: 'node1', 
    target: 'node2', 
    label: '输入参数',
    type: 'physical_connection'
  },
  { 
    source: 'node2', 
    target: 'node3', 
    label: '计算流转',
    type: 'calculation_flow'
  },
  { 
    source: 'node3', 
    target: 'node4', 
    label: '物理承接',
    type: 'physical_connection'
  },
  { 
    source: 'node5', 
    target: 'node2', 
    label: '参数输入',
    type: 'calculation_flow'
  },
  { 
    source: 'node6', 
    target: 'node3', 
    label: '规则校验',
    type: 'rule_check'
  },
  { 
    source: 'node4', 
    target: 'node7', 
    label: '反馈回环',
    type: 'feedback_loop'
  },
  { 
    source: 'node7', 
    target: 'node1', 
    label: '错误路径',
    type: 'error_path'
  }
])

// 状态管理
const selectedNodeType = ref('all')
const selectedNodeId = ref('')
const selectedNodeInfo = ref(null)
const selectedCardId = ref('')
const zoomLevel = ref(1.0)

// 计算属性
const filteredNodes = computed(() => {
  if (selectedNodeType.value === 'all') {
    return exampleNodes.value
  }
  return exampleNodes.value.filter(node => node.nodeType === selectedNodeType.value)
})

// 方法
const filterNodes = () => {
  selectedNodeId.value = ''
  selectedNodeInfo.value = null
}

const handleChartNodeClick = (node) => {
  selectedNodeId.value = node.id
  selectedNodeInfo.value = node
}

const selectCard = (cardId) => {
  selectedCardId.value = cardId
}

const updateZoom = () => {
  // 缩放更新逻辑
}

const getNodeTypeName = (type) => {
  const typeMap = {
    input: '输入条件',
    calculation: '计算节点',
    output: '输出结果',
    parameter: '关键参数',
    rule: '校验规则'
  }
  return typeMap[type] || type
}
</script>

<style scoped>
@import '@/assets/styles/workbench-formula-flow.css';

.formula-flow-example {
  padding: 24px;
  background: #f8fafc;
  border-radius: 16px;
}

.example-header {
  text-align: center;
  margin-bottom: 32px;
}

.example-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 12px;
}

.example-header p {
  font-size: 16px;
  color: #64748b;
  max-width: 800px;
  margin: 0 auto;
}

.example-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
}

.example-section h3 {
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 8px;
}

.section-description {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 20px;
}

.chart-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f1f5f9;
  border-radius: 8px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-group label {
  font-size: 14px;
  font-weight: 500;
  color: #475569;
}

.control-group select,
.control-group input[type="range"] {
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: white;
  font-size: 14px;
}

.zoom-value {
  font-size: 14px;
  font-weight: 500;
  color: #3b82f6;
  min-width: 40px;
}

.selected-node-info {
  margin-top: 20px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.selected-node-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 16px;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.info-label {
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  min-width: 60px;
}

.info-value {
  font-size: 14px;
  color: #334155;
  flex: 1;
}

.card-demo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.usage-instructions {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-top: 32px;
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
}

.usage-instructions h3 {
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 20px;
}

.instructions-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.instruction-item h4 {
  font-size: 16px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 12px;
}

.instruction-item pre {
  background: #f1f5f9;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
}

.instruction-item code {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: #334155;
}

@media (max-width: 768px) {
  .formula-flow-example {
    padding: 16px;
  }
  
  .example-header h2 {
    font-size: 24px;
  }
  
  .card-demo-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-controls {
    flex-direction: column;
    gap: 12px;
  }
}
</style>