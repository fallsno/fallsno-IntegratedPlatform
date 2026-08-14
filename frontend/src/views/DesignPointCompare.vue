<template>
  <div class="design-point-compare">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="title-group">
            <el-icon><DataAnalysis /></el-icon>
            <span class="title">电机与关键参数跨型号对比</span>
          </div>
          <el-button @click="$router.back()" size="small" icon="ArrowLeft">返回设计界面</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="参数对比" name="table">
          <div class="filter-bar">
            <el-form :model="filterForm" inline size="default">
              <el-form-item label="关键字搜索">
                <el-input
                  v-model="filterForm.keyword"
                  placeholder="搜索代号 (如 AT) 或 名称 (如 干燥滚筒)..."
                  style="width: 300px"
                  clearable
                  @input="handleKeywordSearch"
                  prefix-icon="Search"
                />
              </el-form-item>
              <el-form-item label="对比参数">
                <el-select
                  v-model="filterForm.designPoints"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="选择参数..."
                  style="width: 250px"
                  @change="fetchCustomData"
                >
                  <el-option v-for="p in commonParams" :key="p" :label="p" :value="p" />
                </el-select>
              </el-form-item>
              <el-form-item label="列维度">
                <el-select v-model="filterForm.colDimensions[0]" @change="fetchCustomData" style="width: 100px">
                  <el-option label="按部件" value="part_name" />
                  <el-option label="按流程" value="flow_name" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" icon="Refresh" @click="fetchCustomData" :loading="loading">分析</el-button>
              </el-form-item>
            </el-form>
          </div>

          <div v-loading="loading" class="chart-section">
            <div class="chart-header">
              <el-radio-group v-model="chartType" size="small" @change="initChart">
                <el-radio-button value="bar">柱状图</el-radio-button>
                <el-radio-button value="line">折线图</el-radio-button>
              </el-radio-group>
            </div>
            <div ref="pivotChartRef" class="single-chart"></div>
            <el-empty v-if="!pivotData.length && !loading" description="暂无对比数据，请调整筛选条件" />
          </div>

          <div class="table-section">
            <div class="table-toolbar">
              <div class="section-title">数据明细 (按代号排序)</div>
              <div class="toolbar-actions">
                <el-switch v-model="showGuidance" active-text="显示设计指导" inactive-text="仅看数值" @change="fetchCustomData" />
                <el-button icon="Download" size="small" @click="exportData" style="margin-left: 15px;">导出 Excel 报表</el-button>
              </div>
            </div>
            <el-table
              :data="sortedPivotData"
              v-loading="loading"
              border
              stripe
              size="small"
              max-height="600"
              class="compare-table full-width-table"
              highlight-current-row
            >
              <el-table-column
                v-for="dim in filterForm.rowDimensions"
                :key="dim"
                :label="dimensionLabels[dim] || dim"
                width="180"
                fixed="left"
                sortable
              >
                <template #default="{ row }">
                  <span class="dim-label">{{ row._row_keys[dim] || '-' }}</span>
                </template>
              </el-table-column>

              <el-table-column
                v-for="colKey in dynamicColumns"
                :key="colKey"
                :label="colKey"
                align="center"
              >
                <el-table-column
                  v-for="valName in filterForm.designPoints"
                  :key="colKey + valName"
                  :label="valName"
                  width="180"
                  align="right"
                >
                  <template #default="{ row }">
                    <div class="value-cell">
                      <span class="value-text" :class="{ 'has-val': row[colKey] && row[colKey][valName] }">
                        {{ row[colKey] ? formatValue(row[colKey][valName]) : '-' }}
                      </span>
                      <div v-if="showGuidance && row[colKey] && row[colKey][valName]" class="guidance-tags">
                        <el-tag
                          v-if="isOverridden(row[colKey][valName], valName, colKey)"
                          size="small"
                          type="warning"
                          effect="light"
                          title="该值覆盖了系列模板的默认值"
                        >覆盖</el-tag>
                        <el-tag
                          v-if="hasRisk(row[colKey][valName], valName)"
                          size="small"
                          type="danger"
                          effect="dark"
                          title="命中设计规则：数值偏离安全区间"
                        >风险</el-tag>
                      </div>
                    </div>
                  </template>
                </el-table-column>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="公式参数影响分析" name="formula-impact">
          <div class="impact-section">
            <el-alert
              type="info"
              :closable="false"
              title="该页签读取工作台带来的公式上下文，优先用图表展示目标参数变化对多个结果的影响。"
            />
            <el-form :model="impactForm" inline class="impact-form">
              <el-form-item label="型号 ID">
                <el-input v-model="impactForm.modelId" style="width: 120px" />
              </el-form-item>
              <el-form-item label="公式名称">
                <el-input v-model="impactForm.formulaName" style="width: 220px" />
              </el-form-item>
              <el-form-item label="目标参数">
                <el-select
                  v-model="impactForm.targetParameter"
                  filterable
                  allow-create
                  default-first-option
                  style="width: 180px"
                >
                  <el-option
                    v-for="item in impactParameterOptions"
                    :key="item"
                    :label="item"
                    :value="item"
                  />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="impactLoading" @click="loadImpactRows">分析影响</el-button>
              </el-form-item>
            </el-form>

            <div v-loading="impactLoading">
              <div v-if="impactPayload && impactPayload.result_summary && impactPayload.result_summary.length">
                <div class="impact-view-switch">
                  <el-segmented
                    v-model="impactViewMode"
                    :options="[
                      { label: '趋势分析', value: 'trend' },
                      { label: '状态查看', value: 'state' }
                    ]"
                  />
                </div>

                <div v-if="impactViewMode === 'trend'" class="impact-results">
                  <div class="impact-toolbar-card">
                    <div class="impact-toolbar-meta">
                      <div class="impact-toolbar-title">结果趋势分析</div>
                      <div class="impact-toolbar-subtitle">
                        基准参数 {{ impactPayload.baseline_parameter_value || '-' }}，默认展示最敏感结果，可通过下拉切换
                      </div>
                    </div>
                    <el-select
                      v-model="selectedImpactResults"
                      multiple
                      filterable
                      collapse-tags
                      collapse-tags-tooltip
                      placeholder="选择要展示的结果"
                      class="impact-result-select"
                    >
                      <el-option
                        v-for="item in impactTrendOptions"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                      />
                    </el-select>
                  </div>

                  <div class="impact-trend-panel">
                    <div class="impact-panel-header">
                      <h4>结果趋势图</h4>
                      <span>同图对比多个受影响结果</span>
                    </div>
                    <div v-if="impactTrendSeries.length" ref="impactTrendChartRef" class="impact-trend-chart"></div>
                    <el-empty v-else description="暂无可展示的趋势图数据" />
                  </div>

                  <div class="impact-metric-grid">
                    <div class="impact-metric-card">
                      <div class="impact-panel-header">
                        <h4>敏感度排序</h4>
                        <span>点击条形可同步高亮趋势线</span>
                      </div>
                      <div v-if="impactSensitivityRows.length" ref="impactSensitivityChartRef" class="impact-mini-chart"></div>
                      <el-empty v-else description="暂无敏感度数据" />
                    </div>
                    <div class="impact-metric-card">
                      <div class="impact-panel-header">
                        <h4>波动区间</h4>
                        <span>显示最小值、最大值和基准值</span>
                      </div>
                      <div v-if="impactRangeRows.length" ref="impactRangeChartRef" class="impact-mini-chart"></div>
                      <el-empty v-else description="暂无波动区间数据" />
                    </div>
                  </div>

                  <div class="impact-summary-grid">
                    <button
                      v-for="card in compactImpactCards"
                      :key="card.resultName"
                      type="button"
                      class="impact-summary-tile"
                      @click="focusImpactResult(card.resultName)"
                    >
                      <div class="impact-summary-tile__header">
                        <span class="impact-summary-tile__title">{{ card.resultName }}</span>
                        <el-tag size="small" :type="card.impactLevel === 'high' ? 'danger' : (card.impactLevel === 'medium' ? 'warning' : 'info')">
                          {{ card.trendLabel }}
                        </el-tag>
                      </div>
                      <div class="impact-summary-tile__baseline">{{ card.baselineText }}</div>
                      <div class="impact-summary-tile__metrics">
                        <span>敏感度 {{ card.sensitivityText }}</span>
                        <span>区间 {{ card.rangeText }}</span>
                      </div>
                    </button>
                  </div>
                </div>

                <div v-else class="impact-state-panel">
                  <div class="impact-state-filter-card">
                    <div class="impact-panel-header">
                      <h4>状态筛选器</h4>
                      <span>按目标参数切片当前影响分析样本</span>
                    </div>
                    <el-form inline class="impact-state-filter-form">
                      <el-form-item label="目标参数">
                        <el-input :model-value="impactPayload?.target_parameter || impactForm.targetParameter || '-'" readonly style="width: 180px" />
                      </el-form-item>
                      <el-form-item label="筛选类型">
                        <el-select v-model="impactStateFilterType" style="width: 140px">
                          <el-option label="单值" value="single" />
                          <el-option label="多值" value="multi" />
                          <el-option label="区间" value="range" />
                        </el-select>
                      </el-form-item>
                      <el-form-item v-if="impactStateFilterType === 'single'" label="参数值">
                        <el-input v-model="impactStateFilterValue.single" placeholder="例如 40" style="width: 180px" />
                      </el-form-item>
                      <el-form-item v-if="impactStateFilterType === 'multi'" label="参数值">
                        <el-select
                          v-model="impactStateFilterValue.multi"
                          multiple
                          filterable
                          allow-create
                          default-first-option
                          placeholder="例如 40 / 45 / 50"
                          style="width: 260px"
                        />
                      </el-form-item>
                      <el-form-item v-if="impactStateFilterType === 'range'" label="参数区间">
                        <div class="impact-range-inputs">
                          <el-input v-model="impactStateFilterValue.rangeMin" placeholder="最小值" style="width: 120px" />
                          <span>~</span>
                          <el-input v-model="impactStateFilterValue.rangeMax" placeholder="最大值" style="width: 120px" />
                        </div>
                      </el-form-item>
                      <el-form-item>
                        <el-button type="primary" @click="applyImpactStateFilter">应用筛选</el-button>
                        <el-button @click="resetImpactStateFilter">重置</el-button>
                      </el-form-item>
                    </el-form>
                    <div
                      v-if="impactStateFilterType === 'single' && impactStateMatchedHint"
                      class="impact-state-filter-hint"
                    >
                      {{ impactStateMatchedHint }}
                    </div>
                  </div>

                  <div class="impact-state-primary-card">
                    <div class="impact-panel-header">
                      <h4>状态主图</h4>
                      <span>{{ impactStateChartModeLabel }}</span>
                    </div>
                    <div v-if="impactStateChartMode !== 'empty'" ref="impactStatePrimaryChartRef" class="impact-state-primary-chart"></div>
                    <el-empty v-else description="当前筛选没有命中任何状态，请调整筛选条件" />
                  </div>

                  <div class="impact-state-summary-grid">
                    <div v-for="card in impactStateSummaryCards" :key="`${card.title}-${card.value}`" class="impact-state-summary-card">
                      <div class="impact-state-summary-card__title">{{ card.title }}</div>
                      <div class="impact-state-summary-card__value">{{ card.value }}</div>
                      <div class="impact-state-summary-card__meta">{{ card.meta }}</div>
                    </div>
                  </div>

                  <div class="impact-state-table">
                    <h4>状态结果表</h4>
                    <el-table :data="impactStateTableRows" border size="small" max-height="420">
                      <el-table-column prop="resultName" label="结果名称" min-width="180" fixed="left" />
                      <el-table-column v-if="impactStateChartMode === 'single-bar'" prop="currentValue" label="当前值" width="120" />
                      <el-table-column v-if="impactStateChartMode === 'single-bar'" prop="baselineValue" label="基准值" width="120" />
                      <el-table-column v-if="impactStateChartMode === 'single-bar'" prop="deltaValue" label="绝对差值" width="120" />
                      <el-table-column v-if="impactStateChartMode === 'single-bar'" prop="deltaPercent" label="相对变化" width="120" />
                      <el-table-column v-if="impactStateChartMode === 'single-bar'" prop="unitCode" label="单位" width="100" />
                      <el-table-column v-if="impactStateChartMode === 'single-bar'" prop="sensitivity" label="敏感度" width="100" />
                      <el-table-column v-if="impactStateChartMode !== 'single-bar'" prop="minValue" label="最小值" width="120" />
                      <el-table-column v-if="impactStateChartMode !== 'single-bar'" prop="maxValue" label="最大值" width="120" />
                      <el-table-column v-if="impactStateChartMode !== 'single-bar'" prop="stateCount" label="命中状态数" width="120" />
                    </el-table>
                  </div>
                </div>

                <div class="impact-path">
                  <h4>受影响计算链路</h4>
                  <el-table :data="impactPayload.impact_path" border size="small">
                    <el-table-column prop="depth" label="链路深度" width="80" align="center" />
                    <el-table-column prop="scene_name" label="场景" width="140" />
                    <el-table-column prop="node_name" label="公式名称" width="200" />
                    <el-table-column label="依赖变量" min-width="300">
                      <template #default="{ row }">
                        <el-tag v-for="dep in row.dependencies" :key="dep" size="small" class="dep-tag" type="info">{{ dep }}</el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>

                <div class="impact-samples">
                  <h4>参数波动结果明细</h4>
                  <el-table :data="flattenedSamples" border size="small" max-height="400">
                    <el-table-column prop="parameter_value" :label="`${impactForm.targetParameter} (目标)`" width="140" />
                    <el-table-column prop="input_delta_percent" label="变动比例" width="100" />
                    <el-table-column prop="result_name" label="受影响结果" width="180" />
                    <el-table-column prop="current_value" label="结果值" width="120" />
                    <el-table-column prop="delta_value" label="绝对差值" width="120" />
                    <el-table-column prop="delta_percent" label="相对变化" width="100" />
                  </el-table>
                </div>
              </div>
              <el-empty v-else-if="!impactLoading" description="暂无分析结果或目标参数未影响任何结果" />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, nextTick, reactive, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import * as echarts from 'echarts'

