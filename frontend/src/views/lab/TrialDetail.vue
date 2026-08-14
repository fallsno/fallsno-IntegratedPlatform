<template>
  <div class="trial-wizard" v-if="trialData">
    <!-- 顶部常驻信息栏 -->
    <div class="wizard-header">
      <div class="header-main">
        <el-page-header @back="$router.push('/lab')">
          <template #content>
            <div class="header-info">
              <span class="trial-no">{{ trialData.trial_no || 'NO-DATA' }}</span>
              <el-divider direction="vertical" />
              <span class="trial-name">{{ trialData.name }}</span>
              <el-tag size="small" :type="statusTagType">{{ trialData.status }}</el-tag>
            </div>
          </template>
        </el-page-header>
      </div>
      <div class="header-progress">
        <div class="progress-label">整体完成度</div>
        <el-progress :percentage="overallCompletion" :stroke-width="8" style="width: 200px" />
      </div>
      <div class="header-ops">
        <el-button-group>
          <el-button type="primary" plain @click="exportReport">导出报告</el-button>
          <el-button type="warning" plain @click="showAddAnomaly = true">异常登记</el-button>
        </el-button-group>
      </div>
    </div>

    <div class="wizard-body">
      <!-- 左侧垂直步骤条 -->
      <div class="wizard-aside">
        <el-steps :active="currentStepIndex" direction="vertical" finish-status="success">
          <el-step v-for="(step, index) in stepsConfig" :key="index" :title="step.title">
            <template #description>
              <div class="step-desc" @click="jumpToStep(index)" :class="{ 'active': currentStepIndex === index }">
                {{ step.desc }}
              </div>
            </template>
          </el-step>
        </el-steps>
      </div>

      <!-- 右侧分步内容卡片 -->
      <div class="wizard-content">
        <el-scrollbar ref="contentScroll">
          <div class="step-card-wrapper">
            <transition name="fade-slide" mode="out-in">
              <div :key="currentStepIndex" class="step-container-outer">
                <!-- ① 试验目的与产品 -->
                <div v-if="currentStepIndex === 0" class="step-container">
                  <el-card shadow="never" class="wizard-card">
                    <template #header>
                      <div class="card-header">
                        <span>① 试验目的与关联产品</span>
                        <div class="related-task" v-if="trialData.related_task_no">
                          关联任务: <el-tag size="small" type="info">{{ trialData.related_task_no }}</el-tag>
                        </div>
                      </div>
                    </template>

                    <div class="product-info-section mb-20">
                      <div class="section-title">关联产品</div>
                      <el-form label-width="100px">
                        <el-row :gutter="20">
                          <el-col :span="12">
                            <el-form-item label="选择产品">
                              <el-select
                                v-model="trialData.product_type_id"
                                filterable
                                placeholder="选择或搜索产品"
                                @change="handleProductChange"
                                style="width: 100%"
                              >
                                <el-option
                                  v-for="pt in productTypes"
                                  :key="pt.id"
                                  :label="`${pt.type_name || '未知产品'} (${pt.model_code || '无代号'})`"
                                  :value="pt.id"
                                />
                              </el-select>
                            </el-form-item>
                          </el-col>
                          <el-col :span="12">
                            <el-form-item label="产品代号">
                              <el-input v-model="trialData.product_model_code" readonly placeholder="选择产品后自动带入" />
                            </el-form-item>
                          </el-col>
                        </el-row>
                      </el-form>
                    </div>

                    <el-divider />

                    <div class="purpose-section">
                      <div class="section-title">试验目的</div>
                      <div class="template-btns">
                        <span class="label">使用模板:</span>
                        <el-button size="small" link type="primary" @click="applyPurposeTemplate(1)">模板一: 规律验证</el-button>
                        <el-button size="small" link type="primary" @click="applyPurposeTemplate(2)">模板二: 可行性确认</el-button>
                        <el-divider direction="vertical" />
                        <el-tooltip content="字体大小" placement="top">
                          <el-select v-model="trialData.purpose_font_size" size="small" style="width: 70px; margin-right: 5px;" @change="autoSaveTrial">
                            <el-option label="12px" value="12px" />
                            <el-option label="14px" value="14px" />
                            <el-option label="16px" value="16px" />
                          </el-select>
                        </el-tooltip>
                        <el-button 
                          size="small" 
                          :type="trialData.purpose_is_indent ? 'primary' : 'default'" 
                          plain 
                          @click="trialData.purpose_is_indent = !trialData.purpose_is_indent; autoSaveTrial()"
                        >
                          首行缩进
                        </el-button>
                      </div>
                      <el-input
                        v-model="trialData.purpose"
                        type="textarea"
                        :autosize="{ minRows: 6, maxRows: 20 }"
                        maxlength="500"
                        show-word-limit
                        placeholder="请精炼描述本次试验要解决或验证什么问题..."
                        :style="{ 
                          fontSize: trialData.purpose_font_size || '14px',
                          textIndent: trialData.purpose_is_indent ? '2em' : '0'
                        }"
                        @change="autoSaveTrial"
                      />
                    </div>
                  </el-card>
                </div>

                <!-- ② 人员与时间 -->
                <div v-else-if="currentStepIndex === 1" class="step-container">
                  <el-card shadow="never" class="wizard-card">
                    <template #header><span>② 人员与时间</span></template>
                    <el-form label-width="100px" label-position="top">
                      <el-row :gutter="40">
                        <el-col :span="12">
                          <el-form-item label="项目负责人">
                            <el-select
                              v-model="trialData.leader_name"
                              filterable
                              allow-create
                              default-first-option
                              placeholder="输入或选择负责人"
                              @change="handleLeaderNameChange"
                              style="width: 100%"
                            >
                              <el-option
                                v-for="name in commonPersonnel"
                                :key="name"
                                :label="name"
                                :value="name"
                              />
                            </el-select>
                          </el-form-item>
                        </el-col>
                        <el-col :span="12">
                          <el-form-item label="参与人员">
                            <el-select
                              v-model="trialData.participants"
                              multiple
                              filterable
                              allow-create
                              default-first-option
                              placeholder="输入或选择参与人"
                              @change="autoSaveTrial"
                              style="width: 100%"
                              value-key="name"
                            >
                              <el-option 
                                v-for="p in commonParticipants" 
                                :key="p.name" 
                                :label="p.name" 
                                :value="p" 
                              />
                            </el-select>
                          </el-form-item>
                        </el-col>
                      </el-row>
                      <el-divider />
                      <el-row :gutter="40">
                        <el-col :span="12">
                          <el-form-item label="计划时间">
                            <el-date-picker
                              v-model="planRange"
                              type="datetimerange"
                              range-separator="至"
                              start-placeholder="计划开始"
                              end-placeholder="计划结束"
                              class="time-range-picker plan"
                              @change="handlePlanTimeChange"
                            />
                          </el-form-item>
                        </el-col>
                        <el-col :span="12">
                          <el-form-item label="实际时间">
                            <el-date-picker
                              v-model="actualRange"
                              type="datetimerange"
                              range-separator="至"
                              start-placeholder="实际开始"
                              end-placeholder="实际结束"
                              class="time-range-picker actual"
                              @change="handleActualTimeChange"
                            />
                          </el-form-item>
                        </el-col>
                      </el-row>
                    </el-form>
                  </el-card>
                </div>

                <!-- ③ 方法与步骤 -->
                <div v-else-if="currentStepIndex === 2" class="step-container">
                  <el-card shadow="never" class="wizard-card">
                    <template #header><span>③ 试验方法、设备与步骤编排</span></template>
                    
                    <div class="method-section">
                      <div class="section-title">1. 参数介绍</div>
                      <el-table :data="trialData.method_parameters" border size="small" class="param-table">
                        <el-table-column label="参数名称" prop="name">
                          <template #default="{ row }"><el-input v-model="row.name" size="small" /></template>
                        </el-table-column>
                        <el-table-column label="数值" prop="value">
                          <template #default="{ row }"><el-input v-model="row.value" size="small" /></template>
                        </el-table-column>
                        <el-table-column label="单位" prop="unit">
                          <template #default="{ row }"><el-input v-model="row.unit" size="small" /></template>
                        </el-table-column>
                        <el-table-column label="备注" prop="remarks">
                          <template #default="{ row }"><el-input v-model="row.remarks" size="small" /></template>
                        </el-table-column>
                        <el-table-column label="操作" width="60" align="center">
                          <template #default="{ $index }">
                            <el-button type="danger" link @click="trialData.method_parameters.splice($index, 1)"><el-icon><Delete /></el-icon></el-button>
                          </template>
                        </el-table-column>
                      </el-table>
                      <el-button type="primary" plain size="small" class="mt-10" @click="trialData.method_parameters.push({ name: '', value: '', unit: '', remarks: '' })">
                        <el-icon><Plus /></el-icon> 添加参数
                      </el-button>

                      <el-divider />

                      <div class="section-title">2. 主要设备设施 (前期准备)</div>
                      <div class="equipment-grid">
                        <div v-for="eq in trialData.equipment_list" :key="eq.id" class="equipment-card">
                          <div class="eq-status available"></div>
                          <div class="eq-main">
                            <div class="eq-name">{{ eq.name }}</div>
                            <div class="eq-model">{{ eq.model }}</div>
                          </div>
                          <div class="eq-details">
                            <div class="detail-item"><span>品牌:</span> {{ eq.brand }}</div>
                            <div class="detail-item"><span>物料号:</span> {{ eq.material_no }}</div>
                          </div>
                          <el-button type="danger" link class="delete-eq-btn" @click="removeEquipment(eq.id)">
                            <el-icon><Delete /></el-icon>
                          </el-button>
                        </div>
                        <el-button type="primary" plain class="add-eq-btn" @click="openEquipmentSelector">
                          <el-icon><Plus /></el-icon> 选择设备 (从物料库)
                        </el-button>
                      </div>

                      <el-divider />

                      <div class="section-title">3. 试验步骤编排 (可拖拽排序)</div>
                    <div class="steps-list">
                      <draggable 
                        v-model="trialData.steps" 
                        item-key="id" 
                        handle=".step-drag-handle" 
                        @end="handleStepReorder"
                        :animation="200"
                        tag="div"
                      >
                        <template #item="{ element: step, index }">
                          <div class="step-item-card">
                            <div class="step-item-header">
                              <div class="header-left">
                                <el-icon class="step-drag-handle"><Rank /></el-icon>
                                <span class="step-index">Step {{ index + 1 }}</span>
                                <el-input v-model="step.name" size="small" class="step-name-input" @change="saveStep(step)" />
                              </div>
                              <div class="header-right">
                                <div class="step-controls-row">
                                  <el-tooltip content="字体大小" placement="top">
                                    <el-select v-model="step.font_size" size="small" style="width: 80px;" @change="saveStep(step)">
                                      <el-option label="12px" value="12px" />
                                      <el-option label="14px" value="14px" />
                                      <el-option label="16px" value="16px" />
                                    </el-select>
                                  </el-tooltip>
                                  
                                  <div class="operator-select">
                                    <el-icon><User /></el-icon>
                                    <el-select v-model="step.operator_name" size="small" placeholder="指派人员" style="width: 120px;" @change="saveStep(step)">
                                      <el-option v-for="p in trialData.participants" :key="p.name" :label="p.name" :value="p.name" />
                                    </el-select>
                                  </div>

                                  <el-button type="danger" link @click="deleteStep(step.id)">
                                    <el-icon><Delete /></el-icon>
                                  </el-button>
                                </div>
                              </div>
                            </div>
                            <div class="step-item-body">
                              <el-input 
                                v-model="step.description" 
                                type="textarea" 
                                :autosize="{ minRows: 2, maxRows: 15 }" 
                                placeholder="详细操作描述..." 
                                :style="{ 
                                  fontSize: step.font_size || '14px'
                                }"
                                @change="saveStep(step)" 
                              />
                              
                              <!-- 新增：附件展示与上传 -->
                              <div class="step-attachments mt-10">
                                <div class="attachment-list" v-if="getStepMaterials(step.id).length > 0">
                                  <div v-for="file in getStepMaterials(step.id)" :key="file.id" class="attachment-item">
                                    <el-tag closable @close="removeAttachment(file.id)" @click="previewAttachment(file)" class="file-tag">
                                      <el-icon><Document v-if="!isImage(file.file_type) && !isVideo(file.file_type)" /><Picture v-else-if="isImage(file.file_type)" /><VideoCamera v-else /></el-icon>
                                      {{ file.file_name }}
                                    </el-tag>
                                  </div>
                                </div>
                                <el-upload
                                  class="step-uploader"
                                  :action="`/lab-api/trials/${trialId}/upload?node_type=Step_Done&step_id=${step.id}`"
                                  :on-success="(res) => handleUploadSuccess(res, step.id)"
                                  :show-file-list="false"
                                  multiple
                                >
                                  <el-button size="small" type="primary" link icon="Upload">上传图片/视频/文件</el-button>
                                </el-upload>
                              </div>
                            </div>
                          </div>
                        </template>
                      </draggable>
                      <el-button type="primary" plain block @click="addNewStep">+ 新增试验步骤</el-button>
                    </div>

                      <el-divider />
                      
                      <div class="section-title">4. 执行依据 / 方法描述</div>
                    <div class="editor-toolbar">
                      <el-button size="small" plain @click="quoteStandardMethod">从标准方法库引用</el-button>
                      <el-divider direction="vertical" />
                      <el-tooltip content="字体大小" placement="top">
                        <el-select v-model="trialData.method_font_size" size="small" style="width: 70px; margin-right: 5px;" @change="autoSaveTrial">
                          <el-option label="12px" value="12px" />
                          <el-option label="14px" value="14px" />
                          <el-option label="16px" value="16px" />
                        </el-select>
                      </el-tooltip>
                    </div>
                    <el-input
                      v-model="trialData.method_description"
                      type="textarea"
                      :autosize="{ minRows: 6, maxRows: 30 }"
                      placeholder="插入标准文件片段、流程图描述或公式..."
                      :style="{ 
                        fontSize: trialData.method_font_size || '14px'
                      }"
                      @change="autoSaveTrial"
                    />
                    </div>
                  </el-card>
                </div>

                <!-- ④ 数据录入与分析 -->
                <div v-else-if="currentStepIndex === 3" class="step-container analysis-layout">
                  <!-- 顶部操作栏 -->
                  <div class="analysis-top-bar">
                    <div class="left">
                      <el-button-group>
                        <el-dropdown @command="(cmd) => { if(cmd==='local') handleImportCSV(); else if(cmd==='monitor') openMonitorImport(); }">
                          <el-button size="small" type="primary">
                            <el-icon><Upload /></el-icon> 导入数据<el-icon class="el-icon--right"><arrow-down /></el-icon>
                          </el-button>
                          <template #dropdown>
                            <el-dropdown-menu>
                              <el-dropdown-item command="local">本地 CSV/Excel</el-dropdown-item>
                              <el-dropdown-item command="monitor">从监测系统导入</el-dropdown-item>
                            </el-dropdown-menu>
                          </template>
                        </el-dropdown>
                        <el-button size="small" icon="Edit" @click="addDataRow">添加行</el-button>
                        <el-button size="small" :icon="CopyDocument" @click="handleBatchPaste">批量粘贴</el-button>
                      </el-button-group>
                      <input type="file" ref="fileInputRef" style="display: none" accept=".csv,.xlsx,.xls" @change="onFileChange">
                      <el-button size="small" type="danger" plain icon="Delete" @click="clearData" style="margin-left: 10px">清空</el-button>
                    </div>
                    <div class="right">
                      <el-radio-group v-model="activeAnalysisView" size="small">
                        <el-radio-button value="single">单轮趋势</el-radio-button>
                        <el-radio-button value="compare">多轮对比</el-radio-button>
                      </el-radio-group>
                      <el-button size="small" type="success" icon="Download" @click="handleExportData" style="margin-left: 10px">导出结果</el-button>
                    </div>
                  </div>

                  <div class="analysis-main">
                    <!-- 左侧面板：管理与标注 -->
                    <div class="analysis-aside">
                      <el-collapse v-model="activeAnalysisPanels">
                        <el-collapse-item name="groups">
                          <template #title>
                            <div class="panel-header">
                              <el-icon><User /></el-icon><span>传感器组 (多组对比)</span>
                            </div>
                          </template>
                          <div class="aside-list">
                            <div v-for="g in analysisData.groups" :key="g.id" class="group-item" :class="{ active: analysisData.activeGroupId === g.id }" @click="analysisData.activeGroupId = g.id">
                              <div style="display: flex; align-items: center; gap: 8px; width: 100%;">
                                <el-checkbox 
                                  v-if="activeAnalysisView === 'compare'" 
                                  v-model="analysisData.compareGroups" 
                                  :value="g.id"
                                  @click.stop
                                />
                                <div style="flex: 1;">
                                  <el-input v-model="g.name" size="small" class="edit-input" @change="autoSaveTrial" @click.stop />
                                </div>
                                <el-button type="danger" link size="small" @click.stop="removeDataGroup(g.id)"><el-icon><Delete /></el-icon></el-button>
                              </div>
                            </div>
                            <el-button type="primary" plain block size="small" icon="Plus" @click.stop="addDataGroup" class="mt-10">添加传感器组</el-button>
                          </div>
                        </el-collapse-item>
                      <el-collapse-item name="rounds">
                        <template #title>
                          <div class="panel-header">
                            <el-icon><Setting /></el-icon><span>轮次管理 (勾选对比)</span>
                          </div>
                        </template>
                        <div class="aside-list">
                          <div v-for="(r, index) in activeGroup?.rounds" :key="r.id" class="aside-item">
                            <el-checkbox v-if="activeGroup?.filters" v-model="activeGroup.filters.rounds" :value="r.name" />
                            <el-input v-model="r.name" size="small" class="edit-input" @change="autoSaveTrial" />
                            <el-button type="danger" link size="small" @click="deleteRound(index)"><el-icon><Delete /></el-icon></el-button>
                          </div>
                          <div v-if="!activeGroup?.rounds?.length" class="empty-hint">请在右侧表格“设为初始”划分轮次</div>
                        </div>
                      </el-collapse-item>
                        <el-collapse-item name="segments">
                          <template #title>
                            <div class="panel-header">
                              <el-icon><FullScreen /></el-icon><span>状态段 (勾选显示)</span>
                            </div>
                          </template>
                          <div class="aside-list">
                            <div v-for="(s, index) in activeGroup?.segments" :key="s.id" class="segment-config-item">
                              <div class="seg-top">
                                <el-checkbox v-if="activeGroup?.filters" v-model="activeGroup.filters.segments" :value="s.name" />
                                <el-color-picker v-model="s.color" size="small" />
                                <el-input v-model="s.name" size="small" placeholder="状态名" />
                                <el-button type="danger" link @click="deleteSegment(index)"><el-icon><Delete /></el-icon></el-button>
                              </div>
                              <div class="seg-range">
                                <el-input-number v-model="s.range[0]" :controls="false" size="small" placeholder="始" style="width: 60px" />
                                <span>-</span>
                                <el-input-number v-model="s.range[1]" :controls="false" size="small" placeholder="终" style="width: 60px" />
                                <el-button type="primary" link size="small" @click="applySegment(s)">应用</el-button>
                              </div>
                            </div>
                            <el-button type="primary" link size="small" icon="Plus" @click="addSegmentFromSelection">新增状态段</el-button>
                          </div>
                        </el-collapse-item>
                      <el-collapse-item name="filters">
                        <template #title>
                          <div class="panel-header">
                            <el-icon><Search /></el-icon><span>全局筛选</span>
                          </div>
                        </template>
                        <el-form v-if="activeGroup?.filters" label-position="top" size="small" style="padding: 0 10px">
                          <el-form-item label="数值范围">
                            <div class="range-inputs">
                              <el-input-number v-model="activeGroup.filters.numericRange[0]" :controls="false" placeholder="Min" style="width: 80px" />
                              <span class="split">-</span>
                              <el-input-number v-model="activeGroup.filters.numericRange[1]" :controls="false" placeholder="Max" style="width: 80px" />
                            </div>
                          </el-form-item>
                        </el-form>
                      </el-collapse-item>
                      </el-collapse>
                    </div>

                    <!-- 中间：趋势图 -->
                    <div class="analysis-center">
                      <div class="chart-container">
                        <div ref="chartRef" class="real-chart"></div>
                      </div>
                    </div>

                    <!-- 右侧：数据表格与统计 -->
                    <div class="analysis-right">
                      <div class="stats-cards">
                        <div class="stat-card primary">
                          <div class="label">{{ activeGroup?.name }} 样本</div>
                          <div class="value">{{ activeGroup?.points.length || 0 }}</div>
                        </div>
                        <div class="stat-card success">
                          <div class="label">当前均值</div>
                          <div class="value">{{ calculateMean }}</div>
                        </div>
                      </div>

                      <el-table :data="activeGroup?.points || []" border size="small" height="calc(100vh - 220px)" class="data-table" :row-class-name="tableRowClassName" ref="dataTableRef">
                        <el-table-column type="index" label="序号" width="50" fixed />
                        <el-table-column prop="timestamp" label="时间" width="90">
                          <template #default="{ row }"><el-input v-model="row.timestamp" size="small" variant="unstyled" @change="autoSaveTrial" /></template>
                        </el-table-column>
                        <el-table-column prop="value" label="测量值" width="90">
                          <template #default="{ row }">
                            <div class="value-cell">
                              <el-input-number v-model="row.value" :controls="false" size="small" style="width: 100%" @change="autoSaveTrial" />
                              <el-tag v-if="row.isInitial" size="small" type="danger" effect="dark" class="initial-tag">初</el-tag>
                            </div>
                          </template>
                        </el-table-column>
                        <el-table-column label="轮次" width="90">
                          <template #default="{ row }">
                            <el-select v-model="row.round" size="small" placeholder="选择轮次" clearable style="width: 100%" @change="autoSaveTrial">
                              <el-option v-for="r in activeGroup?.rounds" :key="r.id" :label="r.name" :value="r.name" />
                            </el-select>
                          </template>
                        </el-table-column>
                        <el-table-column label="状态" width="90">
                          <template #default="{ row }">
                            <el-select v-model="row.status" size="small" placeholder="选择状态" clearable style="width: 100%" @change="autoSaveTrial">
                              <el-option v-for="s in activeGroup?.segments" :key="s.id" :label="s.name" :value="s.name">
                                <span style="display: flex; align-items: center; gap: 8px;">
                                  <span :style="{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: s.color }"></span>
                                  {{ s.name }}
                                </span>
                              </el-option>
                            </el-select>
                          </template>
                        </el-table-column>
                        <el-table-column prop="remark" label="备注" min-width="120">
                          <template #default="{ row }">
                            <el-input v-model="row.remark" size="small" variant="unstyled" placeholder="添加备注..." @change="autoSaveTrial" />
                          </template>
                        </el-table-column>
                        <el-table-column label="操作" width="120" fixed="right">
                          <template #default="{ row, $index }">
                            <div style="display: flex; gap: 4px;">
                              <el-button type="primary" link size="small" @click="createRoundFromSelection(row)" :disabled="row.isInitial">设为初始</el-button>
                              <el-button type="danger" link size="small" @click="deleteDataRow($index)">
                                <el-icon><Delete /></el-icon>
                              </el-button>
                            </div>
                          </template>
                        </el-table-column>
                      </el-table>
                    </div>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </el-scrollbar>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="wizard-footer">
      <div class="footer-left">
        <el-button type="info" plain @click="showRevisionHistory = true">修订历史</el-button>
        <el-button type="warning" plain @click="showValidationPanel = true">完整性检查</el-button>
        <el-button type="default" plain @click="showMaterialsCenter = true">材料中心</el-button>
      </div>
      <div class="footer-right">
        <el-button v-if="currentStepIndex > 0" @click="prevStep">上一步</el-button>
        <el-button type="primary" plain @click="autoSaveTrial" :loading="isSaving">保存草稿</el-button>
        <el-button v-if="currentStepIndex < 3" type="primary" @click="nextStep">下一步</el-button>
        <el-button v-else type="success" @click="handleFinalSubmit">提交审核</el-button>
      </div>
    </div>

    <!-- 辅助弹窗 -->
    <el-drawer v-model="showValidationPanel" title="试验完整性检查" size="400px">
      <div class="validation-panel">
        <div v-for="(v, i) in validationResults" :key="i" class="validation-item" :class="v.type">
          <el-icon><CircleCheck v-if="v.type === 'success'" /><Warning v-else-if="v.type === 'warning'" /><CircleClose v-else /></el-icon>
          <div class="v-content">
            <div class="v-msg">{{ v.message }}</div>
            <el-button size="small" link type="primary" @click="jumpToStep(v.stepIndex)">前往修改</el-button>
          </div>
        </div>
      </div>
    </el-drawer>

    <el-drawer v-model="showRevisionHistory" title="修订历史" size="500px">
      <el-timeline>
        <el-timeline-item v-for="(h, i) in revisionHistory" :key="i" :timestamp="formatDate(h.created_at)" :type="i === 0 ? 'primary' : ''">
          <div class="history-item">
            <span class="operator">{{ h.operator }}</span>
            <span class="action">{{ h.action }}</span>
            <div class="diff" v-if="h.before_value || h.after_value">
              <div class="old">旧值: {{ h.before_value }}</div>
              <div class="new">新值: {{ h.after_value }}</div>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-drawer>

    <!-- 材料中心 -->
    <el-drawer v-model="showMaterialsCenter" title="材料中心" size="600px">
      <el-table :data="allMaterials" border stripe size="small">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="type" label="类型" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-link type="primary" :href="row.url" target="_blank">预览</el-link>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <!-- 物料库选择弹窗 -->
    <el-dialog v-model="showInventoryDialog" title="从物料库选择" width="1000px" append-to-body>
      <div class="inventory-dialog-header">
        <el-input v-model="inventorySearch" placeholder="搜索物料名称、型号、品牌..." class="inventory-search" clearable :prefix-icon="Search" />
        <div class="selected-count" v-if="selectedInventoryItems.length > 0">已选择 <span>{{ selectedInventoryItems.length }}</span> 项</div>
      </div>
      <el-table ref="inventoryTableRef" :data="filteredInventoryMaterials" border stripe size="small" max-height="500px" @selection-change="handleInventorySelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="category" label="类型" width="100" />
        <el-table-column prop="name" label="名称" width="150">
          <template #default="{ row }">
            <div class="name-with-tag"><span>{{ row.name }}</span><el-tag v-if="row.usage_status === '在用'" size="small" type="success" effect="plain" style="margin-left: 5px">在用</el-tag></div>
          </template>
        </el-table-column>
        <el-table-column prop="model" label="型号" width="150" />
        <el-table-column prop="brand" label="品牌" width="100" />
        <el-table-column prop="range" label="量程/规格" width="100" />
        <el-table-column prop="inventory" label="库存" width="70" align="center">
          <template #default="{ row }"><span :class="{ 'text-danger': row.inventory <= 0 }">{{ row.inventory }}</span></template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showInventoryDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmInventorySelection" :disabled="selectedInventoryItems.length === 0">确认添加 ({{ selectedInventoryItems.length }})</el-button>
      </template>
    </el-dialog>

    <!-- 设备选择器 -->
    <el-dialog v-model="showEquipmentSelector" title="从设备台账库选择" width="800px">
      <el-table :data="equipmentOptions" border stripe @selection-change="handleEqSelection">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="设备名称" />
        <el-table-column prop="model" label="型号" />
        <el-table-column prop="sn" label="编号" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }"><el-tag :type="getEqStatusType(row.status)">{{ row.status }}</el-tag></template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showEquipmentSelector = false">取消</el-button>
        <el-button type="primary" @click="confirmEquipment">确认添加</el-button>
      </template>
    </el-dialog>

    <!-- 异常登记弹窗 -->
    <el-dialog v-model="showAddAnomaly" title="异常情况登记" width="600px">
      <el-form :model="anomalyForm" label-width="80px">
        <el-form-item label="现象"><el-input v-model="anomalyForm.phenomenon" type="textarea" placeholder="描述异常现象..." /></el-form-item>
        <el-form-item label="原因"><el-input v-model="anomalyForm.reason" type="textarea" placeholder="初步原因分析..." /></el-form-item>
        <el-form-item label="对策"><el-input v-model="anomalyForm.measure" type="textarea" placeholder="已采取或拟采取的措施..." /></el-form-item>
        <el-form-item label="影响程度">
          <el-radio-group v-model="anomalyForm.impact">
            <el-radio value="轻微">轻微</el-radio>
            <el-radio value="一般">一般</el-radio>
            <el-radio value="重大">重大</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddAnomaly = false">取消</el-button>
        <el-button type="primary" @click="handleSaveAnomaly">提交登记</el-button>
      </template>
    </el-dialog>

    <!-- 附件预览弹窗 -->
    <el-dialog v-model="previewVisible" :title="previewTitle" width="800px" append-to-body>
      <div class="preview-content" style="text-align: center;">
        <template v-if="isImage(previewFileType)">
          <el-image :src="previewUrl" fit="contain" style="max-width: 100%; max-height: 600px;" />
        </template>
        <template v-else-if="isVideo(previewFileType)">
          <video :src="previewUrl" controls style="max-width: 100%; max-height: 600px;"></video>
        </template>
        <template v-else>
          <div class="file-preview-placeholder">
            <el-icon size="64" color="#909399"><Document /></el-icon>
            <p>该文件类型不支持直接预览</p>
            <el-button type="primary" @click="downloadFile(previewUrl)">下载查看</el-button>
          </div>
        </template>
      </div>
    </el-dialog>

    <!-- 批量粘贴对话框 -->
    <el-dialog v-model="showPasteDialog" title="从 Excel 批量粘贴数据" width="600px">
      <div class="paste-tip mb-10">请从 Excel 复制两列数据（时间、数值），在此处粘贴：</div>
      <el-input
        v-model="pasteContent"
        type="textarea"
        :rows="15"
        placeholder="HH:mm:ss	123.45
