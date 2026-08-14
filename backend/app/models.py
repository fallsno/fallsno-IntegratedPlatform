from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from app.database import Base

# ---------- 参数中心主数据 ----------
class ParameterCategory(Base):
    __tablename__ = "parameter_categories"
    id = Column(Integer, primary_key=True, index=True)
    category_code = Column(String(100), nullable=False, unique=True)
    category_name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("parameter_categories.id", ondelete="SET NULL"), nullable=True)
    sort_order = Column(Integer, default=0)
    description = Column(Text)


class UnitDefinition(Base):
    __tablename__ = "unit_definitions"
    id = Column(Integer, primary_key=True, index=True)
    unit_code = Column(String(50), nullable=False, unique=True)
    unit_name = Column(String(100), nullable=False)
    symbol = Column(String(50))
    dimension_type = Column(String(50))
    precision_default = Column(Integer, default=2)


class ParameterDefinition(Base):
    __tablename__ = "parameter_definitions"
    id = Column(Integer, primary_key=True, index=True)
    param_code = Column(String(100), nullable=False, unique=True)
    param_name = Column(String(100), nullable=False)
    display_name = Column(String(100))
    category_code = Column(String(100), nullable=False)
    value_type = Column(String(50), nullable=False, default="basic")
    data_type = Column(String(50), nullable=False, default="number")
    unit_code = Column(String(50))
    precision = Column(Integer, default=2)
    default_value = Column(String(200))
    description = Column(Text)
    status = Column(String(20), default="active")
    module_id = Column(Integer, ForeignKey("formula_template_modules.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ModuleParameterValue(Base):
    """模块级参数值：参数定义挂在 FormulaTemplateModule 下，值按 模块+型号 存储。"""
    __tablename__ = "module_parameter_values"
    __table_args__ = (
        UniqueConstraint(
            "module_id",
            "version_id",
            "parameter_id",
            name="uq_module_parameter_values_module_version_param",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("formula_template_modules.id", ondelete="CASCADE"), nullable=False)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    parameter_id = Column(Integer, ForeignKey("parameter_definitions.id", ondelete="CASCADE"), nullable=False)
    param_value = Column(String(200), nullable=False)
    value_source = Column(String(50), default="manual")
    version_no = Column(String(50), default="draft")
    sort_order = Column(Integer, default=0)
    remark = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ParameterLookupDefinition(Base):
    __tablename__ = "parameter_lookup_definitions"
    id = Column(Integer, primary_key=True, index=True)
    lookup_code = Column(String(100), nullable=False, unique=True)
    lookup_name = Column(String(100), nullable=False)
    description = Column(Text)
    curve_profile = Column(JSON)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ParameterLookupRow(Base):
    __tablename__ = "parameter_lookup_rows"
    __table_args__ = (
        UniqueConstraint("lookup_id", "lookup_key", name="uq_parameter_lookup_rows_lookup_key"),
    )

    id = Column(Integer, primary_key=True, index=True)
    lookup_id = Column(Integer, ForeignKey("parameter_lookup_definitions.id", ondelete="CASCADE"), nullable=False)
    lookup_key = Column(String(100), nullable=False)
    result_value = Column(String(200), nullable=False)
    sort_order = Column(Integer, default=0)
    remark = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ParameterLookupConfig(Base):
    __tablename__ = "parameter_lookup_configs"
    __table_args__ = (
        UniqueConstraint("parameter_id", name="uq_parameter_lookup_configs_parameter"),
    )

    id = Column(Integer, primary_key=True, index=True)
    parameter_id = Column(Integer, ForeignKey("parameter_definitions.id", ondelete="CASCADE"), nullable=False)
    lookup_id = Column(Integer, ForeignKey("parameter_lookup_definitions.id", ondelete="CASCADE"), nullable=False)
    input_parameter_id = Column(Integer, ForeignKey("parameter_definitions.id", ondelete="CASCADE"), nullable=False)
    base_factor = Column(String(100), default="1")
    final_expression = Column(String(200), default="base_factor*lookup_result")
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ---------- 设备选型库 (V2 新增) ----------
class EquipmentCategory(Base):
    __tablename__ = "equipment_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) # e.g., "电机", "减速机"
    code = Column(String(50), unique=True)     # e.g., "motor", "reducer"
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("EquipmentItem", back_populates="category", cascade="all, delete-orphan")

class EquipmentItem(Base):
    __tablename__ = "equipment_items"
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("equipment_categories.id", ondelete="CASCADE"))
    model_name = Column(String(100), nullable=False) # e.g., "Y2-132S-4"
    brand = Column(String(50))
    specs = Column(JSON) # 存储具体参数，如 {"power": 5.5, "torque": 35, "efficiency": 0.88, "price": 1200}
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("EquipmentCategory", back_populates="items")


class TemplateDefinition(Base):
    __tablename__ = "template_definitions"
    id = Column(Integer, primary_key=True, index=True)
    template_code = Column(String(100), nullable=False, unique=True)
    template_name = Column(String(200), nullable=False)
    template_type = Column(String(50), nullable=False)
    scope_type = Column(String(50), nullable=False)
    scope_id = Column(Integer, nullable=False)
    source_template_id = Column(Integer, ForeignKey("template_definitions.id", ondelete="SET NULL"), nullable=True)
    version_no = Column(String(50), default="v1")
    status = Column(String(20), default="draft")
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TemplateItem(Base):
    __tablename__ = "template_items"
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("template_definitions.id", ondelete="CASCADE"), nullable=False)
    item_type = Column(String(50), nullable=False)
    item_key = Column(String(200), nullable=False)
    item_name = Column(String(200), nullable=False)
    sort_order = Column(Integer, default=0)
    group_path = Column(String(300))
    source_item_id = Column(Integer, ForeignKey("template_items.id", ondelete="SET NULL"), nullable=True)
    override_mode = Column(String(50), default="inherit")
    status = Column(String(20), default="active")
    row_snapshot = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# ---------- 产品类型表（新增） ----------
class ProductType(Base):
    __tablename__ = "product_types"
    id = Column(Integer, primary_key=True, index=True)
    type_code = Column(String(50), nullable=False, unique=True)   # 编码
    model_code = Column(String(100))                              # 代号
    type_name = Column(String(100), nullable=False)               # 名称
    alias_keywords = Column(String(200))                          # 分类别名关键字
    english_name = Column(String(100))                            # 英文
    category = Column(String(100))                                # 类型
    sort_order = Column(Integer, default=0)                       # 排序
    status = Column(String(20), default="active")                 # 状态
    version = Column(String(50))                                  # 版本
    publisher = Column(String(100))                               # 发布人
    machine_model = Column(String(50))                            # 机型 (1500, 2000, 3000, 4000, 5000)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    families = relationship("ModelFamily", back_populates="product_type")
    components = relationship("ProductComponent", back_populates="product_type", cascade="all, delete-orphan")

# ---------- 产品部件表 (BOM) ----------
class ProductComponent(Base):
    __tablename__ = "product_components"
    id = Column(Integer, primary_key=True, index=True)
    product_type_id = Column(Integer, ForeignKey("product_types.id", ondelete="CASCADE"), nullable=True)
    parent_id = Column(Integer, ForeignKey("product_components.id", ondelete="CASCADE"), nullable=True)
    index = Column(Integer)             # 序号
    code = Column(String(50))           # 编码
    model_code = Column(String(100))    # 代号
    name = Column(String(200))          # 名称
    quantity = Column(String(50))       # 数量 (可能是数字也可能是描述，用户例子是1, 4等)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    product_type = relationship("ProductType", back_populates="components")
    children = relationship("ProductComponent", backref=backref('parent', remote_side=[id]), cascade="all, delete-orphan")
    parameters = relationship("ComponentParameter", back_populates="component", cascade="all, delete-orphan")
    design_flows = relationship("ComponentDesignFlow", back_populates="component", cascade="all, delete-orphan")
    template_source_links = relationship(
        "ComponentTemplateSyncLink",
        foreign_keys="ComponentTemplateSyncLink.source_component_id",
        back_populates="source_component",
        cascade="all, delete-orphan",
    )
    template_target_links = relationship(
        "ComponentTemplateSyncLink",
        foreign_keys="ComponentTemplateSyncLink.target_component_id",
        back_populates="target_component",
        cascade="all, delete-orphan",
    )

# ---------- 部件参数表 ----------
class ComponentParameter(Base):
    __tablename__ = "component_parameters"
    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(Integer, ForeignKey("product_components.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    value = Column(String(200))
    unit = Column(String(50))
    param_type = Column(String(50), default='input') # input, calculated
    formula = Column(Text) # 如果是计算参数，存储公式
    
    component = relationship("ProductComponent", back_populates="parameters")

# ---------- 部件设计流程表 ----------
class ComponentDesignFlow(Base):
    __tablename__ = "component_design_flows"
    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(Integer, ForeignKey("product_components.id", ondelete="CASCADE"))
    flow_name = Column(String(200), nullable=False)
    sort_order = Column(Integer, default=0)
    
    component = relationship("ProductComponent", back_populates="design_flows")
    steps = relationship("ComponentFlowStep", back_populates="flow", cascade="all, delete-orphan")

class ComponentFlowStep(Base):
    __tablename__ = "component_flow_steps"
    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(Integer, ForeignKey("component_design_flows.id", ondelete="CASCADE"))
    step_name = Column(String(200), nullable=False)
    sort_order = Column(Integer, default=0)
    calculation_content = Column(JSON) # 存储类似 Excel 的表格数据和公式
    
    flow = relationship("ComponentDesignFlow", back_populates="steps")

# ---------- 型号主表（修改：增加 product_type_id） ----------
class ModelFamily(Base):
    __tablename__ = "model_families"
    id = Column(Integer, primary_key=True, index=True)
    family_code = Column(String(50), nullable=False, unique=True)
    family_name = Column(String(100))
    category = Column(String(50))                     # 保留旧字段，后续可废弃
    capacity_options = Column(String(100))            # 产量档位列表
    default_template_code = Column(String(100))       # 默认模板代号
    sort_order = Column(Integer, default=0)           # 排序
    description = Column(Text)
    product_type_id = Column(Integer, ForeignKey("product_types.id", ondelete="SET NULL"), nullable=True)  # 新增
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    product_type = relationship("ProductType", back_populates="families")
    aliases = relationship("ModelAlias", back_populates="family", cascade="all, delete-orphan")
    versions = relationship("ModelVersion", back_populates="family", cascade="all, delete-orphan")

# ---------- 别名表 ----------
class ModelAlias(Base):
    __tablename__ = "model_aliases"
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("model_families.id", ondelete="CASCADE"))
    alias_code = Column(String(50), nullable=False)
    alias_type = Column(String(20), default='old')
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    family = relationship("ModelFamily", back_populates="aliases")

# ---------- 版本表 ----------
class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("model_families.id", ondelete="CASCADE"))
    version_code = Column(String(50), nullable=False)
    capacity_value = Column(Integer)                               # 产量值
    display_name = Column(String(100))                             # 展示名称
    specification = Column(Text)
    status = Column(String(20), default='active')
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    family = relationship("ModelFamily", back_populates="versions")
    parts = relationship("VersionPart", back_populates="version", cascade="all, delete-orphan")
    attachments = relationship("VersionAttachment", back_populates="version", cascade="all, delete-orphan")

class ModelWorkbenchConfig(Base):
    __tablename__ = 'model_workbench_configs'
    id = Column(Integer, primary_key=True, index=True)
    model_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), index=True)
    formula_template_id = Column(Integer, ForeignKey('formula_templates.id', ondelete="SET NULL"), nullable=True) # 挂载的公式模板


