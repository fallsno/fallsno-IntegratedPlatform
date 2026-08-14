<template>
  <div class="lookup-panel">
    <div class="lookup-panel__sidebar">
      <div class="lookup-panel__sidebar-header">
        <span>附录列表</span>
        <el-button type="primary" size="small" @click="$emit('create')">新增</el-button>
      </div>
      <el-menu
        :default-active="String(activeLookupId || '')"
        class="lookup-panel__menu"
      >
        <el-menu-item
          v-for="item in lookups"
          :key="item.id"
          :index="String(item.id)"
          @click="$emit('select', item)"
        >
          {{ item.lookup_name }}
        </el-menu-item>
      </el-menu>
    </div>

    <div class="lookup-panel__main">
      <div class="lookup-panel__actions">
        <el-tag v-if="activeLookupName" type="info">当前附录：{{ activeLookupName }}</el-tag>
        <span v-if="activeLookupName" class="lookup-panel__hint">公式引用：{{ activeLookupName }}!B:C</span>
        <el-button :disabled="!activeLookupId" @click="$emit('edit')">编辑附录</el-button>
        <el-button type="danger" plain :disabled="!activeLookupId" @click="$emit('delete')">删除附录</el-button>
        <el-button :disabled="!activeLookupId" @click="$emit('add-row')">新增行</el-button>
        <el-button :disabled="!activeLookupId" @click="$emit('import')">导入 Excel/粘贴</el-button>
        <el-button type="success" :disabled="!activeLookupId" @click="$emit('save-rows')">保存附录图表</el-button>
      </div>

      <el-empty v-if="!activeLookupId" description="请选择或新增一个查表附录" />

      <div v-else class="lookup-panel__workspace">
        <ParameterLookupCurvePanel
          :active-lookup-id="activeLookupId"
          :active-lookup-name="activeLookupName"
          :rows="rows"
          :profile="curveProfile"
          :saving="curveSaving"
          :visible="panelVisible"
          @change="$emit('update-curve-profile', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import ParameterLookupCurvePanel from './ParameterLookupCurvePanel.vue'

defineProps({
  lookups: {
    type: Array,
    default: () => []
  },
  rows: {
    type: Array,
    default: () => []
  },
  activeLookupId: {
    type: Number,
    default: 0
  },
  activeLookupName: {
    type: String,
    default: ''
  },
  curveProfile: {
    type: Object,
    default: () => ({})
  },
  curveSaving: {
    type: Boolean,
    default: false
  },
  panelVisible: {
    type: Boolean,
    default: true
  }
})

defineEmits([
  'create',
  'edit',
  'delete',
  'select',
  'add-row',
  'remove-row',
  'import',
  'save-rows',
  'save-curve-profile',
  'update-curve-profile'
])
</script>

<style scoped>
.lookup-panel {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 16px;
}

.lookup-panel__sidebar,
.lookup-panel__main {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.lookup-panel__sidebar-header,
.lookup-panel__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.lookup-panel__actions {
  justify-content: flex-start;
  flex-wrap: wrap;
}

.lookup-panel__hint {
  font-size: 12px;
  color: #475569;
}

.lookup-panel__workspace {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.lookup-panel__menu {
  border-right: none;
}
</style>
