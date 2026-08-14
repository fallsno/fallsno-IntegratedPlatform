<template>
  <el-dialog
    :model-value="modelValue"
    title="导入参数矩阵"
    width="960px"
    @close="emit('update:modelValue', false)"
  >
    <div class="import-dialog">
      <el-alert
        title="导入目标是参数矩阵。支持参数在行或参数在列，先预览确认，再提交入库。"
        type="info"
        :closable="false"
        show-icon
      />

      <div class="import-toolbar">
        <el-upload
          :auto-upload="false"
          :show-file-list="false"
          accept=".xlsx,.xls,.csv"
          action=""
          @change="handleFileChange"
        >
          <el-button type="primary">选择表格</el-button>
        </el-upload>
        <span class="file-name">{{ selectedFileName || '未选择文件' }}</span>
        <el-select v-model="selectedSheetName" class="sheet-select" :disabled="!availableSheets.length" placeholder="选择工作表">
          <el-option
            v-for="sheetName in availableSheets"
            :key="sheetName"
            :label="sheetName"
            :value="sheetName"
          />
        </el-select>
        <el-select v-model="orientationHint" class="orientation-select">
          <el-option
            v-for="item in orientationOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-button :loading="previewLoading" :disabled="!sourceRows.length" @click="requestPreview">
          重新预览
        </el-button>
      </div>

      <div v-if="preview.rows.length" class="preview-block">
        <div class="preview-header">
          <div>
            <div class="preview-title">导入预览</div>
            <div class="preview-subtitle">
              当前识别方向：{{ preview.orientation === 'parameters_in_columns' ? '参数在列' : '参数在行' }}
            </div>
          </div>
          <el-tag type="success">参数 {{ preview.rows.length }} 项</el-tag>
        </div>

        <el-alert
          v-for="warning in preview.warnings"
          :key="warning"
          :title="warning"
          type="warning"
          :closable="false"
          show-icon
          class="preview-warning"
        />

        <el-table :data="preview.rows" size="small" max-height="420" border>
          <el-table-column prop="categoryName" label="分类" min-width="140" />
          <el-table-column prop="paramName" label="参数名" min-width="180" fixed="left" />
          <el-table-column prop="unitCode" label="单位" width="100" />
          <el-table-column
            v-for="versionCode in preview.versionHeaders"
            :key="versionCode"
            :label="versionCode"
            min-width="120"
          >
            <template #default="{ row }">
              {{ row.values?.[versionCode] ?? '' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <template #footer>
      <el-button
        type="primary"
        :loading="submitting"
        :disabled="!preview.rows.length"
        @click="commitImport"
      >
        确认导入
      </el-button>
      <el-button @click="emit('update:modelValue', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'

import {
  buildOrientationOptions,
  commitParameterMatrixImport,
  previewParameterMatrixImport
} from '@/api/designPlatform.js'

const EMPTY_PREVIEW = () => ({
  orientation: 'parameters_in_rows',
  parameterHeaders: [],
  versionHeaders: [],
  rows: [],
  warnings: []
})

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['done', 'update:modelValue'])

const selectedFileName = ref('')
const availableSheets = ref([])
const sheetRowsMap = ref({})
const selectedSheetName = ref('')
const orientationHint = ref('auto')
const orientationOptions = buildOrientationOptions()
const preview = ref(EMPTY_PREVIEW())
const previewLoading = ref(false)
const submitting = ref(false)
const sourceRows = computed(() => sheetRowsMap.value[selectedSheetName.value] || [])

const resetState = () => {
  selectedFileName.value = ''
  availableSheets.value = []
  sheetRowsMap.value = {}
  selectedSheetName.value = ''
  orientationHint.value = 'auto'
  preview.value = EMPTY_PREVIEW()
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      resetState()
    }
  }
)

watch(orientationHint, async () => {
  if (!props.modelValue || !sourceRows.value.length) return
  await requestPreview()
})

watch(selectedSheetName, async () => {
  if (!props.modelValue || !sourceRows.value.length) return
  await requestPreview()
})

