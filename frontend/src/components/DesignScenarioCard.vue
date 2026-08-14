<template>
  <el-card class="scenario-card" shadow="never">
    <template #header>
      <div class="scenario-card__header">
        <div>
          <div class="scenario-card__title">{{ title }}</div>
          <div class="scenario-card__subtitle">{{ sceneCode }}</div>
        </div>
        <el-tag :type="highlightValue ? 'success' : 'info'" effect="plain">
          {{ rows.length }} 项结果
        </el-tag>
      </div>
    </template>

    <div v-if="highlightRow" class="scenario-card__highlight">
      <div class="highlight-label">{{ highlightRow.result_name }}</div>
      <div class="highlight-value">
        {{ highlightRow.result_value }}
        <span>{{ highlightRow.unit_code || '' }}</span>
      </div>
    </div>

    <div class="scenario-card__rows">
      <div v-for="item in rows" :key="item.result_code" class="scenario-row">
        <span class="scenario-row__name">{{ item.result_name }}</span>
        <span class="scenario-row__value">
          {{ item.result_value }} {{ item.unit_code || '' }}
        </span>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  sceneCode: {
    type: String,
    default: ''
  },
  rows: {
    type: Array,
    default: () => []
  }
})

const highlightKeywords = ['推荐电机功率', '电机所需功率', '托轮摩擦力矩', '总重']

const highlightRow = computed(() => props.rows.find((item) => highlightKeywords.includes(item.result_name)) || props.rows[0] || null)
const highlightValue = computed(() => highlightRow.value?.result_value || '')
</script>

<style scoped>
.scenario-card {
  border-radius: 18px;
  border: 1px solid #dbeafe;
  background:
    linear-gradient(180deg, rgba(239, 246, 255, 0.95), rgba(248, 250, 252, 0.92)),
    #fff;
}

.scenario-card__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.scenario-card__title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.scenario-card__subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
}

.scenario-card__highlight {
  padding: 14px 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(34, 197, 94, 0.08));
  border: 1px solid rgba(14, 165, 233, 0.18);
}

.highlight-label {
  font-size: 12px;
  color: #0369a1;
}

.highlight-value {
  margin-top: 6px;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.highlight-value span {
  margin-left: 4px;
  font-size: 13px;
  color: #64748b;
}

.scenario-card__rows {
  margin-top: 14px;
  display: grid;
  gap: 10px;
}

.scenario-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px dashed #dbeafe;
}

.scenario-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.scenario-row__name {
  color: #475569;
}

.scenario-row__value {
  font-weight: 700;
  color: #0f172a;
}
</style>
