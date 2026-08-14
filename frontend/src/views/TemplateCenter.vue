<template>
  <div class="template-center">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <div>
            <h3>模板中心</h3>
            <p>面向系列模板、型号模板与同步差异的统一入口。</p>
          </div>
          <div class="page-actions">
            <el-button @click="$router.push('/guidance')">查看设计指导</el-button>
            <el-button @click="showSync = true">同步弹窗</el-button>
            <el-button type="primary" @click="loadTemplates">刷新模板</el-button>
          </div>
        </div>
      </template>

      <el-table 
        :data="templateTree" 
        stripe 
        v-loading="loading" 
        row-key="id"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        default-expand-all
      >
        <el-table-column prop="template_name" label="模板名称" min-width="220" />
        <el-table-column prop="template_code" label="模板编码" min-width="180" />
        <el-table-column prop="template_type" label="模板类型" width="140">
          <template #default="{ row }">
            <el-tag :type="getTemplateTypeTag(row.template_type)" size="small">
              {{ row.template_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version_no" label="版本" width="100" />
        <el-table-column prop="status" label="状态" width="120" />
      </el-table>
    </el-card>

    <TemplateDiffPanel :stats="currentDiff" />
    <TemplateSyncDialog v-model="showSync" @preview="handlePreview" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import TemplateDiffPanel from '@/components/TemplateDiffPanel.vue'
import TemplateSyncDialog from '@/components/TemplateSyncDialog.vue'
import { fetchTemplateDiffPreview, fetchTemplateTree } from '@/api/designPlatform.js'

const loading = ref(false)
const showSync = ref(false)
const templateTree = ref([])
const currentDiff = ref({})

const loadTemplates = async () => {
  loading.value = true
  try {
    templateTree.value = await fetchTemplateTree()
  } catch (error) {
    console.error(error)
    ElMessage.error('加载模板台账失败')
  } finally {
    loading.value = false
  }
}

const getTemplateTypeTag = (type) => {
  if (type === 'base' || type === 'system') return 'danger'
  if (type === 'series') return 'warning'
  if (type === 'model') return 'success'
  return 'info'
}

const handlePreview = async ({ sourceComponentId, targetComponentId }) => {
  try {
    currentDiff.value = await fetchTemplateDiffPreview(sourceComponentId, targetComponentId)
    showSync.value = false
  } catch (error) {
    console.error(error)
    ElMessage.error('获取模板差异失败')
  }
}

onMounted(loadTemplates)
</script>

<style scoped>
.template-center {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-header p {
  margin-top: 6px;
  color: #64748b;
}

.page-actions {
  display: flex;
  gap: 12px;
}
</style>
