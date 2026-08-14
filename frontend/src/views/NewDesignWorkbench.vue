<template>
  <div class="whitebox-workbench">
    <header class="workbench-header">
      <div class="header-main">
        <el-button link class="back-btn" @click="goBackToModules">
          <el-icon><Back /></el-icon>
        </el-button>
        <div>
          <div class="header-eyebrow">DRUM ENGINEERING WORKSPACE</div>
          <div class="header-title">{{ workbenchTitle }}</div>
        </div>
      </div>

      <div class="header-meta">
        <el-tag effect="dark" type="primary">{{ currentTypeName }}</el-tag>

        <el-popover placement="bottom-start" :width="300" trigger="click">
          <template #reference>
            <el-tag type="success" effect="plain" class="cursor-pointer hover-tag">
              {{ currentVersionPath }} <el-icon class="ml-1"><ArrowDown /></el-icon>
            </el-tag>
          </template>
          <div class="popover-tree-container">
            <el-tree
              v-if="filteredScopeTree.length"
              :data="filteredScopeTree"
              node-key="id"
              default-expand-all
              highlight-current
              :current-node-key="currentTreeNodeKey"
              @node-click="handleScopeNodeClick"
            >
              <template #default="{ data }">
                <div class="scope-node" :class="`scope-node--${data.level}`">
                  <span>{{ data.label }}</span>
                  <el-tag v-if="data.level === 'version'" size="small" type="info" effect="plain">型号</el-tag>
                </div>
              </template>
            </el-tree>
            <el-empty v-else description="当前产品类型下暂无可用型号" />
          </div>
        </el-popover>

        <el-tag type="info" effect="plain">
          {{ activeModule?.moduleName || requestedModuleCode || '未选择模块' }}
        </el-tag>
        <span class="header-meta__stats">{{ moduleSummary.sceneCount }} 块 / {{ moduleSummary.formulaCount }} 式</span>
      </div>

      <div class="header-actions">
        <el-tooltip content="切换主工作区" placement="bottom">
          <el-button @click="cycleWorkspaceMode" size="small" circle><el-icon><Connection /></el-icon></el-button>
        </el-tooltip>
        <el-tooltip content="智能选型" placement="bottom">
          <el-button @click="smartSelectDrawerVisible = true" size="small" circle><el-icon><Cpu /></el-icon></el-button>
        </el-tooltip>
        <el-tooltip content="刷新数据" placement="bottom">
          <el-button plain :loading="loadingWorkbench" @click="loadWorkbench" size="small" circle><el-icon><Refresh /></el-icon></el-button>
        </el-tooltip>
        <el-tooltip content="计算链智能分析" placement="bottom">
          <el-button @click="openCalculationAnalysis" size="small" circle><el-icon><TrendCharts /></el-icon></el-button>
        </el-tooltip>
        <el-tooltip content="执行计算" placement="bottom">
          <el-button type="primary" :loading="executing" @click="handleRunCalculation" size="small" circle><el-icon><VideoPlay /></el-icon></el-button>
        </el-tooltip>
      </div>
    </header>

    <div class="workbench-body">
      <aside class="column column-left">
        <el-card class="panel-card panel-card--grow" shadow="never">
          <div class="panel-section-title">
            <span>参数导航</span>
            <small>{{ filteredModuleInputRows.length }} 项输入 / {{ filteredSelectionParameterRows.length }} 项选型</small>
          </div>
          <div style="margin-bottom: 12px;">
            <el-input
              v-model="parameterSearchKeyword"
              placeholder="搜索参数名称"
              clearable
              :prefix-icon="'Search'"
            />
          </div>
          <div v-if="parameterFeedback.message" class="parameter-feedback" :class="`is-${parameterFeedback.tone}`">
            {{ parameterFeedback.message }}
          </div>
          <div class="left-tree-stack">
            <div class="tree-section">
              <WorkbenchInputTable
                :rows="filteredModuleInputRows"
                :active-key="explanationTarget.type === 'parameter' ? explanationTarget.key : ''"
                title="输入参数树"
                tree-kind="input"
                :allow-group-rename="true"
                @change="handleInputChange"
                @update-name="handleInputNameChange"
                @update-unit="handleInputUnitChange"
                @blur="handleParameterBlur"
                @select="selectParameter"
                @add="handleAddParameter"
                @delete="handleDeleteParameter"
                @delete-group="handleDeleteParameterGroup"
                @rename-group="openRenameGroupDialog"
                @reclassify="openParameterGroupDialog"
              />
            </div>

            <div class="tree-section tree-section--selection">
              <WorkbenchInputTable
                :rows="filteredSelectionParameterRows"
                :active-key="explanationTarget.type === 'parameter' ? explanationTarget.key : ''"
                title="选型参数树"
                tree-kind="selection"
                :allow-add="false"
                empty-description="当前型号尚未完成选型，暂无选型参数"
                @select="selectParameter"
                @delete="handleDeleteParameter"
                @delete-group="handleDeleteParameterGroup"
              />
            </div>
          </div>
        </el-card>
      </aside>

      <main class="column column-center">
        <div class="design-status-strip">
          <div class="summary-grid">
            <el-card
              v-for="row in primaryResultRows"
              :key="row.paramName"
              class="summary-card"
              shadow="never"
              :class="{ 
                'is-active': explanationTarget.type === 'result' && explanationTarget.key === row.paramName,
                'has-warning': row.missingDependencies && row.missingDependencies.length > 0,
                'is-pass': (!row.missingDependencies || row.missingDependencies.length === 0) && row.verificationStatus === 'pass',
                'is-fail': (!row.missingDependencies || row.missingDependencies.length === 0) && row.verificationStatus === 'fail'
              }"
              @click="selectResult(row)"
            >
              <div class="summary-card__header">
                <div class="summary-card__label" style="display: flex; align-items: center;">
                  {{ row.displayName }}
                  <span
                    class="summary-card__status-dot"
                    :class="row.verificationStatus ? 'status-' + row.verificationStatus : 'status-unknown'"
                    :title="row.verificationStatus ? (row.verificationStatus === 'pass' ? '通过' : row.verificationStatus === 'fail' ? '未通过' : '未知') : '未评估'"
                  ></span>
                  <el-tooltip v-if="row.missingDependencies && row.missingDependencies.length > 0" :content="'缺少参数: ' + row.missingDependencies.join('、')" placement="top">
                    <el-icon color="#e6a23c" class="ml-1" style="cursor: help;"><WarningFilled /></el-icon>
                  </el-tooltip>
                </div>
                <el-button size="small" link type="primary" @click.stop="openFocusMetricConfig(row)">配置</el-button>
              </div>

              <div class="summary-card__metric-row">
                <div class="summary-card__metric-inline-label">输出值</div>
                <div class="summary-card__metric-value">{{ formatMetric(row.value, row.unitCode) }}</div>
              </div>
              <div class="summary-card__metric-row summary-card__metric-row--reference">
                <div class="summary-card__metric-inline-label">参考值</div>
                <div class="summary-card__reference-value">{{ resolvePrimaryMetricReference(row) }}</div>
              </div>
              <div v-if="row.ruleDescription" class="summary-card__rule">
                {{ row.ruleDescription }}
              </div>
              <div v-if="row.impactRanges && row.impactRanges.length" class="summary-card__impact-list">
                <div v-for="impact in getVisibleImpactRanges(row)" :key="impact.paramName" class="summary-card__impact-item">
                  <span class="summary-card__impact-name">{{ impact.displayName }}</span>
                  <strong class="summary-card__impact-range">{{ impact.rangeText }}</strong>
                </div>
                <div v-if="getHiddenImpactCount(row) > 0" class="summary-card__impact-more">
                  另有 {{ getHiddenImpactCount(row) }} 项影响参数区间
                </div>
              </div>
              <div v-else-if="row.impactRangesComputing" class="summary-card__impact-empty">
                影响参数区间计算中…
              </div>
              <div v-else-if="row.focusConfig.impactParams?.length" class="summary-card__impact-empty">
                暂无可用符合规则的影响参数区间
              </div>
            </el-card>

            <el-card v-if="!primaryResultRows.length" class="summary-card summary-card--empty" shadow="never">
              <div class="summary-card__label">暂无关注指标</div>
              <div class="summary-card__empty-note">在计算工作台把类型切到“关注指标”后显示</div>
            </el-card>
          </div>
        </div>

        <el-card class="panel-card panel-card--grow" shadow="never">
          <div v-if="calculationError" class="calc-alert">
            {{ calculationError }}
          </div>

          <div class="workspace-mode-bar">
            <el-radio-group v-model="workspaceMode" size="small">
              <el-radio-button value="list" label="list">计算工作台</el-radio-button>
              <el-radio-button value="flow" label="flow">计算流程图</el-radio-button>
              <el-radio-button value="model" label="model">设备模型预览</el-radio-button>
            </el-radio-group>
            <div class="workspace-mode-bar__meta">
              {{ moduleSummary.sceneCount }} 个计算块 · {{ moduleSummary.formulaCount }} 条公式
            </div>
          </div>

          <WorkbenchFormulaMainTable
            v-if="workspaceMode === 'list'"
            :rows="mainTableRows"
            :is-template-mode="true"
            :active-key="explanationTarget.type === 'formula' ? explanationTarget.key : ''"
            :editing-key="editingFormulaKey"
            :editing-field="editingFormulaField"
            :active-formula-draft="activeFormulaDraft"
            :editing-scene-code="editingSceneCode"
            :autocomplete-sections="autocompleteSections"
            :argument-hint="activeFormulaArgumentHint"
            :loading="formulaSaving"
            @select-row="handleFormulaSelect"
            @edit-formula="handleFormulaEdit"
            @open-explanation="handleOpenExplanation"
            @update-draft="handleFormulaDraftChange"
            @save-formula="handleFormulaSave"
            @cancel-edit="handleFormulaCancel"
            @blur-row="handleFormulaBlur"
            @selection-change="handleFormulaEditorSelectionChange"
            @delete-formula="handleFormulaDelete"
            @create-formula="handleFormulaCreate"
            @create-scene="handleSceneCreate(activeModule || modules[0])"
            @delete-scene="handleSceneDelete"
            @start-rename-scene="beginSceneEditing"
            @confirm-rename-scene="handleSceneRenameConfirm"
            @cancel-rename-scene="cancelSceneEditing"
            @metric-type-change="handleFormulaMetricTypeChange"
          />

          <div v-else-if="workspaceMode === 'flow'" class="workspace-flow-canvas">
            <WorkbenchCalculationFlowPanel
              :graph="activeFlowGraph"
              :selected-node-id="activeFlowNodeId"
              :viewport-state="flowViewportState"
              :display-mode="flowDisplayMode"
              :viewport-reset-token="flowViewportResetToken"
              @select-node="handleFlowNodeSelect"
              @drag-node="handleFlowNodeDrag"
              @viewport-change="handleFlowViewportChange"
            />
          </div>
          <div v-else-if="workspaceMode === 'model'" class="workspace-model-canvas">
            <div class="model-preview-head">
              <div>
                <strong>设备模型预览</strong>
                <span>型号与计算上下文联动</span>
              </div>
              <span class="model-preview-badge">3D / DRAWING</span>
            </div>
            <div class="model-preview-stage">
              <div class="drum-illustration" aria-label="滚筒设备模型示意">
                <div class="drum-shell"></div>
                <div class="drum-ring drum-ring--left"></div>
                <div class="drum-ring drum-ring--right"></div>
                <div class="drum-axis"></div>
                <div class="drum-motor"></div>
                <div class="drum-base"></div>
              </div>
              <div class="model-preview-hint">当前型号：{{ currentVersionPath }}</div>
            </div>
          </div>
        </el-card>
      </main>

      <aside class="column column-right">
        <el-card class="panel-card panel-card--grow" shadow="never">
          <div class="tree-section__title tree-section__title--right">
            <strong>设计说明</strong>
            <span>用于解释公式计算、输入参数与来源</span>
          </div>
          <div class="explanation-panel explanation-panel--compact">
            <div class="explanation-panel__head">
              <div class="explanation-panel__headline">
                <span class="explanation-panel__chip">{{ explanationPanel.categoryLabel || '说明面板' }}</span>
                <div class="explanation-panel__title">{{ explanationPanel.title }}</div>
              </div>
              <div class="explanation-panel__actions">
                <el-button v-if="!isExplanationEditing" type="primary" link size="small" @click="startExplanationEditing">
                  编辑
                </el-button>
                <template v-else>
                  <el-button type="primary" link size="small" @click="saveExplanationEditing">保存</el-button>
                  <el-button type="info" link size="small" @click="cancelExplanationEditing">取消</el-button>
                </template>
              </div>
            </div>

            <div v-if="!isExplanationEditing" class="explanation-overview">
              <div v-if="explanationPanel.summary" class="explanation-overview__summary">{{ explanationPanel.summary }}</div>
              <div v-else class="explanation-overview__summary is-empty">当前暂无补充说明。</div>

              <div v-if="explanationPanel.metaCards?.length" class="explanation-metrix">
                <div
                  v-for="(meta, index) in explanationPanel.metaCards"
                  :key="`${explanationPanel.title}-${meta.label}-${index}`"
                  class="explanation-metrix__item"
                  :class="{ 'is-primary': meta.tone === 'primary' }"
                >
                  <div class="explanation-metrix__label">{{ meta.label }}</div>
                  <div class="explanation-metrix__value">{{ String(meta.value ?? '').trim() || '-' }}</div>
                </div>
              </div>
            </div>

            <div v-if="isExplanationEditing" class="explanation-panel__edit-field">
              <div class="explanation-section__title">说明摘要</div>
              <el-input
                v-model="explanationEditForm.summary"
                type="textarea"
                :rows="3"
                placeholder="请输入说明文字..."
                style="margin-bottom: 12px;"
              />

              <div v-if="explanationTarget.type === 'parameter'" class="explanation-edit-section">
                <div class="explanation-section__title">参数来源</div>
                <el-select v-model="explanationEditForm.source_type" size="small" style="width: 160px; margin-bottom: 8px;">
                  <el-option label="人工录入" value="manual" />
                  <el-option label="经验取值" value="experience" />
                  <el-option label="标准/规范" value="standard" />
                  <el-option label="试验/实测" value="test" />
                  <el-option label="厂家资料" value="vendor" />
                  <el-option label="查表/计算" value="lookup" />
                </el-select>
                <el-input
                  v-model="explanationEditForm.source_note"
                  type="textarea"
                  :rows="3"
                  placeholder="填写参数来源、适用边界、取值依据，例如 摩擦系数取自厂家样本第 12 页。"
                />
              </div>
              
              <div v-if="explanationTarget.type === 'formula'" class="explanation-edit-section">
                <div class="explanation-section__title">参数输出标记</div>
                <el-radio-group v-model="explanationEditForm.output_flag" size="small">
                  <el-radio-button value="auto" label="auto">自动推断</el-radio-button>
                  <el-radio-button value="force_output" label="force_output">强制作为输出</el-radio-button>
                  <el-radio-button value="force_internal" label="force_internal">强制内部</el-radio-button>
                </el-radio-group>
              </div>
            </div>

            <div v-if="(explanationPanel.details.length || (explanationTarget.type === 'formula' && explanationPanel.output_flag)) && !isExplanationEditing" class="explanation-section">
              <div class="explanation-section__title"><span class="explanation-section__bar"></span>关键说明</div>
              <div class="explanation-section__body">
                <div v-for="(detail, index) in explanationPanel.details" :key="`${explanationPanel.title}-${index}`" class="explanation-line">
                  {{ detail }}
                </div>
                <div v-if="explanationTarget.type === 'formula'" class="explanation-line">
                  输出标记：{{ explanationPanel.output_flag === 'force_output' ? '强制作为输出' : explanationPanel.output_flag === 'force_internal' ? '强制内部使用' : '自动推断 (Auto)' }}
                </div>
              </div>
            </div>

            <div v-if="explanationTarget.type === 'parameter' && explanationPanel.sourceNote && !isExplanationEditing" class="explanation-section">
              <div class="explanation-section__title"><span class="explanation-section__bar"></span>参数溯源</div>
              <div class="explanation-section__body">
                <div class="explanation-line">
                  <span class="explanation-line__tag">来源</span>
                  {{ explanationPanel.sourceTypeLabel || '未标注' }}
                </div>
                <div class="explanation-line explanation-line--note">{{ explanationPanel.sourceNote }}</div>
              </div>
            </div>

            <div class="explanation-section" v-if="explanationPanel.resources.length || isExplanationEditing">
              <div class="explanation-section__title"><span class="explanation-section__bar"></span>{{ explanationTarget.type === 'parameter' ? '溯源资料' : '说明资源' }}</div>
              <div class="explanation-section__body">
                <div v-if="isExplanationEditing" class="resource-list">
                  <div
                    v-for="(resource, index) in explanationEditForm.resources"
                    :key="index"
                    class="resource-card edit-mode"
                  >
                  <el-select v-model="resource.type" style="width: 100px; margin-bottom: 8px;" size="small">
                    <el-option label="文字" value="text" />
                    <el-option label="图片" value="image" />
                    <el-option label="链接/文档" value="document" />
                    <el-option v-if="explanationTarget.type === 'formula'" label="校核规则" value="verification_rule" />
                  </el-select>
                  
                  <template v-if="resource.type === 'verification_rule'">
                    <el-select v-model="resource.targetParam" placeholder="选择校核参数" size="small" style="margin-bottom: 8px; width: 100%;" filterable>
                      <el-option v-for="row in allAvailableParameters" :key="row.paramName" :label="row.displayName" :value="row.paramName" />
                    </el-select>
                    <el-select v-model="resource.operator" placeholder="对比关系" size="small" style="margin-bottom: 8px; width: 100%;">
                      <el-option label="大于 (>)" value=">" />
                      <el-option label="小于 (<)" value="<" />
                      <el-option label="大于等于 (>=)" value=">=" />
                      <el-option label="小于等于 (<=)" value="<=" />
                      <el-option label="等于 (==)" value="==" />
                      <el-option label="区间 (between)" value="between" />
                    </el-select>
                    <el-input v-if="resource.operator === '=='" v-model="resource.tolerance" placeholder="允许误差" size="small" style="margin-bottom: 8px;" />
                    <div v-if="resource.operator === 'between'" style="display: flex; gap: 8px; margin-bottom: 8px;">
                      <el-input v-model="resource.rangeMin" placeholder="最小值" size="small" />
                      <el-input v-model="resource.rangeMax" placeholder="最大值" size="small" />
                    </div>
                  </template>
                  <template v-else>
                    <el-input v-model="resource.title" placeholder="资源名称" size="small" style="margin-bottom: 8px;" />
                    
                    <el-input v-if="resource.type === 'text'" type="textarea" :rows="3" v-model="resource.content" placeholder="请输入文字说明" size="small" style="margin-bottom: 8px;" />
                    <div v-else-if="resource.type === 'image'" style="margin-bottom: 8px;">
                      <el-upload
                        class="avatar-uploader"
                        action=""
                        :auto-upload="false"
                        :show-file-list="false"
                        :on-change="(file) => handleExplanationImageChange(file, index)"
                      >
                        <img v-if="resource.content" :src="resource.content" class="preview-img" style="max-width: 100%; max-height: 100px; border-radius: 4px;" />
                        <el-button v-else size="small">选择图片</el-button>
                      </el-upload>
                    </div>
                    <div v-else style="margin-bottom: 8px;">
                      <el-input v-model="resource.content" placeholder="资源地址或文件路径" size="small" style="margin-bottom: 8px;" />
                      <el-upload
                        action=""
                        :auto-upload="false"
                        :show-file-list="false"
                        :on-change="(file) => handleExplanationDocumentChange(file, index)"
                      >
                        <el-button size="small">上传文件</el-button>
                      </el-upload>
                    </div>
                  </template>
                  
                  <el-button type="danger" link @click="removeExplanationResource(index)" size="small">删除</el-button>
                </div>
                <el-button type="primary" plain size="small" @click="addExplanationResource">添加资源</el-button>
              </div>

              <div v-else class="resource-tiles">
                <div
                  v-for="(resource, idx) in explanationPanel.resources"
                  :key="`${resource.type}-${resource.title || idx}`"
                  class="resource-tile"
                  :class="`resource-tile--${resource.type}`"
                >
                  <div class="resource-tile__head">
                    <span class="resource-tile__chip">
                      {{ resource.type === 'image' ? '图片' : resource.type === 'text' ? '文字' : resource.type === 'verification_rule' ? '校核' : '文档' }}
                    </span>
                    <div class="resource-tile__title" v-if="resource.type !== 'verification_rule'">{{ resource.title || '未命名资源' }}</div>
                  </div>
                  <div class="resource-tile__body">
                      <template v-if="resource.type === 'verification_rule'">
                        <div class="resource-rule-row">
                          <span class="resource-rule-row__label">目标参数</span>
                          <el-tag size="small" type="info">{{ resource.targetParam }}</el-tag>
                        </div>
                        <div class="resource-rule-row">
                          <span class="resource-rule-row__label">规则</span>
                          <span class="resource-rule-row__value">
                            实际值 {{ resource.operator }} {{ resource.operator === 'between' ? `[${resource.rangeMin}, ${resource.rangeMax}]` : '理论值' }}
                          </span>
                        </div>
                      </template>
                      <img v-else-if="resource.type === 'image'" :src="resource.content" class="resource-tile__image" />
                      <p v-else-if="resource.type === 'text'" class="resource-tile__text">{{ resource.content }}</p>
                      <a v-else-if="isResourceLink(resource.content)" :href="resource.content" target="_blank" class="resource-tile__link">{{ resource.content }}</a>
                      <span v-else class="resource-tile__path">{{ resource.content }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </aside>
    </div>

    <el-drawer v-model="smartSelectDrawerVisible" title="智能选型配置" size="760px">
      <div class="selection-config-drawer">
        <div class="selection-config-shell">
          <div class="selection-config-toolbar">
            <div class="selection-config-toolbar__title">
              <div class="selection-config-toolbar__heading">选型配置表</div>
              <div class="selection-config-toolbar__meta">
                当前表：{{ selectionCategoryObject.label }}
                <span v-if="activeSelectionTableColumns.length">，可用列 {{ activeSelectionTableColumns.length }} 项</span>
              </div>
            </div>
            <div class="selection-config-toolbar__controls">
              <el-select v-model="activeSelectionCategoryCode" size="small" class="selection-config-toolbar__select" placeholder="选择选型表" @change="handleSelectionCategoryChange">
                <el-option v-for="cat in selectionCategoryList" :key="cat.code" :label="cat.label" :value="cat.code" />
              </el-select>
              <el-select v-model="selectedSelectionTableColumn" size="small" class="selection-config-toolbar__select" placeholder="添加表内参数" filterable>
                <el-option v-for="column in activeSelectionTableColumns" :key="column.key" :label="column.label" :value="column.key" />
              </el-select>
              <el-button size="small" :icon="Plus" @click="handleAddSelectionFieldFromColumn">添加</el-button>
              <el-button size="small" type="primary" @click="handleMappingChange">保存</el-button>
            </div>
          </div>

          <div class="selection-config-table-wrap">
            <div class="selection-config-table selection-config-table--editable">
              <div class="selection-config-table__head">
                <div class="selection-config-table__col-name">选型项</div>
                <div class="selection-config-table__col-mapping">映射</div>
                <div class="selection-config-table__col-priority">重要性</div>
                <div class="selection-config-table__col-compare">比较</div>
                <div class="selection-config-table__col-tolerance">范围 %</div>
                <div class="selection-config-table__col-hard">强制</div>
                <div class="selection-config-table__col-action">操作</div>
              </div>
              <div
                v-for="field in activeSelectionFields"
                :key="field.key"
                class="selection-config-table__row"
              >
                <div class="selection-config-table__cell selection-config-table__cell--name">
                  <el-input v-model="field.label" size="small" placeholder="选型项名称" clearable />
                </div>
                <div class="selection-config-table__cell selection-config-table__cell--mapping">
                  <div class="selection-config-mapping">
                    <el-select v-model="selectionMappings[activeSelectionCategoryCode][field.key].source_type" size="small" placeholder="来源类型">
                      <el-option label="参数" value="parameter" />
                      <el-option label="参考值" value="manual" />
                    </el-select>
                    <el-select
                      v-if="selectionMappings[activeSelectionCategoryCode][field.key].source_type === 'parameter'"
                      v-model="selectionMappings[activeSelectionCategoryCode][field.key].parameter_code"
                      size="small"
                      placeholder="选择参数"
                      clearable
                      filterable
                      class="selection-config-mapping__param"
                    >
                      <el-option-group v-for="group in ['输出', '结果', '中间', '输入']" :key="group" :label="group">
                        <el-option
                          v-for="param in selectionOnlyParameters.filter(p => p.group === group)"
                          :key="param.result_code"
                          :label="param.result_name"
                          :value="param.result_code"
                        />
                      </el-option-group>
                    </el-select>
                    <el-input
                      v-else-if="field.type === 'string'"
                      v-model="selectionMappings[activeSelectionCategoryCode][field.key].reference_value"
                      size="small"
                      placeholder="参考文本"
                      clearable
                      class="selection-config-mapping__param"
                    />
                    <el-input-number
                      v-else
                      v-model="selectionMappings[activeSelectionCategoryCode][field.key].reference_value"
                      size="small"
                      :controls="false"
                      placeholder="参考数值"
                      class="selection-config-mapping__param"
                    />
                  </div>
                </div>
                <div class="selection-config-table__cell selection-config-table__cell--priority">
                  <el-input-number v-model="field.priority" size="small" :min="1" :max="99" :step="1" :controls="false" />
                </div>
                <div class="selection-config-table__cell selection-config-table__cell--compare">
                  <el-select v-model="field.compare" size="small">
                    <el-option v-for="option in SELECTION_COMPARE_OPTIONS" :key="option.value" :label="option.label" :value="option.value" />
                  </el-select>
                </div>
                <div class="selection-config-table__cell selection-config-table__cell--tolerance">
                  <div class="selection-config-tolerance">
                    <el-input-number v-model="field.tolerance" size="small" :min="0" :max="100" :step="1" :controls="false" />
                    <span class="selection-config-tolerance__suffix">%</span>
                  </div>
                </div>
                <div class="selection-config-table__cell selection-config-table__cell--hard">
                  <el-checkbox v-model="field.hard_constraint" size="small" />
                </div>
                <div class="selection-config-table__cell selection-config-table__cell--action">
                  <div class="selection-config-actions">
                    <el-button size="small" link type="danger" @click="handleRemoveSelectionField(field.key)">删除</el-button>
                  </div>
                </div>
              </div>
              <div v-if="activeSelectionFields.length === 0" class="selection-config-table__empty">
                从上方「添加表内参数」选择要参与匹配的列，再配置映射和比较范围。
              </div>
            </div>
          </div>
        </div>
        <SmartSelectionPanel
          :selection-category="selectionCategoryObject"
          :field-schema="activeSelectionFields"
          :mapped-params="activeMappedSelectionParams"
          :mapping-configs="selectionMappings[activeSelectionCategoryCode] || {}"
          :current-equipment="currentEquipment"
          @apply-equipment="handleApplyEquipment"
          @clear-equipment="handleClearEquipment"
        />
      </div>
    </el-drawer>

    <el-dialog v-model="focusMetricDialogVisible" title="关注指标配置" width="520px">
      <el-form label-width="88px">
        <el-form-item label="指标名称">
          <el-input :model-value="focusMetricDraft.metricName" disabled />
        </el-form-item>
        <el-form-item label="校核方式">
          <el-radio-group v-model="focusMetricDraft.mode">
            <el-radio label="compare">参数对比</el-radio>
            <el-radio label="range">区间校核</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="影响参数">
          <el-select
            v-model="focusMetricDraft.impactParams"
            multiple
            filterable
            collapse-tags
            placeholder="选择需要反推区间的参数"
            style="width: 100%;"
          >
            <el-option
              v-for="option in focusMetricCompareOptions"
              :key="option.paramName"
              :label="option.displayName"
              :value="option.paramName"
            />
          </el-select>
          <div class="focus-metric-range-hint">选择后，系统按当前型号公式扫描该参数，反推出符合校核规则的最小值~最大值区间。</div>
        </el-form-item>
        <template v-if="focusMetricDraft.mode === 'compare'">
          <el-form-item label="对比参数">
            <el-select v-model="focusMetricDraft.targetParam" filterable placeholder="请选择对比参数" style="width: 100%;">
              <el-option
                v-for="option in focusMetricCompareOptions"
                :key="option.paramName"
                :label="option.displayName"
                :value="option.paramName"
              />
            </el-select>
            <div v-if="selectedParameterRange" class="focus-metric-range-hint">
              当前值区间：{{ selectedParameterRange.min }} ~ {{ selectedParameterRange.max }}
              <span class="focus-metric-range-count">（{{ selectedParameterRange.count }} 个型号）</span>
            </div>
          </el-form-item>
          <el-form-item label="关系">
            <el-select v-model="focusMetricDraft.operator" placeholder="请选择关系" style="width: 100%;">
              <el-option label="大于" value=">" />
              <el-option label="大于等于" value=">=" />
              <el-option label="小于" value="<" />
              <el-option label="小于等于" value="<=" />
              <el-option label="等于" value="==" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="focusMetricDraft.operator === '=='" label="允许误差">
            <el-input v-model="focusMetricDraft.tolerance" placeholder="例如 0.5" />
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="合理区间">
            <div class="focus-metric-range-fields">
              <el-input v-model="focusMetricDraft.rangeMin" placeholder="最小值" />
              <span class="focus-metric-range-separator">~</span>
              <el-input v-model="focusMetricDraft.rangeMax" placeholder="最大值" />
            </div>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="focusMetricDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="formulaSaving" @click="handleFocusMetricConfigSave">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="createSceneDialogVisible" title="新建计算块" width="400px">
      <el-form label-width="100px">
        <el-form-item label="场景名称">
          <el-input v-model="createSceneForm.sceneName" placeholder="未命名场景" />
        </el-form-item>
        <el-form-item label="场景类型">
          <el-radio-group v-model="createSceneForm.sceneType">
            <el-radio label="calc">普通计算</el-radio>
            <el-radio label="verify">校核对比</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createSceneDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmCreateScene" :loading="sceneSaving">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="parameterGroupDialogVisible" title="重新划分参数层级" width="420px">
      <el-form label-width="88px">
        <el-form-item label="参数名称">
          <el-input :model-value="parameterGroupDraft.displayName || parameterGroupDraft.paramName" disabled />
        </el-form-item>
        <el-form-item label="目标分组">
          <el-select v-model="parameterGroupDraft.targetGroupKey" placeholder="请选择目标分组" style="width: 100%;">
            <el-option
              v-for="option in PARAMETER_GROUP_OPTIONS"
              :key="option.key"
              :label="option.label"
              :value="option.key"
            />
            <el-option :value="CUSTOM_GROUP_TOKEN" label="＋ 新建分组" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="parameterGroupDraft.targetGroupKey === CUSTOM_GROUP_TOKEN" label="分组名称">
          <el-input
            v-model="parameterGroupDraft.customGroupLabel"
            placeholder="输入新的分组名称，如：滚筒粘料计算"
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="parameterGroupDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleParameterGroupSave">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="renameGroupDialogVisible" title="重命名参数分组" width="420px">
      <el-form label-width="88px">
        <el-form-item label="原分组名">
          <el-input :model-value="renameGroupDraft.oldLabel" disabled />
        </el-form-item>
        <el-form-item label="新分组名">
          <el-input
            v-model="renameGroupDraft.newLabel"
            placeholder="输入新的分组名称，如：滚筒粘料计算"
            clearable
            @keyup.enter="handleRenameGroupSave"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="renameGroupDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleRenameGroupSave">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <AnalysisWorkbench
      v-model:visible="analysisDialogVisible"
      :model-id="selectedVersionId"
      :module-code="requestedModuleCode"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowDown, Back, Connection, Cpu, Refresh, VideoPlay, DataLine, WarningFilled, CircleCheckFilled, InfoFilled, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from 'axios'

import WorkbenchInputTable from '@/components/WorkbenchInputTable.vue'
import WorkbenchFormulaMainTable from '@/components/WorkbenchFormulaMainTable.vue'
import WorkbenchCalculationFlowPanel from '@/components/WorkbenchCalculationFlowPanel.vue'
import SmartSelectionPanel from '@/components/SmartSelectionPanel.vue'
import AnalysisWorkbench from '@/components/CalculationAnalysis/AnalysisWorkbench.vue'
import { fetchEquipmentCategories, fetchEquipmentItems, fetchMotorCatalogItems } from '@/api/equipmentCatalog'

import { fetchFamilyMatrix, fetchLatestWorkbenchSnapshot, fetchParameterLookups, saveWorkbenchParameters, deleteParameterDefinition, fetchSelectionMappings, saveSelectionMappings, fetchFocusMetricConfigs, saveFocusMetricConfigs } from '@/api/designPlatform'
import { mergeWorkbenchModelRows } from '@/api/designPlatform.helpers.mjs'
import { fetchDrumTree, fetchModelWorkbenchInstance, saveWorkbenchFormula, deleteWorkbenchFormula, createWorkbenchFormulaScene, renameWorkbenchFormulaScene, deleteWorkbenchFormulaScene, analyzeVerificationScan } from '@/api/drumDesign'
import {
  buildExecutionIntermediateRows,
  buildModuleSummary,
  buildWorkbenchParameterRows,
  buildWorkbenchCalculationFlow,
  buildFormulaAutocompleteSections,
  resolveFormulaAutocompleteKeyword,
  resolveFormulaArgumentHint,
  resolveFormulaVariablesFromExpression,
  resolveParameterInsertionDraft,
  extractFormulaParameterRows,
  splitFormulaParameterRows
} from '@/api/drumDesign.helpers.mjs'
import { buildLookupSourceRows } from '@/api/drumDesignLookup.helpers.mjs'
import { ALL_RESERVED_IDENTIFIERS, evaluateFormulaExpression } from '@/utils/formulaEngine.mjs'
import { resolveWorkbenchTreeGroup } from '@/views/newDesignWorkbenchTreeGrouping.mjs'
import {
  createPendingParameterRow,
  findParameterRowIndex,
  removeParameterRow,
  resolveParameterDisplayName,
  shouldPersistParameterRow
} from '@/views/newDesignWorkbenchParameterDrafts.mjs'

const route = useRoute()
const router = useRouter()

const getEquipmentRowsStorageKey = (versionId) => `workbench_equipment_${String(versionId || '').trim()}_${String(activeModuleCode.value || '').trim()}`
const getCurrentEquipmentStorageKey = (versionId) => `new_workbench_current_equipment_${String(versionId || '').trim()}_${String(activeModuleCode.value || '').trim()}`
const DEFAULT_PARAMETER_FEEDBACK = ''

const treeData = ref([])
const selectedTypeId = ref('')
const selectedFamilyId = ref('')
const selectedVersionId = ref('')
const requestedModuleCode = ref('')
const activeModuleCode = ref('')
const rawMatrixData = ref(null)
const modules = ref([])
const parameterRows = ref([])
const latestResults = ref([])
const latestScope = ref({})
const parameterFeedback = ref({ tone: 'info', message: DEFAULT_PARAMETER_FEEDBACK })
const SELECTION_CATEGORY_PRESETS = {
  gearmotor: {
    label: '减速电机选型表',
    default_fields: [
      { key: 'power', label: '所需功率 (kW)', type: 'numeric', compare: 'ge', source_spec: 'power_kw', weight: 0.40, priority: 1 },
      { key: 'speed', label: '输出转速 (rpm)', type: 'numeric', compare: 'near', source_spec: 'speed_rpm', weight: 0.30, tolerance: 12, priority: 2 },
      { key: 'torque', label: '所需扭矩 (Nm)', type: 'numeric', compare: 'ge', source_spec: 'torque_nm', weight: 0.20, priority: 3 },
      { key: 'fb', label: '服务系数', type: 'numeric', compare: 'ge', source_spec: 'service_factor', weight: 0.10, priority: 4 }
    ]
  },
  motor: {
    label: '电动机选型表',
    default_fields: [
      { key: 'power', label: '额定功率 (kW)', type: 'numeric', compare: 'ge', source_spec: 'power_kw', weight: 0.45, priority: 1 },
      { key: 'speed', label: '额定转速 (rpm)', type: 'numeric', compare: 'near', source_spec: 'motor_speed_rpm', weight: 0.35, tolerance: 8, priority: 2 },
      { key: 'voltage', label: '额定电压', type: 'string', compare: 'eq', source_spec: 'voltage', weight: 0.10, priority: 3 },
      { key: 'protection', label: '防护等级', type: 'string', compare: 'eq', source_spec: 'protection', weight: 0.10, priority: 4 }
    ]
  },
  reducer: {
    label: '减速机选型表',
    default_fields: [
      { key: 'ratio', label: '减速比', type: 'numeric', compare: 'near', source_spec: 'ratio', weight: 0.35, tolerance: 10, priority: 1 },
      { key: 'torque', label: '输出扭矩 (Nm)', type: 'numeric', compare: 'ge', source_spec: 'torque_nm', weight: 0.35, priority: 2 },
      { key: 'speed', label: '输出转速 (rpm)', type: 'numeric', compare: 'near', source_spec: 'speed_rpm', weight: 0.20, tolerance: 10, priority: 3 },
      { key: 'service_factor', label: '服务系数', type: 'numeric', compare: 'ge', source_spec: 'service_factor', weight: 0.10, priority: 4 }
    ]
  },
  bearing: {
    label: '轴承选型表',
    default_fields: [
      { key: 'inner_diameter', label: '内径 (mm)', type: 'numeric', compare: 'near', source_spec: 'inner_diameter_mm', weight: 0.30, tolerance: 5, priority: 1 },
      { key: 'outer_diameter', label: '外径 (mm)', type: 'numeric', compare: 'near', source_spec: 'outer_diameter_mm', weight: 0.30, tolerance: 5, priority: 2 },
      { key: 'width', label: '宽度 (mm)', type: 'numeric', compare: 'near', source_spec: 'width_mm', weight: 0.20, tolerance: 5, priority: 3 },
      { key: 'dynamic_load', label: '动载荷 (kN)', type: 'numeric', compare: 'ge', source_spec: 'dynamic_load_kn', weight: 0.20, priority: 4 }
    ]
  },
  fan: {
    label: '风机选型表',
    default_fields: [
      { key: 'airflow', label: '风量 (m³/h)', type: 'numeric', compare: 'ge', source_spec: 'airflow_m3h', weight: 0.35, priority: 1 },
      { key: 'pressure', label: '风压 (Pa)', type: 'numeric', compare: 'ge', source_spec: 'pressure_pa', weight: 0.30, priority: 2 },
      { key: 'power', label: '电机功率 (kW)', type: 'numeric', compare: 'near', source_spec: 'power_kw', weight: 0.20, tolerance: 15, priority: 3 },
      { key: 'noise', label: '噪音 (dB(A))', type: 'numeric', compare: 'le', source_spec: 'noise_dba', weight: 0.15, priority: 4 }
    ]
  }
}
const selectionCategoryList = computed(() => [
  ...Object.entries(SELECTION_CATEGORY_PRESETS).map(([code, preset]) => ({ code, label: preset.label, preset: true })),
  { code: 'custom', label: '自定义选型表', preset: false }
])
const SELECTION_COMPARE_OPTIONS = [
  { value: 'ge', label: '不小于' },
  { value: 'le', label: '不大于' },
  { value: 'near', label: '近似匹配' },
  { value: 'eq', label: '精确匹配' }
]
const activeSelectionCategoryCode = ref('gearmotor')
const selectionFieldConfigs = ref({})
const selectionMappings = ref({})
const selectionTableColumnsByCategory = ref({})
const selectedSelectionTableColumn = ref('')
const createEmptySelectionMapping = (fieldType = 'numeric') => ({
  source_type: 'parameter',
  parameter_code: '',
  reference_value: fieldType === 'string' ? '' : ''
})
const normalizeSelectionMappingEntry = (entry, fieldType = 'numeric') => {
  if (typeof entry === 'string') {
    return {
      source_type: 'parameter',
      parameter_code: String(entry || '').trim(),
      reference_value: fieldType === 'string' ? '' : ''
    }
  }
  if (!entry || typeof entry !== 'object') {
    return createEmptySelectionMapping(fieldType)
  }

  const sourceType = String(entry.source_type || entry.sourceType || '').trim() === 'manual' ? 'manual' : 'parameter'
  const parameterCode = String(entry.parameter_code ?? entry.parameterCode ?? entry.source_parameter ?? '').trim()
  const rawReferenceValue = entry.reference_value ?? entry.referenceValue ?? entry.manual_value ?? ''

  let referenceValue = ''
  if (fieldType === 'string') {
    referenceValue = String(rawReferenceValue ?? '').trim()
  } else if (rawReferenceValue !== '' && rawReferenceValue !== null && rawReferenceValue !== undefined) {
    const numericReference = Number(rawReferenceValue)
    referenceValue = Number.isFinite(numericReference) ? numericReference : ''
  }

  return {
    source_type: sourceType,
    parameter_code: parameterCode,
    reference_value: referenceValue
  }
}
const hasSelectionMappingValue = (entry) => {
  if (typeof entry === 'string') return Boolean(String(entry || '').trim())
  if (!entry || typeof entry !== 'object') return false
  const sourceType = String(entry.source_type || entry.sourceType || '').trim() === 'manual' ? 'manual' : 'parameter'
  if (sourceType === 'manual') {
    return String(entry.reference_value ?? entry.referenceValue ?? entry.manual_value ?? '').trim() !== ''
  }
  return Boolean(String(entry.parameter_code ?? entry.parameterCode ?? entry.source_parameter ?? '').trim())
}
const mergeSelectionMappingsState = (localMappings = {}, remoteMappings = {}) => {
  const merged = {}
  const categoryKeys = new Set([
    ...Object.keys(remoteMappings || {}),
    ...Object.keys(localMappings || {})
  ])
  categoryKeys.forEach((categoryCode) => {
    const localCategory = localMappings?.[categoryCode] || {}
    const remoteCategory = remoteMappings?.[categoryCode] || {}
    const nextCategory = {}
    const fieldKeys = new Set([
      ...Object.keys(remoteCategory || {}),
      ...Object.keys(localCategory || {})
    ])
    fieldKeys.forEach((fieldKey) => {
      const localEntry = localCategory?.[fieldKey]
      const remoteEntry = remoteCategory?.[fieldKey]
      if (hasSelectionMappingValue(localEntry) || remoteEntry === undefined) {
        nextCategory[fieldKey] = localEntry
      } else {
        nextCategory[fieldKey] = remoteEntry
      }
    })
    merged[categoryCode] = nextCategory
  })
  return merged
}
const normalizeSelectionFieldPriority = (field, index = 0) => {
  const rawPriority = Number(field?.priority)
  if (Number.isFinite(rawPriority) && rawPriority > 0) {
    return Math.min(99, Math.max(1, Math.round(rawPriority)))
  }
  return index + 1
}
const normalizeSelectionField = (field, index = 0) => {
  const nextField = { ...(field || {}) }
  const rawTol = Number(nextField.tolerance)
  if (Number.isFinite(rawTol) && rawTol > 0 && rawTol < 1) {
    nextField.tolerance = Math.round(rawTol * 100)
  } else if (!Number.isFinite(rawTol) || rawTol < 0) {
    nextField.tolerance = 10
  } else {
    nextField.tolerance = Math.max(0, Math.min(100, Math.round(rawTol)))
  }
  if (nextField.hard_constraint === undefined || nextField.hard_constraint === null) {
    nextField.hard_constraint = false
  }
  if (!nextField.type) nextField.type = 'numeric'
  if (!nextField.compare) nextField.compare = 'near'
  if (!nextField.weight) nextField.weight = 0.10
  nextField.priority = normalizeSelectionFieldPriority(nextField, index)
  return nextField
}
const ensureSelectionCategoryStructure = (categoryCode) => {
  const normalizedCategoryCode = String(categoryCode || '').trim() || 'gearmotor'
  if (!selectionMappings.value[normalizedCategoryCode] || typeof selectionMappings.value[normalizedCategoryCode] !== 'object') {
    selectionMappings.value[normalizedCategoryCode] = {}
  }
  if (!Array.isArray(selectionFieldConfigs.value[normalizedCategoryCode])) {
    const presetFields = SELECTION_CATEGORY_PRESETS[normalizedCategoryCode]?.default_fields || []
    selectionFieldConfigs.value[normalizedCategoryCode] = presetFields.map((field, index) => normalizeSelectionField(field, index))
  } else {
    selectionFieldConfigs.value[normalizedCategoryCode] = selectionFieldConfigs.value[normalizedCategoryCode].map((field, index) => normalizeSelectionField(field, index))
  }
  const fieldTypeMap = new Map(
    (selectionFieldConfigs.value[normalizedCategoryCode] || [])
      .map((field) => [String(field?.key || '').trim(), String(field?.type || 'numeric').trim() || 'numeric'])
      .filter(([key]) => Boolean(key))
  )
  const normalizedMappings = {}
  Object.entries(selectionMappings.value[normalizedCategoryCode] || {}).forEach(([fieldKey, entry]) => {
    const normalizedFieldKey = String(fieldKey || '').trim()
    if (!normalizedFieldKey) return
    normalizedMappings[normalizedFieldKey] = normalizeSelectionMappingEntry(entry, fieldTypeMap.get(normalizedFieldKey) || 'numeric')
  })
  ;(selectionFieldConfigs.value[normalizedCategoryCode] || []).forEach((field) => {
    const fieldKey = String(field?.key || '').trim()
    if (!fieldKey) return
    if (!normalizedMappings[fieldKey]) {
      normalizedMappings[fieldKey] = createEmptySelectionMapping(String(field?.type || 'numeric').trim() || 'numeric')
    }
  })
  selectionMappings.value[normalizedCategoryCode] = normalizedMappings
}
const availableEquipmentCategories = ref([])
const loadEquipmentCategoriesIfNeeded = async () => {
  if (availableEquipmentCategories.value.length) return
  try {
    availableEquipmentCategories.value = await fetchEquipmentCategories()
  } catch (error) {
    console.error('加载设备分类失败:', error)
    availableEquipmentCategories.value = []
  }
}
const selectionCategoryLookup = computed(() => {
  const map = new Map()
  availableEquipmentCategories.value.forEach((category) => {
    const code = String(category.code || '').trim()
    if (code) {
      map.set(code.toLowerCase(), category)
    }
  })
  return map
})
const selectionCategoryObject = computed(() => {
  const normalizedCategoryCode = String(activeSelectionCategoryCode.value || '').trim() || 'gearmotor'
  const category = selectionCategoryLookup.value.get(normalizedCategoryCode.toLowerCase()) || null
  return {
    code: normalizedCategoryCode,
    label: SELECTION_CATEGORY_PRESETS[normalizedCategoryCode]?.label || category?.name || normalizedCategoryCode,
    categoryId: category ? Number(category.id || 0) : null
  }
})
const activeSelectionFields = computed(() => {
  const normalizedCategoryCode = String(activeSelectionCategoryCode.value || '').trim() || 'gearmotor'
  ensureSelectionCategoryStructure(normalizedCategoryCode)
  return [...(selectionFieldConfigs.value[normalizedCategoryCode] || [])].sort((left, right) => {
    const leftPriority = normalizeSelectionFieldPriority(left, 0)
    const rightPriority = normalizeSelectionFieldPriority(right, 0)
    if (leftPriority !== rightPriority) return leftPriority - rightPriority
    return String(left?.label || left?.key || '').localeCompare(String(right?.label || right?.key || ''), 'zh-CN')
  })
})
const SELECTION_COLUMN_LABEL_MAP = {
  model_name: '型号名称',
  brand: '品牌',
  power: '功率',
  power_kw: '额定功率 (kW)',
  output_power_kw: '输出功率 (kW)',
  required_power_kw: '所需功率 (kW)',
  motor_power: '电机功率',
  motor_power_kw: '电机功率 (kW)',
  speed: '转速',
  speed_rpm: '输出转速 (rpm)',
  output_speed_rpm: '输出转速 (rpm)',
  motor_speed: '电机转速',
  motor_speed_rpm: '电机额定转速 (rpm)',
  input_speed_rpm: '输入转速 (rpm)',
  torque: '扭矩',
  torque_nm: '输出扭矩 (Nm)',
  output_torque_nm: '输出扭矩 (Nm)',
  rated_torque_nm: '额定扭矩 (Nm)',
  fb: '服务系数',
  service_factor: '服务系数',
  ratio: '减速比',
  gearbox_ratio: '减速比',
  reduction_ratio: '减速比',
  voltage: '额定电压',
  rated_voltage: '额定电压',
  current: '额定电流 (A)',
  rated_current_a: '额定电流 (A)',
  frequency: '频率 (Hz)',
  frequency_hz: '频率 (Hz)',
  protection: '防护等级',
  protection_class: '防护等级',
  ip_class: '防护等级',
  insulation_class: '绝缘等级',
  mounting: '安装方式',
  mounting_type: '安装方式',
  series: '系列',
  sub_series: '子系列',
  frame: '机座号',
  frame_size: '机座号',
  pole: '极数',
  poles: '极数',
  bearing_type: '轴承类型',
  inner_diameter: '内径',
  inner_diameter_mm: '内径 (mm)',
  bore_diameter_mm: '孔径 (mm)',
  outer_diameter: '外径',
  outer_diameter_mm: '外径 (mm)',
  od_mm: '外径 (mm)',
  width: '宽度',
  width_mm: '宽度 (mm)',
  thickness_mm: '厚度 (mm)',
  length_mm: '长度 (mm)',
  height_mm: '高度 (mm)',
  weight_kg: '重量 (kg)',
  mass_kg: '质量 (kg)',
  dynamic_load: '动载荷',
  dynamic_load_kn: '动载荷 (kN)',
  static_load: '静载荷',
  static_load_kn: '静载荷 (kN)',
  rated_load_kn: '额定载荷 (kN)',
  limiting_speed_rpm: '极限转速 (rpm)',
  airflow: '风量',
  airflow_m3h: '风量 (m³/h)',
  flow_rate_m3h: '流量 (m³/h)',
  pressure: '风压',
  pressure_pa: '风压 (Pa)',
  static_pressure_pa: '静压 (Pa)',
  total_pressure_pa: '全压 (Pa)',
  noise: '噪音',
  noise_dba: '噪音 (dB(A))',
  sound_level_dba: '声压级 (dB(A))',
  efficiency: '效率 (%)',
  efficiency_percent: '效率 (%)',
  power_factor: '功率因数',
  slip: '转差率 (%)',
  slip_percent: '转差率 (%)',
  duty: '工作制',
  duty_type: '工作制',
  ambient_temp_c: '环境温度 (℃)',
  max_temp_c: '最高温度 (℃)',
  material: '材质',
  lubrication: '润滑方式',
  seal_type: '密封形式',
  connection: '接线方式',
  connection_type: '接线方式',
  gearbox: '减速机型号',
  reducer_model: '减速机型号',
  motor_model: '电机型号',
  certification: '认证',
  standard: '执行标准',
  remark: '备注',
  description: '说明'
}
const SELECTION_COLUMN_UNIT_HINT = [
  { suffix: '_kw', unit: ' (kW)' },
  { suffix: '_kwp', unit: ' (kWp)' },
  { suffix: '_rpm', unit: ' (rpm)' },
  { suffix: '_nm', unit: ' (Nm)' },
  { suffix: '_kn', unit: ' (kN)' },
  { suffix: '_mm', unit: ' (mm)' },
  { suffix: '_cm', unit: ' (cm)' },
  { suffix: '_m', unit: ' (m)' },
  { suffix: '_m2', unit: ' (m²)' },
  { suffix: '_m3', unit: ' (m³)' },
  { suffix: '_m3h', unit: ' (m³/h)' },
  { suffix: '_pa', unit: ' (Pa)' },
  { suffix: '_kpa', unit: ' (kPa)' },
  { suffix: '_bar', unit: ' (bar)' },
  { suffix: '_dba', unit: ' (dB(A))' },
  { suffix: '_db', unit: ' (dB)' },
  { suffix: '_c', unit: ' (℃)' },
  { suffix: '_kg', unit: ' (kg)' },
  { suffix: '_t', unit: ' (t)' },
  { suffix: '_hr', unit: ' (h)' },
  { suffix: '_hz', unit: ' (Hz)' },
  { suffix: '_a', unit: ' (A)' },
  { suffix: '_ma', unit: ' (mA)' },
  { suffix: '_v', unit: ' (V)' },
  { suffix: '_kv', unit: ' (kV)' },
  { suffix: '_percent', unit: ' (%)' },
  { suffix: '_ratio', unit: '' }
]
const prettifySelectionColumnLabel = (columnKey) => {
  const normalizedKey = String(columnKey || '').trim().toLowerCase()
  if (!normalizedKey) return ''

  if (SELECTION_COLUMN_LABEL_MAP[normalizedKey]) {
    return SELECTION_COLUMN_LABEL_MAP[normalizedKey]
  }
  if (SELECTION_COLUMN_LABEL_MAP[columnKey]) {
    return SELECTION_COLUMN_LABEL_MAP[columnKey]
  }

  const cleanKey = String(columnKey || '').trim()
  const segments = cleanKey.split(/[_\s]+/).filter(Boolean)
  const unitSuffix = SELECTION_COLUMN_UNIT_HINT.find((hint) => normalizedKey.endsWith(hint.suffix))?.unit || ''

  const zhFragments = segments.map((segment) => {
    const segLower = segment.toLowerCase()
    if (SELECTION_COLUMN_LABEL_MAP[segLower]) return SELECTION_COLUMN_LABEL_MAP[segLower]
    if (SELECTION_COLUMN_LABEL_MAP[segment]) return SELECTION_COLUMN_LABEL_MAP[segment]
    return segment.charAt(0).toUpperCase() + segment.slice(1).toLowerCase()
  })

  const rawJoined = zhFragments.filter((frag, idx, arr) => arr.indexOf(frag) === idx).join('')
  if (!unitSuffix || rawJoined.endsWith(unitSuffix) || rawJoined.endsWith(unitSuffix.replace(/ /g, ''))) {
    return rawJoined || cleanKey
  }
  return `${rawJoined}${unitSuffix}`
}
const activeSelectionTableColumns = computed(() => {
  const normalizedCategoryCode = String(activeSelectionCategoryCode.value || '').trim() || 'gearmotor'
  return selectionTableColumnsByCategory.value[normalizedCategoryCode] || []
})
const activeSelectionTableColumnLabelMap = computed(() => {
  const map = new Map()
  activeSelectionTableColumns.value.forEach((column) => {
    const key = String(column?.key || '').trim()
    if (!key) return
    map.set(key, String(column?.label || key).trim())
  })
  return map
})
const outputParameters = computed(() => {
  return latestResults.value.filter(r => r.is_output === true || r.output_flag === 'force_output')
})
const allMappableParameters = computed(() => {
  const params = new Map()
  const seen = new Set()

  latestResults.value.forEach((r) => {
    const code = String(r.result_code || '').trim()
    if (!code || seen.has(code)) return
    seen.add(code)
    const isOutput = r.is_output === true || r.output_flag === 'force_output'
    params.set(code, {
      result_code: code,
      result_name: r.result_name || code,
      group: isOutput ? '输出' : '结果',
      isOutput
    })
  })

  moduleExecutionRows.value.forEach((row) => {
    const code = String(row.paramName || '').trim()
    if (!code || seen.has(code)) return
    seen.add(code)
    params.set(code, {
      result_code: code,
      result_name: row.displayName || code,
      group: '中间',
      isOutput: false
    })
  })

  parameterRows.value.forEach((row) => {
    const code = String(row.paramName || '').trim()
    if (!code || seen.has(code)) return
    if (row.valueType === 'equipment' || code.startsWith('电机_') || code.startsWith('减速机_')) return
    seen.add(code)
    params.set(code, {
      result_code: code,
      result_name: row.displayName || code,
      group: '输入',
      isOutput: false
    })
  })

  return Array.from(params.values()).sort((a, b) => {
    const order = { '输出': 0, '结果': 1, '中间': 2, '输入': 3 }
    const ga = order[a.group] ?? 9
    const gb = order[b.group] ?? 9
    if (ga !== gb) return ga - gb
    return String(a.result_name || '').localeCompare(String(b.result_name || ''), 'zh-CN')
  })
})

const selectionOnlyParameters = computed(() => {
  const fullList = allMappableParameters.value
  const selectionCodes = new Set(selectionParamConfigMap.value.keys())
  if (selectionCodes.size === 0) return fullList
  return fullList.filter((param) => selectionCodes.has(String(param.result_code || '').trim()))
})
const readOutputParameterValue = (parameterCode) => {
  const normalizedParameterCode = String(parameterCode || '').trim()
  if (!normalizedParameterCode) return null
  const resultObj = latestResults.value.find(r => String(r.result_code || '').trim() === normalizedParameterCode)
  if (resultObj) {
    const numericValue = Number(resultObj.result_value)
    if (!Number.isNaN(numericValue)) return numericValue
    const trimmedString = String(resultObj.result_value || '').trim()
    return trimmedString || ''
  }
  if (Object.prototype.hasOwnProperty.call(latestScope.value, normalizedParameterCode)) {
    const numericValue = Number(latestScope.value[normalizedParameterCode])
    if (!Number.isNaN(numericValue)) return numericValue
    const trimmedString = String(latestScope.value[normalizedParameterCode] || '').trim()
    return trimmedString || ''
  }
  const parameterRow = parameterRows.value.find(row => String(row.paramName || '').trim() === normalizedParameterCode)
  if (parameterRow) {
    const numericValue = Number(parameterRow.value)
    if (!Number.isNaN(numericValue)) return numericValue
    const trimmedString = String(parameterRow.value || '').trim()
    return trimmedString || ''
  }
  return null
}
const activeMappedSelectionParams = computed(() => {
  const normalizedCategoryCode = String(activeSelectionCategoryCode.value || '').trim() || 'gearmotor'
  ensureSelectionCategoryStructure(normalizedCategoryCode)
  const categoryMappings = selectionMappings.value[normalizedCategoryCode] || {}
  const params = {}
  activeSelectionFields.value.forEach((field) => {
    const mappingEntry = normalizeSelectionMappingEntry(categoryMappings[field.key], field.type)
    const rawValue = mappingEntry.source_type === 'manual'
      ? (String(field?.type || 'numeric').trim() === 'string'
        ? String(mappingEntry.reference_value ?? '').trim()
        : Number.isFinite(Number(mappingEntry.reference_value)) ? Number(mappingEntry.reference_value) : null)
      : (mappingEntry.parameter_code ? readOutputParameterValue(mappingEntry.parameter_code) : null)
    if (rawValue === null || rawValue === '') {
      params[field.key] = field.type === 'numeric' ? 0 : ''
    } else {
      params[field.key] = rawValue
    }
  })
  return params
})
const getSelectionConfigStorageKey = (versionId) => `workbench_selection_field_configs_${versionId || 'default'}`
const getSelectionMappingStorageKey = (versionId) => `workbench_selection_mapping_configs_${versionId || 'default'}`
const loadStoredSelectionFieldConfigs = (versionId) => {
  try {
    const raw = localStorage.getItem(getSelectionConfigStorageKey(versionId))
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return {}
    const normalized = {}
    Object.entries(parsed).forEach(([categoryCode, fields]) => {
      if (!Array.isArray(fields)) return
      normalized[categoryCode] = fields.map((field, index) => normalizeSelectionField(field, index))
    })
    return normalized
  } catch (error) {
    console.error('读取本地选型配置失败:', error)
    return {}
  }
}
const loadStoredSelectionMappings = (versionId) => {
  try {
    const raw = localStorage.getItem(getSelectionMappingStorageKey(versionId))
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch (error) {
    console.error('读取本地选型映射失败:', error)
    return {}
  }
}
const persistSelectionFieldConfigs = () => {
  if (!selectedVersionId.value) return
  try {
    localStorage.setItem(
      getSelectionConfigStorageKey(selectedVersionId.value),
      JSON.stringify(selectionFieldConfigs.value || {})
    )
  } catch (error) {
    console.error('保存本地选型配置失败:', error)
  }
}
const persistSelectionMappings = () => {
  if (!selectedVersionId.value) return
  try {
    localStorage.setItem(
      getSelectionMappingStorageKey(selectedVersionId.value),
      JSON.stringify(selectionMappings.value || {})
    )
  } catch (error) {
    console.error('保存本地选型映射失败:', error)
  }
}
const syncSelectionFieldConfigsFromMappings = (categoryCode) => {
  const normalizedCategoryCode = String(categoryCode || '').trim() || 'gearmotor'
  ensureSelectionCategoryStructure(normalizedCategoryCode)
  const existingFields = selectionFieldConfigs.value[normalizedCategoryCode] || []
  const existingFieldMap = new Map(
    existingFields.map((field) => [String(field?.key || '').trim(), field]).filter(([key]) => Boolean(key))
  )
  Object.keys(selectionMappings.value[normalizedCategoryCode] || {}).forEach((fieldKey) => {
    const normalizedFieldKey = String(fieldKey || '').trim()
    if (!normalizedFieldKey || existingFieldMap.has(normalizedFieldKey)) return
    selectionFieldConfigs.value[normalizedCategoryCode].push({
      key: normalizedFieldKey,
      label: activeSelectionTableColumnLabelMap.value.get(normalizedFieldKey) || prettifySelectionColumnLabel(normalizedFieldKey),
      type: 'numeric',
      compare: 'near',
      source_spec: normalizedFieldKey,
      weight: 0.10,
      priority: (selectionFieldConfigs.value[normalizedCategoryCode] || []).length + 1,
      tolerance: 10,
      hard_constraint: false
    })
  })
}
const loadSelectionTableColumns = async (categoryCode) => {
  const normalizedCategoryCode = String(categoryCode || '').trim() || 'gearmotor'
  if (Array.isArray(selectionTableColumnsByCategory.value[normalizedCategoryCode])) return

  await loadEquipmentCategoriesIfNeeded()
  const category = selectionCategoryLookup.value.get(normalizedCategoryCode.toLowerCase()) || null
  const categoryId = Number(category?.id || 0)
  if (!categoryId) {
    selectionTableColumnsByCategory.value[normalizedCategoryCode] = []
    return
  }

  try {
    const rows = await fetchEquipmentItems({ categoryId })
    const systemColumns = [
      { key: 'model_name', label: '型号名称' },
      { key: 'brand', label: '品牌' }
    ]
    const specKeys = new Set()
    rows.forEach((item) => {
      Object.keys(item?.specs || {}).forEach((key) => specKeys.add(String(key || '').trim()))
    })
    const specColumns = Array.from(specKeys)
      .filter(Boolean)
      .sort((left, right) => left.localeCompare(right))
      .map((key) => ({ key, label: prettifySelectionColumnLabel(key) }))
    selectionTableColumnsByCategory.value[normalizedCategoryCode] = [...systemColumns, ...specColumns]
  } catch (error) {
    console.error('加载选型表列失败:', error)
    selectionTableColumnsByCategory.value[normalizedCategoryCode] = []
  }
}

const handleSelectionCategoryChange = (newCode) => {
  ensureSelectionCategoryStructure(newCode)
  selectedSelectionTableColumn.value = ''
  loadSelectionTableColumns(newCode)
  syncSelectionFieldConfigsFromMappings(newCode)
}
const handleAddSelectionFieldFromColumn = () => {
  const columnKey = String(selectedSelectionTableColumn.value || '').trim()
  if (!columnKey) {
    ElMessage.warning('请先从当前选型表中选择一个表列')
    return
  }
  const normalizedCategoryCode = String(activeSelectionCategoryCode.value || '').trim() || 'gearmotor'
  ensureSelectionCategoryStructure(normalizedCategoryCode)
  const existingField = activeSelectionFields.value.find((field) => String(field.source_spec || field.key || '').trim() === columnKey)
  if (existingField) {
    ElMessage.warning('该表列已经添加为选型参数')
    return
  }
  const isStringField = ['model_name', 'brand'].includes(columnKey)
  const columnLabel = activeSelectionTableColumnLabelMap.value.get(columnKey) || prettifySelectionColumnLabel(columnKey)
  selectionFieldConfigs.value[normalizedCategoryCode].push({
    key: columnKey,
    label: columnLabel,
    type: isStringField ? 'string' : 'numeric',
    compare: isStringField ? 'eq' : 'near',
    source_spec: columnKey,
    weight: 0.10,
    priority: (selectionFieldConfigs.value[normalizedCategoryCode] || []).length + 1,
    tolerance: isStringField ? 0 : 10,
    hard_constraint: false
  })
  selectionMappings.value[normalizedCategoryCode][columnKey] = normalizeSelectionMappingEntry(
    selectionMappings.value[normalizedCategoryCode][columnKey],
    isStringField ? 'string' : 'numeric'
  )
  selectedSelectionTableColumn.value = ''
}
const handleRemoveSelectionField = (fieldKey) => {
  const normalizedCategoryCode = String(activeSelectionCategoryCode.value || '').trim() || 'gearmotor'
  ensureSelectionCategoryStructure(normalizedCategoryCode)
  selectionFieldConfigs.value[normalizedCategoryCode] = (selectionFieldConfigs.value[normalizedCategoryCode] || []).filter(field => field.key !== fieldKey)
  if (selectionMappings.value[normalizedCategoryCode]) {
    delete selectionMappings.value[normalizedCategoryCode][fieldKey]
  }
}
const handleMappingChange = async () => {
  if (!selectedVersionId.value) return
  try {
    const backendMappings = {}
    Object.entries(selectionMappings.value || {}).forEach(([categoryCode, categoryMappings]) => {
      const nextCategoryMappings = {}
      Object.entries(categoryMappings || {}).forEach(([fieldKey, entry]) => {
        const normalizedEntry = normalizeSelectionMappingEntry(entry)
        if (normalizedEntry.source_type === 'parameter' && normalizedEntry.parameter_code) {
          nextCategoryMappings[fieldKey] = normalizedEntry.parameter_code
        }
      })
      if (Object.keys(nextCategoryMappings).length > 0) {
        backendMappings[categoryCode] = nextCategoryMappings
      }
    })
    await saveSelectionMappings(selectedVersionId.value, backendMappings)
    persistSelectionFieldConfigs()
    persistSelectionMappings()
    ElMessage.success('选型映射已保存')
  } catch (error) {
    ElMessage.error('选型映射保存失败')
  }
}

const loadingWorkbench = ref(false)
const executing = ref(false)
const calculationError = ref('')
const explanationTarget = ref({ type: 'module', key: '' })
const smartSelectDrawerVisible = ref(false)

// 计算链智能分析弹窗
const analysisDialogVisible = ref(false)
const openCalculationAnalysis = () => {
  if (!selectedVersionId.value) {
    ElMessage.warning('请先选择计算型号')
    return
  }
  analysisDialogVisible.value = true
}

watch(smartSelectDrawerVisible, async (nextVisible) => {
  if (!nextVisible) return
  try {
    await loadEquipmentCategoriesIfNeeded()
    await loadSelectionTableColumns(activeSelectionCategoryCode.value)
    syncSelectionFieldConfigsFromMappings(activeSelectionCategoryCode.value)
  } catch (_error) {
  }
})
watch(
  () => selectionFieldConfigs.value,
  () => {
    persistSelectionFieldConfigs()
  },
  { deep: true }
)
watch(
  () => selectionMappings.value,
  () => {
    persistSelectionMappings()
  },
  { deep: true }
)
const analysisBaselineSummaryMap = ref({})

const workspaceMode = ref('list')
const analysisTabs = [
  { label: '校核结果', value: 'verify' },
  { label: '设计说明', value: 'explanation' }
]
const parameterSearchKeyword = ref('')
const activeFlowNodeId = ref('')
const flowViewportState = ref({ zoom: 1, center: ['50%', '50%'] })
const flowDisplayMode = ref('all')
const flowViewportResetToken = ref(0)

const editingFormulaKey = ref('')
const editingFormulaField = ref('')
const activeFormulaDraft = ref({})
const formulaSaving = ref(false)
const formulaCursorStart = ref(0)
const formulaCompositionActive = ref(false)
const lookupItems = ref([])

const isExplanationEditing = ref(false)
const explanationEditForm = ref({
  summary: '',
  resources: [],
  output_flag: 'auto',
  source_type: 'manual',
  source_note: ''
})
const focusMetricDialogVisible = ref(false)
const focusMetricEditingKey = ref('')
const focusMetricDraft = ref({
  metricName: '',
  mode: 'compare',
  targetParam: '',
  operator: '>=',
  tolerance: '',
  rangeMin: '',
  rangeMax: '',
  impactParams: []
})

const startExplanationEditing = () => {
  let summary = explanationPanel.value.summary
  if (summary === '当前暂无补充说明。' || summary.startsWith('参数值:') || summary.startsWith('公式表达式：') || summary.startsWith('实际值：')) {
    summary = ''
  }
  
  // Deep clone resources to avoid modifying the original array before saving
  const resources = (explanationPanel.value.resources || [])
    .filter((resource) => resource?.type !== 'focus_metric_config')
    .map(r => {
    const cloned = { ...r }
    // Ensure all required fields for verification_rule exist
    if (cloned.type === 'verification_rule') {
      cloned.targetParam = cloned.targetParam || ''
      cloned.operator = cloned.operator || '<='
      cloned.tolerance = cloned.tolerance || ''
      cloned.rangeMin = cloned.rangeMin || ''
      cloned.rangeMax = cloned.rangeMax || ''
    }
    return cloned
  })
  
  explanationEditForm.value = {
    summary: summary,
    resources: resources,
    output_flag: explanationPanel.value.output_flag || 'auto',
    source_type: explanationPanel.value.sourceType || 'manual',
    source_note: explanationPanel.value.sourceNote || ''
  }
  isExplanationEditing.value = true
}

const cancelExplanationEditing = () => {
  isExplanationEditing.value = false
}

const saveExplanationEditing = () => {
  handleExplanationUpdate({
    summary: explanationEditForm.value.summary,
    resources: explanationEditForm.value.resources,
    output_flag: explanationEditForm.value.output_flag,
    source_type: explanationEditForm.value.source_type,
    source_note: explanationEditForm.value.source_note
  })
  isExplanationEditing.value = false
}

const addExplanationResource = () => {
  explanationEditForm.value.resources.push({
    type: 'text',
    typeLabel: '文字',
    title: '',
    content: ''
  })
}

const handleExplanationImageChange = async (file, index) => {
  try {
    const filePath = await uploadReferenceResource(file.raw)
    explanationEditForm.value.resources[index].content = filePath
    explanationEditForm.value.resources[index].title ||= file.name || file.raw?.name || '图片资料'
    ElMessage.success('图片已上传')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '图片上传失败')
  }
}

const handleExplanationDocumentChange = async (file, index) => {
  try {
    const filePath = await uploadReferenceResource(file.raw)
    explanationEditForm.value.resources[index].content = filePath
    explanationEditForm.value.resources[index].title ||= file.name || file.raw?.name || '参考文件'
    ElMessage.success('文件已上传')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '文件上传失败')
  }
}