import {
  buildImpactCompactCards,
  buildImpactDefaultSelection,
  buildImpactRangeRows,
  buildImpactSensitivityRows,
  buildImpactStateSummaryCards,
  buildImpactStateTableRows,
  buildImpactTrendSeries
  ,
  filterImpactSamplesByMultiValues,
  filterImpactSamplesByRange,
  filterImpactSamplesBySingleValue,
  resolveImpactStateChartMode
} from '@/api/drumDesign'

const route = useRoute()
const loading = ref(false)
const chartType = ref('bar')
const activeTab = ref('table')
const impactLoading = ref(false)
const impactPayload = ref(null)
const selectedImpactResults = ref([])
const impactViewMode = ref('trend')
const impactStateFilterType = ref('single')
const impactStateAppliedFilter = ref({
  filterType: 'single',
  filterValue: ''
})

const filterForm = reactive({
  keyword: '',
  designPoints: route.query.designPoint ? [route.query.designPoint] : ['电机功率', '滚圈宽度'],
  rowDimensions: ['product_type_model_code', 'machine_model', 'family_name'], // 默认全选关键维度
  colDimensions: ['part_name']
})

const impactForm = reactive({
  modelId: String(route.query.modelId || ''),
  formulaName: route.query.formulaName || '',
  targetParameter: route.query.targetParameter || '',
  resultName: route.query.formulaName || '推荐电机功率',
  parameters: {}
})
const impactStateFilterValue = reactive({
  single: '',
  multi: [],
  rangeMin: '',
  rangeMax: ''
})

