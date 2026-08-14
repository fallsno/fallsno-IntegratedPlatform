<template>
  <div class="product-tree-container">
    <div class="tree-header">
      <el-input
        v-model="filterText"
        placeholder="搜索产品或部件..."
        size="small"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <div class="tree-actions">
        <el-tooltip content="刷新" placement="top">
          <el-button link size="small" @click="refreshTree">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="新建产品" placement="top">
          <el-button link size="small" type="primary" @click="$router.push('/product-types')">
            <el-icon><Plus /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </div>
    
    <div class="tree-body" v-loading="loading">
      <el-tree
        ref="treeRef"
        :props="defaultProps"
        :load="loadNode"
        lazy
        node-key="id"
        highlight-current
        :filter-node-method="filterNode"
        @node-click="handleNodeClick"
        :expand-on-click-node="false"
        draggable
        :allow-drag="allowDrag"
        :allow-drop="allowDrop"
        @node-drop="handleDrop"
        class="custom-tree"
      >
        <template #default="{ node, data }">
          <span class="custom-tree-node" :title="data.name">
            <el-icon class="node-icon">
              <Folder v-if="data.type === 'product'" />
              <Document v-else />
            </el-icon>
            <!-- 优先显示代号，如果没有则显示名称 -->
            <span class="node-label">{{ data.code || data.name }}</span>
            <span class="node-name-sub" v-if="data.code && data.name && data.name !== data.code">({{ data.name }})</span>
          </span>
        </template>
      </el-tree>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const filterText = ref('')
const treeRef = ref(null)
const loading = ref(false)

const isDesignDataView = computed(() => route.name === 'DesignWorkbench')

const defaultProps = {
  children: 'children',
  label: 'name',
  isLeaf: 'isLeaf'
}

watch(filterText, (val) => {
  treeRef.value?.filter(val)
})

const filterNode = (value, data) => {
  if (!value) return true
  return data.name.includes(value) || (data.code && data.code.includes(value))
}

let rootResolve = null

const loadNode = async (node, resolve) => {
  if (node.level === 0) {
    rootResolve = resolve
    loading.value = true
    try {
      const res = await axios.get('/product-types/')
      const products = res.data.map(p => ({
        id: `prod_${p.id}`,
        real_id: p.id,
        name: p.type_name || p.model_code,
        code: p.model_code,
        type: 'product',
        isLeaf: false
      }))
      resolve(products)
    } catch (err) {
      console.error('获取产品树失败:', err)
      ElMessage.error('获取产品树失败')
      resolve([])
    } finally {
      loading.value = false
    }
  } else if (node.level === 1 && node.data.type === 'product') {
    // 加载部件
    try {
      const res = await axios.get(`/product-components/?type_id=${node.data.real_id}`)
      const mapComponents = (comps) => {
        return comps.map(c => ({
          id: `comp_${c.id}`,
          real_id: c.id,
          product_id: node.data.real_id,
          name: c.name,
          code: c.code,
          type: 'component',
          isLeaf: !c.children || c.children.length === 0,
          children: c.children ? mapComponents(c.children) : []
        }))
      }
      resolve(mapComponents(res.data))
    } catch (err) {
      console.error('获取部件树失败:', err)
      resolve([])
    }
  } else if (node.data.type === 'component') {
    // 部件下的子部件已经在上面一起加载并映射了，但因为是 lazy 树，el-tree 需要逐层 resolve
    resolve(node.data.children || [])
  } else {
    resolve([])
  }
}

const refreshTree = () => {
  if (rootResolve) {
    // 强制重新加载根节点
    // Element Plus 懒加载树刷新有点麻烦，可以设置 key 强制重渲染，或者手动清空子节点
    // 这里采用简单方案：重置整个树的加载状态
    treeRef.value.store.root.childNodes = []
    loadNode(treeRef.value.store.root, rootResolve)
  }
}

const handleNodeClick = (data) => {
  // 无论是在什么页面，点击树节点都跳转到公式工作台
  if (data.type === 'product') {
    router.push({ name: 'DesignWorkbench', query: { typeId: data.real_id } })
  } else {
    router.push({ name: 'DesignWorkbench', query: { componentId: data.real_id } })
  }
}

// 拖拽层级调整逻辑
const allowDrag = (node) => {
  // 只允许拖拽部件
  return node.data.type === 'component'
}

const allowDrop = (draggingNode, dropNode, type) => {
  // 不允许跨产品拖拽
  if (draggingNode.data.product_id !== dropNode.data.product_id && dropNode.data.type === 'component') return false
  
  // 如果放到产品节点上，只能放 inside（作为顶层部件）
  if (dropNode.data.type === 'product') {
    return type === 'inner'
  }
  
  // 循环引用检测：由于树本身不会有循环，但为了防止前端出错，做个保护
  // 实际上 Element Plus 的 el-tree 不会允许把父节点拖到子节点内部
  return true
}

const handleDrop = async (draggingNode, dropNode, dropType, ev) => {
  // 准备调用后端的拖拽排序/层级更新接口
  const compId = draggingNode.data.real_id
  let newParentId = null
  let newIndex = 0

  if (dropNode.data.type === 'product') {
    newParentId = null
    // 假设放到最后
    newIndex = dropNode.childNodes.length
  } else {
    if (dropType === 'inner') {
      newParentId = dropNode.data.real_id
      newIndex = dropNode.childNodes.length
    } else {
      newParentId = dropNode.parent.data.type === 'product' ? null : dropNode.parent.data.real_id
      const siblings = dropNode.parent.childNodes
      const dropIndex = siblings.findIndex(n => n.data.real_id === dropNode.data.real_id)
      newIndex = dropType === 'before' ? dropIndex : dropIndex + 1
    }
  }

  try {
    await axios.post(`/product-components/${compId}/reorder`, {
      new_parent_id: newParentId,
      new_index: newIndex
    })
    ElMessage.success('层级调整成功')
  } catch (err) {
    console.error('层级调整失败:', err)
    ElMessage.error(err.response?.data?.detail || '层级调整失败，请刷新重试')
    refreshTree() // 失败时刷新树以恢复原状
  }
}
</script>

<style scoped>
.product-tree-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-right: 1px solid #e2e8f0;
}

.tree-header {
  padding: 10px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  gap: 10px;
  align-items: center;
}

.tree-actions {
  display: flex;
  gap: 5px;
}

.tree-body {
  flex: 1;
  overflow: auto;
  padding: 10px 0;
}

.custom-tree {
  background: transparent;
}

.custom-tree-node {
  display: flex;
  align-items: center;
  font-size: 13px;
  width: 100%;
}

.node-icon {
  margin-right: 6px;
  color: #64748b;
}

.node-label {
  font-weight: 500;
  color: #1e293b;
}

.node-name-sub {
  margin-left: 8px;
  color: #64748b;
  font-size: 12px;
}
</style>