const removeExplanationResource = (idx) => {
  explanationEditForm.value.resources.splice(idx, 1)
}

const resourceData = ref({})
const currentResourceData = computed(() => {
  const key = explanationTarget.value.key || explanationTarget.value.type || 'default'
  if (!resourceData.value[key]) {
    resourceData.value[key] = { text: '', images: [], videos: [], files: [] }
  }
  return resourceData.value[key]
})

let autoRunTimer = null

const DEFAULT_PARAMETER_PROVENANCE = Object.freeze({
  source_type: 'manual',
  source_note: '',
  resources: [],
  custom_group_key: '',
  custom_group_label: ''
})

const PARAMETER_GROUP_OPTIONS = Object.freeze([
  { key: 'condition', label: '工况参数' },
  { key: 'structure', label: '滚筒结构' },
  { key: 'selection', label: '选型输入参数' },
  { key: 'general', label: '基础参数' },
  { key: 'custom', label: '自定义参数' }
])

const PARAMETER_GROUP_LABEL_MAP = Object.freeze(
  PARAMETER_GROUP_OPTIONS.reduce((accumulator, option) => {
    accumulator[option.key] = option.label
    return accumulator
  }, {})
)

const PARAMETER_SOURCE_LABELS = {
  manual: '人工录入',
  experience: '经验取值',
  standard: '标准/规范',
  test: '试验/实测',
  vendor: '厂家资料',
  lookup: '查表/计算'
}
const ANALYSIS_PARAMETER_ALIAS_MAP = {
  电机转速: ['电机_额定转速'],
  传动比: ['减速机_减速比', '减速比', '减速比i'],
  电机效率: ['电机_100%效率'],
  进料量: ['滚筒产量', '产量'],
  滚筒产量: ['进料量', '产量'],
  存料量: ['筒内料重'],
  筒内料重: ['存料量'],
  滚筒重量: ['筒体重量', '简体重量'],
  筒体重量: ['滚筒重量', '简体重量'],
  简体重量: ['筒体重量', '滚筒重量'],
  电机频率: ['电机_频率'],
  电机_频率: ['电机频率'],
  电机额定转矩: ['电机_额定转矩', '电机额定扭矩', '电机_额定扭矩'],
  电机_额定转矩: ['电机额定转矩', '电机额定扭矩', '电机_额定扭矩'],
  输出转矩: ['输出扭矩'],
  输出扭矩: ['输出转矩'],
  理论转矩: ['理论扭矩'],
  理论扭矩: ['理论转矩'],
  实际工作滚筒转速: ['滚筒转速', '实际滚筒转速', '工作滚筒转速'],
  滚筒转速: ['实际工作滚筒转速', '实际滚筒转速', '工作滚筒转速']
}

