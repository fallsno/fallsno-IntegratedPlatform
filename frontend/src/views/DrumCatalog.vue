<template>
  <div class="drum-catalog-page">
    <el-card class="hero-card" shadow="never">
      <div class="hero-card__content">
        <div>
          <div class="hero-card__eyebrow">Drum Catalog</div>
          <h2>滚筒分类与型号管理</h2>
          <p>把原生、再生、干混滚筒的分类树、系列规则和具体型号收口到统一入口，直接衔接矩阵维护和设计工作台。</p>
        </div>
        <div class="hero-card__stats">
          <div v-for="card in summaryCards" :key="card.label" class="hero-stat">
            <div class="hero-stat__label">{{ card.label }}</div>
            <div class="hero-stat__value">{{ card.value }}</div>
          </div>
        </div>
      </div>
    </el-card>

    <div class="catalog-toolbar">
      <div class="toolbar-search">
        <el-input 
          v-model="searchQuery" 
          placeholder="搜索分类、系列、型号、中文名..." 
          prefix-icon="Search"
          clearable
          style="width: 320px"
        />
      </div>
      <div class="toolbar-actions">
        <el-button type="primary" icon="Plus" @click="handleCreateType">新增分类</el-button>
        <el-button icon="Plus" @click="handleCreateFamily">新增系列</el-button>
        <el-button icon="Plus" @click="handleCreateVersion">新增型号</el-button>
        <el-button icon="Upload" @click="handleImport">批量导入</el-button>
      </div>
    </div>

    <div class="catalog-layout">
      <el-card class="catalog-pane catalog-pane--tree" shadow="never">
        <DrumCategoryTree
          :tree-data="treeData"
          :current-node-id="selectedNodeId"
          :search-keyword="searchQuery"
          title="滚筒分类树"
          description="支持按分类、系列、型号逐层定位"
          @select="handleTreeSelect"
        />
      </el-card>

      <el-card class="catalog-pane catalog-pane--main" shadow="never">
        <template #header>
          <div class="panel-header">
            <div>
              <div class="panel-title">{{ currentTitle }}</div>
              <div class="panel-subtitle">{{ currentSubtitle }}</div>
            </div>
            <div class="panel-actions">
              <el-button @click="loadTree">刷新分类树</el-button>
              <el-button v-if="selectedFamily" type="primary" @click="handleGenerateVersions">
                批量生成型号
              </el-button>
              <el-button v-if="selectedFamily" @click="goToMatrix">进入型号矩阵</el-button>
              <el-button v-if="selectedVersion" type="success" plain @click="goToWorkbench">
                进入设计工作台
              </el-button>
            </div>
          </div>
        </template>

        <div class="main-content">
          <el-empty
            v-if="!selectedType && !selectedFamily && !selectedVersion"
            description="请从左侧选择分类、系列或型号"
          />

          <template v-else-if="selectedVersion">
            <div class="info-card">
              <div class="section-title">产品管理信息</div>
              <el-descriptions border :column="2">
                <el-descriptions-item label="所属分类">{{ selectedType?.type_name || '-' }}</el-descriptions-item>
                <el-descriptions-item label="所属系列">{{ selectedFamily?.family_code || '-' }}</el-descriptions-item>
                <el-descriptions-item label="型号代号">{{ selectedVersion.version_code }}</el-descriptions-item>
                <el-descriptions-item label="当前产量">{{ selectedVersion.capacity_value }}</el-descriptions-item>
              </el-descriptions>
            </div>
            
            <div class="action-card" style="margin-top: 24px;">
              <div class="section-title">快捷进入设计</div>
              <el-button type="success" size="large" @click="goToWorkbench" style="width: 100%">
                进入工作台开展参数设计与分析
              </el-button>
            </div>
          </template>

          <template v-else-if="selectedFamily">
            <div class="info-card">
              <div class="section-title">产品管理信息</div>
              <el-descriptions border :column="2">
                <el-descriptions-item label="系列代号">{{ selectedFamily.family_code }}</el-descriptions-item>
                <el-descriptions-item label="系列名称">{{ selectedFamily.family_name }}</el-descriptions-item>
                <el-descriptions-item label="型号数量">{{ selectedFamily.versions?.length || 0 }}</el-descriptions-item>
                <el-descriptions-item label="产量档位">{{ selectedFamily.capacity_options }}</el-descriptions-item>
              </el-descriptions>

              <div class="section-title" style="margin-top: 20px;">系列下的型号</div>
              <el-table :data="selectedFamily.versions || []" stripe height="300">
                <el-table-column prop="version_code" label="型号代号" min-width="160" />
                <el-table-column prop="display_name" label="显示名称" min-width="180" />
                <el-table-column prop="capacity_value" label="产量" width="120" />
              </el-table>
            </div>

            <div class="action-card" style="margin-top: 24px;">
              <div class="section-title">快捷进入设计</div>
              <el-button type="primary" size="large" @click="goToMatrix" style="width: 100%">
                进入型号矩阵维护基础参数
              </el-button>
            </div>
          </template>

          <template v-else-if="selectedType">
            <div class="section-title">分类下的系列</div>
            <el-table :data="selectedType.families || []" stripe>
              <el-table-column prop="family_code" label="系列代号" width="120" />
              <el-table-column prop="family_name" label="系列名称" min-width="180" />
              <el-table-column label="型号数量" width="120">
                <template #default="{ row }">{{ row.versions?.length || 0 }}</template>
              </el-table-column>
              <el-table-column prop="capacity_options" label="产量档位" min-width="200" />
            </el-table>
          </template>
        </div>
      </el-card>

      <el-card class="catalog-pane catalog-pane--detail" shadow="never">
        <template #header>
          <div class="panel-title">分析与对比</div>
        </template>

        <div v-if="selectedNode" class="detail-stack">
          <el-empty description="分析与对比区 (开发中)" />
          <div class="detail-tips">
            <div class="section-title">下一步建议</div>
            <ul>
              <li v-if="selectedFamily">先批量生成该系列标准型号，再进入矩阵维护基础参数。</li>
              <li v-if="selectedVersion">直接进入工作台，以当前型号为底稿执行计算与对比。</li>
              <li v-if="selectedType">先确认系列完整性，再批量补齐系列下的具体型号。</li>
            </ul>
          </div>
        </div>
        <el-empty v-else description="尚未选择节点" />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import DrumCategoryTree from '@/components/DrumCategoryTree.vue'
