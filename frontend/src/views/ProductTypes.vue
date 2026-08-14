<template>
  <div class="product-types">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>产品类型管理</span>
            <el-input
              v-model="searchQuery"
              placeholder="搜索名称、代号、机型..."
              prefix-icon="Search"
              clearable
              style="width: 250px; margin-left: 20px;"
            />
            <el-select v-model="filterCategory" placeholder="类型筛选" clearable style="width: 150px; margin-left: 10px;">
              <el-option label="热系统" value="热系统" />
              <el-option label="机械设计" value="机械设计" />
              <el-option label="其余" value="其余" />
            </el-select>
          </div>
          <div class="header-right">
            <el-button type="warning" @click="handleUndo" :disabled="!canUndo">
              <el-icon><RefreshLeft /></el-icon>撤回 (Ctrl+Z)
            </el-button>
            <el-button type="success" @click="handleBatchImport">
              <el-icon><Upload /></el-icon>批量导入部件
            </el-button>
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>新增类型
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredTypes" v-loading="loading" stripe @row-dblclick="goToComponents">
        <el-table-column prop="type_code" label="编码" width="120" />
        <el-table-column prop="model_code" label="代号" width="150" />
        <el-table-column prop="type_name" label="名称" width="150" />
        <el-table-column prop="english_name" label="英文" width="150" />
        <el-table-column prop="category" label="类型" width="100" />
        <el-table-column prop="machine_model" label="机型" width="100" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="publisher" label="发布人" width="100" />
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="400">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="goToComponents(row)">查看部件</el-button>
            <el-button type="success" link @click.stop="cloneType(row)">克隆</el-button>
            <el-button type="warning" link @click.stop="openDeriveDialog(row)">推演</el-button>
            <el-button type="primary" link @click.stop="editType(row)">编辑</el-button>
            <el-button type="danger" link @click.stop="deleteType(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDialog" :title="editing ? '编辑产品类型' : '新建产品类型'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="编码" required>
              <el-input v-model="form.type_code" placeholder="例如 2100742400" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="代号" required>
              <el-input v-model="form.model_code" placeholder="例如 AT120B.ZT" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="名称" required>
              <el-input v-model="form.type_name" placeholder="例如 干燥滚筒" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="英文">
              <el-input v-model="form.english_name" placeholder="例如 Dryer Drum" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="类型">
              <el-select v-model="form.category" placeholder="选择类型" style="width: 100%">
                <el-option label="热系统" value="热系统" />
                <el-option label="机械设计" value="机械设计" />
                <el-option label="其余" value="其余" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="版本">
              <el-input v-model="form.version" placeholder="例如 13" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="机型" prop="machine_model">
              <el-autocomplete
                v-model="form.machine_model"
                :fetch-suggestions="querySearchModel"
                placeholder="请输入机型数字 (如: 1500)"
                style="width: 100%"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发布人">
              <el-input v-model="form.publisher" placeholder="例如 林旭峰" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveType">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入部件对话框 -->
    <el-dialog v-model="showImportDialog" title="Excel 批量导入部件建模" width="700px">
      <el-form label-width="100px">
        <el-form-item label="部件名称" required>
          <el-input v-model="importForm.componentName" placeholder="例如: 筒体" />
        </el-form-item>
        <el-form-item label="Excel 数据" required>
          <el-input
            v-model="importForm.tableData"
            type="textarea"
            :rows="12"
            placeholder="请直接从 Excel 复制表格（含表头）并粘贴到此处。
