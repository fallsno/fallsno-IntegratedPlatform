<template>
  <el-card class="compare-panel" shadow="never">
    <template #header>
      <div class="panel-header">
        <div>
          <div class="panel-title">方案对比</div>
          <div class="panel-subtitle">同型号不同方案的结果差异</div>
        </div>
        <el-tag type="success" effect="plain">{{ caseNames.length }} 个方案</el-tag>
      </div>
    </template>

    <div class="case-chips">
      <el-tag v-for="name in caseNames" :key="name" effect="plain">{{ name }}</el-tag>
    </div>

    <el-empty v-if="!rows.length" description="保存两个以上方案后在这里查看差异" />
    <el-table v-else :data="rows" size="small" stripe>
      <el-table-column prop="result_name" label="结果项" min-width="160" fixed="left" />
      <el-table-column
        v-for="caseName in caseNames"
        :key="caseName"
        :label="caseName"
        min-width="120"
      >
        <template #default="{ row }">{{ row.values?.[caseName] || '-' }}</template>
      </el-table-column>
      <el-table-column prop="delta" label="差值" width="100">
        <template #default="{ row }">
          <el-tag type="warning" effect="plain">{{ row.delta || '-' }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rows: {
    type: Array,
    default: () => []
  },
  cases: {
    type: Array,
    default: () => []
  }
})

const caseNames = computed(() => {
  if (props.cases.length) {
    return props.cases.map((item) => item.caseName)
  }
  const names = new Set()
  for (const row of props.rows) {
    Object.keys(row.values || {}).forEach((key) => names.add(key))
  }
  return [...names]
})
</script>

<style scoped>
.compare-panel {
  margin-top: 16px;
  border-radius: 18px;
  border: 1px solid #e2e8f0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.panel-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
}

.case-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
</style>
