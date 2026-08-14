<template>
  <div id="app">
    <el-container style="height: 100vh;">
      <el-header height="60px">
        <div class="header-content">
          <div class="header-left">
            <el-button v-if="useGlobalDesignChrome" link @click="toggleLeftPanel" style="color: white; margin-right: 15px;">
              <el-icon :size="20"><Expand v-if="!showLeftPanel" /><Fold v-else /></el-icon>
            </el-button>
            <h2 @click="$router.push('/workbench/product-select')" style="cursor: pointer">📋 滚筒设计平台系统</h2>
          </div>
          <div class="header-actions">
            <SearchBar @search="handleSearch" @select="handleSelect" />
            <el-tooltip content="仪表盘" placement="bottom">
              <el-button type="default" link @click="$router.push('/dashboard')" style="color: #94a3b8;">
                <el-icon :size="18"><HomeFilled /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="产品管理" placement="bottom">
              <el-button type="default" link @click="$router.push('/drums')" style="color: #94a3b8;">
                <el-icon :size="18"><Box /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="公式" placement="bottom">
              <el-button type="default" link @click="$router.push('/formulas')" style="color: #94a3b8;">
                <el-icon :size="18"><Document /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="参数中心" placement="bottom">
              <el-button type="default" link @click="$router.push('/parameters')" style="color: #94a3b8;">
                <el-icon :size="18"><Grid /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="设备选型库" placement="bottom">
              <el-button type="default" link @click="$router.push('/catalog')" style="color: #94a3b8;">
                <el-icon :size="18"><Cpu /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="公式工作台" placement="bottom">
              <el-button type="default" link @click="$router.push('/workbench/product-select')" style="color: #94a3b8;">
                <el-icon :size="18"><EditPen /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="试验系统" placement="bottom">
              <el-button type="default" link @click="$router.push('/lab')" style="color: #94a3b8;">
                <el-icon :size="18"><Checked /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="生成报告" placement="bottom">
              <el-button type="default" link @click="openReport" style="color: #94a3b8;">
                <el-icon :size="18"><DocumentChecked /></el-icon>
              </el-button>
            </el-tooltip>
            <el-divider direction="vertical" style="margin: 0 8px" />
            <el-tooltip content="滚筒监测" placement="bottom">
              <el-button type="default" link @click="openMonitor" style="color: #94a3b8;">
                <el-icon :size="18"><Monitor /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="工具箱" placement="bottom">
              <el-button type="default" link @click="openToolbox" style="color: #94a3b8;">
                <el-icon :size="18"><Tools /></el-icon>
              </el-button>
            </el-tooltip>
            <el-button v-if="useGlobalDesignChrome" link @click="toggleRightPanel" style="color: #94a3b8; margin-left: 8px;">
              <el-icon :size="18"><Setting /></el-icon>
            </el-button>
          </div>
        </div>
      </el-header>
      
      <el-container class="main-container">
        <!-- 左侧全局产品导航树 -->
        <el-aside 
          v-if="actualShowLeft" 
          :width="leftPanelWidth + 'px'" 
          class="resizable-aside left-aside"
        >
          <ProductTree />
          <div class="resize-handle right" @mousedown="startResizeLeft"></div>
        </el-aside>
        
        <!-- 主工作区 -->
        <el-main class="main-content" :class="{ 'no-aside': !actualShowLeft && !actualShowRight }">
          <router-view />
        </el-main>
        
        <!-- 右侧上下文面板 -->
        <el-aside 
          v-if="actualShowRight" 
          :width="rightPanelWidth + 'px'" 
          class="resizable-aside right-aside"
        >
          <div class="resize-handle left" @mousedown="startResizeRight"></div>
          <ContextPanel 
            :recommendations="contextRecommendations" 
            :violations="contextViolations" 
            @apply-rec="handleApplyRec"
          />
        </el-aside>
      </el-container>
    </el-container>

    <!-- 命令面板 (Ctrl+Shift+P) -->
    <el-dialog v-model="showCommandPalette" title="命令面板" width="600px" :show-close="false" custom-class="command-palette-dialog">
      <el-autocomplete
        ref="commandInputRef"
        v-model="commandSearch"
        :fetch-suggestions="queryCommands"
        placeholder="输入命令或搜索内容..."
        style="width: 100%"
        @select="handleCommandSelect"
      >
        <template #default="{ item }">
          <div class="command-item">
            <el-icon><component :is="item.icon" /></el-icon>
            <span class="command-text">{{ item.value }}</span>
            <span class="command-desc">{{ item.desc }}</span>
          </div>
        </template>
      </el-autocomplete>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, provide, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { HomeFilled, Box, Document, EditPen, Monitor, Tools, Setting, Expand, Fold, Grid, DocumentChecked, Cpu } from '@element-plus/icons-vue'