const showGuidance = ref(false)

// 模拟指导判断逻辑：判断该参数在当前型号下是否覆盖了基线模板的值
const isOverridden = (val, paramName, colKey) => {
  if (!val) return false
  const numVal = parseFloat(val)
  // 这里用简单的模拟逻辑：假设参数值带有特定尾数或是奇数则判定为覆盖
  if (paramName === '滚圈宽度' && numVal > 150) return true
  if (paramName === '电机功率' && numVal !== 37 && numVal !== 45 && numVal !== 55) return true
  return Math.random() > 0.85
}

// 模拟规则引擎风险判断
const hasRisk = (val, paramName) => {
  if (!val) return false
  const numVal = parseFloat(val)
  // 模拟风险：功率过小或过大
  if (paramName === '电机功率' && (numVal < 30 || numVal > 100)) return true
  // 模拟风险：带速异常
  if (paramName === '带速' && numVal > 2.5) return true
  return Math.random() > 0.95
}

const commonParams = ['电机功率', '滚圈宽度', '滚圈厚度', '带速', '初始含水率W1 %', '产量']
const impactBaseParams = ['摩擦系数', '传动比', '电机效率', '功率储备系数', '滚筒重量', '进料量', '托轮直径', '电机转速']

const pivotData = ref([])
const dynamicColumns = ref([])
const dimensionLabels = {
  machine_model: '机型名称',
  product_type_model_code: '产品代号',
  part_name: '所属部件',
  flow_name: '设计流程',
  family_name: '型号名称',
  created_at: '创建时间'
}