const buildEquivalentSymbolicNameGroups = () => {
  const rawGroups = JSON.parse(JSON.stringify(ANALYSIS_PARAMETER_ALIAS_MAP || {}))
  const merged = new Map()
  const parentMap = new Map()
  const findRoot = (name) => {
    if (!parentMap.has(name)) {
      parentMap.set(name, name)
      merged.set(name, new Set([name]))
    }
    let root = name
    const path = []
    while (parentMap.get(root) !== root) {
      path.push(root)
      root = parentMap.get(root)
    }
    for (const node of path) parentMap.set(node, root)
    return root
  }
  const union = (left, right) => {
    const rootL = findRoot(left)
    const rootR = findRoot(right)
    if (rootL === rootR) return
    const setL = merged.get(rootL) || new Set([left])
    const setR = merged.get(rootR) || new Set([right])
    const smaller = setL.size <= setR.size ? setL : setR
    const bigger = setL.size <= setR.size ? setR : setL
    const smallRoot = setL.size <= setR.size ? rootL : rootR
    const bigRoot = setL.size <= setR.size ? rootR : rootL
    for (const name of smaller) {
      bigger.add(name)
      parentMap.set(name, bigRoot)
    }
    merged.set(smallRoot, new Set())
    merged.set(bigRoot, bigger)
  }
  for (const [key, aliases] of Object.entries(rawGroups || {})) {
    if (!Array.isArray(aliases)) continue
    for (const alias of aliases) {
      union(key, String(alias || '').trim())
    }
  }
  const groups = []
  const seen = new Set()
  for (const root of merged.keys()) {
    const set = merged.get(root) || new Set()
    if (!set.size) continue
    const first = Array.from(set)[0]
    if (seen.has(first)) continue
    const normalized = Array.from(set).filter(Boolean).map((name) => String(name).trim()).filter(Boolean)
    if (!normalized.length) continue
    for (const name of normalized) seen.add(name)
    groups.push(normalized)
  }
  return groups
}

const ANALYSIS_EQUIVALENT_SYMBOLIC_GROUPS = buildEquivalentSymbolicNameGroups()

const iterEquivalentSymbolicNames = (name) => {
  const normalized = String(name || '').trim()
  if (!normalized) return []
  const seen = new Set([normalized])
  const collected = [normalized]
  const aliasNames = ANALYSIS_PARAMETER_ALIAS_MAP[normalized] || []
  for (const rawAlias of aliasNames) {
    const alias = String(rawAlias || '').trim()
    if (!alias || seen.has(alias)) continue
    seen.add(alias)
    collected.push(alias)
  }
  for (const group of ANALYSIS_EQUIVALENT_SYMBOLIC_GROUPS) {
    if (!group.includes(normalized)) continue
    for (const groupName of group) {
      const item = String(groupName || '').trim()
      if (!item || seen.has(item)) continue
      seen.add(item)
      collected.push(item)
    }
  }
  return collected
}

const normalizeResourceRows = (resources = []) => {
  return (Array.isArray(resources) ? resources : []).map((resource) => ({
    type: resource?.type || 'text',
    title: resource?.title || '',
    content: resource?.content || '',
    targetParam: resource?.targetParam || '',
    operator: resource?.operator || '<=',
    tolerance: resource?.tolerance || '',
    rangeMin: resource?.rangeMin || '',
    rangeMax: resource?.rangeMax || '',
    mode: resource?.mode || 'compare',
    metricName: resource?.metricName || '',
    paramName: resource?.paramName || '',
    impactParams: Array.isArray(resource?.impactParams) ? resource.impactParams : []
  }))
}

const createEmptyFocusMetricConfig = (metricName = '') => ({
  type: 'focus_metric_config',
  metricName: String(metricName || '').trim(),
  mode: 'compare',
  targetParam: '',
  operator: '>=',
  tolerance: '',
  rangeMin: '',
  rangeMax: '',
  impactParams: []
})

const createEmptySelectionParamConfig = (paramName = '') => ({
  type: 'selection_param_config',
  paramName: String(paramName || '').trim()
})

const normalizeFocusMetricConfig = (resource = {}, metricName = '') => ({
  ...createEmptyFocusMetricConfig(metricName),
  ...resource,
  type: 'focus_metric_config',
  metricName: String(resource?.metricName || metricName || '').trim(),
  mode: resource?.mode === 'range' ? 'range' : 'compare',
  targetParam: String(resource?.targetParam || '').trim(),
  operator: String(resource?.operator || '>=').trim() || '>=',
  tolerance: String(resource?.tolerance || '').trim(),
  rangeMin: String(resource?.rangeMin || '').trim(),
  rangeMax: String(resource?.rangeMax || '').trim(),
  impactParams: Array.isArray(resource?.impactParams)
    ? resource.impactParams.map((item) => String(item || '').trim()).filter(Boolean)
    : []
})

const normalizeSelectionParamConfig = (resource = {}, paramName = '') => ({
  ...createEmptySelectionParamConfig(paramName),
  ...resource,
  type: 'selection_param_config',
  paramName: String(resource?.paramName || paramName || '').trim()
})

const normalizeParameterProvenance = (value) => {
  if (!value) {
    return { ...DEFAULT_PARAMETER_PROVENANCE }
  }
  if (typeof value === 'object') {
    return {
      source_type: value.source_type || 'manual',
      source_note: value.source_note || '',
      resources: normalizeResourceRows(value.resources || []),
      custom_group_key: String(value.custom_group_key || '').trim(),
      custom_group_label: String(value.custom_group_label || '').trim()
    }
  }
  try {
    const parsed = JSON.parse(String(value || ''))
    return normalizeParameterProvenance(parsed)
  } catch (_error) {
    return {
      source_type: 'manual',
      source_note: String(value || '').trim(),
      resources: []
    }
  }
}

const buildParameterRemark = (row = {}) => {
  const provenance = normalizeParameterProvenance(row.provenance || row.remark || null)
  return JSON.stringify({
    source_type: provenance.source_type || 'manual',
    source_note: provenance.source_note || '',
    resources: normalizeResourceRows(row.resources || provenance.resources || []),
    custom_group_key: String(row.customGroupKey || provenance.custom_group_key || '').trim(),
    custom_group_label: String(row.customGroupLabel || provenance.custom_group_label || '').trim()
  })
}

const isResourceLink = (value = '') => /^(https?:\/\/|\/)/i.test(String(value || '').trim())

const uploadReferenceResource = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await axios.post('/product-components/upload-ref', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return String(data?.file_path || '')
}

const normalizeQueryValue = (value) => {
  if (Array.isArray(value)) {
    return String(value[0] || '')
  }
  return String(value || '')
}

const formatMetric = (value, unitCode = '') => {
  const text = String(value ?? '').trim()
  if (!text) return '-'
  
  let formattedText = text
  if (!isNaN(Number(text)) && text !== '') {
    formattedText = Number(text).toFixed(1)
  }
  
  return unitCode ? `${formattedText} ${unitCode}` : formattedText
}

const formatMetricRange = (minValue, maxValue, unitCode = '') => {
  const minText = formatMetric(minValue, unitCode)
  const maxText = formatMetric(maxValue, unitCode)
  if (minText === '-' && maxText === '-') return '-'
  return `${minText} ~ ${maxText}`
}

const toFiniteMetricNumber = (value) => {
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue : null
}

