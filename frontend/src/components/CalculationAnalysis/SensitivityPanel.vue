<template>
  <div class="sp-panel">
    <!-- 1. 当前结果 -->
    <div class="sp-card sp-card--result">
      <div class="sp-card__head">
        <span class="sp-card__title">当前结果</span>
      </div>
      <div class="sp-result">
        <span class="sp-result__num">{{ fmtValue(baseResult) }}</span>
        <span class="sp-result__unit">{{ targetUnit }}</span>
      </div>
      <div v-if="sensitivity?.total_delta" class="sp-result__range">
        参数波动结果区间 Δ{{ fmtValue(sensitivity.total_delta) }}
      </div>
    </div>

    <!-- 2. 参数影响贡献 -->
    <div class="sp-card sp-card--contrib">
      <div class="sp-card__head">
        <span class="sp-card__title">参数影响贡献</span>
        <span class="sp-card__meta">OAT 单因子扰动</span>
      </div>
      <div v-if="!contributions.length" class="sp-empty">执行分析后生成贡献占比</div>
      <div v-else class="sp-contribs">
        <div v-for="item in contributions" :key="item.name" class="sp-contrib">
          <div class="sp-contrib__row">
            <span class="sp-contrib__name" :title="item.name">{{ item.name }}</span>
            <span class="sp-contrib__pct">{{ fmtNum(item.contribution) }}%</span>
          </div>
          <div class="sp-contrib__bar">
            <div
              class="sp-contrib__fill"
              :style="{ width: `${Math.max(item.contribution, 2)}%` }"
            />
          </div>
          <div class="sp-contrib__delta">
            {{ fmtValue(item.min_result) }} → {{ fmtValue(item.max_result) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 3. 场景比较 -->
    <div class="sp-card sp-card--compare">
      <div class="sp-card__head">
        <span class="sp-card__title">场景比较</span>
      </div>
      <table v-if="compareRows.length" class="sp-table">
        <thead>
          <tr>
            <th>设计方案</th>
            <th class="sp-table__num">{{ targetNode }} ({{ targetUnit }})</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in compareRows"
            :key="row.name"
            :class="{ 'is-active': row.name === activeSceneName }"
          >
            <td>{{ row.name }}</td>
            <td class="sp-table__num">{{ fmtValue(row.target_value) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="sp-empty">执行分析后显示各方案结果</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  targetNode: { type: String, default: '' },
  targetUnit: { type: String, default: '' },
  sensitivity: { type: Object, default: null },
  scenarioResults: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  activeSceneName: { type: String, default: '' },
})

const baseResult = computed(() => props.sensitivity?.base_result ?? null)
const contributions = computed(() => props.sensitivity?.contributions || [])
const compareRows = computed(() =>
  props.scenarioResults.map((s) => ({ name: s.name, target_value: s.target_value }))
)

const fmtValue = (v) => {
  if (v === null || v === undefined || v === '') return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return '—'
  if (!Number.isFinite(n)) return '∞'
  if (n !== 0 && (Math.abs(n) >= 1e6 || Math.abs(n) < 1e-4)) return n.toExponential(3)
  return String(Math.round(n * 10000) / 10000)
}
const fmtNum = (v) => {
  const n = Number(v)
  if (Number.isNaN(n)) return '0'
  return String(Math.round(n * 100) / 100)
}
</script>

<style scoped>
.sp-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0d1219;
  min-height: 0;
  overflow-y: auto;
  gap: 8px;
  padding: 8px;
}
.sp-card {
  background: #111722;
  border: 1px solid #1f2833;
  border-radius: 4px;
  padding: 8px 10px;
  flex-shrink: 0;
}
.sp-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.sp-card__title {
  font-size: 11px;
  font-weight: 600;
  color: #d6deeb;
  letter-spacing: 0.5px;
}
.sp-card__meta {
  font-size: 9px;
  color: #4d5a6d;
}

/* 当前结果 */
.sp-card--result .sp-result {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.sp-result__num {
  font-size: 26px;
  font-weight: 700;
  color: #ffd7d7;
  font-variant-numeric: tabular-nums;
}
.sp-result__unit {
  font-size: 12px;
  color: #8b98a8;
}
.sp-result__range {
  margin-top: 2px;
  font-size: 10px;
  color: #eab308;
}

/* 贡献列表 */
.sp-contribs {
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.sp-contrib__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.sp-contrib__name {
  font-size: 11px;
  color: #aeb9c9;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px;
}
.sp-contrib__pct {
  font-size: 12px;
  font-weight: 700;
  color: #ff5a5a;
  font-variant-numeric: tabular-nums;
}
.sp-contrib__bar {
  height: 5px;
  background: #1c2431;
  border-radius: 2px;
  overflow: hidden;
  margin: 3px 0 2px;
}
.sp-contrib__fill {
  height: 100%;
  background: linear-gradient(90deg, #7a1616, #e23b3b);
  border-radius: 2px;
  transition: width 0.25s ease;
}
.sp-contrib__delta {
  font-size: 9px;
  color: #5d6a7c;
  font-variant-numeric: tabular-nums;
}

/* 场景比较表 */
.sp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
.sp-table th {
  text-align: left;
  color: #7c8a99;
  font-weight: 500;
  padding: 4px 6px;
  border-bottom: 1px solid #1f2833;
}
.sp-table td {
  padding: 5px 6px;
  color: #aeb9c9;
  border-bottom: 1px solid #1a222e;
}
.sp-table__num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.sp-table tr.is-active td {
  background: #241216;
  color: #ffd7d7;
}
.sp-table tr.is-active td:first-child {
  border-left: 2px solid #e23b3b;
}

.sp-empty {
  padding: 14px 0;
  text-align: center;
  font-size: 10px;
  color: #4d5a6d;
}
</style>