const pivotChartRef = ref(null)
let chartInstance = null
const impactTrendChartRef = ref(null)
let impactTrendChartInstance = null
const impactSensitivityChartRef = ref(null)
let impactSensitivityChartInstance = null
const impactRangeChartRef = ref(null)
let impactRangeChartInstance = null
const impactStatePrimaryChartRef = ref(null)
let impactStatePrimaryChartInstance = null

// 按关键字过滤并排序后的数据
const sortedPivotData = computed(() => {
  let data = [...pivotData.value]
  
  // 关键字过滤
  if (filterForm.keyword) {
    const kw = filterForm.keyword.toLowerCase()
    data = data.filter(row => {
      const code = (row._row_keys.product_type_model_code || '').toLowerCase()
      const model = (row._row_keys.machine_model || '').toLowerCase()
      const name = (row._row_keys.family_name || '').toLowerCase()
      return code.includes(kw) || model.includes(kw) || name.includes(kw)
    })
  }

  // 排序
  return data.sort((a, b) => {
    const codeA = a._row_keys.product_type_model_code || ''
    const codeB = b._row_keys.product_type_model_code || ''
    return codeA.localeCompare(codeB)
  })
})

const impactParameterOptions = computed(() => {
  return [...new Set([impactForm.targetParameter, ...impactBaseParams].filter(Boolean))]
})

const impactTrendOptions = computed(() => {
  return (impactPayload.value?.result_summary || []).map((item) => ({
    label: item.result_name,
    value: item.result_name
  }))
})

const flattenedSamples = computed(() => {
  if (!impactPayload.value || !impactPayload.value.samples) return []
  const rows = []
  impactPayload.value.samples.forEach(sample => {
    if (sample.results && sample.results.length) {
      sample.results.forEach(res => {
        rows.push({
          parameter_value: sample.parameter_value,
          input_delta_percent: sample.input_delta_percent,
          result_name: res.result_name,
          current_value: res.current_value,
          delta_value: res.delta_value,
          delta_percent: res.delta_percent
        })
      })
    }
  })
  return rows
})

const impactTrendSeries = computed(() => buildImpactTrendSeries(impactPayload.value, selectedImpactResults.value))
const impactSensitivityRows = computed(() => buildImpactSensitivityRows(impactPayload.value))
const impactRangeRows = computed(() => buildImpactRangeRows(impactPayload.value))
const compactImpactCards = computed(() => buildImpactCompactCards(impactPayload.value, selectedImpactResults.value))
const filteredImpactSamples = computed(() => {
  if (!impactPayload.value) return []
  if (impactStateAppliedFilter.value.filterType === 'multi') {
    return filterImpactSamplesByMultiValues(impactPayload.value, impactStateAppliedFilter.value.filterValue)
  }
  if (impactStateAppliedFilter.value.filterType === 'range') {
    return filterImpactSamplesByRange(impactPayload.value, impactStateAppliedFilter.value.filterValue)
  }
  return filterImpactSamplesBySingleValue(impactPayload.value, impactStateAppliedFilter.value.filterValue)
})
const impactStateChartMode = computed(() => resolveImpactStateChartMode(filteredImpactSamples.value))
const impactStateMatchedSample = computed(() => {
  if (impactStateAppliedFilter.value.filterType !== 'single') return null
  return filteredImpactSamples.value[0] || null
})
const impactStateMatchedHint = computed(() => {
  if (!impactStateAppliedFilter.value.filterValue || !impactStateMatchedSample.value) return ''
  return `输入 ${impactStateAppliedFilter.value.filterValue}，实际命中 ${impactStateMatchedSample.value.parameter_value}`
})
const impactStateSummaryCards = computed(() =>
  buildImpactStateSummaryCards(filteredImpactSamples.value, impactPayload.value?.result_summary || [], impactStateAppliedFilter.value)
)
const impactStateTableRows = computed(() =>
  buildImpactStateTableRows(
    filteredImpactSamples.value,
    impactPayload.value?.result_summary || [],
    impactStateChartMode.value === 'single-bar' ? 'single' : 'multi'
  )
)
const impactStateChartModeLabel = computed(() => {
  if (impactStateChartMode.value === 'single-bar') return '单状态条形图'
  if (impactStateChartMode.value === 'grouped-bar') return '少量多状态分组柱状图'
  if (impactStateChartMode.value === 'heatmap') return '较多状态热力矩阵'
  return '空态'
})
const impactStateSingleBarData = computed(() => {
  if (impactStateChartMode.value !== 'single-bar') return []
  return (filteredImpactSamples.value[0]?.results || []).map((item) => ({
    name: item.result_name,
    value: Number.parseFloat(item.current_value || '0') || 0
  }))
})
const impactStateGroupedBarData = computed(() => {
  if (impactStateChartMode.value !== 'grouped-bar') return []
  const resultNames = [...new Set(filteredImpactSamples.value.flatMap((sample) => (sample.results || []).map((row) => row.result_name)))]
  return resultNames.map((name) => ({
    name,
    values: filteredImpactSamples.value.map((sample) => {
      const matched = (sample.results || []).find((row) => row.result_name === name)
      return Number.parseFloat(matched?.current_value || '0') || 0
    })
  }))
})
const impactStateHeatmapData = computed(() => {
  if (impactStateChartMode.value !== 'heatmap') {
    return { xAxis: [], yAxis: [], values: [] }
  }
  const xAxis = filteredImpactSamples.value.map((sample) => sample.parameter_value)
  const yAxis = [...new Set(filteredImpactSamples.value.flatMap((sample) => (sample.results || []).map((row) => row.result_name)))]
  const values = []
  filteredImpactSamples.value.forEach((sample, xIndex) => {
    yAxis.forEach((name, yIndex) => {
      const matched = (sample.results || []).find((row) => row.result_name === name)
      values.push([xIndex, yIndex, Number.parseFloat(matched?.current_value || '0') || 0])
    })
  })
  return { xAxis, yAxis, values }
})

