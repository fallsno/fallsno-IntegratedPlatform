<template>
  <el-dialog
    v-model="dialogVisible"
    title="补齐参数映射"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-alert
      title="请为以下来源于其他型号的基础参数，在当前型号参数中心中选择对应的映射参数。"
      type="info"
      show-icon
      :closable="false"
      class="mb-4"
    />

    <el-table :data="localMappings" border style="width: 100%" row-class-name="mapping-row">
      <el-table-column prop="source_param_name" label="来源变量名" width="160" />
      <el-table-column label="当前状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.mapping_status === 'ready' ? 'success' : 'danger'" size="small">
            {{ row.mapping_status === 'ready' ? '已绑定' : '待补映射' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="目标参数绑定" min-width="200">
        <template #default="{ row }">
          <el-select
            v-model="row.target_parameter_id"
            placeholder="请选择"
            filterable
            style="width: 100%"
            @change="(val) => handleTargetChange(row, val)"
          >
            <el-option
              v-for="opt in row.candidate_parameters || []"
              :key="opt.id"
              :label="opt.param_name"
              :value="opt.id"
            />
          </el-select>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="saving" :disabled="!canSave" @click="handleSave">保存映射</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { saveFormulaParamMappings } from '@/api/drumDesign'

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
  },
  mappings: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'saved'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const localMappings = ref([])
const saving = ref(false)

watch(() => props.mappings, (newVal) => {
  localMappings.value = JSON.parse(JSON.stringify(newVal))
}, { immediate: true, deep: true })

const canSave = computed(() => {
  // Can save if any change or all are resolved
  return localMappings.value.every(m => m.target_parameter_id)
})

const handleTargetChange = (row, val) => {
  const candidate = (row.candidate_parameters || []).find(c => c.id === val)
  if (candidate) {
    row.target_param_name = candidate.param_name
    row.mapping_status = 'ready'
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    const payload = localMappings.value.map(m => ({
      source_param_name: m.source_param_name,
      target_parameter_id: m.target_parameter_id,
      target_param_name: m.target_param_name
    }))
    
    await saveFormulaParamMappings(props.modelId, props.moduleCode, payload)
    ElMessage.success('映射保存成功')
    dialogVisible.value = false
    emit('saved')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '映射保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.mb-4 {
  margin-bottom: 16px;
}
</style>
