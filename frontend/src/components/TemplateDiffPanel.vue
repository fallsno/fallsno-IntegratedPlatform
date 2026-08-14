<template>
  <el-card shadow="never" class="template-diff-panel">
    <template #header>
      <div class="panel-header">
        <span>模板差异摘要</span>
        <el-tag type="info">{{ stats.summary || '请选择模板对比' }}</el-tag>
      </div>
    </template>
    <el-row :gutter="12">
      <el-col :span="8">
        <el-statistic title="新增流程" :value="stats.added_flows || 0" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="更新步骤" :value="stats.updated_steps || 0" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="影响参数行" :value="stats.affected_rows || 0" />
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup>
defineProps({
  stats: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
</style>
