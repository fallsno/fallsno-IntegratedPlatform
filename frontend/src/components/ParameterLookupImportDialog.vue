<template>
  <el-dialog
    :model-value="modelValue"
    title="导入查表附录"
    width="960px"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="lookup-import-dialog">
      <el-radio-group v-model="importMode">
        <el-radio-button label="paste">粘贴两列</el-radio-button>
        <el-radio-button label="excel">上传 Excel</el-radio-button>
      </el-radio-group>

      <el-alert
        v-if="importMode === 'paste'"
        title="请直接从 Excel 复制两列表格后粘贴，系统会按“查找值 + 结果值”解析。"
        type="info"
        :closable="false"
        show-icon
      />

      <template v-if="importMode === 'paste'">
        <el-input
          v-model="rawText"
          type="textarea"
          :rows="10"
          placeholder="示例：&#10;50\t1&#10;55\t0.919"
        />
      </template>

      <template v-else>
        <el-alert
          title="支持直接选择 .xlsx 工作簿。若识别到 RT300，将自动优先抽取“电机扭矩参数”工作表。"
          type="info"
          :closable="false"
          show-icon
        />
        <div class="lookup-import-dialog__toolbar">
          <el-upload
            :auto-upload="false"
            :show-file-list="false"
            accept=".xlsx,.xls,.csv"
            action=""
            @change="handleFileChange"
          >
            <el-button type="primary">选择表格</el-button>
          </el-upload>
          <span class="lookup-import-dialog__file-name">{{ selectedFileName || '未选择文件' }}</span>
          <el-select
            v-model="selectedSheetName"
            class="lookup-import-dialog__sheet-select"
            :disabled="!availableSheets.length"
            placeholder="选择查表工作表"
          >
            <el-option
              v-for="sheetName in availableSheets"
              :key="sheetName"
              :label="sheetName"
              :value="sheetName"
            />
          </el-select>
        </div>

        <el-alert
          v-if="workbookType === 'rt300'"
          :title="`已识别 RT300 工作簿：查表页 ${selectedSheetName || '未识别'}`"
          type="success"
          :closable="false"
          show-icon
        />
      </template>

      <div class="lookup-import-dialog__actions">
        <el-button :loading="previewLoading" @click="handlePreview">预览</el-button>
        <el-button
          type="primary"
          :loading="applyLoading"
          :disabled="!canApply"
          @click="applyPreview"
        >
          应用到表格
        </el-button>
      </div>

      <el-alert
        v-if="errors.length"
        :title="`发现 ${errors.length} 个校验问题`"
        type="error"
        :closable="false"
        show-icon
      />

      <el-table v-if="previewRows.length" :data="previewRows" border stripe max-height="220">
        <el-table-column prop="lookup_key" label="查找值" min-width="160" />
        <el-table-column prop="result_value" label="结果值" min-width="160" />
      </el-table>

      <el-table
        v-if="tableColumns.length && tablePreviewRows.length"
        :data="tablePreviewRows"
        border
        stripe
        size="small"
        max-height="260"
      >
        <el-table-column
          v-for="column in tableColumns"
          :key="column"
          :prop="column"
          :label="column"
          min-width="160"
        />
      </el-table>

      <el-table v-if="errors.length" :data="errors" border stripe max-height="220">
        <el-table-column prop="row_no" label="行号" width="100" />
        <el-table-column prop="message" label="错误信息" min-width="220" />
      </el-table>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'

import { detectRt300WorkbookSheets } from '@/api/parameterLookupWorkbook.helpers.mjs'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  previewer: {
    type: Function,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'apply'])

const importMode = ref('paste')
const rawText = ref('')
const previewRows = ref([])
const errors = ref([])
const tableColumns = ref([])
const tablePreviewRows = ref([])
const previewLoading = ref(false)
const applyLoading = ref(false)
const selectedFileName = ref('')
const availableSheets = ref([])
const selectedSheetName = ref('')
const sheetRowsMap = ref({})
const workbookType = ref('generic')

const canApply = computed(() => {
  if (errors.value.length) return false
  return previewRows.value.length > 0
})

const resetState = () => {
  importMode.value = 'paste'
  rawText.value = ''
  previewRows.value = []
  errors.value = []
  tableColumns.value = []
  tablePreviewRows.value = []
  previewLoading.value = false
  applyLoading.value = false
  selectedFileName.value = ''
  availableSheets.value = []
  selectedSheetName.value = ''
  sheetRowsMap.value = {}
  workbookType.value = 'generic'
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      resetState()
    }
  }
)

watch(selectedSheetName, async () => {
  if (importMode.value !== 'excel' || !selectedSheetName.value) return
  await requestLookupPreview()
})

const parseRows = () =>
  String(rawText.value || '')
    .split(/\r?\n/)
    .filter((line) => String(line || '').trim())
    .map((line) => String(line).split('\t'))

const parseWorkbookToSheets = async (rawFile) => {
  const buffer = await rawFile.arrayBuffer()
  const workbook = XLSX.read(buffer, { type: 'array' })
  const rowsBySheet = workbook.SheetNames.reduce((accumulator, sheetName) => {
    accumulator[sheetName] = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], {
      header: 1,
      raw: false,
      defval: ''
    })
    return accumulator
  }, {})
  return {
    sheetNames: workbook.SheetNames || [],
    rowsBySheet
  }
}

const requestLookupPreview = async () => {
  const rows =
    importMode.value === 'paste'
      ? parseRows()
      : sheetRowsMap.value[selectedSheetName.value] || []
  if (!rows.length) {
    previewRows.value = []
    errors.value = []
    return
  }
  const payload = await props.previewer({
    sheet_name: importMode.value === 'paste' ? 'pasted' : selectedSheetName.value || 'Sheet1',
    rows
  })
  previewRows.value = Array.isArray(payload?.rows) ? payload.rows : []
  errors.value = Array.isArray(payload?.errors) ? payload.errors : []
  tableColumns.value = Array.isArray(payload?.table_columns) ? payload.table_columns : []
  tablePreviewRows.value = Array.isArray(payload?.table_rows) ? payload.table_rows : []
}

const handlePreview = async () => {
  previewLoading.value = true
  try {
    await requestLookupPreview()
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
    const detected = detectRt300WorkbookSheets(parsedWorkbook.sheetNames)
    workbookType.value = detected.workbookType
    selectedSheetName.value = detected.lookupSheetName || parsedWorkbook.sheetNames[0] || ''
    await handlePreview()
  } catch (error) {
    console.error(error)
    resetState()
    importMode.value = 'excel'
    ElMessage.error('解析表格失败')
  }
}

const applyPreview = async () => {
  applyLoading.value = true
  try {
    emit('apply', {
      rows: previewRows.value,
      table_columns: tableColumns.value,
      table_rows: tablePreviewRows.value
    })
    emit('update:modelValue', false)
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.detail || '应用导入失败')
  } finally {
    applyLoading.value = false
  }
}
</script>

<style scoped>
.lookup-import-dialog {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.lookup-import-dialog__toolbar,
.lookup-import-dialog__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.lookup-import-dialog__actions {
  justify-content: flex-end;
}

.lookup-import-dialog__file-name {
  min-width: 180px;
  color: #64748b;
}

.lookup-import-dialog__sheet-select {
  width: 220px;
}
</style>