class ModelParameterValue(Base):
    __tablename__ = "model_parameter_values"
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    parameter_id = Column(Integer, ForeignKey("parameter_definitions.id", ondelete="CASCADE"), nullable=False)
    param_value = Column(String(200), nullable=False)
    value_source = Column(String(50), default="manual")
    version_no = Column(String(50), default="draft")
    sort_order = Column(Integer, default=0)
    remark = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WorkbenchParameterSnapshot(Base):
    __tablename__ = "workbench_parameter_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    run_key = Column(String(100), nullable=False, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True)
    parameter_id = Column(Integer, ForeignKey("parameter_definitions.id", ondelete="CASCADE"), nullable=False)
    snapshot_value = Column(String(200), nullable=False)
    source_version = Column(String(50))
    source_type = Column(String(50), default="matrix")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkbenchFormulaModule(Base):
    __tablename__ = "workbench_formula_modules"
    __table_args__ = (
        UniqueConstraint("version_id", "module_code", name="uq_workbench_formula_modules_version_module"),
    )

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    module_code = Column(String(50), nullable=False)
    module_name = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WorkbenchFormulaScene(Base):
    __tablename__ = "workbench_formula_scenes"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "module_code",
            "scene_code",
            name="uq_workbench_formula_scenes_version_module_scene",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    module_code = Column(String(50), nullable=False)
    scene_code = Column(String(50), nullable=False)
    scene_name = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WorkbenchFormula(Base):
    __tablename__ = "workbench_formulas"
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    module_code = Column(String(50), nullable=False, default="power_calc")
    module_name = Column(String(100), nullable=False, default="功率计算")
    scene_code = Column(String(50), nullable=False)
    scene_name = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    expression = Column(Text, nullable=False)
    canonical_expression = Column(Text)
    variables = Column(JSON, default=dict)
    description = Column(Text, nullable=True)
    resources = Column(JSON, default=list)
    source_type = Column(String(50), default="manual")
    formula_library_id = Column(Integer, ForeignKey("formula_library.id", ondelete="SET NULL"), nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WorkbenchFormulaModuleSyncLink(Base):
    __tablename__ = "workbench_formula_module_sync_links"
    __table_args__ = (
        UniqueConstraint(
            "source_version_id",
            "source_module_code",
            "target_version_id",
            "target_module_code",
            name="uq_workbench_formula_module_sync_links_pair",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    source_module_code = Column(String(50), nullable=False)
    target_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    target_module_code = Column(String(50), nullable=False)
    sync_status = Column(String(20), default="ready")
    last_sync_mode = Column(String(50), default="manual")
    last_sync_operator = Column(String(100))
    last_sync_summary = Column(JSON, default=dict)
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WorkbenchFormulaParamMapping(Base):
    __tablename__ = "workbench_formula_param_mappings"
    __table_args__ = (
        UniqueConstraint(
            "target_version_id",
            "module_code",
            "source_param_name",
            name="uq_workbench_formula_param_mappings_target_module_param",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    target_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    module_code = Column(String(50), nullable=False)
    source_param_name = Column(String(100), nullable=False)
    target_parameter_id = Column(Integer, ForeignKey("parameter_definitions.id", ondelete="SET NULL"), nullable=True)
    target_param_name = Column(String(100), nullable=True)
    mapping_mode = Column(String(20), default="auto_same_name")
    mapping_status = Column(String(20), default="missing")
    source_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    source_module_code = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# ---------- 部件表（修改：增加 design_flows 关系） ----------
class VersionPart(Base):
    __tablename__ = "version_parts"
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"))
    part_category = Column(String(100), nullable=False)
    part_name = Column(String(200))
    part_code = Column(String(50))
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    version = relationship("ModelVersion", back_populates="parts")
    parameters = relationship("PartParameter", back_populates="part", cascade="all, delete-orphan")
    design_flows = relationship("PartDesignFlow", back_populates="part", cascade="all, delete-orphan")  # 新增

# ---------- 参数表 ----------
class PartParameter(Base):
    __tablename__ = "part_parameters"
    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("version_parts.id", ondelete="CASCADE"))
    param_name = Column(String(100), nullable=False)
    param_value = Column(Text)
    param_unit = Column(String(50))
    param_type = Column(String(20), default='text')
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    part = relationship("VersionPart", back_populates="parameters")

# ---------- 附件表 ----------
class VersionAttachment(Base):
    __tablename__ = "version_attachments"
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100))
    file_size = Column(Integer)
    file_category = Column(String(50))
    description = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(String(100))
    
    version = relationship("ModelVersion", back_populates="attachments")

# ---------- 搜索历史表 ----------
class SearchHistory(Base):
    __tablename__ = "search_history"
    id = Column(Integer, primary_key=True, index=True)
    search_term = Column(String(200), nullable=False)
    search_count = Column(Integer, default=1)
    last_searched = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# ========== 设计流程与公式计算核心模型 ==========

class FormulaLibrary(Base):
    __tablename__ = "formula_library"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    expression = Column(Text, nullable=False)        # 公式表达式，如 a + b / c
    variables = Column(JSON)                         # 变量定义，存储变量名和说明
    description = Column(Text)
    category = Column(String(50))                    # 公式分类
    canonical_expression = Column(Text)
    solve_targets = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ComponentTemplateSyncLink(Base):
    __tablename__ = "component_template_sync_links"
    id = Column(Integer, primary_key=True, index=True)
    source_type_id = Column(Integer, ForeignKey("product_types.id", ondelete="CASCADE"), nullable=False)
    source_component_id = Column(Integer, ForeignKey("product_components.id", ondelete="CASCADE"), nullable=False)
    target_type_id = Column(Integer, ForeignKey("product_types.id", ondelete="CASCADE"), nullable=False)
    target_component_id = Column(Integer, ForeignKey("product_components.id", ondelete="CASCADE"), nullable=False)
    sync_mode = Column(String(50), nullable=False, default="overwrite_template_scope")
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_source_signature = Column(String(64))

    source_component = relationship(
        "ProductComponent",
        foreign_keys=[source_component_id],
        back_populates="template_source_links",
    )
    target_component = relationship(
        "ProductComponent",
        foreign_keys=[target_component_id],
        back_populates="template_target_links",
    )

class PartDesignFlow(Base):
    __tablename__ = "part_design_flows"
    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("version_parts.id", ondelete="CASCADE"))
    flow_name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    part = relationship("VersionPart", back_populates="design_flows")
    steps = relationship("FlowStep", back_populates="flow", cascade="all, delete-orphan")

class FlowStep(Base):
    __tablename__ = "flow_steps"
    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(Integer, ForeignKey("part_design_flows.id", ondelete="CASCADE"))
    step_order = Column(String(20), nullable=False)  # 支持 1, 1.1, 1.2 等层级
    design_point = Column(String(200))               # 设计点名称
    formula_id = Column(Integer, ForeignKey("formula_library.id", ondelete="SET NULL"), nullable=True)
    custom_formula = Column(Text)                    # 手写公式
    note = Column(Text)                              # 计算说明
    result_value = Column(String(100))               # 计算出的数值结果
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    flow = relationship("PartDesignFlow", back_populates="steps")
    formula = relationship("FormulaLibrary")
    # 显式指定外键，解决歧义
    parameters = relationship("StepParameter", 
                              back_populates="step", 
                              cascade="all, delete-orphan",
                              foreign_keys="[StepParameter.step_id]")

class StepParameter(Base):
    __tablename__ = "step_parameters"
    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("flow_steps.id", ondelete="CASCADE"))
    param_name = Column(String(100), nullable=False) # 变量名
    param_value = Column(String(100))                # 变量值
    param_unit = Column(String(50))                  # 单位
    param_type = Column(String(20), default='input') # input, formula_ref, result_ref
    source_step_id = Column(Integer, ForeignKey("flow_steps.id", ondelete="SET NULL"), nullable=True) # 引用哪个步骤的结果
    
    # 显式指定外键
    step = relationship("FlowStep", back_populates="parameters", foreign_keys="[StepParameter.step_id]")
    source_step = relationship("FlowStep", foreign_keys="[StepParameter.source_step_id]")