const formatEstimatedFocusMetricRanges = (ranges = [], unitCode = '') => {
  return ranges
    .map((range) => {
      const minValue = Number(range?.minValue)
      const maxValue = Number(range?.maxValue)
      if (!Number.isFinite(minValue) || !Number.isFinite(maxValue)) return '-'
      const epsilon = Math.max(Math.abs(minValue), Math.abs(maxValue), 1) * 1e-6
      if (Math.abs(maxValue - minValue) <= epsilon) {
        return formatMetric(minValue, unitCode)
      }
      return formatMetricRange(minValue, maxValue, unitCode)
    })
    .filter((text) => text && text !== '-')
    .join('、')
}

const resolveSourceLabel = (source = '') => {
  const labels = {
    model: '型号矩阵',
    snapshot: '工作台快照',
    draft: '手动调整',
    catalog: '默认值',
    empty: '待补参数'
  }
  return labels[String(source || '').trim()] || '待补参数'
}

const resolveSourceTagType = (source = '') => {
  const tagTypes = {
    model: 'success',
    snapshot: 'warning',
    draft: 'primary',
    catalog: 'info',
    empty: 'danger'
  }
  return tagTypes[String(source || '').trim()] || 'danger'
}

const buildRouteQuery = () => ({
  typeId: selectedTypeId.value,
  familyId: selectedFamilyId.value,
  versionId: selectedVersionId.value,
  moduleCode: activeModuleCode.value
})

const syncRouteQuery = async () => {
  await router.replace({
    name: 'NewDesignWorkbench',
    query: {
      ...route.query,
      ...buildRouteQuery()
    }
  })
}

const goBackToModules = () => {
  if (selectedTypeId.value) {
    router.push({
      name: 'ModuleSelection',
      params: { typeId: selectedTypeId.value },
      query: {
        familyId: selectedFamilyId.value || undefined,
        versionId: selectedVersionId.value || undefined
      }
    })
  } else {
    router.push('/workbench/product-select')
  }
}

const currentTypeNode = computed(() => {
  return treeData.value.find((node) => String(node.raw?.id || '') === String(selectedTypeId.value || '')) || null
})

const currentFamilyNode = computed(() => {
  return (currentTypeNode.value?.children || []).find((node) => String(node.raw?.id || '') === String(selectedFamilyId.value || '')) || null
})

const currentVersionNode = computed(() => {
  return (currentFamilyNode.value?.children || []).find((node) => String(node.raw?.id || '') === String(selectedVersionId.value || '')) || null
})

const currentTypeName = computed(() => currentTypeNode.value?.label || '未选择产品类型')
const workbenchTitle = computed(() => {
  const moduleName = activeModule.value?.moduleName || requestedModuleCode.value || '未选择模块'
  return `${currentTypeName.value} / ${moduleName}工作台`
})
const currentVersionPath = computed(() => {
  if (!currentFamilyNode.value || !currentVersionNode.value) return '未选择型号'
  return `${currentFamilyNode.value.label} / ${currentVersionNode.value.label}`
})

const filteredScopeTree = computed(() => currentTypeNode.value?.children || [])
const currentTreeNodeKey = computed(() => (selectedVersionId.value ? `version-${selectedVersionId.value}` : ''))

const activeModule = computed(() => {
  return modules.value.find((module) => String(module.moduleCode || '') === String(activeModuleCode.value || '')) || null
})

const moduleSummary = computed(() => {
  if (!activeModule.value) {
    return { sceneCount: 0, formulaCount: 0 }
  }
  return buildModuleSummary(activeModule.value)
})

const setParameterFeedback = (message, tone = 'info') => {
  parameterFeedback.value = {
    tone,
    message: String(message || '').trim() || DEFAULT_PARAMETER_FEEDBACK
  }
}

const activeModuleFormulaRows = computed(() => {
  return (activeModule.value?.scenes || []).flatMap((scene) =>
    (scene.rows || []).map((row, index) => ({
      ...row,
      moduleCode: activeModule.value?.moduleCode || '',
      sceneCode: scene.sceneCode || '',
      sceneName: scene.sceneName || '未命名场景',
      _rowKey: row._rowKey || `${activeModule.value?.moduleCode || 'module'}:${scene.sceneCode || 'scene'}:${row.id || row.name || index}`,
      resources: Array.isArray(row.resources) ? row.resources : []
    }))
  )
})

const parameterLookupMap = computed(() => {
  return new Map(
    parameterRows.value.map((row) => [String(row.paramName || '').trim(), row])
  )
})

const moduleFormulaNames = computed(() => {
  return new Set(
    activeModuleFormulaRows.value
      .map((row) => String(row.name || '').trim())
      .filter(Boolean)
  )
})

const equipmentParameters = computed(() => {
  return parameterRows.value.filter(r => r.valueType === 'equipment' || r.paramName.startsWith('电机_') || r.paramName.startsWith('减速机_'))
})

const filteredSelectionParameterRows = computed(() => {
  const keyword = parameterSearchKeyword.value.trim().toLowerCase()
  if (!keyword) return equipmentParameters.value
  return equipmentParameters.value.filter(r => 
    String(r.displayName || '').toLowerCase().includes(keyword) || 
    String(r.paramName || '').toLowerCase().includes(keyword)
  )
})

const allAvailableParameters = computed(() => {
  const params = new Map()
  parameterRows.value.forEach(r => params.set(r.paramName, r.displayName || r.paramName))
  moduleExecutionRows.value.forEach(r => params.set(r.paramName, r.displayName || r.paramName))
  return Array.from(params.entries()).map(([paramName, displayName]) => ({ paramName, displayName }))
})

const filteredModuleInputRows = computed(() => {
  const keyword = parameterSearchKeyword.value.trim().toLowerCase()
  if (!keyword) return moduleInputRows.value
  return moduleInputRows.value.filter(r => 
    r.pendingCreate ||
    String(r.displayName || '').toLowerCase().includes(keyword) || 
    String(r.paramName || '').toLowerCase().includes(keyword)
  )
})

watch(equipmentParameters, (newParams) => {
  const versionId = String(selectedVersionId.value || '').trim()
  if (!versionId) return
  const storageKey = getEquipmentRowsStorageKey(versionId)
  if (newParams.length > 0) {
    localStorage.setItem(storageKey, JSON.stringify(newParams))
    return
  }
  localStorage.removeItem(storageKey)
}, { deep: true })

const moduleInputRows = computed(() => {
  const orderedNames = []
  const seen = new Set()
  
  // 过滤掉后台函数参数及无效字符
  const ignoredFunctionParams = new Set([...ALL_RESERVED_IDENTIFIERS].map(id => id.toUpperCase()))

  const isValidParamName = (name) => {
    if (!name) return false
    if (String(name || '').trim() === 'π') return false
    if (/^[0-9.]+$/.test(name)) return false // 纯数字不是参数
    if (ignoredFunctionParams.has(name.toUpperCase())) return false
    // 仅过滤以“=”开头的公式字符串；参数名允许包含括号、斜杠、百分号等合法字符，
    // 避免重命名成“产量(t/h)”“效率%”“功率/产量”这类名字后从参数树消失
    if (String(name || '').trim().startsWith('=')) return false
    return true
  }

  parameterRows.value.forEach((row) => {
    // 先过滤设备参数：选型注入的电机_/减速机_参数只进“选型参数树”，不污染输入参数树
    if (row.valueType === 'equipment' || String(row.paramName || '').startsWith('电机_') || String(row.paramName || '').startsWith('减速机_')) return

    if (row.pendingCreate) {
      const tempName = String(row._tempId || Math.random())
      if (!seen.has(tempName)) {
        seen.add(tempName)
        orderedNames.push(tempName)
      }
      return
    }

    // 过滤掉函数参数和无效字符
    if (!isValidParamName(row.paramName)) return

    const normalizedName = String(row.paramName || '').trim()
    if (normalizedName && !seen.has(normalizedName)) {
      seen.add(normalizedName)
      orderedNames.push(normalizedName)
    }
  })

  const resultRows = orderedNames.map((paramName) => {
    const existing = parameterRows.value.find(r => r.paramName === paramName || r._tempId === paramName)
    if (existing) {
      return {
        ...existing,
        displayName: resolveParameterDisplayName(existing, paramName),
        allowDelete: true
      }
    }
    return {
      parameterId: 0,
      paramCode: '',
      paramName,
      displayName: paramName,
      unitCode: '',
      value: String(latestScope.value?.[paramName] ?? ''),
      dirty: false,
      source: 'empty',
      allowDelete: true
    }
  })

  return resultRows.sort((left, right) => {
    if (!left.paramName) return -1;
    if (!right.paramName) return 1;
    return String(left.paramName || '').localeCompare(String(right.paramName || ''), 'zh-CN');
  })
})

const moduleExecutionRows = computed(() => {
  return buildExecutionIntermediateRows({
    formulaRows: activeModuleFormulaRows.value,
    latestResults: latestResults.value,
    latestScope: latestScope.value
  }).map((row) => ({
    ...row,
    displayName: row.displayName || row.paramName || ''
  }))
})

const referencedFormulaNames = computed(() => {
  const referenced = new Set()
  for (const row of activeModuleFormulaRows.value) {
    for (const name of getFormulaDependencyNames(row)) {
      const normalizedName = String(name || '').trim()
      if (moduleFormulaNames.value.has(normalizedName)) {
        referenced.add(normalizedName)
      }
    }
  }
  return referenced
})

const verificationRulesMap = computed(() => {
  const map = new Map()
  for (const row of activeModuleFormulaRows.value) {
    const name = String(row.name || '').trim()
    if (!name) continue
    const resources = Array.isArray(row.resources) ? row.resources : []
    const rule = resources.find(r => r.type === 'verification_rule')
    if (rule) {
      map.set(name, rule)
    }
  }
  return map
})

/** 按型号隔离的关注指标配置（localStorage 存储，key=versionId_metricName） */
const getFocusMetricStorageKey = (versionId) => `focus_metric_config_${String(versionId || '').trim()}`
const localFocusMetricConfig = ref({})
// 型号级后端独立配置（各型号一份，避免模板/同步导致的串号）
const backendFocusMetricConfigs = ref({})

const loadLocalFocusMetricConfig = (versionId) => {
  try {
    const key = getFocusMetricStorageKey(versionId)
    const raw = localStorage.getItem(key)
    localFocusMetricConfig.value = raw ? JSON.parse(raw) : {}
  } catch (e) {
    localFocusMetricConfig.value = {}
  }
}

const saveLocalFocusMetricConfig = (versionId, metricName, config) => {
  try {
    const key = getFocusMetricStorageKey(versionId)
    const current = { ...localFocusMetricConfig.value }
    current[metricName] = config
    localFocusMetricConfig.value = current
    localStorage.setItem(key, JSON.stringify(current))
  } catch (e) {
    // localStorage 可能满，静默忽略
  }
}

const focusMetricConfigMap = computed(() => {
  const map = new Map()
  // 1. 型号级后端配置（各型号独立，权威，与共享公式资源解耦）
  const backendConfigs = backendFocusMetricConfigs.value || {}
  for (const [metricName, config] of Object.entries(backendConfigs)) {
    if (config) {
      map.set(metricName, normalizeFocusMetricConfig(config, metricName))
    }
  }
  // 2. 型号级 localStorage 配置覆盖（本地优先）
  const localConfigs = localFocusMetricConfig.value || {}
  for (const [metricName, localConfig] of Object.entries(localConfigs)) {
    if (localConfig) {
      map.set(metricName, normalizeFocusMetricConfig(localConfig, metricName))
    }
  }
  // 3. 仅当指标被标记为“关注指标”（公式 resource 存在）、但当前型号尚无独立配置时，
  //    补一个空配置占位，使其仍出现在关注指标卡上，但参考值显示“-”，绝不串用别的型号的配置。
  for (const row of activeModuleFormulaRows.value) {
    const metricName = String(row.name || '').trim()
    if (!metricName || map.has(metricName)) continue
    const resources = Array.isArray(row.resources) ? row.resources : []
    const hasFocusResource = resources.some((resource) => resource?.type === 'focus_metric_config')
    if (hasFocusResource) {
      map.set(metricName, createEmptyFocusMetricConfig(metricName))
    }
  }
  return map
})

const selectionParamConfigMap = computed(() => {
  const map = new Map()
  for (const row of activeModuleFormulaRows.value) {
    const paramName = String(row.name || '').trim()
    if (!paramName) continue
    const resources = Array.isArray(row.resources) ? row.resources : []
    const configResource = resources.find((resource) => resource?.type === 'selection_param_config')
    if (!configResource) continue
    map.set(paramName, normalizeSelectionParamConfig(configResource, paramName))
  }
  return map
})

const findResultRowByEquivalentName = (name) => {
  const normalizedName = String(name || '').trim()
  if (!normalizedName) return null
  const directResult = latestResults.value.find((row) => {
    const rowCode = String(row?.result_code || '').trim()
    const rowName = String(row?.result_name || '').trim()
    return rowCode === normalizedName || rowName === normalizedName
  }) || null
  if (directResult) return directResult
  for (const aliasName of iterEquivalentSymbolicNames(normalizedName)) {
    const matched = latestResults.value.find((row) => {
      const rowCode = String(row?.result_code || '').trim()
      const rowName = String(row?.result_name || '').trim()
      return rowCode === aliasName || rowName === aliasName
    }) || null
    if (matched) return matched
  }
  return null
}

const getMetricCurrentValue = (paramName = '') => {
  const normalizedName = String(paramName || '').trim()
  if (!normalizedName) return null
  const directExecutionRow = moduleExecutionRows.value.find((row) => String(row.paramName || '').trim() === normalizedName)
  if (directExecutionRow?.value !== undefined && directExecutionRow?.value !== null && String(directExecutionRow.value).trim() !== '') {
    return directExecutionRow.value
  }
  for (const aliasName of iterEquivalentSymbolicNames(normalizedName)) {
    const executionRow = moduleExecutionRows.value.find((row) => String(row.paramName || '').trim() === aliasName)
    if (executionRow?.value !== undefined && executionRow?.value !== null && String(executionRow.value).trim() !== '') {
      return executionRow.value
    }
  }
  const parameterRow = findParameterRowByNameOrAlias(normalizedName)
  if (parameterRow?.value !== undefined && parameterRow?.value !== null && String(parameterRow.value).trim() !== '') {
    return parameterRow.value
  }
  const directScopeValue = latestScope.value?.[normalizedName]
  if (directScopeValue !== undefined && directScopeValue !== null && String(directScopeValue).trim() !== '') {
    return directScopeValue
  }
  for (const aliasName of iterEquivalentSymbolicNames(normalizedName)) {
    const aliasScopeValue = latestScope.value?.[aliasName]
    if (aliasScopeValue !== undefined && aliasScopeValue !== null && String(aliasScopeValue).trim() !== '') {
      return aliasScopeValue
    }
  }
  const resultRow = findResultRowByEquivalentName(normalizedName)
  if (resultRow && String(resultRow.result_value || '').trim() !== '') {
    return resultRow.result_value
  }
  return directScopeValue ?? null
}

const buildFocusMetricRuleDescription = (config = {}) => {
  if (!config) return '未配置校核规则'
  if (config.mode === 'range') {
    if (config.rangeMin === '' && config.rangeMax === '') {
      return '未配置合理区间'
    }
    return `区间校核：${config.rangeMin || '-'} ~ ${config.rangeMax || '-'}`
  }
  if (!config.targetParam) {
    return '未配置对比参数'
  }
  return `参数对比：实际值 ${config.operator || '>='} ${config.targetParam}`
}

const resolveFocusMetricReferenceText = (config = {}, unitCode = '') => {
  if (!config) return '-'
  if (config.mode === 'range') {
    return formatMetricRange(config.rangeMin, config.rangeMax, unitCode)
  }
  if (!config.targetParam) {
    return '-'
  }
  return formatMetric(getMetricCurrentValue(config.targetParam), unitCode)
}

const evaluateFocusMetricStatus = (actualValue, config = {}) => {
  if (actualValue === undefined || actualValue === null || String(actualValue).trim() === '') return null
  const actualNum = Number(actualValue)
  if (!Number.isFinite(actualNum)) return null
  if (config.mode === 'range') {
    const min = Number(config.rangeMin)
    const max = Number(config.rangeMax)
    const hasMin = Number.isFinite(min)
    const hasMax = Number.isFinite(max)
    if (!hasMin && !hasMax) return null
    const lowerEpsilon = hasMin ? Math.max(Math.abs(min), 1) * 1e-9 : 0
    const upperEpsilon = hasMax ? Math.max(Math.abs(max), 1) * 1e-9 : 0
    const status = (() => {
      if (hasMin && actualNum + lowerEpsilon < min) return 'fail'
      if (hasMax && actualNum - upperEpsilon > max) return 'fail'
      return 'pass'
    })()
    return status
  }

  const targetValue = Number(getMetricCurrentValue(config.targetParam))
  if (!config.targetParam || !Number.isFinite(targetValue)) return null
  const tolerance = Number(config.tolerance || 0)
  switch (config.operator) {
    case '>':
      return actualNum > targetValue ? 'pass' : 'fail'
    case '>=':
      return actualNum >= targetValue ? 'pass' : 'fail'
    case '<':
      return actualNum < targetValue ? 'pass' : 'fail'
    case '<=':
      return actualNum <= targetValue ? 'pass' : 'fail'
    case '==':
      return Math.abs(actualNum - targetValue) <= tolerance ? 'pass' : 'fail'
    default:
      return null
  }
}

const convertVerificationRuleToFocusConfig = (rule = {}, metricName = '') => {
  if (!rule) return createEmptyFocusMetricConfig(metricName)
  const op = String(rule.operator || '').trim()
  if (op === 'between') {
    return {
      ...createEmptyFocusMetricConfig(metricName),
      mode: 'range',
      rangeMin: String(rule.rangeMin ?? '').trim(),
      rangeMax: String(rule.rangeMax ?? '').trim()
    }
  }
  return {
    ...createEmptyFocusMetricConfig(metricName),
    mode: 'compare',
    targetParam: String(rule.targetParam || '').trim(),
    operator: op || '>=',
    tolerance: String(rule.tolerance ?? '').trim()
  }
}

const resolveUnifiedVerificationStatus = (row = {}) => {
  const metricName = String(row?.name || '').trim()
  if (!metricName) return null
  const actualRow = moduleExecutionRows.value.find(r => String(r.paramName || '').trim() === metricName)
  const actualValue = actualRow?.value ?? getMetricCurrentValue(metricName)
  if (actualValue === undefined || actualValue === null || String(actualValue).trim() === '') return null
  const focusConfig = focusMetricConfigMap.value.get(metricName)
  if (focusConfig) {
    return evaluateFocusMetricStatus(actualValue, focusConfig)
  }
  const rule = verificationRulesMap.value.get(metricName)
  if (rule) {
    const fallbackConfig = convertVerificationRuleToFocusConfig(rule, metricName)
    return evaluateFocusMetricStatus(actualValue, fallbackConfig)
  }
  return null
}

const collectResultMissingDependencies = (resultName = '', config = null) => {
  const missingDependencies = []
  const formulaRow = activeModuleFormulaRows.value.find((row) => String(row.name || '').trim() === String(resultName || '').trim())
  if (formulaRow) {
    Object.keys(formulaRow.variables || {}).forEach((paramName) => {
      const normalizedName = String(paramName || '').trim()
      const parameterRow = parameterLookupMap.value.get(normalizedName)
      const resultRow = resultRowMap.value.get(normalizedName)
      const val = parameterRow?.value ?? resultRow?.value ?? String(latestScope.value?.[normalizedName] ?? '')
      if (String(val).trim() === '') {
        const displayName = parameterRow?.displayName || resultRow?.displayName || normalizedName
        if (!missingDependencies.includes(displayName)) {
          missingDependencies.push(displayName)
        }
      }
    })
  }
  if (config?.mode === 'compare' && config?.targetParam) {
    const targetName = String(config.targetParam || '').trim()
    const targetRow = parameterLookupMap.value.get(targetName) || resultRowMap.value.get(targetName)
    const value = getMetricCurrentValue(targetName)
    if (String(value ?? '').trim() === '') {
      const displayName = targetRow?.displayName || targetName
      if (!missingDependencies.includes(displayName)) {
        missingDependencies.push(displayName)
      }
    }
  }
  return missingDependencies
}

const verificationTargetNames = computed(() => {
  const targets = new Set()
  for (const rule of verificationRulesMap.value.values()) {
    if (rule.targetParam) {
      targets.add(String(rule.targetParam).trim())
    }
  }
  return targets
})

const verificationResultsMap = computed(() => {
  const map = new Map()
  for (const [name, rule] of verificationRulesMap.value.entries()) {
    const actualRow = moduleExecutionRows.value.find(r => String(r.paramName || '').trim() === name)
    if (!actualRow) continue

    let theoryValue = null
    let status = null

    if (rule.targetParam) {
      const targetName = String(rule.targetParam).trim()
      const targetRow = moduleExecutionRows.value.find(r => String(r.paramName || '').trim() === targetName)
      theoryValue = targetRow ? targetRow.value : latestScope.value?.[targetName]

      if (theoryValue !== undefined && theoryValue !== null && theoryValue !== '' && actualRow.value !== undefined && actualRow.value !== null && actualRow.value !== '') {
        const actualNum = Number(actualRow.value)
        const theoryNum = Number(theoryValue)
        if (!isNaN(actualNum) && !isNaN(theoryNum)) {
          const op = rule.operator || '<='
          if (op === '>') status = actualNum > theoryNum ? 'pass' : 'fail'
          else if (op === '<') status = actualNum < theoryNum ? 'pass' : 'fail'
          else if (op === '>=') status = actualNum >= theoryNum ? 'pass' : 'fail'
          else if (op === '<=') status = actualNum <= theoryNum ? 'pass' : 'fail'
          else if (op === '==') {
            const tol = Number(rule.tolerance || 0)
            status = Math.abs(actualNum - theoryNum) <= tol ? 'pass' : 'fail'
          } else if (op === 'between') {
            const min = Number(rule.rangeMin || theoryNum)
            const max = Number(rule.rangeMax || theoryNum)
            status = (actualNum >= min && actualNum <= max) ? 'pass' : 'fail'
          }
        }
      }
    }
    map.set(name, { theoryValue, status, rule })
  }
  return map
})

const findImpactParamUnitCode = (impactName = '') => {
  const direct = moduleExecutionRows.value.find((row) => String(row.paramName || '').trim() === impactName)
  if (direct?.unitCode) return direct.unitCode
  const paramRow = parameterLookupMap.value.get(impactName)
  if (paramRow?.unitCode) return paramRow.unitCode
  const matrixRow = (rawMatrixData.value?.rows || []).find((r) => String(r.paramName || '').trim() === impactName)
  return matrixRow?.unitCode || ''
}

const findImpactParamDisplayName = (impactName = '') => {
  const direct = moduleExecutionRows.value.find((row) => String(row.paramName || '').trim() === impactName)
  if (direct?.displayName) return direct.displayName
  const paramRow = parameterLookupMap.value.get(impactName)
  if (paramRow?.displayName) return paramRow.displayName
  const matrixRow = (rawMatrixData.value?.rows || []).find((r) => String(r.paramName || '').trim() === impactName)
  return matrixRow?.displayName || impactName
}

/** 影响参数区间状态：key=关注指标 paramName，value=区间列表（由后端扫描引擎计算） */
const impactRangesState = ref({})
const impactRangesLoading = ref(new Set())
const impactRangeRequestTokens = new Map()
let impactRangeRefreshTimer = null

/** 组装后端校核扫描所需的数值参数（自动剥离 Hz / kW 等单位后缀） */
const buildNumericScanPayload = () => {
  const payload = {}
  const pushValue = (key, rawValue) => {
    const text = String(rawValue ?? '').trim()
    if (!text || key in payload) return
    let num = Number(text)
    if (!Number.isFinite(num)) {
      const stripped = text.replace(/[^\d.\-+eE]/g, '')
      num = Number(stripped)
    }
    if (Number.isFinite(num)) {
      payload[key] = num
    }
  }
  parameterRows.value.forEach((row) => {
    if (row.paramName) pushValue(row.paramName, row.value)
  })
  Object.entries(latestScope.value || {}).forEach(([key, value]) => pushValue(key, value))
  return payload
}

/** 状态卡最多展示的影响参数区间条数，超出部分折叠为 “+N” */
const MAX_IMPACT_RANGES_DISPLAY = 3

/** 截取状态卡可见的影响参数区间（避免卡片过高） */
const getVisibleImpactRanges = (row = {}) => {
  const ranges = Array.isArray(row?.impactRanges) ? row.impactRanges : []
  return ranges.slice(0, MAX_IMPACT_RANGES_DISPLAY)
}

/** 被折叠隐藏的影响参数区间数量 */
const getHiddenImpactCount = (row = {}) => {
  const ranges = Array.isArray(row?.impactRanges) ? row.impactRanges : []
  return Math.max(0, ranges.length - MAX_IMPACT_RANGES_DISPLAY)
}

/** 将后端扫描返回的 pass_ranges 归一化为前端展示结构 */
const normalizeScanPassRanges = (payload = {}, metricParamName = '') => {
  const impactName = String(payload?.scan_parameter || '').trim()
  const passRanges = Array.isArray(payload?.pass_ranges) ? payload.pass_ranges : []
  const result = []
  for (const range of passRanges) {
    const start = Number(range?.start)
    const end = Number(range?.end)
    if (!Number.isFinite(start) || !Number.isFinite(end)) continue
    result.push({
      paramName: impactName,
      displayName: findImpactParamDisplayName(impactName),
      min: start,
      max: end,
      rangeText: formatMetricRange(start, end, findImpactParamUnitCode(impactName))
    })
  }
  return result
}

/** 触发某关注指标的全部影响参数区间反推（调用后端真实公式扫描） */
const refreshMetricImpactRanges = async (paramName = '', impactParams = []) => {
  const versionId = String(selectedVersionId.value || '').trim()
  if (!versionId || !paramName || !Array.isArray(impactParams) || !impactParams.length) return
  const token = (impactRangeRequestTokens.get(paramName) || 0) + 1
  impactRangeRequestTokens.set(paramName, token)
  impactRangesLoading.value = new Set([...impactRangesLoading.value, paramName])
  try {
    // 组装数值参数可能抛错，必须在 try 内，保证 finally 一定能清掉加载态
    const numericPayload = buildNumericScanPayload()
    const nextRanges = []
    for (const impactName of impactParams) {
      const scanResult = await analyzeVerificationScan(
        {
          model_id: Number(versionId),
          result_name: paramName,
          scan_parameter: impactName,
          parameters: numericPayload,
          steps: 21
        },
        { timeout: 20000 }
      )
      nextRanges.push(...normalizeScanPassRanges(scanResult, paramName))
    }
    if (token === impactRangeRequestTokens.get(paramName)) {
      impactRangesState.value = {
        ...impactRangesState.value,
        [paramName]: nextRanges
      }
    }
  } catch (_error) {
    // 扫描失败（超时/后端错误）时清空区间，静默处理，不影响主链路
    if (token === impactRangeRequestTokens.get(paramName)) {
      impactRangesState.value = {
        ...impactRangesState.value,
        [paramName]: []
      }
    }
  } finally {
    if (token === impactRangeRequestTokens.get(paramName)) {
      const next = new Set(impactRangesLoading.value)
      next.delete(paramName)
      impactRangesLoading.value = next
    }
  }
}

