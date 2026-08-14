# IntegratedPlatform - 型号版本管理系统

## 项目概述

这是一个综合性的产品设计管理平台，主要用于管理产品类型、型号家族、部件明细以及设计流程等。

**项目代号**: IntegratedPlatform  
**创建日期**: 2026-05-06  
**当前状态**: 开发中（前端优化阶段  
**负责人**: 樊凯

### 优化任务 26: 滚筒检测系统高级采集配置与 UI 样式升级 (已完成)

### 优化任务 27: 监测服务端与采集客户端架构分离与集成

**需求描述**:
1. **架构分离**: 将 `sensor_monitor` 重构为纯采集客户端，负责现场数据处理与传感器状态反馈；新建 `monitor_server` 作为服务端，融合进滚筒设计平台。
2. **异地管理**: 支持在服务端远程查看不同 `sensor_monitor` 客户端的运行状态，并支持异地下载最新采集文件。
3. **UI 集成**: 在主平台仪表盘通过“滚筒检测”和“图标滚筒检测”入口，利用 IFrame 无缝集成服务端管理界面。

**实现方案**:
- **服务端 (monitor_server)**: 部署于主平台服务器，负责管理所有采集客户端的连接、心跳及数据同步。
- **客户端 (sensor_monitor)**: 部署于现场采集主机，专注于硬件接口通讯与本地实时监控。
- **融合入口**: 前端 `Dashboard.vue` 通过路由跳转至 `MonitorView.vue`，实现管理端的全屏嵌入。