const handleKeywordSearch = () => {
  // 防抖或即时更新图表
  nextTick(() => {
    initChart()
  })
}

const formatValue = (val) => {
  if (val === undefined || val === null || val === '') return '-'
  const num = parseFloat(val)
  return isNaN(num) ? val : num.toFixed(2)
}

const fetchCustomData = async () => {
  if (!filterForm.designPoints.length) {
    ElMessage.warning('请至少选择一个对比参数')
    return
  }
  loading.value = true
  try {
    const res = await axios.post('/compare/custom', {
      row_dimensions: filterForm.rowDimensions,
      col_dimensions: filterForm.colDimensions,
      values: filterForm.designPoints
    })
    
    pivotData.value = res.data.data
    
    // 提取动态列
    const cols = new Set()
    pivotData.value.forEach(row => {
      Object.keys(row).forEach(k => {
        if (k !== '_row_keys') cols.add(k)
      })
    })
    dynamicColumns.value = Array.from(cols).sort()
    
    nextTick(() => {
      initChart()
    })
  } catch (err) {
    console.error('对比查询失败:', err)
    ElMessage.error('获取对比数据失败')
  } finally {
    loading.value = false
  }
}

const hydrateImpactContext = () => {
  const cached = window.sessionStorage.getItem('drumFormulaImpactContext')
  if (!cached) return
  try {
    const parsed = JSON.parse(cached)
    impactForm.modelId = String(parsed.modelId || impactForm.modelId || '')
    impactForm.formulaName = parsed.formulaName || impactForm.formulaName || ''
    impactForm.targetParameter = parsed.targetParameter || impactForm.targetParameter || ''
    impactForm.resultName = parsed.formulaName || impactForm.resultName || '推荐电机功率'
    impactForm.parameters = parsed.parameters || {}
  } catch {
    impactForm.parameters = {}
  }
}

const loadImpactRows = async () => {
  impactPayload.value = null
  ElMessage.warning('旧版公式参数影响分析已下线')
}

const syncSelectedImpactResults = () => {
  const nextSelection = buildImpactDefaultSelection(
    impactPayload.value,
    impactForm.resultName || impactForm.formulaName,
    3
  )
  selectedImpactResults.value = nextSelection
}

const syncImpactStateDefaultFilter = () => {
  const baselineValue = impactPayload.value?.baseline_parameter_value || ''
  impactStateFilterType.value = 'single'
  impactStateFilterValue.single = baselineValue
  impactStateFilterValue.multi = baselineValue ? [baselineValue] : []
  impactStateFilterValue.rangeMin = ''
  impactStateFilterValue.rangeMax = ''
  impactStateAppliedFilter.value = {
    filterType: 'single',
    filterValue: baselineValue
  }
}

const applyImpactStateFilter = () => {
  if (impactStateFilterType.value === 'multi') {
    impactStateAppliedFilter.value = {
      filterType: 'multi',
      filterValue: [...impactStateFilterValue.multi]
    }
    return
  }
  if (impactStateFilterType.value === 'range') {
    impactStateAppliedFilter.value = {
      filterType: 'range',
      filterValue: {
        min: impactStateFilterValue.rangeMin,
        max: impactStateFilterValue.rangeMax
      }
    }
    return
  }
  impactStateAppliedFilter.value = {
    filterType: 'single',
    filterValue: impactStateFilterValue.single
  }
}

const resetImpactStateFilter = () => {
  syncImpactStateDefaultFilter()
}

const focusImpactResult = (name) => {
  const normalized = String(name || '').trim()
  if (!normalized) return
  if (!selectedImpactResults.value.includes(normalized)) {
    selectedImpactResults.value = [...selectedImpactResults.value, normalized]
  }
  nextTick(() => {
    impactTrendChartInstance?.dispatchAction({ type: 'highlight', seriesName: normalized })
  })
}

const renderImpactTrendChart = async () => {
  await nextTick()
  if (!impactTrendChartRef.value || !impactTrendSeries.value.length) {
    impactTrendChartInstance?.dispose()
    impactTrendChartInstance = null
    return
  }

  if (!impactTrendChartInstance) {
    impactTrendChartInstance = echarts.init(impactTrendChartRef.value)
  }

  impactTrendChartInstance.setOption(
    {
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        type: 'scroll',
        bottom: 0
      },
      grid: {
        left: 48,
        right: 24,
        top: 32,
        bottom: 48,
        containLabel: true
      },
      xAxis: {
        type: 'value',
        name: impactForm.targetParameter || '目标参数',
        scale: true
      },
      yAxis: {
        type: 'value',
        name: '结果值',
        scale: true
      },
      series: impactTrendSeries.value.map((item) => ({
        name: item.name,
        type: 'line',
        smooth: true,
        showSymbol: true,
        symbolSize: 6,
        emphasis: { focus: 'series' },
        data: item.data
      }))
    },
    true
  )

  impactTrendChartInstance.resize()
}

