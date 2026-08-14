<template>
  <el-drawer
    :model-value="modelValue"
    title="公式说明"
    size="360px"
    @close="emit('update:modelValue', false)"
  >
    <template #header>
      <div class="drawer-header">
        <span class="drawer-header-title">公式说明</span>
        <div v-if="editable" class="drawer-header-actions">
          <el-button v-if="!isEditing" type="primary" link @click="startEditing">
            编辑
          </el-button>
          <template v-else>
            <el-button type="primary" link @click="saveEditing">保存</el-button>
            <el-button type="info" link @click="cancelEditing">取消</el-button>
          </template>
        </div>
      </div>
    </template>
    
    <div class="workbench-explanation-drawer">
      <section class="drawer-section">
        <div class="drawer-section__title">{{ title || '未选择对象' }}</div>
        
        <div v-if="isEditing" class="drawer-section__edit-field">
          <el-input
            v-model="editForm.summary"
            type="textarea"
            :rows="4"
            placeholder="请输入说明文字..."
          />
        </div>
        <div v-else class="drawer-section__summary">{{ summary || '当前暂无补充说明。' }}</div>
      </section>

      <section class="drawer-section" v-if="details.length && !isEditing">
        <div class="drawer-section__label">关键说明</div>
        <div class="drawer-detail-list">
          <div
            v-for="(detail, index) in details"
            :key="`${title || 'detail'}-${index}`"
            class="drawer-detail"
          >
            {{ detail }}
          </div>
        </div>
      </section>

      <section class="drawer-section" v-if="resources.length || isEditing || editable">
        <div class="drawer-section__label" style="display: flex; justify-content: space-between; align-items: center;">
          <span>说明资源</span>
          <div v-if="editable && !isEditing" style="display: flex; gap: 8px;">
            <el-upload
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              accept="image/*"
              @change="(file) => handleFileUploadDirectly(file, 'image')"
            >
              <el-button link type="primary" size="small"><el-icon><Picture /></el-icon>添加图片</el-button>
            </el-upload>
            <el-upload
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              accept=".pdf,.doc,.docx,.txt"
              @change="(file) => handleFileUploadDirectly(file, 'document')"
            >
              <el-button link type="primary" size="small"><el-icon><DocumentAdd /></el-icon>添加文档</el-button>
            </el-upload>
          </div>
        </div>
        
        <div v-if="isEditing" class="drawer-resource-list">
          <div
            v-for="(resource, index) in editForm.resources"
            :key="index"
            class="drawer-resource edit-mode"
          >
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
              <el-tag size="small" :type="resource.type === 'image' ? 'success' : resource.type === 'video' ? 'warning' : 'info'">
                {{ resource.type === 'image' ? '图片' : resource.type === 'video' ? '视频' : '文档' }}
              </el-tag>
              <span style="flex: 1; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ resource.title || '已上传资源' }}</span>
              <el-button type="danger" link @click="removeResource(index)" size="small">删除</el-button>
            </div>
          </div>
          <div style="display: flex; gap: 8px; margin-top: 8px;">
            <el-upload
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              accept="image/*"
              @change="(file) => handleFileUpload(file, 'image')"
            >
              <el-button type="primary" plain size="small">上传图片</el-button>
            </el-upload>
            <el-upload
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              accept="video/*"
              @change="(file) => handleFileUpload(file, 'video')"
            >
              <el-button type="primary" plain size="small">上传视频</el-button>
            </el-upload>
            <el-upload
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              accept=".pdf,.doc,.docx,.txt"
              @change="(file) => handleFileUpload(file, 'document')"
            >
              <el-button type="primary" plain size="small">上传文档</el-button>
            </el-upload>
          </div>
        </div>
        
        <div v-else class="drawer-resource-list">
          <div
            v-for="resource in resources"
            :key="`${resource.type}-${resource.title}`"
            class="drawer-resource"
          >
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-tag size="small" :type="resource.type === 'image' ? 'success' : resource.type === 'video' ? 'warning' : 'info'">
                  {{ resource.typeLabel || resource.type === 'image' ? '图片' : resource.type === 'video' ? '视频' : '文档' }}
                </el-tag>
                <span class="drawer-resource__title" style="margin: 0;">{{ resource.title }}</span>
              </div>
              <el-button type="primary" link size="small" @click="previewResource(resource)">预览</el-button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { Picture, DocumentAdd } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  summary: {
    type: String,
    default: ''
  },
  details: {
    type: Array,
    default: () => []
  },
  resources: {
    type: Array,
    default: () => []
  },
  editable: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'update:explanation'])

const isEditing = ref(false)
const editForm = ref({
  summary: '',
  resources: []
})

watch(() => props.modelValue, (val) => {
  if (!val) {
    isEditing.value = false
  }
})

const startEditing = () => {
  editForm.value = {
    summary: props.summary === '当前暂无补充说明。' ? '' : props.summary,
    resources: props.resources.map(r => ({ ...r }))
  }
  isEditing.value = true
}

const cancelEditing = () => {
  isEditing.value = false
}

const saveEditing = () => {
  emit('update:explanation', {
    summary: editForm.value.summary,
    resources: editForm.value.resources
  })
  isEditing.value = false
}

const handleFileUpload = (file, type) => {
  // Mock upload implementation
  editForm.value.resources.push({
    type,
    typeLabel: type === 'image' ? '图片' : type === 'video' ? '视频' : '文档',
    title: file.name,
    content: URL.createObjectURL(file.raw)
  })
  ElMessage.success('添加成功')
}

const handleFileUploadDirectly = (file, type) => {
  const newResource = {
    type,
    typeLabel: type === 'image' ? '图片' : type === 'video' ? '视频' : '文档',
    title: file.name,
    content: URL.createObjectURL(file.raw)
  }
  emit('update:explanation', {
    summary: props.summary,
    resources: [...props.resources, newResource]
  })
  ElMessage.success('添加成功')
}

const previewResource = (resource) => {
  if (resource.type === 'lookup') {
    ElMessage.info('暂不支持预览该查表附录：' + resource.content)
    return
  }
  if (!resource.content) {
    ElMessage.warning('资源内容为空')
    return
  }
  // Open blob URL or text in a new window/tab
  if (resource.content.startsWith('blob:') || resource.content.startsWith('http')) {
    window.open(resource.content, '_blank')
  } else {
    ElMessage.info('预览内容：' + resource.content)
  }
}

const removeResource = (idx) => {
  editForm.value.resources.splice(idx, 1)
}
</script>

<style scoped>
.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.drawer-header-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.drawer-header-actions {
  display: flex;
  gap: 8px;
}

.workbench-explanation-drawer {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.drawer-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.drawer-section__title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.drawer-section__summary {
  font-size: 13px;
  line-height: 1.7;
  color: #475569;
}

.drawer-section__label {
  font-size: 12px;
  font-weight: 700;
  color: #334155;
}

.drawer-detail-list,
.drawer-resource-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.drawer-detail,
.drawer-resource {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px 12px;
  background: #f8fafc;
}

.drawer-resource.edit-mode {
  display: flex;
  flex-direction: column;
}

.drawer-detail {
  font-size: 13px;
  line-height: 1.6;
  color: #334155;
}

.drawer-resource__type {
  font-size: 11px;
  color: #64748b;
}

.drawer-resource__title {
  margin-top: 2px;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}

.drawer-resource__content {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.6;
  color: #475569;
}
</style>
