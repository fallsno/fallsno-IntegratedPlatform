<template>
  <div class="smart-selection-panel">
    <div class="selection-results-toolbar">
      <div class="config-group">
        <span class="group-label">选型表</span>
        <span class="selection-category-tag">{{ categoryLabel }}</span>
      </div>
      <div v-if="isGearmotorCategory" class="config-group">
        <span class="group-label">系列</span>
        <el-select v-model="form.mainSeries" size="small" class="compact-select" @change="handleMainSeriesChange">
          <el-option label="R系列" value="R" />
          <el-option label="F系列" value="F" />
          <el-option label="K系列" value="K" />
          <el-option label="S系列" value="S" />
          <el-option label="W系列" value="W" />
        </el-select>
        <el-select v-model="form.subSeries" size="small" class="compact-select" placeholder="子系列">
          <el-option v-for="sub in availableSubSeries" :key="sub.value" :label="sub.label" :value="sub.value" />
        </el-select>
      </div>
      <div class="config-group">
        <span class="group-label">范围</span>
        <el-input-number v-model="form.tolerance" :min="1" :max="80" :step="1" size="small" class="tolerance-input" />
        <span class="group-label">%</span>
      </div>
      <el-button type="primary" size="small" :loading="loading" @click="fetchRecommendations" class="action-btn">执行选型</el-button>
    </div>

    <div v-if="activeRequirementRows.length" class="requirement-summary">
      <div v-for="row in activeRequirementRows" :key="row.key" class="requirement-chip">
        <span class="requirement-chip__label">{{ row.label }}</span>
        <span class="requirement-chip__value">{{ row.valueText }}</span>
      </div>
    </div>

    <div v-if="currentEquipment && currentEquipment.specific_model" class="current-selection-banner">
      <div class="selection-status">
        <div class="selection-status__main">
          <el-icon class="status-icon"><CircleCheckFilled /></el-icon>
          <span>当前已应用选型</span>
          <strong class="model-text">{{ currentEquipment.specific_model }}</strong>
        </div>
        <el-button type="danger" size="small" link @click="clearCurrentEquipment">清除方案</el-button>
      </div>
      <div class="selection-specs">
        <span v-for="row in buildDisplaySpecRows(currentEquipment)" :key="row.key">{{ row.label }}: {{ row.valueText }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton animated :rows="4" />
    </div>
    <div v-else-if="recommendations.length > 0" class="recommendation-grid">
      <div class="selection-result-table">
        <div class="selection-result-table__head">
          <div class="col col-model">型号 / 系列</div>
          <div class="col col-score">匹配度</div>
          <div class="col col-action"></div>
        </div>
        <div
          v-for="(rec, index) in recommendations"
          :key="`${rec.model_name}-${index}`"
          class="selection-result-card"
          @click="handleApplyModel(rec)"
        >
          <div class="rec-card__primary">
            <div class="col col-model">
              <el-tooltip
                effect="dark"
                placement="right"
                :show-after="380"
                :disabled="!rec.reason"
              >
                <template #content>
                  <div class="rec-tooltip">
                    <div class="rec-tooltip__title">匹配详情</div>
                    <div class="rec-tooltip__body">{{ rec.reason }}</div>
                  </div>
                </template>
                <div class="model-cell">
                  <span class="rank-badge" :class="`rank-${index + 1}`">#{{ index + 1 }}</span>
                  <span class="model-name">{{ rec.model_name || rec.item?.model_name }}</span>
                  <el-tag size="small" type="success" effect="plain" v-if="rec.exactMatch">命中</el-tag>
                </div>
              </el-tooltip>
            </div>
            <div class="col col-score">
              <el-tag :type="getScoreType(rec.score)" size="small" effect="dark" class="score-tag">{{ Number(rec.score).toFixed(0) }}%</el-tag>
            </div>
            <div class="col col-action">
              <el-button type="primary" size="small" @click.stop="handleApplyModel(rec)">应用</el-button>
            </div>
          </div>
          <div v-if="rec.changedSpecs && rec.changedSpecs.length" class="rec-card__changes">
            <span class="rec-card__changes-label">应用后变化</span>
            <span
              v-for="row in rec.changedSpecs.slice(0, 4)"
              :key="`${rec.model_name}-${row.key}`"
              class="rec-card__change-chip"
            >
              {{ row.label }}: {{ row.previousText }} -> {{ row.valueText }}
            </span>
          </div>
          <div class="rec-card__specs">
            <div
              v-for="row in rec.displaySpecs"
              :key="row.key"
              class="spec-chip"
              :class="{ 'is-pass': row.pass, 'is-fail': !row.pass, 'is-changed': row.changed, 'is-primary': row.priority === 1 }"
            >
              <div class="spec-chip__main">
                <span class="spec-chip__label">{{ row.label }}</span>
                <span class="spec-chip__divider"></span>
                <span class="spec-chip__value">{{ row.valueText }}</span>
                <span v-if="row.priority" class="spec-chip__priority">P{{ row.priority }}</span>
              </div>
              <div v-if="row.changed" class="spec-chip__change-note">当前 {{ row.previousText }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="emptyDiagnosis.code !== 'none'" class="empty-diagnosis">
      <div class="empty-diagnosis__card">
        <div class="empty-diagnosis__header">
          <div class="empty-diagnosis__icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
          </div>
          <div class="empty-diagnosis__title">{{ emptyDiagnosis.title }}</div>
        </div>
        <div class="empty-diagnosis__details">
          <div v-for="(line, idx) in emptyDiagnosis.details" :key="idx" class="empty-diagnosis__line">{{ line }}</div>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">
      <el-empty description="先配置映射字段，再点击“执行选型”获取最接近的候选设备" :image-size="80" />
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { CircleCheckFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { fetchEquipmentItems, fetchGearmotorCatalogItems } from '../api/equipmentCatalog'

const props = defineProps({
  selectionCategory: {
    type: Object,
    default: () => ({ code: 'gearmotor', label: '减速电机', categoryId: null })
  },
  fieldSchema: {
    type: Array,
    default: () => []
  },
  mappedParams: {
    type: Object,
    default: () => ({})
  },
  mappingConfigs: {
    type: Object,
    default: () => ({})
  },
  currentEquipment: {
    type: Object,
    default: () => null
  }
})

const emit = defineEmits(['apply-equipment', 'clear-equipment'])

const loading = ref(false)
const recommendations = ref([])
const gearmotorCatalog = ref([])
const genericCatalogCache = ref({})
const emptyDiagnosis = ref({ code: 'none', title: '', details: [] })

const form = reactive({
  mainSeries: 'F',
  subSeries: 'F',
  tolerance: 15
})

const subSeriesMap = {
  R: [
    { label: 'R系列', value: 'R' },
    { label: 'RX系列', value: 'RX' },
    { label: 'RF系列', value: 'RF' },
    { label: 'RXF系列', value: 'RXF' }
  ],
  F: [
    { label: 'F系列', value: 'F' },
    { label: 'FA系列', value: 'FA' },
    { label: 'FF系列', value: 'FF' },
    { label: 'FAF系列', value: 'FAF' }
  ],
  K: [
    { label: 'K系列', value: 'K' },
    { label: 'KA系列', value: 'KA' },
    { label: 'KF系列', value: 'KF' },
    { label: 'KAF系列', value: 'KAF' }
  ],
  S: [
    { label: 'S系列', value: 'S' },
    { label: 'SA系列', value: 'SA' },
    { label: 'SF系列', value: 'SF' },
    { label: 'SAF系列', value: 'SAF' }
  ],
  W: [
    { label: 'W系列', value: 'W' },
    { label: 'WA系列', value: 'WA' },
    { label: 'WF系列', value: 'WF' },
    { label: 'WAF系列', value: 'WAF' }
  ]
}

const availableSubSeries = computed(() => subSeriesMap[form.mainSeries] || [])
const categoryLabel = computed(() => String(props.selectionCategory?.label || props.selectionCategory?.code || '未命名选型').trim() || '未命名选型')
const categoryCode = computed(() => String(props.selectionCategory?.code || 'gearmotor').trim() || 'gearmotor')
const isGearmotorCategory = computed(() => categoryCode.value === 'gearmotor')
const normalizeFieldPriority = (field, index = 0) => {
  const rawPriority = Number(field?.priority)
  if (Number.isFinite(rawPriority) && rawPriority > 0) return Math.min(99, Math.max(1, Math.round(rawPriority)))
  return index + 1
}
const normalizeMappingConfigEntry = (entry, fieldType = 'numeric') => {
  if (typeof entry === 'string') {
    return {
      source_type: 'parameter',
      parameter_code: String(entry || '').trim(),
      reference_value: fieldType === 'string' ? '' : ''
    }
  }
  if (!entry || typeof entry !== 'object') {
    return {
      source_type: 'parameter',
      parameter_code: '',
      reference_value: fieldType === 'string' ? '' : ''
    }
  }
  const sourceType = String(entry.source_type || entry.sourceType || '').trim() === 'manual' ? 'manual' : 'parameter'
  const parameterCode = String(entry.parameter_code ?? entry.parameterCode ?? entry.source_parameter ?? '').trim()
  const rawReferenceValue = entry.reference_value ?? entry.referenceValue ?? entry.manual_value ?? ''
  return {
    source_type: sourceType,
    parameter_code: parameterCode,
    reference_value: String(fieldType || 'numeric').trim() === 'string'
      ? String(rawReferenceValue ?? '').trim()
      : (rawReferenceValue === '' || rawReferenceValue === null || rawReferenceValue === undefined
        ? ''
        : Number.isFinite(Number(rawReferenceValue)) ? Number(rawReferenceValue) : '')
  }
}
const hasMappingConfigValue = (entry, fieldType = 'numeric') => {
  const normalizedEntry = normalizeMappingConfigEntry(entry, fieldType)
  if (normalizedEntry.source_type === 'manual') {
    if (String(fieldType || 'numeric').trim() === 'string') {
      return normalizedEntry.reference_value !== ''
    }
    return normalizedEntry.reference_value !== ''
  }
  return Boolean(normalizedEntry.parameter_code)
}

const activeRequirementRows = computed(() => {
  return (Array.isArray(props.fieldSchema) ? props.fieldSchema : [])
    .map((field) => {
      if (!hasMappingConfigValue(props.mappingConfigs?.[field.key], field.type)) return null
      const rawValue = props.mappedParams?.[field.key]
      if (String(field?.type || 'numeric').trim() === 'string') {
        const textValue = String(rawValue ?? '').trim()
        if (!textValue) return null
        return {
          key: field.key,
          label: field.label || field.key,
          valueText: textValue
        }
      }
      const value = toFiniteNumber(rawValue)
      if (!Number.isFinite(value)) return null
      return {
        key: field.key,
        label: field.label || field.key,
        valueText: formatMetricText(value, field.unit)
      }
    })
    .filter(Boolean)
})

const handleMainSeriesChange = (val) => {
  form.subSeries = (subSeriesMap[val] || [])[0]?.value || val
}

const clearCurrentEquipment = () => {
  emit('clear-equipment')
}

const toFiniteNumber = (value) => {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

const formatMetricText = (value, unit = '') => {
  if (!Number.isFinite(Number(value))) return '-'
  const numeric = Number(value)
  const text = `${numeric}`.includes('.') ? numeric.toFixed(4).replace(/\.?0+$/, '') : String(numeric)
  return [text, unit].filter(Boolean).join(' ')
}
const numericValuesEqual = (left, right) => {
  if (!Number.isFinite(Number(left)) || !Number.isFinite(Number(right))) return false
  return Math.abs(Number(left) - Number(right)) <= Math.max(1e-6, Math.abs(Number(right)) * 1e-6)
}
const normalizeTextValue = (value) => String(value ?? '').trim().toLowerCase()
const buildCurrentEquipmentValueMap = computed(() => {
  const valueMap = new Map()
  ;(Array.isArray(props.fieldSchema) ? props.fieldSchema : []).forEach((field, index) => {
    const candidateValue = resolveFieldValue(props.currentEquipment, field)
    if (candidateValue === null || candidateValue === undefined || candidateValue === '') return
    valueMap.set(String(field?.key || '').trim(), {
      value: candidateValue,
      text: String(field?.type || 'numeric').trim() === 'string'
        ? String(candidateValue)
        : formatMetricText(candidateValue, field.unit),
      priority: normalizeFieldPriority(field, index)
    })
  })
  return valueMap
})

const resolveFieldValue = (item, field) => {
  const specs = item?.specs || item?.item?.specs || {}
  const specCandidates = [
    field.source_spec,
    field.specKey,
    ...(Array.isArray(field.specKeys) ? field.specKeys : [])
  ].map((name) => String(name || '').trim()).filter(Boolean)

  for (const key of specCandidates) {
    if (String(field?.type || 'numeric').trim() === 'string') {
      const directText = String(item?.[key] ?? '').trim()
      if (directText) return directText
      const specText = String(specs?.[key] ?? '').trim()
      if (specText) return specText
    } else {
      const direct = toFiniteNumber(item?.[key])
      if (Number.isFinite(direct)) return direct

      const specValue = toFiniteNumber(specs?.[key])
      if (Number.isFinite(specValue)) return specValue
    }

    if (key === 'power_kw') {
      const value = toFiniteNumber(item?.power ?? specs?.power_kw)
      if (Number.isFinite(value)) return value
    }
    if (key === 'speed_rpm') {
      const value = toFiniteNumber(item?.speed ?? specs?.speed_rpm ?? specs?.output_speed_rpm)
      if (Number.isFinite(value)) return value
    }
    if (key === 'torque_nm') {
      const value = toFiniteNumber(item?.torque ?? specs?.torque_nm)
      if (Number.isFinite(value)) return value
    }
    if (key === 'service_factor') {
      const value = toFiniteNumber(item?.fB ?? specs?.service_factor)
      if (Number.isFinite(value)) return value
    }
    if (key === 'ratio') {
      const value = toFiniteNumber(item?.ratio ?? specs?.ratio)
      if (Number.isFinite(value)) return value
    }
  }
  return null
}

const scoreField = (field, requirementValue, candidateValue) => {
  const normalizedType = String(field?.type || 'numeric').trim()
  const compareMode = String(field?.compare || 'near').trim()

  if (normalizedType === 'string') {
    const expectedText = String(requirementValue ?? '').trim()
    const actualText = String(candidateValue ?? '').trim()
    if (!expectedText || !actualText) {
      return { compared: false, pass: false, score: 0, distanceSortValue: Number.POSITIVE_INFINITY }
    }
    const matches = compareMode === 'eq'
      ? actualText.toLowerCase() === expectedText.toLowerCase()
      : actualText.toLowerCase().includes(expectedText.toLowerCase()) || expectedText.toLowerCase().includes(actualText.toLowerCase())
    return {
      compared: true,
      pass: matches,
      score: matches ? 100 : 0,
      distanceSortValue: matches ? 0 : 1000
    }
  }

  if (!Number.isFinite(requirementValue) || !Number.isFinite(candidateValue)) {
    return { compared: false, pass: false, score: 0, distanceSortValue: Number.POSITIVE_INFINITY }
  }

  const toleranceRatio = Math.max(Number(field.tolerance ?? field.tolerancePercent ?? form.tolerance ?? 15), 0) / 100
  const base = Math.max(Math.abs(requirementValue), 1)
  const diffRatio = Math.abs(candidateValue - requirementValue) / base

  if (compareMode === 'ge') {
    if (candidateValue >= requirementValue) {
      const surplusRatio = (candidateValue - requirementValue) / base
      return {
        compared: true,
        pass: true,
        score: Math.max(65, 100 - surplusRatio * 40),
        distanceSortValue: surplusRatio
      }
    }
    return {
      compared: true,
      pass: false,
      score: toleranceRatio <= 0 ? 0 : Math.max(0, 70 - (diffRatio / toleranceRatio) * 70),
      distanceSortValue: 100 + diffRatio
    }
  }

  if (compareMode === 'le') {
    if (candidateValue <= requirementValue) {
      const marginRatio = (requirementValue - candidateValue) / base
      return {
        compared: true,
        pass: true,
        score: Math.max(65, 100 - marginRatio * 40),
        distanceSortValue: marginRatio
      }
    }
    return {
      compared: true,
      pass: false,
      score: toleranceRatio <= 0 ? 0 : Math.max(0, 70 - (diffRatio / toleranceRatio) * 70),
      distanceSortValue: 100 + diffRatio
    }
  }

  if (compareMode === 'eq') {
    return {
      compared: true,
      pass: diffRatio === 0,
      score: diffRatio === 0 ? 100 : 0,
      distanceSortValue: diffRatio === 0 ? 0 : 1000 + diffRatio
    }
  }

  return {
    compared: true,
    pass: toleranceRatio <= 0 ? diffRatio === 0 : diffRatio <= toleranceRatio,
    score: toleranceRatio <= 0 ? (diffRatio === 0 ? 100 : 0) : Math.max(0, 100 - (diffRatio / toleranceRatio) * 100),
    distanceSortValue: diffRatio
  }
}

const evaluateCandidate = (item) => {
  const activeFields = (Array.isArray(props.fieldSchema) ? props.fieldSchema : [])
    .map((field, index) => {
      const requirementValue = String(field?.type || 'numeric').trim() === 'string'
        ? String(props.mappedParams?.[field.key] ?? '').trim()
        : toFiniteNumber(props.mappedParams?.[field.key])
      const candidateValue = resolveFieldValue(item, field)
      const fieldScore = scoreField(field, requirementValue, candidateValue)
      const currentValueMeta = buildCurrentEquipmentValueMap.value.get(String(field.key || '').trim())
      const changed = currentValueMeta
        ? (String(field?.type || 'numeric').trim() === 'string'
          ? normalizeTextValue(currentValueMeta.value) !== normalizeTextValue(candidateValue)
          : !numericValuesEqual(currentValueMeta.value, candidateValue))
        : false
      return {
        key: field.key,
        label: field.label || field.key,
        unit: field.unit || '',
        weight: Math.max(Number(field.weight || 0), 0),
        priority: normalizeFieldPriority(field, index),
        hardConstraint: Boolean(field.hard_constraint),
        requirementValue,
        candidateValue,
        compared: fieldScore.compared,
        pass: fieldScore.pass,
        score: fieldScore.score,
        distanceSortValue: Number.isFinite(fieldScore.distanceSortValue) ? fieldScore.distanceSortValue : Number.POSITIVE_INFINITY,
        changed,
        previousText: currentValueMeta?.text || ''
      }
    })
    .filter((field) => field.compared)
    .sort((left, right) => {
      if (left.priority !== right.priority) return left.priority - right.priority
      return String(left.label || '').localeCompare(String(right.label || ''), 'zh-CN')
    })

  if (!activeFields.length) return null

  const hardConstraintFailed = activeFields.some((field) => field.hardConstraint && !field.pass)
  if (hardConstraintFailed) return null

  const totalWeight = activeFields.reduce((sum, field) => sum + field.weight, 0) || 1
  const totalScore = activeFields.reduce((sum, field) => sum + (field.score * field.weight), 0) / totalWeight
  const exactMatch = activeFields.every((field) => field.pass)

  return {
    exactMatch,
    score: Math.max(0, Math.min(100, totalScore)),
    displaySpecs: activeFields.map((field) => ({
      key: field.key,
      label: field.label,
      pass: field.pass,
      priority: field.priority,
      changed: field.changed,
      previousText: field.previousText,
      valueText: formatMetricText(field.candidateValue, field.unit)
    })),
    comparisonSignature: activeFields.map((field) => ({
      key: field.key,
      priority: field.priority,
      pass: field.pass,
      distanceSortValue: field.distanceSortValue,
      score: field.score
    })),
    changedSpecs: activeFields.filter((field) => field.changed).map((field) => ({
      key: field.key,
      label: field.label,
      previousText: field.previousText || '-',
      valueText: formatMetricText(field.candidateValue, field.unit)
    })),
    reason: activeFields
      .map((field) => `P${field.priority} ${field.label} 需求 ${formatMetricText(field.requirementValue, field.unit)}，候选 ${formatMetricText(field.candidateValue, field.unit)}`)
      .join('；')
  }
}

const buildDisplaySpecRows = (item) => {
  return (Array.isArray(props.fieldSchema) ? props.fieldSchema : [])
    .map((field) => {
      const value = resolveFieldValue(item, field)
      if (String(field?.type || 'numeric').trim() === 'string') {
        if (!String(value ?? '').trim()) return null
        return {
          key: field.key,
          label: field.label || field.key,
          valueText: String(value)
        }
      }
      if (!Number.isFinite(value)) return null
      return {
        key: field.key,
        label: field.label || field.key,
        valueText: formatMetricText(value, field.unit)
      }
    })
    .filter(Boolean)
}

const buildUniqueModelName = (item) => {
  if (isGearmotorCategory.value && item.base_size && form.subSeries) {
    return `${form.subSeries}${item.base_size} ${item.motor_params?.model || ''}`.trim()
  }
  return String(item.model_name || item.item?.model_name || '').trim()
}
const buildRecommendationDedupKey = (candidate) => {
  const modelName = String(candidate?.model_name || candidate?.item?.model_name || '').trim().toLowerCase()
  const specSignature = (Array.isArray(candidate?.displaySpecs) ? candidate.displaySpecs : [])
    .map((row) => `${String(row?.key || '').trim()}:${String(row?.valueText || '').trim()}`)
    .sort((left, right) => left.localeCompare(right, 'zh-CN'))
    .join('|')
  const scoreSignature = `${Number(candidate?.score || 0).toFixed(4)}|${candidate?.exactMatch ? '1' : '0'}`
  return [modelName, specSignature, scoreSignature].join('||')
}
const dedupeRecommendations = (candidates = []) => {
  const uniqueCandidates = []
  const signatureSet = new Set()
  ;(Array.isArray(candidates) ? candidates : []).forEach((candidate) => {
    const dedupKey = buildRecommendationDedupKey(candidate)
    if (!dedupKey || signatureSet.has(dedupKey)) return
    signatureSet.add(dedupKey)
    uniqueCandidates.push(candidate)
  })
  return uniqueCandidates
}
const compareRecommendations = (left, right) => {
  const leftSignature = Array.isArray(left?.comparisonSignature) ? left.comparisonSignature : []
  const rightSignature = Array.isArray(right?.comparisonSignature) ? right.comparisonSignature : []
  const maxLength = Math.max(leftSignature.length, rightSignature.length)
  for (let index = 0; index < maxLength; index += 1) {
    const leftField = leftSignature[index]
    const rightField = rightSignature[index]
    if (!leftField && rightField) return 1
    if (leftField && !rightField) return -1
    if (!leftField || !rightField) continue
    if (leftField.pass !== rightField.pass) return Number(rightField.pass) - Number(leftField.pass)
    if (leftField.distanceSortValue !== rightField.distanceSortValue) return leftField.distanceSortValue - rightField.distanceSortValue
    if (leftField.score !== rightField.score) return rightField.score - leftField.score
  }
  if (left.exactMatch !== right.exactMatch) return Number(right.exactMatch) - Number(left.exactMatch)
  if (left.score !== right.score) return right.score - left.score
  return String(left.model_name || '').localeCompare(String(right.model_name || ''), 'zh-CN')
}

const ensureCatalogLoaded = async () => {
  if (isGearmotorCategory.value) {
    if (!gearmotorCatalog.value.length) {
      gearmotorCatalog.value = await fetchGearmotorCatalogItems()
    }
    return gearmotorCatalog.value
  }

  const categoryId = Number(props.selectionCategory?.categoryId || 0)
  if (!categoryId) return []
  if (!Array.isArray(genericCatalogCache.value[categoryId])) {
    genericCatalogCache.value[categoryId] = await fetchEquipmentItems({ categoryId })
  }
  return genericCatalogCache.value[categoryId] || []
}

const fetchRecommendations = async () => {
  emptyDiagnosis.value = { code: 'none', title: '', details: [] }
  recommendations.value = []

  const mappedFields = (Array.isArray(props.fieldSchema) ? props.fieldSchema : [])
    .filter((field) => {
      return hasMappingConfigValue(props.mappingConfigs?.[field.key], field.type)
    })

  if (!mappedFields.length) {
    emptyDiagnosis.value = {
      code: 'no_mapping',
      title: '尚未配置参数映射',
      details: [
        '请在上方「选型配置表」中，为至少一个选型项选择参数，或填写参考值。',
        '系统将根据参数值或手填参考值，从选型表中检索最匹配的候选型号。'
      ]
    }
    ElMessage.warning('请先为选型项配置参数或参考值')
    return
  }

  const validRequirementFields = mappedFields.filter((field) => {
    const rawValue = props.mappedParams?.[field.key]
    const mappingEntry = normalizeMappingConfigEntry(props.mappingConfigs?.[field.key], field.type)
    const isStringType = String(field?.type || 'numeric').trim() === 'string'
    if (isStringType) {
      return String(rawValue ?? '').trim() !== ''
    }
    const numeric = toFiniteNumber(rawValue)
    if (mappingEntry.source_type === 'manual') {
      return Number.isFinite(numeric)
    }
    return Number.isFinite(numeric) && numeric !== 0
  })

  if (!validRequirementFields.length) {
    emptyDiagnosis.value = {
      code: 'empty_requirement',
      title: '映射的计算参数无有效值',
      details: [
        '已配置参数或参考值，但当前没有可比较的有效输入。',
        '如果来源是参数，请先执行一次「计算」，确保结果已生成后再执行选型。',
        '如果来源是参考值，请检查填写内容是否为空。'
      ]
    }
    ElMessage.warning('当前选型项没有可比较的有效输入值')
    return
  }

  loading.value = true
  try {
    const rows = await ensureCatalogLoaded()

    if (!rows.length) {
      emptyDiagnosis.value = {
        code: 'no_catalog',
        title: '当前选型表无数据',
        details: [
          `「${categoryLabel.value}」分类下暂未录入设备型号数据。`,
          '请联系管理员在设备库中添加该分类的型号，或切换到其他选型表。'
        ]
      }
      ElMessage.warning('当前选型表无可用设备数据')
      loading.value = false
      return
    }

    const seriesFilteredRows = rows.filter((item) => {
      if (!isGearmotorCategory.value) return true
      return Array.isArray(item.available_types) ? item.available_types.includes(form.subSeries) : true
    })

    if (!seriesFilteredRows.length) {
      emptyDiagnosis.value = {
        code: 'series_filter_empty',
        title: '所选系列无匹配型号',
        details: [
          `当前「${form.mainSeries} / ${form.subSeries}」系列过滤后为空。`,
          '可以尝试切换系列或子系列，或扩大选型范围。'
        ]
      }
      loading.value = false
      return
    }

    let hardConstraintRejectCount = 0
    let typeMismatchCount = 0
    let noCandidateValueCount = 0

    const evaluated = seriesFilteredRows.map((item) => {
      const fieldEvaluations = (Array.isArray(props.fieldSchema) ? props.fieldSchema : [])
        .map((field) => {
          const requirementValue = String(field?.type || 'numeric').trim() === 'string'
            ? String(props.mappedParams?.[field.key] ?? '').trim()
            : toFiniteNumber(props.mappedParams?.[field.key])
          const candidateValue = resolveFieldValue(item, field)
          const fieldScore = scoreField(field, requirementValue, candidateValue)
          return {
            key: field.key,
            hardConstraint: Boolean(field.hard_constraint),
            compared: fieldScore.compared,
            pass: fieldScore.pass,
            requirementValue,
            candidateValue,
            type: String(field?.type || 'numeric').trim()
          }
        })

      const hasCompared = fieldEvaluations.some((f) => f.compared)
      if (!hasCompared) {
        noCandidateValueCount++
        return null
      }

      const hardFailed = fieldEvaluations.some((f) => f.hardConstraint && !f.pass)
      if (hardFailed) {
        hardConstraintRejectCount++
        return null
      }

      const evaluation = evaluateCandidate(item)
      if (!evaluation) {
        typeMismatchCount++
        return null
      }
      return {
        ...item,
        ...evaluation,
        model_name: buildUniqueModelName(item),
        specific_model: buildUniqueModelName(item),
        selection_category: categoryCode.value
      }
    })

    const candidates = dedupeRecommendations(
      evaluated
      .filter(Boolean)
      .sort(compareRecommendations)
    )

    recommendations.value = candidates.slice(0, 12)

    if (!recommendations.value.length) {
      const diagnosisDetails = []
      if (hardConstraintRejectCount > 0) {
        diagnosisDetails.push(`• 硬性约束淘汰：${hardConstraintRejectCount} 项（不满足「强制」勾选的选型项）`)
      }
      if (noCandidateValueCount > 0) {
        diagnosisDetails.push(`• 候选值缺失：${noCandidateValueCount} 项（选型表中对应列为空）`)
      }
      if (typeMismatchCount > 0) {
        diagnosisDetails.push(`• 类型比较失败：${typeMismatchCount} 项（数值/文本规则与候选值不兼容）`)
      }
      if (!diagnosisDetails.length) {
        diagnosisDetails.push('• 所有候选在比较规则下得分过低，未达到纳入范围')
      }
      emptyDiagnosis.value = {
        code: 'all_filtered',
        title: '未找到满足条件的候选项',
        details: [
          `已扫描 ${seriesFilteredRows.length} 项，全部被过滤。原因如下：`,
          ...diagnosisDetails,
          '建议：放宽「范围 %」或取消部分「强制」约束后重试。'
        ]
      }
      ElMessage.info('当前选型条件下无可匹配候选项，已给出诊断原因')
    } else {
      ElMessage.success(`已找到 ${recommendations.value.length} 个最接近的候选项`)
    }
  } catch (error) {
    console.error('获取推荐失败:', error)
    emptyDiagnosis.value = {
      code: 'network_error',
      title: '检索选型表失败',
      details: [
        '网络请求或后端接口异常。',
        '请检查网络连接或稍后重试。'
      ]
    }
    ElMessage.error('检索选型表失败，请检查配置或网络')
  } finally {
    loading.value = false
  }
}

const handleApplyModel = (row) => {
  ElMessage.success(`已应用具体型号: ${row.model_name}`)
  emit('apply-equipment', {
    ...row,
    specific_model: row.model_name,
    selection_category: categoryCode.value
  })
}

const getScoreType = (score) => {
  if (score >= 85) return 'success'
  if (score >= 65) return 'warning'
  return 'info'
}
</script>

<style scoped>
.smart-selection-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background-color: transparent;
  padding: 0;
}

.selection-results-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border: 1px solid #dbe3ef;
  border-radius: 10px;
  padding: 10px 12px;
  flex-wrap: wrap;
  gap: 12px;
}

.config-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}

.selection-category-tag {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  color: #0f172a;
  font-size: 12px;
}

.compact-select {
  width: 110px;
}

.tolerance-input {
  width: 88px;
}

.requirement-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.requirement-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid #dbe3ef;
  border-radius: 6px;
  background: #f8fafc;
  font-size: 12px;
}

