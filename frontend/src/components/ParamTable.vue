<template>
  <div>
    <el-button type="primary" size="small" @click="addParam" style="margin-bottom: 10px">
      <el-icon><Plus /></el-icon>新增参数
    </el-button>

    <el-table :data="parameters" border>
      <el-table-column prop="param_name" label="参数名称">
        <template #default="{ row }">
          <el-input v-if="row.editing" v-model="row.param_name" size="small" />
          <span v-else>{{ row.param_name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="param_value" label="参数值">
        <template #default="{ row }">
          <el-input v-if="row.editing" v-model="row.param_value" size="small" />
          <span v-else>{{ row.param_value || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="param_unit" label="单位" width="100">
        <template #default="{ row }">
          <el-input v-if="row.editing" v-model="row.param_unit" size="small" />
          <span v-else>{{ row.param_unit || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row, $index }">
          <template v-if="!row.editing">
            <el-button link type="primary" @click="editRow(row)">编辑</el-button>
            <el-button link type="danger" @click="deleteParam(row.id)">删除</el-button>
          </template>
          <template v-else>
            <el-button link type="success" @click="saveRow(row)">保存</el-button>
            <el-button link type="info" @click="cancelEdit(row)">取消</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps(['partId', 'parameters'])
const emit = defineEmits(['refresh'])

const parameters = ref(props.parameters || [])

const addParam = () => {
  parameters.value.push({
    param_name: '',
    param_value: '',
    param_unit: '',
    editing: true,
    isNew: true
  })
}

const editRow = (row) => {
  row.editing = true
  row._backup = { ...row }
}

const cancelEdit = (row) => {
  if (row.isNew) {
    parameters.value = parameters.value.filter(p => p !== row)
  } else {
    Object.assign(row, row._backup)
    row.editing = false
  }
}

const saveRow = async (row) => {
  try {
    if (row.isNew) {
      await axios.post(`/versions/parts/${props.partId}/parameters`, {
        param_name: row.param_name,
        param_value: row.param_value,
        param_unit: row.param_unit
      })
      ElMessage.success('参数已添加')
      emit('refresh')
    } else {
      await axios.put(`/versions/parameters/${row.id}`, {
        param_name: row.param_name,
        param_value: row.param_value,
        param_unit: row.param_unit
      })
      row.editing = false
      ElMessage.success('参数已更新')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const deleteParam = async (id) => {
  await axios.delete(`/versions/parameters/${id}`)
  ElMessage.success('参数已删除')
  emit('refresh')
}
</script>