import { fetchDrumTree, generateFamilyVersions } from '@/api/drumDesign'

const router = useRouter()

const searchQuery = ref('')

const handleCreateType = () => {
  ElMessage.info('新增分类功能开发中')
}
const handleCreateFamily = () => {
  ElMessage.info('新增系列功能开发中')
}
const handleCreateVersion = () => {
  ElMessage.info('新增型号功能开发中')
}
const handleImport = () => {
  ElMessage.info('批量导入功能开发中')
}

const treeData = ref([])
const selectedNode = ref(null)
const selectedNodeId = ref('')
const selectedType = ref(null)
const selectedFamily = ref(null)
const selectedVersion = ref(null)

const countFamilies = (rows = []) => rows.reduce((sum, item) => sum + (item.families?.length || 0), 0)
const countVersions = (rows = []) =>
  rows.reduce(
    (sum, item) =>
      sum + (item.families || []).reduce((familySum, family) => familySum + (family.versions?.length || 0), 0),
    0
  )

const summaryCards = computed(() => [
  { label: '分类', value: treeData.value.length },
  { label: '系列', value: countFamilies(treeData.value) },
  { label: '型号', value: countVersions(treeData.value) }
])

const currentTitle = computed(() => {
  if (selectedVersion.value) return `${selectedVersion.value.version_code} 型号详情`
  if (selectedFamily.value) return `${selectedFamily.value.family_code} 系列详情`
  if (selectedType.value) return `${selectedType.value.type_name} 分类详情`
  return '滚筒分类总览'
})

const currentSubtitle = computed(() => {
  if (selectedVersion.value) return '查看该型号的产量档位、所属系列以及下一步设计入口'
  if (selectedFamily.value) return '查看该系列下所有标准型号，并执行批量补齐'
  if (selectedType.value) return '查看该分类下的系列分布与规则归属'
  return '从左侧分类树选择对象后，在这里查看当前层级的明细'
})

const levelLabel = computed(() => {
  if (!selectedNode.value) return ''
  if (selectedNode.value.level === 'version') return '型号'
  if (selectedNode.value.level === 'family') return '系列'
  return '分类'
})

