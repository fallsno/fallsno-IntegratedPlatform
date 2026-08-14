<template>
  <div class="product-components">
    <el-page-header @back="$router.push('/product-types')">
      <template #content>
        <span>{{ productType?.type_name }} ({{ productType?.model_code || '' }}) - 部件明细表</span>
      </template>
    </el-page-header>

    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>部件清单</span>
            <el-input
              v-model="searchQuery"
              placeholder="搜索部件名称、编码、代号..."
              prefix-icon="Search"
              size="default"
              style="width: 300px; margin-left: 20px;"
              clearable
              @input="handleSearch"
            />
            <!-- 批量操作工具栏 -->
            <div v-if="selectedRows && selectedRows.length > 0" class="batch-actions">
              <el-divider direction="vertical" />
              <span class="selected-count">已选 {{ selectedRows.length }} 项</span>
              <el-button type="primary" size="small" @click="handleBatchCopy">
                <el-icon><CopyDocument /></el-icon>复制到...
              </el-button>
            </div>
          </div>
          <div class="header-right">
            <el-button type="warning" @click="handleUndo" :disabled="!canUndo">
              <el-icon><RefreshLeft /></el-icon>撤回 (Ctrl+Z)
            </el-button>
            <el-button type="primary" @click="handleAddRoot">
              <el-icon><Plus /></el-icon>新增顶层部件
            </el-button>
          </div>
        </div>
      </template>

      <el-table 
        ref="tableRef"
        :data="filteredComponents" 
        row-key="id" 
        :default-expanded-rows="expandedRowKeys"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        @expand-change="handleExpandChange"
        @row-dblclick="goToDesign"
        @selection-change="handleSelectionChange"
        :row-class-name="tableRowClassName"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="名称" min-width="400">
          <template #default="{ row, $index, treeNode }">
            <div class="name-cell" :style="{ paddingLeft: getIndent(treeNode?.level || 0) + 'px' }">
              <div v-if="!row.parent_id" class="root-indicator">
                <el-icon><FolderOpened /></el-icon>
              </div>
              <div v-else class="sub-indicator">
                <el-icon><Document /></el-icon>
              </div>
              <span :class="{ 
                'root-component-name': !row.parent_id, 
                'sub-component-name': row.parent_id 
              }">{{ row.name }}</span>
              <span class="level-symbol" :class="getLevelSymbolClass(treeNode?.level || 0)">
                {{ getLevelSymbol(treeNode?.level || 0) }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="序号" width="70" align="center">
          <template #default="{ row }">
            <span class="index-value">{{ row.index }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="编码" min-width="120" />
        <el-table-column prop="model_code" label="代号" min-width="120" />
        <el-table-column prop="quantity" label="数量" width="70" align="center" />
        <el-table-column label="操作" width="430" fixed="right">
          <template #default="{ row }">
            <el-button type="success" link @click.stop="handleAddChild(row)">新增子</el-button>
            <el-button type="warning" link @click.stop="handleChangeParent(row)">修改层级</el-button>
            <el-button type="primary" link @click.stop="openTemplateSyncDialog(row)">同步模板</el-button>
            <el-button type="primary" link @click.stop="openTemplateResyncDialog(row)">重同步</el-button>
            <el-button type="primary" link @click.stop="goToDesign(row)">设计</el-button>
            <el-button type="primary" link @click.stop="editComponent(row)">编辑</el-button>
            <el-button type="danger" link @click.stop="deleteComponent(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑部件对话框 -->
    <el-dialog v-model="showDialog" :title="editing ? '编辑部件' : '新增部件'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="序号">
          <el-input-number v-model="form.index" :min="1" />
        </el-form-item>
        <el-form-item label="编码">
          <el-input v-model="form.code" placeholder="例如 2100754605" />
        </el-form-item>
        <el-form-item label="代号">
          <el-input v-model="form.model_code" placeholder="例如 AT120B.1" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="例如 进料端座" />
        </el-form-item>
        <el-form-item label="数量">
          <el-input v-model="form.quantity" placeholder="例如 1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveComponent">保存</el-button>
      </template>
    </el-dialog>

    <!-- 修改层级对话框 -->
    <el-dialog v-model="showParentDialog" title="修改层级" width="500px">
      <el-form label-width="100px">
        <el-form-item label="当前部件">
          <span>{{ selectedComponent?.name }}</span>
        </el-form-item>
        <el-form-item label="新父级">
          <el-tree-select
            v-model="newParentId"
            :data="parentOptions"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="选择新的父级（不选则为顶层）"
            clearable
            check-strictly
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showParentDialog = false">取消</el-button>
        <el-button type="primary" @click="saveNewParent">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量复制对话框 -->
    <el-dialog v-model="showCloneDialog" title="批量复制部件到其他产品型号" width="550px">
      <el-form :model="cloneForm" label-width="120px">
        <el-form-item label="要复制的部件">
          <div class="selected-items-list" style="max-height: 200px; overflow-y: auto; display: flex; flex-wrap: wrap; gap: 5px; border: 1px solid #dcdfe6; padding: 10px; border-radius: 4px;">
            <el-tag v-for="item in selectedRows" :key="item.id" size="small">
              {{ item.name }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="目标型号" required>
          <el-select 
            v-model="cloneForm.targetTypeId" 
            placeholder="搜索名称、代号或机型..." 
            style="width: 100%" 
            filterable
            clearable
            @change="fetchTargetComponents"
          >
            <el-option
              v-for="item in productTypes"
              :key="item.id"
              :label="`${item.type_name} | ${item.model_code || '无代号'} | ${item.machine_model || '无机型'}`"
              :value="item.id"
            >
              <div class="product-type-option">
                <span class="option-name">{{ item.type_name }}</span>
                <span class="option-info">
                  <el-tag size="small" effect="plain">{{ item.model_code || 'N/A' }}</el-tag>
                  <el-tag size="small" type="success" effect="plain" style="margin-left: 5px">
                    {{ item.machine_model || 'N/A' }}
                  </el-tag>
                </span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="父级部件">
          <el-tree-select
            v-model="cloneForm.targetParentId"
            :data="targetComponents"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="选择目标父级（不选则为顶层）"
            clearable
            check-strictly
            :loading="loadingTarget"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCloneDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmCloneTo" :loading="cloning">确定复制</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showTemplateSyncDialog" title="同步设计模板到同系列型号" width="720px">
      <el-form label-width="120px">
        <el-form-item label="来源部件">
          <span>{{ templateSourceComponent?.name }}</span>
        </el-form-item>
        <el-form-item label="目标型号" required>
          <el-select
            v-model="templateSyncForm.targetTypeIds"
            multiple
            filterable
            placeholder="请选择目标型号"
            style="width: 100%"
            @change="handleTemplateTargetTypeChange"
          >
            <el-option
              v-for="item in availableTemplateTargetTypes"
              :key="item.id"
              :label="`${item.type_name} | ${item.model_code || '无代号'}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          v-for="targetTypeId in templateSyncForm.targetTypeIds"
          :key="targetTypeId"
          :label="`${getProductTypeName(targetTypeId)} 部件`"
          required
        >
          <el-tree-select
            v-model="templateSyncForm.targetComponentByType[targetTypeId]"
            :data="templateTargetComponents[targetTypeId] || []"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="选择目标部件"
            check-strictly
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="同步策略">
          <el-select v-model="templateSyncForm.syncMode" style="width: 100%">
            <el-option label="覆盖模板范围" value="overwrite_template_scope" />
            <el-option label="仅补缺失项" value="append_missing" />
          </el-select>
        </el-form-item>
        <el-form-item label="建立来源关系">
          <el-switch v-model="templateSyncForm.createLink" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTemplateSyncDialog = false">取消</el-button>
        <el-button type="primary" :loading="syncingTemplate" @click="submitTemplateSync">开始同步</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showTemplateResyncDialog" title="重新同步设计模板" width="680px">
      <el-form label-width="120px">
        <el-form-item label="来源部件">
          <span>{{ templateResyncSourceComponent?.name }}</span>
        </el-form-item>
        <el-form-item label="目标部件" required>
          <el-checkbox-group v-model="templateResyncForm.targetComponentIds" class="template-link-list">
            <el-checkbox
              v-for="link in resyncCandidateLinks"
              :key="link.id"
              :label="link.target_component_id"
            >
              {{ formatTemplateLinkLabel(link) }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="同步策略">
          <el-select v-model="templateResyncForm.syncMode" clearable placeholder="默认沿用上次策略" style="width: 100%">
            <el-option label="沿用上次策略" value="" />
            <el-option label="覆盖模板范围" value="overwrite_template_scope" />
            <el-option label="仅补缺失项" value="append_missing" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTemplateResyncDialog = false">取消</el-button>
        <el-button type="primary" :loading="resyncingTemplate" @click="submitTemplateResync">开始重同步</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FolderOpened, Document, Search, RefreshLeft, CopyDocument, Plus } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const typeId = route.params.typeId
const productType = ref(null)
const components = ref([])
const loading = ref(false)
const expandedRowKeys = ref([])
const searchQuery = ref('')
const tableRef = ref(null)

const historyStack = ref([])

const filterTree = (list, query) => {
  if (!query) return list
  const result = []
  const lowerQuery = query.toLowerCase()
  
  const searchInNode = (node) => {
    const matchName = node.name?.toLowerCase().includes(lowerQuery)
    const matchCode = node.code?.toLowerCase().includes(lowerQuery)
    const matchModel = node.model_code?.toLowerCase().includes(lowerQuery)
    const hasMatch = matchName || matchCode || matchModel
    
    let filteredChildren = []
    if (node.children && node.children.length > 0) {
      filteredChildren = node.children.filter(searchInNode)
    }
    
    if (hasMatch || filteredChildren.length > 0) {
      return {
        ...node,
        children: filteredChildren.length > 0 ? filteredChildren : node.children
      }
    }
    return null
  }
  
  list.forEach(node => {
    const filteredNode = searchInNode(node)
    if (filteredNode) {
      result.push(filteredNode)
    }
  })
  
  return result
}

const filteredComponents = computed(() => {
  return filterTree(components.value, searchQuery.value)
})

const handleSearch = () => {
  if (searchQuery.value) {
    expandMatchingNodes(components.value, searchQuery.value)
  } else {
    loadExpandState()
  }
}

const expandMatchingNodes = (list, query) => {
  const lowerQuery = query.toLowerCase()
  const matchedIds = []
  
  const traverse = (nodes) => {
    nodes.forEach(node => {
      const matchName = node.name?.toLowerCase().includes(lowerQuery)
      const matchCode = node.code?.toLowerCase().includes(lowerQuery)
      const matchModel = node.model_code?.toLowerCase().includes(lowerQuery)
      
      if (matchName || matchCode || matchModel) {
        matchedIds.push(node.id)
      }
      
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      }
    })
  }
  
  traverse(list)
  
  const expandAllParents = (nodes, targetId, parentIds = []) => {
    for (const node of nodes) {
      if (node.id === targetId) {
        return parentIds
      }
      if (node.children && node.children.length > 0) {
        const result = expandAllParents(node.children, targetId, [...parentIds, node.id])
        if (result) return result
      }
    }
    return null
  }
  
  const nodesToExpand = new Set()
  
  matchedIds.forEach(id => {
    const parents = expandAllParents(list, id)
    if (parents) {
      parents.forEach(pid => {
        nodesToExpand.add(pid)
      })
    }
    nodesToExpand.add(id)
  })
  
  expandedRowKeys.value = Array.from(nodesToExpand)
  saveExpandState()
  
  nextTick(() => {
    if (tableRef.value) {
      const expandRowById = (nodes, targetIds) => {
        nodes.forEach(node => {
          if (targetIds.has(node.id) && tableRef.value) {
            tableRef.value.toggleRowExpansion(node, true)
          }
          if (node.children && node.children.length > 0) {
            expandRowById(node.children, targetIds)
          }
        })
      }
      expandRowById(components.value, nodesToExpand)
    }
  })
}

const showDialog = ref(false)
const editing = ref(false)
const form = ref({ index: 1, code: '', model_code: '', name: '', quantity: '1', parent_id: null, product_type_id: typeId })
let editingId = null

const showParentDialog = ref(false)
const selectedComponent = ref(null)
const newParentId = ref(null)
const parentOptions = ref([])

const saveExpandState = () => {
  localStorage.setItem(`product_components_expand_${typeId}`, JSON.stringify(expandedRowKeys.value))
}

const loadExpandState = () => {
  const saved = localStorage.getItem(`product_components_expand_${typeId}`)
  if (saved) {
    try {
      expandedRowKeys.value = JSON.parse(saved)
    } catch (e) {
      expandedRowKeys.value = []
    }
  }
}

const selectedRowId = ref(null)
const selectedRows = ref([])

// 批量复制相关变量
const showCloneDialog = ref(false)
const cloning = ref(false)
const productTypes = ref([])
const targetComponents = ref([])
const loadingTarget = ref(false)
const cloneForm = ref({
  targetTypeId: null,
  targetParentId: null
})
const showTemplateSyncDialog = ref(false)
const syncingTemplate = ref(false)
const templateSourceComponent = ref(null)
const templateTargetComponents = ref({})
const templateSyncForm = ref({
  targetTypeIds: [],
  targetComponentByType: {},
  syncMode: 'overwrite_template_scope',
  createLink: true
})
const showTemplateResyncDialog = ref(false)
const resyncingTemplate = ref(false)
const templateResyncSourceComponent = ref(null)
const templateLinks = ref([])
const templateResyncForm = ref({
  targetComponentIds: [],
  syncMode: ''
})
const availableTemplateTargetTypes = computed(() => (
  productTypes.value.filter(item => String(item.id) !== String(typeId))
))
const resyncCandidateLinks = computed(() => (
  templateLinks.value.filter(link => link.source_component_id === templateResyncSourceComponent.value?.id)
))

const handleRowClick = (row) => {
  selectedRowId.value = row.id
  // 同时切换勾选状态（增强交互）
  if (tableRef.value) {
    tableRef.value.toggleRowSelection(row)
  }
}

const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

const tableRowClassName = ({ row }) => {
  if (selectedRowId.value === row.id) {
    return 'selected-row'
  }
  return ''
}

// 批量复制逻辑
const handleBatchCopy = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先勾选要复制的部件')
    return
  }
  cloneForm.value = { targetTypeId: null, targetParentId: null }
  showCloneDialog.value = true
  
  // 获取产品类型列表
  try {
    await fetchProductTypes()
  } catch (e) {
    ElMessage.error('获取产品型号列表失败')
  }
}

