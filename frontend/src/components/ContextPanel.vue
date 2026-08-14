<template>
  <div class="context-panel-container">
    <div class="panel-header">
      <span>上下文面板</span>
    </div>
    
    <div class="panel-body">
      <el-tabs v-model="activeTab" class="context-tabs">
        <el-tab-pane label="💡 智能推荐" name="recommend">
          <div class="tab-content">
            <el-empty v-if="!recommendations.length" description="暂无推荐数据" :image-size="60" />
            <div v-else class="rec-list">
              <el-card v-for="(rec, idx) in recommendations" :key="idx" shadow="hover" class="rec-card">
                <div class="rec-header">
                  <span class="rec-param">{{ rec.param }}</span>
                  <el-tag size="small" type="success">{{ rec.value }}</el-tag>
                </div>
                <div class="rec-desc">{{ rec.desc }}</div>
                <div class="rec-action">
                  <el-button type="primary" link size="small" @click="$emit('apply-rec', rec)">应用此推荐</el-button>
                </div>
              </el-card>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="⚠️ 违规项" name="violations">
          <div class="tab-content">
            <el-empty v-if="!violations.length" description="无违规项，设计良好" :image-size="60" />
            <div v-else class="vio-list">
              <el-alert
                v-for="(vio, idx) in violations"
                :key="idx"
                :title="vio.param"
                :description="vio.message"
                :type="vio.severity === 'error' ? 'error' : 'warning'"
                show-icon
                :closable="false"
                style="margin-bottom: 10px;"
              />
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="📚 知识库" name="knowledge">
          <div class="tab-content">
            <el-empty description="请选择设计参数查看相关知识" :image-size="60" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  recommendations: {
    type: Array,
    default: () => []
  },
  violations: {
    type: Array,
    default: () => []
  }
})

defineEmits(['apply-rec'])

const activeTab = ref('recommend')
</script>

<style scoped>
.context-panel-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  border-left: 1px solid #e2e8f0;
}

.panel-header {
  padding: 10px 15px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  font-weight: 600;
  font-size: 14px;
  color: #334155;
}

.panel-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.context-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

:deep(.el-tab-pane) {
  height: 100%;
}

.tab-content {
  height: 100%;
  overflow-y: auto;
  padding: 15px;
}

.rec-card {
  margin-bottom: 10px;
}

.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.rec-param {
  font-weight: 600;
  color: #1e293b;
}

.rec-desc {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 10px;
}

.rec-action {
  text-align: right;
}
</style>
