<template>
  <div class="design-guidance">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <div>
            <h3>设计指导驾驶舱</h3>
            <p>集中查看规则命中、推荐动作和处理结果。</p>
          </div>
          <el-button @click="loadData">刷新</el-button>
        </div>
      </template>

      <div class="summary-cards">
        <el-card v-for="card in summary.cards" :key="card.key" shadow="hover" class="summary-card">
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value">{{ card.value }}</div>
        </el-card>
      </div>

      <el-table :data="hits" stripe v-loading="loading">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="action-panel">
              <div class="action-toolbar">
                <el-button
                  v-if="!row.action_count"
                  size="small"
                  type="primary"
                  @click="handleGenerateActions(row)"
                >
                  生成推荐动作
                </el-button>
              </div>

              <el-table :data="row.actions" size="small" empty-text="暂无推荐动作">
                <el-table-column prop="action_label" label="推荐动作" min-width="220" />
                <el-table-column label="状态" width="120">
                  <template #default="{ row: action }">
                    <el-tag :type="getGuidanceActionStatusMeta(action.status).type">
                      {{ getGuidanceActionStatusMeta(action.status).label }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="处理备注" min-width="240">
                  <template #default="{ row: action }">
                    <el-input v-model="action.result_note" placeholder="填写处理结果或备注" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="240">
                  <template #default="{ row: action }">
                    <el-space wrap>
                      <el-button size="small" @click="handleUpdateAction(action, 'in_progress')">
                        开始处理
                      </el-button>
                      <el-button size="small" type="success" @click="handleUpdateAction(action, 'resolved')">
                        标记完成
                      </el-button>
                      <el-button size="small" type="info" @click="handleUpdateAction(action, 'dismissed')">
                        忽略
                      </el-button>
                    </el-space>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="source_type" label="来源" width="140" />
        <el-table-column prop="target_type" label="对象类型" width="140" />
        <el-table-column prop="severity" label="风险级别" width="120" />
        <el-table-column prop="message" label="命中信息" min-width="220" />
        <el-table-column prop="action_count" label="动作数" width="100" />
        <el-table-column prop="open_action_count" label="待执行动作" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import {
  fetchGuidanceSummary,
  generateGuidanceActions,
  getGuidanceActionStatusMeta,
  normalizeGuidanceSummary,
  updateGuidanceAction
} from '@/api/designPlatform.js'

const loading = ref(false)
const hits = ref([])
const summary = ref(normalizeGuidanceSummary())

const loadData = async () => {
  loading.value = true
  try {
    const payload = await fetchGuidanceSummary()
    summary.value = payload.summary
    hits.value = payload.hits
  } catch (error) {
    console.error(error)
    ElMessage.error('加载设计指导数据失败')
  } finally {
    loading.value = false
  }
}

const handleGenerateActions = async (hit) => {
  try {
    await generateGuidanceActions(hit.id)
    ElMessage.success('推荐动作已生成')
    await loadData()
  } catch (error) {
    console.error(error)
    ElMessage.error('生成推荐动作失败')
  }
}

const handleUpdateAction = async (action, status) => {
  try {
    await updateGuidanceAction(action.id, {
      status,
      resultNote: action.result_note || ''
    })
    ElMessage.success('动作状态已更新')
    await loadData()
  } catch (error) {
    console.error(error)
    ElMessage.error('更新动作失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.design-guidance {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header p {
  margin-top: 6px;
  color: #64748b;
}

.action-panel {
  padding: 8px 12px 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.action-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.summary-card {
  min-height: 110px;
}

.metric-label {
  color: #64748b;
  font-size: 14px;
}

.metric-value {
  margin-top: 12px;
  font-size: 30px;
  font-weight: 600;
  color: #0f172a;
}
</style>