const fetchTargetComponents = async (typeId) => {
  if (!typeId) {
    targetComponents.value = []
    return
  }
  loadingTarget.value = true
  try {
    const res = await axios.get('/product-components/', { params: { type_id: typeId } })
    targetComponents.value = res.data
  } catch (e) {
    ElMessage.error('获取目标型号部件失败')
  } finally {
    loadingTarget.value = false
  }
}

const fetchProductTypes = async () => {
  if (productTypes.value.length > 0) {
    return
  }
  const res = await axios.get('/product-types/')
  productTypes.value = res.data
}

const fetchTemplateTargetComponents = async (targetTypeId) => {
  if (!targetTypeId) return
  if (templateTargetComponents.value[targetTypeId]) return

  const res = await axios.get('/product-components/', { params: { type_id: targetTypeId } })
  templateTargetComponents.value = {
    ...templateTargetComponents.value,
    [targetTypeId]: res.data
  }
}

const getProductTypeName = (targetTypeId) => {
  const productType = productTypes.value.find(item => item.id === targetTypeId)
  return productType?.type_name || `型号 ${targetTypeId}`
}

const formatTemplateLinkLabel = (link) => {
  const productType = productTypes.value.find(item => item.id === link.target_type_id)
  const modelLabel = productType?.model_code || productType?.type_name || `型号 ${link.target_type_id}`
  return `${modelLabel} / 部件 #${link.target_component_id}`
}