格式要求：
第一列：系列 (如 原生1500型)
第二列：机型代号 (如 GT120，支持 GT320/AT320)
后续列：参数名称 (如 直径, 周长, 筒体壁厚...)"
          />
        </el-form-item>
        <div style="margin-left: 100px; color: #909399; font-size: 12px; line-height: 1.5">
          提示：系统将自动识别表头中的参数名，并根据第一二列匹配对应的产品型号，自动在每个型号下建立该部件及设计参数。
        </div>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmBatchImport" :loading="importing">开始导入</el-button>
      </template>
    </el-dialog>

    <!-- 机型推演对话框 -->
    <el-dialog v-model="showDeriveDialog" title="机型推演" width="500px">
      <el-form :model="deriveForm" label-width="120px">
        <el-alert title="将克隆该型号并应用缩放系数修改所有数值型参数" type="info" show-icon style="margin-bottom: 20px" :closable="false" />
        <el-form-item label="源机型">
          <span>{{ currentDeriveSource?.type_name || '' }} ({{ currentDeriveSource?.model_code || '' }})</span>
        </el-form-item>
        <el-form-item label="目标代号" required>
          <el-input v-model="deriveForm.target_code" placeholder="例如 AT160B.ZT" />
        </el-form-item>
        <el-form-item label="目标名称" required>
          <el-input v-model="deriveForm.target_name" placeholder="例如 1600型干燥滚筒" />
        </el-form-item>
        <el-form-item label="缩放系数" required>
          <el-input-number v-model="deriveForm.scale_factor" :step="0.1" :min="0.1" :max="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDeriveDialog = false">取消</el-button>
          <el-button type="primary" @click="submitDerive" :loading="deriving">确认推演</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, RefreshLeft, Upload, Search } from '@element-plus/icons-vue'

const router = useRouter()
const types = ref([])
const loading = ref(false)
const showDialog = ref(false)
const editing = ref(false)
const searchQuery = ref('')
const filterCategory = ref('')

const filteredTypes = computed(() => {
  let list = types.value
  
  // 1. 类型筛选
  if (filterCategory.value) {
    list = list.filter(item => item.category === filterCategory.value)
  }
  
  // 2. 搜索框过滤 (名称、代号、机型)
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.trim().toLowerCase()
    list = list.filter(item => 
      (item.type_name && item.type_name.toLowerCase().includes(query)) ||
      (item.model_code && item.model_code.toLowerCase().includes(query)) ||
      (item.machine_model && String(item.machine_model).toLowerCase().includes(query)) ||
      (item.type_code && item.type_code.toLowerCase().includes(query))
    )
  }
  
  return list
})

const form = ref({ 
  type_code: '', 
  model_code: '',
  type_name: '', 
  english_name: '',
  category: '',
  version: '',
  publisher: '',
  description: '' 
})
let editingId = null

const historyStack = ref([])

const saveToHistory = () => {
  const snapshot = JSON.parse(JSON.stringify(types.value))
  historyStack.value.push(snapshot)
  if (historyStack.value.length > 20) {
    historyStack.value.shift()
  }
}

const canUndo = computed(() => historyStack.value.length > 0)

const handleUndo = async () => {
  if (!canUndo.value) return
  
  try {
    await axios.post('/product-types/undo-last')
    await fetchTypes()
    historyStack.value.pop()
    ElMessage.success('撤回成功')
  } catch (e) {
    console.error('撤回失败:', e)
    ElMessage.error('撤回失败或没有可撤回的操作')
  }
}

const handleKeyDown = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
    e.preventDefault()
    handleUndo()
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString()
}

