import assert from 'node:assert/strict'

import { normalizeParameterImportRows } from './designPlatform.helpers.mjs'

const rows = normalizeParameterImportRows(`ROLLER_DIAMETER,滚筒直径,basic,mm\n,空编码,basic,mm`)

assert.equal(rows.length, 2)
assert.equal(rows[0].param_code, 'ROLLER_DIAMETER')
assert.equal(rows[1].param_name, '空编码')

console.log('parameter import helpers passed')
