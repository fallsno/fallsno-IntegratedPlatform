<template>
  <el-card class="module-card" shadow="never" :class="{ 'is-active': active }">
    <div class="module-card__header" @click="emit('select', module)">
      <div class="module-card__title-wrap">
        <el-tooltip v-if="!editing" :content="moduleSummaryText" placement="top">
          <div class="module-card__title" :title="moduleTitle">{{ moduleTitle }}</div>
        </el-tooltip>
        <el-input
          v-else
          v-model="draftName"
          size="small"
          placeholder="请输入模块名称"
          @keyup.enter="handleRename"
        />
      </div>
      <div class="module-card__actions" @click.stop>
        <el-tooltip content="新增场景" placement="top">
          <el-button circle text @click="emit('create-scene', module)">
            <el-icon><Plus /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip :content="editing ? '确认重命名' : '重命名'" placement="top">
          <el-button v-if="!editing" circle text @click="editing = true">
            <el-icon><EditPen /></el-icon>
          </el-button>
          <el-button v-else circle text type="primary" @click="handleRename">
            <el-icon><Check /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip v-if="editing" content="取消" placement="top">
          <el-button circle text @click="handleCancelEdit">
            <el-icon><Close /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="跨型号同步" placement="top">
          <el-button circle text @click="emit('sync-module', module)">
            <el-icon><Connection /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="删除模块" placement="top">
          <el-button circle text type="danger" @click="emit('delete-module', module)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </el-tooltip>
        <el-icon class="module-card__toggle">
          <ArrowDownBold v-if="active" />
          <ArrowRightBold v-else />
        </el-icon>
      </div>
    </div>
    
    <div class="module-card__sync-info" v-if="module.sync_info && !active">
      <el-tag size="small" type="info" class="mr-2">来源: {{ module.sync_info.source_version_name }}</el-tag>
      <el-tag size="small" :type="module.sync_info.sync_status === 'ready' ? 'success' : 'warning'">
        {{ module.sync_info.sync_status === 'ready' ? '同步就绪' : '待补映射' }}
      </el-tag>
    </div>

    <div v-if="active" class="module-card__body">
      <el-empty v-if="!module.scenes?.length" description="当前模块暂无场景">
        <el-button type="primary" size="small" @click="emit('create-scene', module)">新增场景</el-button>
      </el-empty>
      <slot v-else />
    </div>
  </el-card>
</template>

<script setup>
import {
  ArrowDownBold,
  ArrowRightBold,
  Check,
  Close,
  Connection,
  Delete,
  EditPen,
  Plus
} from '@element-plus/icons-vue'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  module: {
    type: Object,
    default: () => ({})
  },
  active: {
    type: Boolean,
    default: false
  },
  summary: {
    type: Object,
    default: () => ({ sceneCount: 0, formulaCount: 0 })
  }
})

const emit = defineEmits(['select', 'rename', 'create-scene', 'delete-module', 'sync-module'])

const editing = ref(false)
const draftName = ref('')

const moduleTitle = computed(() => String(props.module?.moduleName || '未命名模块'))
const moduleSummaryText = computed(() => `${moduleTitle.value} · ${props.summary.sceneCount} 个场景 · ${props.summary.formulaCount} 条公式`)

watch(
  () => props.module?.moduleName,
  (value) => {
    draftName.value = String(value || '')
  },
  { immediate: true }
)

const handleRename = () => {
  const nextName = String(draftName.value || '').trim()
  if (!nextName) {
    return
  }
  emit('rename', props.module, nextName)
  editing.value = false
}

const handleCancelEdit = () => {
  draftName.value = String(props.module?.moduleName || '')
  editing.value = false
}
</script>

<style scoped>
.module-card {
  border-radius: 18px;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.module-card.is-active {
  border-color: #bfdbfe;
  box-shadow: 0 16px 32px rgba(59, 130, 246, 0.08);
}

.module-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
}

.module-card__title-wrap {
  min-width: 0;
  flex: 1;
}

.module-card__title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.module-card__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: flex-end;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s ease;
}

.module-card__header:hover .module-card__actions,
.module-card.is-active .module-card__actions {
  opacity: 1;
  pointer-events: auto;
}

.module-card__toggle {
  color: #94a3b8;
  margin-left: 2px;
}

.module-card__body {
  display: grid;
  gap: 12px;
  padding-top: 12px;
}

.module-card__sync-info {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.mr-2 {
  margin-right: 8px;
}
</style>