HH:mm:ss	126.78"
      />
      <template #footer>
        <el-button @click="showPasteDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmPaste">确认导入</el-button>
      </template>
    </el-dialog>

    <!-- 从监测系统导入对话框 -->
    <el-dialog v-model="showMonitorImportDialog" title="从滚筒监测系统导入数据" width="800px">
      <el-table v-loading="monitorFileLoading" :data="monitorFiles" border size="small" height="400px">
        <el-table-column prop="name" label="文件名" />
        <el-table-column prop="mtime" label="修改时间" width="160" />
        <el-table-column prop="size" label="大小" width="100">
          <template #default="{ row }">{{ (row.size / 1024).toFixed(2) }} KB</template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="importMonitorFile(row.name)">导入</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import labApi from '@/api/lab'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import draggable from 'vuedraggable'
import * as XLSX from 'xlsx'
import * as echarts from 'echarts'
import { 
  Rank, User, Delete, Close, Upload, Search, Edit, CirclePlus, Plus,
  CircleCheck, Warning, CircleClose, Picture, Setting, FullScreen,
  Document, VideoCamera, CopyDocument, Download, ArrowDown
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const trialId = route.params.id
const trialData = ref(null)
const currentStepIndex = ref(0)
const isSaving = ref(false)
const activeExecutionItems = ref(['equipment', 'materials', 'steps', 'anomalies'])

// 导入导出相关状态
const showPasteDialog = ref(false)
const pasteContent = ref('')
const showMonitorImportDialog = ref(false)
const monitorFiles = ref([])
const monitorFileLoading = ref(false)
const fileInputRef = ref(null)

// 步骤配置
const stepsConfig = [
  { title: '试验目的与产品', desc: '解决什么问题及关联产品' },
  { title: '人员与时间', desc: '责任归属与时间轴' },
  { title: '方法与步骤', desc: '参数、设备与执行步骤' },
  { title: '数据录入与分析', desc: '数据导入、标注与趋势' }
]

// 辅助状态
const showValidationPanel = ref(false)
const showRevisionHistory = ref(false)
const showEquipmentSelector = ref(false)
const showMaterialsCenter = ref(false)
const showAddAnomaly = ref(false)
const showInventoryDialog = ref(false)

// --- 新增：预览相关状态 ---
const previewVisible = ref(false)
const previewUrl = ref('')
const previewTitle = ref('')
const previewFileType = ref('')

const revisionHistory = ref([])
const userOptions = ref([])
const equipmentOptions = ref([])
const tempEqSelection = ref([])
const inventoryMaterials = ref([])
const inventorySearch = ref('')
const selectedInventoryItems = ref([])
const activeSecForInventory = ref(null)

const anomalyForm = ref({ phenomenon: '', reason: '', measure: '', impact: '一般' })
const editingSecId = ref(null)
const tempSecName = ref('')
const secNameInput = ref(null)

// --- 新增：产品与人员常亮 ---
const productTypes = ref([])
const commonPersonnel = ref(['樊凯', '夏浙源', '杨森', '张工', '李工'])
const commonParticipants = ref([
  { name: '樊凯', role: '核心成员' },
  { name: '夏浙源', role: '核心成员' },
  { name: '杨森', role: '核心成员' }
])

// --- 新增：第四步 数据分析状态 ---
const analysisData = ref({
  groups: [
    { 
      id: Date.now(), 
      name: '默认传感器组', 
      points: [], 
      rounds: [], 
      segments: [],
      filters: {
        rounds: [],
        segments: [],
        numericRange: [null, null],
        timeRange: null
      }
    }
  ],
  activeGroupId: null, // 当前查看的组ID
  compareGroups: [], // 多传感器对比时选中的组ID
  opPoints: []
})

// 初始化 activeGroupId
onMounted(() => {
  if (analysisData.value.groups.length > 0) {
    analysisData.value.activeGroupId = analysisData.value.groups[0].id
  }
})

const activeGroup = computed(() => {
  if (!analysisData.value?.groups || analysisData.value.groups.length === 0) return null
  const group = analysisData.value.groups.find(g => g.id === analysisData.value.activeGroupId)
  return group || analysisData.value.groups[0]
})

const addDataGroup = () => {
  const newGroup = { 
    id: Date.now(), 
    name: `新传感器组 ${analysisData.value.groups.length + 1}`, 
    points: [],
    rounds: [],
    segments: [],
    filters: {
      rounds: [],
      segments: [],
      numericRange: [null, null],
      timeRange: null
    }
  }
  analysisData.value.groups.push(newGroup)
  analysisData.value.activeGroupId = newGroup.id
  ElMessage.success('已添加新传感器组')
  autoSaveTrial()
}

const removeDataGroup = (id) => {
  if (analysisData.value.groups.length <= 1) return ElMessage.warning('至少保留一组数据')
  analysisData.value.groups = analysisData.value.groups.filter(g => g.id !== id)
  if (analysisData.value.activeGroupId === id) {
    analysisData.value.activeGroupId = analysisData.value.groups[0].id
  }
  autoSaveTrial()
}

const activeAnalysisView = ref('single') // single, compare
const activeAnalysisPanels = ref(['groups', 'rounds', 'segments', 'filters'])
const chartRef = ref(null)
const dataTableRef = ref(null)

// 计算属性
const overallCompletion = computed(() => {
  if (!trialData.value) return 0
  let score = 0
  if (trialData.value.purpose) score += 25
  if (trialData.value.leader_name) score += 25
  if (trialData.value.equipment_ids?.length) score += 15
  if (trialData.value.steps?.length) score += 35
  return Math.min(100, score)
})

const calculateMean = computed(() => {
  const points = activeGroup.value?.points || []
  if (!points.length) return 0
  const sum = points.reduce((acc, p) => acc + (p.value || 0), 0)
  return (sum / points.length).toFixed(2)
})

const statusTagType = computed(() => {
  const map = { 'Draft': 'info', 'Ongoing': 'primary', 'Finished': 'success', 'UnderReview': 'warning' }
  return map[trialData.value?.status] || 'info'
})

const filteredInventoryMaterials = computed(() => {
  if (!inventorySearch.value) return inventoryMaterials.value
  const kwd = inventorySearch.value.toLowerCase()
  return inventoryMaterials.value.filter(m => 
    m.name?.toLowerCase().includes(kwd) || m.model?.toLowerCase().includes(kwd) || m.brand?.toLowerCase().includes(kwd)
  )
})

const planRange = ref([])
const actualRange = ref([])
const participantIds = ref([])

// 初始化
onMounted(async () => {
  // 并行发送请求，不再使用 await 阻塞
  const loadData = async () => {
    isSaving.value = true // 借用 isSaving 作为加载状态
    try {
      await Promise.all([
        fetchTrialData(),
        fetchRevisionHistory(),
        fetchProductTypes()
      ])
      
      // 模拟数据
      equipmentOptions.value = [
        { id: 101, name: '万能试验机', model: 'WAW-600', sn: 'SN-001', range: '600kN', expiry_date: '2026-12-31', status: 'available', brand: '国产', material_no: 'EQ-001' },
        { id: 102, name: '激光对中仪', model: 'SKF TKSA 11', sn: 'SN-102', range: '±2mm', expiry_date: '2025-06-30', status: 'available', brand: 'SKF', material_no: 'EQ-002' }
      ]
      
      // 如果后端没有返回 equipment_list，则根据 equipment_ids 从选项中匹配（兼容旧数据）
      if (trialData.value?.equipment_ids?.length > 0 && (!trialData.value.equipment_list || trialData.value.equipment_list.length === 0)) {
        const list = []
        trialData.value.equipment_ids.forEach(id => {
          const eq = equipmentOptions.value.find(e => e.id === id)
          if (eq) list.push(eq)
        })
        trialData.value.equipment_list = list
      }
    } finally {
      isSaving.value = false
    }
  }

  loadData()
  window.addEventListener('resize', handleResize)
})

const handleResize = () => {
  if (myChart) myChart.resize()
}

const fetchProductTypes = async () => {
  try {
    const res = await axios.get('/product-types/')
    productTypes.value = res.data
  } catch (err) {
    console.error('获取产品类型失败:', err)
  }
}

// --- 图表逻辑 ---
let myChart = null
const initChart = () => {
  if (!chartRef.value) return
  
  // 检查容器是否有尺寸
  const clientWidth = chartRef.value.clientWidth
  const clientHeight = chartRef.value.clientHeight
  if (clientWidth === 0 || clientHeight === 0) {
    // 如果没有尺寸，延迟后重试
    setTimeout(() => initChart(), 100)
    return
  }
  
  if (myChart) myChart.dispose()
  
  myChart = echarts.init(chartRef.value)
  
  const series = []
  const xAxisData = []
  const markAreas = []
  
  if (activeAnalysisView.value === 'single') {
    let points = activeGroup.value?.points || []
    const roundsFilter = activeGroup.value?.filters?.rounds || []
    const segmentsFilter = activeGroup.value?.filters?.segments || []
    
    // 过滤轮次
    if (roundsFilter.length > 0) {
      points = points.filter(p => roundsFilter.includes(p.round))
    }
    
    // 过滤状态段
    if (segmentsFilter.length > 0) {
      points = points.filter(p => segmentsFilter.includes(p.status))
    }
    
    // 生成状态段的标记区域
    if (activeGroup.value?.segments) {
      activeGroup.value.segments.forEach(seg => {
        // 只显示选中的状态段或所有状态段
        if (segmentsFilter.length === 0 || segmentsFilter.includes(seg.name)) {
          // 找到该状态段在过滤后数据中的起始和结束位置
          const segPoints = points.filter(p => p.status === seg.name)
          if (segPoints.length > 0) {
            const startIdx = points.indexOf(segPoints[0])
            const endIdx = points.indexOf(segPoints[segPoints.length - 1])
            markAreas.push({
              name: seg.name,
              itemStyle: {
                color: seg.color,
                opacity: 0.15
              },
              data: [
                [
                  { xAxis: startIdx, name: seg.name },
                  { xAxis: endIdx }
                ]
              ]
            })
          }
        }
      })
    }
    
    series.push({
      name: activeGroup.value.name,
      type: 'line',
      smooth: true,
      data: points.map(p => ({
        value: p.value,
        itemStyle: p.isInitial ? { color: '#ef4444', borderWidth: 2, borderColor: '#fff' } : null,
        symbolSize: p.isInitial ? 10 : 4,
        symbol: p.isInitial ? 'diamond' : 'circle'
      })),
      markPoint: { 
        data: (analysisData.value.opPoints || []).map(op => ({ 
          name: op.name, 
          coord: [op.timestamp, op.value], 
          symbol: 'pin' 
        })) 
      },
      markArea: markAreas.length > 0 ? { data: markAreas.map(ma => ma.data[0]) } : undefined
    })
    points.forEach(p => xAxisData.push(p.timestamp))
  } else {
    // 多传感器/多轮对比
    const selectedGroups = analysisData.value.compareGroups && analysisData.value.compareGroups.length > 0 
      ? analysisData.value.compareGroups 
      : [analysisData.value.activeGroupId]
    
    // 找出所有时间戳的并集
    const allTimestamps = []
    const timestampSet = new Set()
    
    selectedGroups.forEach(groupId => {
      const group = analysisData.value.groups.find(g => g.id === groupId)
      if (group) {
        const roundsFilter = group.filters?.rounds || []
        let points = group.points || []
        
        if (roundsFilter.length > 0) {
          points = points.filter(p => roundsFilter.includes(p.round))
        }
        
        points.forEach(p => {
          if (!timestampSet.has(p.timestamp)) {
            timestampSet.add(p.timestamp)
            allTimestamps.push(p.timestamp)
          }
        })
      }
    })
    allTimestamps.sort()
    allTimestamps.forEach(t => xAxisData.push(t))
    
    // 为每个选中的组或组内的轮次创建系列
    selectedGroups.forEach(groupId => {
      const group = analysisData.value.groups.find(g => g.id === groupId)
      if (!group) return
      
      const roundsFilter = group.filters?.rounds || []
      
      if (roundsFilter.length > 0) {
        // 组内有多轮，对比组内的轮次
        roundsFilter.forEach(roundName => {
          const roundPoints = group.points.filter(p => p.round === roundName)
          const dataMap = {}
          roundPoints.forEach(p => {
            dataMap[p.timestamp] = p
          })
          
          const alignedData = []
          allTimestamps.forEach(timestamp => {
            const p = dataMap[timestamp]
            alignedData.push(p ? {
              value: p.value,
              itemStyle: p.isInitial ? { color: '#ef4444', borderWidth: 2, borderColor: '#fff' } : null,
              symbolSize: p.isInitial ? 10 : 4,
              symbol: p.isInitial ? 'diamond' : 'circle'
            } : null)
          })
          
          series.push({
            name: `${group.name} - ${roundName}`,
            type: 'line',
            smooth: true,
            data: alignedData
          })
        })
      } else {
        // 组内没有轮次，直接对比整个组
        const dataMap = {}
        group.points.forEach(p => {
          dataMap[p.timestamp] = p
        })
        
        const alignedData = []
        allTimestamps.forEach(timestamp => {
          const p = dataMap[timestamp]
          alignedData.push(p ? {
            value: p.value,
            itemStyle: p.isInitial ? { color: '#ef4444', borderWidth: 2, borderColor: '#fff' } : null,
            symbolSize: p.isInitial ? 10 : 4,
            symbol: p.isInitial ? 'diamond' : 'circle'
          } : null)
        })
        
        series.push({
          name: group.name,
          type: 'line',
          smooth: true,
          data: alignedData
        })
      }
    })
  }

  const option = {
    title: { 
      text: activeAnalysisView.value === 'single' ? activeGroup.value?.name : '多轮对比', 
      left: 'center',
      top: 10
    },
    tooltip: { trigger: 'axis' },
    legend: { bottom: 10 },
    grid: { top: 60, bottom: 60, left: 60, right: 30 },
    xAxis: { type: 'category', data: xAxisData, boundaryGap: false },
    yAxis: { type: 'value', scale: true },
    series: series,
    toolbox: {
      feature: {
        dataZoom: { yAxisIndex: 'none' },
        restore: {},
        saveAsImage: {}
      }
    }
  }
  
  myChart.setOption(option)
}

watch([() => analysisData.value.groups, activeAnalysisView, () => analysisData.value.activeGroupId, () => analysisData.value.compareGroups], () => {
  nextTick(() => initChart())
}, { deep: true })

onUnmounted(() => {
  if (myChart) myChart.dispose()
  window.removeEventListener('resize', handleResize)
})

const fetchTrialData = async () => {
  try {
    const res = await labApi.get(`/trials/${trialId}`)
    trialData.value = res.data
    
    // 如果有 equipment_ids 但没有 equipment_list，需要初始化 equipment_list
    // 这里我们可以从 equipmentOptions 中匹配，或者等 equipmentOptions 加载完后再匹配
    if (trialData.value.equipment_ids && !trialData.value.equipment_list) {
      trialData.value.equipment_list = []
    }

    if (!trialData.value.steps) {
      trialData.value.steps = []
    } else {
      // 按照 sort_order 排序
      trialData.value.steps.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
    }
    currentStepIndex.value = trialData.value.current_step_index || 0
    if (trialData.value.plan_start_at) planRange.value = [trialData.value.plan_start_at, trialData.value.plan_end_at]
    if (trialData.value.actual_start_at) actualRange.value = [trialData.value.actual_start_at, trialData.value.actual_end_at]
    
    // 初始化分析数据
    if (trialData.value.data_analysis && trialData.value.data_analysis.groups) {
      // 深度合并并确保 filters 存在
      analysisData.value = {
        ...analysisData.value,
        ...trialData.value.data_analysis,
        groups: trialData.value.data_analysis.groups.map(g => ({
          ...g,
          points: g.points || [],
          rounds: g.rounds || [],
          segments: g.segments || [],
          filters: g.filters || {
            rounds: [],
            segments: [],
            numericRange: [null, null],
            timeRange: null
          }
        }))
      }
    } else if (trialData.value.data_analysis && !trialData.value.data_analysis.groups) {
      // 兼容旧版本数据，将其转换为新结构
      const oldPoints = trialData.value.data_analysis.points || []
      analysisData.value.groups[0].points = oldPoints
      analysisData.value.groups[0].rounds = trialData.value.data_analysis.rounds || []
      analysisData.value.groups[0].segments = trialData.value.data_analysis.segments || []
      analysisData.value.groups[0].filters = {
        rounds: [],
        segments: [],
        numericRange: [null, null],
        timeRange: null
      }
    }
    
    // 强制确保 activeGroupId 指向有效的组
    if (analysisData.value.groups && analysisData.value.groups.length > 0) {
      const exists = analysisData.value.groups.find(g => g.id === analysisData.value.activeGroupId)
      if (!exists) {
        analysisData.value.activeGroupId = analysisData.value.groups[0].id
      }
    }
  } catch (err) { 
    console.error('加载详情失败:', err)
    ElMessage.error('加载失败') 
  }
}

const handleProductChange = (id) => {
  const pt = productTypes.value.find(p => p.id === id)
  if (pt) {
    trialData.value.product_name = pt.type_name
    trialData.value.product_model_code = pt.model_code
    autoSaveTrial()
  }
}

const handleLeaderNameChange = (val) => {
  trialData.value.leader_name = val
  autoSaveTrial()
}

const removeParticipant = (index) => {
  trialData.value.participants.splice(index, 1)
  autoSaveTrial()
}

const fetchRevisionHistory = async () => {
  try {
    const res = await labApi.get(`/trials/${trialId}/revision_history`)
    revisionHistory.value = res.data
  } catch (err) {}
}

const autoSaveTrial = async () => {
  isSaving.value = true
  try {
    const payload = { 
      ...trialData.value, 
      current_step_index: currentStepIndex.value, 
      operator: '当前用户',
      data_analysis: analysisData.value
    }
    // 排除关联表字段，防止后端更新冲突
    const fieldsToExclude = ['steps', 'sections', 'anomaly_logs', 'materials', 'revisions']
    fieldsToExclude.forEach(field => delete payload[field])
    
    await labApi.put(`/trials/${trialId}`, payload)
    ElMessage({
      message: '草稿已保存',
      type: 'success',
      duration: 1000
    })
    fetchRevisionHistory()
  } catch (err) {
    console.error('保存失败:', err)
    ElMessage.error('保存失败，请检查网络连接')
  } finally { 
    setTimeout(() => isSaving.value = false, 500) 
  }
}

// 导航
const jumpToStep = (index) => { currentStepIndex.value = index; autoSaveTrial() }
const prevStep = () => { if (currentStepIndex.value > 0) jumpToStep(currentStepIndex.value - 1) }
const nextStep = () => { if (currentStepIndex.value < 3) jumpToStep(currentStepIndex.value + 1) }

// 动态表格逻辑
const getSections = (stage) => trialData.value?.sections?.filter(s => s.stage === stage).sort((a,b) => (a.sort_order||0)-(b.sort_order||0)) || []
const getSortedFields = (fields) => [...(fields||[])].sort((a,b) => (a.label||'').localeCompare(b.label||'', 'zh-CN'))
const getDynamicColWidth = (field, col) => {
  if (field.columnWidths?.[col]) return field.columnWidths[col]
  return 150
}

const saveSection = async (sec) => { await labApi.put(`/trials/${trialId}/sections/${sec.id}`, sec) }
const addNewSection = async (stage) => {
  const res = await labApi.post(`/trials/${trialId}/sections`, { name: '新章节', stage, data_content: { fields: [] } })
  trialData.value.sections.push(res.data)
}
const handleDeleteSection = (id) => {
  ElMessageBox.confirm('确定删除章节吗？').then(async () => {
    await labApi.delete(`/trials/${trialId}/sections/${id}`)
    trialData.value.sections = trialData.value.sections.filter(s => s.id !== id)
  })
}
const startEditSecName = (sec) => { editingSecId.value = sec.id; tempSecName.value = sec.name; nextTick(() => secNameInput.value?.focus()) }
const saveSecName = async (sec) => {
  if (tempSecName.value && tempSecName.value !== sec.name) {
    sec.name = tempSecName.value
    await saveSection(sec)
  }
  editingSecId.value = null
}

// --- 步骤附件处理 ---
const getStepMaterials = (stepId) => {
  if (!trialData.value?.materials) return []
  return trialData.value.materials.filter(m => m.step_id === stepId)
}

const handleUploadSuccess = (res, stepId) => {
  if (!trialData.value.materials) trialData.value.materials = []
  trialData.value.materials.push(res)
  ElMessage.success('上传成功')
}

const isImage = (type) => type?.startsWith('image/')
const isVideo = (type) => type?.startsWith('video/')

const previewAttachment = (file) => {
  // 从 file_path 提取相对路径并拼接静态资源前缀
  // 确保路径使用正斜杠，且不以斜杠开头
  let relativePath = file.file_path.replace(/\\/g, '/');
  if (relativePath.startsWith('/')) {
    relativePath = relativePath.substring(1);
  }
  
  // 映射到前端代理路径：/lab-api/static/lab_files/...
  // 经过 proxy rewrite 变为 /api/static/lab_files/...
  previewUrl.value = `/lab-api/${relativePath}`;
  previewTitle.value = file.file_name;
  previewFileType.value = file.file_type;
  previewVisible.value = true;
};

const removeAttachment = async (id) => {
  try {
    await labApi.delete(`/trial-materials/${id}`)
    trialData.value.materials = trialData.value.materials.filter(m => m.id !== id)
    ElMessage.success('已移除附件')
  } catch (err) {
    console.error('移除附件失败:', err)
    ElMessage.error('移除失败')
  }
}

const downloadFile = (url) => {
  window.open(url, '_blank')
}

// 步骤与测量
const addNewStep = async () => {
  const res = await labApi.post(`/trials/${trialId}/steps`, { name: '新步骤', sort_order: trialData.value.steps?.length || 0, status: 'Pending', measurement_items: [] })
  trialData.value.steps.push(res.data)
}
const saveStep = async (s) => { await labApi.put(`/trials/${trialId}/steps/${s.id}`, s) }
const deleteStep = async (id) => { await labApi.delete(`/trials/${trialId}/steps/${id}`); trialData.value.steps = trialData.value.steps.filter(s => s.id !== id) }
const handleStepReorder = async () => { 
  isSaving.value = true
  try {
    const updates = trialData.value.steps.map((s, i) => {
      s.sort_order = i
      return saveStep(s)
    })
    await Promise.all(updates)
    ElMessage.success('步骤排序已保存')
  } catch (err) {
    console.error('排序保存失败:', err)
    ElMessage.error('排序保存失败')
  } finally {
    isSaving.value = false
  }
}

// --- 第四步：数据分析逻辑 ---
const handleImportCSV = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

const onFileChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = (ev) => {
    const data = ev.target.result
    const workbook = XLSX.read(data, { type: 'binary' })
    const firstSheetName = workbook.SheetNames[0]
    const worksheet = workbook.Sheets[firstSheetName]
    const json = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
    
    processImportedData(json)
    e.target.value = '' // 清空以便下次触发
  }
  reader.readAsBinaryString(file)
}

