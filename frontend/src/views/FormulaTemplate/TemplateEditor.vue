<template>
  <section class="template-editor">
    <el-card shadow="never" class="template-editor__meta">
      <template #header>
        <div class="header-bar">
          <div>
            <div class="page-title">模板编辑器</div>
            <div class="page-subtitle">按模块 / 计算块维护公式模板，供型号工作台执行。</div>
          </div>
          <div class="header-actions">
            <el-button @click="router.push('/formula-templates')">返回列表</el-button>
            <el-button :loading="loading" @click="loadTemplate">刷新</el-button>
            <el-button type="primary" :loading="saving" @click="saveTemplate">保存模板</el-button>
          </div>
        </div>
      </template>

      <el-form label-width="88px" class="meta-form">
        <el-form-item label="模板编码">
          <el-input v-model="template.template_code" />
        </el-form-item>
        <el-form-item label="模板名称">
          <el-input v-model="template.template_name" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="template.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
    </el-card>

    <div v-loading="loading" class="template-editor__content">
      <el-card
        v-for="(module, moduleIndex) in template.modules"
        :key="`module-${moduleIndex}`"
        shadow="never"
        class="module-card"
      >
        <template #header>
          <div class="module-header">
            <el-input v-model="module.module_name" placeholder="模块名称" />
            <el-input v-model="module.module_code" placeholder="模块编码" />
            <el-button link type="danger" @click="removeModule(moduleIndex)">删除模块</el-button>
          </div>
        </template>

        <div class="scene-list">
          <div v-for="(scene, sceneIndex) in module.scenes" :key="`scene-${moduleIndex}-${sceneIndex}`" class="scene-block">
            <div class="scene-header">
              <el-input v-model="scene.scene_name" placeholder="计算块名称" />
              <el-input v-model="scene.scene_code" placeholder="计算块编码" />
              <el-button link type="primary" @click="addItem(scene)">新增公式</el-button>
              <el-button link type="danger" @click="removeScene(module, sceneIndex)">删除计算块</el-button>
            </div>

            <el-table :data="scene.items" stripe size="small">
              <el-table-column label="公式名称" min-width="180">
                <template #default="{ row }">
                  <el-input v-model="row.formula_name" />
                </template>
              </el-table-column>
              <el-table-column label="表达式" min-width="320">
                <template #default="{ row }">
                  <el-input v-model="row.expression" />
                </template>
              </el-table-column>
              <el-table-column label="变量" min-width="200">
                <template #default="{ row }">
                  <el-input
                    :model-value="formatVariables(row.variables)"
                    placeholder="用逗号分隔变量名"
                    @input="updateVariables(row, $event)"
                  />
                </template>
              </el-table-column>
              <el-table-column label="单位" width="120">
                <template #default="{ row }">
                  <el-input v-model="row.unit" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="90" fixed="right">
                <template #default="{ $index }">
                  <el-button link type="danger" @click="removeItem(scene, $index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <div class="module-footer">
          <el-button type="primary" plain @click="addScene(module)">新增计算块</el-button>
        </div>
      </el-card>

      <el-empty v-if="!template.modules.length" description="当前模板还没有模块">
        <el-button type="primary" @click="addModule">新增模块</el-button>
      </el-empty>
    </div>

    <div class="footer-bar">
      <el-button type="primary" plain @click="addModule">新增模块</el-button>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { fetchFormulaTemplateStructure, saveFormulaTemplateStructure } from '@/api/drumDesign'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const template = ref({
  id: null,
  template_code: '',
  template_name: '',
  description: '',
  modules: []
})

const addModule = () => {
  template.value.modules.push({
    module_code: `module_${template.value.modules.length + 1}`,
    module_name: `模块 ${template.value.modules.length + 1}`,
    scenes: []
  })
}

const removeModule = (index) => {
  template.value.modules.splice(index, 1)
}

const addScene = (module) => {
  module.scenes = module.scenes || []
  module.scenes.push({
    scene_code: `scene_${module.scenes.length + 1}`,
    scene_name: `计算块 ${module.scenes.length + 1}`,
    items: []
  })
}

const removeScene = (module, index) => {
  module.scenes.splice(index, 1)
}

const addItem = (scene) => {
  scene.items = scene.items || []
  scene.items.push({
    formula_name: `公式 ${scene.items.length + 1}`,
    expression: '=0',
    variables: {},
    unit: ''
  })
}

const removeItem = (scene, index) => {
  scene.items.splice(index, 1)
}

const formatVariables = (variables = {}) => Object.keys(variables || {}).join(', ')

const updateVariables = (row, value) => {
  const names = String(value || '')
    .split(/[，,]/)
    .map((item) => item.trim())
    .filter(Boolean)
  row.variables = Object.fromEntries(names.map((name) => [name, '']))
}

const normalizeTemplate = (payload = {}) => ({
  id: payload.id || null,
  template_code: payload.template_code || '',
  template_name: payload.template_name || '',
  description: payload.description || '',
  is_active: payload.is_active ?? true,
  modules: Array.isArray(payload.modules) ? payload.modules : []
})

const loadTemplate = async () => {
  loading.value = true
  try {
    const payload = await fetchFormulaTemplateStructure(route.params.id)
    template.value = normalizeTemplate(payload)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载模板结构失败')
  } finally {
    loading.value = false
  }
}

const saveTemplate = async () => {
  saving.value = true
  try {
    const payload = await saveFormulaTemplateStructure(route.params.id, template.value)
    template.value = normalizeTemplate(payload)
    ElMessage.success('模板结构已保存')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存模板结构失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadTemplate)
</script>

<style scoped>
.template-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
}

.template-editor__content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-bar,
.module-header,
.scene-header,
.footer-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-bar,
.scene-header {
  justify-content: space-between;
}

.header-actions,
.module-header {
  display: flex;
  gap: 8px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.page-subtitle {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
}

.scene-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.scene-block {
  padding: 12px;
  border: 1px solid #dbe3ef;
  border-radius: 12px;
  background: #f8fafc;
}

.module-footer {
  margin-top: 12px;
}
</style>