/** 防抖刷新所有关注指标的影响参数区间 */
let impactRangeBatchRunning = false
let impactRangeBatchPending = false

const runImpactRangeRefresh = async () => {
  impactRangeRefreshTimer = null
  const versionId = String(selectedVersionId.value || '').trim()
  if (!versionId) return
  // 上一批扫描还在执行时，标记待办，结束后再补一次，避免并发堆积
  if (impactRangeBatchRunning) {
    impactRangeBatchPending = true
    return
  }
  impactRangeBatchRunning = true
  try {
    const targets = []
    for (const row of moduleExecutionRows.value) {
      const paramName = String(row.paramName || '').trim()
      const focusConfig = focusMetricConfigMap.value.get(paramName)
      const impactParams = Array.isArray(focusConfig?.impactParams) ? focusConfig.impactParams : []
      if (impactParams.length) {
        targets.push({ paramName, impactParams })
      }
    }
    await Promise.all(targets.map(({ paramName, impactParams }) => refreshMetricImpactRanges(paramName, impactParams)))
  } finally {
    impactRangeBatchRunning = false
    if (impactRangeBatchPending) {
      impactRangeBatchPending = false
      scheduleImpactRangeRefresh()
    }
  }
}

const scheduleImpactRangeRefresh = () => {
  if (impactRangeRefreshTimer) {
    clearTimeout(impactRangeRefreshTimer)
  }
  impactRangeRefreshTimer = setTimeout(runImpactRangeRefresh, 800)
}

watch(
  () => [
    selectedVersionId.value,
    moduleExecutionRows.value,
    focusMetricConfigMap.value,
    latestScope.value
  ],
  () => scheduleImpactRangeRefresh(),
  { deep: true, immediate: true }
)

const primaryResultRows = computed(() => {
  return moduleExecutionRows.value
    .filter((row) => {
      const name = String(row.paramName || '').trim()
      return focusMetricConfigMap.value.has(name)
    })
    .map((row) => {
      const paramName = String(row.paramName || '').trim()
      const focusConfig = focusMetricConfigMap.value.get(paramName) || createEmptyFocusMetricConfig(paramName)
      const missingDependencies = collectResultMissingDependencies(paramName, focusConfig)
      return {
        ...row,
        paramName,
        focusConfig,
        theoryValue: focusConfig.mode === 'compare' ? getMetricCurrentValue(focusConfig.targetParam) : null,
        verificationStatus: missingDependencies.length ? null : evaluateFocusMetricStatus(row.value, focusConfig),
        missingDependencies,
        ruleDescription: buildFocusMetricRuleDescription(focusConfig),
        impactRanges: impactRangesState.value[paramName] || [],
        impactRangesComputing: impactRangesLoading.value.has(paramName)
      }
    })
})

const primaryResultRowsLegacy = computed(() => {
  return moduleExecutionRows.value
    .filter((row) => {
      const name = String(row.paramName || '').trim()
      return verificationRulesMap.value.has(name)
    })
    .map((row) => {
      const name = String(row.paramName || '').trim()
      const vResult = verificationResultsMap.value.get(name) || {}
      
      const missingDependencies = []
      
      // 1. 检查公式依赖
      const formulaRow = activeModuleFormulaRows.value.find(r => String(r.name || '').trim() === name)
      if (formulaRow && formulaRow.variables) {
        Object.keys(formulaRow.variables).forEach((paramName) => {
          const normalizedName = String(paramName || '').trim()
          const parameterRow = parameterLookupMap.value.get(normalizedName)
          const resultRow = resultRowMap.value.get(normalizedName)
          const val = parameterRow?.value ?? resultRow?.value ?? String(latestScope.value?.[normalizedName] ?? '')
          if (String(val).trim() === '') {
            const dName = parameterRow?.displayName || resultRow?.displayName || normalizedName
            if (!missingDependencies.includes(dName)) missingDependencies.push(dName)
          }
        })
      }
      
      // 2. 检查校核理论值依赖
      if (vResult.rule && vResult.rule.targetParam) {
        const targetName = String(vResult.rule.targetParam).trim()
        const parameterRow = parameterLookupMap.value.get(targetName)
        const resultRow = resultRowMap.value.get(targetName)
        const val = parameterRow?.value ?? resultRow?.value ?? String(latestScope.value?.[targetName] ?? '')
        if (String(val).trim() === '') {
          const dName = parameterRow?.displayName || resultRow?.displayName || targetName
          if (!missingDependencies.includes(dName)) missingDependencies.push(dName)
        }
      }
      
      return {
        ...row,
        theoryValue: vResult.theoryValue,
        verificationRule: vResult.rule,
        verificationStatus: vResult.status,
        missingDependencies
      }
    })
})



const resultRowMap = computed(() => {
  return new Map(
    moduleExecutionRows.value.map((row) => [String(row.paramName || '').trim(), row])
  )
})

const formulaScenes = computed(() => {
  return (activeModule.value?.scenes || []).map((scene) => {
    let rows = scene.rows || []
    
    // Inject new draft if it belongs to this scene
    if (activeFormulaDraft.value?._isNewDraft && 
        activeFormulaDraft.value.scene_code === scene.sceneCode &&
        activeFormulaDraft.value.module_code === activeModule.value?.moduleCode) {
      rows = [...rows, activeFormulaDraft.value]
    }

    return {
      ...scene,
      rows: rows.map((row, index) => {
        const rowKey = row._rowKey || `${activeModule.value?.moduleCode || 'module'}:${scene.sceneCode || 'scene'}:${row.id || row.name || index}`
        const dependencies = getFormulaDependencyNames(row).map((paramName) => {
          const normalizedName = String(paramName || '').trim()
          const parameterRow = parameterLookupMap.value.get(normalizedName)
          const resultRow = resultRowMap.value.get(normalizedName)
          return {
            parameterId: parameterRow?.parameterId || resultRow?.parameterId || 0,
            paramCode: parameterRow?.paramCode || resultRow?.paramCode || '',
            paramName: normalizedName,
            displayName: parameterRow?.displayName || resultRow?.displayName || normalizedName,
            unitCode: parameterRow?.unitCode || resultRow?.unitCode || '',
            value: parameterRow?.value ?? resultRow?.value ?? String(latestScope.value?.[normalizedName] ?? ''),
            source: parameterRow?.source || resultRow?.source || (moduleFormulaNames.value.has(normalizedName) ? 'snapshot' : 'empty')
          }
        })
        const missingDependencies = dependencies
          .filter((dependency) => String(dependency.value ?? '').trim() === '')
          .map((dependency) => dependency.displayName)

        const unifiedStatus = resolveUnifiedVerificationStatus(row)

        return {
          ...row,
          sceneCode: scene.sceneCode || '',
          sceneName: scene.sceneName || '未命名场景',
          _rowKey: rowKey,
          dependencies,
          missingDependencies,
          resultRow: resultRowMap.value.get(String(row.name || '').trim()) || null,
          description: row.description || '',
          resources: Array.isArray(row.resources) ? row.resources : [],
          verificationStatus: unifiedStatus
        }
      })
    }
  })
})

const activeFormula = computed(() => {
  const allRows = formulaScenes.value.flatMap(s => s.rows)
  const matched = allRows.find(row => String(row._rowKey || '') === String(editingFormulaKey.value || ''))
  if (matched) return matched
  return activeFormulaDraft.value?._isNewDraft ? activeFormulaDraft.value : {}
})

const activeFormulaContext = computed(() => {
  const base = activeFormula.value || {}
  const draft = activeFormulaDraft.value || {}
  const expression = draft.expression ?? base.expression ?? ''
  const variables = resolveFormulaVariablesFromExpression(expression, draft.variables || base.variables || {})
  return {
    ...base,
    ...draft,
    expression,
    variables
  }
})

const getFormulaDependencyNames = (row = {}) => {
  return Object.keys(
    resolveFormulaVariablesFromExpression(
      String(row?.expression || '').trim(),
      row?.variables || {}
    )
  )
    .map((name) => String(name || '').trim())
    .filter(Boolean)
}

const autocompleteKeyword = computed(() => {
  if (formulaCompositionActive.value) return null
  
  const expr = String(activeFormulaContext.value?.expression || '')
  if (!expr.startsWith('=')) return null
  if (formulaCursorStart.value === 0) return null

  return resolveFormulaAutocompleteKeyword({
    expression: expr,
    selectionStart: formulaCursorStart.value
  })
})

const autocompleteSections = computed(() => {
  if (autocompleteKeyword.value === null) return []
  
  const allIntermediateSourceRows = buildExecutionIntermediateRows({
    formulaRows: activeModuleFormulaRows.value,
    latestResults: latestResults.value,
    latestScope: latestScope.value
  })
  return buildFormulaAutocompleteSections({
    keyword: autocompleteKeyword.value,
    parameterRows: [...parameterRows.value, ...allIntermediateSourceRows],
    lookupItems: lookupItems.value
  })
})

const activeFormulaArgumentHint = computed(() =>
  resolveFormulaArgumentHint({
    expression: String(activeFormulaContext.value?.expression || ''),
    selectionStart: formulaCursorStart.value
  })
)

const mainTableRows = computed(() => {
  return formulaScenes.value.flatMap((scene) => {
    const sceneRows = (scene.rows || []).map((row) => {
      const rowName = String(row.name || '').trim()
      let metricType = 'normal'
      if (focusMetricConfigMap.value.has(rowName)) metricType = 'focus'
      else if (selectionParamConfigMap.value.has(rowName)) metricType = 'selection'
      return {
        rowType: row.resultRow ? 'result' : 'formula',
        key: row._rowKey,
        name: row.name || '未命名公式',
        expression: row.expression || '',
        value: resolveFormulaMetric(row) || '-',
        meta: '',
        raw: row,
        verificationStatus: row.verificationStatus,
        metricType
      }
    })
    return [
      {
        rowType: 'group',
        key: `group:${scene.sceneCode}`,
        label: scene.sceneName || '未命名场景',
        moduleCode: scene.moduleCode,
        sceneCode: scene.sceneCode,
        sceneType: scene.sceneType,
        moduleName: scene.moduleName,
        sceneName: scene.sceneName
      },
      ...sceneRows
    ]
  })
})

const activeFlowGraph = computed(() => {
  return buildWorkbenchCalculationFlow({
    moduleCode: activeModuleCode.value,
    focusedFormulaName: '',
    formulaRows: activeModuleFormulaRows.value,
    parameterRows: parameterRows.value,
    latestResults: latestResults.value,
    latestScope: latestScope.value
  })
})

const handleFormulaSelect = (row) => {
  if (row.raw) {
    if (row.raw._isNewDraft) return
    
    const key = String(row.raw._rowKey || '')
    
    // Try to insert into currently editing formula, but don't insert itself
    if (editingFormulaKey.value && key !== editingFormulaKey.value) {
      const insertion = resolveParameterInsertionDraft({
        row: row.raw,
        editingFormulaKey: editingFormulaKey.value,
        editingFormulaField: editingFormulaField.value,
        activeFormulaDraft: activeFormulaDraft.value,
        formulaCursorStart: formulaCursorStart.value
      })
      
      if (insertion.inserted) {
        activeFormulaDraft.value = {
          ...activeFormulaDraft.value,
          expression: insertion.nextExpression
        }
        formulaCursorStart.value = insertion.nextCursorStart
        if (autoRunTimer) {
          clearTimeout(autoRunTimer)
          autoRunTimer = null
        }
        return
      }
    }

    explanationTarget.value = { type: 'formula', key }
  }
}

const handleFormulaEdit = (rawRow, field = 'expression') => {
  if (rawRow) {
    if (rawRow._isNewDraft) return
    const key = String(rawRow._rowKey || '')
    
    if (editingFormulaKey.value && editingFormulaKey.value !== key) {
      // Do not allow editing another formula while one is already being edited
      ElMessage.warning('请先保存或取消当前正在编辑的公式')
      return
    }
    
    explanationTarget.value = { type: 'formula', key }
    
    if (editingFormulaKey.value === key) {
      // Just switch the editing field without resetting the draft
      editingFormulaField.value = field
    } else {
      // Start editing a new row
      editingFormulaKey.value = key
      editingFormulaField.value = field
      activeFormulaDraft.value = { ...rawRow }
    }
  }
}

const handleOpenExplanation = (row) => {
  handleFormulaSelect(row)
}

const handleFormulaDraftChange = ({ field, value }) => {
  activeFormulaDraft.value = {
    ...activeFormulaDraft.value,
    [field]: value
  }
}

const handleFormulaCancel = () => {
  if (activeFormulaDraft.value?._isNewDraft) {
    editingFormulaKey.value = ''
    editingFormulaField.value = ''
    activeFormulaDraft.value = {}
    return
  }
  editingFormulaKey.value = ''
  editingFormulaField.value = ''
  activeFormulaDraft.value = {}
}

const handleFormulaBlur = (rowKey) => {
  if (editingFormulaKey.value !== rowKey) return

  const isNew = activeFormulaDraft.value?._isNewDraft
  if (isNew) {
    // If it's a new draft and it's empty, just cancel
    if (!String(activeFormulaDraft.value?.name || '').trim() && !String(activeFormulaDraft.value?.expression || '').trim()) {
      handleFormulaCancel()
      return
    }
  } else {
    // Check if modified
    const original = formulaScenes.value.flatMap(s => s.rows).find(r => r._rowKey === rowKey)
    if (original) {
      const nameUnchanged = String(original.name || '').trim() === String(activeFormulaDraft.value?.name || '').trim()
      const exprUnchanged = String(original.expression || '').trim() === String(activeFormulaDraft.value?.expression || '').trim()
      if (nameUnchanged && exprUnchanged) {
        handleFormulaCancel()
        return
      }
    }
  }

  // Otherwise try to save
  handleFormulaSave()
}

const handleFormulaEditorSelectionChange = ({ start = 0, isComposing = false } = {}) => {
  formulaCursorStart.value = Number(start || 0)
  formulaCompositionActive.value = Boolean(isComposing)
}

const handleFormulaSave = async () => {
  if (!selectedVersionId.value) {
    ElMessage.warning('请先选择具体型号')
    return
  }
  if (!String(activeFormulaDraft.value?.name || '').trim()) {
    ElMessage.warning('请填写公式名称')
    return
  }
  if (!String(activeFormulaDraft.value?.expression || '').trim()) {
    ElMessage.warning('请填写公式表达式')
    return
  }

  const savingKey = editingFormulaKey.value
  formulaSaving.value = true
  try {
    const payload = {
      id: activeFormulaDraft.value.id && activeFormulaDraft.value.id > 0 ? activeFormulaDraft.value.id : null,
      model_id: Number(selectedVersionId.value),
      module_code: String(activeFormulaDraft.value.module_code || activeModuleCode.value || 'power_calc').trim(),
      module_name: String(activeFormulaDraft.value.module_name || '未命名模块').trim(),
      scene_code: String(activeFormulaDraft.value.scene_code || activeFormulaDraft.value.sceneCode || 'power').trim(),
      scene_name: String(activeFormulaDraft.value.scene_name || activeFormulaDraft.value.sceneName || '未命名场景').trim(),
      name: String(activeFormulaDraft.value.name || '').trim(),
      expression: String(activeFormulaDraft.value.expression || '').trim(),
      canonical_expression: String(activeFormula.value?.canonical_expression || '').trim(),
      variables: activeFormulaContext.value.variables || {},
      source_type: 'manual',
      description: String(activeFormulaDraft.value.description || '').trim(),
      resources: activeFormulaDraft.value.resources || [],
      output_flag: activeFormulaDraft.value.output_flag || 'auto'
    }

    const localLookupResolver = (lookupName) => {
      const matched = lookupItems.value.find((item) => String(item.lookup_name || '') === String(lookupName || ''))
      if (!matched) throw new Error(`附录“${lookupName}”不存在`)
      return 1
    }
    const localCurveResolver = (lookupName) => {
      const matched = lookupItems.value.find((item) => String(item.lookup_name || '') === String(lookupName || ''))
      if (!matched) throw new Error(`曲线表“${lookupName}”不存在`)
      return 1
    }

    // Attempt to evaluate formula to check for syntax errors and derive variable bindings.
    const existingVariables = Object.entries(payload.variables || {}).reduce((result, [name, unitCode]) => {
      const normalizedName = String(name || '').trim()
      if (!normalizedName) {
        return result
      }
      result[normalizedName] = typeof unitCode === 'string' ? unitCode : ''
      return result
    }, {})
    const extractedVariableNames = []
    const sampleScope = Object.fromEntries(Object.keys(existingVariables).map((name) => [name, 1]))

    evaluateFormulaExpression(payload.expression, sampleScope, {
      availableVariableNames: Object.keys(existingVariables),
      lookupResolver: localLookupResolver,
      curveResolver: localCurveResolver,
      defaultMissingValue: 1,
      onVariableExtracted: (name) => extractedVariableNames.push(name)
    })

    payload.variables = extractedVariableNames.reduce((result, name) => {
      const normalizedName = String(name || '').trim()
      if (!normalizedName) {
        return result
      }
      result[normalizedName] = existingVariables[normalizedName] || ''
      return result
    }, {})

    await saveWorkbenchFormula(selectedVersionId.value, payload)
    await loadVersionContext(activeModuleCode.value)
    
    if (editingFormulaKey.value === savingKey) {
      editingFormulaKey.value = ''
      editingFormulaField.value = ''
      activeFormulaDraft.value = {}
    }
    
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '保存失败')
  } finally {
    formulaSaving.value = false
  }
}

const handleFormulaDelete = async (row) => {
  if (!selectedVersionId.value || !row?.id || row?._isNewDraft) return
  
  try {
    await ElMessageBox.confirm(
      `将永久删除公式“${row.displayName || row.name || '未命名公式'}”，且不可恢复。是否继续？`,
      '删除公式',
      { type: 'warning' }
    )
    await deleteWorkbenchFormula(selectedVersionId.value, row.id)
    await loadVersionContext(activeModuleCode.value)
    ElMessage.success('公式已删除')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除公式失败')
    }
  }
}

const handleFormulaCreate = (scene) => {
  const newKey = `draft:new:${scene.moduleCode}:${scene.sceneCode}`
  editingFormulaKey.value = newKey
  editingFormulaField.value = 'all' // Support editing both when creating new formula
  activeFormulaDraft.value = {
    id: 0,
    model_id: Number(selectedVersionId.value || 0),
    module_code: scene.moduleCode || activeModuleCode.value,
    module_name: scene.moduleName || '未命名模块',
    scene_code: scene.sceneCode,
    scene_name: scene.sceneName || '未命名场景',
    name: '',
    expression: '',
    variables: {},
    source_type: 'manual',
    _isNewDraft: true,
    _rowKey: newKey
  }
}

const buildWorkbenchSaveRows = (rows = []) => rows.map((row) => ({
  version_id: Number(selectedVersionId.value),
  parameter_id: Number(row.parameterId || 0),
  param_code: String(row.paramCode || '').trim(),
  param_name: String(row.paramName || '').trim(),
  param_value: String(row.value || '').trim(),
  unit_code: String(row.unitCode || '').trim(),
  value_type: String(row.valueType || 'basic').trim(),
  description: String(row.description || '').trim(),
  remark: buildParameterRemark(row)
}))

const saveDirtyParameterRows = async ({ runCalc = false } = {}) => {
  if (!selectedFamilyId.value || !selectedVersionId.value) return
  const rowsToSave = parameterRows.value.filter((row) =>
    (row.dirty || row.pendingCreate) && shouldPersistParameterRow(row)
  )
  if (!rowsToSave.length) {
    if (runCalc) {
      await runCalculation({ silent: true, showSuccess: false })
    }
    return
  }
  await saveWorkbenchParameters({
    family_id: Number(selectedFamilyId.value),
    module_code: String(activeModuleCode.value || '').trim(),
    rows: buildWorkbenchSaveRows(rowsToSave)
  })
  parameterRows.value.forEach((row) => {
    if (rowsToSave.some((saved) => saved._tempId === row._tempId || saved.paramName === row.paramName)) {
      row.dirty = false
      row.pendingCreate = false
    }
  })
  if (runCalc) {
    await runCalculation({ silent: true, showSuccess: false })
  }
}

const handleExplanationUpdate = async (data) => {
  if (explanationTarget.value?.type === 'parameter') {
    const targetIndex = parameterRows.value.findIndex((row) => String(row.paramName || '').trim() === String(explanationTarget.value.key || '').trim())
    if (targetIndex < 0) return
    const existingRow = parameterRows.value[targetIndex]
    const nextProvenance = {
      ...normalizeParameterProvenance(existingRow.provenance || existingRow.remark || null),
      source_type: data.source_type || 'manual',
      source_note: data.source_note || '',
      resources: normalizeResourceRows(data.resources || [])
    }
    parameterRows.value[targetIndex] = {
      ...existingRow,
      description: data.summary || '',
      resources: nextProvenance.resources,
      provenance: nextProvenance,
      remark: buildParameterRemark({
        ...existingRow,
        provenance: nextProvenance,
        resources: nextProvenance.resources
      }),
      dirty: true,
      source: 'draft'
    }
    try {
      await saveDirtyParameterRows({ runCalc: true })
      ElMessage.success('参数说明已保存')
    } catch (error) {
      ElMessage.error(error?.response?.data?.detail || '参数说明保存失败')
    }
    return
  }

  let targetFormulaRow = null
  
  if (explanationTarget.value?.type === 'formula') {
    const key = explanationTarget.value.key
    targetFormulaRow = mainTableRows.value.find((r) => r.key === key)?.raw
  } else if (explanationTarget.value?.type === 'result') {
    const paramName = explanationTarget.value.key
    targetFormulaRow = activeModuleFormulaRows.value.find(r => String(r.name || '').trim() === paramName)
  }

  if (targetFormulaRow) {
    // If we are not currently editing this formula, we need to set it as the active draft
    // so that handleFormulaSave can save it properly.
    const isCurrentlyEditing = editingFormulaKey.value === targetFormulaRow._rowKey
    
    if (!isCurrentlyEditing) {
      editingFormulaKey.value = targetFormulaRow._rowKey
      editingFormulaField.value = 'explanation'
      // Need to populate activeFormulaDraft with the full row data before updating
      activeFormulaDraft.value = { ...targetFormulaRow }
    }
    
    const hiddenFocusResources = normalizeResourceRows(targetFormulaRow.resources || []).filter((resource) => resource.type === 'focus_metric_config')
    activeFormulaDraft.value = {
      ...activeFormulaDraft.value,
      description: data.summary,
      resources: [...normalizeResourceRows(data.resources || []), ...hiddenFocusResources],
      output_flag: data.output_flag
    }
    
    // Force update the local row immediately so UI reflects changes before API returns
    targetFormulaRow.description = data.summary
    targetFormulaRow.resources = [...normalizeResourceRows(data.resources || []), ...hiddenFocusResources]
    targetFormulaRow.output_flag = data.output_flag
    
    // Also update the original row in formulaScenes to ensure reactivity
    for (const scene of formulaScenes.value) {
      const row = scene.rows.find(r => r._rowKey === targetFormulaRow._rowKey)
      if (row) {
        row.description = data.summary
        row.resources = [...normalizeResourceRows(data.resources || []), ...hiddenFocusResources]
        row.output_flag = data.output_flag
        break
      }
    }
    
    // Also update activeModuleFormulaRows to ensure reactivity for result cards
    const activeRow = activeModuleFormulaRows.value.find(r => r._rowKey === targetFormulaRow._rowKey)
    if (activeRow) {
      activeRow.description = data.summary
      activeRow.resources = [...normalizeResourceRows(data.resources || []), ...hiddenFocusResources]
      activeRow.output_flag = data.output_flag
    }
    
    await handleFormulaSave()
  }
}

const focusMetricCompareOptions = computed(() => {
  const currentMetricName = String(focusMetricDraft.value.metricName || '').trim()
  return allAvailableParameters.value.filter((option) => String(option.paramName || '').trim() !== currentMetricName)
})

/** 选中的对比参数在所有型号下的值区间 */
const selectedParameterRange = computed(() => {
  const target = String(focusMetricDraft.value.targetParam || '').trim()
  if (!target || !rawMatrixData.value?.rows) return null
  const row = rawMatrixData.value.rows.find((r) => String(r.paramName || '').trim() === target)
  if (!row?.values) return null
  const vals = Object.values(row.values).filter((v) => v !== '' && v !== null && v !== undefined).map(Number)
  if (vals.length === 0) return null
  return { min: Math.min(...vals), max: Math.max(...vals), count: vals.length }
})

const openFocusMetricConfig = (row = {}) => {
  const metricName = String(row.paramName || row.name || '').trim()
  if (!metricName) return
  const targetFormulaRow = activeModuleFormulaRows.value.find((item) => String(item.name || '').trim() === metricName)
  if (!targetFormulaRow) {
    ElMessage.warning('当前关注指标未找到对应公式，暂时无法配置')
    return
  }
  const existingConfig = focusMetricConfigMap.value.get(metricName) || createEmptyFocusMetricConfig(metricName)
  focusMetricEditingKey.value = String(targetFormulaRow._rowKey || '')
  focusMetricDraft.value = normalizeFocusMetricConfig(existingConfig, metricName)
  focusMetricDialogVisible.value = true
}

const saveFormulaRowPatch = async (targetFormulaRow, patch = {}) => {
  if (!targetFormulaRow?._rowKey) return
  const wasEditing = editingFormulaKey.value === targetFormulaRow._rowKey
  if (!wasEditing) {
    editingFormulaKey.value = targetFormulaRow._rowKey
    editingFormulaField.value = 'explanation'
  }
  activeFormulaDraft.value = {
    ...targetFormulaRow,
    ...patch
  }
  await handleFormulaSave()
}

const handleFormulaMetricTypeChange = async ({ row, value }) => {
  const rowKey = String(row?._rowKey || '').trim()
  if (!rowKey) return
  const targetFormulaRow = activeModuleFormulaRows.value.find((item) => String(item._rowKey || '').trim() === rowKey)
  if (!targetFormulaRow) return
  const normalizedResources = normalizeResourceRows(targetFormulaRow.resources || [])
  const otherResources = normalizedResources.filter((resource) => resource.type !== 'focus_metric_config' && resource.type !== 'selection_param_config')
  const nextResources = [...otherResources]
  if (value === 'focus') {
    nextResources.push(normalizeFocusMetricConfig(normalizedResources.find((resource) => resource.type === 'focus_metric_config'), String(targetFormulaRow.name || '').trim()))
  } else if (value === 'selection') {
    nextResources.push(normalizeSelectionParamConfig(normalizedResources.find((resource) => resource.type === 'selection_param_config'), String(targetFormulaRow.name || '').trim()))
  }
  try {
    await saveFormulaRowPatch(targetFormulaRow, { resources: nextResources })
  } catch (_error) {
  }
}

