<template>
  <section class="formula-template-center">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <div>
            <div class="page-title">公式模板中心</div>
            <div class="page-subtitle">维护通用物理公式模板，供型号工作台只读执行复用。</div>
          </div>
          <div class="page-actions">
            <el-button :loading="loading" @click="loadTemplates">刷新</el-button>
            <el-button type="primary" :loading="creating" @click="handleCreateTemplate">新建模板</el-button>
          </div>
        </div>
      </template>

      <el-table :data="templates" v-loading="loading" stripe height="calc(100vh - 220px)">
        <el-table-column prop="template_code" label="模板编码" width="180" />
        <el-table-column prop="template_name" label="模板名称" min-width="220" />
        <el-table-column prop="description" label="说明" min-width="260" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditor(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { createFormulaTemplate, fetchFormulaTemplates } from '@/api/drumDesign'

const router = useRouter()
const loading = ref(false)
const creating = ref(false)
const templates = ref([])

const loadTemplates = async () => {
  loading.value = true
  try {
    templates.value = await fetchFormulaTemplates()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载公式模板失败')
  } finally {
    loading.value = false
  }
}

const openEditor = (row) => {
  router.push(`/formula-templates/${row.id}/edit`)
}

const handleCreateTemplate = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入模板名称', '新建公式模板', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：再生系列公式模板'
    })
    creating.value = true
    const normalizedName = String(value || '').trim()
    const templateCode = `TPL_${Date.now()}`
    const created = await createFormulaTemplate({
      template_code: templateCode,
      template_name: normalizedName || templateCode,
      description: '待补充',
      is_active: true
    })
    ElMessage.success('模板已创建')
    router.push(`/formula-templates/${created.id}/edit`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '创建模板失败')
    }
  } finally {
    creating.value = false
  }
}

onMounted(loadTemplates)
</script>

<style scoped>
.formula-template-center {
  padding: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.page-subtitle {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
}

.page-actions {
  display: flex;
  gap: 8px;
}
</style>
