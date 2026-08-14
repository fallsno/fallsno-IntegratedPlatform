<template>
  <section class="scene-focus-group">
    <div class="scene-focus-group__tabs">
      <el-tooltip
        v-for="scene in scenes"
        :key="scene.sceneCode"
        :content="buildSceneSummary(scene)"
        placement="top"
      >
        <button
          type="button"
          class="scene-focus-group__tab"
          :class="{ 'is-active': scene.sceneCode === activeSceneCode }"
          @click="emit('select-scene', scene)"
        >
          <span class="scene-focus-group__tab-title">{{ scene.sceneName }}</span>
          <el-icon 
            class="scene-focus-group__tab-delete" 
            @click.stop="emit('delete-scene', scene)"
          >
            <Close />
          </el-icon>
        </button>
      </el-tooltip>
    </div>

    <div v-if="currentScene" class="scene-focus-group__panel">
      <div class="scene-focus-group__header">
        <div>
          <el-tooltip
            v-if="currentScene.sceneCode !== editingSceneCode"
            :content="buildSceneSummary(currentScene)"
            placement="top"
          >
            <div
              class="scene-focus-group__title"
              @dblclick.stop="emit('start-rename-scene', currentScene)"
            >
              {{ currentScene.sceneName }}
            </div>
          </el-tooltip>
          <el-input
            v-else
            ref="sceneTitleInputRef"
            class="scene-focus-group__title-input"
            :model-value="sceneDraftName"
            size="small"
            :disabled="sceneSaving"
            placeholder="请输入场景名称"
            @input="sceneDraftName = $event"
            @keyup.enter="emit('confirm-rename-scene', currentScene, sceneDraftName)"
            @keyup.esc="emit('cancel-rename-scene', currentScene)"
            @blur="emit('cancel-rename-scene', currentScene)"
          />
        </div>
        <div class="scene-focus-group__actions">
          <el-tooltip content="新增公式" placement="top">
            <el-button circle text @click="emit('create-formula', currentScene)">
              <el-icon><Plus /></el-icon>
            </el-button>
          </el-tooltip>
          <el-button
            v-if="currentScene.rows.length && !batchMode"
            text
            size="small"
            @click="emit('enter-batch-delete', currentScene)"
          >
            批量删除
          </el-button>
          <div
            v-if="currentScene.sceneCode !== editingSceneCode"
            class="scene-focus-group__actions--danger"
          >
            <el-tooltip content="删除场景" placement="top">
              <el-button
                circle
                text
                type="danger"
                class="scene-focus-group__delete-button"
                @click="emit('delete-scene', currentScene)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </div>
      </div>

      <div v-if="batchMode" class="scene-focus-group__batch-bar">
        <span>已选 {{ selectedFormulaKeys.length }} 条</span>
        <div class="scene-focus-group__batch-actions">
          <el-button
            type="danger"
            size="small"
            :loading="batchDeleting"
            :disabled="!selectedFormulaKeys.length"
            @click="emit('confirm-batch-delete', currentScene)"
          >
            删除
          </el-button>
          <el-button size="small" @click="emit('cancel-batch-delete', currentScene)">取消</el-button>
        </div>
      </div>

      <el-empty v-if="!currentScene.rows.length" description="当前场景暂无公式">
        <el-button type="primary" size="small" @click="emit('create-formula', currentScene)">新增公式</el-button>
      </el-empty>

      <WorkbenchFormulaList
        v-else
        :rows="currentScene.rows"
        :active-formula-key="activeFormulaKey"
        :editing-formula-key="editingFormulaKey"
        :highlight-map="highlightMap"
        :result-map="resultMap"
        :moving="moving"
        :batch-mode="batchMode"
        :selected-row-keys="selectedFormulaKeys"
        @select="emit('select-formula', $event)"
        @delete="emit('delete-formula', $event)"
        @toggle-select="emit('toggle-formula-select', $event)"
        @reorder="emit('reorder', { moduleCode: currentScene.moduleCode, sceneCode: currentScene.sceneCode, orderedIds: $event.orderedIds })"
      >
        <template #inline-editor="{ row }">
          <slot name="inline-editor" :row="row" />
        </template>
      </WorkbenchFormulaList>
    </div>
  </section>
