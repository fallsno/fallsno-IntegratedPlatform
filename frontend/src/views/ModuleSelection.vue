<template>
  <div class="module-selection">
    <div class="header-section">
      <el-button link @click="$router.push('/workbench/product-select')" class="back-btn">
        <el-icon><Back /></el-icon> 返回大类选择
      </el-button>
      <h1 class="page-title">{{ typeName }} - 计算模块管理</h1>
      <p class="page-subtitle">按模块进入对应的设计工作台：点击"功率计算"进入功率计算工作台，点击"支腿/结构"进入对应模块工作台。</p>
    </div>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新建模块
      </el-button>
    </div>

    <div class="content-section" v-loading="loading">
      <el-empty v-if="!loading && modules.length === 0" description="当前大类暂无计算模块" />
      
      <div class="module-grid" v-else>
        <div 
          v-for="(module, index) in modules" 
          :key="module.moduleCode"
          class="module-card"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <div class="module-card-header">
            <h3 class="module-name">{{ module.moduleName }}</h3>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, module)">
              <el-button link class="more-btn"><el-icon><MoreFilled /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit"><el-icon><Edit /></el-icon>编辑属性</el-dropdown-item>
                  <el-dropdown-item command="delete" divided style="color: #f56c6c"><el-icon><Delete /></el-icon>删除模块</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          
          <div class="module-meta">
            <div class="meta-item">
              <span class="meta-value">{{ module.sceneCount }}</span>
              <span class="meta-label">计算场景</span>
            </div>
            <div class="meta-divider"></div>
            <div class="meta-item">
              <span class="meta-value">{{ module.formulaCount }}</span>
              <span class="meta-label">公式节点</span>
            </div>
          </div>
          
          <div class="module-desc">
            {{ module.entryDescription }}
          </div>
          
          <div class="module-action">
            <el-button type="primary" class="enter-btn" @click="goToWorkbench(module.moduleCode)">
              进入{{ module.moduleName }}工作台
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Module Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑计算模块' : '新建计算模块'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="模块名称" prop="moduleName">
          <el-input v-model="form.moduleName" placeholder="请输入模块名称"></el-input>
        </el-form-item>
        <el-form-item label="模块编码" prop="moduleCode" v-if="!isEdit">
          <el-input v-model="form.moduleCode" placeholder="请输入模块编码 (如: M01)"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back, Plus, MoreFilled, Edit, Delete } from '@element-plus/icons-vue'
import { 
  fetchDrumTree, 
  fetchTypeModuleEntries,
  createWorkbenchFormulaModule,
  renameWorkbenchFormulaModule,
  deleteWorkbenchFormulaModule
} from '@/api/drumDesign'
import { canEnterExistingDesignWorkbench } from '@/router/workbenchAccess.mjs'

const router = useRouter()
const route = useRoute()
const typeId = route.params.typeId