const renderImpactSensitivityChart = async () => {
  await nextTick()
  if (!impactSensitivityChartRef.value || !impactSensitivityRows.value.length) {
    impactSensitivityChartInstance?.dispose()
    impactSensitivityChartInstance = null
    return
  }

  if (!impactSensitivityChartInstance) {
    impactSensitivityChartInstance = echarts.init(impactSensitivityChartRef.value)
    impactSensitivityChartInstance.on('click', (params) => focusImpactResult(params.name))
  }

  impactSensitivityChartInstance.setOption(
    {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 120, right: 20, top: 20, bottom: 16, containLabel: true },
      xAxis: { type: 'value', name: '敏感度' },
      yAxis: {
        type: 'category',
        data: impactSensitivityRows.value.map((item) => item.resultName)
      },
      series: [
        {
          type: 'bar',
          barMaxWidth: 18,
          data: impactSensitivityRows.value.map((item) => ({
            name: item.resultName,
            value: item.sensitivity,
            itemStyle: {
              color: item.impactLevel === 'high' ? '#ef4444' : item.impactLevel === 'medium' ? '#f59e0b' : '#60a5fa'
            }
          }))
        }
      ]
    },
    true
  )

  impactSensitivityChartInstance.resize()
}

const renderImpactRangeChart = async () => {
  await nextTick()
  if (!impactRangeChartRef.value || !impactRangeRows.value.length) {
    impactRangeChartInstance?.dispose()
    impactRangeChartInstance = null
    return
  }

  if (!impactRangeChartInstance) {
    impactRangeChartInstance = echarts.init(impactRangeChartRef.value)
    impactRangeChartInstance.on('click', (params) => focusImpactResult(params.name))
  }

  impactRangeChartInstance.setOption(
    {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 120, right: 24, top: 20, bottom: 16, containLabel: true },
      xAxis: { type: 'value', name: '结果范围' },
      yAxis: {
        type: 'category',
        data: impactRangeRows.value.map((item) => item.resultName)
      },
      series: [
        {
          type: 'bar',
          stack: 'range',
          silent: true,
          itemStyle: { color: 'transparent' },
          data: impactRangeRows.value.map((item) => item.min)
        },
        {
          type: 'bar',
          stack: 'range',
          name: '波动区间',
          barMaxWidth: 14,
          data: impactRangeRows.value.map((item) => ({
            name: item.resultName,
            value: item.span,
            itemStyle: { color: '#93c5fd', borderRadius: 999 }
          }))
        },
        {
          type: 'scatter',
          name: '基准值',
          symbolSize: 10,
          data: impactRangeRows.value.map((item) => [item.baseline, item.resultName]),
          itemStyle: { color: '#1d4ed8' }
        }
      ]
    },
    true
  )

  impactRangeChartInstance.resize()
}

const renderImpactStatePrimaryChart = async () => {
  await nextTick()
  if (!impactStatePrimaryChartRef.value || impactStateChartMode.value === 'empty') {
    impactStatePrimaryChartInstance?.dispose()
    impactStatePrimaryChartInstance = null
    return
  }

  if (!impactStatePrimaryChartInstance) {
    impactStatePrimaryChartInstance = echarts.init(impactStatePrimaryChartRef.value)
  }

  if (impactStateChartMode.value === 'single-bar') {
    impactStatePrimaryChartInstance.setOption(
      {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 120, right: 24, top: 20, bottom: 16, containLabel: true },
        xAxis: { type: 'value', name: '结果值' },
        yAxis: { type: 'category', data: impactStateSingleBarData.value.map((item) => item.name) },
        series: [{
          type: 'bar',
          data: impactStateSingleBarData.value.map((item) => item.value),
          barMaxWidth: 18,
          itemStyle: { color: '#3b82f6', borderRadius: [0, 999, 999, 0] }
        }]
      },
      true
    )
  } else if (impactStateChartMode.value === 'grouped-bar') {
    impactStatePrimaryChartInstance.setOption(
      {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { type: 'scroll', bottom: 0 },
        grid: { left: 56, right: 24, top: 28, bottom: 48, containLabel: true },
        xAxis: { type: 'category', data: filteredImpactSamples.value.map((sample) => sample.parameter_value) },
        yAxis: { type: 'value', name: '结果值' },
        series: impactStateGroupedBarData.value.map((item) => ({
          name: item.name,
          type: 'bar',
          data: item.values
        }))
      },
      true
    )
  } else {
    const maxValue = Math.max(...impactStateHeatmapData.value.values.map((item) => item[2]), 0)
    impactStatePrimaryChartInstance.setOption(
      {
        tooltip: { position: 'top' },
        grid: { left: 120, right: 24, top: 20, bottom: 56, containLabel: true },
        xAxis: {
          type: 'category',
          data: impactStateHeatmapData.value.xAxis,
          name: impactPayload.value?.target_parameter || '目标参数'
        },
        yAxis: { type: 'category', data: impactStateHeatmapData.value.yAxis },
        visualMap: {
          min: 0,
          max: maxValue,
          orient: 'horizontal',
          left: 'center',
          bottom: 0
        },
        series: [{
          type: 'heatmap',
          data: impactStateHeatmapData.value.values,
          label: { show: false }
        }]
      },
      true
    )
  }

  impactStatePrimaryChartInstance.resize()
}

const renderImpactVisuals = () => {
  renderImpactTrendChart()
  renderImpactSensitivityChart()
  renderImpactRangeChart()
  renderImpactStatePrimaryChart()
}