# ---------- 操作历史记录表 ----------
class OperationHistory(Base):
    __tablename__ = "operation_history"
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String(50), nullable=False)  # create, update, delete, clone, reorder
    module = Column(String(50), nullable=False)  # product_types, product_components, design_flows, etc.
    entity_id = Column(Integer, nullable=True)  # 操作的实体ID
    before_data = Column(JSON, nullable=True)  # 操作前的数据
    after_data = Column(JSON, nullable=True)  # 操作后的数据
    context = Column(JSON, nullable=True)  # 上下文信息（如 product_type_id, component_id 等）
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ---------- 知识库与规则引擎 ----------
class DesignRule(Base):
    __tablename__ = "design_rules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    target_type = Column(String(50))  # product_type, component, or parameter
    target_id = Column(Integer, nullable=True)
    constraint_expr = Column(String(500))  # mathjs 表达式，如 "value > 0 && value < 100"
    severity = Column(String(20), default="warning")  # warning, error
    message = Column(String(200))  # 校验失败时的提示信息
    is_active = Column(Boolean, default=True)


class RuleHitRecord(Base):
    __tablename__ = "rule_hit_records"
    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(50), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(Integer, nullable=False)
    severity = Column(String(20), default="warning")
    message = Column(String(255), nullable=False)
    suggestion = Column(Text)
    status = Column(String(20), default="open")
    hit_snapshot = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GuidanceAction(Base):
    __tablename__ = "guidance_actions"
    id = Column(Integer, primary_key=True, index=True)
    rule_hit_id = Column(
        Integer,
        ForeignKey("rule_hit_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_code = Column(String(100), nullable=False)
    action_label = Column(String(200), nullable=False)
    action_type = Column(String(50), default="review")
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="open")
    result_note = Column(Text)
    result_snapshot = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    category = Column(String(50))  # 金属, 非金属, 等
    properties = Column(JSON)  # 存储密度、弹性模量、许用应力等 {"density": 7850, "allowable_stress": 235}
    description = Column(Text)

# ---------- 设计变更与协同 ----------
class DesignChange(Base):
    __tablename__ = "design_changes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    product_type_id = Column(Integer, ForeignKey("product_types.id"))
    status = Column(String(20), default="draft")  # draft, submitted, approved, rejected
    applicant = Column(String(50))
    reviewer = Column(String(50))
    change_data = Column(JSON)  # 记录变更前后的参数值对比
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DesignComment(Base):
    __tablename__ = "design_comments"
    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(50))  # component, flow, or parameter
    target_id = Column(Integer)
    user_name = Column(String(50))
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ---------- 公式模板中心 ----------
class FormulaTemplate(Base):
    __tablename__ = 'formula_templates'
    id = Column(Integer, primary_key=True, index=True)
    template_code = Column(String(50), unique=True, index=True)
    template_name = Column(String(100)) # e.g. "再生系列公式模板"
    product_type_id = Column(Integer) # 关联大类
    description = Column(String(255))
    is_active = Column(Boolean, default=True)

