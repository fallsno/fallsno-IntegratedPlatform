<template>
  <div class="catalog-explorer">
    <div class="catalog-main">
      <div class="main-header">
        <div class="header-title">
          <h2>减速电机选型参数表 (F系列平行轴)</h2>
        </div>
        <div class="header-controls">
          <el-button type="primary" plain @click="openMotorManual" style="margin-right: 20px;">
            <el-icon><Document /></el-icon> 电机技术手册
          </el-button>
          <span class="control-label">额定功率：</span>
          <el-select
            v-model="selectedPower"
            placeholder="选择功率"
            style="width: 160px; margin-right: 16px;"
          >
            <el-option
              v-for="power in powerList"
              :key="power.toString()"
              :label="power.toFixed(2) + ' kW'"
              :value="power.toString()"
            />
          </el-select>
          <el-input
            v-model="searchQuery"
            placeholder="搜索减速机机座号或电机..."
            clearable
            style="width: 250px"
            :prefix-icon="Search"
          />
        </div>
      </div>

      <el-table
        v-loading="loadingCatalog"
        :data="filteredData"
        :span-method="objectSpanMethod"
        border
        height="100%"
        style="width: 100%; flex: 1;"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 'bold' }"
      >
        <el-table-column prop="speed" label="输出转速 na [r/min]" width="140" align="center">
          <template #default="{ row }">{{ Number(row.speed || 0).toFixed(1) }}</template>
        </el-table-column>
        <el-table-column prop="torque" label="最大输出扭矩 Ma [Nm]" width="160" align="center" />
        <el-table-column prop="ratio" label="减速比 i" width="120" align="center" />
        <el-table-column prop="fB" label="服务系数 fB" width="120" align="center">
          <template #default="{ row }">
            <span :class="{'warning-text': row.fB < 1.5}">{{ Number(row.fB || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="fra" label="许用径向载荷 Fra [N]" width="180" align="center" />
        <el-table-column prop="reducer_params.model" label="减速机型号" min-width="180" align="center" />
        <el-table-column prop="motor_params.model" label="电机型号" min-width="120" align="center" />
        <el-table-column prop="weight" label="重量 m [kg]" width="100" align="center">
          <template #default="{ row }">
            {{ row.weight > 0 ? row.weight : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" plain @click="handleApplyModel(row)">
              查看电机参数
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="motorDialogVisible"
      title="电机技术参数详情"
      width="800px"
      destroy-on-close
    >
      <div v-if="motorDetails" class="motor-details-container">
        <el-descriptions title="基本参数" :column="3" border>
          <el-descriptions-item label="电机型号">{{ motorDetails.model_name }}</el-descriptions-item>
          <el-descriptions-item label="系列">{{ motorDetails.specs.series }}</el-descriptions-item>
          <el-descriptions-item label="能效等级">
            <el-tag size="small" :type="motorDetails.specs.efficiency_class === 'IE3' ? 'success' : 'info'">
              {{ motorDetails.specs.efficiency_class }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="额定功率 (PN)">{{ motorDetails.specs.power_kw }} kW</el-descriptions-item>
          <el-descriptions-item label="极数">{{ motorDetails.specs.poles || '-' }} 极</el-descriptions-item>
          <el-descriptions-item label="额定转速 (nN)">{{ motorDetails.specs.speed_rpm }} r/min</el-descriptions-item>
          <el-descriptions-item label="额定转矩 (MN)">{{ motorDetails.specs.torque_nm }} Nm</el-descriptions-item>
          <el-descriptions-item label="额定电流 (IN)">{{ motorDetails.specs.current_a || '-' }} A</el-descriptions-item>
          <el-descriptions-item label="功率因数">{{ motorDetails.specs.power_factor || '-' }}</el-descriptions-item>
          <el-descriptions-item label="100%效率">{{ motorDetails.specs.efficiency_percent || '-' }} %</el-descriptions-item>
          <el-descriptions-item label="启动电流比 (M1)">{{ motorDetails.specs.starting_current_ratio_m1 || '-' }}</el-descriptions-item>
          <el-descriptions-item label="启动电流比 (M2)">{{ motorDetails.specs.starting_current_ratio_m2 || '-' }}</el-descriptions-item>
          <el-descriptions-item label="制动器型号">{{ motorDetails.specs.brake_model || '-' }}</el-descriptions-item>
          <el-descriptions-item label="质量 (m)">{{ motorDetails.specs.mass_kg || '-' }} kg</el-descriptions-item>
          <el-descriptions-item label="转动惯量 (J)">{{ motorDetails.specs.inertia_10_4_kgm2 ? motorDetails.specs.inertia_10_4_kgm2 + ' ×10⁻⁴ kgm²' : '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="action-bar" style="margin-top: 20px; text-align: right;">
          <el-button type="success" @click="injectMotorParamsToWorkbench">
            <el-icon><Check /></el-icon> 注入设计工作台 (校核)
          </el-button>
        </div>
      </div>
      <div v-else v-loading="loadingMotor" element-loading-text="加载电机参数中..." style="min-height: 200px;">
        <el-empty v-if="!loadingMotor" description="未在数据库中找到该电机的详细参数" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Search, Document, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { fetchGearmotorCatalogItems, fetchMotorCatalogItems } from '../api/equipmentCatalog'

const router = useRouter()

const loadingCatalog = ref(false)
const catalogItems = ref([])
const powerList = ref([])
const selectedPower = ref('')
const searchQuery = ref('')

const motorDialogVisible = ref(false)
const motorDetails = ref(null)
const loadingMotor = ref(false)

async function loadCatalog() {
  loadingCatalog.value = true
  try {
    const rows = await fetchGearmotorCatalogItems()
    catalogItems.value = rows
    const powers = [...new Set(rows.map(item => item.power))].sort((a, b) => a - b)
    powerList.value = powers
    if (powers.length > 0 && !selectedPower.value) {
      selectedPower.value = powers[0].toString()
    }
  } catch (error) {
    console.error('加载减速电机目录失败:', error)
    ElMessage.error('加载减速电机目录失败')
  } finally {
    loadingCatalog.value = false
  }
}

onMounted(() => {
  loadCatalog()
})

const currentPowerData = computed(() => {
  if (!selectedPower.value) return []
  const targetPower = parseFloat(selectedPower.value)
  return catalogItems.value.filter(item => item.power === targetPower)
})

const filteredData = computed(() => {
  let data = currentPowerData.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    data = data.filter(item =>
      item.reducer_params.model.toLowerCase().includes(q) ||
      item.motor_params.model.toLowerCase().includes(q)
    )
  }
  return data
})

const spanArr = ref([])

const getSpanArr = (data) => {
  spanArr.value = []
  let pos = 0
  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      spanArr.value.push(1)
      pos = 0
    } else if (
      data[i].reducer_params.model === data[i - 1].reducer_params.model &&
      data[i].motor_params.model === data[i - 1].motor_params.model &&
      data[i].weight === data[i - 1].weight
    ) {
      spanArr.value[pos] += 1
      spanArr.value.push(0)
    } else {
      spanArr.value.push(1)
      pos = i
    }
  }
}

watch(filteredData, (newVal) => {
  getSpanArr(newVal)
}, { immediate: true })

const objectSpanMethod = ({ column, rowIndex }) => {
  if (['reducer_params.model', 'motor_params.model', 'weight'].includes(column.property)) {
    const _row = spanArr.value[rowIndex]
    const _col = _row > 0 ? 1 : 0
    return {
      rowspan: _row,
      colspan: _col
    }
  }
}

const openMotorManual = () => {
  const url = 'http://localhost:8000/static/manuals/11_DRN_电机技术手册.pdf'
  window.open(url, '_blank')
}

const handleApplyModel = async (row) => {
  motorDialogVisible.value = true
  loadingMotor.value = true
  motorDetails.value = null

  try {
    const motorModel = row.motor_params.model.trim()
    let formattedModel = motorModel
    const match = motorModel.match(/([A-Z0-9]+)(\d{2,3}[SMLH]?[A-Z]*)(\d+)/i)
    if (match) {
      formattedModel = motorModel.replace(/([A-Z]+)(\d+[SMLH]?[A-Z]*?)(\d)$/i, '$1 $2 $3')
    }

    const dataArray = await fetchMotorCatalogItems(formattedModel)
    let matchedMotor = null
    if (dataArray.length > 0) {
      matchedMotor = dataArray.find(item => item.model_name === formattedModel || item.model_name.replace(/\s+/g, '') === motorModel)
      if (!matchedMotor) matchedMotor = dataArray[0]
    }

    if (matchedMotor) {
      motorDetails.value = matchedMotor
    } else {
      ElMessage.warning(`未在数据库中找到型号 ${motorModel} (${formattedModel}) 的纯电机详细参数`)
    }
  } catch (error) {
    console.error('获取电机参数失败:', error)
    ElMessage.error('获取电机参数失败')
  } finally {
    loadingMotor.value = false
  }
}

const injectMotorParamsToWorkbench = () => {
  if (!motorDetails.value) return
  localStorage.setItem('selected_motor_for_workbench', JSON.stringify(motorDetails.value))
  motorDialogVisible.value = false
  ElMessage.success('电机参数已注入，正在跳转至设计工作台...')
  router.push('/workbench/product-select')
}
</script>

<style scoped>
.catalog-explorer {
  display: flex;
  height: 100%;
  background-color: var(--el-bg-color-page);
  border-radius: 8px;
  overflow: hidden;
}

.catalog-main {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  background-color: #fff;
}

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title h2 {
  margin: 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}

.header-controls {
  display: flex;
  align-items: center;
}

.control-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-right: 8px;
}

.warning-text {
  color: var(--el-color-danger);
  font-weight: bold;
}
</style>