const parseWorkbookToSheets = async (rawFile) => {
  const buffer = await rawFile.arrayBuffer()
  const workbook = XLSX.read(buffer, { type: 'array' })
  const rowsBySheet = workbook.SheetNames.reduce((accumulator, sheetName) => {
    const worksheet = workbook.Sheets[sheetName]
    accumulator[sheetName] = XLSX.utils.sheet_to_json(worksheet, { header: 1, raw: false, defval: '' })
    return accumulator
  }, {})
  return {
    sheetNames: workbook.SheetNames || [],
    rowsBySheet
  }
}

const autoPickBestSheetPreview = async () => {
  const candidateSheets = availableSheets.value.filter((sheetName) => (sheetRowsMap.value[sheetName] || []).length)
  if (!candidateSheets.length) {
    preview.value = EMPTY_PREVIEW()
    return
  }

  previewLoading.value = true
  try {
    let bestMatch = null
    for (const sheetName of candidateSheets) {
      const currentPreview = await previewParameterMatrixImport({
        sheet_name: sheetName,
        rows: sheetRowsMap.value[sheetName],
        orientation_hint: orientationHint.value
      })
      const score = [
        Number(currentPreview.rows?.length || 0),
        Number(currentPreview.versionHeaders?.length || 0),
        -Number(currentPreview.warnings?.length || 0)
      ]
      const isBetter =
        !bestMatch ||
        score[0] > bestMatch.score[0] ||
        (score[0] === bestMatch.score[0] && score[1] > bestMatch.score[1]) ||
        (score[0] === bestMatch.score[0] && score[1] === bestMatch.score[1] && score[2] > bestMatch.score[2])
      if (isBetter) {
        bestMatch = { sheetName, preview: currentPreview, score }
      }
    }

    selectedSheetName.value = bestMatch?.sheetName || candidateSheets[0]
    preview.value = bestMatch?.preview || EMPTY_PREVIEW()
  } catch (error) {
    console.error(error)
    preview.value = EMPTY_PREVIEW()
    ElMessage.error(error?.response?.data?.detail || '生成导入预览失败')
  } finally {
    previewLoading.value = false
  }
}

const requestPreview = async () => {
  if (!sourceRows.value.length) {
    ElMessage.warning('请先选择待导入的表格')
    return
  }
  previewLoading.value = true
  try {
    preview.value = await previewParameterMatrixImport({
      sheet_name: selectedSheetName.value || selectedFileName.value || 'Sheet1',
      rows: sourceRows.value,
      orientation_hint: orientationHint.value
    })
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.detail || '生成导入预览失败')
  } finally {
    previewLoading.value = false
  }
}

const handleFileChange = async (file) => {
  const rawFile = file?.raw
  if (!rawFile) {
    ElMessage.warning('未读取到上传文件')
    return
  }
  try {
    selectedFileName.value = rawFile.name || ''
    const parsedWorkbook = await parseWorkbookToSheets(rawFile)
    availableSheets.value = parsedWorkbook.sheetNames
    sheetRowsMap.value = parsedWorkbook.rowsBySheet
    selectedSheetName.value = parsedWorkbook.sheetNames[0] || ''
    await autoPickBestSheetPreview()
  } catch (error) {
    console.error(error)
    preview.value = EMPTY_PREVIEW()
    availableSheets.value = []
    sheetRowsMap.value = {}
    selectedSheetName.value = ''
    ElMessage.error('解析表格失败')
  }
}

const commitImport = async () => {
  if (!preview.value.rows.length) {
    ElMessage.warning('请先完成导入预览')
    return
  }
  submitting.value = true
  try {
    const result = await commitParameterMatrixImport({
      orientation: preview.value.orientation,
      parameter_rows: preview.value.rows.map((row) => ({
        param_name: row.paramName,
        unit_code: row.unitCode,
        category_name: row.categoryName,
        values: row.values || {}
      }))
    })
    ElMessage.success(`导入完成：参数 ${result.imported_parameter_count} 项，型号值 ${result.saved_value_count} 个`)
    emit('done')
    emit('update:modelValue', false)
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.detail || '提交导入失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.import-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.import-toolbar,
.preview-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.import-toolbar {
  flex-wrap: wrap;
}

.file-name {
  min-width: 180px;
  color: #64748b;
}

.orientation-select {
  width: 160px;
}

.sheet-select {
  width: 200px;
}

.preview-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-header {
  justify-content: space-between;
}

.preview-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.preview-subtitle {
  margin-top: 4px;
  color: #64748b;
}

.preview-warning {
  margin-bottom: 0;
}
</style>
