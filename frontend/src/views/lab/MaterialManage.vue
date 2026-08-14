<template>
  <div class="material-manage">
    <div class="page-header">
      <div class="header-left">
        <h2>实验物料库</h2>
        <p class="subtitle">试验设备及配件的一站式管理中心</p>
      </div>
      <div class="header-ops">
        <el-upload
          action="/lab-api/materials/upload-excel"
          :show-file-list="false"
          :on-success="handleExcelSuccess"
          :on-error="handleUploadError"
          accept=".xlsx, .xls"
          class="import-upload"
        >
          <el-button type="success" plain :icon="Upload">Excel 导入</el-button>
        </el-upload>
        <el-button type="warning" plain :icon="CopyDocument" @click="showPasteDialog = true">
          粘贴导入
        </el-button>
        <el-button type="primary" :icon="Plus" @click="handleNewMaterial">
          新增物料
        </el-button>
      </div>
    </div>

    <!-- 数据统计栏 -->
    <div class="stats-bar">
      <div class="stat-item">
        <div class="stat-value">{{ stats.totalTypes }}</div>
        <div class="stat-label">物料类型</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.totalQuantity }}</div>
        <div class="stat-label">设备总数</div>
      </div>
      <div class="stat-item in-use">
        <div class="stat-value">{{ stats.inUseCount }}</div>
        <div class="stat-label">正在使用</div>
      </div>
      <div class="stat-item warning">
        <div class="stat-value">{{ stats.lowStockCount }}</div>
        <div class="stat-label">库存告急</div>
      </div>
    </div>

    <!-- 筛选过滤栏 -->
    <div class="filter-bar">
      <el-input
        v-model="filter.keyword"
        placeholder="搜索名称、型号、品牌或物料号..."
        class="search-input"
        clearable
        :prefix-icon="Search"
      />
      <el-select v-model="filter.category" placeholder="按类型筛选" clearable style="width: 160px">
        <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
      </el-select>
      <el-select v-model="filter.status" placeholder="使用状态" clearable style="width: 140px">
        <el-option label="在用" value="在用" />
        <el-option label="闲置" value="闲置" />
        <el-option label="备用" value="备用" />
        <el-option label="损坏" value="损坏" />
      </el-select>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table 
        :data="filteredMaterials" 
        border 
        stripe 
        style="width: 100%" 
        size="small"
        class="custom-table"
      >
        <el-table-column prop="category" label="类型" :width="getColWidth('category')" fixed="left" sortable />
        <el-table-column prop="name" label="名称" :width="getColWidth('name')" fixed="left">
          <template #default="{ row }">
            <div class="name-cell">
              <span>{{ row.name }}</span>
              <el-tag v-if="row.usage_status === '在用'" size="small" type="success" effect="plain" class="status-tag">在用</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="model" label="型号" :width="getColWidth('model')" />
        <el-table-column label="图片" width="80" align="center">
          <template #default="{ row }">
            <el-image 
              v-if="row.image_url" 
              :src="row.image_url" 
              :preview-src-list="[row.image_url]"
              fit="cover" 
              class="material-thumb"
              preview-teleported
            />
            <el-icon v-else class="no-img-icon"><Picture /></el-icon>
          </template>
        </el-table-column>
        <el-table-column prop="material_no" label="物料号" :width="getColWidth('material_no')" />
        <el-table-column prop="brand" label="品牌" :width="getColWidth('brand')" />
        <el-table-column prop="voltage" label="电压" :width="getColWidth('voltage')" />
        <el-table-column prop="range" label="量程" :width="getColWidth('range')" />
        <el-table-column prop="total_quantity" label="总数" width="70" align="center" />
        <el-table-column prop="used_quantity" label="已用" width="70" align="center" />
        <el-table-column prop="inventory" label="库存" width="70" align="center">
          <template #default="{ row }">
            <span :class="{'out-of-stock': row.inventory <= 0}">{{ row.inventory }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="usage_status" label="使用情况" :width="getColWidth('usage_status')">
          <template #default="{ row }">
            <span :class="getStatusClass(row.usage_status)">{{ row.usage_status }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="install_method" label="安装方式" :width="getColWidth('install_method')" show-overflow-tooltip />
        <el-table-column prop="sensor_size" label="尺寸" :width="getColWidth('sensor_size')" />
        <el-table-column prop="install_requirement" label="安装要求" :width="getColWidth('install_requirement')" show-overflow-tooltip />
        <el-table-column label="手册" width="80" align="center">
          <template #default="{ row }">
            <el-link v-if="row.manual_url" type="primary" :href="row.manual_url" target="_blank" :icon="Document">查看</el-link>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="editMaterial(row)">编辑</el-button>
            <el-button link type="danger" @click="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="showDialog" :title="dialogTitle" width="700px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="类型" prop="category">
              <el-select
                v-model="form.category"
                filterable
                allow-create
                default-first-option
                placeholder="选择或输入新类型"
                style="width: 100%"
              >
                <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="名称" prop="name">
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="型号" prop="model">
              <el-input v-model="form.model" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="物料号">
              <el-input v-model="form.material_no" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="品牌">
              <el-input v-model="form.brand" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="图片">
              <div class="uploader-wrapper">
                <el-upload
                  action="/lab-api/materials/upload-image"
                  :show-file-list="false"
                  :on-success="handleImageSuccess"
                  :on-error="handleUploadError"
                  accept="image/*"
                  class="material-uploader"
                >
                  <img v-if="form.image_url" :src="form.image_url" class="form-thumb" />
                  <el-icon v-else class="uploader-icon"><Plus /></el-icon>
                </el-upload>
                <el-button 
                  v-if="form.image_url" 
                  type="danger" 
                  link 
                  :icon="Delete" 
                  class="del-img-btn"
                  @click="form.image_url = ''"
                >删除图片</el-button>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="电压">
              <el-input v-model="form.voltage" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="量程">
              <el-input v-model="form.range" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="总数量">
              <el-input-number v-model="form.total_quantity" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="已使用">
              <el-input-number v-model="form.used_quantity" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="库存">
              <el-input-number v-model="form.inventory" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="使用情况">
          <el-select
            v-model="form.usage_status"
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入状态"
            style="width: 100%"
          >
            <el-option label="在用" value="在用" />
            <el-option label="闲置" value="闲置" />
            <el-option label="备用" value="备用" />
            <el-option label="损坏" value="损坏" />
            <el-option label="测试中" value="测试中" />
          </el-select>
        </el-form-item>
        <el-form-item label="安装方式">
          <el-input v-model="form.install_method" type="textarea" :rows="2" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="传感器尺寸">
              <el-input v-model="form.sensor_size" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="使用手册">
              <div class="manual-upload-wrapper">
                <el-upload
                  action="/lab-api/materials/upload-manual"
                  :show-file-list="false"
                  :on-success="handleManualSuccess"
                  :on-error="handleUploadError"
                >
                  <el-button size="small" type="primary" plain :icon="Upload">上传手册 (PDF/DOC)</el-button>
                </el-upload>
                <div v-if="form.manual_url" class="manual-ops">
                  <el-link type="primary" :href="form.manual_url" target="_blank" class="manual-link">{{ form.manual_name || '查看手册' }}</el-link>
                  <el-button type="danger" link :icon="Delete" @click="clearManual">删除</el-button>
                </div>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="安装要求">
          <el-input v-model="form.install_requirement" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMaterial">保存</el-button>
      </template>
    </el-dialog>

    <!-- 粘贴导入弹窗 -->
    <el-dialog v-model="showPasteDialog" title="粘贴 Excel/表格内容导入" width="800px">
      <div class="paste-container">
        <p class="hint">请直接从 Excel 中复制行内容，并粘贴到下方文本框中：</p>
        <el-input
          v-model="pasteText"
          type="textarea"
          :rows="15"
          placeholder="类型	名称	型号	图片	物料号	品牌	电压	量程	总数量	已使用数量	库存	使用情况	安装方式	传感器尺寸	安装要求"
          class="paste-input"
        />
        <div class="parse-preview" v-if="parsedData.length">
          <p>解析预览 ({{ parsedData.length }} 条):</p>
          <el-table :data="parsedData.slice(0, 5)" size="small" border>
            <el-table-column prop="category" label="类型" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="model" label="型号" />
          </el-table>
          <p v-if="parsedData.length > 5" class="more-hint">...等共 {{ parsedData.length }} 条数据</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="showPasteDialog = false">取消</el-button>
        <el-button type="primary" @click="handlePasteImport" :disabled="!parsedData.length">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from '@/api/lab'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, CopyDocument, Search, Picture } from '@element-plus/icons-vue'

const materials = ref([])
const showDialog = ref(false)
const dialogTitle = ref('新增物料')
const formRef = ref(null)

// 筛选与统计相关
const filter = ref({
  keyword: '',
  category: '',
  status: ''
})

const categories = computed(() => {
  const cats = new Set(materials.value.map(m => m.category))
  return Array.from(cats).filter(Boolean)
})

const filteredMaterials = computed(() => {
  return materials.value.filter(m => {
    const matchKwd = !filter.value.keyword || 
      [m.name, m.model, m.brand, m.material_no].some(v => v?.toLowerCase().includes(filter.value.keyword.toLowerCase()))
    const matchCat = !filter.value.category || m.category === filter.value.category
    const matchStatus = !filter.value.status || m.usage_status === filter.value.status
    return matchKwd && matchCat && matchStatus
  })
})

const stats = computed(() => {
  return {
    totalTypes: categories.value.length,
    totalQuantity: materials.value.reduce((sum, m) => sum + (m.total_quantity || 0), 0),
    inUseCount: materials.value.filter(m => m.usage_status === '在用').length,
    lowStockCount: materials.value.filter(m => (m.inventory || 0) <= 0).length
  }
})

const getStatusClass = (status) => {
  if (status === '在用') return 'status-in-use'
  if (status === '损坏') return 'status-damaged'
  if (status === '测试中') return 'status-testing'
  return ''
}

// 粘贴导入相关
const showPasteDialog = ref(false)
const pasteText = ref('')
const parsedData = ref([])

watch(pasteText, (val) => {
  if (!val.trim()) {
    parsedData.value = []
    return
  }
  
  const lines = val.trim().split('\n')
  const results = []
  
  lines.forEach(line => {
    const cols = line.split('\t')
    if (cols.length >= 2) { // 至少要有类型和名称
      results.push({
        category: cols[0]?.trim() || '',
        name: cols[1]?.trim() || '',
        model: cols[2]?.trim() || '',
        // cols[3] 是图片占位，跳过
        material_no: cols[4]?.trim() || '',
        brand: cols[5]?.trim() || '',
        voltage: cols[6]?.trim() || '',
        range: cols[7]?.trim() || '',
        total_quantity: parseInt(cols[8]) || 0,
        used_quantity: parseInt(cols[9]) || 0,
        inventory: parseInt(cols[10]) || 0,
        usage_status: cols[11]?.trim() || '',
        install_method: cols[12]?.trim() || '',
        sensor_size: cols[13]?.trim() || '',
        install_requirement: cols[14]?.trim() || ''
      })
    }
  })
  parsedData.value = results
})

const handlePasteImport = async () => {
  try {
    for (const item of parsedData.value) {
      await axios.post('/materials', item)
    }
    ElMessage.success(`成功导入 ${parsedData.value.length} 条数据`)
    showPasteDialog.value = false
    pasteText.value = ''
    fetchMaterials()
  } catch (err) {
    ElMessage.error('导入部分数据失败')
  }
}

const handleExcelSuccess = (res) => {
  ElMessage.success('Excel 导入成功')
  fetchMaterials()
}

const handleUploadError = (err) => {
  console.error('Upload Error:', err)
  ElMessage.error('上传失败，请检查网络或文件格式')
}

const handleImageSuccess = (res) => {
  form.value.image_url = res.url
  ElMessage.success('图片上传成功')
}

const handleManualSuccess = (res) => {
  form.value.manual_url = res.url
  form.value.manual_name = res.name
  ElMessage.success('使用手册上传成功')
}

const clearManual = () => {
  form.value.manual_url = ''
  form.value.manual_name = ''
}

const getColWidth = (prop) => {
  let maxChars = 10 // 基础长度
  materials.value.forEach(row => {
    const val = String(row[prop] || '')
    const lines = val.split('\n')
    lines.forEach(line => {
      let lineLen = 0
      for (let i = 0; i < line.length; i++) {
        lineLen += line.charCodeAt(i) > 127 ? 2 : 1
      }
      if (lineLen > maxChars) maxChars = lineLen
    })
  })
  return Math.min(400, Math.max(100, maxChars * 8 + 30))
}

const form = ref({
  category: '',
  name: '',
  model: '',
  image_url: '',
  material_no: '',
  brand: '',
  voltage: '',
  range: '',
  total_quantity: 0,
  used_quantity: 0,
  inventory: 0,
  usage_status: '',
  install_method: '',
  sensor_size: '',
  install_requirement: ''
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  category: [{ required: true, message: '请输入类型', trigger: 'blur' }]
}

const fetchMaterials = async () => {
  try {
    const res = await axios.get('/materials')
    materials.value = res.data
  } catch (err) {
    ElMessage.error('获取物料列表失败')
  }
}

const handleNewMaterial = () => {
  dialogTitle.value = '新增物料'
  form.value = {
    category: '', name: '', model: '', image_url: '', material_no: '',
    brand: '', voltage: '', range: '', total_quantity: 0, used_quantity: 0,
    inventory: 0, usage_status: '', install_method: '', sensor_size: '',
    install_requirement: '', manual_url: '', manual_name: ''
  }
  showDialog.value = true
}

const editMaterial = (row) => {
  dialogTitle.value = '编辑物料'
  form.value = { ...row }
  showDialog.value = true
}

const saveMaterial = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (form.value.id) {
          await axios.put(`/materials/${form.value.id}`, form.value)
          ElMessage.success('更新成功')
        } else {
          await axios.post('/materials', form.value)
          ElMessage.success('保存成功')
        }
        showDialog.value = false
        fetchMaterials()
      } catch (err) {
        ElMessage.error('保存失败')
      }
    }
  })
}

