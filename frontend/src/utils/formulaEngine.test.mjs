import assert from 'node:assert/strict'

import {
  evaluateFormulaExpression,
  evaluateFormulaRows,
  normalizeFormulaExpression,
  FormulaEngineError
} from './formulaEngine.mjs'

const run = (name, fn) => {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    throw error
  }
}

run('支持中文变量名与大写三角函数', () => {
  const result = evaluateFormulaExpression('=总重 kg*9.8/(4*COS(角度/2))', {
    '总重 kg': 100,
    角度: 0
  })

  assert.ok(Math.abs(result.value - 245) < 1e-10)
  assert.equal(result.formattedValue, '245')
})

run('支持全角符号、乘除号、pi 常量与幂运算', () => {
  const result = evaluateFormulaExpression('=（半径 × π ^ 2）÷ 2', {
    半径: 4
  })

  assert.ok(Math.abs(result.value - (4 * Math.PI ** 2) / 2) < 1e-10)
  assert.equal(result.normalizedExpression, '(半径*pi^2)/2')
})

run('缺失变量时自动注册为 0 并继续计算', () => {
  assert.throws(
    () => evaluateFormulaExpression('=总重 / 宽度', { 总重: 10 }),
    (error) => {
      assert.ok(error instanceof FormulaEngineError)
      assert.equal(error.code, 'RESULT_INVALID')
      return true
    }
  )
})

run('normalizeFormulaExpression 兼容常见工程写法', () => {
  assert.equal(
    normalizeFormulaExpression('=【角度】×COS（θ）＋π'),
    '(角度)*cos(θ)+pi'
  )
})

run('支持依赖参数出现在后续行时的多轮计算', () => {
  assert.equal(typeof evaluateFormulaRows, 'function')

  const rows = [
    {
      name: '托轮摩擦力矩 N.m',
      expression: '=托轮摩擦力 N*滚圈直径 mm/2/1000'
    },
    {
      name: '托轮摩擦力 N',
      expression: '=托轮正压力 N*摩擦系数μ'
    }
  ]

  evaluateFormulaRows(rows, {
    baseScope: {
      '托轮正压力 N': 77341,
      '摩擦系数μ': 0.1,
      '滚圈直径 mm': 1000
    },
    precision: 4
  })

  assert.equal(rows[0].value, '3867.05')
  assert.equal(rows[0].error, false)
  assert.equal(rows[1].value, '7734.1')
  assert.equal(rows[1].error, false)
})

run('循环依赖时返回明确的依赖链路', () => {
  const rows = [
    { name: 'A', expression: '=B+1' },
    { name: 'B', expression: '=A+1' }
  ]

  evaluateFormulaRows(rows, {
    baseScope: {},
    precision: 4,
    variableMap: {
      A: { B: '' },
      B: { A: '' }
    }
  })

  assert.equal(rows[0].error, true)
  assert.match(rows[0].errorMessage, /A -> B -> A/)
  assert.equal(rows[1].error, true)
  assert.match(rows[1].errorMessage, /B -> A -> B/)
})

run('支持 VLOOKUP 查表并返回计算结果', () => {
  const result = evaluateFormulaExpression('=142*VLOOKUP(电机频率,电机扭矩参数!B:C,2,0)', {
    电机频率: 50
  }, {
    lookupResolver: (lookupName, lookupKey, colIndex, exact) => {
      assert.equal(lookupName, '电机扭矩参数')
      assert.equal(lookupKey, '50')
      assert.equal(colIndex, 2)
      assert.equal(exact, true)
      return 1
    }
  })

  assert.equal(result.formattedValue, '142')
})

run('VLOOKUP 非精确匹配模式时报错', () => {
  assert.throws(
    () => evaluateFormulaExpression('=VLOOKUP(电机频率,电机扭矩参数!B:C,2,1)', { 电机频率: 50 }, {
      lookupResolver: () => 1
    }),
    (error) => {
      assert.ok(error instanceof FormulaEngineError)
      assert.equal(error.code, 'LOOKUP_RANGE_MODE_INVALID')
      return true
    }
  )
})

run('IFERROR 在查表失败时返回兜底值', () => {
  const result = evaluateFormulaExpression('=IFERROR(142*VLOOKUP(电机频率,电机扭矩参数!B:C,2,0),0)', {
    电机频率: 999
  }, {
    lookupResolver: () => {
      throw new FormulaEngineError('LOOKUP_NOT_FOUND', '附录“电机扭矩参数”未找到键值 999')
    }
  })

  assert.equal(result.formattedValue, '0')
})

run('支持 CURVE2D 公式语法校验', () => {
  const result = evaluateFormulaExpression('=CURVE2D(电机扭矩参数,电机频率,DRE,X2Y,LINEAR)', {
    电机频率: 32
  }, {
    curveResolver: (lookupName, inputValue, seriesKey, direction, lookupMode) => {
      assert.equal(lookupName, '电机扭矩参数')
      assert.equal(inputValue, 32)
      assert.equal(seriesKey, 'DRE')
      assert.equal(direction, 'X2Y')
      assert.equal(lookupMode, 'LINEAR')
      return 0.913
    }
  })

  assert.equal(result.formattedValue, '0.913')
})

run('CURVE2D 非法方向时报错', () => {
  assert.throws(
    () => evaluateFormulaExpression('=CURVE2D(电机扭矩参数,电机频率,DRE,XY,LINEAR)', {
      电机频率: 32
    }, {
      curveResolver: () => 0.913
    }),
    (error) => {
      assert.ok(error instanceof FormulaEngineError)
      assert.equal(error.code, 'CURVE_DIRECTION_INVALID')
      return true
    }
  )
})

run('CURVE2D 支持未初始化的合法参数输入', () => {
  const result = evaluateFormulaExpression(
    '=电机_额定转矩*CURVE2D(电机扭矩参数,电机_频率,DRN,X2Y,LINEAR)',
    {},
    {
      availableVariableNames: ['电机_额定转矩', '电机_频率'],
      curveResolver: () => 1
    }
  )
  assert.equal(result.value, 0)
})