const handleBatchPaste = () => { 
  showPasteDialog.value = true
}

const confirmPaste = () => {
  if (!pasteContent.value) {
    showPasteDialog.value = false
    return
  }
  
  // 解析粘贴内容（通常是 Tab 分隔）
  const lines = pasteContent.value.split('\n').filter(l => l.trim())
  const data = lines.map(line => line.split('\t'))
  
  processImportedData(data)
  pasteContent.value = ''
  showPasteDialog.value = false
}

const openMonitorImport = async () => {
  showMonitorImportDialog.value = true
  monitorFileLoading.value = true
  try {
    // 关键：由于 axios.defaults.baseURL = '/api'，
    // 调用 /data/files 实际上会发送请求到 /api/data/files
    // 这正好命中 Vite 代理中转发到 5001 端口的配置
    const res = await axios.get('/data/files')
    if (Array.isArray(res.data)) {
      monitorFiles.value = res.data
    } else {
      console.error('监测系统返回了非预期的格式:', res.data)
      // 备选：如果 baseURL 没起作用，尝试完整路径
      const resAlt = await axios.get('/api/data/files')
      if (Array.isArray(resAlt.data)) {
        monitorFiles.value = resAlt.data
      } else {
        monitorFiles.value = []
        ElMessage.warning('未能获取到有效的文件列表，请检查监测系统后端是否正常运行')
      }
    }
  } catch (err) {
    console.error('获取监测文件失败:', err)
    // 尝试直接通过 5001 端口（如果浏览器能直连）
    try {
      const resDirect = await axios.get('http://127.0.0.1:5001/api/data/files')
      if (Array.isArray(resDirect.data)) {
        monitorFiles.value = resDirect.data
        return
      }
    } catch (e2) {}
    
    ElMessage.error('无法连接到监测系统，请确保监测系统已启动')
    monitorFiles.value = []
  } finally {
    monitorFileLoading.value = false
  }
}

