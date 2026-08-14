<template>
  <div class="formula-path-bar">
    <el-tooltip content="模块" placement="top">
      <el-tag effect="plain" size="small">{{ moduleName || '-' }}</el-tag>
    </el-tooltip>
    <span class="formula-path-bar__divider">/</span>
    <el-tooltip content="场景" placement="top">
      <el-tag effect="plain" size="small" type="success">{{ sceneName || '-' }}</el-tag>
    </el-tooltip>
    <span class="formula-path-bar__divider">/</span>
    <el-tooltip content="公式" placement="top">
      <el-tag effect="plain" size="small" type="info">{{ formulaName || '-' }}</el-tag>
    </el-tooltip>
  </div>
</template>

<script setup>
defineProps({
  moduleName: {
    type: String,
    default: ''
  },
  sceneName: {
    type: String,
    default: ''
  },
  formulaName: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.formula-path-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.formula-path-bar__divider {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1;
}
</style>