const openTemplateSyncDialog = async (row) => {
  templateSourceComponent.value = row
  templateTargetComponents.value = {}
  templateSyncForm.value = {
    targetTypeIds: [],
    targetComponentByType: {},
    syncMode: 'overwrite_template_scope',
    createLink: true
  }
  try {
    await fetchProductTypes()
    showTemplateSyncDialog.value = true
  } catch (error) {
    ElMessage.error('获取目标型号列表失败')
  }
}

const handleTemplateTargetTypeChange = async (targetTypeIds) => {
  const nextMapping = {}
  for (const targetTypeId of targetTypeIds) {
    nextMapping[targetTypeId] = templateSyncForm.value.targetComponentByType[targetTypeId] || null
    await fetchTemplateTargetComponents(targetTypeId)
  }
  templateSyncForm.value.targetComponentByType = nextMapping
}

const submitTemplateSync = async () => {
  if (!templateSourceComponent.value) return
  if (templateSyncForm.value.targetTypeIds.length === 0) {
    ElMessage.warning('请选择至少一个目标型号')
    return
  }

  const targets = templateSyncForm.value.targetTypeIds.map(targetTypeId => ({
    target_type_id: targetTypeId,
    target_component_id: templateSyncForm.value.targetComponentByType[targetTypeId]
  }))

  if (targets.some(item => !item.target_component_id)) {
    ElMessage.warning('请为每个目标型号选择目标部件')
    return
  }

  syncingTemplate.value = true
  try {
    const res = await axios.post(`/product-components/${templateSourceComponent.value.id}/sync-template`, {
      targets,
      sync_mode: templateSyncForm.value.syncMode,
      create_link: templateSyncForm.value.createLink
    })
    ElMessage.success(`已同步 ${res.data.results.length} 个目标部件`)
    showTemplateSyncDialog.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '模板同步失败')
  } finally {
    syncingTemplate.value = false
  }
}