import SearchBar from '@/components/SearchBar.vue'
import ProductTree from '@/components/ProductTree.vue'
import ContextPanel from '@/components/ContextPanel.vue'
import { shouldUseGlobalDesignChrome } from '@/router/appShell.helpers.mjs'

const router = useRouter()
const route = useRoute()

// 新工作台等页面由自身管理布局，旧设计壳层仅对显式声明的路由启用
const useGlobalDesignChrome = computed(() => shouldUseGlobalDesignChrome(route))

const handleSearch = (kw) => router.push({ name: 'Search', query: { q: kw } })
const handleSelect = (item) => {
  if (item.type === 'model' && item.family_id) {
    router.push({ name: 'Versions', params: { familyId: item.family_id } })
  }
}

// 布局状态与持久化
const showLeftPanel = ref(localStorage.getItem('showLeftPanel') !== 'false')
const showRightPanel = ref(localStorage.getItem('showRightPanel') === 'true')
const leftPanelWidth = ref(parseInt(localStorage.getItem('leftPanelWidth')) || 250)
const rightPanelWidth = ref(parseInt(localStorage.getItem('rightPanelWidth')) || 300)

// 侧边栏实际显示状态：仅旧壳层路由启用
const actualShowLeft = computed(() => useGlobalDesignChrome.value && showLeftPanel.value)
const actualShowRight = computed(() => useGlobalDesignChrome.value && showRightPanel.value)

const toggleLeftPanel = () => {
  showLeftPanel.value = !showLeftPanel.value
  localStorage.setItem('showLeftPanel', showLeftPanel.value)
}

const toggleRightPanel = () => {
  showRightPanel.value = !showRightPanel.value
  localStorage.setItem('showRightPanel', showRightPanel.value)
}

// 拖拽调整宽度逻辑
let isResizingLeft = false
let isResizingRight = false

const startResizeLeft = (e) => {
  isResizingLeft = true
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
}

const startResizeRight = (e) => {
  isResizingRight = true
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
}

const handleMouseMove = (e) => {
  if (isResizingLeft) {
    const newWidth = Math.max(150, Math.min(e.clientX, 600))
    leftPanelWidth.value = newWidth
  } else if (isResizingRight) {
    const newWidth = Math.max(200, Math.min(document.body.clientWidth - e.clientX, 800))
    rightPanelWidth.value = newWidth
  }
}

const stopResize = () => {
  if (isResizingLeft) {
    localStorage.setItem('leftPanelWidth', leftPanelWidth.value)
  }
  if (isResizingRight) {
    localStorage.setItem('rightPanelWidth', rightPanelWidth.value)
  }
  isResizingLeft = false
  isResizingRight = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = 'default'
}

// 提供全局上下文数据
const contextRecommendations = ref([])
const contextViolations = ref([])

provide('setContextData', (recs, vios) => {
  contextRecommendations.value = recs || []
  contextViolations.value = vios || []
})

const handleApplyRec = (rec) => {
  // 触发全局事件，让工作台内部页接收并处理
  window.dispatchEvent(new CustomEvent('apply-recommendation', { detail: rec }))
}

// 命令面板逻辑
const showCommandPalette = ref(false)
const commandSearch = ref('')
const commandInputRef = ref(null)

