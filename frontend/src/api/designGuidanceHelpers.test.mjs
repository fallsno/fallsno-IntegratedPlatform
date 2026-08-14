import assert from 'node:assert/strict'

import {
  buildGuidanceActionUpdatePayload,
  getGuidanceActionStatusMeta,
  normalizeGuidanceHit,
  normalizeGuidanceSummary
} from './designPlatform.helpers.mjs'

const summary = normalizeGuidanceSummary({
  total_hits: 3,
  open_hits: 2,
  action_open_count: 4,
  action_resolved_count: 1,
  severity_stats: { high: 1, warning: 1, info: 1 }
})

assert.equal(summary.cards.length, 4)
assert.deepEqual(summary.cards[0], { key: 'total', label: '规则命中', value: 3 })
assert.deepEqual(summary.cards[2], { key: 'actionOpen', label: '待执行动作', value: 4 })
assert.deepEqual(summary.cards[3], { key: 'actionResolved', label: '已完成动作', value: 1 })

const hit = normalizeGuidanceHit({
  id: 8,
  status: 'open',
  actions: [
    { id: 1, status: 'open', action_label: '复核模板差异' },
    { id: 2, status: 'resolved', action_label: '比对目标部件' }
  ]
})
assert.equal(hit.action_count, 2)
assert.equal(hit.open_action_count, 1)

assert.deepEqual(getGuidanceActionStatusMeta('in_progress'), { type: 'warning', label: '处理中' })
assert.deepEqual(
  buildGuidanceActionUpdatePayload({
    status: 'resolved',
    resultNote: '已确认',
    resultSnapshot: { source: 'manual' }
  }),
  { status: 'resolved', result_note: '已确认', result_snapshot: { source: 'manual' } }
)

console.log('guidance helpers passed')
