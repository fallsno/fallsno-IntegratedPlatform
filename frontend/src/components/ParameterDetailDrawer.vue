<template>
  <el-drawer
    :model-value="modelValue"
    :title="drawerTitle"
    size="460px"
    @close="emit('close')"
  >
    <el-form v-if="parameter" label-width="92px">
      <el-form-item label="参数编码">
        <el-input v-model="form.param_code" :disabled="!isEditMode" />
      </el-form-item>
      <el-form-item label="参数名称">
        <el-input v-model="form.param_name" :disabled="!isEditMode" />
      </el-form-item>
      <el-form-item label="显示名称">
        <el-input v-model="form.display_name" :disabled="!isEditMode" />
      </el-form-item>
      <el-form-item label="分类">
        <el-input v-model="form.category_code" :disabled="!isEditMode" />
      </el-form-item>
      <el-form-item label="单位">
        <el-input v-model="form.unit_code" :disabled="!isEditMode" />
      </el-form-item>
      <el-form-item label="值类型">
        <el-select v-model="form.value_type" :disabled="!isEditMode" style="width: 100%">
          <el-option label="基础参数" value="basic" />
          <el-option label="产品参数" value="product" />
          <el-option label="环境参数" value="environment" />
        </el-select>
      </el-form-item>
      <el-form-item label="数据类型">
        <el-input v-model="form.data_type" :disabled="!isEditMode" />
      </el-form-item>
      <el-form-item label="精度">
        <el-input-number v-model="form.precision" :min="0" :disabled="!isEditMode" />
      </el-form-item>
      <el-form-item label="默认值">
        <el-input v-model="form.default_value" :disabled="!isEditMode" />
      </el-form-item>
      <el-form-item label="状态">
        <el-input v-model="form.status" :disabled="!isEditMode" />
      </el-form-item>
      <el-form-item label="说明">
        <el-input v-model="form.description" type="textarea" :rows="3" :disabled="!isEditMode" />
      </el-form-item>
    </el-form>
    <el-empty v-else description="请选择参数查看详情" />

    <template v-if="isEditMode" #footer>
      <div class="drawer-footer">
        <el-button @click="emit('close')">取消</el-button>
        <el-button type="primary" :loading="saving" @click="emit('save', { ...form })">保存</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  parameter: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'view'
  },
  saving: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'save'])

const form = reactive({
  param_code: '',
  param_name: '',
  display_name: '',
  category_code: 'uncategorized',
  unit_code: '',
  value_type: 'basic',
  data_type: 'number',
  precision: 2,
  default_value: '',
  description: '',
  status: 'active'
})

watch(
  () => props.parameter,
  (value) => {
    Object.assign(form, {
      param_code: value?.param_code || '',
      param_name: value?.param_name || '',
      display_name: value?.display_name || value?.param_name || '',
      category_code: value?.category_code || 'uncategorized',
      unit_code: value?.unit_code || '',
      value_type: value?.value_type || 'basic',
      data_type: value?.data_type || 'number',
      precision: Number(value?.precision ?? 2),
      default_value: value?.default_value == null ? '' : String(value.default_value),
      description: value?.description || '',
      status: value?.status || 'active'
    })
  },
  { immediate: true }
)

const isEditMode = computed(() => props.mode === 'edit' || props.mode === 'create')
const drawerTitle = computed(() => {
  if (props.mode === 'create') return '新增参数'
  if (props.mode === 'edit') return '编辑参数'
  return '参数详情'
})
</script>

<style scoped>
.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