const commands = [
  { value: '跳转到仪表盘', desc: '系统概览与统计', icon: 'Menu', action: () => router.push('/dashboard') },
  { value: '进入滚筒产品管理', desc: '打开滚筒统一入口', icon: 'Box', action: () => router.push('/drums') },
  { value: '进入公式工作台', desc: '聚焦公式求解与结果查看', icon: 'Files', action: () => router.push({ name: 'ProductTypeSelection' }) },
  { value: '执行全局计算', desc: '重新计算所有公式', icon: 'Refresh', action: () => window.dispatchEvent(new CustomEvent('global-calculate')) },
  { value: '对比分析', desc: '多机型设计点对比', icon: 'DataAnalysis', action: () => router.push('/compare') },
  { value: '打开公式', desc: '查看与编辑计算公式', icon: 'Document', action: () => router.push('/formulas') }
]

const queryCommands = (qs, cb) => {
  const results = qs ? commands.filter(c => c.value.includes(qs) || c.desc.includes(qs)) : commands
  cb(results)
}

const handleCommandSelect = (item) => {
  if (item.action) {
    item.action()
    showCommandPalette.value = false
    commandSearch.value = ''
  }
}

const handleKeyDown = (e) => {
  if (e.ctrlKey && e.shiftKey && e.key.toUpperCase() === 'P') {
    e.preventDefault()
    showCommandPalette.value = true
    setTimeout(() => {
      // 自动聚焦输入框
      const input = document.querySelector('.command-palette-input input')
      if (input) input.focus()
    }, 100)
  }
}

const openMonitor = () => {
  const monitorUrl = `${window.location.protocol}//${window.location.hostname}:5001/admin`
  window.open(monitorUrl, '_blank')
}
const openToolbox = () => window.open('http://10.30.10.64:5002', '_blank')
const openReport = () => {
  // 实际业务中这里会带上当前项目的 ID
  const routeUrl = router.resolve({
    path: '/report',
    query: { projectCode: 'GT-2026-001' }
  })
  window.open(routeUrl.href, '_blank')
}

onMounted(() => window.addEventListener('keydown', handleKeyDown))
onUnmounted(() => window.removeEventListener('keydown', handleKeyDown))
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', sans-serif; background: #f0f2f5; overflow: hidden; }

.el-header { background: #1e293b; color: white; display: flex; align-items: center; padding: 0 20px; }
.header-content { width: 100%; display: flex; justify-content: space-between; align-items: center; }
.header-left { display: flex; align-items: center; }
.header-actions { display: flex; gap: 15px; align-items: center; }
h2 { color: #38bdf8; margin: 0; font-size: 18px; }

.main-container {
  height: calc(100vh - 60px);
  overflow: hidden;
  display: flex;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow: auto;
  background: #f1f5f9;
}

.resizable-aside {
  position: relative;
  background: #fff;
  overflow: hidden;
  flex-shrink: 0;
}

.left-aside {
  border-right: 1px solid #e2e8f0;
}

.right-aside {
  border-left: 1px solid #e2e8f0;
}

.resize-handle {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 5px;
  cursor: col-resize;
  background-color: transparent;
  transition: background-color 0.2s;
  z-index: 10;
}

.resize-handle:hover, .resize-handle:active {
  background-color: #38bdf8;
}

.resize-handle.right {
  right: 0;
}

.resize-handle.left {
  left: 0;
}

/* 命令面板样式 */
.command-palette-dialog .el-dialog__header { display: none; }
.command-palette-dialog .el-dialog__body { padding: 10px; }
.command-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
}
.command-text {
  margin-left: 10px;
  flex: 1;
  font-weight: bold;
}
.command-desc {
  color: #999;
  font-size: 12px;
}

/* 全局对话框美化优化 */
.el-dialog {
  border-radius: 12px !important;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
  border: 1px solid #e2e8f0;
}

.el-dialog__header {
  margin: 0 !important;
  padding: 16px 24px !important;
  background: linear-gradient(to right, #f8fafc, #f1f5f9);
  border-bottom: 1px solid #e2e8f0;
}

.el-dialog__title {
  font-size: 16px !important;
  font-weight: 700 !important;
  color: #1e293b !important;
}

.el-dialog__body {
  padding: 24px !important;
}

.el-dialog__footer {
  padding: 12px 24px !important;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

/* 统一按钮圆角 */
.el-button {
  border-radius: 6px !important;
}
</style>
