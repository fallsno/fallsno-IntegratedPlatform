import assert from 'node:assert/strict'

import {
  createPendingParameterRow,
  findParameterRowIndex,
  removeParameterRow,
  resolveParameterDisplayName,
  shouldPersistParameterRow
} from './newDesignWorkbenchParameterDrafts.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('createPendingParameterRow 不把临时标识写入真实参数名', () => {
  const row = createPendingParameterRow('new_1785394904006_ro2ac')

  assert.equal(row.paramName, '')
  assert.equal(row.displayName, '')
  assert.equal(row._tempId, 'new_1785394904006_ro2ac')
  assert.equal(row.pendingCreate, true)
})

run('resolveParameterDisplayName 对未命名新增参数保持空白显示而不是回填 tempId', () => {
  const displayName = resolveParameterDisplayName(
    {
      paramName: '',
      displayName: '',
      pendingCreate: true,
      _tempId: 'new_1785394904006_ro2ac'
    },
    'new_1785394904006_ro2ac'
  )

  assert.equal(displayName, '')
})

run('shouldPersistParameterRow 只按真实参数名是否填写判断是否可保存', () => {
  assert.equal(
    shouldPersistParameterRow({
      paramName: '',
      pendingCreate: true,
      _tempId: 'new_1785394904006_ro2ac'
    }),
    false
  )

  assert.equal(
    shouldPersistParameterRow({
      paramName: 'new_实际参数',
      pendingCreate: false
    }),
    true
  )
})

run('findParameterRowIndex 优先使用 _tempId 定位未保存草稿', () => {
  const rows = [
    {
      paramName: '',
      displayName: '',
      pendingCreate: true,
      _tempId: 'new_first'
    },
    {
      paramName: '',
      displayName: '',
      pendingCreate: true,
      _tempId: 'new_second'
    }
  ]

  assert.equal(
    findParameterRowIndex(rows, {
      paramName: '',
      _tempId: 'new_second'
    }),
    1
  )
})

run('removeParameterRow 删除空名称草稿时只移除当前目标行', () => {
  const rows = [
    {
      paramName: '',
      displayName: '',
      pendingCreate: true,
      _tempId: 'new_first'
    },
    {
      paramName: '',
      displayName: '',
      pendingCreate: true,
      _tempId: 'new_second'
    },
    {
      paramName: '已命名参数',
      displayName: '已命名参数',
      pendingCreate: false
    }
  ]

  const nextRows = removeParameterRow(rows, {
    paramName: '',
    _tempId: 'new_first'
  })

  assert.deepEqual(
    nextRows.map((row) => row._tempId || row.paramName),
    ['new_second', '已命名参数']
  )
})
