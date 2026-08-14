<template>
  <div class="lookup-curve-panel">
    <el-empty v-if="!activeLookupId" description="请选择附录后再维护" />

    <template v-else>
      <div class="lookup-curve-panel__header">
        <el-tag type="info">{{ tableModeLabel }}</el-tag>
      </div>

      <el-form label-width="68px" class="lookup-curve-panel__form" size="small">
        <el-form-item label="配置名称">
          <el-input v-model="draft.profile_name" placeholder="例如：电机扭矩参数曲线" />
        </el-form-item>
        <el-form-item label="X 轴列">
          <el-select v-model="draft.x_axis_column" filterable allow-create default-first-option placeholder="选择或输入 X 轴列">
            <el-option v-for="column in draft.table_columns" :key="column" :label="column" :value="column" />
          </el-select>
        </el-form-item>
        <el-form-item label="查值方式">
          <el-select v-model="draft.default_lookup_mode">
            <el-option label="LINEAR" value="LINEAR" />
          </el-select>
        </el-form-item>
        <el-form-item label="允许插值">
          <el-switch v-model="draft.allow_interpolation" />
        </el-form-item>
      </el-form>

      <div class="lookup-curve-panel__section">
        <div class="lookup-curve-panel__section-header">
          <strong>表格数据</strong>
          <span class="lookup-curve-panel__section-hint">导入后优先保持原表结构</span>
        </div>
        <el-table :data="draft.table_rows" border stripe max-height="320" size="small">
          <el-table-column
            v-for="column in draft.table_columns"
            :key="column"
            :label="column"
            :min-width="140"
          >
            <template #default="{ row }">
              <el-input v-model="row[column]" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="76" fixed="right">
            <template #default="{ $index }">
              <el-button link type="danger" @click="removeTableRow($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="lookup-curve-panel__layout">
        <div class="lookup-curve-panel__section">
          <div class="lookup-curve-panel__section-header">
            <strong>系列配置</strong>
            <div class="lookup-curve-panel__section-actions">
              <el-button size="small" @click="addSeries">新增系列</el-button>
            </div>
          </div>
          <div v-for="(item, index) in draft.series_columns" :key="index" class="lookup-curve-panel__series-row">
            <el-input v-model="item.series_key" placeholder="系列名，如 DRN" />
            <el-select v-model="item.source_column" filterable allow-create default-first-option placeholder="选择列">
              <el-option v-for="column in draft.table_columns" :key="column" :label="column" :value="column" />
            </el-select>
            <el-switch v-model="item.reverse_lookup_enabled" inline-prompt active-text="Y2X" inactive-text="X2Y" />
            <el-button link type="danger" @click="removeSeries(index)">删除</el-button>
          </div>
        </div>

        <div class="lookup-curve-panel__section">
          <div class="lookup-curve-panel__section-header">
            <strong>备注列</strong>
          </div>
          <el-select
            v-model="draft.note_columns"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="可选"
          >
            <el-option v-for="column in draft.table_columns" :key="column" :label="column" :value="column" />
          </el-select>
        </div>
      </div>

      <div class="lookup-curve-panel__section">
        <div class="lookup-curve-panel__section-header">
          <strong>曲线图</strong>
          <span class="lookup-curve-panel__section-hint">根据当前表格与系列配置实时生成</span>
        </div>
        <div v-if="chartReady" ref="chartRef" class="lookup-curve-panel__chart"></div>
        <el-empty v-else description="请先配置 X 轴列和至少一个有效系列" />
      </div>
    </template>
  </div>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

import {
  buildAppendixChartTableModel,
  buildCurveProfileDraftFromImportPreview,
  buildLookupCurveChartOption,
  hasMeaningfulCurveProfileChange,
  normalizeParameterLookupCurveProfile
} from '@/api/parameterLookup.helpers.mjs'

const props = defineProps({
  activeLookupId: {
    type: Number,
    default: 0
  },
  activeLookupName: {
    type: String,
    default: ''
  },
  rows: {
    type: Array,
    default: () => []
  },
  profile: {
    type: Object,
    default: () => ({})
  },
  saving: {
    type: Boolean,
    default: false
  },
  visible: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['change'])

const draft = ref(normalizeParameterLookupCurveProfile({}))
const chartRef = ref(null)
const chartInstance = ref(null)
let chartResizeObserver = null
let chartResizeFrame = 0

const tableModeLabel = computed(() => (draft.value.table_columns.includes('查找值') ? '附录行兼容视图' : '原表结构'))

const chartPreview = computed(() => {
  const profile = normalizeParameterLookupCurveProfile(draft.value || {})
  const xAxisColumn = String(profile.x_axis_column || '').trim()
  if (!xAxisColumn) {
    return { x_axis_column: '', series: [] }
  }
  return {
    x_axis_column: xAxisColumn,
    series: profile.series_columns
      .map((item) => {
        const points = profile.table_rows
          .map((row) => ({
            x: Number(row?.[xAxisColumn]),
            y: Number(row?.[item.source_column])
          }))
          .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y))
        return {
          series_key: item.series_key,
          source_column: item.source_column,
          reverse_lookup_enabled: item.reverse_lookup_enabled,
          is_monotonic: false,
          points
        }
      })
      .filter((item) => item.points.length > 0)
  }
})

const chartReady = computed(() => chartPreview.value.series.length > 0)