const handleFocusMetricConfigSave = async () => {
  const rowKey = String(focusMetricEditingKey.value || '').trim()
  const targetFormulaRow = activeModuleFormulaRows.value.find((item) => String(item._rowKey || '').trim() === rowKey)
  if (!targetFormulaRow) {
    ElMessage.warning('未找到对应公式，无法保存关注指标配置')
    return
  }
  const nextConfig = normalizeFocusMetricConfig(focusMetricDraft.value, String(targetFormulaRow.name || '').trim())
  if (nextConfig.mode === 'compare' && !nextConfig.targetParam) {
    ElMessage.warning('请选择对比参数')
    return
  }
  if (nextConfig.mode === 'range' && nextConfig.rangeMin === '' && nextConfig.rangeMax === '') {
    ElMessage.warning('请至少填写一个区间边界')
    return
  }
  const normalizedResources = normalizeResourceRows(targetFormulaRow.resources || [])
  const otherResources = normalizedResources.filter((resource) => resource.type !== 'focus_metric_config')
  const metricName = String(targetFormulaRow.name || '').trim()
  try {
    await saveFormulaRowPatch(targetFormulaRow, {
      resources: [...otherResources, nextConfig]
    })
    // 保存到型号级后端独立配置（各型号一份，互不影响）
    if (selectedVersionId.value) {
      const nextBackend = { ...(backendFocusMetricConfigs.value || {}) }
      nextBackend[metricName] = nextConfig
      await saveFocusMetricConfigs(selectedVersionId.value, nextBackend)
      backendFocusMetricConfigs.value = nextBackend
    }
    // 同时保存到型号级 localStorage（不同型号可独立配置）
    saveLocalFocusMetricConfig(selectedVersionId.value, metricName, nextConfig)
    focusMetricDialogVisible.value = false
  } catch (_error) {
  }
}

const resolvePrimaryMetricReference = (row = {}) => {
  return resolveFocusMetricReferenceText(row.focusConfig, row.unitCode)
}

const handleFlowNodeSelect = (node = {}) => {
  flowDisplayMode.value = 'default'
  activeFlowNodeId.value = String(node?.id || '')
}

const handleFlowNodeDrag = ({ nodeId, x, y }) => {
  const node = activeFlowGraph.value.nodes.find(n => n.id === nodeId)
  if (node) {
    node.x = x
    node.y = y
  }
}

const handleFlowViewportChange = (nextViewport = {}) => {
  flowViewportState.value = {
    zoom: Number(nextViewport?.zoom || 1),
    center: Array.isArray(nextViewport?.center) ? [...nextViewport.center] : ['50%', '50%']
  }
}

const resolveDefaultFlowNode = () => {
  const nodes = Array.isArray(activeFlowGraph.value?.nodes) ? activeFlowGraph.value.nodes : []
  if (!nodes.length) return null

  if (explanationTarget.value.type === 'result') {
    const matchedResultNode = nodes.find((node) => String(node?.name || '').trim() === String(explanationTarget.value.key || '').trim())
    if (matchedResultNode) return matchedResultNode
  }

  if (explanationTarget.value.type === 'formula') {
    const formulaRow = activeModuleFormulaRows.value.find((row) => String(row._rowKey || '').trim() === String(explanationTarget.value.key || '').trim())
    const formulaName = String(formulaRow?.name || '').trim()
    if (formulaName) {
      const matchedFormulaNode = nodes.find((node) => String(node?.name || '').trim() === formulaName)
      if (matchedFormulaNode) return matchedFormulaNode
    }
  }

  return nodes.find((node) => node.nodeType === 'result')
    || nodes.find((node) => node.nodeType === 'formula')
    || nodes[0]
}

watch(
  () => [workspaceMode.value, activeFlowGraph.value?.nodes?.length || 0, activeModuleCode.value, explanationTarget.value.type, explanationTarget.value.key],
  ([mode]) => {
    if (mode !== 'flow') return
    const defaultNode = resolveDefaultFlowNode()
    if (!defaultNode) {
      activeFlowNodeId.value = ''
      return
    }
    if (!activeFlowNodeId.value || !activeFlowGraph.value?.nodes?.some((node) => String(node?.id || '') === String(activeFlowNodeId.value || ''))) {
      activeFlowNodeId.value = String(defaultNode.id || '')
    }
    flowDisplayMode.value = 'default'
  },
  { immediate: true }
)

const editingSceneCode = ref('')
const sceneSaving = ref(false)

const createSceneDialogVisible = ref(false)
const createSceneForm = ref({
  module: null,
  sceneName: '',
  sceneType: 'calc'
})
const parameterGroupDialogVisible = ref(false)
const CUSTOM_GROUP_TOKEN = '__custom_group__'
const parameterGroupDraft = ref({
  row: null,
  paramName: '',
  displayName: '',
  targetGroupKey: '',
  customGroupLabel: ''
})
const renameGroupDialogVisible = ref(false)
const renameGroupDraft = ref({
  group: null,
  groupKey: '',
  oldLabel: '',
  newLabel: ''
})

const handleSceneCreate = (module) => {
  if (!selectedVersionId.value) {
    return
  }
  if (!module) {
    ElMessage.warning('请先选择或创建一个模块')
    return
  }
  createSceneForm.value = {
    module,
    sceneName: '',
    sceneType: 'calc'
  }
  createSceneDialogVisible.value = true
}

const confirmCreateScene = async () => {
  const module = createSceneForm.value.module
  try {
    sceneSaving.value = true
    const created = await createWorkbenchFormulaScene(selectedVersionId.value, {
      module_code: module.moduleCode,
      scene_name: createSceneForm.value.sceneName || '未命名场景',
      scene_type: createSceneForm.value.sceneType
    })
    
    // 更新本地状态
    const moduleIndex = modules.value.findIndex(m => m.moduleCode === module.moduleCode)
    if (moduleIndex !== -1) {
      modules.value[moduleIndex].scenes = [
        ...modules.value[moduleIndex].scenes,
        {
          moduleCode: created.module_code,
          moduleName: created.module_name,
          sceneCode: created.scene_code,
          sceneName: created.scene_name,
          sceneType: created.scene_type || createSceneForm.value.sceneType,
          rows: []
        }
      ]
    }
    
    ElMessage.success('计算块创建成功')
    createSceneDialogVisible.value = false
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '创建计算块失败')
  } finally {
    sceneSaving.value = false
  }
}

const beginSceneEditing = ({ sceneCode }) => {
  editingSceneCode.value = sceneCode
}

const cancelSceneEditing = () => {
  editingSceneCode.value = ''
}

const handleSceneRenameConfirm = async ({ moduleCode, sceneCode, nextName }) => {
  if (!selectedVersionId.value) return
  const trimmedName = String(nextName || '').trim()
  if (!trimmedName) {
    cancelSceneEditing()
    return
  }

  sceneSaving.value = true
  try {
    const renamed = await renameWorkbenchFormulaScene(
      selectedVersionId.value,
      moduleCode,
      sceneCode,
      { scene_name: trimmedName }
    )
    
    // Update local state
    const moduleIndex = modules.value.findIndex(m => m.moduleCode === moduleCode)
    if (moduleIndex !== -1) {
      const sceneIndex = modules.value[moduleIndex].scenes.findIndex(s => s.sceneCode === sceneCode)
      if (sceneIndex !== -1) {
        modules.value[moduleIndex].scenes[sceneIndex].sceneName = renamed?.scene_name || trimmedName
      }
    }
    
    cancelSceneEditing()
    ElMessage.success('计算块名称已更新')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '计算块改名失败')
  } finally {
    sceneSaving.value = false
  }
}

const handleSceneDelete = async ({ moduleCode, sceneCode }) => {
  if (!selectedVersionId.value || !moduleCode || !sceneCode) return
  
  try {
    await ElMessageBox.confirm(
      `将永久删除该计算块及其包含的所有公式，且不可恢复。是否继续？`,
      '删除计算块',
      { type: 'warning' }
    )
    await deleteWorkbenchFormulaScene(selectedVersionId.value, moduleCode, sceneCode)
    
    // Update local state
    const moduleIndex = modules.value.findIndex(m => m.moduleCode === moduleCode)
    if (moduleIndex !== -1) {
      modules.value[moduleIndex].scenes = modules.value[moduleIndex].scenes.filter(s => s.sceneCode !== sceneCode)
    }
    
    ElMessage.success('计算块已删除')
    await loadVersionContext(moduleCode)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除计算块失败')
    }
  }
}
// 智能选型持久化状态
const currentEquipment = ref(null)

const handleClearEquipment = () => {
  const versionId = String(selectedVersionId.value || '').trim()
  currentEquipment.value = null
  if (versionId) {
    localStorage.removeItem(getCurrentEquipmentStorageKey(versionId))
    localStorage.removeItem(getEquipmentRowsStorageKey(versionId))
  }
  parameterRows.value = parameterRows.value.filter(
    (row) => !(row.valueType === 'equipment' || String(row.paramName || '').startsWith('电机_') || String(row.paramName || '').startsWith('减速机_'))
  )
}

const formatMotorModelForLookup = (motorModel) => {
  const normalizedModel = String(motorModel || '').trim()
  if (!normalizedModel) return ''
  const match = normalizedModel.match(/([A-Z0-9]+)(\d{2,3}[SMLH]?[A-Z]*)(\d+)/i)
  if (!match) return normalizedModel
  return normalizedModel.replace(/([A-Z]+)(\d+[SMLH]?[A-Z]*?)(\d)$/i, '$1 $2 $3')
}

const resolveExactMotorDetails = async (equipment) => {
  const baseMotor = {
    ...(equipment?.item?.motor_params || {}),
    ...(equipment?.motor_params || {})
  }
  const baseSpecs = equipment?.item?.specs || equipment?.specs || {}
  const motorModel = String(baseMotor.model || baseSpecs.motor || '').trim()
  if (!motorModel) return baseMotor

  try {
    const lookupModel = formatMotorModelForLookup(motorModel)
    const dataArray = await fetchMotorCatalogItems(lookupModel)
    if (!Array.isArray(dataArray) || !dataArray.length) return baseMotor
    const exactMatches = dataArray.filter((item) => {
      const candidateName = String(item?.model_name || '').trim()
      return candidateName === lookupModel || candidateName.replace(/\s+/g, '') === motorModel.replace(/\s+/g, '')
    })
    const matchedMotor = exactMatches.find((item) => Number(item?.specs?.frequency || 0) === 50)
      || exactMatches[0]
      || dataArray.find((item) => Number(item?.specs?.frequency || 0) === 50)
      || dataArray[0]
    if (!matchedMotor) return baseMotor

    const specs = matchedMotor.specs || {}
    return {
      ...baseMotor,
      model: motorModel.replace(/\s+/g, ''),
      series: specs.series || baseMotor.series || 'DRN',
      efficiency_class: specs.efficiency_class || baseMotor.efficiency_class || 'IE3',
      power: Number(specs.power_kw ?? baseMotor.power ?? 0) || baseMotor.power,
      poles: Number(specs.poles ?? baseMotor.poles ?? 0) || baseMotor.poles || 4,
      speed: Number(specs.speed_rpm ?? baseMotor.speed ?? 0) || baseMotor.speed,
      torque: Number(specs.torque_nm ?? baseMotor.torque ?? baseMotor.torque_nm ?? 0) || baseMotor.torque || baseMotor.torque_nm,
      current: Number(specs.current_a ?? baseMotor.current ?? baseMotor.current_a ?? 0) || baseMotor.current || baseMotor.current_a,
      power_factor: Number(specs.power_factor ?? baseMotor.power_factor ?? 0) || baseMotor.power_factor,
      efficiency_100: Number(specs.efficiency_percent ?? baseMotor.efficiency_100 ?? 0) || baseMotor.efficiency_100,
      start_current_ratio_m1: Number(specs.starting_current_ratio_m1 ?? baseMotor.start_current_ratio_m1 ?? 0) || baseMotor.start_current_ratio_m1,
      start_current_ratio_m2: Number(specs.starting_current_ratio_m2 ?? baseMotor.start_current_ratio_m2 ?? 0) || baseMotor.start_current_ratio_m2,
      brake_model: specs.brake_model || baseMotor.brake_model,
      mass: Number(specs.mass_kg ?? baseMotor.mass ?? baseMotor.weight ?? 0) || baseMotor.mass || baseMotor.weight,
      inertia: Number(specs.inertia_10_4_kgm2 ?? baseMotor.inertia ?? 0) || baseMotor.inertia,
      voltage: [specs.voltage, specs.frequency ? `${specs.frequency}Hz` : ''].filter(Boolean).join('/') || baseMotor.voltage,
      protection: specs.protection || baseMotor.protection || specs.protection_class || 'IP55'
    }
  } catch (error) {
    console.error('获取精确电机详情失败:', error)
    return baseMotor
  }
}

const buildEquipmentParameterMappings = (equipment) => {
  const motor = equipment?.motor_params || equipment?.item?.motor_params || {}
  const reducer = equipment?.reducer_params || equipment?.item?.reducer_params || {}
  let motorFreq = ''
  if (motor.voltage) {
    const freqMatch = String(motor.voltage).match(/(\d+)Hz/i)
    if (freqMatch) motorFreq = freqMatch[1]
  }

  return [
    { name: '电机_型号', val: motor.model, type: 'equipment' },
    { name: '电机_系列', val: motor.series || 'DRN', type: 'equipment' },
    { name: '电机_能效等级', val: motor.efficiency_class || 'IE3', type: 'equipment' },
    { name: '电机_额定功率', val: motor.power, type: 'equipment', unitCode: 'kW' },
    { name: '电机_极数', val: motor.poles || 4, type: 'equipment', unitCode: '极' },
    { name: '电机_额定转速', val: motor.speed, type: 'equipment', unitCode: 'r/min' },
    { name: '电机_额定转矩', val: motor.torque || motor.torque_nm || 142, type: 'equipment', unitCode: 'Nm' },
    { name: '电机_额定电流', val: motor.current || motor.current_a || 40.5, type: 'equipment', unitCode: 'A' },
    { name: '电机_功率因数', val: motor.power_factor || 0.87, type: 'equipment' },
    { name: '电机_100%效率', val: motor.efficiency_100 || 93.6, type: 'equipment', unitCode: '%' },
    { name: '电机_启动电流比M1', val: motor.start_current_ratio_m1 || 9.6, type: 'equipment' },
    { name: '电机_启动电流比M2', val: motor.start_current_ratio_m2 || 3.5, type: 'equipment' },
    { name: '电机_制动器型号', val: motor.brake_model || 'BE30', type: 'equipment' },
    { name: '电机_质量', val: motor.mass || motor.weight || 170, type: 'equipment', unitCode: 'kg' },
    { name: '电机_转动惯量', val: motor.inertia || 1950, type: 'equipment', unitCode: '10⁻⁴ kgm²' },
    { name: '电机_频率', val: motorFreq || '50Hz', type: 'equipment' },
    { name: '电机_防护等级', val: motor.protection || 'IP55', type: 'equipment' },
    { name: '减速机_型号', val: reducer.model, type: 'equipment' },
    { name: '减速机_最大允许扭矩', val: reducer.max_torque, type: 'equipment', unitCode: 'Nm' },
    { name: '减速机_减速比', val: reducer.ratio, type: 'equipment' },
    { name: '减速机_传动效率', val: reducer.efficiency, type: 'equipment' },
    { name: '减速机_输出转矩', val: equipment?.torque || equipment?.item?.torque || reducer.max_torque, type: 'equipment', unitCode: 'Nm' }
  ]
}

const applyEquipmentParametersToRows = (equipment, options = {}) => {
  const {
    persistEquipment = true,
    showSuccess = false,
    rerunCalculation = false
  } = options

  currentEquipment.value = equipment || null
  if (persistEquipment) {
    const versionId = String(selectedVersionId.value || '').trim()
    if (equipment) {
      if (versionId) {
        localStorage.setItem(getCurrentEquipmentStorageKey(versionId), JSON.stringify(equipment))
      }
    } else if (versionId) {
      localStorage.removeItem(getCurrentEquipmentStorageKey(versionId))
    }
  }

  const mapping = buildEquipmentParameterMappings(equipment)
  const nextEquipmentRows = mapping
    .filter((p) => p.val !== undefined && p.val !== null && p.val !== '')
    .map((p) => {
      const existing = parameterRows.value.find(r => r.paramName === p.name || r.displayName === p.name)
      return {
        ...(existing || {}),
        parameterId: existing?.parameterId || 0,
        paramCode: existing?.paramCode || '',
        paramName: p.name,
        displayName: p.name,
        unitCode: p.unitCode || existing?.unitCode || '',
        valueType: 'equipment',
        value: String(p.val),
        dirty: true,
        source: existing?.source || 'draft',
        pendingCreate: existing?.pendingCreate ?? true
      }
    })

  const existingEquipmentRows = parameterRows.value.filter(
    (row) => row.valueType === 'equipment' || String(row.paramName || '').startsWith('电机_') || String(row.paramName || '').startsWith('减速机_')
  )
  const otherRows = parameterRows.value.filter(
    (row) => !(row.valueType === 'equipment' || String(row.paramName || '').startsWith('电机_') || String(row.paramName || '').startsWith('减速机_'))
  )

  const dedupedEquipmentRows = []
  const seenEquipmentNames = new Set()
  nextEquipmentRows.forEach((row) => {
    const rowKey = String(row.paramName || '').trim()
    if (!rowKey || seenEquipmentNames.has(rowKey)) return
    seenEquipmentNames.add(rowKey)
    dedupedEquipmentRows.push(row)
  })

  const modified = dedupedEquipmentRows.length !== existingEquipmentRows.length
    || dedupedEquipmentRows.some((row, index) => {
      const existing = existingEquipmentRows[index]
      return !existing
        || String(existing.paramName || '') !== String(row.paramName || '')
        || String(existing.value || '') !== String(row.value || '')
        || String(existing.unitCode || '') !== String(row.unitCode || '')
    })

  parameterRows.value = [...dedupedEquipmentRows, ...otherRows]
  // 重新计算 summaryCards（关注指标状态）
  if (modified) {
    recalculateSummaryCards()
  }

  if (modified && showSuccess) {
    ElMessage.success('选型参数已加入当前工作台，可直接用于校核公式，但不会写入参数中心')
  }
  if (modified && rerunCalculation) {
    handleRunCalculation()
  }
}

/** 选型后立即刷新关注指标摘要卡片（不依赖公式计算结果） */
const recalculateSummaryCards = () => {
  // 触发 summaryCards 重新计算：设置当前设备的参数值到 latestScope
  const equipmentScope = {}
  currentEquipment.value?.motor_params?.forEach((p) => {
    if (p.name && p.val !== undefined) {
      equipmentScope[p.name] = String(p.val)
    }
  })
  // 合并到现有 scope
  latestScope.value = { ...latestScope.value, ...equipmentScope }
  // 强制触发 reactivity
  latestScope.value = { ...latestScope.value }
}

const handleApplyEquipment = async (equipment) => {
  const exactMotor = await resolveExactMotorDetails(equipment)
  const normalizedEquipment = {
    ...(equipment || {}),
    motor_params: exactMotor
  }
  applyEquipmentParametersToRows(normalizedEquipment, {
    persistEquipment: true,
    showSuccess: true,
    rerunCalculation: true
  })

  smartSelectDrawerVisible.value = false
}

const explanationPanel = computed(() => {
  if (explanationTarget.value.type === 'parameter') {
    const row = parameterRows.value.find((item) => String(item.paramName || '') === String(explanationTarget.value.key || ''))
    if (row) {
      const provenance = normalizeParameterProvenance(row.provenance || row.remark || null)
      return {
        title: row.displayName,
        categoryLabel: row.valueType === 'equipment' ? '选型参数' : '输入参数',
        summary: row.description || `参数值: ${formatMetric(row.value, row.unitCode)}`,
        metaCards: [
          { label: '当前值', value: formatMetric(row.value, row.unitCode), tone: 'primary' },
          { label: '参数编码', value: row.paramName || '-', tone: 'default' },
          { label: '系统来源', value: resolveSourceLabel(row.source), tone: 'default' },
          { label: '取值方式', value: PARAMETER_SOURCE_LABELS[provenance.source_type || 'manual'] || '人工录入', tone: 'default' }
        ],
        details: [
          `参数编码：${row.paramName}`,
          `当前值：${formatMetric(row.value, row.unitCode)}`,
          `系统来源：${resolveSourceLabel(row.source)}`
        ],
        resources: normalizeResourceRows(row.resources || provenance.resources || []),
        sourceType: provenance.source_type || 'manual',
        sourceTypeLabel: PARAMETER_SOURCE_LABELS[provenance.source_type || 'manual'] || '人工录入',
        sourceNote: provenance.source_note || ''
      }
    }
  }

  if (explanationTarget.value.type === 'formula') {
    const row = formulaScenes.value.flatMap((scene) => scene.rows).find((item) => String(item._rowKey || '') === String(explanationTarget.value.key || ''))
    if (row) {
      return {
        title: row.name || '未命名公式',
        categoryLabel: '公式节点',
        summary: row.description || `公式表达式：${row.expression || '暂无表达式'}`,
        output_flag: row.output_flag || 'auto',
        metaCards: [
          { label: '公式名称', value: row.name || '未命名公式', tone: 'primary' },
          { label: '所在场景', value: row.sceneName || row.scene_name || '-', tone: 'default' },
          { label: '依赖数量', value: String(row.dependencies?.length || 0), tone: 'default' },
          { label: '结果', value: resolveFormulaMetric(row), tone: 'default' }
        ],
        details: [
          `依赖：${row.dependencies.map((item) => item.displayName).join('、') || '无'}`,
          `结果：${resolveFormulaMetric(row)}`
        ],
        resources: row.resources || []
      }
    }
  }

  if (explanationTarget.value.type === 'result') {
    // 结果卡片现在只显示配置了校核规则的，所以从 primaryResultRows 找
    const row = primaryResultRows.value.find((item) => String(item.paramName || '') === String(explanationTarget.value.key || ''))
    if (row) {
      const formulaRow = activeModuleFormulaRows.value.find(r => String(r.name || '').trim() === row.paramName)
      return {
        title: row.displayName,
        categoryLabel: '关键指标',
        summary: formulaRow?.description || row.description || `实际值：${formatMetric(row.value, row.unitCode)}`,
        metaCards: [
          { label: '当前实际值', value: formatMetric(row.value, row.unitCode), tone: 'primary' },
          { label: '参数编码', value: row.paramName || '-', tone: 'default' },
          { label: '所在场景', value: row.sceneName || '模块输出', tone: 'default' }
        ],
        details: [
          `场景：${row.sceneName || '模块输出'}`
        ],
        resources: formulaRow?.resources || row.resources || []
      }
    }
  }

  return {
    title: activeModule.value?.moduleName || '设计工作台',
    categoryLabel: '模块总览',
    summary: activeModule.value?.description || '当前模块概览。',
    metaCards: [
      { label: '产品', value: currentTypeName.value || '-', tone: 'primary' },
      { label: '型号', value: currentVersionPath.value || '-', tone: 'default' }
    ],
    details: [
      `产品：${currentTypeName.value}`,
      `型号：${currentVersionPath.value}`
    ],
    resources: activeModule.value?.resources || []
  }
})

const buildParameterPayload = ({ numericOnly = false } = {}) => {
  return parameterRows.value.reduce((payload, row) => {
    const key = String(row.paramName || '').trim()
    const value = String(row.value ?? '').trim()
    if (!key || !value) {
      return payload
    }
    if (numericOnly) {
      const numericValue = Number(value)
      if (!Number.isFinite(numericValue)) {
        return payload
      }
      payload[key] = numericValue
      return payload
    }
    payload[key] = value
    return payload
  }, {})
}

const normalizeTemplateVariableMap = (variables = {}) => {
  if (Array.isArray(variables)) {
    return Object.fromEntries(
      variables
        .map((name) => String(name || '').trim())
        .filter(Boolean)
        .map((name) => [name, ''])
    )
  }
  if (variables && typeof variables === 'object') {
    return Object.fromEntries(
      Object.entries(variables)
        .map(([name, unitCode]) => [String(name || '').trim(), typeof unitCode === 'string' ? unitCode : ''])
        .filter(([name]) => Boolean(name))
    )
  }
  return {}
}

const normalizeTemplateModules = (templateStructure = {}) => {
  return (Array.isArray(templateStructure?.modules) ? templateStructure.modules : []).map((module) => {
    const moduleCode = String(module.module_code || module.moduleCode || '')
    const moduleName = String(module.module_name || module.moduleName || '未命名模块')
    const scenes = (Array.isArray(module.scenes) ? module.scenes : []).map((scene) => {
      const sceneCode = String(scene.scene_code || scene.sceneCode || '')
      const sceneName = String(scene.scene_name || scene.sceneName || '未命名场景')
      const sceneType = String(scene.scene_type || scene.sceneType || 'calc')
      const items = Array.isArray(scene.items) ? scene.items : []
      return {
        moduleCode,
        moduleName,
        sceneCode,
        sceneName,
        sceneType,
        rows: items.map((item, index) => ({
          id: item.item_id || item.id || 0,
          name: item.formula_name || item.name || `公式 ${index + 1}`,
          expression: item.expression || '=0',
          variables: normalizeTemplateVariableMap(item.variables),
          unit_code: item.unit || '',
          scene_name: sceneName,
          scene_code: sceneCode,
          module_code: moduleCode,
          module_name: moduleName,
          sort_order: item.sort_order || index,
          description: item.description || '',
          resources: Array.isArray(item.resources) ? item.resources : [],
          _rowKey: `${moduleCode || 'module'}:${sceneCode || 'scene'}:${item.item_id || item.id || item.formula_name || index}`
        }))
      }
    })
    return {
      moduleCode,
      moduleName,
      scenes,
      sceneCount: scenes.length,
      formulaCount: scenes.reduce((count, scene) => count + scene.rows.length, 0)
    }
  })
}

const normalizeExecutionResults = (payload = {}) => {
  if (Array.isArray(payload?.latest_results)) {
    return payload.latest_results
  }

  const computedResults = payload?.computed_results || {}
  const results = []
  for (const [formulaName, result] of Object.entries(computedResults)) {
    results.push({
      scene_code: '',
      scene_name: '',
      result_code: formulaName,
      result_name: formulaName,
      result_value: String(result?.value ?? ''),
      unit_code: result?.unit || '',
      source_formula: formulaName
    })
  }
  return results
}