</template>

<script setup>
import { Delete, Plus } from '@element-plus/icons-vue'
import { computed, nextTick, ref, watch } from 'vue'

import WorkbenchFormulaList from './WorkbenchFormulaList.vue'

const props = defineProps({
  scenes: {
    type: Array,
    default: () => []
  },
  activeSceneCode: {
    type: String,
    default: ''
  },
  activeFormulaKey: {
    type: String,
    default: ''
  },
  editingFormulaKey: {
    type: String,
    default: ''
  },
  editingSceneCode: {
    type: String,
    default: ''
  },
  sceneSaving: {
    type: Boolean,
    default: false
  },
  highlightMap: {
    type: Object,
    default: () => ({})
  },
  resultMap: {
    type: Object,
    default: () => ({})
  },
  moving: {
    type: Boolean,
    default: false
  },
  batchMode: {
    type: Boolean,
    default: false
  },
  selectedFormulaKeys: {
    type: Array,
    default: () => []
  },
  batchDeleting: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'select-scene',
  'start-rename-scene',
  'confirm-rename-scene',
  'cancel-rename-scene',
  'delete-scene',
  'create-formula',
  'select-formula',
  'reorder',
  'enter-batch-delete',
  'cancel-batch-delete',
  'confirm-batch-delete',
  'toggle-formula-select',
  'delete-formula'
])

const currentScene = computed(() => {
  const scenes = Array.isArray(props.scenes) ? props.scenes : []
  return scenes.find((scene) => scene.sceneCode === props.activeSceneCode) || scenes[0] || null
})

const sceneTitleInputRef = ref(null)
const sceneDraftName = ref('')

watch(
  () => [props.editingSceneCode, currentScene.value?.sceneCode, currentScene.value?.sceneName],
  async () => {
    if (String(props.editingSceneCode || '') !== String(currentScene.value?.sceneCode || '')) {
      sceneDraftName.value = ''
      return
    }
    sceneDraftName.value = currentScene.value?.sceneName || ''
    await nextTick()
    sceneTitleInputRef.value?.focus?.()
    sceneTitleInputRef.value?.select?.()
  },
  { immediate: true }
)

const buildSceneSummary = (scene = {}) => `${scene.sceneName || '未命名场景'} · ${Array.isArray(scene.rows) ? scene.rows.length : 0} 条公式`
</script>

<style scoped>
.scene-focus-group {
  display: grid;
  gap: 14px;
}

.scene-focus-group__tabs {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.scene-focus-group__tab {
  min-width: 180px;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  background: #fff;
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  display: block;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.scene-focus-group__tab.is-active {
  border-color: #93c5fd;
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
  box-shadow: 0 12px 24px rgba(59, 130, 246, 0.08);
}

.scene-focus-group__tab-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.scene-focus-group__tab-delete {
  font-size: 12px;
  margin-left: 6px;
  opacity: 0;
  transition: opacity 0.18s ease, color 0.18s ease;
  color: #94a3b8;
}

.scene-focus-group__tab-delete:hover {
  color: #ef4444;
}

.scene-focus-group__tab:hover .scene-focus-group__tab-delete {
  opacity: 1;
}

.scene-focus-group__panel {
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 14px;
  background: #f8fafc;
}

.scene-focus-group__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.scene-focus-group__title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  cursor: text;
}

.scene-focus-group__title-input {
  width: 220px;
}

.scene-focus-group__actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.scene-focus-group__actions--danger {
  display: inline-flex;
  align-items: center;
}

.scene-focus-group__delete-button {
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s ease;
}

.scene-focus-group__header:hover .scene-focus-group__delete-button,
.scene-focus-group__tab:hover .scene-focus-group__delete-button {
  opacity: 1;
  pointer-events: auto;
}

.scene-focus-group__batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border: 1px solid #fecaca;
  border-radius: 14px;
  background: #fff7f7;
  color: #7f1d1d;
}

.scene-focus-group__batch-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

</style>
