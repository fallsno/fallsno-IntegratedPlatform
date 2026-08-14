<template>
  <el-dialog :model-value="modelValue" title="模板同步预览" width="520px" @close="emit('update:modelValue', false)">
    <el-form label-width="120px">
      <el-form-item label="源部件 ID">
        <el-input-number v-model="sourceComponentId" :min="1" style="width: 100%;" />
      </el-form-item>
      <el-form-item label="目标部件 ID">
        <el-input-number v-model="targetComponentId" :min="1" style="width: 100%;" />
      </el-form-item>
      <el-form-item label="同步策略">
        <el-select v-model="syncMode" style="width: 100%;">
          <el-option label="覆盖模板范围" value="overwrite_template_scope" />
        </el-select>
      </el-form-item>
    </el-form>
    <el-alert
      title="首版支持先查看差异，再执行正式同步。冲突明细仍以摘要方式展示。"
      type="info"
      :closable="false"
      show-icon
    />
    <el-alert
      v-if="result"
      :title="result.summary.summary"
      type="success"
      :closable="false"
      show-icon
      style="margin-top: 12px;"
    />
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="emitPreview">查看差异</el-button>
      <el-button type="success" :loading="submitting" @click="handleExecute">执行同步</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { executeTemplateSync } from '@/api/designPlatform.js'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['preview', 'update:modelValue'])

const sourceComponentId = ref(1)
const targetComponentId = ref(1)
const syncMode = ref('overwrite_template_scope')
const submitting = ref(false)
const result = ref(null)

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      sourceComponentId.value = 1
      targetComponentId.value = 1
      syncMode.value = 'overwrite_template_scope'
      result.value = null
    }
  }
)

const emitPreview = () => {
  emit('preview', {
    sourceComponentId: sourceComponentId.value,
    targetComponentId: targetComponentId.value
  })
}

const handleExecute = async () => {
  submitting.value = true
  try {
    result.value = await executeTemplateSync({
      sourceComponentId: sourceComponentId.value,
      targetComponentId: targetComponentId.value,
      syncMode: syncMode.value
    })
    emitPreview()
  } catch (error) {
    console.error(error)
    ElMessage.error('执行模板同步失败')
  } finally {
    submitting.value = false
  }
}
</script>