const initChart = () => {
  if (!pivotChartRef.value || !pivotData.value.length) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(pivotChartRef.value)

  const xAxisLabels = sortedPivotData.value.map(row =>
    filterForm.rowDimensions.map(dim => row._row_keys[dim] || '').join(' / ')
  )

  if (filterForm.designPoints.length === 1) {
    // 单参数：经典柱状/折线图，每列一个系列
    const primaryParam = filterForm.designPoints[0]
    const series = dynamicColumns.value.map(col => ({
      name: col,
      type: chartType.value,
      data: sortedPivotData.value.map(row => {
        const val = row[col] ? row[col][primaryParam] : 0
        return parseFloat(val) || 0
      }),
      smooth: true,
      barMaxWidth: 50,
      label: { show: true, position: 'top', formatter: p => p.value > 0 ? p.value.toFixed(1) : '' }
    }))

    chartInstance.setOption({
      title: { text: `【${primaryParam}】跨型号对比`, left: 'center', textStyle: { fontSize: 16, color: '#334155' } },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { bottom: 5, type: 'scroll', textStyle: { color: '#64748b' } },
      grid: { left: '2%', right: '3%', bottom: '12%', containLabel: true },
      xAxis: { type: 'category', data: xAxisLabels, axisLabel: { interval: 0, rotate: 20, color: '#64748b' } },
      yAxis: { type: 'value', name: primaryParam, splitLine: { lineStyle: { type: 'dashed' } } },
      series,
      color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899']
    })
  } else {
    // 多参数：分组柱状/多系列折线，每参数一个色系
    const paramColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899']

    if (chartType.value === 'bar') {
      // 分组柱状图：每个参数一个系列，每列一个簇
      const series = filterForm.designPoints.map((param, pIdx) => {
        const color = paramColors[pIdx % paramColors.length]
        return {
          name: param,
          type: 'bar',
          barGap: '5%',
          barCategoryGap: '30%',
          data: dynamicColumns.value.map(col => {
            const val = sortedPivotData.value.reduce((sum, row) => {
              return sum + (parseFloat(row[col]?.[param]) || 0)
            }, 0) / Math.max(dynamicColumns.value.length, 1)
            return parseFloat(val.toFixed(2)) || 0
          }),
          itemStyle: { color, borderRadius: [4, 4, 0, 0] },
          label: { show: true, position: 'top', formatter: p => p.value > 0 ? p.value.toFixed(1) : '', fontSize: 9 }
        }
      })

      chartInstance.setOption({
        title: { text: '多参数综合对比 (均值)', left: 'center', textStyle: { fontSize: 16, color: '#334155' } },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: params => {
          const parts = params.map(p => `${p.marker} ${p.seriesName}: <b>${p.value}</b>`).join('<br/>')
          return `<b>${params[0].axisValue}</b><br/>${parts}`
        }},
        legend: { bottom: 5, type: 'scroll', textStyle: { color: '#64748b' } },
        grid: { left: '2%', right: '3%', bottom: '12%', containLabel: true },
        xAxis: { type: 'category', data: dynamicColumns.value, axisLabel: { interval: 0, rotate: 15, color: '#64748b' } },
        yAxis: { type: 'value', name: '参数均值', splitLine: { lineStyle: { type: 'dashed' } } },
        series,
        color: paramColors
      })
    } else {
      // 折线图：每个参数一条线，X轴为产品型号
      const series = filterForm.designPoints.map((param, pIdx) => {
        const color = paramColors[pIdx % paramColors.length]
        return {
          name: param,
          type: 'line',
          data: sortedPivotData.value.map(row => {
            const vals = dynamicColumns.value.map(col => parseFloat(row[col]?.[param]) || 0)
            return vals.reduce((a, b) => a + b, 0) / Math.max(vals.length, 1)
          }),
          smooth: true,
          lineStyle: { width: 2, color },
          itemStyle: { color },
          areaStyle: { color, opacity: 0.08 },
          label: { show: true, position: 'top', formatter: p => p.value > 0 ? p.value.toFixed(1) : '', fontSize: 9 }
        }
      })

      chartInstance.setOption({
        title: { text: '多参数趋势对比 (按型号)', left: 'center', textStyle: { fontSize: 16, color: '#334155' } },
        tooltip: { trigger: 'axis', formatter: params => {
          const parts = params.map(p => `${p.marker} ${p.seriesName}: <b>${p.value}</b>`).join('<br/>')
          return `<b>${params[0].axisValue}</b><br/>${parts}`
        }},
        legend: { bottom: 5, type: 'scroll', textStyle: { color: '#64748b' } },
        grid: { left: '2%', right: '3%', bottom: '12%', containLabel: true },
        xAxis: { type: 'category', data: xAxisLabels, axisLabel: { interval: 0, rotate: 20, color: '#64748b' } },
        yAxis: { type: 'value', name: '参数均值', splitLine: { lineStyle: { type: 'dashed' } } },
        series,
        color: paramColors
      })
    }
  }
}

const exportData = () => {
  if (!pivotData.value.length) return
  const wsData = []
  const header = [...filterForm.rowDimensions.map(d => dimensionLabels[d])]
  dynamicColumns.value.forEach(c => {
    filterForm.designPoints.forEach(v => header.push(`${c}-${v}`))
  })
  wsData.push(header)

  sortedPivotData.value.forEach(row => {
    const rowData = filterForm.rowDimensions.map(d => row._row_keys[d])
    dynamicColumns.value.forEach(c => {
      filterForm.designPoints.forEach(v => rowData.push(row[c] ? row[c][v] : ''))
    })
    wsData.push(rowData)
  })

  const ws = XLSX.utils.aoa_to_sheet(wsData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '对比数据')
  XLSX.writeFile(wb, `参数对比报表_${new Date().getTime()}.xlsx`)
}

