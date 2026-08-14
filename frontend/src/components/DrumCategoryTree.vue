<template>
  <div class="drum-category-tree">
    <div class="tree-toolbar">
      <div class="tree-title">{{ title }}</div>
    </div>

    <el-scrollbar class="tree-scroll">
      <el-tree
        ref="treeRef"
        :data="filteredTreeData"
        :current-node-key="currentNodeId"
        default-expand-all
        highlight-current
        node-key="id"
        @node-click="handleNodeClick"
      >
        <template #default="{ data }">
          <div class="tree-node">
            <span class="tree-node__label">{{ data.label }}</span>
          </div>
        </template>
      </el-tree>
      <el-empty v-if="!filteredTreeData.length" description="未找到匹配节点" />
    </el-scrollbar>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  treeData: {
    type: Array,
    default: () => []
  },
  currentNodeId: {
    type: String,
    default: ''
  },
  searchKeyword: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: '滚筒分类树'
  }
})

const emit = defineEmits(['select'])

const treeRef = ref(null)

const matchesKeyword = (node, normalizedKeyword) => {
  if (!normalizedKeyword) return true
  const content = [
    node.label,
    node.raw?.type_name,
    node.raw?.family_code,
    node.raw?.family_name,
    node.raw?.version_code,
    node.raw?.display_name
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
  return content.includes(normalizedKeyword)
}

const filterNodes = (rows, normalizedKeyword) => {
  return (Array.isArray(rows) ? rows : []).reduce((accumulator, node) => {
    const children = filterNodes(node.children || [], normalizedKeyword)
    if (matchesKeyword(node, normalizedKeyword) || children.length) {
      accumulator.push({
        ...node,
        children
      })
    }
    return accumulator
  }, [])
}

const filteredTreeData = computed(() => filterNodes(props.treeData, props.searchKeyword.trim().toLowerCase()))

const handleNodeClick = (data, node) => {
  emit('select', { data, node })
}

watch(
  () => props.currentNodeId,
  (value) => {
    if (value && treeRef.value) {
      treeRef.value.setCurrentKey(value)
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.drum-category-tree {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.tree-toolbar {
  display: grid;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.tree-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.tree-scroll {
  flex: 1;
  min-height: 0;
  padding-top: 12px;
}

.tree-node {
  width: 100%;
  padding: 6px 8px 6px 0;
  box-sizing: border-box;
}

.tree-node__label {
  display: block;
  font-weight: 600;
  line-height: 1.4;
  color: #0f172a;
  word-break: break-word;
}

:deep(.el-tree-node__content) {
  height: auto;
  min-height: 32px;
  align-items: flex-start;
  padding-top: 2px;
  padding-bottom: 2px;
}

:deep(.el-tree-node__expand-icon) {
  margin-top: 8px;
}
</style>