const confirmDelete = (row) => {
  ElMessageBox.confirm(`确定删除物料 "${row.name}" 吗？`, '警告', {
    type: 'warning'
  }).then(async () => {
    try {
      await axios.delete(`/materials/${row.id}`)
      ElMessage.success('已删除')
      fetchMaterials()
    } catch (err) {
      ElMessage.error('删除失败')
    }
  })
}

const importExampleData = async () => {
  const exampleData = [
    { 
      category: '传感器采集设备', name: '接近开关', model: 'E2E-X10MC118 2M OMS', 
      material_no: '1100061679', brand: 'Omron', voltage: '10-24V', range: '0-10mm', 
      total_quantity: 2, used_quantity: 2, inventory: 0, usage_status: '在用', 
      sensor_size: 'M18', install_method: '支架固定' 
    },
    { 
      category: '传感器采集设备', name: '压力传感器2-300Kg', model: 'PBMH-03', 
      material_no: '淘宝', brand: '蚌埠中诺称重测力传感器', voltage: '8V', range: '300Kg', 
      total_quantity: 2, used_quantity: 2, inventory: 0, usage_status: '在用',
      install_requirement: '需校准'
    },
    { 
      category: '固定配件', name: '方螺母', model: 'M16×40×40-15 居中', 
      material_no: '1100077372', total_quantity: 6, used_quantity: 2, inventory: 4, 
      usage_status: '在用' 
    },
    { 
      category: '电源', name: '电源1', model: 'DRA-60-12', 
      material_no: '1100040611', brand: 'MEAN WELL', voltage: '100-240V', range: '12V', 
      total_quantity: 1, used_quantity: 1, inventory: 0, usage_status: '在用' 
    },
    {
      category: '其他配件', name: '采集卡', model: 'USB315x',
      material_no: '淘宝', brand: '阿尔泰', voltage: '0-10v', range: 'USB（输出）',
      total_quantity: 1, used_quantity: 1, inventory: 0, usage_status: '在用'
    }
  ]
  
  try {
    for (const item of exampleData) {
      await axios.post('/materials', item)
    }
    ElMessage.success('示例数据导入完成')
    fetchMaterials()
  } catch (err) {
    ElMessage.error('导入失败')
  }
}

