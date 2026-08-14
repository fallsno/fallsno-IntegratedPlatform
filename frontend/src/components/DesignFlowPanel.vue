<template>
  <div class="design-flow-panel">
    <div style="margin-bottom: 10px; display: flex; gap: 10px">
      <el-button type="primary" size="small" @click="showFlowDialog = true">
        <el-icon><Plus /></el-icon>新建流程
      </el-button>
      <el-button v-if="currentFlow" type="success" size="small" @click="generateGraph">
        <el-icon><Share /></el-icon>生成流程图
      </el-button>
    </div>

    <el-row :gutter="15">
      <el-col v-for="flow in flows" :key="flow.id" :span="24">
        <el-card class="flow-card" :class="{ active: currentFlow?.id === flow.id }" shadow="hover">
          <template #header>
            <div class="flow-header">
              <span @click="toggleFlow(flow)">{{ flow.flow_name }}</span>
              <el-button type="danger" link @click="deleteFlow(flow.id)">删除</el-button>
            </div>
          </template>
          <div v-if="currentFlow?.id === flow.id">
            <el-tree
              :data="buildStepTree(flow.steps)"
              :props="{ children: 'children', label: 'label' }"
              node-key="id"
              default-expand-all
            >
              <template #default="{ node, data }">
                <div class="step-node">
                  <div class="step-header">
                    <strong>{{ data.step_order }}</strong> {{ data.design_point || '未命名设计点' }}
                    <el-button link type="primary" size="small" @click="editStep(data)">编辑</el-button>
                    <el-button link type="danger" size="small" @click="deleteStep(data.id)">删除</el-button>
                  </div>
                  <div class="step-detail" v-if="data.design_point">
                    <div><span>公式：</span>{{ data.formula?.name || data.custom_formula || '无' }}</div>
                    <div><span>输入参数：</span>
                      <el-tag v-for="p in data.parameters.filter(p => p.param_type === 'input')" :key="p.id" size="small">
                        {{ p.param_name }} = {{ p.param_value }} {{ p.param_unit }}
                      </el-tag>
                    </div>
                    <div><span>输出参数：</span>
                      <el-tag v-for="p in data.parameters.filter(p => p.param_type === 'output')" :key="p.id" size="small" type="success">
                        {{ p.param_name }} = {{ p.param_value }} {{ p.param_unit }}
                      </el-tag>
                    </div>
                    <div><span>说明：</span>{{ data.note }}</div>
                  </div>
                </div>
              </template>
            </el-tree>
            <el-button style="margin-top: 10px" size="small" @click="addStep(flow)">新增步骤</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="graphDialogVisible" title="设计流程图" width="800px">
      <div ref="graphContainer" style="height: 500px; border: 1px solid #eee"></div>
    </el-dialog>

    <el-dialog v-model="stepDialogVisible" title="编辑步骤" width="600px">
      <el-form :model="stepForm" label-width="100px">
        <el-form-item label="步骤编号">
          <el-input v-model="stepForm.step_order" placeholder="例如 1, 1.1" />
        </el-form-item>
        <el-form-item label="设计点">
          <el-input v-model="stepForm.design_point" placeholder="例如 滚筒直径" />
        </el-form-item>
        <el-form-item label="公式引用">
          <el-select v-model="stepForm.formula_id" placeholder="选择公式库公式" clearable filterable>
            <el-option v-for="f in formulas" :key="f.id" :label="f.name" :value="f.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="自定义公式">
          <el-input v-model="stepForm.custom_formula" placeholder="若未选公式库可手写表达式" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="stepForm.note" type="textarea" />
        </el-form-item>
        <el-divider>参数设置</el-divider>
        <el-form-item label="输入参数">
          <div v-for="(p, idx) in inputParams" :key="idx" style="margin-bottom:10px; border: 1px solid #eee; padding: 10px; border-radius: 4px">
            <el-row :gutter="10">
              <el-col :span="6">
                <el-input v-model="p.param_name" placeholder="参数名" />
              </el-col>
              <el-col :span="6">
                <el-select v-model="p.param_type" placeholder="类型" size="small">
                  <el-option label="直接输入" value="input" />
                  <el-option label="引用结果" value="result_ref" />
                </el-select>
              </el-col>
              <el-col :span="10">
                <el-input v-if="p.param_type === 'input'" v-model="p.param_value" placeholder="值" />
                <el-select v-else v-model="p.source_step_id" placeholder="选择来源步骤" clearable>
                  <el-option 
                    v-for="step in currentFlow?.steps.filter(s => s.id !== editingStepId)" 
                    :key="step.id" 
                    :label="`${step.step_order} ${step.design_point}`" 
                    :value="step.id" 
                  />
                </el-select>
              </el-col>
              <el-col :span="2">
                <el-button link type="danger" @click="removeParam('input', idx)">删除</el-button>
              </el-col>
            </el-row>
            <el-row :gutter="10" style="margin-top: 5px">
              <el-col :span="6">
                <el-input v-model="p.param_unit" placeholder="单位" size="small" />
              </el-col>
            </el-row>
          </div>
          <el-button size="small" @click="addParam('input')">添加输入</el-button>
        </el-form-item>
        <el-form-item label="输出参数">
          <div v-for="(p, idx) in outputParams" :key="idx" style="margin-bottom:5px">
            <el-input v-model="p.param_name" placeholder="参数名" style="width:100px" />
            <el-input v-model="p.param_value" placeholder="值" style="width:120px" />
            <el-input v-model="p.param_unit" placeholder="单位" style="width:80px" />
            <el-button link @click="removeParam('output', idx)">删除</el-button>
          </div>
          <el-button size="small" @click="addParam('output')">添加输出</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stepDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveStep">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