const fetchTypes = async () => {
  loading.value = true
  try {
    const res = await axios.get('/product-types/')
    types.value = res.data
  } catch (e) {
    ElMessage.error('获取产品类型失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  saveToHistory()
  editing.value = false
  form.value = { 
    type_code: '', 
    model_code: '',
    type_name: '', 
    english_name: '',
    category: '',
    version: '',
    machine_model: '',
    publisher: '',
    description: '' 
  }
  showDialog.value = true
}

const saveType = async () => {
  if (!form.value.type_code.trim() || !form.value.type_name.trim()) {
    ElMessage.warning('编码和名称不能为空')
    return
  }
  try {
    if (editing.value) {
      await axios.put(`/product-types/${editingId}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/product-types/', form.value)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    fetchTypes()
  } catch (e) {
    ElMessage.error('保存失败')
    historyStack.value.pop()
  }
}

const editType = (row) => {
  saveToHistory()
  editing.value = true
  editingId = row.id
  form.value = { ...row }
  showDialog.value = true
}

const cloneType = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要克隆产品类型"${row.type_name}"吗？克隆后会复制所有部件、设计流程和公式。`,
      '确认克隆',
      { confirmButtonText: '确定克隆', cancelButtonText: '取消', type: 'warning' }
    )
    saveToHistory()
    const res = await axios.post(`/product-types/${row.id}/clone`)
    ElMessage.success('克隆成功')
    fetchTypes()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('克隆失败')
      historyStack.value.pop()
    }
  }
}

const deleteType = (id) => {
  ElMessageBox.confirm('确定删除该类型及其下所有组件吗？', '警告', { type: 'warning' })
    .then(async () => {
      saveToHistory()
      await axios.delete(`/product-types/${id}`)
      ElMessage.success('删除成功，可点击撤回恢复')
      fetchTypes()
    })
}

// 批量导入相关
const showImportDialog = ref(false)
const importing = ref(false)
const importForm = ref({
  componentName: '',
  tableData: ''
})

const handleBatchImport = () => {
  importForm.value = {
    componentName: '',
    tableData: ''
  }
  showImportDialog.value = true
}

const confirmBatchImport = async () => {
  if (!importForm.value.componentName.trim()) {
    ElMessage.warning('请输入部件名称')
    return
  }
  if (!importForm.value.tableData.trim()) {
    ElMessage.warning('请粘贴 Excel 数据')
    return
  }
  
  importing.value = true
  try {
    const res = await axios.post('/product-types/batch-import-components', importForm.value)
    ElMessage.success(`导入成功，共在 ${res.data.created_count} 个型号下创建了部件`)
    showImportDialog.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导入失败，请检查数据格式')
  } finally {
    importing.value = false
  }
}

const goToComponents = (row) => {
  router.push({ name: 'ProductComponents', params: { typeId: row.id } })
}

// 机型推演逻辑
const showDeriveDialog = ref(false)
const deriving = ref(false)
const currentDeriveSource = ref(null)
const deriveForm = ref({
  target_code: '',
  target_name: '',
  scale_factor: 1.2
})

const openDeriveDialog = (row) => {
  currentDeriveSource.value = row
  deriveForm.value = {
    target_code: row.model_code ? row.model_code + '_New' : '',
    target_name: row.type_name ? row.type_name + ' 推演版' : '',
    scale_factor: 1.2
  }
  showDeriveDialog.value = true
}

const submitDerive = async () => {
  if (!deriveForm.value.target_code || !deriveForm.value.target_name) {
    ElMessage.warning('请填写目标代号和名称')
    return
  }
  deriving.value = true
  try {
    await axios.post(`/product-types/${currentDeriveSource.value.id}/derive`, deriveForm.value)
    ElMessage.success('机型推演成功')
    showDeriveDialog.value = false
    fetchTypes()
  } catch (err) {
    console.error('推演失败:', err)
    ElMessage.error('推演失败，请检查网络')
  } finally {
    deriving.value = false
  }
}

const goToFamilies = (row) => {
  router.push({ name: 'Families', params: { typeId: row.id } })
}

const querySearchModel = (queryString, cb) => {
  const models = [
    { value: '1500' },
    { value: '2000' },
    { value: '3000' },
    { value: '4000' },
    { value: '5000' }
  ]
  const results = queryString
    ? models.filter(item => item.value.toLowerCase().includes(queryString.toLowerCase()))
    : models
  cb(results)
}

onMounted(() => {
  fetchTypes()
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-left {
  display: flex;
  align-items: center;
}
.header-right {
  display: flex;
  gap: 10px;
}
.product-types {
  cursor: pointer;
}
</style>
