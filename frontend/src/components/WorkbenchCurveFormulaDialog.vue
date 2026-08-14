<template>
  <el-dialog
    :model-value="modelValue"
    title="曲线查值"
    width="860px"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="curve-dialog">
      <div class="curve-dialog__form">
        <el-form label-width="96px">
          <el-form-item label="附录表">
            <el-select v-model="lookupName" filterable placeholder="请选择曲线附录" @change="handleLookupChange">
              <el-option
                v-for="item in lookupItems"
                :key="item.id"
                :label="item.lookup_name"
                :value="item.lookup_name"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="输入参数">
            <el-select v-model="inputName" filterable allow-create default-first-option placeholder="请选择参数">
              <el-option
                v-for="item in parameterOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="曲线系列">
            <el-select v-model="seriesKey" filterable placeholder="请选择系列">
              <el-option
                v-for="item in seriesOptions"
                :key="item.series_key"
                :label="item.series_key"
                :value="item.series_key"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="查值方向">
            <el-radio-group v-model="direction">
              <el-radio-button label="X2Y">X查Y</el-radio-button>
              <el-radio-button label="Y2X">Y查X</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="查值方式">
            <el-select v-model="lookupMode">
              <el-option label="LINEAR" value="LINEAR" />
            </el-select>
          </el-form-item>
          <el-form-item label="前置系数">
            <el-input v-model="multiplier" placeholder="例如 142，可留空" />
          </el-form-item>
        </el-form>

        <el-alert v-if="errorMessage" :title="errorMessage" type="warning" :closable="false" show-icon />

        <div class="curve-dialog__preview">
          <div class="curve-dialog__preview-label">公式预览</div>
          <code>{{ formulaPreview || '=' }}</code>
        </div>
      </div>

      <div class="curve-dialog__chart-wrap">
        <el-empty v-if="!lookupName" description="选择附录后可查看曲线预览" />
        <template v-else>
          <div ref="chartRef" class="curve-dialog__chart" />
          <div v-if="previewWarnings.length" class="curve-dialog__warnings">
            <div v-for="item in previewWarnings" :key="item">{{ item }}</div>
          </div>
        </template>
      </div>
    </div>

    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :disabled="!canSubmit" @click="handleConfirm">插入公式</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts'

import {
  fetchParameterLookupCurvePreview,
  fetchParameterLookupCurveProfile
} from '@/api/designPlatform.js'
import {
  buildCurveFormulaExpression,
  parseCurveFormulaExpression
} from '@/api/drumDesign.helpers.mjs'
import {
  buildLookupCurveChartOption,
  normalizeParameterLookupCurvePreview
} from '@/api/parameterLookup.helpers.mjs'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  lookupItems: {
    type: Array,
    default: () => []
  },
  parameterRows: {
    type: Array,
    default: () => []
  },
  initialExpression: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'apply'])

const chartRef = ref(null)
const chartInstance = ref(null)
const lookupName = ref('')
const inputName = ref('')
const seriesKey = ref('')
const direction = ref('X2Y')
const lookupMode = ref('LINEAR')
const multiplier = ref('')
const preview = ref({})
const profile = ref({})
const errorMessage = ref('')

const parameterOptions = computed(() =>
  (Array.isArray(props.parameterRows) ? props.parameterRows : [])
    .filter((item) => String(item?.paramName || '').trim())
    .map((item) => ({
      label: item.displayName || item.paramName,
      value: item.paramName
    }))
)

const seriesOptions = computed(() => {
  const profileSeries = Array.isArray(profile.value?.series_columns) ? profile.value.series_columns : []
  if (profileSeries.length) return profileSeries
  return Array.isArray(preview.value?.series) ? preview.value.series : []
})

const previewWarnings = computed(() => normalizeParameterLookupCurvePreview(preview.value || {}).warnings)

const formulaPreview = computed(() => buildCurveFormulaExpression({
  lookupName: lookupName.value,
  inputName: inputName.value,
  seriesKey: seriesKey.value,
  direction: direction.value,
  lookupMode: lookupMode.value,
  multiplier: multiplier.value
}))

const canSubmit = computed(() =>
  Boolean(lookupName.value && inputName.value && seriesKey.value && direction.value && lookupMode.value)
)

const selectedLookup = computed(() =>
  (Array.isArray(props.lookupItems) ? props.lookupItems : []).find(
    (item) => String(item.lookup_name || '') === String(lookupName.value || '')
  ) || null
)

const renderChart = async () => {
  await nextTick()
  if (!chartRef.value) return
  if (!chartInstance.value) {
    chartInstance.value = echarts.init(chartRef.value)
  }
  chartInstance.value.setOption(buildLookupCurveChartOption(preview.value || {}), true)
}

const loadLookupAssets = async () => {
  errorMessage.value = ''
  preview.value = {}
  profile.value = {}
  if (!selectedLookup.value?.id) return
  try {
    const [nextProfile, nextPreview] = await Promise.all([
      fetchParameterLookupCurveProfile(selectedLookup.value.id),
      fetchParameterLookupCurvePreview(selectedLookup.value.id)
    ])
    profile.value = nextProfile
    preview.value = nextPreview
    if (!seriesKey.value) {
      seriesKey.value = String(nextProfile?.series_columns?.[0]?.series_key || nextPreview?.series?.[0]?.series_key || '')
    }
    await renderChart()
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || '加载曲线预览失败'
  }
}

const resetFromExpression = async () => {
  const parsed = parseCurveFormulaExpression(props.initialExpression || '')
  lookupName.value = parsed?.lookupName || ''
  inputName.value = parsed?.inputName || ''
  seriesKey.value = parsed?.seriesKey || ''
  direction.value = parsed?.direction || 'X2Y'
  lookupMode.value = parsed?.lookupMode || 'LINEAR'
  multiplier.value = parsed?.multiplier || ''
  if (lookupName.value) {
    await loadLookupAssets()
  } else {
    preview.value = {}
    profile.value = {}
    errorMessage.value = ''
  }
}

const handleLookupChange = async () => {
  seriesKey.value = ''
  await loadLookupAssets()
}

const handleConfirm = () => {
  emit('apply', formulaPreview.value)
  emit('update:modelValue', false)
}

watch(
  () => props.modelValue,
  async (visible) => {
    if (visible) {
      await resetFromExpression()
      await renderChart()
      return
    }
    errorMessage.value = ''
  }
)

watch(
  () => props.initialExpression,
  async () => {
    if (props.modelValue) {
      await resetFromExpression()
    }
  }
)

onBeforeUnmount(() => {
  chartInstance.value?.dispose()
  chartInstance.value = null
})
</script>

<style scoped>
.curve-dialog {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 16px;
}

.curve-dialog__form,
.curve-dialog__chart-wrap {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.curve-dialog__chart {
  width: 100%;
  height: 360px;
}

.curve-dialog__preview {
  margin-top: 12px;
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
  color: #0f172a;
  word-break: break-all;
}

.curve-dialog__preview-label {
  margin-bottom: 6px;
  color: #64748b;
  font-size: 12px;
}

.curve-dialog__warnings {
  margin-top: 10px;
  color: #92400e;
  font-size: 12px;
  display: grid;
  gap: 6px;
}
</style>