const loading = ref(false)
const typeName = ref('加载中...')
const modules = ref([])
const currentModelId = ref(null)
const selectedFamilyId = ref('')
const selectedVersionId = ref('')
const treeData = ref([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref(null)
const form = ref({
  moduleName: '',
  moduleCode: ''
})

const rules = {
  moduleName: [{ required: true, message: '请输入模块名称', trigger: 'blur' }],
  moduleCode: [{ required: true, message: '请输入模块编码', trigger: 'blur' }]
}

const normalizeQueryValue = (value) => {
  if (Array.isArray(value)) {
    return String(value[0] || '').trim()
  }
  return String(value || '').trim()
}

const resolveVersionContext = (typeNode, preferredFamilyId = '', preferredVersionId = '') => {
  const families = typeNode?.children || []
  if (!families.length) {
    return { familyNode: null, versionNode: null }
  }

  if (preferredVersionId) {
    for (const familyNode of families) {
      const versionNode = (familyNode.children || []).find(
        (item) => String(item.raw?.id || '') === String(preferredVersionId || '')
      )
      if (versionNode) {
        return { familyNode, versionNode }
      }
    }
  }

  if (preferredFamilyId) {
    const familyNode = families.find((item) => String(item.raw?.id || '') === String(preferredFamilyId || '')) || null
    const versionNode = familyNode?.children?.[0] || null
    if (familyNode && versionNode) {
      return { familyNode, versionNode }
    }
  }

  const familyNode = families.find((item) => (item.children || []).length) || families[0] || null
  const versionNode = familyNode?.children?.[0] || null
  return { familyNode, versionNode }
}

const syncRouteQuery = async () => {
  const nextQuery = { ...route.query }

  if (selectedFamilyId.value) nextQuery.familyId = String(selectedFamilyId.value)
  else delete nextQuery.familyId

  if (selectedVersionId.value) nextQuery.versionId = String(selectedVersionId.value)
  else delete nextQuery.versionId

  const currentFamilyId = normalizeQueryValue(route.query.familyId)
  const currentVersionId = normalizeQueryValue(route.query.versionId)
  if (
    currentFamilyId === String(nextQuery.familyId || '') &&
    currentVersionId === String(nextQuery.versionId || '')
  ) {
    return
  }

  await router.replace({
    name: 'ModuleSelection',
    params: { typeId },
    query: nextQuery
  })
}

const loadData = async () => {
  loading.value = true
  try {
    treeData.value = await fetchDrumTree()
    const typeNode = treeData.value.find(node => String(node.raw?.id || '') === String(typeId))
    
    if (!typeNode) {
      ElMessage.error('找不到对应的产品大类')
      router.push('/workbench/product-select')
      return
    }
    
    typeName.value = typeNode.label || typeNode.raw?.type_name || '未命名产品'
    
    const preferredFamilyId = normalizeQueryValue(route.query.familyId)
    const preferredVersionId = normalizeQueryValue(route.query.versionId)
    const { familyNode, versionNode } = resolveVersionContext(typeNode, preferredFamilyId, preferredVersionId)
    
    if (!versionNode?.raw?.id) {
      selectedFamilyId.value = String(familyNode?.raw?.id || '')
      selectedVersionId.value = ''
      currentModelId.value = null
      modules.value = []
      return
    }
    
    selectedFamilyId.value = String(familyNode?.raw?.id || '')
    selectedVersionId.value = String(versionNode.raw?.id || '')
    currentModelId.value = versionNode.raw.id
    await syncRouteQuery()
    const rawModules = await fetchTypeModuleEntries(typeId, {
      versionId: versionNode.raw.id
    })
    modules.value = normalizeModuleOptions(rawModules)
  } catch (error) {
    ElMessage.error('加载计算模块失败')
  } finally {
    loading.value = false
  }
}

const normalizeModuleOptions = (rawList = []) =>
  (Array.isArray(rawList) ? rawList : []).map((module) => {
    const moduleCode = String(module.moduleCode || module.module_code || '')
    const lowerCode = moduleCode.toLowerCase()
    let moduleName = module.moduleName || module.module_name
    if (!moduleName || moduleName === '未命名模块') {
      if (moduleCode === 'power_calc') moduleName = '功率计算'
      else if (moduleCode === 'structure_calc') moduleName = '结构计算'
      else if (lowerCode.includes('power')) moduleName = '功率计算'
      else if (lowerCode.includes('structure')) moduleName = '结构计算'
      else if (lowerCode.includes('thrust') || lowerCode.includes('roller') || lowerCode.includes('roller') || lowerCode.includes('bearing') || lowerCode.includes('leg') || lowerCode.includes('support') || moduleCode.includes('支腿')) moduleName = '支腿计算'
      else if (lowerCode.includes('shell') || lowerCode.includes('barrel') || lowerCode.includes('tube')) moduleName = '筒体计算'
      else moduleName = moduleCode ? `${moduleCode} 计算` : '未命名模块'
    }

    const scenes = Array.isArray(module.scenes) ? module.scenes : []
    const formulaCount = Number(
      module.formulaCount
      || module.formula_count
      || scenes.reduce(
        (count, scene) => count + (Array.isArray(scene.formulas) ? scene.formulas.length : Array.isArray(scene.rows) ? scene.rows.length : 0),
        0
      )
    )
    const sceneCount = Number(module.sceneCount || module.scene_count || scenes.length)
    let entryDescription = String(module.entryDescription || module.description || '').trim()
    if (!entryDescription) {
      entryDescription = '包含该模块所需的输入参数与公式网络，支持白盒化推导与校核分析。'
    }
    const nameKey = String(moduleName || '')
    if (!String(module.entryDescription || module.description || '').trim()) {
      if (nameKey.includes('功率')) entryDescription = '用于功率、扭矩、转速等主驱动侧计算，输出电机/减速机选型所需的关键参数推导。'
      else if (nameKey.includes('支腿')) entryDescription = '用于支腿承载、接触、挡轮等关键受力与校核计算。'
      else if (nameKey.includes('结构') || nameKey.includes('筒体')) entryDescription = '用于结构强度、载荷与关键部件校核计算。'
    }
    return {
      moduleCode,
      moduleName,
      sceneCount,
      formulaCount,
      entryDescription
    }
  }).filter((module) => module.moduleCode)

const handleCreate = () => {
  if (!currentModelId.value) {
    ElMessage.warning('当前无可用型号，无法创建模块')
    return
  }
  isEdit.value = false
  form.value = { moduleName: '', moduleCode: '' }
  dialogVisible.value = true
  if (formRef.value) formRef.value.clearValidate()
}

const handleCommand = (cmd, module) => {
  if (cmd === 'edit') {
    isEdit.value = true
    form.value = { moduleName: module.moduleName, moduleCode: module.moduleCode }
    dialogVisible.value = true
    if (formRef.value) formRef.value.clearValidate()
  } else if (cmd === 'delete') {
    ElMessageBox.confirm(`确定要删除计算模块 "${module.moduleName}" 吗？此操作不可恢复。`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(async () => {
      try {
        await deleteWorkbenchFormulaModule(currentModelId.value, module.moduleCode)
        ElMessage.success('模块已删除')
        loadData()
      } catch (error) {
        ElMessage.error('删除模块失败')
      }
    }).catch(() => {})
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      try {
        if (isEdit.value) {
          await renameWorkbenchFormulaModule(currentModelId.value, form.value.moduleCode, {
            module_name: form.value.moduleName
          })
          ElMessage.success('模块属性已更新')
        } else {
          await createWorkbenchFormulaModule(currentModelId.value, {
            module_code: form.value.moduleCode,
            module_name: form.value.moduleName
          })
          ElMessage.success('新建模块成功')
        }
        dialogVisible.value = false
        loadData()
      } catch (error) {
        ElMessage.error(isEdit.value ? '更新模块失败' : '新建模块失败')
      } finally {
        saving.value = false
      }
    }
  })
}

const goToWorkbench = (moduleCode) => {
  if (!canEnterExistingDesignWorkbench({ typeId, moduleCode })) {
    ElMessage.warning('必须先选择产品大类和计算模块')
    return
  }

  router.push({
    name: 'NewDesignWorkbench',
    query: {
      typeId,
      familyId: selectedFamilyId.value,
      versionId: selectedVersionId.value,
      moduleCode
    }
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.module-selection {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
  min-height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.header-section {
  margin-bottom: 24px;
  animation: fadeIn 0.4s ease-out;
}

.back-btn {
  font-size: 15px;
  margin-bottom: 16px;
  color: #64748b;
  padding: 0;
}

.back-btn:hover {
  color: #3b82f6;
}

.page-title {
  font-size: 30px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 12px 0;
}

.page-subtitle {
  font-size: 15px;
  color: #64748b;
  margin: 0;
}

.toolbar {
  margin-bottom: 32px;
  display: flex;
  justify-content: flex-end;
  animation: fadeIn 0.5s ease-out;
}

.content-section {
  flex: 1;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

.module-card {
  display: flex;
  flex-direction: column;
  padding: 24px;
  border-radius: 20px;
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
  transition: all 0.3s ease;
  animation: fadeInUp 0.5s ease-out backwards;
}

.module-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 32px rgba(37, 99, 235, 0.08);
  border-color: rgba(59, 130, 246, 0.4);
}

.module-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.module-name {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  line-height: 1.4;
}

.more-btn {
  color: #94a3b8;
  font-size: 20px;
  padding: 4px;
  height: auto;
}

.more-btn:hover {
  color: #3b82f6;
}

.module-meta {
  display: flex;
  align-items: center;
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}

.meta-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.meta-value {
  font-size: 22px;
  font-weight: 700;
  color: #2563eb;
  line-height: 1;
}

.meta-label {
  font-size: 12px;
  color: #64748b;
}

.meta-divider {
  width: 1px;
  height: 32px;
  background: #e2e8f0;
}

.module-desc {
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
  margin-bottom: 24px;
  flex: 1;
}

.module-action {
  margin-top: auto;
}

.enter-btn {
  width: 100%;
  border-radius: 10px;
  font-weight: 600;
  height: 40px;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
