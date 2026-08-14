<template>
  <el-card class="parameter-panel" shadow="never">
    <template #header>
      <div class="header-row">
        <div class="title">{{ panelTitle || '步骤参数区' }}</div>
        <div class="header-actions">
          <el-button v-if="mappings.length > 0" type="warning" text @click="emit('open-mapping')">补齐参数映射</el-button>
          <el-button type="primary" text :loading="saving" @click="emit('sync')">回写参数中心矩阵</el-button>
        </div>
      </div>
    </template>

    <el-empty
      v-if="!hasExplanation && !hasLegacyData"
      description="请选择设计步骤查看计算理由"
    />

    <div v-if="hasExplanation" class="explanation-section">
      <div class="section-title">步骤目的</div>
      <el-input
        type="textarea"
        :rows="3"
        resize="vertical"
        :model-value="explanation.purpose"
        @input="handleExplanationChange('purpose', $event)"
      />

      <div class="section-title">关键输入</div>
      <div v-if="explanation.keyInputs.length" class="parameter-list">
        <div
          v-for="input in explanation.keyInputs"
          :key="input.paramName"
          class="parameter-row"
        >
          <div class="parameter-row__meta">
            <span class="parameter-row__name">{{ input.paramName }}</span>
            <el-tag size="small" :type="resolveSourceTagType(input.source)" class="ml-2">{{ input.source }}</el-tag>
          </div>
          <div class="parameter-row__value">
            <span class="value-text">{{ input.value }}</span>
            <span class="value-unit">{{ input.unit || '-' }}</span>
          </div>
        </div>
      </div>
      <div v-else class="empty-hint">暂无关键输入数据</div>

      <div class="section-title">推导关系</div>
      <div class="explanation-content">{{ explanation.derivation }}</div>

      <div class="section-title">结果与影响</div>
      <el-input
        type="textarea"
        :rows="3"
        resize="vertical"
        :model-value="explanation.impact"
        @input="handleExplanationChange('impact', $event)"
      />
    </div>

    <template v-else-if="hasLegacyData">
    <div v-if="summaryItems.length" class="parameter-section">
      <div class="section-title">结论摘要</div>
      <ul class="plain-list">
        <li v-for="item in summaryItems" :key="item">{{ item }}</li>
      </ul>
    </div>

    <div v-if="baseRows.length" class="parameter-section">
      <div class="section-title">关键参数</div>
      <div class="parameter-list">
        <div
          v-for="row in baseRows"
          :key="`${row.parameterId}-${row.paramName}`"
          class="parameter-row"
          :class="buildBaseRowStateClass(row)"
        >
          <div class="parameter-row__meta">
            <el-tooltip :content="buildBaseRowTooltip(row)" placement="top">
              <span class="parameter-row__name">{{ row.paramName }}</span>
            </el-tooltip>
            <el-tag 
              v-if="getMappingFor(row.paramName)" 
              size="small" 
              :type="getMappingFor(row.paramName).mapping_status === 'ready' ? 'info' : 'danger'"
              class="ml-2"
            >
              {{ getMappingFor(row.paramName).mapping_status === 'ready' ? `绑: ${getMappingFor(row.paramName).target_param_name}` : '待补映射' }}
            </el-tag>
          </div>
          <div class="parameter-row__control">
            <el-input 
              :model-value="row.value" 
              @input="handleInputChange(row, $event)"
            />
            <div class="parameter-row__suffix">
              <span>{{ row.unitCode || '-' }}</span>
              <!-- 智能选型推荐入口 (遵循弱干扰原则，Hover显示) -->
              <el-popover
                v-if="row.equipmentRecommendations && row.equipmentRecommendations.length > 0"
                placement="left-start"
                :width="360"
                trigger="click"
                popper-class="clean-recommendation-popper"
              >
                <template #reference>
                  <el-button link class="magic-stick-btn">
                    <el-icon><MagicStick /></el-icon>
                  </el-button>
                </template>
                <div class="equipment-recommendation-panel">
                  <div class="recommendation-header">
                    <span class="header-title">智能推荐选型</span>
                    <span class="header-count">{{ row.equipmentRecommendations.length }} 个方案</span>
                  </div>
                  <div class="recommendation-list">
                    <div 
                      v-for="(item, index) in row.equipmentRecommendations" 
                      :key="index"
                      class="recommendation-item"
                      @click="handleApplyRecommendation(row, item)"
                    >
                      <div class="item-main">
                        <span class="item-model">{{ item.model_name }}</span>
                        <span class="item-brand">{{ item.brand || '通用' }}</span>
                      </div>
                      <div class="item-specs">
                        <span v-for="(val, key) in item.specs" :key="key" class="spec-text">
                          <span class="spec-label">{{ key }}:</span> {{ val }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </el-popover>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="lookupSourceRows.length" class="parameter-section">
      <div class="section-title">查询依据</div>
      <div class="parameter-list">
        <button
          v-for="row in lookupSourceRows"
          :key="row.key"
          type="button"
          class="intermediate-row intermediate-row--lookup"
          :disabled="!row.jumpable"
          @click="handleLookupClick(row)"
        >
          <span class="parameter-row__name">{{ row.lookupName }}</span>
          <div class="intermediate-row__content">
            <span class="intermediate-row__value">{{ row.rangeText }}</span>
            <span class="parameter-row__hint">{{ row.detailText }}</span>
          </div>
        </button>
      </div>
    </div>

    <div v-if="constraintItems.length" class="parameter-section">
      <div class="section-title">约束条件</div>
      <ul class="plain-list">
        <li v-for="item in constraintItems" :key="item">{{ item }}</li>
      </ul>
    </div>
    </template>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'

const props = defineProps({
  panelTitle: {
    type: String,
    default: ''
  },
  explanation: {
    type: Object,
    default: () => ({
      purpose: '',
      keyInputs: [],
      derivation: '',
      impact: ''
    })
  },
  summaryItems: {
    type: Array,
    default: () => []
  },
  baseRows: {
    type: Array,
    default: () => []
  },
  lookupSourceRows: {
    type: Array,
    default: () => []
  },
  constraintItems: {
    type: Array,
    default: () => []
  },
  mappings: {
    type: Array,
    default: () => []
  },
  saving: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'update:data', 
  'sync', 
  'open-mapping', 
  'jump-lookup',
  'update-explanation',
  'apply-equipment'
])


const handleInputChange = (row, value) => {
  emit('change', row, value)
}

const handleLookupClick = (row) => {
  emit('jump-lookup', row)
}

const handleExplanationChange = (field, value) => {
  emit('update-explanation', { field, value })
}

const handleApplyRecommendation = (row, item) => {
  emit('apply-equipment', item)
}

const hasExplanation = computed(() =>
  Boolean(
    props.explanation &&
    (
      props.explanation.purpose ||
      props.explanation.derivation ||
      props.explanation.impact ||
      props.explanation.keyInputs?.length
    )
  )
)

const hasLegacyData = computed(() =>
  props.summaryItems.length || props.baseRows.length || props.lookupSourceRows.length || props.constraintItems.length
)

const getMappingFor = (paramName) => {
  return props.mappings.find(m => m.source_param_name === paramName)
}

const rowSourceSummaryMap = {
  model: '型号值',
  snapshot: '草稿值',
  matrix: '矩阵值',
  draft: '本次值',
  empty: '待补充',
  missing: '缺参'
}

const resolveSourceTagType = (sourceText) => {
  if (sourceText === '产品参数') return 'primary'
  if (sourceText === '环境参数') return 'success'
  if (sourceText === '查表/经验依据') return 'warning'
  return 'info'
}

const buildBaseRowTooltip = (row) => {
  const segments = []
  if (row.isReferenced) segments.push('已引用')
  if (row.pendingCreate) segments.push('未建项')
  if (row.defaultValue) segments.push(`默认 ${row.defaultValue}`)
  if (row.dirty) segments.push('已修改')
  if (row.source) segments.push(rowSourceSummaryMap[row.source] || row.source)
  return segments.join(' · ') || row.paramName
}

const buildBaseRowStateClass = (row) => ({
  'parameter-row--dirty': !!row.dirty,
  'parameter-row--pending': !!row.pendingCreate,
  'parameter-row--missing': row.source === 'missing'
})

</script>

<style scoped>
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.parameter-section + .parameter-section {
  margin-top: 18px;
}

.explanation-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.explanation-content {
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 10px;
  border-left: 4px solid #3b82f6;
  color: #334155;
  line-height: 1.6;
}

.plain-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 8px;
  color: #334155;
}

