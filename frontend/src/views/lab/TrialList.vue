<template>
  <div class="trial-list">
    <div class="page-header">
      <h2>试验记录</h2>
      <div class="header-ops">
        <el-button type="warning" plain @click="$router.push('/lab/materials')">
          <el-icon><Management /></el-icon> 物料库管理
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">新建试验</el-button>
      </div>
    </div>

    <el-table :data="trials" style="width: 100%" v-loading="loading">
      <el-table-column prop="name" label="试验名称" min-width="200" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="current_stage" label="当前阶段" width="150" />
      <el-table-column prop="creator" label="记录人" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push(`/lab/trial/${row.id}`)">进入试验</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreateDialog" title="发起新试验" width="450px">
      <el-form :model="createForm" label-width="100px" style="padding: 10px">
        <el-form-item label="试验名称" required>
          <el-input v-model="createForm.name" placeholder="例如：某型号滚筒可靠性验证" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="createForm.creator" placeholder="姓名" />
        </el-form-item>
        <div class="create-hint">
          <el-icon><InfoFilled /></el-icon>
          系统将自动为您配置完整的准备、执行和回顾工作区。
        </div>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">立即开始试验</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from '@/api/lab'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Management, InfoFilled } from '@element-plus/icons-vue'

const router = useRouter()
const trials = ref([])
const templates = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const createForm = ref({ name: '', creator: '' })

const fetchTrials = async () => {
  loading.value = true
  try {
    const res = await axios.get('/trials')
    trials.value = res.data
  } catch (err) {
    ElMessage.error('获取试验列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  const name = createForm.value.name?.trim()
  if (!name) {
    return ElMessage.warning('请填写试验名称')
  }
  try {
    const res = await axios.post('/trials', { ...createForm.value, name })
    ElMessage.success('试验工作区已就绪')
    router.push(`/lab/trial/${res.data.id}`)
  } catch (err) {
    ElMessage.error('创建失败')
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除试验记录 "${row.name}" 吗？此操作不可撤销，且会删除所有关联数据。`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await axios.delete(`/trials/${row.id}`)
      ElMessage.success('删除成功')
      fetchTrials()
    } catch (err) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const statusType = (s) => {
  if (s === 'Finished') return 'success'
  if (s === 'Ongoing') return 'primary'
  return 'info'
}

const formatDate = (d) => new Date(d).toLocaleString()

onMounted(() => {
  fetchTrials()
})
</script>

<style scoped>
.trial-list { background: #fff; padding: 20px; border-radius: 8px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
h2 { margin: 0; }
.create-hint { margin-top: 15px; font-size: 13px; color: #64748b; background: #f8fafc; padding: 10px; border-radius: 4px; display: flex; align-items: center; gap: 8px; }
</style>