const openTemplateResyncDialog = async (row) => {
  templateResyncSourceComponent.value = row
  templateResyncForm.value = {
    targetComponentIds: [],
    syncMode: ''
  }
  try {
    await fetchProductTypes()
    const res = await axios.get(`/product-components/${row.id}/template-links`)
    templateLinks.value = res.data
    const candidateLinks = res.data.filter(link => link.source_component_id === row.id)
    if (candidateLinks.length === 0) {
      ElMessage.warning('该部件暂无已建立的模板来源关系')
      return
    }
    templateResyncForm.value.targetComponentIds = candidateLinks.map(link => link.target_component_id)
    showTemplateResyncDialog.value = true
  } catch (error) {
    ElMessage.error('获取模板关系失败')
  }
}

const submitTemplateResync = async () => {
  if (!templateResyncSourceComponent.value) return
  if (templateResyncForm.value.targetComponentIds.length === 0) {
    ElMessage.warning('请至少选择一个目标部件')
    return
  }

  resyncingTemplate.value = true
  try {
    const payload = {
      target_component_ids: templateResyncForm.value.targetComponentIds,
      sync_mode: templateResyncForm.value.syncMode || null
    }
    const res = await axios.post(`/product-components/${templateResyncSourceComponent.value.id}/resync-template`, payload)
    ElMessage.success(`已重同步 ${res.data.results.length} 个目标部件`)
    showTemplateResyncDialog.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '模板重同步失败')
  } finally {
    resyncingTemplate.value = false
  }
}