const echarts = window.echarts

const props = defineProps(['partId'])

const flows = ref([])
const currentFlow = ref(null)
const formulas = ref([])
const stepDialogVisible = ref(false)
const graphDialogVisible = ref(false)
const graphContainer = ref(null)
const stepForm = ref({
  id: null,
  step_order: '',
  design_point: '',
  formula_id: null,
  custom_formula: '',
  note: '',
  parameters: []
})
let editingFlowId = null
let editingStepId = null

const inputParams = computed(() => stepForm.value.parameters.filter(p => p.param_type === 'input'))
const outputParams = computed(() => stepForm.value.parameters.filter(p => p.param_type === 'output'))

const fetchFlows = async () => {
  try {
    const res = await axios.get(`/design-flows/part/${props.partId}`)
    flows.value = res.data
  } catch (e) {
    ElMessage.error('获取流程失败')
  }
}

const fetchFormulas = async () => {
  try {
    const res = await axios.get('/formulas/')
    formulas.value = res.data
  } catch (e) {
    ElMessage.error('获取公式列表失败')
  }
}

const toggleFlow = (flow) => {
  currentFlow.value = flow
}

const deleteFlow = (id) => {
  ElMessageBox.confirm('确定删除该流程及其所有步骤吗？', '警告', { type: 'warning' })
    .then(async () => {
      await axios.delete(`/design-flows/${id}`)
      ElMessage.success('删除成功')
      if (currentFlow.value?.id === id) currentFlow.value = null
      fetchFlows()
    })
}

const buildStepTree = (steps) => {
  const map = {}
  const roots = []
  const sortedSteps = [...steps].sort((a, b) => a.step_order.localeCompare(b.step_order, undefined, { numeric: true }))
  sortedSteps.forEach(step => {
    map[step.step_order] = { ...step, label: `${step.step_order} ${step.design_point}`, children: [] }
  })
  sortedSteps.forEach(step => {
    const parts = step.step_order.split('.')
    if (parts.length > 1) {
      const parentOrder = parts.slice(0, -1).join('.')
      if (map[parentOrder]) {
        map[parentOrder].children.push(map[step.step_order])
      } else {
        roots.push(map[step.step_order])
      }
    } else {
      roots.push(map[step.step_order])
    }
  })
  return roots
}

const addStep = (flow) => {
  editingFlowId = flow.id
  editingStepId = null
  stepForm.value = {
    id: null,
    step_order: '',
    design_point: '',
    formula_id: null,
    custom_formula: '',
    note: '',
    parameters: []
  }
  stepDialogVisible.value = true
}

const editStep = (step) => {
  editingFlowId = step.flow_id
  editingStepId = step.id
  stepForm.value = {
    ...step,
    parameters: step.parameters || []
  }
  stepDialogVisible.value = true
}

const addParam = (type) => {
  stepForm.value.parameters.push({
    param_name: '',
    param_value: '',
    param_unit: '',
    param_type: type
  })
}

const removeParam = (type, idx) => {
  const params = stepForm.value.parameters.filter(p => p.param_type === type)
  const otherParams = stepForm.value.parameters.filter(p => p.param_type !== type)
  params.splice(idx, 1)
  stepForm.value.parameters = [...otherParams, ...params]
}

const saveStep = async () => {
  const stepData = {
    step_order: stepForm.value.step_order,
    design_point: stepForm.value.design_point,
    formula_id: stepForm.value.formula_id,
    custom_formula: stepForm.value.custom_formula,
    note: stepForm.value.note,
    parameters: stepForm.value.parameters
  }

  try {
    if (editingStepId) {
      await axios.put(`/design-flows/steps/${editingStepId}`, stepData)
      ElMessage.success('更新成功')
    } else {
      await axios.post(`/design-flows/${editingFlowId}/steps`, stepData)
      ElMessage.success('添加成功')
    }
    stepDialogVisible.value = false
    fetchFlows()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const deleteStep = (id) => {
  ElMessageBox.confirm('确定删除该步骤吗？', '警告', { type: 'warning' })
    .then(async () => {
      await axios.delete(`/design-flows/steps/${id}`)
      ElMessage.success('删除成功')
      fetchFlows()
    })
}

const generateGraph = async () => {
  if (!currentFlow.value) return
  try {
    const res = await axios.get(`/design-flows/${currentFlow.value.id}/graph`)
    const { nodes, edges } = res.data
    graphDialogVisible.value = true
    // 在对话框渲染后初始化图表
    setTimeout(() => {
      const container = graphContainer.value
      if (container) {
        const chart = echarts.init(container)
        const option = {
          title: { text: '设计流程图' },
          tooltip: {},
          series: [{
            type: 'graph',
            layout: 'force',
            symbolSize: 50,
            roam: true,
            label: { show: true, position: 'right' },
            edgeSymbol: ['circle', 'arrow'],
            edgeSymbolSize: [4, 10],
            edgeLabel: { fontSize: 12 },
            data: nodes.map(n => ({ name: n.id, label: n.label })),
            links: edges.map(e => ({ source: e.source, target: e.target, label: e.label }))
          }]
        }
        chart.setOption(option)
      }
    }, 100)
  } catch (e) {
    ElMessage.error('生成流程图失败')
  }
}

onMounted(() => {
  fetchFlows()
  fetchFormulas()
})
</script>

<style scoped>
.flow-card { margin-bottom: 15px; }
.flow-header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
.step-node { padding: 5px 0; }
.step-header { font-weight: 500; }
.step-detail { margin-left: 20px; font-size: 0.9em; color: #606266; }
</style>