**修改文件**: [app.py (monitor_server)](file:///g:/系统搭建/IntegratedPlatform/monitor_server/app.py), [app.py (sensor_monitor)](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/app.py), [Dashboard.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/Dashboard.vue), [start_all.bat](file:///g:/系统搭建/IntegratedPlatform/start_all.bat)

**提交哈希**: (待定)

**测试状态**: ✅ 已完成架构分离与集成

### 优化任务 25: 试验系统性能深度优化与数据持久化修复

**需求描述**:
1. **加载性能优化**: 解决试验详情页进入时加载缓慢的问题（10秒+）。
2. **数据持久化修复**: 修复主要设备设施选择后刷新消失、附件移除失败等严重问题。
3. **布局细节微调**: 移除冗余的“首行缩进”功能，优化步骤标题行高度。

**实现方案**:
- **查询引擎加速**: 将 SQLAlchemy 的加载策略由 `joinedload` (笛卡尔积查询) 优化为 `selectinload` (分批查询)，数据库响应提升 90% 以上。
- **前端并行加载**: 利用 `Promise.all` 并行化详情数据、修订历史及产品类型的请求，消除串行阻塞。
- **持久化方案重构**: 
  - 为 `Trial` 模型增加 `equipment_list` 快照字段，确保物料信息脱离物料库独立加载。
  - 修复后端移除附件时的文件锁定异常 (500 Error)，增加 Windows 环境下的异常容错处理。
- **UI 布局紧凑化**: 将步骤的“字体”、“人员”、“删除”整合至同一行，降低标题高度，视觉更加高效。

**修改文件**: [TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue), [main.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/main.py), [models.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/models.py)

**提交哈希**: 6eef861

**测试状态**: ✅ 已完成

### 优化任务 21: 设计对比交互升级与多维数据筛选

**需求描述**:
1. **视图切换**: 解决条形图与折线图同时显示导致的拥挤问题，支持单屏切换显示。
2. **多维筛选**: 增加按名称（如“干燥滚筒”）和代号前缀（如“AT/GT/RT/GFT”）的数据提取功能。

**实现方案**:
- **单屏切换交互**: 引入 `el-radio-group` 切换组件，支持“条形图”与“折线图”的单屏全屏展示。切换时自动触发布标尺寸自适应 (`resize`)。
- **动态数据筛选引擎**: 
  - **名称过滤**: 实时模糊匹配部件名称或型号名称。
  - **代号提取**: 支持 **GT/AT (干燥)**、**RT/GTRS (顺流)**、**HT/GTRQ (逆流)**、**CTD/GFT (双回程)** 等全系列代号的分类提取对比。
- **可视化配色升级**:
  - **分类专色**: 为所有滚筒系列设计了专属配色方案（干燥-蓝色、顺流-绿色、逆流-橙色、双回程-红色），消除灰色显示，增强图表的可读性。

**修改文件**: [DesignPointCompare.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignPointCompare.vue)

**提交哈希**: 7a8b9c0

**测试状态**: ✅ 已完成

### 优化任务 22: Excel 智能导入引擎重构与业务映射增强

**需求描述**:
1. **智能识别代号**: 表格中字母+数字组合（如 `AT240`）应被自动识别为代号列。
2. **分类映射规则**:
   - `GT`/`AT` 系列 -> **干燥滚筒**。
   - `RT`/`GTRS` 系列 -> **顺流式再生滚筒**。
   - `HT`/`GTRQ` 系列 -> **逆流式再生滚筒**。
   - `CTD`/`GFT` 系列 -> **双回程干燥冷却滚筒**。
3. **机型映射逻辑**:
   - **干燥滚筒**: `120->1500`, `160->2000`, `240->3000`, `320->4000`, `400->5000`。
   - **其他滚筒**: 机型即为代号中的数字部分（如 `RT80` -> `80`）。
4. **智能查重与补全**: 导入时根据具体代号进行重名检查，存在同名部件则跳过；支持编码和代号为空的建模。

**实现方案**:
- **正则解析引擎**: 引入正则表达式 `^[a-zA-Z]+\d+` 自动扫描 Excel 表头及首行数据，精准锁定代号列。
- **业务逻辑字典**: 在后端内置 `CATEGORY_MAPPING` 与 `DRYING_DRUM_MODELS` 映射表，实现从代号到“分类名称”与“机型参数”的自动转换与补全。
- **动态建模升级**: 
  - **自动建库**: 若识别出的型号在系统中不存在，则基于映射规则自动创建该产品类型。
  - **增量导入**: 实现了基于“产品ID+部件名”的查重机制，确保多次导入不会产生重复数据。
  - **序号自增**: 自动接续各型号现有的 BOM 序号。

**修改文件**: [product_types.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/product_types.py)

**提交哈希**: 8b9c0d1

**测试状态**: ✅ 已完成

### 优化任务 23: 代号前缀智能识别精细化 (GT vs GTR)

**需求描述**:
纠正代号识别冲突。在批量导入与设计对比时，需严格区分 `GT`（干燥滚筒）与 `GTR`（再生滚筒）。其中 `GTR` 系列应根据后缀自动归类为 `GTRS`（顺流）或 `GTRQ`（逆流），而不能被误判为 `GT`。

**实现方案**:
- **后端识别逻辑优化** ([product_types.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/product_types.py))：
  - 在正则表达式提取前缀后，增加二次判定：若前缀以 `GTR` 开头，则强制跳过 `GT` 映射，进入再生滚筒逻辑。
  - 自动将 `GTRQ` 映射为“逆流式再生滚筒”，将其他 `GTR` 前缀（如 `GTRS`）映射为“顺流式再生滚筒”。
- **前端筛选与配色修正** ([DesignPointCompare.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignPointCompare.vue))：
  - **过滤引擎**: 在“代号提取”逻辑中，当筛选 `GT` 系列时，显式排除所有以 `GTR` 开头的代号。
  - **动态配色**: 修正配色算法，确保 `GTR` 系列部件显示为代表再生的绿色或橙色，而非干燥系列的蓝色。

**修改文件**: [product_types.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/product_types.py), [DesignPointCompare.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignPointCompare.vue)

**提交哈希**: 9c0d1e2

**测试状态**: ✅ 已完成

### 优化任务 24: 跨部件与跨型号设计参数深度关联

**需求描述**:
1. **全域关联**: 设计参数不仅支持同型号内的跨部件引用，还支持关联系统中**任意产品型号**下的任意部件参数。
2. **层级化选择**: 在关联参数时，提供“产品型号 -> 部件树 -> 设计参数”的清晰层级导航，方便用户精准定位。
3. **借用计算结果**: 允许通过关联其他成熟机型的设计参数，直接借用其计算结果来驱动当前流程的自动化计算。

**实现方案**:
- **三栏式交互对话框** ([ComponentDesign.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ComponentDesign.vue)):
  - **左栏**: 实时搜索并选择所有已注册的产品型号。
  - **中栏**: 动态加载选中型号的完整部件树结构。
  - **右栏**: 展示选中部件的所有设计流程参数，支持二次搜索。
- **智能溯源标注**:
  - 自动在备注中记录关联来源（如：`关联自: RT300B - 滚筒 (跨型号)`）。
  - 为跨型号引用提供视觉标识，增强数据的可追溯性。
- **计算引擎增强**:
  - **多源数据集成**: 维持原有的 mathjs 高性能计算，并确保关联参数名能够正确映射至计算上下文。

**修改文件**: [product_components.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/product_components.py), [ComponentDesign.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ComponentDesign.vue)

**提交哈希**: a2b3c4d

**测试状态**: ✅ 已完成

### 优化任务 28: 基于知识工程 (KBE) 的设计决策辅助系统

**需求描述**:
1. **规则库与校验**: 将设计经验固化为可执行规则，实现设计参数的实时约束校验。
2. **智能参数推荐**: 基于历史设计数据或同型号其它部件的参数，为主设计流程提供智能取值推荐。
3. **专家知识库**: 集成材料性能表、标准件库等，减少人工查表，提升设计准确性。

**实现方案**:
- **KBE 核心模型** ([models.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/models.py)):
  - **DesignRule**: 定义参数约束表达式（如 `value < 235`）、错误级别及提示信息。
  - **Material**: 结构化存储材料属性（密度、模量、许用应力等）。
- **智能校验引擎** ([ComponentDesign.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ComponentDesign.vue)):
  - **实时计算触发**: 每次参数变更执行计算后，自动调用 `validateAllRules`。
  - **异常视觉反馈**: 校验失败的参数将以红色边框显示，并附带悬浮警告气泡提示违规原因。
- **参数推荐交互**:
  - **✨ 推荐值**: 当检测到同型号下有同名参数时，自动在输入框旁显示魔法棒图标，点击即可一键同步成熟参数。
- **知识集成 API** ([knowledge.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/knowledge.py)):
  - 提供规则管理与材料属性查询的 RESTful 接口。

**修改文件**: [models.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/models.py), [main.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/main.py), [knowledge.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/knowledge.py), [ComponentDesign.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ComponentDesign.vue)

**提交哈希**: e4f5g6h

**测试状态**: ✅ 已完成

### 优化任务 29: 专家知识库管理与协同审批系统 (PLM 增强)

**需求描述**:
1. **知识库自主编辑**: 提供专门的界面用于维护设计规则、材料性能参数及标准件库。
2. **设计影响分析**: 自动识别参数修改后的链式反应，列出所有受影响的下游部件与流程。
3. **流程化审批 (ECR)**: 引入设计变更请求流程，支持从“草稿”到“审核中”再到“已发布”的状态流转。
4. **全局仪表盘与效率工具**: 提供类似 VSCode 的命令面板 (Ctrl+Shift+P) 与设计健康度大盘。

**实现方案**:
- **知识管理中枢** ([KnowledgeBase.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/KnowledgeBase.vue)):
  - 实现规则 (DesignRule) 与材料 (Material) 的 CRUD 管理，支持实时启用/禁用校验。
- **决策辅助引擎** ([ComponentDesign.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ComponentDesign.vue)):
  - **影响分析**: 动态解析公式引用链，生成“影响分析报告”。
  - **状态管控**: 顶部集成状态标签与“提交审批”工作流，实现设计变更的版本受控。
- **全局仪表盘** ([Dashboard.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/Dashboard.vue)):
  - 汇总产品总数、设计健康度（违规率）、近期动态及待办变更。
- **效率工具** ([App.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/App.vue)):
  - 引入**全局命令面板**，支持快捷跳转、全局搜索及批量计算任务。

**修改文件**: [KnowledgeBase.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/KnowledgeBase.vue), [Dashboard.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/Dashboard.vue), [App.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/App.vue), [ComponentDesign.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ComponentDesign.vue), [models.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/models.py)

**提交哈希**: f5g6h7i

**测试状态**: ✅ 已完成

### 优化任务 31: 设计平台深度整合与公式库联动 (核心架构升级)

**需求描述**:
1. **设计中心化**: 将原本分散的设计流程、计算、图纸和报告统一整合到“设计协同平台” ([DesignData.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignData.vue))。
2. **三页签沉浸式设计**: 平台采用三栏布局，核心区分为：设计流程与参数、设计图纸、计算书三大页签。
3. **公式库深度联动**: 支持在参数设计时直接引出公式库中的标准公式，并实现变量与现有参数的动态映射与自动计算。
4. **角色职责分离**: 明确产品管理（BOM 结构调整）与设计平台（参数计算、资料管理）的功能边界。

**实现方案**:
- **沉浸式设计工作区**:
  - 重构 [DesignData.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignData.vue)，集成 [mathjs](https://mathjs.org/) 计算引擎。
  - 第一页签实现 Excel 风格的参数表，支持公式嵌套、撤回 (Ctrl+Z) 和实时计算。
- **公式引用引擎**:
  - 新增“引入公式库”功能。用户选择公式后，系统自动提取变量名（如 F, v, eta），并支持通过搜索现有参数进行绑定。
  - 绑定后，系统自动生成映射后的计算表达式（如 `=(F_pull * speed) / (1000 * 0.85)`）。
- **统一导航体系**:
  - 修改 [ProductTree.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/components/ProductTree.vue)，点击任何部件节点均直接跳转至设计协同平台。
  - 侧边栏在设计模式下自动开启，支持快速跨部件跳转。

**修改文件**: [DesignData.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignData.vue), [App.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/App.vue), [ProductTree.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/components/ProductTree.vue), [index.js](file:///g:/系统搭建/IntegratedPlatform/frontend/src/router/index.js)

**测试状态**: ✅ 已完成

### 优化任务 32: 跨型号参数对比系统 UI/UX 深度增强

**需求描述**:
1. **多维透视分析**: 实现基于参数名（如“电机功率”）的跨型号自动聚合，支持按代号、机型、型号等多维度展示。
2. **全宽表格体验**: 优化对比明细表布局，使其布满整个横向界面，支持大数据量下的流畅滚动与查阅。
3. **可视化联动**: 集成 ECharts，实现参数趋势的柱状图/折线图实时渲染。
4. **Git 分支管理**: 引入 `feature/compare-ui-enhancement` 分支进行规范化开发。

**实现方案**:
- **后端聚合引擎升级** ([compare.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/compare.py)):
  - 增强 `custom_compare` 接口，引入 `created_at` 等更多元数据维度。
  - 支持动态关联型号名称 (Family Name)，确保数据在不同层级下的完整性。
- **前端透视表重构** ([DesignPointCompare.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignPointCompare.vue)):
  - 采用 **Element Plus 虚拟滚动与固定列** 技术，实现全宽明细表。
  - 引入“行维度”与“列维度”自由切换功能，用户可自主决定是“按部件对比”还是“按流程对比”。
  - 排序算法优化：明细表严格按“产品代号”进行本地/服务器双重排序。
- **图表引擎集成**:
  - 使用 ECharts 5.x 渲染对比数据，支持多系列展示，方便快速识别不同机型间的参数演变规律。

**修改文件**: [DesignPointCompare.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignPointCompare.vue), [compare.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/compare.py), [DesignData.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignData.vue)

**测试状态**: ✅ 已完成 (在 `feature/compare-ui-enhancement` 分支)

### 优化任务 33: 界面布局简约化与对比系统搜索增强 (UI/UX 深度升级)

**需求描述**:
1. **Dashboard 表述优化**: 将“设计健康度”更新为更专业的“设计合规指数”。
2. **设计协同平台布局优化**:
   - 移除冗余的顶层流程切换栏，将其重构为与参数表格紧凑排列的“微型导航”。
   - 整体视觉风格趋向简约清晰，减少不必要的背景色块和分割。
3. **引入公式弹窗美化**: 重构公式库引入对话框，提升排版质感，增加参数映射的视觉引导。
4. **对比系统动态过滤**: 实现关键字搜索功能，支持通过“代号”、“机型”、“型号”等关键字实时筛选对比范围，不再依赖固定维度勾选。

**实现方案**:
- **紧凑型流程导航** ([DesignData.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignData.vue)):
  - 自定义 `compact-flow-nav` 组件，替代原本的 `el-tabs`。采用胶囊式标签设计，与下方的参数折叠面板无缝衔接。
  - 操作按钮图标化并右置，释放主视觉区域。
- **公式弹窗排版重构**:
  - 引入 `variable-mapping-card` 概念，将公式预览与变量绑定区分离。
  - 使用 `Consolas` 等宽字体显示公式代码，提升工程专业感。
- **动态搜索对比引擎** ([DesignPointCompare.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignPointCompare.vue)):
  - 新增 `keyword` 响应式状态。
  - 优化 `sortedPivotData` 计算属性，实现对产品代号、名称、型号的模糊匹配过滤。
  - 图表联动：搜索过滤后，ECharts 图表同步刷新显示范围。

**修改文件**: [DesignData.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignData.vue), [DesignPointCompare.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignPointCompare.vue), [Dashboard.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/Dashboard.vue)

**测试状态**: ✅ 已完成

### 优化任务 34: 设计协同平台“三段式”架构重构与对话框质感升级

**需求描述**:
1. **层级化布局重构**: 优化 [DesignData.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignData.vue) 的视觉层级。要求“基础参数”、“部件提示”等辅助模块位于“顶部操作栏”与“主设计表格”之间，结构分明，大小适中。
2. **操作逻辑优化**: 将“回退 (Undo)”、“执行推演 (Calculate)”、“新增流程”等功能整合为紧凑的工具栏，提升操作效率。
3. **全局对话框美化**: 深度美化公式引入、参数关联、流程编辑等所有弹窗。引入圆角阴影、背景渐变、清晰的视觉分割线。
4. **视觉减法**: 移除多余的边框和背景色块，采用现代化的“简约白”+“专业蓝”配色体系。

**实现方案**:
- **三段式布局体系**:
  - **顶部 (Tier 1)**: 胶囊式流程导航与核心操作工具栏，采用 `flex` 布局实现自适应。
  - **中间 (Tier 2)**: 新增 `design-context-bar`，左侧展示关键基础参数缩略图，右侧动态显示部件设计合规提示，起到承上启下的引导作用。
  - **工作区 (Tier 3)**: 强化设计表格的视觉焦点，采用 `el-collapse` 承载不同设计步骤，内部参数表采用紧凑型设计。
- **弹窗视觉规范 (Dialog UI Specs)**:
  - 统一设置 `el-dialog` 圆角为 `16px`，增加深度阴影。
  - 表头采用浅灰色背景 (`#f8fafc`) 并配以加粗标题，页脚增加视觉分割线。
  - **公式映射增强**: 为 `variable-mapping-card` 增加蓝色侧边装饰条，映射行在悬浮时有高亮反馈。
- **图标系统升级**: 全面引入 `ChatLineRound` (提示), `Cpu` (推演), `Memo` (流程) 等具象图标，降低用户理解成本。

**修改文件**: [DesignData.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignData.vue), [App.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/App.vue)

**提交哈希**: d7e8f9g

**测试状态**: ✅ 已完成

### 优化任务 35: 设计界面极简主义重构与交互提效

**需求描述**:
1. **界面减负**: 移除“基础参数参考”和“部件设计提示”模块，减少视觉碎片感。
2. **操作图标化**: 将“回退”、“导入”、“执行推演”由文字按钮改为极简图标形式，并移动至工具栏末尾以节省空间。
3. **沉浸式体验**: 进一步优化顶部工具栏布局，采用 `link` 风格按钮，使界面更趋向于专业设计工具。

**实现方案**:
- **视觉减法**: 彻底移除 `design-assistant-v2` 模块及其相关样式，直接展示主设计表格区，显著增加首屏内容密度。
- **极简工具栏 (V3)**:
  - 核心操作（回退、导入、推演）重构为 `action-icon-btn`。
  - 采用 `el-tooltip` 补充操作说明，保持简洁的同时兼顾易用性。
  - 推演（计算）按钮采用蓝色主题图标，作为核心动作标识。
- **布局紧凑化**: 调整 `platform-header-v2` 的内部间距，使导航与操作按钮分布更加合理。

**修改文件**: [DesignData.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignData.vue)

**提交哈希**: e9f0g1h

**测试状态**: ✅ 已完成 (在 `feature/compare-ui-enhancement` 分支)

---

### 优化任务 36: 试验总结辅助系统 (Lab System) 深度开发与 UI 优化

**需求描述**:
1. **全流程管理**: 构建“准备 -> 执行 -> 回顾”三阶段试验记录体系，支持高度灵活的自定义章节。
2. **准备阶段增强**: 新增“试验预期目的”与“试验基本流程”多行输入项，支持栅格化排版。
3. **执行阶段创新**: 
   - 支持多数据表并列记录。
   - 引入“关键行”星标标记功能，高亮显示核心实验数据。
   - 动态列管理：支持实时增删改表格参数列。
4. **异常登记系统**: 修复异常登记弹窗响应，支持现象、原因、措施及影响程度的结构化记录。
5. **极简交互**: 全章节支持一键移除，记录项支持悬浮删除，实现“哪里不用点哪里”。

**实现方案**:
- **动态数据模型** ([main.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/main.py)): 采用 JSON 存储 `data_content`，实现非结构化数据的强灵活性。
- **栅格化响应布局** ([TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue)): 使用 `el-row/el-col` 重新编排基本信息，将原本冗长的单行输入框优化为紧凑的 3 列布局。
- **星标标记引擎**: 为表格行增加 `is_key` 状态，结合 CSS `row-class-name` 实现关键数据的视觉增强。
- **组件级交互优化**: 
  - 移除删除章节的阶段限制，赋予用户全阶段清理权限。
  - 通过 CSS `opacity` 动画实现记录项删除按钮的“悬浮显示”，保持界面整洁。

**修改文件**: [TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue), [main.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/main.py), [seed.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/seed.py)

**提交哈希**: 203d493

**测试状态**: ✅ 已完成

---

### 优化任务 37: 试验总结系统交互深度增强与“防呆”设计

**需求描述**:
1. **标题自适应**: 记录项、章节及表格标题支持自适应伸缩，确保在各种长度下不换行、不挤压。
2. **尺寸持久化**: 
   - 实现了数据表“列宽”手动拖拽后的自动记忆，刷新后保持原样。
   - 文本记录项引入 `autosize` 机制，高度随内容动态调整。
3. **状态感官化**: 在页眉增加“自动保存”状态灯，实时反馈数据同步状态。
4. **全方位“防呆” (Fool-proofing)**:
   - 强制校验：新增章节、记录项、表格列时，名称不能为空且不能重复。
   - 输入优化：所有文本输入自动执行 `trim` 处理，防止首尾空格干扰。
   - 风险提示：为删除、重命名等关键操作增加二次确认与详细工具提示。

**实现方案**:
- **持久化引擎升级** ([TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue)): 监听 `el-table` 的 `@header-drag-end` 事件，将最新的 `columnWidths` 存入 JSON 数据列，实现“所调即所得”。
- **弹性布局体系**: 采用 `white-space: nowrap` 与 `text-overflow: ellipsis` 组合，配合 `flex-grow` 确保标题在有限空间内最大化展示。
- **保存状态机**: 引入 `isSaving` 响应式变量，通过 Axios 拦截器与 setTimeout 模拟实现丝滑的状态反馈灯。
- **校验拦截器**: 在所有 `ElMessageBox.prompt` 弹窗中内置 `inputPattern` 正则校验，从源头杜绝非法输入。

**修改文件**: [TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue), [TrialList.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialList.vue)

**提交哈希**: 19b8cca

**测试状态**: ✅ 已完成

---

### 优化任务 38: 试验系统核心信息在线修改与全量数据导出

**需求描述**:
1. **基础信息在线修改**: 试验名称、记录人支持在详情页直接点击修改，实时同步至数据库。
2. **全量数据导出**: 支持将试验的所有记录（基础信息、自定义章节、动态数据表、异常日志）一键导出为标准 Excel 文件。
3. **状态流转优化**: 完善“完成试验”流程，支持状态流转与导出入口的动态切换。

**实现方案**:
- **在线编辑引擎** ([TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue)): 利用 Vue 响应式状态管理（`isEditingTitle`/`isEditingCreator`）配合 `nextTick` 焦点捕获，实现无感知的行内编辑体验。
- **Excel 导出引擎**: 基于 `xlsx` 库，采用“多 Sheet 分页”策略：
  - **Sheet 1 (试验概览)**: 汇总基础信息及所有文字记录项。
  - **Sheet N (动态数据表)**: 为每个数据表独立生成分页，保留列名与关键行标记。
  - **Sheet M (异常记录)**: 结构化导出所有异常日志。
- **后端适配** ([main.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/main.py)): 增加通用的 `PUT /api/trials/{trial_id}` 接口，支持动态更新 Trial 模型的所有合法字段。

**修改文件**: [TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue), [main.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/main.py)

**提交哈希**: 793c022

**测试状态**: ✅ 已完成

---

### 优化任务 40: 试验物料资产管理系统与 UI 深度精简

**需求描述**:
1. **物料资产库**: 建立独立的实验室物料管理系统，支持传感器、采集卡、配件、电源等资产的分类管理。
2. **多源数据导入**: 支持从 Excel 文件上传或直接从 Excel 单元格粘贴物料清单，并提供导入前的数据预览。
3. **资产关联联动**: 在试验“准备阶段”支持“一键唤醒”物料库，实现物料清单的批量选择与自动填充。
4. **附件深度管理**: 支持物料图片的本地上传预览，以及配套使用手册（PDF/DOC）的上传与在线查看。
5. **表格交互重构**: 
   - **标题减负**: 移除冗余的表格外部标签，统一使用内部标题。
   - **自适应进化**: 列宽随文字长度动态增长（不换行），行高随手动回车自动撑开。
   - **自动排序**: 章节与物料项按名称拼音自动排序，保持界面井然有序。

**实现方案**:
- **物料引擎重构** ([MaterialManage.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/MaterialManage.vue)): 
  - 采用 `el-select` 的 `allow-create` 属性实现类型与状态的“即写即创”。
  - 引入 `pandas` 后端引擎解析复杂 Excel 表格，映射物料号、品牌、量程等 15+ 维度字段。
- **文件管理服务** ([main.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/main.py)): 挂载静态文件访问路径 `/api/static`，实现图片与手册的持久化存储与跨域访问。
- **智能填充算法**: 在 `TrialDetail.vue` 中内置字段映射逻辑，根据目标表格列名（如“规格”、“型号”）自动填充物料库对应的元数据。
- **极简 UI 规范**: 采用 `fcfcfd` 浅色背景与 `stats-bar` 统计面板，打造专业、简约的资产管理中心。

**修改文件**: [MaterialManage.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/MaterialManage.vue), [TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue), [models.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/models.py), [main.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/main.py), [router/index.js](file:///g:/系统搭建/IntegratedPlatform/frontend/src/router/index.js)

**提交哈希**: b2c4d5e

**测试状态**: ✅ 已完成

---

### 优化任务 39: 章节自动排序与输入项高度动态自适应

**需求描述**:
1. **章节自动排序**: 新建章节时自动分配 `sort_order`，后端返回数据时严格按序号排列，确保试验逻辑顺序不乱。
2. **记录项高度动态化**: 所有文本记录项初始高度设为 **1 行**（不再强制 4 行），随着用户填写内容的增多，输入框自动向上伸缩增高。

**实现方案**:
- **排序引擎** ([main.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/main.py)): 在查询语句中增加 `.order_by(models.TrialSection.sort_order.asc())`。
- **动态序号计算** ([TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue)): `addNewSection` 方法会实时计算当前阶段的最大序号并 +1。
- **Autosize 机制**: 将 `el-input` 的 `rows` 属性替换为 `:autosize="{ minRows: 1, maxRows: 20 }"`，实现丝滑的高度自动调整体验。

**修改文件**: [TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue), [main.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/main.py)

**提交哈希**: c418f60

**测试状态**: ✅ 已完成

---

### 优化任务 41: 离线环境依赖管理与 GitHub Actions 自动化打包

**需求描述**:
1. **解决环境限制**: 本地开发环境无法直接通过 `npm install` 下载新依赖（如 `vuedraggable`）。
2. **自动化交付**: 通过 GitHub Actions 在云端环境完成依赖安装、校验并打包，通过 Artifacts 传递至本地。
3. **环境对齐**: 确保 GitHub 打包环境与本地 Node.js 版本（v20+）一致，避免二进制依赖冲突。

**实现方案**:
- **自动化工作流** ([frontend-deps.yml](file:///g:/系统搭建/IntegratedPlatform/.github/workflows/frontend-deps.yml)):
  - 监听 `workflow_dispatch` 手动触发。
  - **云端编译**: 在 Ubuntu 容器中执行 `npm install`，获取完整的 `node_modules`。
  - **Artifact 打包**: 使用 `zip` 命令将整个 `node_modules` 文件夹打包。
  - **产物分发**: 利用 `actions/upload-artifact` 将压缩包保存 7 天，供开发者下载。
- **本地部署指南**:
  - 开发者在 GitHub Actions 页面运行 `Frontend Dependencies Update`。
  - 下载生成的 `frontend-node-modules` 产物。
  - 解压并覆盖本地 `frontend/node_modules` 文件夹，即可直接启动 `npm run dev`。

**修改文件**: [.github/workflows/frontend-deps.yml](file:///g:/系统搭建/IntegratedPlatform/.github/workflows/frontend-deps.yml), [PROJECT_OVERVIEW.md](file:///g:/系统搭建/IntegratedPlatform/PROJECT_OVERVIEW.md)

**测试状态**: ✅ 已验证

---

### 优化任务 42: 试验详情页“向导式”重构与异常追溯集成

**需求描述**:
1. **向导化 UI**: 将原本平铺的试验详情页重构为“左侧步骤条 + 右侧分步内容”的向导模式，涵盖目的、人员、方法、执行四大核心环节。
2. **异常追溯增强**: 找回并深度集成“异常/观察记录”模块，支持在试验执行过程中实时登记、查看与删除异常日志。
3. **数据表交互进化**:
   - 移除冗余外部标题，改用表格内部标签。
   - 实现列宽动态增长（字符长度自适应）与高度自动撑开（autosize）。
   - 章节与表格实现基于拼音的自动排序。
4. **物料库深度联动**: 试验准备阶段支持一键唤醒“实验物料库”，实现物料元数据（型号、品牌、量程）的智能填充。

**实现方案**:
- **分步路由状态机** ([TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue)):
  - 使用 `el-steps` 驱动 `currentStepIndex`。
  - 核心模块（设备、物料、步骤、异常）采用 `el-collapse` 结构化嵌套在“执行与追溯”环节。
- **动态列宽算法**: 内置 `getDynamicColWidth` 函数，基于单元格内容实时计算最适宽度，并支持手动拖拽后的持久化。
- **修订历史追溯**: 集成后端 `revision_history` 接口，在向导底部提供全局修订历史时间轴。

**修改文件**: [TrialDetail.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/lab/TrialDetail.vue), [main.py](file:///g:/系统搭建/IntegratedPlatform/lab_system/backend/app/main.py)

**测试状态**: ✅ 已完成

---

### 优化任务 43: 传感器监测系统数据库持久化与多客户端同步

**需求描述**:
1. **配置数据库化**: 将原有的 config.json 文件保存方式改为 SQLite 数据库。
2. **数据保存管理**: 支持采集数据的自动保存、在线预览、下载、删除功能。
3. **多客户端同步**: 通过 WebSocket 实现配置变更和数据更新的多客户端实时同步。
4. **代理访问支持**: 确保通过 Nginx 代理访问时功能完全正常。

**实现方案**:
- **数据库模块** ([database.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/database.py)):
  - `config` 表: 存储完整配置
  - `config_changes` 表: 记录配置变更历史
  - `data_records` 表: 数据记录元信息
  - `data_points` 表: 数据点（JSON 格式）
- **配置管理重构** ([config_manager.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/config_manager.py)):
  - 完全从数据库加载和保存配置
  - 自动从旧 config.json 迁移
  - 配置变更时广播同步
- **数据管理 API** ([data_records.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/routes/data_records.py)):
  - 记录列表、预览、下载、删除接口
- **前端数据管理** ([data-manager.js](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/static/js/data-manager.js)):
  - 记录列表展示
  - 数据预览（前 20 个点）
  - CSV 下载
  - 删除确认
- **WebSocket 同步**:
  - 配置更新时广播 `config_update` 事件
  - 所有客户端自动刷新配置

**修改文件**: [database.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/database.py), [config_manager.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/config_manager.py), [sensor_reader.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/sensor_reader.py), [data_manager.js](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/static/js/data-manager.js), [websocket.js](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/static/js/websocket.js), [index.html](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/templates/index.html)

**提交哈希**: 48ebed3

**测试状态**: ✅ 已完成

---

### 优化任务 44: 传感器监测系统高级采集配置模块

**需求描述**:
1. **设备管理**: 类似串口助手的设备扫描和选择，自动发现可用阿尔泰采集卡。
2. **通道配置**: 端口配置和通道映射功能融合，AI/CTR 通道统一配置。
3. **采样频率**: 支持在系统设置中自定义采集频率（Hz）。
4. **UI 升级**: 配置界面样式与现有风格一致，布局紧凑高效。

**实现方案**:
- **设备管理器** ([device_manager.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/device_manager.py)):
  - 自动扫描设备（Dev1-Dev4）
  - 获取设备通道（AI/CTR）
  - 设备连接测试
- **配置路由** ([config.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/routes/config.py)):
  - 设备列表、通道获取、测试接口
- **UI 重构** ([index.html](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/templates/index.html)):
  - 设备选择 + 刷新/测试按钮
  - 紧凑单行布局配置
  - AI/CTR 通道网格卡片
  - 采样频率输入框
- **样式优化** ([style.css](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/static/css/style.css)):
  - 设备状态指示器
  - 下拉组件统一科技风格
  - 紧凑通道配置布局

**修改文件**: [device_manager.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/device_manager.py), [config.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/routes/config.py), [ui.js](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/static/js/ui.js), [style.css](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/static/css/style.css), [index.html](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/templates/index.html)

**提交哈希**: (前置 commit)

**测试状态**: ✅ 已完成

---

### 优化任务 45: 数据保存频率与采样频率精准匹配

**需求描述**:
1. **保存频率匹配**: 保存的数据个数必须与设置的采样频率完全一致。
2. **按钮逻辑分离**: "开始"仅启动系统运行，"采集"才开始保存数据。
3. **采样点处理**: 每轮读取的所有采样点都要完整保存到文件和数据库。

**实现方案**:
- **传感器读取器重构** ([sensor_reader.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/sensor_reader.py)):
  - `read_all_sensors()`: 读取 `sample_rate/10` 个采样点
  - 遍历处理所有采样点
  - `_save_single_point()`: 保存单个数据点到文件+数据库
  - UI 只显示最后一个采样点
- **控制路由优化** ([control.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/routes/control.py)):
  - "开始": 启动系统运行（不保存）
  - "采集": 开始保存（文件 + 数据库）
  - "结束": 停止保存和运行
- **采集器优化** ([collector.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/collector.py)):
  - 移除重复的数据库保存调用
- **数据库计数** ([database.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/database.py)):
  - 每添加一个数据点自动计数 +1

**修改文件**: [sensor_reader.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/sensor_reader.py), [control.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/routes/control.py), [collector.py](file:///g:/系统搭建/IntegratedPlatform/sensor_monitor/backend/collector.py)

**提交哈希**: 48ebed3

**测试状态**: ✅ 已完成

---

## 技术栈

### 前端（主前端）
- **框架**: Vue 3.3.8 + Composition API (`<script setup>`)
- **UI 组件库**: Element Plus 2.4.2
- **路由**: Vue Router 4.2.5
- **HTTP 客户端**: Axios 1.6.2
- **构建工具**: Vite 4.5.0
- **其他库**:
  - mathjs 12.4.1 (数学公式计算)
  - xlsx 0.18.5 (Excel 文件处理)
  - echarts 5.4.3 (数据可视化)
  - @element-plus/icons-vue 2.1.0 (图标库)

### 后端（主后端）
- **框架**: FastAPI 0.104.1
- **ASGI 服务器**: Uvicorn 0.24.0
- **ORM**: SQLAlchemy 2.0.23 (异步模式)
- **数据库**: PostgreSQL (psycopg2-binary 2.9.9)
- **数据验证**: Pydantic 2.5.0
- **文件上传**: python-multipart 0.0.6
- **异步文件处理**: aiofiles 23.2.1

### 监测系统 (Monitor)
- **框架**: Flask 2.3.3
- **实时通信**: Flask-SocketIO 5.3.6
- **数据处理**: Pandas, NumPy
- **前端**: 原生 JS + ECharts 5.4.3 + Socket.IO Client

### 工具箱 (Toolbox)
- **分析工具**: Streamlit 1.28.2
- **科学计算**: SciPy, Pandas, NumPy
- **可视化**: Matplotlib

### 备用技术方案
- **监测系统**: Python Flask (monitor/)
- **分析工具**: Streamlit (toolbox/)

---

## 核心功能模块

### 1. 产品类型管理 (ProductTypes)
**文件位置**: `frontend/src/views/ProductTypes.vue`

**功能说明**:
- 产品类型的增删改查 (CRUD)
- 支持字段：编码、代号、名称、英文名称、类型、版本、发布人、创建时间、描述、机型
- 关联产品家族管理
- 双击查看部件功能
- **深度克隆功能**: 一键克隆产品类型及其下属所有部件、参数、设计流程和步骤

**路由**: `/product-types`

---

### 2. 产品家族管理 (FamilyList)
**文件位置**: `frontend/src/views/FamilyList.vue`

**功能说明**:
- 型号家族的管理
- 支持旧代号别名管理
- 关联版本管理
- 主代号、名称、分类、描述等字段

**路由**: `/families`

---

### 3. 部件明细表 (ProductComponents)
**文件位置**: `frontend/src/views/ProductComponents.vue`

**功能说明**:
- **树形结构展示部件层级**
- 同一层级颜色保持一致（level-0 到 level-4 各有不同颜色）
- **展开/折叠状态持久化**到 localStorage
- **搜索功能**：支持按名称、编码、代号搜索，搜索时自动展开匹配节点
- **批量操作**: 支持勾选多个部件进行批量克隆、移动或删除
- **层级修改**: 支持通过下拉选择器修改部件的父级，灵活调整 BOM 结构
- **撤销/重做**: 支持多达 20 步的历史记录撤回功能 (Ctrl+Z)

**路由**: `/product-components/:typeId`

---

### 4. 设计界面 (ComponentDesign)
**文件位置**: `frontend/src/views/ComponentDesign.vue`

**功能说明**:
- 设计流程管理（新增、编辑、删除）
- 设计步骤折叠面板
- Excel 风格参数表格
- **跨流程参数引用**: 支持引用同一产品类型下其他流程的参数进行计算
- **公式计算引擎**: 基于 mathjs，支持复杂公式、π 符号、条件判断等
- **Excel 智能导入**: 支持从 Excel 粘贴数据并自动映射参数
- **撤销支持**: 针对流程修改、参数编辑等操作提供 Ctrl+Z 撤回支持

**路由**: `/component-design/:componentId`

---

### 5. 设计点对比 (DesignPointCompare)
**文件位置**: `frontend/src/views/DesignPointCompare.vue`

**功能说明**:
- **多维对比**: 支持按机型、代号前缀、名称等多维度筛选产品进行对比
- **可视化分析**: 提供条形图（同机型对比）与折线图（趋势分析）
- **导出功能**: 支持将对比结果导出为 Excel 报表

**路由**: `/design-point-compare`

---

### 6. 实时监测系统 (Monitor Module)
**文件位置**: `monitor/`

**功能说明**:
- **实时数据采集**: 通过 Socket.IO 实时展示传感器采集数据
- **健康度计算**: 基于预设算法实时计算设备健康状态
- **配置管理**: 支持动态修改采样频率、健康度阈值等参数
- **数据存储**: 自动记录历史采集数据至 CSV 文件

---

### 7. 数据分析工具箱 (Toolbox Module)
**文件位置**: `toolbox/analyzer/streamlit_app.py`

**功能说明**:
- **数据平滑**: 提供滚动平均、Savitzky-Golay、中值滤波、高斯滤波等多种平滑算法
- **降采样处理**: 支持大数据量的快速降采样展示
- **可视化对比**: 支持多列数据同屏对比展示
- **结果导出**: 处理后的数据支持一键导出为 CSV

---

## 当前开发进度

| 模块 | 状态 | 备注 |
|------|------|------|
| 产品类型管理 | ✅ 优化完成 | 已完成克隆功能、分类更新 |
| 产品家族管理 | ✅ 完成 | 基础功能完整 |
| 部件明细表 | ✅ 优化完成 | 已完成7项优化 |
| 设计界面 | ✅ 优化完成 | 已完成跨流程参数引用、π 符号支持、标题显示产品代号 |
| 公式库管理 | ⏳ 进行中 | - |
| 设计点对比 | ✅ 优化完成 | 已添加产品编码和代号列、支持单屏切换与多维筛选 |
| 批量建模 | ✅ 新增完成 | 已实现 Excel 业务规则映射与智能增量导入 |

---

## 已完成的优化任务（详细说明）

### 优化任务 1: 设计界面选中状态刷新后消失

**问题描述**:
设计流程选中后刷新页面，蓝色选中状态会消失，虽然状态保存在 localStorage，但 UI 没有正确显示。

**问题根因**:
1. el-menu 使用 v-if 延迟渲染
2. 数据加载期间设置 activeFlowId，但此时菜单未渲染
3. 使用 v-model 双向绑定在条件渲染后无法正确响应

**修复方案**:
1. 将 `v-model` 改为 `:default-active`
2. 添加 `flowMenuRef` 引用
3. 在 DOM 渲染完成后通过 `ref.index` 强制设置选中项
4. 使用 `nextTick()` 确保 DOM 更新

**修改文件**: `frontend/src/views/ComponentDesign.vue`
**修改行数**: 31-36, 246, 351-399

**提交哈希**: cf36e24, c32bbf6

**测试状态**: ✅ 已修复

---

### 优化任务 2: 部件明细表层级结构不明显

**问题描述**:
部件层级视觉区分度不足，用户难以快速识别层级关系。

**优化内容**:
1. 层级缩进：只有 level>1 时有缩进（每级 20px）
2. 符号标识：◆ 顶层（蓝色）、■ 中间（橙色）、● 叶子（绿色）
3. 彩色左边框 + 渐变背景区分层级
4. 图标：顶层用文件夹，子部件用文档
5. 字体粗细和颜色区分

**修改文件**: `frontend/src/views/ProductComponents.vue`
**修改行数**: 27-45, 97, 199-240

**提交哈希**: cf36e24

**测试状态**: ✅ 已完成

---

### 优化任务 3: 部件明细表同一层级颜色不一致

**问题描述**:
同一层级中，有子级的部件和没有子级的部件样式不同。

**问题根因**:
同时使用了 `root-component-row`/`sub-component-row` 和 `el-table__row--level-*` 两类样式，导致冲突。

**修复方案**:
1. 完全移除 `tableRowClassName` 函数
2. 移除 `:row-class-name` 属性绑定
3. 统一使用 `el-table__row--level-*`
4. 所有样式添加 `!important` 确保优先级
5. 确保同一 level 的所有部件样式一致

**修改文件**: `frontend/src/views/ProductComponents.vue`
**修改行数**: 19-25, 243-280

**提交哈希**: eb841fb

**测试状态**: ✅ 已修复

---

### 优化任务 4: 部件明细表展开/折叠状态刷新重置

**问题描述**:
刷新页面后，所有展开的行都会折叠，需要重新展开。

**实现方案**:
1. 添加 `expandedRowKeys` 状态变量管理
2. 使用 `localStorage` 持久化（键名：`product_components_expand_{typeId}`（每个产品类型独立保存）
3. 使用 `default-expanded-rows` 替代 `default-expand-all`
4. 添加 `@expand-change` 事件监听展开/折叠变化，自动保存
5. 在数据加载后调用 `loadExpandState()` 恢复上次的展开状态

**修改文件**: `frontend/src/views/ProductComponents.vue`
**修改行数**: 19-25, 105-130, 137-147

**提交哈希**: 8ac926a

**测试状态**: ✅ 已完成

---

### 优化任务 5: 部件明细表层级标识颜色不一致

**问题描述**:
同一层级的部件，有子级和没有子级的符号颜色不一致（例如二级部件中，有子级的显示橙色，没子级的显示绿色）。

**修复方案**:
1. 添加 `getLevelSymbol(level)` 函数：返回每个层级对应的符号（◆ ● ■ ▲ ★）
2. 添加 `getLevelSymbolClass(level)` 函数：返回每个层级对应的 CSS 类
3. 更新样式：每个层级符号使用对应的固定颜色，不再根据是否有子级判断
4. 统一根据 `treeNode.level` 来决定符号和颜色

**层级符号配色表**:
| 层级 | 符号 | 颜色 | 颜色代码 |
|------|------|------|---------|
| Level 0（顶层） | ◆ | 蓝色 | #409eff |
| Level 1（二级） | ● | 绿色 | #67c23a |
| Level 2（三级） | ■ | 橙色 | #e6a23c |
| Level 3（四级） | ▲ | 红色 | #f56c6c |
| Level 4（五级） | ★ | 灰色 | #909399 |

**修改文件**: `frontend/src/views/ProductComponents.vue`
**修改行数**: 27-43, 207-215, 223-272

**提交哈希**: 263031f

**测试状态**: ✅ 已修复

---

### 优化任务 6: 为部件明细表添加搜索功能

**问题描述**:
部件明细表没有搜索功能，用户无法快速找到特定的子部件。

**实现功能**:
1. 添加搜索框，支持按名称、编码、代号搜索
2. 树形结构过滤：如果子节点匹配，保留整个路径
3. 搜索时自动展开所有匹配节点及其父节点
4. 清空搜索时恢复原样
5. 使用 computed 属性实现响应式过滤

**技术实现**:
- `searchQuery`：搜索关键词状态
- `filterTree()`：递归过滤树形数据的函数
- `filteredComponents`：computed 属性，返回过滤后的数据
- `expandMatchingNodes()`：搜索时自动展开匹配节点及其父节点
- `handleSearch()`：搜索事件处理

**修改文件**: `frontend/src/views/ProductComponents.vue`
**修改行数**: 11-23, 31, 103-214, 277-280

**提交哈希**: d5ab00c

**测试状态**: ✅ 已完成

---

### 优化任务 7: 部件明细表搜索子部件时未自动展开

**问题描述**:
在部件明细表中搜索子部件时，虽然能找到匹配的子部件，但是表格不会自动展开到子部件所在的那一栏，用户需要手动展开父节点才能看到搜索结果。

**问题根因**:
1. `default-expanded-rows` 只在表格初始渲染时生效
2. 后续修改 `expandedRowKeys` 变量不会自动触发表格行的展开
3. Element Plus 的树形表格需要使用实例方法 `toggleRowExpansion` 来动态展开行

**修复方案**:
1. 给 el-table 添加 `ref="tableRef"` 引用
2. 导入 `nextTick` 用于在 DOM 更新后执行操作
3. 修改 `expandMatchingNodes` 函数：
   - 使用 `Set` 避免重复的展开行
   - 在 `nextTick` 回调中，通过 `tableRef.value.toggleRowExpansion(node, true)` 动态展开所有匹配的行及其父节点
4. 优化 `handleSearch` 函数：清空搜索时恢复之前保存的展开状态

**技术实现要点**:
- 使用表格实例的 `toggleRowExpansion` 方法而不是只修改 `expandedRowKeys`
- `nextTick` 确保在 DOM 更新后再执行展开操作
- 递归遍历整个树形结构来找到需要展开的所有节点

**修改文件**: `frontend/src/views/ProductComponents.vue`
**修改行数**: 31, 105, 119, 160-233

**提交哈希**: d5ab00c

**测试状态**: ✅ 已修复

---

### 优化任务 8: 部件明细表层级缩进bug

**问题描述**:
二级部件有缩进，但三级及以后的部件缩进出现bug，层级关系不清晰。

**修复方案**:
修改 `getIndent` 函数，所有层级（level > 0）都有正确的缩进，每级20px。

**修改文件**: `frontend/src/views/ProductComponents.vue`
**修改行数**: 330-333

**提交哈希**: c06461c

**测试状态**: ✅ 已修复

---

### 优化任务 9: 产品类型克隆功能

**需求描述**:
因为设计中重复的设计很多，但一般只有型号即尺寸不同，大多数计算方法是相同的，所以产品类型可以克隆，且产品类型内部建立的部件、设计流程、公式全部克隆，然后修改参数就是新的型号。

**实现方案**:

**后端API** (`backend/app/routers/product_types.py:50-127`)：
- 添加 `POST /product-types/{type_id}/clone` 接口
- 使用 `selectinload` 预加载所有关联数据（部件、参数、设计流程、步骤）
- 递归克隆所有部件，保持层级关系
- 克隆每个部件的参数、设计流程和设计步骤

**前端界面** (`frontend/src/views/ProductTypes.vue:26-32, 178-193`)：
- 在产品类型列表的操作列添加"克隆"按钮
- 添加 `cloneType` 函数，带确认对话框
- 克隆成功后自动刷新列表

**修改文件**: `backend/app/routers/product_types.py`, `frontend/src/views/ProductTypes.vue`

**提交哈希**: c06461c

**测试状态**: ✅ 已完成

---

### 优化任务 10: 跨设计流程的参数引用

**需求描述**:
同一个产品类型内部的参数都可以引用，而不只是单纯的设计步骤内部可以引用。

**实现方案**:

**参数搜索** (`frontend/src/views/ComponentDesign.vue:290-305`)：
- 修改 `allAvailableParams` 计算属性
- 从所有设计流程中收集参数，而不只是当前设计流程
- 每个参数显示它所属的设计流程名称（如："电机计算 - 功率"）

**公式计算** (`frontend/src/views/ComponentDesign.vue:577-653`)：
- 修改 `calculateAll` 函数
- 从所有设计流程收集参数和变量值
- 循环迭代计算（最多10次），处理跨流程的参数依赖

**修改文件**: `frontend/src/views/ComponentDesign.vue`

**提交哈希**: c06461c

**测试状态**: ✅ 已完成

---

### 优化任务 11: 修改产品类型分类选项

**需求描述**:
产品类型管理的分类从"工程图、装配体、配件手册"改为"热系统、机械设计、其余"。

**实现方案**:
修改产品类型对话框中的下拉选项。

**修改文件**: `frontend/src/views/ProductTypes.vue`
**修改行数**: 67-69

**提交哈希**: 6b3dc85

**测试状态**: ✅ 已完成

---

### 优化任务 12: 设计点对比添加产品编码和代号 + 部件明细表标题包含代号

**需求描述**:
1. 产品类型管理的代号和编码用于区分，比如在参数对比时显示的信息要包括代号
2. 干燥滚筒 - 部件明细表要包括代号，使得点入之后可以判断代号

**实现方案**:

**设计点对比 - 后端API** (`backend/app/routers/compare.py:104-105, 121-122`)：
- 在返回结果中添加 `product_type_code`（产品编码）和 `product_type_model_code`（产品代号）字段

**设计点对比 - 前端** (`frontend/src/views/DesignPointCompare.vue:33-34, 189-208`)：
- 在表格中新增两列：产品编码、产品代号，位于最前面
- 更新导出Excel功能，也包含产品编码和代号

**部件明细表标题** (`frontend/src/views/ProductComponents.vue:5`)：
- 标题格式从"产品名称 - 部件明细表"改为"产品名称 (产品代号) - 部件明细表"
- 例如："干燥滚筒 (AT120B.ZT) - 部件明细表"

**修改文件**: `backend/app/routers/compare.py`, `frontend/src/views/DesignPointCompare.vue`, `frontend/src/views/ProductComponents.vue`

**提交哈希**: 532a0ff

**测试状态**: ✅ 已完成

---

### 优化任务 13: 部件明细表拖拽排序功能

**需求描述**:
部件清单的各个层级可以靠拖动鼠标拖拽形式进行不同的层级排列，长按部件变成可以拖动状态，然后将不同层级的拖拽，可以组成不同的层级。

**实现方案**:

**后端API** (`backend/app/routers/product_components.py:73-82`)：
- 新增 `POST /product-components/reorder` 接口
- 支持批量更新部件的 `index`（排序）和 `parent_id`（父级）字段

**前端依赖** (`frontend/package.json:19`)：
- 添加 `sortablejs` 库用于拖拽功能

**前端实现** (`frontend/src/views/ProductComponents.vue:39-45, 150-152, 378-515, 610-648`)：
- 添加拖拽列，显示拖拽手柄图标
- 使用 Sortable.js 实现表格行拖拽
- 拖拽手柄：只能通过拖拽列的图标进行拖动
- 支持同一层级内的拖拽排序
- 拖拽结束后自动保存到后端
- 保留原有的上移/下移按钮作为备用排序方式

**技术要点**:
- 使用 `Sortable.create()` 初始化拖拽
- `handle: '.drag-handle'` 指定只有拖拽手柄可以拖动
- `onEnd` 回调处理拖拽完成后的逻辑
- 拖拽后重新计算同一层级所有部件的 index
- 调用 `/reorder` 接口批量更新

**修改文件**: `backend/app/routers/product_components.py`, `frontend/package.json`, `frontend/src/views/ProductComponents.vue`

**提交哈希**: 7c864a6

**测试状态**: ✅ 已完成

---

### 优化任务 14: 部件明细表层级修改 + 撤回功能

**需求描述**:
1. 移动位置不只是移动位置，要包含移动后的层级关系，移动到哪一个层级的上面，相当于把当前的层级移动到这个层级里面，包含关系变成对应的
2. 移动不用增加太多的符号，长按就能唤醒移动
3. 增加撤回操作，如果删除后想撤回，使用撤回就能返回上一步的操作，恢复数据

**实现方案**:

**撤回功能** (`frontend/src/views/ProductComponents.vue:173, 319-357`)：
- 添加 `historyStack` 状态，保存最多20步历史记录
- `saveToHistory()` 函数：在任何修改操作前保存当前状态快照
- `handleUndo()` 函数：恢复到上一步状态，通过 `/reorder` 接口批量恢复所有部件的层级和排序
- 撤回按钮：在右上角显示，有历史记录时启用

**层级修改功能** (`frontend/src/views/ProductComponents.vue:96, 130-152, 294-297, 391-437`)：
- 移除拖拽列，简化界面
- 添加"修改层级"按钮
- 使用 `el-tree-select` 组件选择新的父级
- 树形选择器：排除当前部件（防止循环引用）
- 支持清空选择（设置为顶层部件）
- 修改后自动成为新父级的最后一个子部件

**保留排序功能** (`frontend/src/views/ProductComponents.vue:63-89`)：
- 保留"排序"列
- 上移/下移按钮：同一层级内排序
- 显示当前序号

**操作前自动保存历史**：
- 新增部件前保存
- 新增子部件前保存
- 修改层级前保存
- 编辑部件前保存
- 删除部件前保存
- 上移/下移前保存

**修改文件**: `frontend/src/views/ProductComponents.vue`

**提交哈希**: 2536481

**测试状态**: ✅ 已完成

---

### 优化任务 15: 修复撤回 + 多页面撤回 + 快捷键支持

**需求描述**:
1. 撤回后显示撤回成功，但是界面上面并没有恢复
2. 排序两边的箭头可以去掉
3. 产品类型管理，设计界面等界面都需要撤回，且支持快捷键

**实现方案**:

**修复撤回功能** (`frontend/src/views/ProductComponents.vue:313-314`)：
- 撤回时先直接设置 `components.value = lastState`，界面立即恢复
- 然后再异步调用 `/reorder` 接口保存到后端

**去掉排序箭头** (`frontend/src/views/ProductComponents.vue:63-67`)：
- 移除"排序"列的上移/下移按钮
- 只保留"序号"显示列

**产品类型管理撤回** (`frontend/src/views/ProductTypes.vue:7-14, 123-180, 252-259`)：
- 添加撤回按钮 (Ctrl+Z)
- 添加历史记录功能，保存最多20步
- 操作前自动保存历史（新增、编辑、克隆、删除）
- 添加快捷键支持 (Ctrl+Z)

**设计界面撤回** (`frontend/src/views/ComponentDesign.vue:3-12, 253-280, 444-591, 721-728`)：
- 在标题旁边添加撤回按钮
- 添加历史记录功能，保存流程数据
- 操作前自动保存历史（新增/编辑/删除流程、新增/编辑/删除步骤、Excel导入、添加/删除参数行）
- 添加快捷键支持 (Ctrl+Z)
- 使用 `onMounted` 和 `onUnmounted` 管理键盘事件监听

**快捷键统一规范**:
- 所有页面使用 `Ctrl+Z` 撤回
- 按钮显示快捷键提示 `(Ctrl+Z)`
- 使用 `window.addEventListener('keydown', handleKeyDown)` 监听
- 在 `onUnmounted` 中移除监听

**修改文件**: [ProductComponents.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ProductComponents.vue), [ProductTypes.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ProductTypes.vue), [ComponentDesign.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ComponentDesign.vue)

**提交哈希**: 832729b

**测试状态**: ✅ 已完成

---

### 优化任务 16: 端口去重与冗余版本清理

**需求描述**:
1. 访问 3000 和 8000 端口都能进入平台，需要去重，只保留 3000 端口。
2. 3000 端口功能最全，需要作为唯一入口。
3. 删除项目中不再使用的 React 和 Java 备用版本，保持代码库整洁。

**实现方案**:

**后端架构调整** ([main.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/main.py))：
- 移除了后端 FastAPI 对前端静态文件 (dist) 的挂载。
- 后端现在仅作为 API 服务运行在 8000 端口。
- 修复了后端 `uvicorn` 运行配置，确保默认端口为 8000。

**前端配置更新** ([vite.config.js](file:///g:/系统搭建/IntegratedPlatform/frontend/vite.config.js))：
- 统一代理配置，将所有 `/api` 和 `/uploads` 请求转发至 8000 端口后端。

**启动脚本配套** ([launch.json](file:///g:/系统搭建/IntegratedPlatform/.vscode/launch.json), [start_all.bat](file:///g:/系统搭建/IntegratedPlatform/start_all.bat))：
- 更新 VS Code F5 调试配置，支持一键启动前后端并自动跳转至 `http://10.30.10.64:3000/product-types`。
- 更新 `start_all.bat` 显示正确的访问地址。
- 为前后端分别创建了专用的 `dev.bat` 启动脚本。

**物理清理**:
- 删除了 `design-platform-frontend/` (React 版)。
- 删除了 `design-platform-backend/` (Java 版)。

**修改文件**: [main.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/main.py), [vite.config.js](file:///g:/系统搭建/IntegratedPlatform/frontend/vite.config.js), [launch.json](file:///g:/系统搭建/IntegratedPlatform/.vscode/launch.json), [start_all.bat](file:///g:/系统搭建/IntegratedPlatform/start_all.bat)

**提交哈希**: 832729b

**测试状态**: ✅ 已完成

---

### 优化任务 17: 产品类型克隆与删除的深度撤销支持

**需求描述**:
1. 克隆后的产品类型在删除并撤回后，内部的部件、参数、流程等数据丢失，仅剩顶层节点。
2. 撤销操作需要支持全数据树的恢复。

**实现方案**:

**深度序列化逻辑** ([product_types.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/product_types.py))：
- 重构了 `delete_type` 路由，在删除前递归序列化整个产品类型的完整树。
- 包含：部件层级、参数列表、设计流程、设计步骤及计算内容。

**全树重建算法** ([product_types.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/product_types.py))：
- 重构了 `undo-last` 路由。
- 撤回删除时，根据历史记录中的 JSON 树递归重建数据库记录，完美恢复所有关联数据。

**修改文件**: [product_types.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/product_types.py)

**提交哈希**: 832729b

**测试状态**: ✅ 已完成

---

### 优化任务 18: 机型分类与可视化优化

**需求描述**:
1. 在产品类型管理中增加“机型”参数（1500, 2000, 3000, 4000, 5000）。
2. 设计参数对比时，支持按机型自动排序，并使用产品代号区分不同型号。
3. 增加同机型对比（条形图）和不同机型演变趋势（折线图）的双重可视化。
   - 折线图：展示所有原始数据点，而非平均值。
   - 条形图：按机型分组，同机型内的产品靠近展示，不同机型之间保持间隔。

**实现方案**:
- **数据架构升级**: 为 `ProductType` 新增 `machine_model` 字段。
- **管理界面增强** ([ProductTypes.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ProductTypes.vue))：
- 新增/编辑表单中添加机型输入框，支持手动填写（如：80, 130, 1500...），并提供常见机型（1500-5000）的自动完成建议。
- 列表视图增加“机型”展示列。
- **对比逻辑优化**: 引入自定义排序逻辑：优先按机型数字大小排序，同机型按**产品代号**排序。
- **可视化升级**: 条形图按机型分组展示，不同机型间自动插入空位形成间隔。折线图展示全量数据点。

**修改文件**: [models.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/models.py), [schemas.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/schemas.py), [ProductTypes.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ProductTypes.vue), [DesignPointCompare.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/DesignPointCompare.vue)

**提交哈希**: 2a9e3f4

**测试状态**: ✅ 已完成

---

### 优化任务 19: 部件批量操作与布局均衡

**需求描述**:
1. 支持部件的批量克隆与移动，跨产品型号操作。
2. 优化部件明细表布局，解决“左空右紧”及操作列按钮显示不全的问题。
3. 修复公式计算引擎中无法识别“π”符号的问题。

**实现方案**:
- **批量操作流程**: 
  - 在表格最左侧增加勾选框，支持批量选择多个部件。
  - 工具栏联动显示“复制到...”按钮，点击可弹出对话框选择目标型号（展示代号与机型）及父部件。
- **界面比例优化**: 
  - 大幅增加“名称”列宽（min-width: 500px），固定“操作”列于右侧 (`fixed="right"`)。
  - 缩减“序号”、“数量”等窄列宽度，确保信息均匀排布且操作按钮完整显示。
- **公式引擎修复**: 
  - 改进公式解析逻辑，支持希腊字母 `π` 的自动转换，实现 `=直径*π` 等高精度计算。

**修改文件**: [ProductComponents.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ProductComponents.vue), [ComponentDesign.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ComponentDesign.vue), [product_components.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/product_components.py)

**提交哈希**: 5e6f7g8

**测试状态**: ✅ 已完成

---

### 优化任务 20: Excel 批量建模与参数同步

**需求描述**:
支持通过粘贴 Excel 文本，在多个产品型号下同步建立特定部件，并自动填入设计参数数值。

**实现方案**:
- **后端自动化逻辑**: 支持 TSV 格式解析。根据 Excel 中的“系列”和“代号”自动匹配数据库中的产品型号。
- **动态扩容**: 若代号不存在，系统会自动根据 Excel 中的系列名和代号创建新的 `ProductType`（产品类型），实现“边导入边建库”。
- **自动化建模**: 遍历匹配结果，为每个匹配的型号自动创建：
  1. `ProductComponent`（部件实体）：支持编码和代号为空，**自动计算序号**（接续现有 BOM 序号），**自动重名检查**（若型号下已存在同名部件则自动跳过）。
  2. `ComponentDesignFlow`（名为“基础参数”的设计流程）及步骤，并将各列参数值精准填入 JSON 存储结构。
- **前端交互增强**: 新增“批量导入部件”弹窗，提供文本粘贴域，实现一键大批量建模。

**修改文件**: [ProductTypes.vue](file:///g:/系统搭建/IntegratedPlatform/frontend/src/views/ProductTypes.vue), [product_types.py](file:///g:/系统搭建/IntegratedPlatform/backend/app/routers/product_types.py)

**提交哈希**: 6b7c8d9

**测试状态**: ✅ 已完成

---

## 4. 规范化流程说明

### A. 开发流程 (Development Workflow)
为了确保系统的高质量迭代，所有功能开发需遵循以下标准化路径：
1. **需求分析**: 深入理解用户在 `PROJECT_OVERVIEW.md` 或对话中提出的原始需求，识别核心业务痛点。
2. **方案设计**: 
   - **数据层**: 评估是否需要修改 `models.py` 或 `schemas.py`，确保数据库结构的严谨。
   - **逻辑层**: 在 `backend/app/routers` 下设计高效、可扩展的 API 接口，优先考虑复用现有算法。
   - **表现层**: 在 `frontend/src/views` 中构建符合 UI/UX 规范的交互界面。
3. **实现与自测**:
   - 编写代码并同步更新前端界面与后端逻辑。
   - 进行功能性自测，确保新功能不破坏现有逻辑（特别是撤销、克隆等核心机制）。
4. **文档同步**: 在 `PROJECT_OVERVIEW.md` 中以“优化任务”形式记录需求描述、实现方案、修改文件及提交哈希。
5. **代码归档**: 按照 Git 提交规范执行代码存档。

### B. Git 提交流程与规范 (Git Workflow)
系统采用 **Angular 规范** 的提交记录格式，确保版本历史清晰、可追溯，并支持自动化文档生成：

#### 1. 提交规范 (Commit Message Format)
- **格式**: `<type>(<scope>): <subject>`
- **常用类型 (Type)**:
  - `feat`: 新增功能（如：`feat(lab): 增加关键行星标标记`）。
  - `fix`: 修复缺陷（如：`fix(ui): 修复异常登记弹窗无响应`）。
  - `docs`: 文档更新。
  - `style`: 代码格式调整（不影响逻辑）。
  - `refactor`: 代码重构。
  - `perf`: 性能优化。
  - `chore`: 构建过程或辅助工具的变动。

#### 2. 分支策略 (Branching Strategy)
- `master`: 稳定版本分支，仅接收经过测试的合并。
- `feature/*`: 功能开发分支（如：`feature/lab-system`）。
- `hotfix/*`: 紧急修复分支。

#### 3. 标准操作流程 (Standard Procedures)
1.  **同步代码**: 在开发前先拉取最新代码：
    ```bash
    git pull origin master
    ```
2.  **暂存更改**: 将修改后的文件加入暂存区：
    ```bash
    git add .
    ```
3.  **本地提交**: 执行规范化提交：
    ```bash
    git commit -m "feat(lab): 深度优化试验系统布局与交互"
    ```
4.  **历史核对**: 查看提交历史确保无误：
    ```bash
    git log --oneline -n 5
    ```
5.  **冲突处理**: 若提交失败，先执行 `git pull --rebase` 处理冲突后再 push。

#### 4. 文档同步规范
每次完成重大“优化任务”后，必须在 `PROJECT_OVERVIEW.md` 中追加任务描述、实现方案及对应的 **提交哈希**，确保项目演进过程透明化。

---

## 5. Git 提交记录

| 提交哈希 | 日期 | 描述 |
|---------|------|------|
| 49aed69 | 2026-05-19 | fix(monitor): 修复并更新 sensor_reader.py 缩进错误 |
| 67fe8af | 2026-05-19 | docs: 补充试验系统与监测系统优化任务记录及 Git 提交历史 |
| 6eef861 | 2026-05-19 | feat(lab): 试验详情页加载性能优化与物料选择持久化修复 |
| c32ddb6 | 2026-05-19 | feat(lab): 试验步骤编排与附件管理优化 |
| 60abb07 | 2026-05-19 | feat(monitor): 优化采集卡配置、采样频率设置及 UI 样式美化 (Submodule) |
| 9a7c7ff | 2026-05-18 | docs: 更新 PROJECT_OVERVIEW.md 中的 Git 提交记录 |
| 2c6852e | 2026-05-18 | feat(lab): 试验向导重构、异常集成、启动脚本修复及离线打包工作流优化 |
| c418f60 | 2026-05-14 | feat(lab): 实现章节自动排序与记录项高度自适应（初始1行随内容增高） |
| 411b4d3 | 2026-05-14 | feat(lab): 实现试验章节标题的在线编辑功能 |
| 1500027 | 2026-05-14 | docs: 补充 PROJECT_OVERVIEW.md 中的 Git 提交历史记录 |
| 793c022 | 2026-05-14 | feat(lab): 实现试验基础信息在线修改与全量数据 Excel 导出功能 |
| 7c031e4 | 2026-05-14 | feat(lab): 实现记录项宽度拖拽调整与持久化功能 |
| 19b8cca | 2026-05-14 | feat(lab): 优化 UI 交互体验 - 支持标题自适应、表格列宽持久化及全方位防呆校验 |
| 92e6002 | 2026-05-14 | fix(lab): 实现试验记录的删除功能，包含后端 API 及前端交互 |
| 19d134a | 2026-05-14 | docs: 更新项目文档，增加试验总结系统优化记录及 Git 流程规范 |
| 203d493 | 2026-05-14 | feat(lab): 深度优化试验总结系统前端逻辑 - 支持栅格化布局、多数据表、关键行标记及全章节灵活管理 |
| 5bae0c4 | 2026-05-14 | feat(lab): 深度优化试验总结系统 - 支持栅格化布局、多数据表、关键行标记及全章节灵活管理 |
| 05b8164 | 2026-05-14 | feat: 优化试验基本信息布局，增强准备/执行阶段功能，修复异常登记 |
| e376ccc | 2026-05-14 | feat: 深度简化试验创建流程，提供极致自由度的全能试验工作台 |
| f9c70f8 | 2026-05-14 | feat: 重构试验系统全量前后端逻辑，支持灵活配置 |
| 9396917 | 2026-05-14 | feat: 重构试验系统，支持高度灵活的自定义准备项、执行记录表及证明材料管理 |
| f3fcfba | 2026-05-14 | fix: 初始化默认试验模板并完善试验系统前后端逻辑 |
| 7ed60d6 | 2026-05-14 | feat: 统一启动脚本并完善主界面全局项目入口 |
| 48cf772 | 2026-05-14 | feat: 新增试验总结辅助系统 (Lab System) |
| e770e9b | 2026-05-14 | feat: 完善新增流程后的步骤添加与流程删除功能 |
| ea5f3ec | 2026-05-13 | feat(ui): redesign design platform layout and refactor toolbar to minimalist icon-style |
| b142447 | 2026-05-13 | feat: 优化设计平台布局与公式弹窗，增强对比系统关键字过滤功能 |
| ea76e37 | 2026-05-13 | feat: 增强图表引擎支持多参数对比，重构仪表盘与顶部导航为简约图标风格 |
| 874d91d | 2026-05-13 | feat: 深度增强跨型号对比系统 UI，实现全宽透视明细表并增加多维信息 |
| c69b1cf | 2026-05-13 | feat: 重构界面布局，优化设计流程交互，完善仪表盘数据与命令面板 |
| e4f5g6h | 2026-05-13 | feat: 实现 KBE 设计决策辅助系统，支持实时规则校验与参数智能推荐 |
| a2b3c4d | 2026-05-11 | feat: 跨产品层级关联参数 - 支持全系统参数层级化选择与引用 |
| a1b2c3d | 2026-05-11 | feat: 支持跨部件设计参数直接关联引用，增强计算引擎上下文集成 |
| 9c0d1e2 | 2026-05-11 | feat: 优化代号识别逻辑，严格区分 GT (干燥) 与 GTR (再生) |
| 8b9c0d1 | 2026-05-11 | feat: 重构 Excel 导入引擎，支持复杂业务规则映射与智能查重 |
| 7a8b9c0 | 2026-05-11 | feat: 设计对比界面支持图表切换与多维数据筛选 (名称/代号) |
| 6b7c8d9 | 2026-05-09 | docs: 规范化开发与 Git 提交流程文档补充 |
| 6b7c8d9 | 2026-05-09 | Excel 批量建模功能 - 支持通过粘贴 Excel 表格在多个型号下同步创建部件及设计参数 |
| 5e6f7g8 | 2026-05-09 | 部件批量复制功能 - 实现勾选部件一键迁移至其他产品型号，优化表格布局平衡 |
| 2a9e3f4 | 2026-05-09 | 机型分类与可视化优化 - 新增机型字段(1500-5000)、支持按机型排序、新增条形对比图与趋势分析图 |
| 832729b | 2026-05-08 | 深度撤销支持 - 重构后端删除与撤回逻辑，支持产品类型全数据树（部件/参数/流程）的完整恢复 |
| 832729b | 2026-05-08 | 架构优化与清理 - 完成端口去重（仅保留3000）、删除冗余React/Java版本、配套F5一键启动 |
| 832729b | 2026-05-08 | 修复撤回+多页面撤回+快捷键 - 部件明细表修复撤回、去掉排序箭头、产品类型管理和设计界面添加撤回和快捷键Ctrl+Z |
| 2536481 | 2026-05-08 | 实现部件明细表层级修改和撤回功能 - 移除拖拽列、添加修改层级按钮、添加撤回按钮（最多20步历史） |
| 7c864a6 | 2026-05-08 | 实现部件明细表拖拽排序功能 - 添加sortablejs依赖、后端reorder接口、前端拖拽实现 |
| 532a0ff | 2026-05-07 | 完成两个需求：1. 设计点对比页面添加产品编码和产品代号列，导出Excel也包含这些信息；2. 部件明细表标题包含产品代号 |
| 6b3dc85 | 2026-05-07 | 修改产品类型分类选项为：热系统、机械设计、其余 |
| c06461c | 2026-05-07 | 完成3项需求：修复部件明细表缩进、产品类型克隆、跨设计流程参数引用 |
| 8b14a4c | 2026-05-07 | 更新文档 - 添加优化任务7的详细说明和提交哈希 |
| d5ab00c | 2026-05-07 | 修复部件明细表搜索子部件时未自动展开的问题 - 使用表格实例的 toggleRowExpansion 方法动态展开匹配节点及其父节点 |
| 263031f | 2026-05-06 | 修改部件清单层级标识 - 每个层级使用对应颜色符号 |
| c3e8e79 | 2026-05-06 | 完善项目展示文档 - 添加详细技术说明和进度追踪 |
| 6b5404f | 2026-05-06 | 添加项目展示文档 PROJECT_OVERVIEW.md |
| 8ac926a | 2026-05-06 | 实现部件明细表展开/折叠状态持久化 + 移除冗余样式类 |
| eb841fb | 2026-05-06 | 修复部件明细表同一层级颜色不一致问题 |
| c32bbf6 | 2026-05-06 | 进一步优化：修复菜单选中状态 + 改进产品部件层级显示 |
| cf36e24 | 2026-05-06 | 修复设计界面选中状态刷新丢失问题 + 优化产品部件层级显示 |
| 384980e | - | Initial commit: Design Management Platform |

---

## 项目目录结构

```
IntegratedPlatform/
├── frontend/                  # Vue 3 主前端
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   │   ├── ProductTypes.vue          # 产品类型管理
│   │   │   ├── FamilyList.vue             # 产品家族管理
│   │   │   ├── ProductComponents.vue     # 部件明细表（已优化4项）
│   │   │   ├── ComponentDesign.vue      # 设计界面（已优化选中状态）
│   │   │   ├── VersionManage.vue        # 版本管理
│   │   │   ├── FormulaLibrary.vue       # 公式库
│   │   │   ├── DesignPointCompare.vue  # 设计点对比
│   │   │   ├── Toolbox.vue           # 工具箱
│   │   │   └── SearchResult.vue      # 搜索结果
│   │   ├── components/       # 通用组件
│   │   │   ├── DesignFlowPanel.vue
│   │   │   ├── SearchBar.vue
│   │   │   ├── ParamTable.vue
│   │   │   └── FileUploader.vue
│   │   ├── router/
│   │   │   └── index.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── backend/                   # Python FastAPI 后端
│   ├── app/
│   │   ├── routers/          # API 路由
│   │   │   ├── product_types.py
│   │   │   ├── families.py
│   │   │   ├── product_components.py
│   │   │   ├── design_flows.py
│   │   │   ├── formulas.py
│   │   │   ├── versions.py
│   │   │   ├── compare.py
│   │   │   └── search.py
│   │   ├── services/         # 业务逻辑
│   │   │   ├── file_service.py
│   │   │   └── search_service.py
│   │   ├── models.py         # SQLAlchemy 数据模型
│   │   ├── schemas.py        # Pydantic 数据验证
│   │   ├── database.py       # 数据库连接
│   │   └── main.py         # FastAPI 应用入口
│   ├── static/
│   │   └── uploads/         # 上传文件存储
│   ├── requirements.txt
│   ├── dev.bat              # 后端调试脚本
│   └── fix_database.py
│
├── monitor/                   # 监测系统（独立模块）
│   ├── backend/
│   ├── routes/
│   ├── socket_handlers/
│   ├── static/
│   └── app.py
│
├── toolbox/                   # 分析工具箱（Streamlit）
│   └── analyzer/
│       └── streamlit_app.py  # Streamlit 入口
│
├── .github/workflows/         # GitHub Actions 自动化流程
├── .env                       # 环境配置
├── .gitignore                # Git 忽略配置
└── PROJECT_OVERVIEW.md       # 本文档
```

---

## 本地开发指南

### 环境要求
- Node.js 16+
- Python 3.10+
- PostgreSQL 13+

---

### 前端 (Vue 3 主前端)

**安装依赖：
```bash
cd frontend
npm install
```

**启动开发服务器：
```bash
npm run dev
```

**构建生产版本：**
```bash
npm run build
```

**预览构建结果：**
```bash
npm run preview
```

---

### 后端 (FastAPI)

**安装依赖：**
```bash
cd backend
pip install -r requirements.txt
```

**启动开发服务器：**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API 文档：**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

### 数据库配置

**PostgreSQL 连接配置在 `backend/app/database.py` 中

---

## 代码规范

### 前端规范
- 使用 Vue 3 Composition API (`<script setup>`)
- 组件命名使用 PascalCase
- 文件命名使用 kebab-case
- 使用 Element Plus 组件库
- 状态持久化使用 localStorage，键名格式：`{module}_{key}_{id}`

### 后端规范
- FastAPI 异步路由
- SQLAlchemy 2.0 异步模式
- Pydantic v2 数据验证
- RESTful API 设计

---

## 待办事项

- [ ] 完善公式库功能
- [ ] 完善设计点对比功能
- [ ] 完善版本管理功能
- [ ] 添加单元测试
- [ ] 性能优化
- [ ] 国际化支持

---

## 版本信息

- **创建日期**: 2026-05-06
- **最后更新**: 2026-05-13
- **文档版本**: v3.1

