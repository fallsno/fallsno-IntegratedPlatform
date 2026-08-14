import assert from 'node:assert/strict'

import { buildTemplateSyncPayload } from './designPlatform.helpers.mjs'

const payload = buildTemplateSyncPayload({ sourceComponentId: 1, targetComponentId: 2 })

assert.equal(payload.source_component_id, 1)
assert.equal(payload.target_component_id, 2)
assert.equal(payload.sync_mode, 'overwrite_template_scope')

console.log('template sync helpers passed')