class FormulaTemplateModule(Base):
    __tablename__ = 'formula_template_modules'
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('formula_templates.id', ondelete="CASCADE"))
    module_code = Column(String(50))
    module_name = Column(String(100)) # e.g. "动力计算"
    sort_order = Column(Integer, default=0)

class FormulaTemplateScene(Base):
    __tablename__ = 'formula_template_scenes'
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey('formula_template_modules.id', ondelete="CASCADE"))
    scene_code = Column(String(50))
    scene_name = Column(String(100))
    sort_order = Column(Integer, default=0)
    scene_type = Column(String(50), default="calc") # 'calc' or 'verify'

class FormulaTemplateItem(Base):
    __tablename__ = 'formula_template_items'
    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey('formula_template_scenes.id', ondelete="CASCADE"))
    formula_name = Column(String(100)) # e.g. "托轮正压力"
    expression = Column(String(500)) # e.g. "=总重*9.8/(4*COS(角度/2))"
    variables = Column(JSON) # e.g. ["总重", "角度"]
    unit = Column(String(20))
    description = Column(Text, nullable=True)
    resources = Column(JSON, default=list)
    sort_order = Column(Integer, default=0)
    output_flag = Column(String(20), default="auto") # 'auto', 'force_true', 'force_false'

class ModelSelectionMapping(Base):
    __tablename__ = "model_selection_mappings"
    __table_args__ = (
        UniqueConstraint("version_id", "target_category", "target_field", name="uq_model_selection_mappings_field"),
    )
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    target_category = Column(String(50), nullable=False) # e.g. 'motor'
    target_field = Column(String(100), nullable=False)   # e.g. 'power'
    source_parameter = Column(String(200), nullable=False) # the output parameter name to bind
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ModelFocusMetricConfig(Base):
    """关注指标参考区间配置，按型号（version_id）独立存储。

    与公式的 resources 字段解耦，避免参考区间在不同型号间因模板/同步被复制共享。
    每个（型号 + 指标名）唯一，后续仅覆盖当前型号自己的配置。
    """
    __tablename__ = "model_focus_metric_configs"
    __table_args__ = (
        UniqueConstraint("version_id", "metric_name", name="uq_model_focus_metric_configs_metric"),
    )
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(200), nullable=False)  # 关注指标名称
    config = Column(JSON, default=dict)                # 参考区间/对比配置对象
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
