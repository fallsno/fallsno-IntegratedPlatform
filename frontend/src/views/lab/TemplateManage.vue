<template>
  <div class="template-manage">
    <div class="page-header">
      <h2>模板管理</h2>
      <el-button type="primary" @click="handleNewTemplate">新建模板</el-button>
    </div>

    <el-table :data="templates" border>
      <el-table-column prop="name" label="模板名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button link type="primary" @click="editTemplate(row)">编辑配置</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showEditDialog" title="编辑模板" width="800px">
      <el-form :model="editingTemplate" label-width="100px">
        <el-form-item label="模板名称" required>
          <el-input v-model="editingTemplate.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input type="textarea" v-model="editingTemplate.description" />
        </el-form-item>
        
        <el-divider>阶段配置</el-divider>
        <el-tabs v-model="activeStageTab">
          <el-tab-pane v-for="(sections, stage) in editingTemplate.config.stages" :key="stage" :label="stageMap[stage]" :name="stage">
            <div v-for="(sec, idx) in sections" :key="idx" class="sec-edit-card">
              <div class="sec-header">
                <el-input v-model="sec.name" size="small" style="width: 200px" />
                <el-button type="danger" link size="small" @click="removeSec(stage, idx)">删除章节</el-button>
              </div>
              <div class="field-list">
                <div v-for="(field, fIdx) in sec.fields" :key="fIdx" class="field-row">
                  <el-input v-model="field.label" size="small" placeholder="字段标签" style="width: 150px" />
                  <el-select v-model="field.type" size="small" style="width: 120px">
                    <el-option label="文本输入" value="text" />
                    <el-option label="数值" value="number" />
                    <el-option label="日期时间" value="date" />
                    <el-option label="动态表格" value="table" />
                  </el-select>
                  <div v-if="field.type === 'table'" class="table-cols-config">
                    <el-tag v-for="(col, cIdx) in field.columns" :key="cIdx" closable @close="field.columns.splice(cIdx, 1)">
                      {{ col }}
                    </el-tag>
                    <el-button type="primary" link size="small" @click="addTableCol(field)">+ 添加列</el-button>
                  </div>
                  <el-button type="danger" link @click="removeField(sec, fIdx)"><el-icon><Delete /></el-icon></el-button>
                </div>
                <el-button type="primary" link size="small" @click="addField(sec)">+ 添加表单项</el-button>
              </div>
            </div>
            <el-button type="primary" plain size="small" @click="addSec(stage)" style="margin-top: 10px">+ 添加新章节 (如：传感器配置)</el-button>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate">保存模板</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from '@/api/lab'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'

const templates = ref([])
const showEditDialog = ref(false)
const activeStageTab = ref('Preparation')
const editingTemplate = ref({
  name: '',
  description: '',
  config: {
    stages: {
      Preparation: [],
      Execution: [],
      Review: []
    }
  }
})

const stageMap = {
  Preparation: '准备阶段',
  Execution: '执行阶段',
  Review: '回顾阶段'
}

const fetchTemplates = async () => {
  const res = await axios.get('/templates')
  templates.value = res.data
}

const handleNewTemplate = () => {
  editingTemplate.value = {
    name: '',
    description: '',
    config: {
      stages: {
        Preparation: [
          { name: '1. 试验基本信息', fields: [
            { label: '试验人员', type: 'text' },
            { label: '环境参数', type: 'table', columns: ['环境温度(℃)', '环境湿度(%RH)'] },
            { label: '设备信息', type: 'table', columns: ['产品名称', '代号', '编号'] }
          ] },
          { name: '2. 物料/仪器准备', fields: [{ label: '物料清单', type: 'table', columns: ['名称', '型号/规格', '量程', '分辨率', '证明材料'] }] },
          { name: '3. 初始状态记录', fields: [{ label: '状态描述/读数', type: 'table', columns: ['测点/位置', '初始状态', '初始读数', '单位'] }] }
        ],
        Execution: [
          { name: '试验执行数据记录', fields: [{ label: '关键数据记录表', type: 'table', columns: ['测量点/关键点', '测量仪器', '测量数据', '单位', '实验现象描述', '证明材料'] }] }
        ],
        Review: [
          { name: '试验回顾与总结', fields: [
            { label: '试验结果分析', type: 'text' },
            { label: '结论判定', type: 'text' }
          ] }
        ]
      }
    }
  }
  showEditDialog.value = true
}

const editTemplate = (row) => {
  editingTemplate.value = JSON.parse(JSON.stringify(row))
  showEditDialog.value = true
}

const addSec = (stage) => {
  editingTemplate.value.config.stages[stage].push({ name: '新章节', fields: [] })
}

const removeSec = (stage, idx) => {
  editingTemplate.value.config.stages[stage].splice(idx, 1)
}

const addField = (sec) => {
  sec.fields.push({ label: '新项名称', type: 'text' })
}

const addTableCol = (field) => {
  ElMessageBox.prompt('请输入列名', '添加表格列').then(({ value }) => {
    if (!field.columns) field.columns = []
    field.columns.push(value)
  })
}

const removeField = (sec, idx) => {
  sec.fields.splice(idx, 1)
}

const saveTemplate = async () => {
  try {
    if (editingTemplate.value.id) {
      await axios.put(`/templates/${editingTemplate.value.id}`, editingTemplate.value)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/templates', editingTemplate.value)
      ElMessage.success('保存成功')
    }
    showEditDialog.value = false
    fetchTemplates()
  } catch (err) {
    ElMessage.error('保存失败')
  }
}

onMounted(fetchTemplates)
</script>

<style scoped>
.template-manage { background: #fff; padding: 20px; border-radius: 8px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.sec-edit-card { border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
.sec-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.field-row { display: flex; gap: 10px; margin-bottom: 8px; align-items: center; }
</style>