const confirmCloneTo = async () => {
  if (!cloneForm.value.targetTypeId) {
    ElMessage.warning('请选择目标产品型号')
    return
  }
  
  cloning.value = true
  try {
    // 循环执行克隆
    const promises = selectedRows.value.map(row => 
      axios.post(`/product-components/${row.id}/clone`, null, {
        params: {
          target_type_id: cloneForm.value.targetTypeId,
          target_parent_id: cloneForm.value.targetParentId || null
        }
      })
    )
    await Promise.all(promises)
    ElMessage.success(`成功复制 ${selectedRows.value.length} 个部件`)
    showCloneDialog.value = false
    // 如果克隆到了当前型号，则刷新
    if (cloneForm.value.targetTypeId == typeId) {
      fetchComponents()
    }
  } catch (e) {
    ElMessage.error('批量复制失败')
  } finally {
    cloning.value = false
  }
}

const handleExpandChange = (row, expandedRows) => {
  expandedRowKeys.value = expandedRows.map(r => r.id)
  saveExpandState()
}

const saveToHistory = () => {
  const snapshot = JSON.parse(JSON.stringify(components.value))
  historyStack.value.push(snapshot)
  if (historyStack.value.length > 20) {
    historyStack.value.shift()
  }
}

const canUndo = computed(() => historyStack.value.length > 0)

