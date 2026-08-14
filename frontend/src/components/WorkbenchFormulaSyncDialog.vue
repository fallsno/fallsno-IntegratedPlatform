<template>
  <el-dialog
    v-model="dialogVisible"
    title="跨型号模块同步"
    width="800px"
    :close-on-click-modal="false"
    @closed="handleClosed"
    append-to-body
  >
    <el-steps :active="currentStep" finish-status="success" align-center class="sync-steps">
      <el-step title="选择目标型号" />
      <el-step title="预检确认" />
      <el-step title="同步完成" />
    </el-steps>

    <div class="sync-body" v-loading="loading">
      <!-- Step 0: 选择目标 -->
      <div v-if="currentStep === 0" class="step-container">
        <el-alert
          title="选择要同步到的目标型号。同步后，目标型号将复用当前模块的公式逻辑，但参数取值将自动从目标型号的参数中心读取。"
          type="info"
          show-icon
          :closable="false"
          class="mb-4"
        />
        <div class="scope-selection">
          <el-radio-group v-model="scopeType" @change="handleScopeChange">
            <el-radio-button label="same_family">同系列</el-radio-button>
            <el-radio-button label="same_product_type">同产品大类</el-radio-button>
            <el-radio-button label="all">全部滚筒</el-radio-button>
          </el-radio-group>
        </div>
        <el-table
          :data="targets"
          style="width: 100%"
          @selection-change="handleTargetSelection"
          border
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="family_name" label="系列" width="180">
            <template #default="{ row }">
              {{ row.family_code || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="version_code" label="型号名称" />
          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 'ready' ? 'success' : 'info'" size="small">
                {{ row.status === 'ready' ? '就绪' : '未同步' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div class="step-actions">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :disabled="!selectedTargets.length" @click="handleNextToPreview">下一步：预检</el-button>
        </div>
      </div>

      <!-- Step 1: 预检确认 -->
      <div v-if="currentStep === 1" class="step-container">
        <div v-if="previewViewModel">
          <el-descriptions
            :title="`模块: ${previewViewModel.sourceModuleName} (包含 ${previewViewModel.formulaCount} 条公式)`"
            :column="1"
            border
            class="mb-4"
          >
            <el-descriptions-item label="目标型号">{{ selectedTargets.map(t => t.version_code).join(', ') }}</el-descriptions-item>
            <el-descriptions-item label="同步状态">
              <el-tag :type="previewViewModel.canSync ? 'success' : 'danger'">
                {{ previewViewModel.canSync ? '就绪可同步' : '存在未映射参数' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>

          <div class="mappings-section">
            <div class="mappings-title">
              待确认参数映射 
              <el-tag type="danger" size="small" round v-if="previewViewModel.unresolvedMappings.length">
                {{ previewViewModel.unresolvedMappings.length }} 项需处理
              </el-tag>
            </div>
            <el-table :data="previewViewModel.unresolvedMappings" border style="width: 100%" class="mb-4" row-class-name="unresolved-row">
              <el-table-column prop="sourceName" label="源公式参数" />
              <el-table-column label="目标型号参数">
                <template #default>
                  <span class="text-danger"><el-icon><Warning /></el-icon> 尚未映射</span>
                </template>
              </el-table-column>
            </el-table>

            <div class="mappings-title">
              已映射参数
              <el-tag type="success" size="small" round v-if="previewViewModel.resolvedMappings.length">
                {{ previewViewModel.resolvedMappings.length }} 项
              </el-tag>
            </div>
            <el-table :data="previewViewModel.resolvedMappings" border style="width: 100%">
              <el-table-column prop="sourceName" label="源公式参数" />
              <el-table-column prop="targetName" label="目标型号参数" />
              <el-table-column label="映射来源" width="120">
                <template #default="{ row }">
                  <el-tag :type="row.isAutoMapped ? 'info' : 'success'" size="small">
                    {{ row.isAutoMapped ? '同名自动映射' : '已映射' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <div class="step-actions mt-4">
          <el-button @click="currentStep = 0">上一步</el-button>
          <el-button 
            type="primary" 
            @click="handleExecuteSync"
          >
            {{ previewViewModel?.unresolvedMappings?.length ? '允许待补映射并同步' : '执行同步' }}
          </el-button>
        </div>
      </div>

      <!-- Step 2: 同步完成 -->
      <div v-if="currentStep === 2" class="step-container success-step">
        <el-result
          icon="success"
          title="同步成功"
          :sub-title="`已成功将模块同步至 ${selectedTargets.map(t => t.version_code).join(', ')}`"
        >
          <template #extra>
            <el-button @click="dialogVisible = false">关闭</el-button>
          </template>
        </el-result>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  getFormulaSyncTargets,
  previewFormulaSync,
  executeFormulaSync
} from '@/api/drumDesign'
import { buildFormulaSyncPreviewViewModel } from '@/api/drumDesign.helpers.mjs'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  modelId: {
    type: [Number, String],
    required: true
  },
  moduleCode: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'sync-success'])
const router = useRouter()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const currentStep = ref(0)
const loading = ref(false)

// Step 0 Data
const scopeType = ref('same_family')
const targets = ref([])
const selectedTargets = ref([])

// Step 1 Data
const previewViewModel = ref(null)

watch(dialogVisible, async (visible) => {
  if (visible) {
    resetState()
    await loadTargets()
  }
})

const resetState = () => {
  currentStep.value = 0
  scopeType.value = 'same_family'
  targets.value = []
  selectedTargets.value = []
  previewViewModel.value = null
}

const handleClosed = () => {
  resetState()
}

const loadTargets = async () => {
  if (!props.modelId) return
  loading.value = true
  try {
    targets.value = await getFormulaSyncTargets(props.modelId, { scope_type: scopeType.value })
  } catch (error) {
    ElMessage.error('获取目标型号失败')
  } finally {
    loading.value = false
  }
}

const handleScopeChange = () => {
  selectedTargets.value = []
  loadTargets()
}

const handleTargetSelection = (selection) => {
  selectedTargets.value = selection
}

const handleNextToPreview = async () => {
  if (!selectedTargets.value.length) return
  
  loading.value = true
  try {
    const data = await previewFormulaSync(props.modelId, props.moduleCode, selectedTargets.value.map(t => t.version_id))
    if (data) {
      previewViewModel.value = buildFormulaSyncPreviewViewModel(data)
      currentStep.value = 1
    }
  } catch (error) {
    ElMessage.error('预检失败')
  } finally {
    loading.value = false
  }
}

const handleExecuteSync = async () => {
  if (!selectedTargets.value.length) return
  
  loading.value = true
  try {
    await executeFormulaSync(props.modelId, props.moduleCode, {
      target_version_ids: selectedTargets.value.map(t => t.version_id),
      conflict_actions: [],
      allow_missing_mapping_targets: selectedTargets.value.map(t => t.version_id)
    })
    currentStep.value = 2
    emit('sync-success')
  } catch (error) {
    ElMessage.error('同步执行失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.sync-steps {
  margin-bottom: 24px;
}

.sync-body {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 10px;
}

.scope-selection {
  margin-bottom: 16px;
}

.step-container {
  display: flex;
  flex-direction: column;
}

.step-actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}

.mappings-section {
  margin-top: 16px;
}

.mappings-title {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.text-danger {
  color: #f56c6c;
  display: flex;
  align-items: center;
  gap: 4px;
}

:deep(.unresolved-row) {
  background-color: #fef0f0 !important;
}

.success-step {
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}
</style>