.requirement-chip__label {
  color: #64748b;
}

.requirement-chip__value {
  color: #0f172a;
  font-weight: 600;
}

.current-selection-banner {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  padding: 12px;
}

.selection-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 13px;
  color: #065f46;
}

.status-icon {
  font-size: 16px;
  color: #10b981;
}

.selection-status__main {
  display: flex;
  align-items: center;
  gap: 6px;
}

.model-text {
  font-family: monospace;
  font-size: 14px;
  color: #047857;
}

.selection-specs {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #064e3b;
  font-family: monospace;
  background: rgba(16, 185, 129, 0.1);
  padding: 6px 10px;
  border-radius: 4px;
}

.recommendation-grid {
  display: flex;
  flex-direction: column;
}

.selection-result-table {
  display: flex;
  flex-direction: column;
  border: 1px solid #dbe3ef;
  border-radius: 10px;
  background: #ffffff;
  overflow: hidden;
}

.selection-result-table__head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 100px 90px;
  gap: 12px;
  align-items: center;
  padding: 10px 14px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.2px;
}

.selection-result-table__head .col {
  min-width: 0;
}

.selection-result-table__head .col.col-action {
  text-align: right;
}

.selection-result-card {
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #eef2f7;
  cursor: pointer;
  transition: background 0.18s ease, box-shadow 0.18s ease;
}

