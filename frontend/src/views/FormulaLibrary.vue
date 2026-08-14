<template>
  <div class="formula-library">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>公式库管理</span>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>新增公式
          </el-button>
        </div>
      </template>

      <el-row :gutter="10" style="margin-bottom: 10px">
        <el-col :span="6">
          <el-select v-model="filterCategory" placeholder="筛选分类" clearable @change="fetchFormulas">
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-col>
      </el-row>

      <el-table :data="formulas" v-loading="loading" stripe>
        <el-table-column prop="name" label="公式名称" width="180" />
        <el-table-column label="标准关系" min-width="260">
          <template #default="{ row }">
            <code>{{ row.canonical_expression || row.expression }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column label="变量">
          <template #default="{ row }">
            <el-tag v-for="(desc, varName) in row.variables" :key="varName" size="small">
              {{ varName }}: {{ desc }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="可求目标" width="220">
          <template #default="{ row }">
            <el-tag
              v-for="target in getSolveTargetKeys(row)"
              :key="target"
              size="small"
              type="success"
              style="margin-right: 4px"
            >
              {{ target }}
            </el-tag>
            <span v-if="getSolveTargetKeys(row).length === 0" style="color: #909399">旧模式</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" link @click="editFormula(row)">编辑</el-button>
            <el-button type="danger" link @click="deleteFormula(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDialog" :title="editing ? '编辑公式' : '新增公式'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="公式名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="表达式" required>
          <el-input v-model="form.expression" placeholder="例如 a + b * c" />
        </el-form-item>
        <el-form-item label="标准关系">
          <el-input v-model="form.canonical_expression" placeholder="例如 P = 1.732 * U * I * cosΦ * η" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="例如 几何计算" />
        </el-form-item>
        <el-form-item label="变量定义">
          <div v-for="(desc, varName) in form.variables" :key="varName" style="margin-bottom:5px">
            <el-input v-model="form.variables[varName]" placeholder="描述" style="width:200px" />
            <span style="margin:0 5px">变量名：</span>
            <el-input :model-value="varName" placeholder="变量名" style="width:100px" disabled />
            <el-button link type="danger" @click="deleteVariable(varName)">删除</el-button>
          </div>
          <el-button size="small" @click="addVariable">添加变量</el-button>
        </el-form-item>
        <el-form-item label="可求目标">
          <div style="width: 100%">
            <div
              v-for="(target, index) in solveTargets"
              :key="index"
              style="margin-bottom: 12px; padding: 12px; border: 1px solid #e4e7ed; border-radius: 6px"
            >
              <el-row :gutter="8" style="margin-bottom: 8px">
                <el-col :span="6">
                  <el-input v-model="target.key" placeholder="目标参数" />
                </el-col>
                <el-col :span="16">
                  <el-input v-model="target.expression" placeholder="求解表达式，例如 P / (1.732 * U * cosΦ * η)" />
                </el-col>
                <el-col :span="2">
                  <el-button link type="danger" @click="removeSolveTarget(index)">删除</el-button>
                </el-col>
              </el-row>
              <el-row :gutter="8">
                <el-col :span="12">
                  <el-input v-model="target.required_variables" placeholder="必填变量，逗号分隔" />
                </el-col>
                <el-col :span="12">
                  <el-input v-model="target.description" placeholder="说明，例如 已知功率求电流" />
                </el-col>
              </el-row>
            </div>
            <el-button size="small" @click="addSolveTarget">添加目标参数</el-button>
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFormula">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const formulas = ref([])
const categories = ref([])
const filterCategory = ref('')
const loading = ref(false)
const showDialog = ref(false)
const editing = ref(false)
const form = ref({
  name: '',
  expression: '',
  category: '',
  variables: {},
  description: '',
  canonical_expression: '',
  solve_targets: {}
})
const solveTargets = ref([])
let editingId = null

const emptyForm = () => ({
  name: '',
  expression: '',
  category: '',
  variables: {},
  description: '',
  canonical_expression: '',
  solve_targets: {}
})

const normalizeSolveTargetsForEdit = (formula) => (
  Object.entries(formula?.solve_targets || {}).map(([key, config]) => ({
    key,
    expression: config?.expression || '',
    required_variables: Array.isArray(config?.required_variables) ? config.required_variables.join(', ') : '',
    description: config?.description || ''
  }))
)

const buildSolveTargetsPayload = () => {
  const payload = {}
  solveTargets.value.forEach((target) => {
    const key = target.key?.trim()
    const expression = target.expression?.trim()
    if (!key || !expression) return
    payload[key] = {
      expression,
      required_variables: target.required_variables
        .split(/[,，]/)
        .map(item => item.trim())
        .filter(Boolean),
      description: target.description?.trim() || ''
    }
  })
  return payload
}

const fetchFormulas = async () => {
  loading.value = true
  try {
    const params = filterCategory.value ? { category: filterCategory.value } : {}
    const res = await axios.get('/formulas/', { params })
    formulas.value = res.data
    const cats = new Set(res.data.map(f => f.category).filter(Boolean))
    categories.value = Array.from(cats)
  } catch (e) {
    ElMessage.error('获取公式失败')
  } finally {
    loading.value = false
  }
}

const getSolveTargetKeys = (formula) => Object.keys(formula?.solve_targets || {})

const addVariable = () => {
  const newVar = prompt('输入变量名（例如 a, b, D）')
  if (newVar && !form.value.variables[newVar]) {
    form.value.variables[newVar] = ''
  }
}

const deleteVariable = (varName) => {
  delete form.value.variables[varName]
}

const addSolveTarget = () => {
  solveTargets.value.push({
    key: '',
    expression: '',
    required_variables: '',
    description: ''
  })
}

const removeSolveTarget = (index) => {
  solveTargets.value.splice(index, 1)
}

const saveFormula = async () => {
  if (!form.value.name || !form.value.expression) {
    ElMessage.warning('名称和表达式不能为空')
    return
  }
  try {
    const payload = {
      ...form.value,
      canonical_expression: form.value.canonical_expression?.trim() || null,
      solve_targets: buildSolveTargetsPayload()
    }
    if (editing.value) {
      await axios.put(`/formulas/${editingId}`, payload)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/formulas/', payload)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    editing.value = false
    form.value = emptyForm()
    solveTargets.value = []
    editingId = null
    fetchFormulas()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const editFormula = (row) => {
  editing.value = true
  editingId = row.id
  form.value = {
    ...emptyForm(),
    ...row,
    variables: { ...(row.variables || {}) }
  }
  solveTargets.value = normalizeSolveTargetsForEdit(row)
  showDialog.value = true
}

const openCreateDialog = () => {
  editing.value = false
  editingId = null
  form.value = emptyForm()
  solveTargets.value = []
  showDialog.value = true
}

const deleteFormula = async (id) => {
  await ElMessageBox.confirm('确定删除该公式吗？', '警告', { type: 'warning' })
  await axios.delete(`/formulas/${id}`)
  ElMessage.success('删除成功')
  fetchFormulas()
}

onMounted(fetchFormulas)
</script>
