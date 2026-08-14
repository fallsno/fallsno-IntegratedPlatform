<template>
  <div class="family-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button @click="router.push('/product-types')" style="margin-right: 10px">
              <el-icon><ArrowLeft /></el-icon>返回类型列表
            </el-button>
            <span class="title">产品型号列表 {{ currentTypeName ? `(${currentTypeName})` : '' }}</span>
          </div>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>新增型号
          </el-button>
        </div>
      </template>

      <el-table :data="families" v-loading="loading" stripe>
        <el-table-column prop="family_code" label="主代号" width="150" />
        <el-table-column prop="family_name" label="名称" width="180" />
        <el-table-column label="产品类型" width="150">
          <template #default="{ row }">
            {{ getProductTypeName(row.product_type_id) }}
          </template>
        </el-table-column>
        <el-table-column label="旧代号" width="250">
          <template #default="{ row }">
            <el-tag v-for="alias in row.aliases" :key="alias.id" size="small" style="margin-right: 5px">
              {{ alias.alias_code }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类(旧)" width="150" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" link @click="goToVersions(row.id)">版本管理</el-button>
            <el-button type="warning" link @click="goToMatrix(row.id)">矩阵维护</el-button>
            <el-button type="success" link @click="editFamily(row)">编辑</el-button>
            <el-button type="danger" link @click="deleteFamily(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑型号对话框 -->
    <el-dialog v-model="showAddDialog" :title="editingFamily ? '编辑型号' : '新增型号'" width="500px">
      <el-form :model="familyForm" label-width="100px">
        <el-form-item label="产品类型">
          <el-select v-model="familyForm.product_type_id" placeholder="请选择产品类型" clearable>
            <el-option v-for="pt in productTypes" :key="pt.id" :label="pt.type_name" :value="pt.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="主代号" required>
          <el-input v-model="familyForm.family_code" placeholder="例如 AT240R.0" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="familyForm.family_name" placeholder="例如 干燥滚筒" />
        </el-form-item>
        <el-form-item label="分类(旧)">
          <el-input v-model="familyForm.category" placeholder="例如 干燥滚筒" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="familyForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="旧代号（多个用逗号分隔）">
          <el-input v-model="aliasInput" placeholder="例如 GT240GF1.0, GTRS200B.0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFamily">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const props = defineProps({
  typeId: {
    type: [String, Number],
    default: null
  }
})

const families = ref([])
const productTypes = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const editingFamily = ref(null)
const familyForm = ref({ 
  family_code: '', 
  family_name: '', 
  category: '', 
  description: '', 
  product_type_id: null 
})
const aliasInput = ref('')

const currentTypeName = computed(() => {
  if (!props.typeId) return ''
  const pt = productTypes.value.find(p => p.id == props.typeId)
  return pt ? pt.type_name : ''
})

const fetchProductTypes = async () => {
  try {
    const res = await axios.get('/product-types/')
    productTypes.value = res.data
  } catch (e) {
    console.error('获取产品类型失败', e)
  }
}

const getProductTypeName = (typeId) => {
  if (!typeId) return ''
  const pt = productTypes.value.find(p => p.id == typeId)
  return pt ? pt.type_name : ''
}

const fetchFamilies = async () => {
  loading.value = true
  try {
    const params = {}
    if (props.typeId) {
      params.product_type_id = props.typeId
    }
    const res = await axios.get('/families/', { params })
    families.value = res.data
  } catch (e) {
    ElMessage.error('获取型号列表失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  editingFamily.value = null
  familyForm.value = { 
    family_code: '', 
    family_name: '', 
    category: '', 
    description: '', 
    product_type_id: props.typeId ? parseInt(props.typeId) : null 
  }
  aliasInput.value = ''
  showAddDialog.value = true
}

const saveFamily = async () => {
  if (!familyForm.value.family_code?.trim()) {
    ElMessage.warning('主代号不能为空')
    return
  }
  if (!familyForm.value.family_name?.trim()) {
    ElMessage.warning('名称不能为空')
    return
  }
  try {
    if (editingFamily.value) {
      await axios.put(`/families/${editingFamily.value.id}`, familyForm.value)
      ElMessage.success('更新成功')
    } else {
      const res = await axios.post('/families/', familyForm.value)
      const familyId = res.data.id
      if (aliasInput.value.trim()) {
        const aliases = aliasInput.value.split(',').map(s => s.trim()).filter(s => s)
        for (const code of aliases) {
          await axios.post(`/families/${familyId}/aliases?alias_code=${encodeURIComponent(code)}&alias_type=old`)
        }
      }
      ElMessage.success('创建成功')
    }
    showAddDialog.value = false
    editingFamily.value = null
    familyForm.value = { family_code: '', family_name: '', category: '', description: '', product_type_id: null }
    aliasInput.value = ''
    fetchFamilies()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const editFamily = (row) => {
  editingFamily.value = row
  familyForm.value = { 
    family_code: row.family_code,
    family_name: row.family_name,
    category: row.category || '',
    description: row.description || '',
    product_type_id: row.product_type_id || null
  }
  aliasInput.value = row.aliases ? row.aliases.map(a => a.alias_code).join(', ') : ''
  showAddDialog.value = true
}

const deleteFamily = async (id) => {
  await ElMessageBox.confirm('确定删除该型号及其所有版本和部件吗？', '警告', { type: 'warning' })
  try {
    await axios.delete(`/families/${id}`)
    ElMessage.success('删除成功')
    fetchFamilies()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

const goToVersions = (familyId) => {
  router.push({ name: 'Versions', params: { familyId } })
}

const goToMatrix = (familyId) => {
  router.push({ name: 'ModelParameterMatrix', params: { familyId } })
}

onMounted(async () => {
  await fetchProductTypes()
  fetchFamilies()
})
</script>

<style scoped>
.family-list { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-left { display: flex; align-items: center; }
.title { font-size: 16px; font-weight: bold; }
</style>
