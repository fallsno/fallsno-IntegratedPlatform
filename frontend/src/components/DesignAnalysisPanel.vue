<template>
  <el-card class="analysis-panel" shadow="never">
    <template #header>
      <div class="panel-header">
        <div>
          <div class="panel-title">参数分析</div>
          <div class="panel-subtitle">首期先做单参数敏感性分析</div>
        </div>
        <el-tag type="warning" effect="plain">分析</el-tag>
      </div>
    </template>

    <el-form label-position="top" class="analysis-form">
      <el-form-item label="分析参数">
        <el-select v-model="form.targetParameter" placeholder="选择参数">
          <el-option
            v-for="item in parameterOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="结果项">
        <el-select v-model="form.resultName" placeholder="选择结果项">
          <el-option label="推荐电机功率" value="推荐电机功率" />
          <el-option label="电机所需功率" value="电机所需功率" />
          <el-option label="托轮摩擦力矩" value="托轮摩擦力矩" />
        </el-select>
      </el-form-item>
      <div class="analysis-grid">
        <el-form-item label="分析档位">
          <el-input-number v-model="form.steps" :min="3" :max="9" />
        </el-form-item>
        <el-form-item label="浮动比例">
          <el-input-number v-model="form.deltaRatio" :min="0.05" :max="0.5" :step="0.05" />
        </el-form-item>
      </div>
      <el-button type="primary" :loading="loading" @click="emitAnalysis">开始分析</el-button>
    </el-form>

    <div class="trend-panel">
      <div class="trend-title">{{ analysisTitle }}</div>
      <el-empty v-if="!seriesData.labels?.length" description="执行分析后在这里查看趋势" />
      <div v-else class="trend-bars">
        <div v-for="(label, index) in seriesData.labels" :key="`${label}-${index}`" class="trend-row">
          <span class="trend-row__label">{{ label }}</span>
          <div class="trend-row__bar">
            <div class="trend-row__fill" :style="{ width: `${getBarWidth(index)}%` }"></div>
          </div>
          <span class="trend-row__value">{{ seriesData.values[index] }}</span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  parameterOptions: {
    type: Array,
    default: () => []
  },
  seriesData: {
    type: Object,
    default: () => ({ labels: [], values: [], resultName: '', targetParameter: '' })
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['run-analysis'])

const form = reactive({
  targetParameter: '',
  resultName: '推荐电机功率',
  steps: 5,
  deltaRatio: 0.2
})

watch(
  () => props.parameterOptions,
  (options) => {
    if (!form.targetParameter && options.length) {
      form.targetParameter = options[0].value
    }
  },
  { immediate: true }
)

const maxValue = computed(() => Math.max(...(props.seriesData.values || [0]), 0))
const analysisTitle = computed(() => {
  if (!props.seriesData.resultName) return '趋势预览'
  return `${props.seriesData.targetParameter || '参数'} -> ${props.seriesData.resultName}`
})

const getBarWidth = (index) => {
  const current = Number(props.seriesData.values?.[index] || 0)
  const base = maxValue.value || 1
  return Math.max((current / base) * 100, 12)
}

const emitAnalysis = () => {
  emit('run-analysis', {
    targetParameter: form.targetParameter,
    resultName: form.resultName,
    steps: form.steps,
    deltaRatio: form.deltaRatio
  })
}
</script>

<style scoped>
.analysis-panel {
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

.analysis-form {
  display: grid;
  gap: 4px;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.trend-panel {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid #e2e8f0;
}

.trend-title {
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}

.trend-bars {
  display: grid;
  gap: 10px;
}

.trend-row {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr) 72px;
  gap: 10px;
  align-items: center;
}

.trend-row__label {
  font-size: 12px;
  color: #475569;
}

.trend-row__bar {
  height: 10px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
}

.trend-row__fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #0ea5e9, #22c55e);
}

.trend-row__value {
  text-align: right;
  font-weight: 700;
  color: #0f172a;
}
</style>
