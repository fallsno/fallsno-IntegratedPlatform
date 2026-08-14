<template>
  <div class="report-view-container">
    <div class="report-actions">
      <el-button type="primary" @click="printReport">打印 / 导出 PDF</el-button>
      <el-button @click="$router.back()">返回</el-button>
    </div>
    
    <div class="report-view" id="report-content">
      <div class="report-header">
        <h1>{{ reportTitle }}</h1>
        <div class="report-meta">
          <span>项目代号: {{ projectCode }}</span>
          <span>生成日期: {{ currentDate }}</span>
        </div>
      </div>

    <div class="report-section">
      <h2>1. 设计参数与计算结果</h2>
      <el-table :data="parameters" border style="width: 100%">
        <el-table-column prop="name" label="参数名称" width="180" />
        <el-table-column prop="value" label="计算值" width="120" />
        <el-table-column prop="unit" label="单位" width="100" />
        <el-table-column prop="formula" label="计算公式/来源" />
      </el-table>
    </div>

    <div class="report-section">
      <h2>2. 设备选型清单 (BOM)</h2>
      <el-table :data="equipments" border style="width: 100%">
        <el-table-column prop="category" label="设备类型" width="120" />
        <el-table-column prop="model" label="推荐型号" width="180" />
        <el-table-column prop="brand" label="品牌" width="120" />
        <el-table-column prop="specs" label="关键参数" />
      </el-table>
    </div>

    <div class="report-section">
      <h2>3. 计算链路拓扑图</h2>
      <div class="mindmap-placeholder">
        <!-- 这里可以挂载 ECharts 或 Canvas 渲染的思维导图 -->
        <p>计算链路图表区域</p>
      </div>
    </div>
  </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const reportTitle = ref('工程设计计算书')
const projectCode = ref(route.query.projectCode || 'N/A')
const currentDate = ref(new Date().toLocaleDateString())

const parameters = ref([
  { name: '所需功率', value: '18.5', unit: 'kW', formula: '=扭矩*转速/9550' },
  { name: '输出扭矩', value: '1250', unit: 'N.m', formula: '=载荷*半径' }
])

const equipments = ref([
  { category: '电机', model: 'Y2-160L-4', brand: '西门子', specs: '功率: 18.5kW, 转速: 1460rpm' },
  { category: '减速机', model: 'ZLYJ225', brand: '国茂', specs: '速比: 31.5, 扭矩: 2500N.m' }
])

const printReport = () => {
  window.print()
}

onMounted(() => {
  // 实际业务中，这里会根据 route.query.id 去后端拉取完整的快照数据
  // 渲染完成后，可以触发一个全局事件，通知无头浏览器可以开始截图/打印 PDF 了
  setTimeout(() => {
    window.dispatchEvent(new Event('report-rendered'))
  }, 1000)
})
</script>

<style scoped>
.report-view-container {
  padding: 20px;
  background: #f0f2f5;
  min-height: 100vh;
}

.report-actions {
  max-width: 1000px;
  margin: 0 auto 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.report-view {
  padding: 40px;
  max-width: 1000px;
  margin: 0 auto;
  background: #fff;
  color: #000;
  font-family: 'SimSun', '宋体', serif; /* 报告通常使用衬线字体 */
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.report-header {
  text-align: center;
  margin-bottom: 40px;
  border-bottom: 2px solid #000;
  padding-bottom: 20px;
}

.report-header h1 {
  font-size: 28px;
  margin-bottom: 10px;
}

.report-meta {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #666;
}

.report-section {
  margin-bottom: 30px;
}

.report-section h2 {
  font-size: 18px;
  border-left: 4px solid #3b82f6;
  padding-left: 10px;
  margin-bottom: 15px;
}

.mindmap-placeholder {
  height: 400px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}

/* 打印样式优化 */
@media print {
  .report-view-container {
    padding: 0;
    background: #fff;
  }
  .report-actions {
    display: none;
  }
  .report-view {
    padding: 0;
    box-shadow: none;
  }
  .el-table {
    border-color: #000 !important;
  }
  .el-table th, .el-table td {
    border-color: #000 !important;
    color: #000 !important;
  }
}
</style>