.parameter-list {
  display: grid;
  gap: 12px;
}

.parameter-row {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #f8fafc;
}

.parameter-row--dirty {
  border-color: #f59e0b;
  background: #fffbeb;
}

.parameter-row--pending,
.parameter-row--missing {
  border-color: #fbbf24;
}

.parameter-row__meta {
  display: flex;
  align-items: center;
  min-width: 0;
}

.parameter-row__name {
  display: inline-flex;
  max-width: 100%;
  font-weight: 700;
  color: #0f172a;
  word-break: break-word;
}

.ml-2 {
  margin-left: 8px;
}

.parameter-row__control {
  margin-top: 10px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.parameter-row__suffix {
  display: flex;
  align-items: center;
  gap: 8px;
}

.parameter-row__suffix span {
  text-align: right;
  font-size: 12px;
  color: #64748b;
}

.parameter-row__value {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.value-text {
  font-weight: 700;
  color: #0f172a;
}

.value-unit {
  font-size: 12px;
  color: #64748b;
}

.empty-hint {
  padding: 12px 16px;
  background: #f1f5f9;
  border-radius: 10px;
  color: #64748b;
  text-align: center;
}

.intermediate-row--lookup {
  border-color: #c7d2fe;
  background: #eef2ff;
}

.intermediate-row--lookup:hover {
  border-color: #818cf8;
  box-shadow: 0 10px 24px rgba(129, 140, 248, 0.14);
}

.intermediate-row--lookup:disabled,
.intermediate-row--lookup:disabled:hover {
  cursor: not-allowed;
  opacity: 0.72;
  border-color: #c7d2fe;
  box-shadow: none;
}

.intermediate-row__content {
  margin-top: 10px;
  display: grid;
  gap: 6px;
}

.intermediate-row__value {
  font-weight: 700;
  color: #0f172a;
}

.parameter-row__hint {
  font-size: 12px;
  color: #475569;
}

/* 智能选型推荐样式 (遵循克制与弱干扰) */
.magic-stick-btn {
  font-size: 14px;
  padding: 4px;
  color: #94a3b8;
  opacity: 0;
  transition: opacity 0.2s, color 0.2s;
}

.parameter-row:hover .magic-stick-btn {
  opacity: 1;
}

.magic-stick-btn:hover {
  color: #3b82f6;
}

.equipment-recommendation-panel {
  display: flex;
  flex-direction: column;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.header-title {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.header-count {
  font-size: 12px;
  color: #64748b;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  max-height: 250px;
  overflow-y: auto;
}

.recommendation-item {
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.recommendation-item:hover {
  background-color: #f1f5f9;
}

.item-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.item-model {
  font-family: monospace;
  font-weight: 600;
  font-size: 13px;
  color: #0f172a;
}

.item-brand {
  font-size: 11px;
  color: #64748b;
  background: #e2e8f0;
  padding: 1px 6px;
  border-radius: 10px;
}

.item-specs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
}

.spec-text {
  color: #334155;
}

.spec-label {
  color: #94a3b8;
}
</style>