const levelTagType = computed(() => {
  if (!selectedNode.value) return 'info'
  if (selectedNode.value.level === 'version') return 'success'
  if (selectedNode.value.level === 'family') return 'warning'
  return 'info'
})

const pickDefaultSelection = (rows = []) => {
  const firstType = rows[0] || null
  const firstFamily = firstType?.children?.[0] || null
  const firstVersion = firstFamily?.children?.[0] || null
  return {
    data: firstVersion || firstFamily || firstType,
    type: firstType?.raw || null,
    family: firstFamily?.raw || null,
    version: firstVersion?.raw || null
  }
}

const loadTree = async () => {
  treeData.value = await fetchDrumTree()
  if (!selectedNodeId.value) {
    const fallbackSelection = pickDefaultSelection(treeData.value)
    if (fallbackSelection.data) {
      applyResolvedSelection(fallbackSelection)
    }
  }
}

const applyResolvedSelection = ({ data, type, family, version }) => {
  selectedNode.value = data
  selectedNodeId.value = data?.id || ''
  selectedType.value = type || null
  selectedFamily.value = family || null
  selectedVersion.value = version || null
}

const handleTreeSelect = (selection) => {
  const { data, node } = selection
  if (data?.level === 'version') {
    applyResolvedSelection({
      data,
      type: node?.parent?.parent?.data?.raw || null,
      family: node?.parent?.data?.raw || null,
      version: data.raw || null
    })
    return
  }
  if (data?.level === 'family') {
    applyResolvedSelection({
      data,
      type: node?.parent?.data?.raw || null,
      family: data.raw || null,
      version: null
    })
    return
  }
  applyResolvedSelection({
    data,
    type: data?.raw || null,
    family: null,
    version: null
  })
}

const handleGenerateVersions = async () => {
  if (!selectedFamily.value?.id) return
  const result = await generateFamilyVersions(selectedFamily.value.id)
  ElMessage.success(`已生成 ${result.created_count || 0} 个型号`)
  await loadTree()
}

const goToMatrix = () => {
  if (!selectedFamily.value?.id) return
  router.push({ name: 'ModelParameterMatrix', params: { familyId: selectedFamily.value.id } })
}

const goToWorkbench = () => {
  if (!selectedVersion.value?.id || !selectedFamily.value?.id) return
  router.push({
    name: 'DesignWorkbench',
    query: {
      familyId: selectedFamily.value.id,
      versionId: selectedVersion.value.id
    }
  })
}

onMounted(loadTree)
</script>

<style scoped>
.drum-catalog-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-card {
  border: none;
  background:
    radial-gradient(circle at top left, rgba(56, 189, 248, 0.14), transparent 30%),
    linear-gradient(135deg, #0f172a, #1e293b 60%, #1d4ed8);
  color: #e2e8f0;
}

.hero-card :deep(.el-card__body) {
  padding: 24px;
}

.hero-card__content {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.hero-card__eyebrow {
  margin-bottom: 8px;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #7dd3fc;
}

.hero-card h2 {
  margin: 0;
  color: #f8fafc;
}

.hero-card p {
  margin-top: 10px;
  max-width: 720px;
  line-height: 1.7;
  color: rgba(226, 232, 240, 0.86);
}

.hero-card__stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(88px, 1fr));
  gap: 12px;
  min-width: 280px;
}

.hero-stat {
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.38);
}

.hero-stat__label {
  font-size: 12px;
  color: #94a3b8;
}

.hero-stat__value {
  margin-top: 8px;
  font-size: 26px;
  font-weight: 700;
  color: #f8fafc;
}

.catalog-layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr) 320px;
  gap: 16px;
  min-height: 680px;
}

.catalog-pane {
  min-height: 0;
}

.catalog-pane--tree :deep(.el-card__body),
.catalog-pane--detail :deep(.el-card__body) {
  height: 100%;
}

.catalog-pane--main :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.panel-subtitle {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

.panel-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.main-content {
  flex: 1;
}

.section-title {
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}

.detail-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-hero {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.detail-hero__title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.detail-tips ul {
  padding-left: 18px;
  color: #475569;
  line-height: 1.8;
}

.catalog-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
}

@media (max-width: 1440px) {
  .catalog-layout {
    grid-template-columns: 280px minmax(0, 1fr);
  }

  .catalog-pane--detail {
    grid-column: 1 / -1;
  }
}
</style>
