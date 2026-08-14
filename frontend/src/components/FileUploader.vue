<template>
  <div>
    <el-upload
      class="upload-demo"
      drag
      :action="`/versions/${versionId}/upload`"
      :headers="{}"
      :on-success="handleSuccess"
      :before-upload="beforeUpload"
      multiple
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
      <template #tip>
        <div class="el-upload__tip">支持图片、Word、Excel、PDF，单个不超过50MB</div>
      </template>
    </el-upload>

    <el-table :data="attachments" style="margin-top: 15px" v-if="attachments.length">
      <el-table-column prop="file_name" label="文件名" />
      <el-table-column prop="file_category" label="类型" width="100" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button link type="primary" @click="downloadFile(row.id)">下载</el-button>
          <el-button link type="danger" @click="deleteFile(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps(['versionId', 'partId'])
const attachments = ref([])

const fetchAttachments = async () => {
  try {
    const res = await axios.get(`/versions/${props.versionId}/attachments`)
    attachments.value = res.data
  } catch (e) {
    ElMessage.error('获取附件失败')
  }
}

const beforeUpload = (file) => {
  const isValid = file.size / 1024 / 1024 < 50
  if (!isValid) ElMessage.error('文件不能超过50MB')
  return isValid
}

const handleSuccess = () => {
  ElMessage.success('上传成功')
  fetchAttachments()
}

const downloadFile = (id) => {
  window.open(`/versions/attachments/${id}/download`)
}

const deleteFile = (id) => {
  ElMessageBox.confirm('确定删除该附件吗？', '警告', { type: 'warning' })
    .then(async () => {
      await axios.delete(`/versions/attachments/${id}`)
      ElMessage.success('删除成功')
      fetchAttachments()
    })
}

onMounted(fetchAttachments)
</script>