const importMonitorFile = async (filename) => {
  try {
    let res;
    try {
      // 同样遵循 baseURL 规则
      res = await axios.get(`/data/download/${filename}`, { responseType: 'blob' })
    } catch (e) {
      // 备选路径
      res = await axios.get(`/api/data/download/${filename}`, { responseType: 'blob' })
    }
    
    const reader = new FileReader()
    reader.onload = (ev) => {
      const data = ev.target.result
      const workbook = XLSX.read(data, { type: 'binary' })
      const firstSheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[firstSheetName]
      const json = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
      processImportedData(json)
      showMonitorImportDialog.value = false
    }
    reader.readAsBinaryString(res.data)
  } catch (err) {
    console.error('下载监测文件失败:', err)
    ElMessage.error('下载文件失败')
  }
}

const processImportedData = (rows) => {
  if (rows.length < 2) {
    ElMessage.warning('文件数据行数不足')
    return
  }

  // 第一步：解析表头
  const headerRow = rows[0]
  const hasHeader = headerRow.some(cell => 
    typeof cell === 'string' && 
    (cell.toLowerCase().includes('time') || 
     cell.toLowerCase().includes('timestamp') || 
     cell.includes('时间') || 
     isNaN(parseFloat(cell)))
  )

  let headers = []
  let dataStartRow = 0

  if (hasHeader) {
    headers = headerRow.map(h => (typeof h === 'string' ? h.trim() : `列 ${h}`))
    dataStartRow = 1
  } else {
    // 如果没有表头，生成默认列名
    headers = ['时间'].concat(Array.from({ length: headerRow.length - 1 }, (_, i) => `传感器 ${i + 1}`))
  }

  // 第二步：确定哪些列包含数值数据
  const dataColumns = []
  // 假设第一列是时间，从第二列开始检查
  for (let colIndex = 1; colIndex < headers.length; colIndex++) {
    // 检查前几行是否有数值
    let hasData = false
    for (let rowIndex = dataStartRow; rowIndex < Math.min(rows.length, dataStartRow + 10); rowIndex++) {
      const cell = rows[rowIndex]?.[colIndex]
      if (cell !== undefined && cell !== null && cell !== '' && !isNaN(parseFloat(cell))) {
        hasData = true
        break
      }
    }
    if (hasData) {
      dataColumns.push({
        index: colIndex,
        name: headers[colIndex]
      })
    }
  }

  if (dataColumns.length === 0) {
    ElMessage.warning('未在文件中找到有效的数值数据列')
    return
  }

  // 第三步：为每个数据列创建/找到对应的传感器组并填充数据
  const groupsCreated = []
  let totalPointsImported = 0

  dataColumns.forEach(colInfo => {
    // 查找是否已存在同名的传感器组
    let group = analysisData.value.groups.find(g => g.name === colInfo.name)
    if (!group) {
      // 创建新的传感器组
      group = {
        id: Date.now() + Math.random(),
        name: colInfo.name,
        points: [],
        rounds: [],
        segments: [],
        filters: {
          rounds: [],
          segments: [],
          numericRange: [null, null],
          timeRange: null
        }
      }
      analysisData.value.groups.push(group)
      groupsCreated.push(group.name)
    }

    // 填充该列的数据
    for (let rowIndex = dataStartRow; rowIndex < rows.length; rowIndex++) {
      const row = rows[rowIndex]
      if (!row) continue

      const timestampCell = row[0]
      const valueCell = row[colInfo.index]
      const value = parseFloat(valueCell)

      if (isNaN(value)) continue

      let timestampStr = ''
      if (timestampCell) {
        if (typeof timestampCell === 'number') {
          // 如果是 Excel 序列号
          try {
            timestampStr = dayjs('1899-12-30').add(timestampCell, 'day').format('HH:mm:ss')
          } catch {
            timestampStr = dayjs().format('HH:mm:ss')
          }
        } else {
          timestampStr = String(timestampCell)
        }
      } else {
        timestampStr = dayjs().format('HH:mm:ss')
      }

      group.points.push({
        id: Date.now() + Math.random(),
        timestamp: timestampStr,
        value: value,
        round: '',
        status: '',
        op: '',
        remark: '',
        isInitial: false
      })
      totalPointsImported++
    }
  })

  // 如果是第一次导入，激活第一个创建的组
  if (groupsCreated.length > 0) {
    const firstNewGroup = analysisData.value.groups.find(g => g.name === groupsCreated[0])
    if (firstNewGroup) {
      analysisData.value.activeGroupId = firstNewGroup.id
    }
  }

  let message = `成功导入 ${totalPointsImported} 条数据`
  if (groupsCreated.length > 0) {
    message += `，并创建了 ${groupsCreated.length} 个新传感器组`
  }
  ElMessage.success(message)
  autoSaveTrial()
}
const addDataRow = () => { 
  console.log('Adding data row, current activeGroup:', activeGroup.value)
  if (!activeGroup.value) {
    ElMessage.warning('请先选择或创建一个传感器组')
    return
  }
  
  // 确保 points 是数组
  if (!activeGroup.value.points) {
    activeGroup.value.points = []
  }

  const newPoint = { 
    id: Date.now(), 
    timestamp: dayjs().format('HH:mm:ss'), 
    value: 0, 
    round: '', 
    status: '', 
    op: '', 
    remark: '',
    isInitial: false 
  }
  
  // 使用解构赋值确保触发 Vue 的数组响应式
  activeGroup.value.points = [...activeGroup.value.points, newPoint]
  
  console.log('New point added, total points:', activeGroup.value.points.length)
  ElMessage({
    message: '已添加新行',
    type: 'success',
    duration: 800
  })
  autoSaveTrial()
}