onMounted(fetchMaterials)
</script>

<style scoped>
.material-manage {
  padding: 24px;
  background: #fcfcfd;
  min-height: 100vh;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
}
.header-left h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
}
.subtitle {
  margin: 8px 0 0;
  color: #666;
  font-size: 14px;
}
.header-ops {
  display: flex;
  gap: 12px;
}

/* 统计栏样式 */
.stats-bar {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}
.stat-item {
  flex: 1;
  background: #fff;
  border: 1px solid #eee;
  padding: 16px 20px;
  border-radius: 10px;
  transition: all 0.2s;
}
.stat-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  line-height: 1;
}
.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-top: 8px;
}
.stat-item.in-use .stat-value { color: #10b981; }
.stat-item.warning .stat-value { color: #ef4444; }

/* 筛选栏样式 */
.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  align-items: center;
}
.search-input {
  width: 320px;
}

.table-card {
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  overflow: hidden;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-tag {
  height: 20px;
  line-height: 18px;
  padding: 0 6px;
  font-size: 11px;
}

.material-thumb {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}
.no-img-icon {
  font-size: 24px;
  color: #e5e7eb;
}

.status-in-use { color: #10b981; font-weight: 500; }
.status-damaged { color: #ef4444; font-weight: 500; }
.status-testing { color: #f59e0b; font-weight: 500; }
.out-of-stock { color: #f56c6c; font-weight: bold; }

.custom-table :deep(.el-table__cell) {
  padding: 8px 0;
}
.custom-table :deep(.cell) {
  white-space: pre-wrap;
  line-height: 1.6;
  color: #374151;
}

.uploader-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.material-uploader {
  border: 1px dashed #d1d5db;
  border-radius: 8px;
  cursor: pointer;
  width: 80px;
  height: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: border-color 0.2s;
  overflow: hidden;
}
.material-uploader:hover {
  border-color: #3b82f6;
}
.uploader-icon {
  font-size: 20px;
  color: #9ca3af;
}
.form-thumb {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  object-fit: cover;
}

.manual-upload-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.manual-ops {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fafc;
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}
.manual-link {
  font-size: 13px;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.paste-container {
  font-size: 12px;
  color: #67c23a;
  margin-top: 5px;
  line-height: 1.2;
}
.no-data {
  color: #94a3b8;
}

.paste-container {
  padding: 0 10px;
}
.paste-input :deep(.el-textarea__inner) {
  background: #f9fafb;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.6;
}
.parse-preview {
  margin-top: 20px;
}
.parse-preview p {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
}

.hint {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 12px;
}
.more-hint {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 8px;
  text-align: center;
}
</style>