const handleUndo = async () => {
  if (!canUndo.value) return
  
  const lastState = historyStack.value.pop()
  if (!lastState) return
  
  try {
    const reorderData = []
    const flattenTree = (nodes, parentId = null) => {
      nodes.forEach((node, idx) => {
        reorderData.push({
          id: node.id,
          index: idx + 1,
          parent_id: parentId
        })
        if (node.children && node.children.length > 0) {
          flattenTree(node.children, node.id)
        }
      })
    }
    flattenTree(lastState)
    
    await axios.post('/product-components/reorder', reorderData)
    
    components.value = JSON.parse(JSON.stringify(lastState))
    
    ElMessage.success('撤回成功')
    
    nextTick(() => {
      if (tableRef.value) {
        tableRef.value.doLayout()
      }
    })
  } catch (e) {
    console.error('撤回失败:', e)
    ElMessage.error('撤回失败')
  }
}

const handleKeyDown = (e) => {
  const key = e.key.toLowerCase()
  const isCtrl = e.ctrlKey || e.metaKey
  
  if (isCtrl && key === 'z') {
    e.preventDefault()
    handleUndo()
  }
}

const fetchProductType = async () => {
  const res = await axios.get(`/product-types/${typeId}`)
  productType.value = res.data
}

const fetchComponents = async () => {
  loading.value = true
  try {
    const res = await axios.get(`/product-components/`, { params: { type_id: typeId } })
    components.value = res.data
    loadExpandState()
  } catch (e) {
    ElMessage.error('获取部件列表失败')
  } finally {
    loading.value = false
  }
}

const handleAddRoot = () => {
  saveToHistory()
  editing.value = false
  form.value = { index: components.value.length + 1, code: '', model_code: '', name: '', quantity: '1', parent_id: null, product_type_id: typeId }
  showDialog.value = true
}

const handleAddChild = (parent) => {
  saveToHistory()
  editing.value = false
  form.value = { index: (parent.children?.length || 0) + 1, code: '', model_code: '', name: '', quantity: '1', parent_id: parent.id, product_type_id: typeId }
  showDialog.value = true
}

const handleChangeParent = (row) => {
  saveToHistory()
  selectedComponent.value = row
  newParentId.value = row.parent_id
  
  const buildOptions = (nodes, excludeId) => {
    const result = []
    nodes.forEach(node => {
      if (node.id !== excludeId) {
        const option = { ...node }
        if (node.children && node.children.length > 0) {
          option.children = buildOptions(node.children, excludeId)
        }
        result.push(option)
      }
    })
    return result
  }
  
  parentOptions.value = buildOptions(components.value, row.id)
  showParentDialog.value = true
}

const saveNewParent = async () => {
  if (!selectedComponent.value) return
  
  try {
    const siblings = newParentId.value 
      ? (findComponentById(components.value, newParentId.value)?.children || [])
      : components.value.filter(c => !c.parent_id)
    
    const reorderData = [
      { 
        id: selectedComponent.value.id, 
        index: siblings.length + 1, 
        parent_id: newParentId.value || null 
      }
    ]
    
    await axios.post('/product-components/reorder', reorderData)
    ElMessage.success('移动成功')
    showParentDialog.value = false
    fetchComponents()
  } catch (e) {
    ElMessage.error('移动失败')
    historyStack.value.pop()
  }
}