const deleteDataRow = (index) => {
  if (!activeGroup.value) return
  ElMessageBox.confirm('确定删除这一行数据吗？').then(() => {
    const deletedPoint = activeGroup.value.points[index]
    activeGroup.value.points.splice(index, 1)
    
    // 如果删除的是初始值点，需要重新计算轮次
    if (deletedPoint && deletedPoint.isInitial) {
      recalculateAllRounds()
    }
    
    ElMessage.success('已删除')
    autoSaveTrial()
  })
}
const clearData = () => {
  ElMessageBox.confirm('确定清空当前组所有实验数据吗？').then(() => {
    activeGroup.value.points = []
    autoSaveTrial()
  })
}

const createRoundFromSelection = (row) => {
  if (!activeGroup.value) return
  
  // 先检查是否已经是初始值
  if (row.isInitial) {
    ElMessage.warning('该点已设为初始值')
    return
  }
  
  // 设为初始值
  row.isInitial = true
  
  // 重新计算所有轮次
  recalculateAllRounds()
  
  ElMessage.success('已设为初始值，轮次已重新划分')
  autoSaveTrial()
}

const recalculateAllRounds = () => {
  if (!activeGroup.value) return
  
  const points = activeGroup.value.points || []
  const initialPoints = points.filter(p => p.isInitial)
  
  // 清空所有轮次
  activeGroup.value.rounds = []
  
  // 如果没有初始值，清空所有点的轮次
  if (initialPoints.length === 0) {
    points.forEach(p => p.round = '')
    return
  }
  
  // 找出所有初始值点的索引
  const initialIndices = []
  points.forEach((p, idx) => {
    if (p.isInitial) initialIndices.push(idx)
  })
  
  // 划分轮次：两个初始值之间的所有点属于一个轮次
  for (let i = 0; i < initialIndices.length; i++) {
    const startIdx = initialIndices[i]
    const endIdx = i < initialIndices.length - 1 ? initialIndices[i + 1] : points.length
    const roundName = `轮次 ${i + 1}`
    
    // 创建轮次
    activeGroup.value.rounds.push({
      id: Date.now() + i,
      name: roundName,
      initialValue: points[startIdx].value,
      startTime: points[startIdx].timestamp
    })
    
    // 给这个轮次的所有点标记
    for (let j = startIdx; j < endIdx; j++) {
      points[j].round = roundName
    }
  }
}