const syncDraftFromProps = () => {
  try {
    const normalized = normalizeParameterLookupCurveProfile(props.profile || {})
    const hasSnapshot = (normalized.table_rows || []).length > 0
    if (!hasSnapshot && Array.isArray(props.rows) && props.rows.length) {
      draft.value = normalizeParameterLookupCurveProfile(
        buildCurveProfileDraftFromImportPreview(
          { rows: props.rows },
          {
            profile_name: normalized.profile_name || props.activeLookupName || '',
            series_columns: normalized.series_columns,
            default_lookup_mode: normalized.default_lookup_mode || 'LINEAR',
            allow_interpolation: normalized.allow_interpolation !== false
          }
        )
      )
    } else {
      const tableModel = buildAppendixChartTableModel(props.rows || [], normalized)
      draft.value = {
        ...normalized,
        table_columns: [...tableModel.columns],
        table_rows: tableModel.rows.map((row) => ({ ...row })),
        series_columns: normalized.series_columns.map((row) => ({ ...row })),
        note_columns: [...normalized.note_columns]
      }
    }
  } catch (e) {
    console.error('ParameterLookupCurvePanel syncDraftFromProps failed', e)
    draft.value = normalizeParameterLookupCurveProfile({})
  }
}

const addSeries = () => {
  draft.value.series_columns.push({
    series_key: '',
    source_column: '',
    reverse_lookup_enabled: false
  })
}

const removeSeries = (index) => {
  draft.value.series_columns.splice(index, 1)
}

const removeTableRow = (index) => {
  draft.value.table_rows.splice(index, 1)
}

const queueChartResize = () => {
  if (!chartInstance.value) {
    return
  }
  if (chartResizeFrame) {
    cancelAnimationFrame(chartResizeFrame)
  }
  chartResizeFrame = requestAnimationFrame(() => {
    chartInstance.value?.resize()
    chartResizeFrame = 0
  })
}

const flushChartResize = async () => {
  await nextTick()
  queueChartResize()
  requestAnimationFrame(() => {
    queueChartResize()
  })
}

const bindChartResizeObserver = async () => {
  await nextTick()
  if (typeof ResizeObserver === 'undefined' || !chartRef.value) {
    return
  }
  chartResizeObserver?.disconnect()
  chartResizeObserver = new ResizeObserver(() => {
    queueChartResize()
  })
  chartResizeObserver.observe(chartRef.value)
  if (chartRef.value.parentElement) {
    chartResizeObserver.observe(chartRef.value.parentElement)
  }
}

const renderChart = async () => {
  await nextTick()
  if (!chartReady.value || !chartRef.value || !props.visible) {
    chartResizeObserver?.disconnect()
    chartResizeObserver = null
    chartInstance.value?.dispose()
    chartInstance.value = null
    return
  }
  try {
    if (!chartInstance.value) {
      const el = chartRef.value
      if (!el || !el.offsetParent || el.clientWidth === 0) {
        return
      }
      chartInstance.value = echarts.init(el)
    }
    chartInstance.value.setOption(buildLookupCurveChartOption(chartPreview.value), true)
    await bindChartResizeObserver()
    await flushChartResize()
  } catch (e) {
    console.error('ParameterLookupCurvePanel renderChart failed', e)
    chartResizeObserver?.disconnect()
    chartResizeObserver = null
    chartInstance.value?.dispose()
    chartInstance.value = null
  }
}

watch(
  () => props.profile,
  () => {
    syncDraftFromProps()
  },
  { deep: true, immediate: true }
)

watch(
  draft,
  () => {
    if (hasMeaningfulCurveProfileChange(draft.value, props.profile)) {
      emit('change', normalizeParameterLookupCurveProfile(draft.value))
    }
    renderChart()
  },
  { deep: true }
)

watch(
  () => props.rows,
  () => {
    if (!props.activeLookupId) return
    syncDraftFromProps()
  },
  { deep: true }
)

watch(
  () => props.visible,
  async (visible) => {
    if (!visible) {
      return
    }
    await nextTick()
    await renderChart()
  },
  { immediate: true }
)

watch(
  () => props.activeLookupId,
  async () => {
    if (!props.visible) {
      return
    }
    await nextTick()
    await renderChart()
  }
)

watch(
  () => props.saving,
  async (saving, previous) => {
    if (previous && !saving && props.visible) {
      await nextTick()
      await renderChart()
    }
  }
)

onBeforeUnmount(() => {
  chartResizeObserver?.disconnect()
  chartResizeObserver = null
  if (chartResizeFrame) {
    cancelAnimationFrame(chartResizeFrame)
    chartResizeFrame = 0
  }
  chartInstance.value?.dispose()
  chartInstance.value = null
})
</script>

<style scoped>
.lookup-curve-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lookup-curve-panel__header,
.lookup-curve-panel__section-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lookup-curve-panel__header,
.lookup-curve-panel__section-header {
  justify-content: space-between;
}

.lookup-curve-panel__section-hint {
  color: #64748b;
  font-size: 12px;
}

.lookup-curve-panel__form,
.lookup-curve-panel__section {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px;
  background: #fff;
}

.lookup-curve-panel__form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  column-gap: 8px;
}

.lookup-curve-panel__form :deep(.el-form-item) {
  margin-bottom: 4px;
}

.lookup-curve-panel__layout {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.9fr);
  gap: 8px;
}

.lookup-curve-panel__series-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto auto;
  gap: 6px;
  align-items: center;
  margin-bottom: 6px;
}

.lookup-curve-panel__chart {
  width: 100%;
  height: 280px;
}
</style>