watch(activeTab, (value) => {
  if (value === 'formula-impact' && impactForm.targetParameter && !impactPayload.value) {
    loadImpactRows()
  }
  if (value === 'formula-impact') {
    renderImpactVisuals()
  }
})

watch(impactPayload, () => {
  syncSelectedImpactResults()
  syncImpactStateDefaultFilter()
  renderImpactVisuals()
}, { deep: true })

watch(selectedImpactResults, () => {
  renderImpactTrendChart()
}, { deep: true })

watch(
  () => [impactViewMode.value, impactStateAppliedFilter.value, impactStateChartMode.value],
  () => {
    if (activeTab.value === 'formula-impact') {
      renderImpactStatePrimaryChart()
    }
  },
  { deep: true }
)

onBeforeUnmount(() => {
  impactTrendChartInstance?.dispose()
  impactTrendChartInstance = null
  impactSensitivityChartInstance?.dispose()
  impactSensitivityChartInstance = null
  impactRangeChartInstance?.dispose()
  impactRangeChartInstance = null
  impactStatePrimaryChartInstance?.dispose()
  impactStatePrimaryChartInstance = null
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

onMounted(() => {
  fetchCustomData()
  hydrateImpactContext()
  if (activeTab.value === 'formula-impact' && impactForm.targetParameter) {
    loadImpactRows()
  }
})
</script>

<style scoped>
.design-point-compare { padding: 20px; background: #f8fafc; min-height: calc(100vh - 60px); }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.title-group { display: flex; align-items: center; gap: 10px; color: #1e293b; }
.title { font-size: 18px; font-weight: bold; }

.filter-bar { background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e2e8f0; }

.chart-section { 
  background: #fff; 
  padding: 20px; 
  border-radius: 8px; 
  border: 1px solid #e2e8f0;
  margin-bottom: 20px;
}
.chart-header { display: flex; justify-content: flex-end; margin-bottom: 10px; }
.single-chart { height: 450px; width: 100%; }

.table-section { background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 40px; }
.impact-section { display: grid; gap: 16px; padding: 8px 0 24px; }
.impact-form { gap: 8px 0; }
.table-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.section-title { font-weight: bold; color: #475569; border-left: 4px solid #3b82f6; padding-left: 10px; margin-bottom: 0; }

.full-width-table { width: 100%; }
:deep(.el-table__body-wrapper) { overflow-x: auto; }

.dim-label { font-weight: 500; color: #1e293b; }
.value-cell { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.value-text { font-family: 'Consolas', monospace; color: #94a3b8; }
.value-text.has-val { color: #3b82f6; font-weight: bold; font-size: 14px; }
.guidance-tags { display: flex; gap: 4px; justify-content: flex-end; width: 100%; }
.toolbar-actions { display: flex; align-items: center; }

:deep(.compare-table .el-table__header th) { background-color: #f1f5f9; color: #475569; }

/* 影响分析新增样式 */
.impact-results { display: flex; flex-direction: column; gap: 16px; }
.impact-view-switch,
.impact-toolbar-card,
.impact-trend-panel,
.impact-metric-card,
.impact-state-filter-card,
.impact-state-primary-card,
.impact-path,
.impact-samples,
.impact-state-table {
  background: #fff;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}
.impact-view-switch {
  display: flex;
  justify-content: flex-start;
}
.impact-toolbar-card {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}
.impact-toolbar-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.impact-toolbar-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}
.impact-toolbar-subtitle {
  font-size: 13px;
  color: #64748b;
}
.impact-result-select {
  width: 320px;
  max-width: 100%;
}
.impact-trend-panel {
  display: grid;
  gap: 12px;
}
.impact-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.impact-panel-header h4,
.impact-path h4,
.impact-samples h4 {
  margin: 0;
  color: #1e293b;
}
.impact-panel-header span {
  font-size: 12px;
  color: #64748b;
}
.impact-metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.impact-state-panel {
  display: grid;
  gap: 16px;
}
.impact-state-filter-form {
  margin-top: 12px;
}
.impact-state-filter-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
}
.impact-range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}
.impact-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}
.impact-state-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}
.impact-state-summary-card {
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  padding: 12px 14px;
}
.impact-state-summary-card__title {
  font-size: 13px;
  color: #64748b;
}
.impact-state-summary-card__value {
  margin-top: 8px;
  font-size: 20px;
  font-weight: 700;
  color: #1d4ed8;
}
.impact-state-summary-card__meta {
  margin-top: 8px;
  font-size: 12px;
  color: #475569;
}
.impact-summary-tile {
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}
.impact-summary-tile:hover {
  border-color: #93c5fd;
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.1);
  transform: translateY(-1px);
}
.impact-summary-tile__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}
.impact-summary-tile__title {
  font-weight: 600;
  color: #1e293b;
}
.impact-summary-tile__baseline {
  margin-top: 10px;
  font-size: 18px;
  font-weight: 700;
  color: #2563eb;
}
.impact-summary-tile__metrics {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: #475569;
}
.impact-trend-chart {
  width: 100%;
  height: 380px;
}
.impact-state-primary-chart {
  width: 100%;
  height: 380px;
}
.impact-mini-chart {
  width: 100%;
  height: 240px;
}
.dep-tag { margin-right: 5px; margin-bottom: 5px; }

@media (max-width: 960px) {
  .impact-toolbar-card,
  .impact-panel-header {
    flex-direction: column;
    align-items: stretch;
  }

  .impact-result-select {
    width: 100%;
  }

  .impact-metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