const addSegmentByRange = (name, startIdx, endIdx) => {
  const segment = {
    id: Date.now(),
    name: name || `状态段 ${activeGroup.value.segments.length + 1}`,
    color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][activeGroup.value.segments.length % 5],
    range: [startIdx, endIdx]
  }
  
  // 在表格中标记
  const points = activeGroup.value.points
  for (let i = startIdx - 1; i < endIdx && i < points.length; i++) {
    points[i].status = segment.name
  }
  
  activeGroup.value.segments.push(segment)
  ElMessage.success(`已标记序号 ${startIdx}-${endIdx} 为 ${segment.name}`)
  autoSaveTrial()
}

const deleteRound = (index) => {
  if (!activeGroup.value) return
  const round = activeGroup.value.rounds[index]
  
  ElMessageBox.confirm(`确定删除轮次 ${round.name} 吗？相关的初始值标记也会被移除。`).then(() => {
    // 找出该轮次中的初始值点并取消标记
    if (activeGroup.value.points) {
      activeGroup.value.points.forEach(p => {
        if (p.round === round.name && p.isInitial) {
          p.isInitial = false
        }
        if (p.round === round.name) {
          p.round = ''
        }
      })
    }
    
    // 删除轮次
    activeGroup.value.rounds.splice(index, 1)
    
    // 重新计算剩余轮次
    recalculateAllRounds()
    
    // 从过滤器中移除
    if (activeGroup.value.filters && activeGroup.value.filters.rounds) {
      activeGroup.value.filters.rounds = activeGroup.value.filters.rounds.filter(r => r !== round.name)
    }
    
    ElMessage.success(`已删除轮次: ${round.name}`)
    autoSaveTrial()
  })
}

