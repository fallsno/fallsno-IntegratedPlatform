<template>
  <div class="toolbox-container">
    <h2>🛠️ 工具箱</h2>
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="tool-card" shadow="hover">
          <div class="tool-icon">
            <el-icon :size="64"><Tools /></el-icon>
          </div>
          <div class="tool-info">
            <h3>传感器数据分析工具</h3>
            <p class="version">版本 2.5.0</p>
            <p class="description">平滑滤波、波形分离、相位分析、通道差值计算</p>
          </div>
          <div class="tool-actions">
            <el-button type="primary" @click="openTool">
              <el-icon><Monitor /></el-icon>在线使用
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
const openTool = () => {
  window.open('/tools/analyzer', '_blank')
}
</script>

<style scoped>
.toolbox-container { padding: 20px; }
.tool-card { text-align: center; height: 100%; }
.tool-icon { padding: 20px 0; }
.version { color: #909399; font-size: 12px; }
.description { color: #606266; margin: 10px 0; }
.tool-actions { margin-top: 15px; }
</style>