const saveComponent = async () => {
  if (!form.value.code.trim() || !form.value.name.trim()) {
    ElMessage.warning('编码和名称不能为空')
    return
  }
  try {
    if (editing.value) {
      await axios.put(`/product-components/${editingId}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/product-components/', form.value)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    fetchComponents()
  } catch (e) {
    ElMessage.error('保存失败')
    historyStack.value.pop()
  }
}

const editComponent = (row) => {
  saveToHistory()
  editing.value = true
  editingId = row.id
  form.value = { ...row }
  showDialog.value = true
}

const deleteComponent = (id) => {
  ElMessageBox.confirm('确定删除该组件及其下所有子组件吗？', '警告', { type: 'warning' })
    .then(async () => {
      saveToHistory()
      await axios.delete(`/product-components/${id}`)
      ElMessage.success('删除成功')
      fetchComponents()
    })
}

const goToDesign = (row) => {
  router.push({ name: 'DesignWorkbench', query: { componentId: row.id } })
}

const getIndent = (level) => {
  if (level <= 0) return 0
  return level * 20
}

const getLevelSymbol = (level) => {
  const symbols = ['◆', '●', '■', '▲', '★']
  return symbols[level] || '○'
}

const getLevelSymbolClass = (level) => {
  const classes = ['level-0-symbol', 'level-1-symbol', 'level-2-symbol', 'level-3-symbol', 'level-4-symbol']
  return classes[level] || ''
}

const findComponentById = (list, id) => {
  for (const node of list) {
    if (node.id === id) return node
    if (node.children && node.children.length > 0) {
      const found = findComponentById(node.children, id)
      if (found) return found
    }
  }
  return null
}

onMounted(async () => {
  await fetchProductType()
  await fetchComponents()
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.product-components { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-left { display: flex; align-items: center; gap: 10px; }
.batch-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 10px;
}
.selected-count {
  font-size: 13px;
  color: #909399;
}
.selected-items-list {
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px;
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}
.product-type-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.option-name {
  font-weight: bold;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}
.option-info {
  display: flex;
  align-items: center;
}
.template-link-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.name-cell { display: flex; gap: 10px; }
.name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 32px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}
.name-cell:hover {
  background: rgba(64, 158, 255, 0.1);
}
.name-cell.is-selected {
  background: rgba(64, 158, 255, 0.2);
  outline: 1px solid #409eff;
}
.root-indicator {
  color: #409eff;
  font-size: 18px;
  display: flex;
  align-items: center;
}
.sub-indicator {
  color: #67c23a;
  font-size: 16px;
  display: flex;
  align-items: center;
}
.root-component-name {
  font-weight: 700;
  font-size: 15px;
  color: #303133;
}
.sub-component-name {
  font-weight: 500;
  color: #606266;
}
.level-symbol {
  margin-left: 8px;
  font-weight: bold;
  font-size: 14px;
}
.level-0-symbol {
  color: #409eff;
}
.level-1-symbol {
  color: #67c23a;
}
.level-2-symbol {
  color: #e6a23c;
}
.level-3-symbol {
  color: #f56c6c;
}
.level-4-symbol {
  color: #909399;
}
.index-value {
  min-width: 30px;
  text-align: center;
  font-weight: 600;
}
</style>

<style>
.product-components .el-table__expand-icon {
  margin-right: 8px;
}

.product-components .el-table td {
  padding: 14px 0;
}

.product-components .el-table__row--level-0 {
  background: linear-gradient(90deg, #ecf5ff 0%, #f5f7fa 100%) !important;
  border-left: 4px solid #409eff !important;
}

.product-components .el-table__row--level-0 td {
  font-weight: 600 !important;
  font-size: 14px !important;
}

.product-components .el-table__row--level-1 {
  background: linear-gradient(90deg, #f0f9ff 0%, #ffffff 100%) !important;
  border-left: 4px solid #67c23a !important;
}

.product-components .el-table__row--level-2 {
  background: linear-gradient(90deg, #fdf6ec 0%, #ffffff 100%) !important;
  border-left: 4px solid #e6a23c !important;
}

.product-components .el-table__row--level-3 {
  background: linear-gradient(90deg, #fef0f0 0%, #ffffff 100%) !important;
  border-left: 4px solid #f56c6c !important;
}

.product-components .el-table__row--level-4 {
  background: linear-gradient(90deg, #f4f4f5 0%, #ffffff 100%) !important;
  border-left: 4px solid #909399 !important;
}
</style>