const addSegmentFromSelection = () => {
  if (!activeGroup.value) return
  const newSegment = {
    id: Date.now(),
    name: `状态段 ${activeGroup.value.segments.length + 1}`,
    color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][activeGroup.value.segments.length % 5],
    range: [1, 10] // 默认给一个可见的区间
  }
  activeGroup.value.segments.push(newSegment)
  applySegment(newSegment)
  autoSaveTrial()
}

const deleteSegment = (index) => {
  if (!activeGroup.value) return
  const segment = activeGroup.value.segments[index]
  // 清除当前组表格中的标记
  if (activeGroup.value.points) {
    activeGroup.value.points.forEach(p => {
      if (p.status === segment.name) p.status = ''
    })
  }
  activeGroup.value.segments.splice(index, 1)
  autoSaveTrial()
}

const applySegment = (s) => {
  if (!activeGroup.value) return
  if (s.range[0] > 0 && s.range[1] >= s.range[0]) {
    const points = activeGroup.value.points || []
    for (let i = s.range[0] - 1; i < s.range[1] && i < points.length; i++) {
      points[i].status = s.name
    }
    ElMessage.success(`状态段 ${s.name} 已应用到序号 ${s.range[0]}-${s.range[1]}`)
    autoSaveTrial()
  } else {
    ElMessage.warning('请输入正确的起止序号')
  }
}

const getSegmentColor = (statusName) => {
  const seg = activeGroup.value?.segments?.find(s => s.name === statusName)
  return seg ? seg.color : '#94a3b8'
}

const tableRowClassName = ({ row }) => {
  if (row.isInitial) return 'initial-row'
  return ''
}

const handleExportData = () => {
  if (!activeGroup.value || !activeGroup.value.points?.length) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  const data = activeGroup.value.points.map(p => ({
    '时间': p.timestamp,
    '测量值': p.value,
    '轮次': p.round,
    '状态': p.status,
    '操作': p.op,
    '备注': p.remark
  }))

  const worksheet = XLSX.utils.json_to_sheet(data)
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, activeGroup.value.name || '实验数据')
  
  XLSX.writeFile(workbook, `${trialData.value.trial_no || 'Trial'}_${activeGroup.value.name}_数据导出.xlsx`)
  ElMessage.success('数据已导出为Excel')
}
const exportReport = () => { ElMessage.success('实验报告生成中，请稍候...') }
const handleFinalSubmit = () => { ElMessage.success('试验报告已提交审核') }

// 校验面板
const validationResults = computed(() => {
  const res = []
  if (!trialData.value) return res
  if (!trialData.value.purpose) res.push({ type: 'danger', message: '目的未填写', stepIndex: 0 })
  if (!trialData.value.leader_name) res.push({ type: 'danger', message: '负责人未指定', stepIndex: 1 })
  if (!trialData.value.steps?.length) res.push({ type: 'warning', message: '无步骤编排', stepIndex: 2 })
  return res
})

const handleSaveAnomaly = async () => { 
  const res = await labApi.post(`/trials/${trialId}/anomalies`, anomalyForm.value)
  trialData.value.anomaly_logs.push(res.data)
  showAddAnomaly.value = false
}

const formatDate = (d) => d ? dayjs(d).format('YYYY-MM-DD HH:mm') : '-'
const getStepStatusTag = (s) => ({ 'Pending': 'info', 'Ongoing': 'primary', 'Completed': 'success', 'Anomaly': 'danger' }[s] || 'info')
const getEqStatusType = (s) => s === 'available' ? 'success' : 'danger'
const selectedEquipments = computed(() => equipmentOptions.value.filter(e => trialData.value?.equipment_ids?.includes(e.id)))

const applyPurposeTemplate = (t) => { trialData.value.purpose = t===1 ? "旨在验证..." : "旨在确认..."; autoSaveTrial() }
const handlePlanTimeChange = (v) => { if(v){trialData.value.plan_start_at=v[0]; trialData.value.plan_end_at=v[1]} autoSaveTrial() }
const handleActualTimeChange = (v) => { if(v){trialData.value.actual_start_at=v[0]; trialData.value.actual_end_at=v[1]} autoSaveTrial() }
const handleEqSelection = (v) => { tempEqSelection.value = v }
const confirmEquipment = () => { trialData.value.equipment_ids = tempEqSelection.value.map(e=>e.id); showEquipmentSelector.value = false; autoSaveTrial() }
const quoteStandardMethod = () => { trialData.value.method_description += "\n引用 SOP..."; autoSaveTrial() }
const removeParam = (i) => { trialData.value.method_parameters.splice(i,1); autoSaveTrial() }
const addParam = () => { trialData.value.method_parameters.push({name:'', value:'', unit:'', remarks:''}); autoSaveTrial() }

const allMaterials = computed(() => {
  const mats = []
  trialData.value?.sections?.forEach(sec => {
    sec.data_content?.fields?.forEach(f => {
      f.rows?.forEach(r => { if(r.materials) r.materials.forEach(m => mats.push(m)) })
    })
  })
  return mats
})
// 物料库联动
const openInventorySelector = (sec) => { activeSecForInventory.value = sec; showInventoryDialog.value = true; fetchInventory() }
const openEquipmentSelector = () => { activeSecForInventory.value = 'step3_equipment'; showInventoryDialog.value = true; fetchInventory() }

const fetchInventory = async () => { const res = await labApi.get('/materials'); inventoryMaterials.value = res.data }
const handleInventorySelectionChange = (val) => { selectedInventoryItems.value = val }

const removeEquipment = (id) => {
  trialData.value.equipment_list = trialData.value.equipment_list.filter(e => e.id !== id)
  autoSaveTrial()
}