const normalizeModules = (rawModules = []) => {
  return (Array.isArray(rawModules) ? rawModules : []).map((module) => {
    const moduleCode = String(module.moduleCode || module.module_code || '')
    let moduleName = module.moduleName || module.module_name
    if (!moduleName || moduleName === '未命名模块') {
      if (moduleCode === 'power_calc') moduleName = '功率计算'
      else if (moduleCode === 'structure_calc') moduleName = '结构计算'
      else moduleName = '未命名模块'
    }

    const scenes = Array.isArray(module.scenes) ? module.scenes : []
    const normalizedScenes = scenes.map((scene) => ({
      moduleCode: moduleCode,
      moduleName: moduleName,
      sceneCode: String(scene.sceneCode || scene.scene_code || ''),
      sceneName: scene.sceneName || scene.scene_name || '未命名场景',
      sceneType: scene.sceneType || scene.scene_type || 'calc',
      rows: (Array.isArray(scene.rows) ? scene.rows : Array.isArray(scene.formulas) ? scene.formulas : []).map((row, index) => ({
        ...row,
        _rowKey: `${moduleCode || 'module'}:${String(scene.sceneCode || scene.scene_code || 'scene')}:${row.id || row.name || index}`
      }))
    }))
    const formulaCount = normalizedScenes.reduce((count, scene) => count + scene.rows.length, 0)
    return {
      moduleCode: moduleCode,
      moduleName: moduleName,
      scenes: normalizedScenes,
      sceneCount: normalizedScenes.length,
      formulaCount
    }
  }).filter((module) => module.moduleCode)
}

const resolveTypeNode = (preferredTypeId = '') => {
  return treeData.value.find((typeNode) => String(typeNode.raw?.id || '') === String(preferredTypeId || '')) || treeData.value[0] || null
}

const resolveVersionContext = (typeNode, preferredFamilyId = '', preferredVersionId = '') => {
  const families = typeNode?.children || []
  if (!families.length) {
    return { familyNode: null, versionNode: null }
  }

  if (preferredVersionId) {
    for (const familyNode of families) {
      const versionNode = (familyNode.children || []).find((item) => String(item.raw?.id || '') === String(preferredVersionId || ''))
      if (versionNode) {
        return { familyNode, versionNode }
      }
    }
  }

  if (preferredFamilyId) {
    const familyNode = families.find((item) => String(item.raw?.id || '') === String(preferredFamilyId || '')) || null
    const versionNode = familyNode?.children?.[0] || null
    if (familyNode && versionNode) {
      return { familyNode, versionNode }
    }
  }

  const familyNode = families.find((item) => (item.children || []).length) || families[0] || null
  const versionNode = familyNode?.children?.[0] || null
  return { familyNode, versionNode }
}

const ensureExplanationFocus = () => {
  if (primaryResultRows.value.length) {
    explanationTarget.value = { type: 'result', key: primaryResultRows.value[0].paramName }
    return
  }
  const firstFormula = formulaScenes.value[0]?.rows?.[0]
  if (firstFormula) {
    explanationTarget.value = { type: 'formula', key: firstFormula._rowKey }
    return
  }
  explanationTarget.value = { type: 'module', key: activeModuleCode.value }
}

const runCalculation = async ({ silent = false, showSuccess = false } = {}) => {
  if (!selectedVersionId.value) {
    return
  }

  calculationError.value = ''
  executing.value = true
  try {
    const payload = await fetchModelWorkbenchInstance(
      selectedVersionId.value,
      buildParameterPayload({ numericOnly: false }),
      { moduleCode: requestedModuleCode.value }
    )
    const nextModules = normalizeTemplateModules(payload?.template_structure || {})
    modules.value = nextModules

    const matchedModule = nextModules.find((module) => String(module.moduleCode || '') === String(requestedModuleCode.value || ''))
    activeModuleCode.value = matchedModule?.moduleCode || ''
    latestResults.value = normalizeExecutionResults(payload)
    latestScope.value = payload?.scope || {}
    ensureExplanationFocus()
    if (showSuccess) {
      ElMessage.success('计算结果已更新')
    }
  } catch (error) {
    calculationError.value = error?.response?.data?.detail || error?.message || '执行计算失败，请检查输入参数'
    if (!silent) {
      ElMessage.error(calculationError.value)
    }
  } finally {
    executing.value = false
  }
}

const handleRunCalculation = async () => {
  if (!selectedFamilyId.value || !selectedVersionId.value) return
  try {
    await saveDirtyParameterRows({ runCalc: false })
  } catch (error) {
    console.error('保存参数失败', error)
    ElMessage.error(error?.response?.data?.detail || '保存参数失败')
    return
  }
  await runCalculation({ silent: false, showSuccess: true })
}

const scheduleAutoRun = () => {
  if (autoRunTimer) {
    clearTimeout(autoRunTimer)
  }
  autoRunTimer = setTimeout(() => {
    autoRunTimer = null
    runCalculation({ silent: true, showSuccess: false })
  }, 400)
}

const loadVersionContext = async (preferredModuleCode = '') => {
  // 提前确定模块编码，保证选型参数存储/恢复按「型号+模块」隔离
  requestedModuleCode.value = String(preferredModuleCode || requestedModuleCode.value || '')
  activeModuleCode.value = requestedModuleCode.value

  if (!selectedFamilyId.value || !selectedVersionId.value) {
    modules.value = []
    parameterRows.value = []
    rawMatrixData.value = null
    latestResults.value = []
    latestScope.value = {}
    activeModuleCode.value = ''
    currentEquipment.value = null
    return
  }

  // 加载型号级关注指标配置
  loadLocalFocusMetricConfig(selectedVersionId.value)

  const [matrix, snapshot, lookups, mappings, focusConfigs] = await Promise.all([
    fetchFamilyMatrix(selectedFamilyId.value, preferredModuleCode),
    fetchLatestWorkbenchSnapshot(selectedVersionId.value),
    fetchParameterLookups(),
    fetchSelectionMappings(selectedVersionId.value),
    fetchFocusMetricConfigs(selectedVersionId.value)
  ])

  backendFocusMetricConfigs.value = focusConfigs || {}
  lookupItems.value = lookups || []
  const storedSelectionFieldConfigs = loadStoredSelectionFieldConfigs(selectedVersionId.value)
  const storedSelectionMappings = loadStoredSelectionMappings(selectedVersionId.value)
  selectionFieldConfigs.value = Object.fromEntries(
    Object.entries(storedSelectionFieldConfigs || {}).map(([categoryCode, fields]) => [
      categoryCode,
      Array.isArray(fields) ? fields.map((field) => ({ ...field })) : []
    ])
  )
  const normalizedMappings = mappings && typeof mappings === 'object' && Object.keys(mappings).length > 0 ? mappings : {}
  const hasLegacyFlatMapping = Object.values(normalizedMappings).every((value) => typeof value === 'string')
  let remoteSelectionMappings = {}
  if (hasLegacyFlatMapping) {
    remoteSelectionMappings = {
      gearmotor: {
        power: normalizedMappings.power || '',
        speed: normalizedMappings.speed || '',
        torque: normalizedMappings.torque || '',
        fb: normalizedMappings.fb || ''
      }
    }
    activeSelectionCategoryCode.value = 'gearmotor'
  } else {
    remoteSelectionMappings = normalizedMappings
    const existingCategoryCodes = Object.keys(normalizedMappings).filter((code) => normalizedMappings[code] && Object.keys(normalizedMappings[code]).length > 0)
    if (existingCategoryCodes.length > 0) {
      activeSelectionCategoryCode.value = existingCategoryCodes[0]
    }
  }
  selectionMappings.value = mergeSelectionMappingsState(storedSelectionMappings, remoteSelectionMappings)
  const localCategoryCodes = Object.keys(selectionFieldConfigs.value || {}).filter((code) => {
    const fields = selectionFieldConfigs.value?.[code]
    return Array.isArray(fields) && fields.length > 0
  })
  if (localCategoryCodes.length > 0 && !selectionFieldConfigs.value?.[activeSelectionCategoryCode.value]?.length) {
    activeSelectionCategoryCode.value = localCategoryCodes[0]
  }
  ensureSelectionCategoryStructure(activeSelectionCategoryCode.value)
  Object.keys(selectionMappings.value || {}).forEach((categoryCode) => {
    syncSelectionFieldConfigsFromMappings(categoryCode)
  })
  await loadEquipmentCategoriesIfNeeded()
  await loadSelectionTableColumns(activeSelectionCategoryCode.value)

  // 保存原始矩阵数据，用于参数区间计算
  rawMatrixData.value = matrix

  const modelRows = buildWorkbenchParameterRows(matrix, selectedVersionId.value).map((row) => ({
    ...row,
    resources: normalizeParameterProvenance(row.remark || null).resources,
    provenance: normalizeParameterProvenance(row.remark || null),
    dirty: false,
    source: row.value ? 'model' : 'empty'
  }))
  const snapshotMap = new Map((snapshot?.rows || []).map((row) => [Number(row.parameter_id || 0), row.snapshot_value]))
  parameterRows.value = mergeWorkbenchModelRows({
    modelRows,
    snapshotMap
  })

  currentEquipment.value = null

  const savedCurrentEquipment = localStorage.getItem(getCurrentEquipmentStorageKey(selectedVersionId.value))
  if (savedCurrentEquipment) {
    try {
      const parsedCurrentEquipment = JSON.parse(savedCurrentEquipment)
      const exactMotor = await resolveExactMotorDetails(parsedCurrentEquipment)
      const normalizedEquipment = {
        ...(parsedCurrentEquipment || {}),
        motor_params: exactMotor
      }
      currentEquipment.value = normalizedEquipment
      applyEquipmentParametersToRows(normalizedEquipment, {
        persistEquipment: false,
        showSuccess: false,
        rerunCalculation: false
      })
    } catch (e) {
      console.error('Failed to restore current equipment:', e)
    }
  } else {
    const savedEquipment = localStorage.getItem(getEquipmentRowsStorageKey(selectedVersionId.value))
    if (savedEquipment) {
      try {
        const parsedEquipment = JSON.parse(savedEquipment)
        if (Array.isArray(parsedEquipment) && parsedEquipment.length) {
          const equipmentByName = new Map()
          parsedEquipment.forEach((row) => {
            const rowKey = String(row?.paramName || row?.displayName || '').trim()
            if (!rowKey) return
            equipmentByName.set(rowKey, {
              ...row,
              paramName: rowKey,
              displayName: row?.displayName || rowKey,
              valueType: 'equipment'
            })
          })
          const otherRows = parameterRows.value.filter(
            (row) => !(row.valueType === 'equipment' || String(row.paramName || '').startsWith('电机_') || String(row.paramName || '').startsWith('减速机_'))
          )
          parameterRows.value = [...equipmentByName.values(), ...otherRows]
        }
      } catch (e) {
        console.error('Failed to parse saved equipment parameters', e)
      }
    }
  }

  explanationTarget.value = { type: 'module', key: activeModuleCode.value }
  await syncRouteQuery()
  await runCalculation({ silent: true, showSuccess: false })
}

const loadWorkbench = async () => {
  loadingWorkbench.value = true
  try {
    treeData.value = await fetchDrumTree()
    const preferredTypeId = normalizeQueryValue(route.query.typeId)
    const preferredFamilyId = normalizeQueryValue(route.query.familyId)
    const preferredVersionId = normalizeQueryValue(route.query.versionId)
    const preferredModuleCode = normalizeQueryValue(route.query.moduleCode)
    requestedModuleCode.value = preferredModuleCode
    const typeNode = resolveTypeNode(preferredTypeId)

    if (!typeNode) {
      selectedTypeId.value = ''
      selectedFamilyId.value = ''
      selectedVersionId.value = ''
      modules.value = []
      parameterRows.value = []
      latestResults.value = []
      latestScope.value = {}
      return
    }

    selectedTypeId.value = String(typeNode.raw?.id || '')
    const { familyNode, versionNode } = resolveVersionContext(typeNode, preferredFamilyId, preferredVersionId)
    selectedFamilyId.value = String(familyNode?.raw?.id || '')
    selectedVersionId.value = String(versionNode?.raw?.id || '')
    await loadVersionContext(preferredModuleCode)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载工作台失败，请稍后重试')
  } finally {
    loadingWorkbench.value = false
  }
}

const handleScopeNodeClick = async (node) => {
  if (!node) return

  let familyNode = null
  let versionNode = null

  if (node.level === 'family') {
    familyNode = node
    versionNode = node.children?.[0] || null
  } else if (node.level === 'version') {
    versionNode = node
    familyNode = (currentTypeNode.value?.children || []).find((item) =>
      (item.children || []).some((child) => String(child.raw?.id || '') === String(node.raw?.id || ''))
    ) || null
  }

  if (!familyNode || !versionNode) {
    return
  }

  selectedFamilyId.value = String(familyNode.raw?.id || '')
  selectedVersionId.value = String(versionNode.raw?.id || '')
  await loadVersionContext(activeModuleCode.value)
}

const handleModuleChange = async (moduleCode) => {
  activeModuleCode.value = String(moduleCode || '')
  explanationTarget.value = { type: 'module', key: activeModuleCode.value }
  await syncRouteQuery()
  ensureExplanationFocus()
}

const handleInputChange = (row, value) => {
  const nextValue = String(value ?? '')
  const nextRows = [...parameterRows.value]
  const targetIndex = findParameterRowIndex(nextRows, row)

  if (targetIndex >= 0) {
    nextRows[targetIndex] = {
      ...nextRows[targetIndex],
      value: nextValue,
      dirty: true,
      source: 'draft'
    }
  } else {
    const targetName = String(row.paramName || '').trim()
    nextRows.push({
      parameterId: Number(row.parameterId || 0),
      paramCode: row.paramCode || '',
      paramName: targetName,
      displayName: row.displayName || targetName,
      unitCode: row.unitCode || '',
      valueType: 'basic',
      value: nextValue,
      dirty: true,
      source: 'draft'
    })
  }

  parameterRows.value = nextRows
  explanationTarget.value = { type: 'parameter', key: String(row.paramName || '').trim() }
}

const handleInputNameChange = (row, name) => {
  const nextName = String(name ?? '').trim()
  const nextRows = [...parameterRows.value]
  const targetIndex = findParameterRowIndex(nextRows, row)

  if (targetIndex >= 0) {
    nextRows[targetIndex] = {
      ...nextRows[targetIndex],
      paramName: nextName,
      displayName: nextName,
      dirty: true,
      source: 'draft',
      _nameConfirmed: true
    }
    parameterRows.value = nextRows
  }
}

const handleInputUnitChange = (row, unitCode) => {
  const nextUnit = String(unitCode ?? '').trim()
  const nextRows = [...parameterRows.value]
  const targetIndex = findParameterRowIndex(nextRows, row)

  if (targetIndex >= 0) {
    nextRows[targetIndex] = {
      ...nextRows[targetIndex],
      unitCode: nextUnit,
      dirty: true,
      source: 'draft'
    }
    parameterRows.value = nextRows
  }
}

const handleParameterBlur = async (row) => {
  if (!selectedFamilyId.value || !selectedVersionId.value) return

  const targetIndex = findParameterRowIndex(parameterRows.value, row)
  const targetRow = targetIndex >= 0 ? parameterRows.value[targetIndex] : null
  if (!targetRow || !targetRow.dirty) return

  try {
    await saveDirtyParameterRows({ runCalc: true })
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存参数并计算失败')
  }
}

const selectParameter = (row) => {
  if (editingFormulaKey.value && row.paramName !== activeFormulaDraft.value?.paramName) {
    const insertion = resolveParameterInsertionDraft({
      row,
      editingFormulaKey: editingFormulaKey.value,
      editingFormulaField: editingFormulaField.value,
      activeFormulaDraft: activeFormulaDraft.value,
      formulaCursorStart: formulaCursorStart.value
    })
    if (insertion.inserted) {
      activeFormulaDraft.value = {
        ...activeFormulaDraft.value,
        expression: insertion.nextExpression
      }
      formulaCursorStart.value = insertion.nextCursorStart
      if (autoRunTimer) {
        clearTimeout(autoRunTimer)
        autoRunTimer = null
      }
      return
    }
  }
  explanationTarget.value = { type: 'parameter', key: String(row.paramName || '') }
}

const handleAddParameter = () => {
  const tempId = `new_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`
  parameterSearchKeyword.value = ''
  parameterRows.value.unshift(createPendingParameterRow(tempId))
}

const openParameterGroupDialog = (row) => {
  const paramName = String(row?.paramName || '').trim()
  const displayName = String(row?.displayName || row?.paramName || '').trim()
  if (!paramName && !displayName) {
    ElMessage.warning('请先命名参数，再调整层级')
    return
  }

  const currentGroup = resolveWorkbenchTreeGroup(row, 'input')
  parameterGroupDraft.value = {
    row: row || null,
    paramName,
    displayName,
    targetGroupKey: currentGroup.key || 'general',
    customGroupLabel: ''
  }
  parameterGroupDialogVisible.value = true
}

const handleParameterGroupSave = async () => {
  const draft = parameterGroupDraft.value || {}
  const sourceRow = draft.row || {}
  let targetGroupKey = String(draft.targetGroupKey || '').trim()
  const paramName = String(sourceRow.paramName || draft.paramName || '').trim()

  if (!paramName) {
    ElMessage.warning('请先命名参数，再调整层级')
    return
  }
  if (!targetGroupKey) {
    ElMessage.warning('请选择目标分组')
    return
  }

  // 新建自定义分组：用分组名作为 key，标签为用户输入的组名
  if (targetGroupKey === CUSTOM_GROUP_TOKEN) {
    const customLabel = String(draft.customGroupLabel || '').trim()
    if (!customLabel) {
      ElMessage.warning('请输入新的分组名称')
      return
    }
    targetGroupKey = `custom:${customLabel}`
  }
  const targetGroupLabel = targetGroupKey.startsWith('custom:')
    ? targetGroupKey.slice('custom:'.length)
    : (PARAMETER_GROUP_LABEL_MAP[targetGroupKey] || '自定义参数')

  const nextRows = [...parameterRows.value]
  const targetIndex = findParameterRowIndex(nextRows, sourceRow)
  const baseRow = targetIndex >= 0 ? nextRows[targetIndex] : sourceRow
  const nextProvenance = {
    ...normalizeParameterProvenance(baseRow.provenance || baseRow.remark || null),
    custom_group_key: targetGroupKey,
    custom_group_label: targetGroupLabel
  }
  const nextRow = {
    ...baseRow,
    paramName,
    displayName: String(baseRow.displayName || draft.displayName || paramName).trim() || paramName,
    customGroupKey: targetGroupKey,
    customGroupLabel: targetGroupLabel,
    provenance: nextProvenance,
    dirty: true,
    source: 'draft'
  }
  nextRow.remark = buildParameterRemark(nextRow)

  if (targetIndex >= 0) {
    nextRows[targetIndex] = nextRow
  } else {
    nextRows.unshift(nextRow)
  }
  parameterRows.value = nextRows
  explanationTarget.value = { type: 'parameter', key: paramName }
  parameterGroupDialogVisible.value = false
  setParameterFeedback(`已将 ${nextRow.displayName || paramName} 调整到 ${targetGroupLabel}`, 'success')

  try {
    await saveDirtyParameterRows()
    ElMessage.success(`已调整到${targetGroupLabel}`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存参数层级失败')
  }
}

const openRenameGroupDialog = (group) => {
  const groupKey = String(group?.key || '').trim()
  const oldLabel = String(group?.label || '自定义分组').trim()
  if (!groupKey) {
    ElMessage.warning('无法识别的参数分组')
    return
  }
  renameGroupDraft.value = {
    group: group || null,
    groupKey,
    oldLabel,
    newLabel: oldLabel
  }
  renameGroupDialogVisible.value = true
}

const handleRenameGroupSave = async () => {
  const draft = renameGroupDraft.value || {}
  const groupKey = String(draft.groupKey || '').trim()
  const oldLabel = String(draft.oldLabel || '').trim()
  const newLabel = String(draft.newLabel || '').trim()

  if (!groupKey) {
    ElMessage.warning('无法识别的参数分组')
    return
  }
  if (!newLabel) {
    ElMessage.warning('请输入新的分组名称')
    return
  }
  if (newLabel === oldLabel) {
    renameGroupDialogVisible.value = false
    return
  }

  const newGroupKey = `custom:${newLabel}`
  const nextRows = parameterRows.value.map((row) => {
    const currentGroup = resolveWorkbenchTreeGroup(row, 'input')
    if (currentGroup.key !== groupKey) {
      return row
    }
    const nextProvenance = {
      ...normalizeParameterProvenance(row.provenance || row.remark || null),
      custom_group_key: newGroupKey,
      custom_group_label: newLabel
    }
    const nextRow = {
      ...row,
      customGroupKey: newGroupKey,
      customGroupLabel: newLabel,
      provenance: nextProvenance,
      dirty: true
    }
    nextRow.remark = buildParameterRemark(nextRow)
    return nextRow
  })

  const renamedCount = nextRows.reduce(
    (acc, row) => (row.customGroupKey === newGroupKey ? acc + 1 : acc),
    0
  )
  if (renamedCount === 0) {
    ElMessage.warning('该分组下没有可重命名的参数')
    return
  }

  parameterRows.value = nextRows
  renameGroupDialogVisible.value = false
  setParameterFeedback(`已将分组 "${oldLabel}" 重命名为 "${newLabel}"`, 'success')

  try {
    await saveDirtyParameterRows()
    ElMessage.success(`分组已重命名为"${newLabel}"`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存分组重命名失败')
  }
}

const handleDeleteParameter = (row) => {
  ElMessageBox.confirm(`确定要删除参数 ${row.displayName || row.paramName || '未命名'} 吗？`, '删除参数', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      if (row.parameterId && Number(row.parameterId) > 0 && selectedVersionId.value) {
        await deleteParameterDefinition(Number(row.parameterId))
      }
      parameterRows.value = removeParameterRow(parameterRows.value, row)
      await runCalculation({ silent: true, showSuccess: false })
      ElMessage.success('参数已删除')
    } catch (error) {
      ElMessage.error(error?.response?.data?.detail || '删除参数失败')
    }
  }).catch(() => {})
}

const handleDeleteParameterGroup = (group) => {
  ElMessageBox.confirm(`确定要删除参数集合 "${group.label}" 下的 ${group.rows.length} 个参数吗？`, '删除参数集合', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const rowsToDelete = group.rows;
      const idsToDelete = rowsToDelete.filter(r => r.parameterId && Number(r.parameterId) > 0).map(r => Number(r.parameterId));
      
      if (idsToDelete.length > 0) {
        for (const id of idsToDelete) {
          await deleteParameterDefinition(id);
        }
      }
      
      rowsToDelete.forEach(row => {
        parameterRows.value = removeParameterRow(parameterRows.value, row);
      });
      
      await runCalculation({ silent: true, showSuccess: false });
      ElMessage.success(`参数集合 "${group.label}" 已删除`);
    } catch (error) {
      ElMessage.error(error?.response?.data?.detail || '删除参数集合失败');
    }
  }).catch(() => {});
}

const selectFormula = (row) => {
  explanationTarget.value = { type: 'formula', key: String(row._rowKey || '') }
}

const selectResult = (row) => {
  if (editingFormulaKey.value && row.paramName !== activeFormulaDraft.value?.paramName) {
    const insertion = resolveParameterInsertionDraft({
      row,
      editingFormulaKey: editingFormulaKey.value,
      editingFormulaField: editingFormulaField.value,
      activeFormulaDraft: activeFormulaDraft.value,
      formulaCursorStart: formulaCursorStart.value
    })
    if (insertion.inserted) {
      activeFormulaDraft.value = {
        ...activeFormulaDraft.value,
        expression: insertion.nextExpression
      }
      formulaCursorStart.value = insertion.nextCursorStart
      if (autoRunTimer) {
        clearTimeout(autoRunTimer)
        autoRunTimer = null
      }
      return
    }
  }
  explanationTarget.value = { type: 'result', key: String(row.paramName || '') }
}

const cycleWorkspaceMode = () => {
  const modes = ['list', 'flow', 'model']
  const currentIndex = modes.indexOf(workspaceMode.value)
  workspaceMode.value = modes[(currentIndex + 1) % modes.length]
}

const resolveFormulaStateLabel = (row) => {
  if (row.missingDependencies?.length) {
    return '依赖待补齐'
  }
  if (row.resultRow?.value) {
    return '已完成计算'
  }
  return '等待计算'
}

const resolveFormulaMetric = (row) => {
  return formatMetric(row.resultRow?.value || '', row.resultRow?.unitCode || row.unit_code || '')
}

const findParameterRowByNameOrAlias = (name) => {
  const normalizedName = String(name || '').trim()
  if (!normalizedName) return null
  const directRow = parameterRows.value.find((row) => String(row.paramName || '').trim() === normalizedName)
  if (directRow) return directRow

  const aliasNames = ANALYSIS_PARAMETER_ALIAS_MAP[normalizedName] || []
  const aliasRow = parameterRows.value.find((row) => aliasNames.includes(String(row.paramName || '').trim()))
  if (aliasRow) return aliasRow

  const reverseAliasRow = parameterRows.value.find((row) => {
    const rowName = String(row.paramName || '').trim()
    return (ANALYSIS_PARAMETER_ALIAS_MAP[rowName] || []).includes(normalizedName)
  })
  return reverseAliasRow || null
}

const parameterNameMatchesDependency = (selectedParamName, dependencyName) => {
  const normalizedSelected = String(selectedParamName || '').trim()
  const normalizedDependency = String(dependencyName || '').trim()
  if (!normalizedSelected || !normalizedDependency) return false
  if (normalizedSelected === normalizedDependency) return true
  if ((ANALYSIS_PARAMETER_ALIAS_MAP[normalizedDependency] || []).includes(normalizedSelected)) return true
  if ((ANALYSIS_PARAMETER_ALIAS_MAP[normalizedSelected] || []).includes(normalizedDependency)) return true
  return false
}

onMounted(() => {
  loadWorkbench()
})

onBeforeUnmount(() => {
  if (autoRunTimer) {
    clearTimeout(autoRunTimer)
  }
})
</script>

<style scoped>
.selection-config-drawer {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  background: #f3f6fb;
}

.selection-config-shell {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px 12px;
  border-bottom: 1px solid #dbe3ef;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.96));
}

.selection-config-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.selection-config-toolbar__heading {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.selection-config-toolbar__meta {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
}

.selection-config-toolbar__controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-config-toolbar__select {
  width: 180px;
}

.selection-config-table-wrap {
  width: 100%;
  overflow-x: auto;
  overflow-y: visible;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #dbe3ef;
  -webkit-overflow-scrolling: touch;
}

.selection-config-table-wrap::-webkit-scrollbar {
  height: 8px;
}

.selection-config-table-wrap::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 9999px;
}

.selection-config-table-wrap::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.selection-config-table {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  min-width: 760px;
  border: none;
  border-radius: 0;
  overflow: hidden;
}

.selection-config-table__head,
.selection-config-table__row {
  display: grid;
  grid-template-columns: 168px minmax(252px, 1.4fr) 80px 96px 96px 48px 56px;
  gap: 6px;
  align-items: start;
  padding: 6px 10px;
}

.selection-config-table__head {
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 1;
}

.selection-config-table__head > div,
.selection-config-table__cell {
  min-width: 0;
  overflow: visible;
}

.selection-config-table__col-hard,
.selection-config-table__cell--hard {
  text-align: center;
}

.selection-config-table__row {
  border-bottom: 1px solid #eef2f7;
}

.selection-config-table__row:last-of-type {
  border-bottom: none;
}

.selection-config-table__cell {
  display: flex;
  align-items: center;
  min-height: 32px;
  width: 100%;
}

