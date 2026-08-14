<template>
  <div class="knowledge-base">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>📚 专家知识库管理</h2>
          <el-radio-group v-model="activeTab" size="large">
            <el-radio-button value="rules">设计规则库</el-radio-button>
            <el-radio-button value="materials">材料属性库</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 1. 设计规则管理 -->
      <div v-if="activeTab === 'rules'">
        <div class="toolbar">
          <el-button type="primary" @click="openRuleDialog('add')">新增规则</el-button>
          <el-input v-model="ruleSearch" placeholder="搜索规则名称..." style="width: 300px; margin-left: 20px" clearable />
        </div>
        <el-table :data="filteredRules" border stripe style="margin-top: 20px">
          <el-table-column prop="name" label="规则名称" width="180" />
          <el-table-column prop="constraint_expr" label="约束表达式" width="250">
            <template #default="{ row }">
              <code class="expr-code">{{ row.constraint_expr }}</code>
            </template>
          </el-table-column>
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }">
              <el-tag :type="row.severity === 'error' ? 'danger' : 'warning'">{{ row.severity === 'error' ? '错误' : '警告' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="提示信息" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" @change="toggleRule(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button type="primary" link @click="openRuleDialog('edit', row)">编辑</el-button>
              <el-button type="danger" link @click="deleteRule(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 2. 材料库管理 -->
      <div v-if="activeTab === 'materials'">
        <div class="toolbar">
          <el-button type="primary" @click="openMaterialDialog('add')">新增材料</el-button>
        </div>
        <el-table :data="materials" border stripe style="margin-top: 20px">
          <el-table-column prop="name" label="材料名称" width="150" />
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column label="物理性能 (JSON)">
            <template #default="{ row }">
              <pre class="props-pre">{{ JSON.stringify(row.properties, null, 2) }}</pre>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button type="primary" link @click="openMaterialDialog('edit', row)">编辑</el-button>
              <el-button type="danger" link @click="deleteMaterial(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 规则编辑弹窗 -->
    <el-dialog v-model="showRuleDialog" :title="ruleFormTitle" width="500px">
      <el-form :model="ruleForm" label-width="100px">
        <el-form-item label="规则名称" required>
          <el-input v-model="ruleForm.name" placeholder="例如: 滚圈宽度上限" />
        </el-form-item>
        <el-form-item label="约束表达式" required>
          <el-input v-model="ruleForm.constraint_expr" placeholder="例如: value <= 200" />
          <div class="form-tip">使用 'value' 代表当前参数值</div>
        </el-form-item>
        <el-form-item label="严重程度">
          <el-select v-model="ruleForm.severity" style="width: 100%">
            <el-option label="警告" value="warning" />
            <el-option label="错误" value="error" />
          </el-select>
        </el-form-item>
        <el-form-item label="提示信息" required>
          <el-input type="textarea" v-model="ruleForm.message" placeholder="校验失败时显示的文字" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRuleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref('rules')
const rules = ref([])
const materials = ref([])
const ruleSearch = ref('')

// 规则相关
const showRuleDialog = ref(false)
const ruleForm = ref({ name: '', constraint_expr: '', severity: 'warning', message: '', is_active: true })
const ruleFormTitle = ref('新增规则')
const editingRuleId = ref(null)

const fetchRules = async () => {
  const res = await axios.get('/knowledge/rules')
  rules.value = res.data
}

const fetchMaterials = async () => {
  const res = await axios.get('/knowledge/materials')
  materials.value = res.data
}

const filteredRules = computed(() => {
  if (!ruleSearch.value) return rules.value
  return rules.value.filter(r => r.name.includes(ruleSearch.value))
})

const openRuleDialog = (mode, row = null) => {
  if (mode === 'edit') {
    ruleForm.value = { ...row }
    editingRuleId.value = row.id
    ruleFormTitle.value = '编辑规则'
  } else {
    ruleForm.value = { name: '', constraint_expr: '', severity: 'warning', message: '', is_active: true }
    editingRuleId.value = null
    ruleFormTitle.value = '新增规则'
  }
  showRuleDialog.value = true
}

const saveRule = async () => {
  try {
    if (editingRuleId.value) {
      await axios.put(`/knowledge/rules/${editingRuleId.value}`, ruleForm.value)
    } else {
      await axios.post('/knowledge/rules', ruleForm.value)
    }
    ElMessage.success('保存成功')
    showRuleDialog.value = false
    fetchRules()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const toggleRule = async (row) => {
  await axios.put(`/knowledge/rules/${row.id}`, row)
  ElMessage.success('状态已更新')
}

const deleteRule = (id) => {
  ElMessageBox.confirm('确定删除该规则吗?', '提示').then(async () => {
    await axios.delete(`/knowledge/rules/${id}`)
    fetchRules()
  })
}

onMounted(() => {
  fetchRules()
  fetchMaterials()
})
</script>

<style scoped>
.knowledge-base { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.toolbar { margin-bottom: 20px; display: flex; align-items: center; }
.expr-code { background: #f4f4f5; padding: 2px 5px; border-radius: 4px; font-family: monospace; color: #409eff; }
.props-pre { margin: 0; font-size: 12px; color: #666; }
.form-tip { font-size: 12px; color: #909399; margin-top: 5px; }
</style>