const confirmInventorySelection = () => {
  if (activeSecForInventory.value === 'step3_equipment') {
    if (!trialData.value.equipment_list) trialData.value.equipment_list = []
    selectedInventoryItems.value.forEach(m => {
      if (!trialData.value.equipment_list.find(e => e.id === m.id)) {
        trialData.value.equipment_list.push({
          id: m.id,
          name: m.name,
          model: m.model,
          brand: m.brand,
          material_no: m.material_no
        })
      }
    })
    // 同时也更新 equipment_ids 以便持久化
    trialData.value.equipment_ids = trialData.value.equipment_list.map(e => e.id)
    autoSaveTrial()
  } else {
    const sec = activeSecForInventory.value
    let tableField = sec.data_content.fields.find(f => f.type === 'table')
    if (!tableField) { 
      sec.data_content.fields.push({ type: 'table', label: '数据表', columns: ['参数', '测量值', '判定'], rows: [{}] })
      tableField = sec.data_content.fields[sec.data_content.fields.length-1] 
    }
    selectedInventoryItems.value.forEach(m => {
      const row = {}
      tableField.columns.forEach(col => {
        if (col.includes('名称')) row[col] = m.name
        else if (col.includes('型号')) row[col] = m.model
        else if (col.includes('品牌')) row[col] = m.brand
        else if (col.includes('物料号')) row[col] = m.material_no
      })
      tableField.rows.push(row)
    })
    saveSection(sec)
  }
  showInventoryDialog.value = false
}
</script>

<style scoped>
.trial-wizard { height: 100vh; display: flex; flex-direction: column; background: #fcfcfd; }
.wizard-header { height: 64px; background: #fff; border-bottom: 1px solid #eef2f6; padding: 0 24px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
.header-info { display: flex; align-items: center; gap: 12px; }
.trial-no { font-weight: 600; color: #1e293b; font-family: monospace; }
.trial-name { font-size: 16px; color: #64748b; }
.header-progress { display: flex; align-items: center; gap: 15px; }
.progress-label { font-size: 12px; color: #94a3b8; }
.wizard-body { flex: 1; display: flex; overflow: hidden; }
.wizard-aside { width: 200px; background: #fff; border-right: 1px solid #eef2f6; padding: 40px 15px; flex-shrink: 0; }
.step-desc { font-size: 13px; color: #94a3b8; cursor: pointer; transition: all 0.2s; padding: 6px 0; }
.step-desc.active { color: #3b82f6; font-weight: 600; }
.wizard-content { flex: 1; background: #f8fafc; overflow-y: auto; }
.step-card-wrapper { max-width: 1400px; margin: 0 auto; padding: 25px 30px 100px; }
.wizard-card { border-radius: 12px; border: 1px solid #eef2f6; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.equipment-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
.equipment-card { background: #fff; border: 1px solid #eef2f6; border-radius: 8px; padding: 12px; position: relative; }
.eq-status { width: 6px; height: 6px; border-radius: 50%; position: absolute; top: 12px; right: 12px; }
.eq-status.available { background: #10b981; }
.eq-main { margin-bottom: 8px; }
.eq-name { font-weight: 600; font-size: 14px; }
.eq-model { font-size: 11px; color: #94a3b8; }
.eq-details { font-size: 12px; color: #64748b; }
.steps-list { display: flex; flex-direction: column; gap: 12px; }
.step-item-card { background: #fff; border: 1px solid #eef2f6; border-radius: 8px; overflow: hidden; }
.step-item-header { padding: 8px 16px; background: #f8fafc; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
.step-drag-handle { cursor: move; color: #cbd5e1; }
.step-index { font-weight: 700; color: #64748b; font-size: 12px; min-width: 40px; }
.step-name-input { width: 300px; }
.step-controls-row { display: flex; align-items: center; gap: 15px; }
.operator-select { display: flex; align-items: center; gap: 8px; color: #64748b; font-size: 13px; }
.step-item-body { padding: 12px; }
.measurement-section { background: #f0f9ff; padding: 12px; border-radius: 6px; margin-top: 10px; }
.section-label { font-weight: 600; color: #0369a1; font-size: 12px; margin-bottom: 8px; }
.measurement-item { margin-bottom: 8px; }
.wizard-footer { height: 72px; background: #fff; border-top: 1px solid #eef2f6; padding: 0 40px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; box-shadow: 0 -4px 12px rgba(0,0,0,0.03); }
.sec-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; }
.sec-title-wrap { display: flex; align-items: center; gap: 10px; }
.sec-title-wrap h3 { margin: 0; font-size: 15px; color: #1e293b; cursor: pointer; }
.dynamic-table-container { margin-bottom: 24px; }
.table-header-ops { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.table-label { font-weight: 600; color: #475569; font-size: 13px; }
.cell-textarea :deep(.el-textarea__inner) { box-shadow: none; border: none; background: transparent; padding: 4px 8px; resize: none; line-height: 1.5; white-space: pre; overflow-x: hidden; }

/* 修复项目负责人选择框 visibility */
:deep(.el-select .el-input__wrapper) {
  min-height: 40px;
}
:deep(.el-form-item__label) {
  font-weight: 600;
  color: #334155;
}

.fade-slide-enter-active, .fade-slide-leave-active { transition: all 0.3s ease; }
.fade-slide-enter-from { opacity: 0; transform: translateX(20px); }
.fade-slide-leave-to { opacity: 0; transform: translateX(-20px); }
.mb-20 { margin-bottom: 20px; }
.mt-10 { margin-top: 10px; }
.mb-15 { margin-bottom: 15px; }
.validation-item { display: flex; gap: 12px; padding: 12px; border-radius: 6px; margin-bottom: 10px; }
.validation-item.danger { background: #fef2f2; color: #991b1b; }
.validation-item.warning { background: #fffbeb; color: #92400e; }
.validation-item.success { background: #f0fdf4; color: #166534; }

/* --- 数据分析布局 --- */
.analysis-layout { height: 100%; display: flex; flex-direction: column; background: #fff !important; padding: 0 !important; max-width: none !important; margin: 0 !important; }
.analysis-top-bar { height: 64px; border-bottom: 1px solid #eef2f6; display: flex; justify-content: space-between; align-items: center; padding: 0 30px; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.03); z-index: 10; }
.analysis-main { flex: 1; display: flex; overflow: hidden; background: #f0f2f5; padding: 15px; gap: 15px; }
.analysis-aside { width: 240px; border-right: none; overflow-y: auto; background: #fff; padding: 20px; flex-shrink: 0; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.04); }
.analysis-center { flex: 1; display: flex; flex-direction: column; background: #fff; margin: 0; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.04); position: relative; }
.analysis-right { width: 320px; display: flex; flex-direction: column; background: #fff; padding: 20px; border-left: none; flex-shrink: 0; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.04); }

.panel-header { display: flex; align-items: center; gap: 10px; color: #1e293b; font-weight: 600; font-size: 14px; margin-bottom: 2px; }
.aside-list { padding: 10px 0; }
.group-item { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-radius: 8px; cursor: pointer; transition: all 0.2s; margin-bottom: 10px; border: 1px solid #f1f5f9; background: #f8fafc; }
.group-item:hover { background: #f1f5f9; border-color: #e2e8f0; }
.group-item.active { background: #eff6ff; border-color: #3b82f6; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1); }
.group-item .edit-input { flex: 1; }

.aside-item { display: flex; align-items: center; gap: 12px; margin-bottom: 15px; padding: 4px 0; }
.segment-config-item { border: 1px solid #f1f5f9; border-radius: 10px; padding: 12px; margin-bottom: 15px; background: #f8fafc; }
.seg-top { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.seg-range { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #64748b; }

.edit-input { flex: 1; }
.range-inputs { display: flex; align-items: center; gap: 10px; padding: 5px 0; }
.range-inputs .split { color: #94a3b8; }

:deep(.el-collapse) { border: none; }
:deep(.el-collapse-item__header) { border: none; height: 48px; line-height: 48px; background: transparent; }
:deep(.el-collapse-item__wrap) { border: none; background: transparent; }
:deep(.el-collapse-item__content) { padding-bottom: 20px; }

.chart-container { flex: 1; position: relative; padding: 30px; min-height: 450px; }
.real-chart { width: 100%; height: 100%; }

.stats-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
.stat-card { background: #f8fafc; border: 1px solid #eef2f6; border-radius: 10px; padding: 18px; text-align: center; transition: transform 0.2s; }
.stat-card:hover { transform: translateY(-2px); }
.stat-card.primary { border-top: 4px solid #3b82f6; }
.stat-card.success { border-top: 4px solid #10b981; }
.stat-card .label { font-size: 13px; color: #64748b; margin-bottom: 8px; }
.stat-card .value { font-size: 24px; font-weight: 800; color: #1e293b; }

.data-table { border-radius: 10px; overflow: hidden; border: 1px solid #eef2f6; }
.value-cell { display: flex; align-items: center; gap: 6px; position: relative; }
.initial-tag { flex-shrink: 0; font-size: 10px; padding: 0 4px; height: 18px; line-height: 18px; }
.round-text { font-size: 12px; color: #64748b; }

:deep(.initial-row) { background-color: #fef2f2 !important; }
:deep(.initial-row .el-table__cell) { border-bottom: 2px solid #ef4444 !important; }

.delete-eq-btn { position: absolute; bottom: 8px; right: 8px; }

/* 步骤附件样式 */
.step-attachments {
  border-top: 1px dashed #eef2f6;
  padding-top: 10px;
}
.attachment-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}
.file-tag {
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}
.file-tag:hover {
  opacity: 0.8;
  transform: translateY(-1px);
}
.file-preview-placeholder {
  padding: 40px;
  background: #f8fafc;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

/* 填写习惯优化 */
.step-format-tools {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-right: 15px;
  border-right: 1px solid #eef2f6;
  padding-right: 15px;
}
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  background: #f8fafc;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #eef2f6;
}
.purpose-section .template-btns {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
:deep(.el-textarea__inner) {
  line-height: 1.6;
  transition: all 0.2s;
}
</style>