.selection-config-table__cell--hard {
  justify-content: center;
  height: 32px;
}

.selection-config-table__cell--action {
  justify-content: flex-end;
  height: 32px;
}

.selection-config-table__cell :deep(.el-input),
.selection-config-table__cell :deep(.el-select),
.selection-config-table__cell :deep(.el-input-number) {
  width: 100%;
}

.selection-config-mapping {
  display: grid;
  grid-template-columns: 88px 1fr;
  gap: 6px;
  width: 100%;
  align-items: center;
}

.selection-config-mapping__param {
  min-width: 0;
}

.selection-config-mapping :deep(.el-select),
.selection-config-mapping :deep(.el-input-number),
.selection-config-mapping :deep(.el-input) {
  width: 100%;
}

.selection-config-tolerance {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
}

.selection-config-tolerance :deep(.el-input-number) {
  width: 100%;
}

.selection-config-tolerance__suffix {
  font-size: 12px;
  color: #64748b;
  flex-shrink: 0;
}

.selection-config-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  height: 32px;
  white-space: nowrap;
}

.selection-config-table__empty {
  padding: 22px 12px;
  font-size: 12px;
  color: #94a3b8;
  text-align: center;
}

@media (max-width: 820px) {
  .selection-config-table {
    min-width: 720px;
  }

  .selection-config-table__head,
  .selection-config-table__row {
    grid-template-columns: 152px minmax(232px, 1.4fr) 76px 92px 92px 44px 52px;
    gap: 5px;
    padding: 6px 8px;
  }

  .selection-config-mapping {
    grid-template-columns: 84px 1fr;
  }
}

.whitebox-workbench {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 60px);
  padding: 16px;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.1), transparent 22%),
    linear-gradient(180deg, #f8fafc, #eef2ff 42%, #f8fafc);
  box-sizing: border-box;
  overflow: hidden;
}

.workbench-header {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) auto auto;
  gap: 20px;
  align-items: center;
  padding: 20px 24px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
  flex-shrink: 0;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  font-size: 20px;
  color: #64748b;
  padding: 4px;
}

.back-btn:hover {
  color: #3b82f6;
}

.header-title {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.header-subtitle {
  margin-top: 8px;
  max-width: 760px;
  font-size: 14px;
  line-height: 1.75;
  color: #475569;
}

.header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.workbench-body {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr) 360px;
  gap: 16px;
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

.column {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  height: 100%;
}

.panel-card {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 32px rgba(15, 23, 42, 0.05);
  display: flex;
  flex-direction: column;
}

.panel-card :deep(.el-card__header) {
  padding: 18px 20px 12px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
  flex-shrink: 0;
}

.panel-card :deep(.el-card__body) {
  padding: 16px 20px 20px;
}

.panel-card--grow {
  flex: 1;
  min-height: 0;
}

.panel-card--grow :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.panel-desc {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.6;
  color: #64748b;
}

.panel-tags {
  display: flex;
  gap: 8px;
}

.scope-summary {
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(59, 130, 246, 0.04));
}

.scope-summary__label {
  font-size: 12px;
  color: #64748b;
}

.scope-summary__value {
  margin-top: 6px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.scope-node {
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  line-height: 1.6;
}

.scope-node--family {
  font-weight: 600;
  color: #334155;
}

.scope-node--version {
  color: #0f172a;
}

.module-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.module-item {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid #dbe5f1;
  border-radius: 16px;
  background: #fff;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.module-item:hover,
.module-item.is-active {
  border-color: #2563eb;
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.96), #ffffff);
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.12);
}

.module-item__title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.module-item__meta {
  margin-top: 8px;
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #2563eb;
}

.left-panel-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.left-panel-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding-right: 4px;
}
.left-panel-tabs :deep(.el-tab-pane) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.equipment-card {
  border: 1px solid #c7d2fe;
  background: #f8fafc;
}

.equipment-params-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.equipment-param-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  font-size: 13px;
}

.ep-label {
  color: #475569;
  font-weight: 500;
}

.ep-value {
  color: #0f172a;
  font-weight: 700;
}

.input-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 100%;
  overflow: auto;
}

.input-card {
  padding: 14px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.input-card:hover,
.input-card.is-active {
  border-color: #3b82f6;
  box-shadow: 0 10px 22px rgba(59, 130, 246, 0.1);
}

.input-card__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.input-card__title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.input-card__meta {
  margin-top: 4px;
  font-size: 12px;
  color: #94a3b8;
}

.input-card__hint {
  margin-top: 10px;
  font-size: 12px;
  color: #64748b;
}

.workspace-mode-bar {
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
  border-bottom: 1px solid #dbe2ea;
  background: #f7f9fc;
}

.workspace-mode-bar__meta {
  font-size: 12px;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}

.workspace-flow-canvas {
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 420px;
  height: calc(100% - 38px);
  background-color: #f8fafc;
  background-image: radial-gradient(#cbd5e1 0.7px, transparent 0.7px);
  background-size: 16px 16px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.summary-card {
  cursor: pointer;
  border-radius: 12px;
  border: 1px solid rgba(191, 219, 254, 0.8);
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.6), #ffffff);
  transition: all 0.2s ease;
}

.summary-card :deep(.el-card__body) {
  padding: 12px;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(37, 99, 235, 0.1);
  border-color: rgba(59, 130, 246, 0.4);
}

.summary-card.is-active {
  transform: translateY(-2px);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.35), 0 8px 20px rgba(37, 99, 235, 0.18);
  border-color: rgba(37, 99, 235, 0.9);
}

.summary-card.is-pass {
  border-color: rgba(16, 185, 129, 0.4);
  border-left: 2px solid #10b981;
  background: linear-gradient(180deg, rgba(209, 250, 229, 0.6), #ffffff);
}
.summary-card.is-pass .summary-card__metric-value {
  color: #059669;
}

.summary-card.is-fail {
  border-color: rgba(239, 68, 68, 0.4);
  border-left: 2px solid #ef4444;
  background: linear-gradient(180deg, rgba(254, 226, 226, 0.6), #ffffff);
}
.summary-card.is-fail .summary-card__metric-value {
  color: #dc2626;
}

.summary-card.has-warning {
  border-color: rgba(230, 162, 60, 0.4);
  border-left: 2px solid #e6a23c;
  background: linear-gradient(180deg, rgba(253, 246, 236, 0.6), #ffffff);
}
.summary-card.has-warning .summary-card__metric-value {
  color: #d97706;
}

.summary-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.summary-card__label {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.summary-card__actual,
.summary-card__reference {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  padding: 4px 0;
}

.summary-card__actual {
  margin-bottom: 4px;
  border-bottom: 1px dashed #e2e8f0;
}

.summary-card__metric-label {
  font-size: 12px;
  color: #64748b;
}

.summary-card__metric-value {
  color: #2563eb;
  font-weight: 700;
  font-size: 16px;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.summary-card__reference-value {
  color: #475569;
  font-size: 14px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.summary-card__metric-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 4px 0;
}

.summary-card__metric-row--reference {
  border-top: 1px dashed #e2e8f0;
}

.summary-card__metric-inline-label {
  flex-shrink: 0;
  font-size: 12px;
  color: #64748b;
}

.summary-card__rule {
  margin-top: 8px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(37, 99, 235, 0.08);
  font-size: 11px;
  line-height: 1.5;
  color: #475569;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.summary-card__impact-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e2e8f0;
}

.summary-card__impact-item {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.summary-card__impact-name {
  color: #64748b;
}

.summary-card__impact-range {
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.summary-card__impact-empty {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e2e8f0;
  font-size: 11px;
  color: #94a3b8;
}

.summary-card__impact-more {
  padding-top: 2px;
  font-size: 10px;
  color: #94a3b8;
  text-align: right;
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 8px;
  }
}

@media (max-width: 560px) {
  .summary-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}

.summary-card__status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  margin-left: 8px;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.6) inset;
}
.summary-card__status-dot.status-pass { background: #059669; }
.summary-card__status-dot.status-fail { background: #dc2626; }
.summary-card__status-dot.status-unknown { background: #9ca3af; }

.summary-card--empty {
  cursor: default;
}

.calc-alert {
  margin-bottom: 16px;
  padding: 12px 14px;
  border: 1px solid rgba(248, 113, 113, 0.24);
  border-radius: 14px;
  background: rgba(254, 242, 242, 0.9);
  color: #b91c1c;
  font-size: 13px;
  line-height: 1.6;
}

.scene-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  overflow: auto;
}

.scene-section {
  padding: 16px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.85);
}

.scene-section__header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.scene-section__title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.scene-section__desc {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
}

.formula-card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.formula-card {
  padding: 16px;
  border: 1px solid rgba(191, 219, 254, 0.8);
  border-radius: 18px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.formula-card:hover,
.formula-card.is-active {
  border-color: #2563eb;
  box-shadow: 0 16px 28px rgba(37, 99, 235, 0.12);
}

.formula-card__header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.formula-card__title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.formula-card__meta {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
}

.formula-card__result {
  font-size: 18px;
  font-weight: 700;
  color: #2563eb;
  text-align: right;
}

.formula-card__expression {
  margin: 14px 0;
  padding: 12px 14px;
  border-radius: 14px;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.formula-card__deps-label {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 12px;
  color: #64748b;
}

.formula-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.formula-chip {
  padding: 6px 10px;
  border: 1px solid rgba(191, 219, 254, 0.9);
  border-radius: 999px;
  background: rgba(239, 246, 255, 0.9);
  color: #1d4ed8;
  font-size: 12px;
  cursor: pointer;
}

.formula-card__warning {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(254, 249, 195, 0.9);
  color: #854d0e;
  font-size: 12px;
  line-height: 1.6;
}

.explanation-panel--compact {
  display: flex;
  flex-direction: column;
  gap: 2px;
  height: 100%;
  overflow-y: auto;
  padding: 2px 2px 8px 2px;
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 transparent;
}
.explanation-panel--compact::-webkit-scrollbar { width: 6px; }
.explanation-panel--compact::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.explanation-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 10px 10px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 4px;
}
.explanation-panel__headline {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}
.explanation-panel__chip {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #bfdbfe;
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
  color: #1e40af;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.explanation-panel__title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.35;
  word-break: break-word;
}
.explanation-panel__actions {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.explanation-overview {
  padding: 6px 10px 10px;
  border-bottom: 1px solid #f1f5f9;
}
.explanation-overview__summary {
  font-size: 12px;
  line-height: 1.7;
  color: #475569;
}
.explanation-overview__summary.is-empty {
  color: #94a3b8;
  font-style: italic;
}
.explanation-metrix {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  margin-top: 8px;
  background: #e2e8f0;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
}
.explanation-metrix__item {
  padding: 6px 8px 7px;
  background: #ffffff;
}
.explanation-metrix__item.is-primary {
  background: linear-gradient(180deg, #f8fafc 0%, #eff6ff 100%);
}
.explanation-metrix__label {
  font-size: 10.5px;
  color: #64748b;
  letter-spacing: 0.02em;
}
.explanation-metrix__value {
  margin-top: 3px;
  font-size: 12.5px;
  font-weight: 700;
  line-height: 1.4;
  color: #0f172a;
  word-break: break-word;
}

.explanation-section {
  padding: 8px 10px;
  border-bottom: 1px solid #f1f5f9;
}
.explanation-section:last-child {
  border-bottom: none;
}
.explanation-section__title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 6px;
  padding-top: 2px;
}
.explanation-section__bar {
  display: inline-block;
  width: 3px;
  height: 11px;
  border-radius: 2px;
  background: linear-gradient(180deg, #3b82f6 0%, #6366f1 100%);
}
.explanation-section__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.explanation-line {
  font-size: 12px;
  line-height: 1.65;
  color: #475569;
  padding: 4px 7px;
  border-radius: 4px;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
}
.explanation-line__tag {
  display: inline-block;
  margin-right: 6px;
  padding: 0 6px;
  border-radius: 3px;
  font-size: 10.5px;
  font-weight: 600;
  color: #475569;
  background: #e2e8f0;
}
.explanation-line--note {
  background: #fffbeb;
  border-color: #fef3c7;
  color: #78350f;
}

.explanation-panel__edit-field {
  padding: 6px 10px 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.explanation-edit-section {
  padding: 8px 10px;
  border-radius: 6px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.resource-tiles {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}
.resource-tile {
  padding: 6px 7px 7px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}
.resource-tile--verification_rule {
  grid-column: 1 / -1;
  background: linear-gradient(180deg, #fefce8 0%, #ffffff 100%);
  border-color: #fde68a;
}
.resource-tile__head {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
.resource-tile__chip {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
  background: #e2e8f0;
  color: #334155;
}
.resource-tile--image .resource-tile__chip { background: #ede9fe; color: #5b21b6; }
.resource-tile--text .resource-tile__chip { background: #dbeafe; color: #1e40af; }
.resource-tile--document .resource-tile__chip { background: #dcfce7; color: #166534; }
.resource-tile--verification_rule .resource-tile__chip { background: #fde68a; color: #854d0e; }
.resource-tile__title {
  font-size: 11.5px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.resource-tile__body {
  font-size: 11.5px;
  line-height: 1.55;
  color: #475569;
  min-width: 0;
}
.resource-tile__image {
  max-width: 100%;
  max-height: 120px;
  border-radius: 4px;
  display: block;
}
.resource-tile__text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 110px;
  overflow-y: auto;
}
.resource-tile__link,
.resource-tile__path {
  display: block;
  word-break: break-all;
  color: #2563eb;
  text-decoration: none;
  font-size: 11px;
}
.resource-tile__link:hover { text-decoration: underline; }
.resource-tile__path { color: #64748b; }

.resource-rule-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 11.5px;
  line-height: 1.55;
  padding: 2px 0;
}
.resource-rule-row__label {
  flex-shrink: 0;
  font-size: 10.5px;
  color: #64748b;
  padding-top: 1px;
}
.resource-rule-row__value {
  color: #0f172a;
  font-weight: 500;
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}
.resource-card.edit-mode {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px dashed #cbd5e1;
  background: #f8fafc;
}
.resource-card__type {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.resource-editor {
  margin-top: 8px;
}

.resource-editor :deep(.el-form-item__label) {
  font-weight: 600;
  color: #334155;
  font-size: 12px;
}

.ml-1 {
  margin-left: 4px;
}

.hover-tag {
  transition: all 0.2s ease;
}

.hover-tag:hover {
  opacity: 0.85;
}

.popover-tree-container,
.popover-module-container {
  max-height: 350px;
  overflow-y: auto;
}

/* 亮色工程工作台 */
.whitebox-workbench {
  --wb-bg: #f3f6fb;
  --wb-panel: #ffffff;
  --wb-panel-2: #f8fafc;
  --wb-line: #dbe3ef;
  --wb-line-soft: #e8edf5;
  --wb-text: #0f172a;
  --wb-muted: #64748b;
  --wb-blue: #2563eb;
  --wb-green: #059669;
  --wb-amber: #d97706;
  --wb-red: #dc2626;
  gap: 8px;
  height: calc(100vh - 60px);
  padding: 10px 14px 12px;
  color: var(--wb-text);
  background: linear-gradient(180deg, #f7f9fc 0%, #eef3f8 100%);
}

.workbench-header {
  min-height: 54px;
  padding: 8px 14px;
  border: 1px solid var(--wb-line-soft);
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 10px 24px rgba(148, 163, 184, 0.16);
}

.header-main { gap: 10px; }
.header-eyebrow {
  margin-bottom: 2px;
  color: #64748b;
  font-family: Bahnschrift, "DIN Alternate", sans-serif;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
}
.header-title {
  color: #0f172a;
  font-family: Bahnschrift, "DIN Alternate", "Microsoft YaHei UI", sans-serif;
  font-size: 17px;
  letter-spacing: 0.01em;
}
.back-btn { color: #64748b; }
.back-btn:hover { color: var(--wb-blue); }
.header-meta { gap: 6px; }
.header-meta :deep(.el-tag) {
  height: 24px;
  border-color: #dbe3ef;
  border-radius: 6px;
  color: #475569;
  background: #ffffff;
}
.header-actions { gap: 6px; }
.header-actions :deep(.el-button) {
  border-color: #dbe3ef;
  color: #475569;
  background: #ffffff;
}
.header-actions :deep(.el-button--primary) {
  border-color: var(--wb-blue);
  color: #fff;
  background: var(--wb-blue);
}

.context-strip {
  display: grid;
  grid-template-columns: 180px 180px minmax(220px, 1fr) 150px auto;
  min-height: 42px;
  border: 1px solid var(--wb-line-soft);
  border-radius: 10px;
  background: #ffffff;
  overflow: hidden;
}
.context-field {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 7px 12px;
  border-right: 1px solid var(--wb-line-soft);
}
.context-field span {
  flex: 0 0 auto;
  color: #64748b;
  font-size: 11px;
}
.context-field strong {
  overflow: hidden;
  color: #0f172a;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.context-updated {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 14px;
  color: #64748b;
  font-size: 11px;
  white-space: nowrap;
}

.workbench-body {
  grid-template-columns: 340px minmax(500px, 1fr) 320px;
  gap: 8px;
}
.column { gap: 8px; }
.panel-card {
  border: 1px solid var(--wb-line);
  border-radius: 10px;
  color: var(--wb-text);
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 10px 20px rgba(148, 163, 184, 0.10);
}
.panel-card :deep(.el-card__body) { padding: 10px; }
.panel-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 26px;
  margin: -2px 0 8px;
  padding-bottom: 7px;
  border-bottom: 1px solid var(--wb-line-soft);
  color: #0f172a;
  font-size: 12px;
  font-weight: 700;
}
.panel-section-title::before {
  width: 3px;
  height: 12px;
  margin-right: 7px;
  background: var(--wb-blue);
  content: "";
}
.panel-section-title span { flex: 1; }
.panel-section-title small { color: #64748b; font-size: 10px; }

.whitebox-workbench :deep(.el-input__wrapper),
.whitebox-workbench :deep(.el-select__wrapper),
.whitebox-workbench :deep(.el-textarea__inner) {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  color: #0f172a;
  background: #ffffff;
  box-shadow: none;
}
.whitebox-workbench :deep(.el-input__inner),
.whitebox-workbench :deep(.el-select__selected-item),
.whitebox-workbench :deep(.el-textarea__inner) { color: #0f172a; }
.whitebox-workbench :deep(.el-tabs__item) { color: #64748b; font-size: 11px; }
.whitebox-workbench :deep(.el-tabs__item.is-active) { color: var(--wb-blue); }
.whitebox-workbench :deep(.el-tabs__active-bar) { background: var(--wb-blue); }
.whitebox-workbench :deep(.el-tabs__nav-wrap::after) { background: var(--wb-line-soft); }

.summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 6px;
}
.summary-card {
  min-height: 96px;
  border-color: var(--wb-line);
  border-radius: 5px;
  background: linear-gradient(145deg, #151b23, #0e1319);
}
.summary-card :deep(.el-card__body) { padding: 10px 11px; }
.summary-card:hover {
  transform: none;
  border-color: #46515f;
  box-shadow: inset 0 2px 0 var(--wb-red), 0 8px 18px rgba(0, 0, 0, 0.22);
}
.summary-card.is-active {
  transform: none;
  border-color: var(--wb-blue);
  box-shadow: inset 0 2px 0 var(--wb-blue), 0 0 0 2px rgba(37, 99, 235, 0.3), 0 8px 18px rgba(0, 0, 0, 0.25);
}
.summary-card.is-pass,
.summary-card.is-fail,
.summary-card.has-warning { background: linear-gradient(145deg, #151b23, #0e1319); }
/* 状态栏配色：通过左侧状态条 + 数值色区分通过/未通过/缺失 */
.summary-card.is-pass { border-left: 2px solid var(--wb-green); }
.summary-card.is-pass .summary-card__metric-value { color: var(--wb-green); }
.summary-card.is-fail { border-left: 2px solid var(--wb-red); }
.summary-card.is-fail .summary-card__metric-value { color: var(--wb-red); }
.summary-card.has-warning { border-left: 2px solid var(--wb-warn, #d97706); }
.summary-card.has-warning .summary-card__metric-value { color: var(--wb-warn, #d97706); }
.summary-card__header { margin-bottom: 8px; }
.summary-card__label { color: #aeb7c3; font-size: 11px; }
.summary-card__empty-note { margin-top: 14px; color: #596574; font-size: 10px; line-height: 1.5; }
.summary-card--status { border-left: 2px solid var(--wb-green); }
.summary-card__metric-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 4px 0;
}
.summary-card__metric-row--reference {
  border-top: 1px dashed rgba(148, 163, 184, 0.2);
}
.summary-card__metric-inline-label {
  color: #7c8a99;
  font-size: 11px;
}
.summary-card__rule {
  margin-top: 8px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(37, 99, 235, 0.14);
  font-size: 10px;
  line-height: 1.5;
  color: #8fa3bd;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.summary-card__impact-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}
.summary-card__impact-item {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 10px;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.summary-card__impact-name { color: #7c8a99; }
.summary-card__impact-range {
  color: #dbe5f1;
  font-variant-numeric: tabular-nums;
}
.summary-card__impact-empty {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
  font-size: 10px;
  color: #596574;
}

.summary-card__impact-more {
  padding-top: 2px;
  font-size: 10px;
  color: #596574;
  text-align: right;
}

.focus-metric-range-fields {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.focus-metric-range-fields :deep(.el-input) {
  flex: 1;
}

.focus-metric-range-separator {
  flex-shrink: 0;
  color: #64748b;
  font-size: 12px;
}

/* 参数区间提示 */
.focus-metric-range-hint {
  font-size: 11px;
  color: #7c8a99;
  margin-top: 4px;
  line-height: 1.4;
}
.focus-metric-range-count {
  color: #5a6a7a;
  font-size: 10px;
}

.left-tree-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
  height: calc(100% - 52px);
  min-height: 0;
}

.tree-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.tree-section--selection {
  flex: 1;
  min-height: 220px;
  padding-top: 4px;
  border-top: 1px solid #e2e8f0;
}

.tree-section__title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.tree-section__title strong {
  font-size: 13px;
  color: #0f172a;
}

.tree-section__title span {
  font-size: 11px;
  color: #64748b;
}

.tree-section__title--right {
  margin-bottom: 10px;
}

.workspace-mode-bar {
  height: 40px;
  padding: 0 12px;
  border-color: #dbe2ea;
  background: #f8fafc;
}

.workspace-mode-bar :deep(.el-radio-button__inner) {
  border-color: #d6dde8;
  color: #475569;
  background: #ffffff;
  box-shadow: none;
}

.workspace-mode-bar :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  border-color: #2563eb;
  color: #2563eb;
  background: #eff6ff;
  box-shadow: -1px 0 0 0 #2563eb;
}

.workspace-mode-bar__meta {
  color: #64748b;
  font-size: 12px;
}

.workspace-model-canvas {
  min-height: 0;
  height: calc(100% - 40px);
}

.workspace-flow-canvas {
  background-color: #f8fafc;
  background-image: radial-gradient(#d5dce7 0.7px, transparent 0.7px);
}

.calc-alert {
  border-radius: 8px;
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.model-preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 0 14px;
  border-bottom: 1px solid #dbe2ea;
  background: #f8fafc;
}
.model-preview-head strong { display: block; color: #0f172a; font-size: 13px; }
.model-preview-head span { color: #64748b; font-size: 11px; }
.model-preview-badge { color: #2563eb !important; font-family: Consolas, monospace; letter-spacing: .08em; }
.model-preview-stage {
  position: relative;
  height: calc(100% - 44px);
  overflow: hidden;
  background:
    linear-gradient(rgba(148,163,184,.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148,163,184,.12) 1px, transparent 1px),
    radial-gradient(circle at 50% 45%, #ffffff, #eef3f8 70%);
  background-size: 24px 24px, 24px 24px, auto;
}
.drum-illustration {
  position: absolute;
  left: 50%;
  top: 52%;
  width: 430px;
  height: 110px;
  transform: translate(-50%, -50%);
  filter: drop-shadow(0 16px 14px rgba(148, 163, 184, 0.35));
}
.drum-shell {
  position: absolute;
  left: 58px;
  top: 17px;
  width: 275px;
  height: 72px;
  border: 1px solid #94a3b8;
  border-radius: 38px;
  background: linear-gradient(180deg, #cfd8e3 0%, #a9b6c6 30%, #8ea0b6 72%, #d8e0ea 100%);
  transform: skewX(-6deg);
}
.drum-ring {
  position: absolute;
  top: 8px;
  width: 24px;
  height: 90px;
  border: 5px solid #2563eb;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.10);
  box-shadow: inset 0 0 0 2px #93c5fd, 0 0 10px rgba(37,99,235,.12);
}
.drum-ring--left { left: 66px; }
.drum-ring--right { left: 289px; }
.drum-axis { position: absolute; left: 33px; top: 49px; width: 335px; height: 9px; background: #94a3b8; box-shadow: 0 2px 0 rgba(100, 116, 139, 0.25); }
.drum-motor {
  position: absolute;
  right: 4px;
  top: 42px;
  width: 88px;
  height: 45px;
  border-radius: 4px 24px 24px 4px;
  background: repeating-linear-gradient(90deg, #93c5fd 0 5px, #60a5fa 5px 9px);
  box-shadow: inset 0 -8px 0 rgba(37,99,235,.18);
}
.drum-base { position: absolute; left: 27px; right: 8px; bottom: 2px; height: 10px; transform: skewX(-20deg); background: #cbd5e1; box-shadow: 0 5px 0 rgba(148, 163, 184, 0.35); }
.model-preview-hint { position: absolute; right: 10px; bottom: 8px; color: #64748b; font-size: 11px; }

.explanation-panel--compact { scrollbar-color: #cbd5e1 transparent; }
.explanation-panel__head { border-color: #dbe2ea; }
.explanation-panel__chip { border-color: #bfdbfe; color: #2563eb; background: #eff6ff; }
.explanation-panel__title,
.explanation-section__title,
.explanation-metrix__value,
.resource-tile__title,
.resource-rule-row__value { color: #0f172a; }
.explanation-overview,
.explanation-section { border-color: #dbe2ea; }
.explanation-overview__summary,
.explanation-line,
.resource-tile__body { color: #64748b; }
.explanation-metrix { border-color: #e2e8f0; background: #e2e8f0; }
.explanation-metrix__item,
.explanation-metrix__item.is-primary,
.resource-tile { color: #334155; background: #f8fafc; }
.explanation-line { border-color: #e2e8f0; background: #f8fafc; }
.explanation-section__bar { background: #2563eb; }

@media (max-width: 1400px) {
  .workbench-body {
    grid-template-columns: 340px minmax(0, 1fr);
  }

  .column-right {
    grid-column: 1 / -1;
  }
}

@media (max-width: 1080px) {
  .workbench-header {
    grid-template-columns: 1fr;
  }

  .header-actions {
    justify-content: flex-start;
  }

  .workbench-body {
    grid-template-columns: 1fr;
  }

  .explanation-metrix,
  .resource-tiles {
    grid-template-columns: 1fr;
  }
}
</style>