.selection-result-card:last-child {
  border-bottom: none;
}

.selection-result-card:hover {
  background: linear-gradient(180deg, #f8fbff 0%, #f0f7ff 100%);
  box-shadow: inset 3px 0 0 #3b82f6;
}

.rec-card__primary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 100px 90px;
  gap: 12px;
  align-items: center;
  padding: 12px 14px 8px;
}

.rec-card__changes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 14px 8px;
}

.rec-card__changes-label {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 700;
}

.rec-card__change-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: #f8fbff;
  color: #1e40af;
  font-size: 11px;
  line-height: 1.4;
}

.rec-card__primary .col {
  min-width: 0;
}

.rec-card__primary .col.col-action {
  display: flex;
  justify-content: flex-end;
}

.model-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.rank-badge {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 3px 8px;
  border-radius: 5px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.rank-1 { color: #0f766e; background: #ccfbf1; }
.rank-2 { color: #1d4ed8; background: #dbeafe; }
.rank-3 { color: #9a3412; background: #ffedd5; }

.model-name {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.15px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.score-tag {
  font-weight: 700;
  letter-spacing: 0.3px;
  padding: 4px 10px;
  min-width: 56px;
  text-align: center;
}

.rec-card__specs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
  padding: 0 14px 12px;
}

.spec-chip {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 12px;
  border-radius: 7px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  min-width: 0;
  transition: all 0.15s ease;
}

.spec-chip.is-pass {
  background: linear-gradient(180deg, #f0fdf4 0%, #dcfce7 100%);
  border-color: #86efac;
}

.spec-chip.is-fail {
  background: linear-gradient(180deg, #fef2f2 0%, #fee2e2 100%);
  border-color: #fca5a5;
}

.spec-chip.is-changed {
  border-color: #93c5fd;
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.12);
}

.spec-chip.is-primary {
  box-shadow: inset 2px 0 0 #1d4ed8;
}

.spec-chip__main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.spec-chip__label {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  white-space: nowrap;
}

.is-pass .spec-chip__label { color: #166534; }
.is-fail .spec-chip__label { color: #991b1b; }

.spec-chip__divider {
  flex-shrink: 0;
  width: 1px;
  height: 14px;
  background: #cbd5e1;
}

.is-pass .spec-chip__divider { background: #86efac; }
.is-fail .spec-chip__divider { background: #fca5a5; }

.spec-chip__value {
  flex: 1 1 auto;
  min-width: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  text-align: right;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.is-pass .spec-chip__value { color: #15803d; }
.is-fail .spec-chip__value { color: #b91c1c; }

.spec-chip__priority {
  margin-left: auto;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  min-height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
  color: #334155;
  font-size: 10px;
  font-weight: 700;
}

.spec-chip__change-note {
  padding-left: 2px;
  font-size: 11px;
  line-height: 1.4;
  color: #1d4ed8;
}

.rec-tooltip {
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rec-tooltip__title {
  font-size: 13px;
  font-weight: 700;
  color: #fef3c7;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  padding-bottom: 6px;
}

.rec-tooltip__body {
  font-size: 12px;
  line-height: 1.75;
  color: #e2e8f0;
  white-space: pre-line;
}

.text-success {
  color: #10b981 !important;
}

.text-warning {
  color: #f59e0b !important;
}

.rec-action {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}

.spec-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-family: monospace;
  font-size: 14px;
  background: #f8fafc;
  padding: 6px 8px;
  border-radius: 4px;
}

.spec-cell .lbl {
  color: #64748b;
  font-size: 11px;
}

.spec-cell .val {
  color: #1e293b;
  font-weight: 600;
}

.empty-diagnosis {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.empty-diagnosis__card {
  width: 100%;
  border: 1px solid #fde68a;
  border-radius: 10px;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  padding: 16px 18px;
}

.empty-diagnosis__header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.empty-diagnosis__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(245, 158, 11, 0.15);
  color: #d97706;
  flex-shrink: 0;
}

.empty-diagnosis__title {
  font-size: 14px;
  font-weight: 700;
  color: #92400e;
  line-height: 1.4;
}

.empty-diagnosis__details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.empty-diagnosis__line {
  font-size: 12px;
  line-height: 1.6;
  color: #78350f;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
</style>
