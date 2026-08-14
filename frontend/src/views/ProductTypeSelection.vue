<template>
  <div class="product-type-selection">
    <div class="header-section">
      <h1 class="page-title">选择产品大类</h1>
      <p class="page-subtitle">请选择您要进行设计的产品类型，进入对应的计算模块空间。</p>
    </div>

    <div class="content-section" v-loading="loading">
      <el-empty v-if="!loading && productTypes.length === 0" description="暂无可用产品大类" />
      
      <div class="type-grid" v-else>
        <div 
          v-for="item in productTypes" 
          :key="item.id"
          class="type-card"
          @click="goToModules(item.id)"
        >
          <div class="type-card-bg"></div>
          <div class="type-card-content">
            <div class="type-icon">
              <el-icon><Box /></el-icon>
            </div>
            <h3 class="type-name">{{ item.name }}</h3>
            <div class="type-meta">
              <span>{{ item.familyCount }} 个系列</span>
              <el-divider direction="vertical" />
              <span>{{ item.versionCount }} 个型号</span>
            </div>
            <div class="type-action">
              <span>进入模块</span>
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Box, ArrowRight } from '@element-plus/icons-vue'
import { fetchDrumTree } from '@/api/drumDesign'

const router = useRouter()
const treeData = ref([])
const loading = ref(false)

const productTypes = computed(() =>
  treeData.value.map((typeNode) => ({
    id: String(typeNode.raw?.id || ''),
    name: typeNode.label || typeNode.raw?.type_name || '未命名产品',
    familyCount: (typeNode.children || []).length,
    versionCount: (typeNode.children || []).reduce((count, familyNode) => count + (familyNode.children || []).length, 0)
  }))
)

const loadData = async () => {
  loading.value = true
  try {
    treeData.value = await fetchDrumTree()
  } catch (error) {
    ElMessage.error('加载产品大类失败')
  } finally {
    loading.value = false
  }
}

const goToModules = (typeId) => {
  router.push({
    name: 'ModuleSelection',
    params: { typeId }
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.product-type-selection {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
  min-height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.header-section {
  text-align: center;
  margin-bottom: 48px;
  animation: fadeInDown 0.6s ease-out;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 16px 0;
  letter-spacing: 0.05em;
}

.page-subtitle {
  font-size: 16px;
  color: #64748b;
  margin: 0;
}

.content-section {
  flex: 1;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 32px;
  padding: 20px 0;
}

.type-card {
  position: relative;
  border-radius: 24px;
  background: #ffffff;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(226, 232, 240, 0.8);
  animation: fadeInUp 0.6s ease-out backwards;
}

.type-card:nth-child(1) { animation-delay: 0.1s; }
.type-card:nth-child(2) { animation-delay: 0.2s; }
.type-card:nth-child(3) { animation-delay: 0.3s; }
.type-card:nth-child(4) { animation-delay: 0.4s; }

.type-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(37, 99, 235, 0.12);
  border-color: rgba(59, 130, 246, 0.3);
}

.type-card-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 120px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  opacity: 0.8;
  transition: all 0.4s ease;
}

.type-card:hover .type-card-bg {
  height: 100%;
  opacity: 0.1;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.type-card-content {
  position: relative;
  padding: 32px;
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
}

.type-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #3b82f6;
  box-shadow: 0 8px 16px rgba(59, 130, 246, 0.15);
  margin-bottom: 24px;
  transition: transform 0.4s ease;
}

.type-card:hover .type-icon {
  transform: scale(1.1);
  color: #2563eb;
}

.type-name {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 12px 0;
}

.type-meta {
  display: flex;
  align-items: center;
  color: #64748b;
  font-size: 14px;
  margin-bottom: 32px;
}

.type-action {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #3b82f6;
  font-weight: 600;
  font-size: 15px;
  padding-top: 20px;
  border-top: 1px solid rgba(226, 232, 240, 0.6);
  transition: color 0.3s ease;
}

.type-action .el-icon {
  transition: transform 0.3s ease;
}

.type-card:hover .type-action {
  color: #2563eb;
}

.type-card:hover .type-action .el-icon {
  transform: translateX(4px);
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>