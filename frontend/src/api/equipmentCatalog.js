import axios from 'axios'

export async function fetchEquipmentCategories() {
  const { data } = await axios.get('/equipment/categories')
  return Array.isArray(data) ? data : []
}

export async function fetchEquipmentItems({ categoryId, queryStr } = {}) {
  try {
    const { data } = await axios.get('/equipment/items', {
      params: {
        ...(categoryId ? { category_id: categoryId } : {}),
        ...(queryStr ? { query_str: queryStr } : {})
      }
    })
    return Array.isArray(data) ? data : []
  } catch (error) {
    console.error('Failed to fetch equipment items:', error)
    return []
  }
}

export function buildGenericEquipmentItem(item = {}) {
  const specs = item.specs || {}
  return {
    id: item.id,
    model_name: item.model_name,
    brand: item.brand || '',
    category_id: item.category_id,
    specs
  }
}

function normalizeGearmotorItem(item = {}) {
  const specs = item.specs || {}
  const gearbox = String(specs.gearbox || '').trim() || String(item.model_name || '').split(' ')[0] || ''
  let motor = String(specs.motor || '').trim() || String(item.model_name || '').split(' ').slice(1).join(' ') || ''
  
  if (motor) {
    const motorParts = motor.split(/\s+/)
    if (motorParts.length > 1 && motorParts[0].toUpperCase() === motorParts[1].substring(0, motorParts[0].length).toUpperCase()) {
      motor = motorParts.slice(1).join(' ')
    }
  }
  
  const modelMatch = String(item.model_name || '').match(/^(\S+)\s+(.+?)-([\d.]+)$/)
  const ratioFromModel = modelMatch ? Number(modelMatch[3]) : null

  return {
    id: item.id,
    model_name: item.model_name,
    available_types: ['F', 'FA', 'FF', 'FAF'],
    base_size: gearbox.replace(/^F/i, ''),
    power: Number(specs.power_kw || 0),
    speed: Number(specs.speed_rpm || 0),
    torque: Number(specs.torque_nm || 0),
    fB: Number(specs.service_factor || 0),
    fra: Number(specs.radial_load_n || 0),
    weight: Number(specs.weight_kg || specs.mass_kg || 0),
    ratio: Number(specs.ratio || ratioFromModel || 0),
    reducer_params: {
      ratio: Number(specs.ratio || ratioFromModel || 0),
      efficiency: specs.efficiency || '96%',
      input_speed: Number(specs.input_speed_rpm || specs.motor_speed_rpm || 0),
      max_torque: Number(specs.torque_nm || 0),
      fra: Number(specs.radial_load_n || 0),
      weight: Number(specs.weight_kg || specs.mass_kg || 0),
      model: ['F/FA/FF/FAF', gearbox.replace(/^F/i, '')].filter(Boolean).join(' ')
    },
    motor_params: {
      model: motor.replace(/\s+/g, ''),
      power: Number(specs.power_kw || 0),
      speed: Number(specs.motor_speed_rpm || specs.input_speed_rpm || 1450),
      voltage: specs.voltage || '380V/50Hz',
      protection: specs.protection || 'IP55'
    },
    item
  }
}

function buildGearmotorDedupKey(item = {}) {
  const modelName = String(item.model_name || '').trim().toUpperCase()
  const baseSize = String(item.base_size || '').trim().toUpperCase()
  const motorModel = String(item.motor_params?.model || '').trim().toUpperCase()
  const numericFields = [
    Number(item.power || 0),
    Number(item.speed || 0),
    Number(item.torque || 0),
    Number(item.fB || 0),
    Number(item.fra || 0),
    Number(item.weight || 0),
    Number(item.ratio || 0)
  ].map((value) => (Number.isFinite(value) ? value.toFixed(6) : '0'))

  return [modelName, baseSize, motorModel, ...numericFields].join('|')
}

function dedupeGearmotorItems(items = []) {
  const uniqueItems = []
  const seen = new Set()

  ;(Array.isArray(items) ? items : []).forEach((item) => {
    const dedupKey = buildGearmotorDedupKey(item)
    if (!dedupKey || seen.has(dedupKey)) return
    seen.add(dedupKey)
    uniqueItems.push(item)
  })

  return uniqueItems
}

export async function fetchGearmotorCatalogItems() {
  try {
    const { data } = await axios.get('/equipment/items')

    return dedupeGearmotorItems(
      (Array.isArray(data) ? data : [])
      .filter(item => {
        const catCode = item.category?.code || ''
        const categoryId = Number(item.category_id || item.category?.id || 0)
        const specs = item?.specs || {}
        const series = String(specs.series || '').toUpperCase()
        const gearbox = String(specs.gearbox || '').toUpperCase()
        const modelName = String(item?.model_name || '').toUpperCase()
        const isRightCategory = catCode === 'gearmotor' || categoryId === 6
        const isFSeries = series === 'F' || gearbox.startsWith('F') || modelName.startsWith('F')
        return isRightCategory && isFSeries
      })
      .map(normalizeGearmotorItem)
    )
      .sort((a, b) => {
        if (a.power !== b.power) return a.power - b.power
        if (a.speed !== b.speed) return a.speed - b.speed
        return a.ratio - b.ratio
      })
  } catch (error) {
    console.error('Failed to fetch gearmotor catalog items:', error)
    return []
  }
}

export async function fetchMotorCatalogItems(queryStr) {
  const { data } = await axios.get('/equipment/items', {
    params: {
      query_str: queryStr
    }
  })
  return (Array.isArray(data) ? data : []).filter(item => {
    const specs = item?.specs || {}
    return Number(specs.power_kw || 0) > 0 && Number(specs.speed_rpm || 0) > 0
  })
}
