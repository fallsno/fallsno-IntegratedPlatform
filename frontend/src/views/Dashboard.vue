<template>
  <div class="dashboard">
    <!-- 顶部统计卡片区 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <div class="stat-card primary">
          <div class="stat-icon"><el-icon :size="32"><Box /></el-icon></div>
          <div class="stat-info">
            <div class="stat-label">产品总数</div>
            <div class="stat-value">{{ stats.productCount }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card success">
          <div class="stat-icon"><el-icon :size="32"><CircleCheck /></el-icon></div>
          <div class="stat-info">
            <div class="stat-label">设计合规指数</div>
            <div class="stat-value" :style="{ color: healthColor }">{{ stats.healthScore }}%</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card warning">
          <div class="stat-icon"><el-icon :size="32"><Clock /></el-icon></div>
          <div class="stat-info">
            <div class="stat-label">待处理变更</div>
            <div class="stat-value">{{ stats.pendingChanges }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card info">
          <div class="stat-icon"><el-icon :size="32"><Connection /></el-icon></div>
          <div class="stat-info">
            <div class="stat-label">激活规则数</div>
            <div class="stat-value">{{ stats.ruleCount }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷操作与动态区 -->
    <el-row :gutter="16" style="margin-top: 24px">
      <!-- 左侧：近期动态 -->
      <el-col :span="14">
        <el-card class="activity-card" shadow="hover">
          <template #header>
            <div class="card-header-compact">
              <span>📊 近期设计动态</span>
            </div>
          </template>
          <el-timeline size="small">
            <el-timeline-item
              v-for="(activity, index) in activities"
              :key="index"
              :timestamp="activity.time"
              :type="activity.type"
              placement="top"
            >
              <span class="activity-text">{{ activity.content }}</span>
            </el-timeline-item>
            <el-timeline-item v-if="!activities.length" timestamp="--" type="info">
              <span class="activity-text">暂无动态记录</span>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>

      <!-- 右侧：快捷操作 -->
      <el-col :span="10">
        <el-card class="quick-card" shadow="hover">
          <template #header>
            <div class="card-header-compact">
              <span>⚡ 快捷入口</span>
            </div>
          </template>
          <div class="quick-grid">
            <div class="quick-item" @click="$router.push('/product-types')">
              <el-icon :size="24"><FolderOpened /></el-icon>
              <span>产品管理</span>
            </div>
            <div class="quick-item" @click="$router.push('/knowledge')">
              <el-icon :size="24"><Notebook /></el-icon>
              <span>知识库</span>
            </div>
            <div class="quick-item" @click="$router.push('/formulas')">
              <el-icon :size="24"><Document /></el-icon>
              <span>公式库</span>
            </div>
            <div class="quick-item" @click="$router.push('/workbench/product-select')">
              <el-icon :size="24"><EditPen /></el-icon>
              <span>公式工作台</span>
            </div>
            <div class="quick-item" @click="$router.push('/compare')">
              <el-icon :size="24"><DataAnalysis /></el-icon>
              <span>设计对比</span>
            </div>
            <div class="quick-item" @click="openLab">
              <el-icon :size="24"><Reading /></el-icon>
              <span>试验总结</span>
            </div>
            <div class="quick-item" @click="openMonitor">
              <el-icon :size="24"><Monitor /></el-icon>
              <span>滚筒检测</span>
            </div>
            <div class="quick-item" @click="openToolbox">
              <el-icon :size="24"><Tools /></el-icon>
              <span>数据工具</span>
            </div>
          </div>

          <el-divider style="margin: 16px 0" />

          <!-- 底部状态概览 (替代原来的工具入口) -->
          <div class="tool-links">
            <span class="tool-hint">系统状态</span>
            <div class="tool-btns">
              <el-tag type="success" effect="dark" class="status-tag">
                <el-icon><Check /></el-icon> 服务正常运行
              </el-tag>
              <el-tag type="info" effect="plain" class="status-tag">
                v2.1.0-Release
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import {
  Box, CircleCheck, Clock, Connection,
  FolderOpened, Notebook, Document, EditPen,
  Monitor, Tools, Reading, DataAnalysis, Check,
  Histogram
} from '@element-plus/icons-vue'

const router = useRouter()
const stats = ref({ productCount: 0, healthScore: 100, pendingChanges: 0, ruleCount: 0 })
const activities = ref([])

const healthColor = computed(() => {
  if (stats.value.healthScore >= 90) return '#67c23a'
  if (stats.value.healthScore >= 70) return '#e6a23c'
  return '#f56c6c'
})

const fetchStats = async () => {
  try {
    const res = await axios.get('/dashboard/stats')
    stats.value = res.data
  } catch (err) { console.error('获取统计数据失败:', err) }
}

const fetchActivities = async () => {
  try {
    const res = await axios.get('/dashboard/activities')
    activities.value = res.data
  } catch (err) { console.error('获取动态失败:', err) }
}

const openMonitor = () => {
  const monitorUrl = `${window.location.protocol}//${window.location.hostname}:5001/admin`
  window.open(monitorUrl, '_blank')
}
const openToolbox = () => window.open('/tools', '_blank')
const openLab = () => router.push('/lab')

onMounted(() => { fetchStats(); fetchActivities() })
</script>

<style scoped>
.dashboard { padding: 24px; background: #f5f7fa; min-height: calc(100vh - 60px); }

.stat-row { }
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 12px;
  background: #fff;
  border: none;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }

.stat-icon {
  width: 56px; height: 56px;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.stat-card.primary .stat-icon { background: #ecf5ff; color: #409eff; }
.stat-card.success .stat-icon { background: #f0f9eb; color: #67c23a; }
.stat-card.warning .stat-icon { background: #fdf6ec; color: #e6a23c; }
.stat-card.info .stat-icon { background: #f4f4f5; color: #909399; }

.stat-info { flex: 1; min-width: 0; }
.stat-label { font-size: 13px; color: #909399; margin-bottom: 4px; }
.stat-value { font-size: 28px; font-weight: 700; color: #1e293b; font-family: 'Arial', sans-serif; }

.activity-card, .quick-card { border-radius: 12px; border: none; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.card-header-compact { font-size: 15px; font-weight: 600; color: #1e293b; }

.activity-text { font-size: 13px; color: #475569; }

.quick-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.quick-item {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8px;
  padding: 18px 10px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;
  color: #475569;
  font-size: 13px;
}
.quick-item:hover { background: #3b82f6; color: #fff; border-color: #3b82f6; transform: translateY(-1px); }

.tool-links { }
.tool-hint { font-size: 12px; color: #94a3b8; margin-bottom: 8px; display: block; }
.tool-btns { display: flex; gap: 10px; flex-wrap: wrap; }
.status-tag { display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px; border-radius: 6px; }
</style>
