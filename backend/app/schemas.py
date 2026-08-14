from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ---------- 参数中心主数据 ----------
class ParameterDefinitionBase(BaseModel):
    param_code: str
    param_name: str
    display_name: Optional[str] = None
    category_code: str
    value_type: Optional[str] = "basic"
    data_type: Optional[str] = "number"
    unit_code: Optional[str] = None
    precision: Optional[int] = 2
    default_value: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "active"


class ParameterDefinitionCreate(BaseModel):
    param_code: Optional[str] = None
    param_name: Optional[str] = None
    display_name: Optional[str] = None
    category_code: Optional[str] = None
    value_type: Optional[str] = "basic"
    data_type: Optional[str] = "number"
    unit_code: Optional[str] = None
    precision: Optional[int] = 2
    default_value: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "active"


class ParameterDefinitionUpdate(ParameterDefinitionBase):
    pass


class ParameterDefinitionOut(ParameterDefinitionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ParameterDefaultUpdateRequest(BaseModel):
    default_value: str
    reason: Optional[str] = "workbench_sync"


class ParameterDefaultUpdateOut(ParameterDefinitionOut):
    sync_reason: Optional[str] = None


class ParameterImportRequest(BaseModel):
    rows: List[Dict[str, Any]] = Field(default_factory=list)


class ParameterImportError(BaseModel):
    row_no: int
    message: str


class ParameterImportResult(BaseModel):
    created_count: int = 0
    errors: List[ParameterImportError] = Field(default_factory=list)


class ParameterMatrixImportPreviewRequest(BaseModel):
    sheet_name: Optional[str] = None
    rows: List[List[Any]] = Field(default_factory=list)
    orientation_hint: str = "auto"


class ParameterMatrixImportPreviewRow(BaseModel):
    param_name: str
    unit_code: str = ""
    category_name: str = ""
    values: Dict[str, str] = Field(default_factory=dict)


class ParameterMatrixImportPreviewOut(BaseModel):
    orientation: str
    parameter_headers: List[str] = Field(default_factory=list)
    version_headers: List[str] = Field(default_factory=list)
    rows: List[ParameterMatrixImportPreviewRow] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ParameterMatrixImportCommitRequest(BaseModel):
    orientation: str
    parameter_rows: List[ParameterMatrixImportPreviewRow] = Field(default_factory=list)


class ParameterMatrixImportCommitOut(BaseModel):
    imported_parameter_count: int = 0
    saved_value_count: int = 0
    warnings: List[str] = Field(default_factory=list)


class ParameterDistributionValue(BaseModel):
    version_id: int
    version_code: str
    param_value: str = ""


class ParameterDistributionOut(BaseModel):
    parameter_id: int
    param_code: str
    param_name: str
    unit_code: Optional[str] = None
    family_id: Optional[int] = None
    family_code: Optional[str] = None
    values: List[ParameterDistributionValue] = Field(default_factory=list)


class ParameterLookupDefinitionCreate(BaseModel):
    lookup_code: Optional[str] = None
    lookup_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "active"


class ParameterLookupDefinitionOut(BaseModel):
    id: int
    lookup_code: str
    lookup_name: str
    description: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ParameterLookupRowPayload(BaseModel):
    lookup_key: str
    result_value: str
    sort_order: Optional[int] = 0
    remark: Optional[str] = None


class ParameterLookupRowsSaveRequest(BaseModel):
    rows: List[ParameterLookupRowPayload] = Field(default_factory=list)


class ParameterLookupRowsSaveOut(BaseModel):
    lookup_id: int
    saved_count: int = 0


class ParameterLookupCurveSeriesPayload(BaseModel):
    series_key: str
    source_column: str
    reverse_lookup_enabled: bool = False


class ParameterLookupCurveProfilePayload(BaseModel):
    profile_name: Optional[str] = None
    x_axis_column: Optional[str] = ""
    table_columns: List[str] = Field(default_factory=list)
    table_rows: List[Dict[str, Any]] = Field(default_factory=list)
    series_columns: List[ParameterLookupCurveSeriesPayload] = Field(default_factory=list)
    note_columns: List[str] = Field(default_factory=list)
    default_lookup_mode: str = "LINEAR"
    allow_interpolation: bool = True


class ParameterLookupCurvePointOut(BaseModel):
    x: float
    y: float


class ParameterLookupCurveSeriesOut(BaseModel):
    series_key: str
    source_column: str
    reverse_lookup_enabled: bool = False
    is_monotonic: bool = False
    points: List[ParameterLookupCurvePointOut] = Field(default_factory=list)


class ParameterLookupCurvePreviewOut(BaseModel):
    lookup_id: int
    lookup_name: str
    profile_name: Optional[str] = None
    x_axis_column: str
    series: List[ParameterLookupCurveSeriesOut] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ParameterLookupImportPreviewRequest(BaseModel):
    sheet_name: Optional[str] = None
    rows: List[List[Any]] = Field(default_factory=list)


class ParameterLookupImportError(BaseModel):
    row_no: int
    message: str


class ParameterLookupImportPreviewOut(BaseModel):
    rows: List[ParameterLookupRowPayload] = Field(default_factory=list)
    errors: List[ParameterLookupImportError] = Field(default_factory=list)
    table_columns: List[str] = Field(default_factory=list)
    table_rows: List[Dict[str, str]] = Field(default_factory=list)


class ParameterLookupConfigRequest(BaseModel):
    lookup_id: int
    input_parameter_id: int
    base_factor: Optional[str] = "1"
    final_expression: Optional[str] = "base_factor*lookup_result"
    status: Optional[str] = "active"


class ParameterLookupConfigOut(ParameterLookupConfigRequest):
    parameter_id: int
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- 设备选型库 (V2 新增) ----------
class EquipmentCategoryBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class EquipmentCategoryCreate(EquipmentCategoryBase):
    pass

class EquipmentCategoryOut(EquipmentCategoryBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EquipmentItemBase(BaseModel):
    category_id: int
    model_name: str
    brand: Optional[str] = None
    specs: Optional[Dict[str, Any]] = Field(default_factory=dict)
    status: Optional[str] = "active"

class EquipmentItemCreate(EquipmentItemBase):
    pass

class EquipmentItemOut(EquipmentItemBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EquipmentRequirements(BaseModel):
    min_power_kw: float
    target_speed_rpm: float
    speed_tolerance_percent: Optional[float] = 10.0
    min_torque_nm: float

class EquipmentRecommendRequest(BaseModel):
    category_code: str
    requirements: EquipmentRequirements

class EquipmentRecommendation(BaseModel):
    item: EquipmentItemOut
    score: float
    match_details: Dict[str, float]
    reason: str

class TemplateDefinitionBase(BaseModel):
    template_code: str
    template_name: str
    template_type: str
    scope_type: str
    scope_id: int
    source_template_id: Optional[int] = None
    version_no: Optional[str] = "v1"
    status: Optional[str] = "draft"
    description: Optional[str] = None


class TemplateDefinitionCreate(TemplateDefinitionBase):
    pass


class TemplateDefinitionOut(TemplateDefinitionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateItemBase(BaseModel):
    template_id: int
    item_type: str
    item_key: str
    item_name: str
    sort_order: Optional[int] = 0
    group_path: Optional[str] = None
    source_item_id: Optional[int] = None
    override_mode: Optional[str] = "inherit"
    status: Optional[str] = "active"
    row_snapshot: Optional[Dict[str, Any]] = None


class TemplateItemCreate(TemplateItemBase):
    pass


class TemplateItemOut(TemplateItemBase):
    id: int

    class Config:
        from_attributes = True

# ---------- 产品类型 ----------
class ProductTypeBase(BaseModel):
    type_code: str
    model_code: Optional[str] = None
    type_name: str
    alias_keywords: Optional[str] = None
    english_name: Optional[str] = None
    category: Optional[str] = None
    sort_order: Optional[int] = 0
    status: Optional[str] = "active"
    version: Optional[str] = None
    publisher: Optional[str] = None
    machine_model: Optional[str] = None
    description: Optional[str] = None

class ProductTypeCreate(ProductTypeBase):
    pass

class ProductTypeOut(ProductTypeBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# ---------- 产品部件 (BOM) ----------
class ProductComponentBase(BaseModel):
    index: Optional[int] = None
    code: Optional[str] = None
    model_code: Optional[str] = None
    name: Optional[str] = None
    quantity: Optional[str] = None
    parent_id: Optional[int] = None
    product_type_id: Optional[int] = None

class ProductComponentCreate(ProductComponentBase):
    pass

class ProductComponentOut(ProductComponentBase):
    id: int
    created_at: Optional[datetime] = None
    children: List['ProductComponentOut'] = []
    class Config:
        from_attributes = True

# ---------- 部件参数 ----------
class ComponentParameterBase(BaseModel):
    name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    param_type: Optional[str] = 'input'
    formula: Optional[str] = None

class ComponentParameterCreate(ComponentParameterBase):
    component_id: int

class ComponentParameterOut(ComponentParameterBase):
    id: int
    class Config:
        from_attributes = True

# ---------- 设计流程 ----------
class ComponentFlowStepBase(BaseModel):
    step_name: str
    sort_order: Optional[int] = 0
    calculation_content: Optional[Dict[str, Any]] = None

class ComponentFlowStepCreate(ComponentFlowStepBase):
    flow_id: int

class ComponentFlowStepOut(ComponentFlowStepBase):
    id: int
    class Config:
        from_attributes = True

class ComponentDesignFlowBase(BaseModel):
    flow_name: str
    sort_order: Optional[int] = 0

class ComponentDesignFlowCreate(ComponentDesignFlowBase):
    component_id: int

class ComponentDesignFlowOut(ComponentDesignFlowBase):
    id: int
    steps: List[ComponentFlowStepOut] = []
    class Config:
        from_attributes = True

# ---------- 产品型号 (Family) ----------
class ModelFamilyBase(BaseModel):
    family_code: str
    family_name: Optional[str] = None
    category: Optional[str] = None
    capacity_options: Optional[str] = None
    default_template_code: Optional[str] = None
    sort_order: Optional[int] = 0
    description: Optional[str] = None
    product_type_id: Optional[int] = None

class ModelFamilyCreate(ModelFamilyBase):
    pass

class ModelFamilyOut(ModelFamilyBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# ---------- 别名 (Alias) ----------
class ModelAliasBase(BaseModel):
    alias_code: str
    alias_type: Optional[str] = 'old'
    is_primary: Optional[bool] = False

class ModelAliasCreate(ModelAliasBase):
    family_id: int

class ModelAliasOut(ModelAliasBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# ---------- 版本 ----------
class ModelVersionBase(BaseModel):
    family_id: Optional[int] = None
    version_code: str
    capacity_value: Optional[int] = None
    display_name: Optional[str] = None
    specification: Optional[str] = None
    status: Optional[str] = 'active'
    created_by: Optional[str] = None

class ModelVersionCreate(ModelVersionBase):
    pass

class ModelVersionOut(ModelVersionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# ---------- 附件 (Attachment) ----------
class VersionAttachmentBase(BaseModel):
    file_name: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_category: Optional[str] = None
    description: Optional[str] = None

class VersionAttachmentCreate(VersionAttachmentBase):
    version_id: int
    file_path: str

class VersionAttachmentOut(VersionAttachmentBase):
    id: int
    file_path: str
    class Config:
        from_attributes = True


class ModelParameterValueBase(BaseModel):
    version_id: int
    parameter_id: int
    param_value: str
    value_source: Optional[str] = "manual"
    version_no: Optional[str] = "draft"
    sort_order: Optional[int] = 0
    remark: Optional[str] = None


class ModelParameterValueOut(ModelParameterValueBase):
    id: int

    class Config:
        from_attributes = True


class WorkbenchParameterSnapshotBase(BaseModel):
    run_key: str
    version_id: Optional[int] = None
    parameter_id: int
    snapshot_value: str
    source_version: Optional[str] = None
    source_type: Optional[str] = "matrix"


class WorkbenchParameterSnapshotOut(WorkbenchParameterSnapshotBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkbenchFormulaUpsertRequest(BaseModel):
    id: Optional[int] = None
    model_id: int
    module_code: Optional[str] = "power_calc"
    module_name: Optional[str] = "功率计算"
    scene_code: str
    scene_name: str
    name: str
    expression: str
    canonical_expression: Optional[str] = None
    variables: Dict[str, str] = Field(default_factory=dict)
    description: Optional[str] = None
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    source_type: Optional[str] = "manual"
    formula_library_id: Optional[int] = None
    sort_order: Optional[int] = 0


class WorkbenchFormulaOut(BaseModel):
    id: int
    model_id: int
    module_code: str = "power_calc"
    module_name: str = "功率计算"
    scene_code: str
    scene_name: str
    name: str
    expression: str
    canonical_expression: Optional[str] = None
    variables: Dict[str, str] = Field(default_factory=dict)
    description: Optional[str] = None
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    source_type: str = "manual"
    formula_library_id: Optional[int] = None
    sort_order: int = 0


class WorkbenchFormulaReorderRow(BaseModel):
    id: int
    sort_order: int


class WorkbenchFormulaReorderRequest(BaseModel):
    rows: List[WorkbenchFormulaReorderRow] = Field(default_factory=list)


class WorkbenchFormulaBatchDeleteRequest(BaseModel):
    formula_ids: List[int] = Field(default_factory=list)


class WorkbenchFormulaBatchDeleteOut(BaseModel):
    success: bool = True
    deleted_count: int = 0
    deleted_ids: List[int] = Field(default_factory=list)


class WorkbenchFormulaDeleteOut(BaseModel):
    success: bool = True
    deleted_formula_id: int


class WorkbenchFormulaSceneOut(BaseModel):
    module_code: str
    module_name: str
    scene_code: str
    scene_name: str
    formulas: List[WorkbenchFormulaOut] = Field(default_factory=list)


class WorkbenchFormulaModuleSyncInfo(BaseModel):
    source_version_id: int
    source_version_name: str
    source_module_code: str
    sync_status: str
    last_synced_at: Optional[str] = None

class WorkbenchFormulaModuleOut(BaseModel):
    module_code: str
    module_name: str
    scenes: List[WorkbenchFormulaSceneOut] = Field(default_factory=list)
    sync_info: Optional[WorkbenchFormulaModuleSyncInfo] = None


class WorkbenchFormulaModuleListOut(BaseModel):
    modules: List[WorkbenchFormulaModuleOut] = Field(default_factory=list)
    rows: List[WorkbenchFormulaOut] = Field(default_factory=list)


class WorkbenchTypeModuleEntryOut(BaseModel):
    module_code: str
    module_name: str
    description: str = ""
    scene_count: int = 0
    formula_count: int = 0
    source_type_id: int


class WorkbenchTypeModuleEntryListOut(BaseModel):
    type_id: int
    modules: List[WorkbenchTypeModuleEntryOut] = Field(default_factory=list)


class WorkbenchFormulaModuleCreateRequest(BaseModel):
    module_name: str
    module_code: Optional[str] = ""


class WorkbenchFormulaModuleRenameRequest(BaseModel):
    module_name: str


class WorkbenchFormulaSceneCreateRequest(BaseModel):
    module_code: str
    scene_name: str


class WorkbenchFormulaSceneRenameRequest(BaseModel):
    scene_name: str


class WorkbenchFormulaModuleDeleteOut(BaseModel):
    success: bool = True
    deleted_module_code: str
    deleted_scene_count: int = 0
    deleted_formula_count: int = 0


class WorkbenchFormulaSceneDeleteOut(BaseModel):
    success: bool = True
    deleted_module_code: str
    deleted_scene_code: str
    deleted_formula_count: int = 0


class WorkbenchFormulaMappingSaveRow(BaseModel):
    source_param_name: str
    target_parameter_id: int
    target_param_name: str


class WorkbenchFormulaMappingSaveRequest(BaseModel):
    mappings: List[WorkbenchFormulaMappingSaveRow] = Field(default_factory=list)


class WorkbenchFormulaSyncTargetOut(BaseModel):
    version_id: int
    version_code: str
    family_id: Optional[int] = None
    family_code: Optional[str] = None
    product_type_id: Optional[int] = None
    product_type_name: Optional[str] = None
    enabled: bool = True


class WorkbenchFormulaMappingOut(BaseModel):
    source_param_name: str
    target_parameter_id: Optional[int] = None
    target_param_name: Optional[str] = None
    mapping_mode: str = "auto_same_name"
    mapping_status: str = "missing"
    candidate_parameters: List[ParameterDefinitionOut] = Field(default_factory=list)


class WorkbenchFormulaSyncPreviewTargetOut(BaseModel):
    target_version_id: int
    target_version_code: str
    status: str = "ready"
    new_modules: List[str] = Field(default_factory=list)
    new_scenes: List[str] = Field(default_factory=list)
    new_formulas: List[str] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    auto_mappings: List[WorkbenchFormulaMappingOut] = Field(default_factory=list)
    missing_mappings: List[WorkbenchFormulaMappingOut] = Field(default_factory=list)


class WorkbenchFormulaSyncTargetsOut(BaseModel):
    targets: List[WorkbenchFormulaSyncTargetOut] = Field(default_factory=list)


class WorkbenchFormulaSyncPreviewRequest(BaseModel):
    scope_type: str = "manual"
    target_version_ids: List[int] = Field(default_factory=list)


class WorkbenchFormulaSyncPreviewOut(BaseModel):
    source: Dict[str, Any]
    targets: List[WorkbenchFormulaSyncPreviewTargetOut] = Field(default_factory=list)


class WorkbenchFormulaSyncConflictAction(BaseModel):
    target_version_id: int
    scene_code: str
    formula_name: str
    action: str = "overwrite"


class WorkbenchFormulaSyncExecuteRequest(BaseModel):
    target_version_ids: List[int] = Field(default_factory=list)
    conflict_actions: List[WorkbenchFormulaSyncConflictAction] = Field(default_factory=list)
    allow_missing_mapping_targets: List[int] = Field(default_factory=list)


class WorkbenchFormulaSyncExecuteOut(BaseModel):
    success_target_count: int = 0
    skipped_target_count: int = 0
    failed_target_count: int = 0
    created_module_count: int = 0
    created_scene_count: int = 0
    created_formula_count: int = 0
    overwritten_formula_count: int = 0
    missing_mapping_count: int = 0


class FamilyMatrixRowInput(BaseModel):
    version_id: int
    parameter_id: int
    param_value: Optional[str] = ""
    value_source: Optional[str] = "manual"
    version_no: Optional[str] = "draft"
    sort_order: Optional[int] = 0
    remark: Optional[str] = None


class FamilyMatrixSaveRequest(BaseModel):
    rows: List[FamilyMatrixRowInput] = Field(default_factory=list)


class WorkbenchParameterValueInput(BaseModel):
    version_id: int
    parameter_id: Optional[int] = 0
    param_code: Optional[str] = ""
    param_name: str = ""
    param_value: str = ""
    unit_code: Optional[str] = ""
    value_type: Optional[str] = "basic"
    description: Optional[str] = None
    remark: Optional[str] = None


class WorkbenchParameterSaveRequest(BaseModel):
    family_id: int
    module_code: Optional[str] = ""
    module_id: Optional[int] = None
    rows: List[WorkbenchParameterValueInput] = Field(default_factory=list)


class WorkbenchSnapshotRowInput(BaseModel):
    version_id: Optional[int] = None
    parameter_id: int
    snapshot_value: str
    source_version: Optional[str] = None
    source_type: Optional[str] = "matrix"


class WorkbenchSnapshotCreateRequest(BaseModel):
    run_key: str = ""
    rows: List[WorkbenchSnapshotRowInput] = Field(default_factory=list)


class DrumTreeVersionOut(BaseModel):
    id: int
    version_code: str
    capacity_value: Optional[int] = None
    display_name: Optional[str] = None


class DrumTreeFamilyOut(BaseModel):
    id: int
    family_code: str
    family_name: Optional[str] = None
    capacity_options: Optional[str] = None
    versions: List[DrumTreeVersionOut] = Field(default_factory=list)


class DrumTreeTypeOut(BaseModel):
    id: int
    type_name: str
    alias_keywords: Optional[str] = None
    families: List[DrumTreeFamilyOut] = Field(default_factory=list)


class DrumGenerateVersionsOut(BaseModel):
    family_id: int
    created_count: int
    versions: List[DrumTreeVersionOut] = Field(default_factory=list)


class DrumDesignExecuteRequest(BaseModel):
    model_id: Optional[int] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class DrumDesignResultOut(BaseModel):
    scene_code: str
    scene_name: str
    result_code: str
    result_name: str
    result_value: str
    unit_code: Optional[str] = None
    source_formula: Optional[str] = None
    lookup_detail: Optional[Dict[str, Any]] = None


class DrumDesignExecuteOut(BaseModel):
    results: List[DrumDesignResultOut] = Field(default_factory=list)
    scope: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class DrumDesignAnalyzeRequest(BaseModel):
    model_id: Optional[int] = None
    target_parameter: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result_name: str = "推荐电机功率"
    steps: int = 5
    delta_ratio: float = 0.2


class DrumDesignAnalyzeOut(BaseModel):
    target_parameter: str
    result_name: str
    x_axis: List[str] = Field(default_factory=list)
    values: List[str] = Field(default_factory=list)


class DrumDesignImpactAnalyzeRequest(BaseModel):
    model_id: int
    target_result_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class DrumDesignImpactItem(BaseModel):
    parameter_name: str
    impact_level: str
    direction: str
    sensitivity: float
    parameter_type: str


class DrumDesignImpactAnalyzeOut(BaseModel):
    target_result_name: str
    impacts: List[DrumDesignImpactItem] = Field(default_factory=list)


class DrumVerificationScanRequest(BaseModel):
    model_id: int
    result_name: str
    scan_parameter: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    scan_start: Optional[float] = None
    scan_end: Optional[float] = None
    scan_step: Optional[float] = None
    steps: int = 21


class DrumVerificationScanPointOut(BaseModel):
    parameter_value: str
    actual_value: str = ""
    theory_value: str = ""
    margin_value: str = ""
    pass_status: str = "unknown"


class DrumVerificationScanRangeOut(BaseModel):
    start: str = ""
    end: str = ""
    status: str = "pass"


class DrumVerificationScanSummaryOut(BaseModel):
    current_parameter_value: str = ""
    current_actual_value: str = ""
    current_theory_value: str = ""
    current_margin_value: str = ""
    current_pass_status: str = "unknown"
    min_margin_value: str = ""
    worst_parameter_value: str = ""
    usable_ranges_text: str = ""


class DrumVerificationScanOut(BaseModel):
    result_name: str
    scan_parameter: str
    unit_code: str = ""
    scan_start: str = ""
    scan_end: str = ""
    scan_step: str = ""
    points: List[DrumVerificationScanPointOut] = Field(default_factory=list)
    pass_ranges: List[DrumVerificationScanRangeOut] = Field(default_factory=list)
    fail_ranges: List[DrumVerificationScanRangeOut] = Field(default_factory=list)
    summary: DrumVerificationScanSummaryOut = Field(default_factory=DrumVerificationScanSummaryOut)
    warnings: List[str] = Field(default_factory=list)


class DrumDesignCompareCaseInput(BaseModel):
    case_name: str
    results: List[DrumDesignResultOut] = Field(default_factory=list)


class DrumDesignCompareRequest(BaseModel):
    mode: str = "same_model"
    case_ids: List[int] = Field(default_factory=list)
    family_id: Optional[int] = None
    cases: List[DrumDesignCompareCaseInput] = Field(default_factory=list)


class DrumDesignCompareRowOut(BaseModel):
    result_name: str
    values: Dict[str, str] = Field(default_factory=dict)
    delta: str = ""


class DrumDesignCompareOut(BaseModel):
    mode: str
    rows: List[DrumDesignCompareRowOut] = Field(default_factory=list)

# ---------- 部件参数 (新增) ----------
class PartParameterBase(BaseModel):
    param_name: Optional[str] = None
    param_value: Optional[str] = None
    param_unit: Optional[str] = None
    param_type: Optional[str] = 'text'
    sort_order: Optional[int] = 0

class PartParameterCreate(PartParameterBase):
    part_id: Optional[int] = None

class PartParameterOut(PartParameterBase):
    id: int
    class Config:
        from_attributes = True

# ---------- 部件 ----------
class VersionPartBase(BaseModel):
    version_id: Optional[int] = None
    part_category: Optional[str] = None
    part_name: Optional[str] = None
    part_code: Optional[str] = None
    sort_order: Optional[int] = 0
    parameters: List[PartParameterBase] = []  # 新增：允许在创建部件时带上参数

class VersionPartCreate(VersionPartBase):
    pass

class VersionPartOut(VersionPartBase):
    id: int
    created_at: Optional[datetime] = None
    parameters: List[PartParameterOut] = []  # 新增
    class Config:
        from_attributes = True

# ---------- 公式库 ----------
class FormulaBase(BaseModel):
    name: str
    expression: str
    variables: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    category: Optional[str] = None
    canonical_expression: Optional[str] = None
    solve_targets: Dict[str, Any] = Field(default_factory=dict)

class FormulaCreate(FormulaBase):
    pass

class FormulaUpdate(BaseModel):
    name: Optional[str] = None
    expression: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    category: Optional[str] = None
    canonical_expression: Optional[str] = None
    solve_targets: Optional[Dict[str, Any]] = None

class FormulaOut(FormulaBase):
    id: int
    class Config:
        from_attributes = True

class FormulaEvaluateRequest(BaseModel):
    expression: str
    scope: Dict[str, Any] = Field(default_factory=dict)
    available_variable_names: List[str] = Field(default_factory=list)
    precision: int = 4

class FormulaEvaluateResult(BaseModel):
    value: Optional[float] = None
    formatted_value: str
    normalized_expression: str
    processed_expression: str
    mapped_scope: Dict[str, Any] = Field(default_factory=dict)


class TemplateSyncTarget(BaseModel):
    target_type_id: int
    target_component_id: int


class TemplateSyncRequest(BaseModel):
    targets: List[TemplateSyncTarget]
    sync_mode: str = "overwrite_template_scope"
    create_link: bool = True


class TemplateResyncRequest(BaseModel):
    target_component_ids: List[int] = Field(default_factory=list)
    sync_mode: Optional[str] = None


class TemplateExecuteSyncRequest(BaseModel):
    source_component_id: int
    target_component_id: int
    sync_mode: Optional[str] = "overwrite_template_scope"


class ComponentTemplateSyncLinkOut(BaseModel):
    id: int
    source_type_id: int
    source_component_id: int
    target_type_id: int
    target_component_id: int
    sync_mode: str
    last_synced_at: Optional[datetime] = None
    last_source_signature: Optional[str] = None

    class Config:
        from_attributes = True


class TemplateSyncResultOut(BaseModel):
    target_type_id: int
    target_component_id: int
    sync_mode: str
    stats: Dict[str, int]
    link_id: Optional[int] = None


class TemplateSyncResponse(BaseModel):
    source_component_id: int
    source_signature: str
    results: List[TemplateSyncResultOut]

# ---------- 设计流程步骤参数 ----------
class StepParameterBase(BaseModel):
    param_name: str
    param_value: Optional[str] = None
    param_unit: Optional[str] = None
    param_type: Optional[str] = 'input'
    source_step_id: Optional[int] = None

class StepParameterCreate(StepParameterBase):
    step_id: int

class StepParameterOut(StepParameterBase):
    id: int
    class Config:
        from_attributes = True

# ---------- 设计流程步骤 ----------
class FlowStepBase(BaseModel):
    step_order: str
    design_point: Optional[str] = None
    formula_id: Optional[int] = None
    custom_formula: Optional[str] = None
    note: Optional[str] = None
    result_value: Optional[str] = None
    parameters: List[StepParameterBase] = []

class FlowStepCreate(FlowStepBase):
    flow_id: Optional[int] = None

class FlowStepOut(FlowStepBase):
    id: int
    parameters: List[StepParameterOut] = []
    class Config:
        from_attributes = True

# ---------- 设计流程 ----------
class DesignFlowBase(BaseModel):
    part_id: Optional[int] = None
    flow_name: str
    description: Optional[str] = None

class DesignFlowCreate(DesignFlowBase):
    pass

class DesignFlowOut(DesignFlowBase):
    id: int
    steps: List[FlowStepOut] = []
    class Config:
        from_attributes = True

# ---------- 知识库与规则引擎 ----------
class DesignRuleBase(BaseModel):
    name: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    constraint_expr: Optional[str] = None
    severity: Optional[str] = "warning"
    message: Optional[str] = None
    is_active: Optional[bool] = True

class DesignRuleOut(DesignRuleBase):
    id: int
    class Config:
        from_attributes = True


class RuleHitRecordBase(BaseModel):
    source_type: str
    target_type: str
    target_id: int
    severity: Optional[str] = "warning"
    message: str
    suggestion: Optional[str] = None
    status: Optional[str] = "open"
    hit_snapshot: Optional[Dict[str, Any]] = None


class RuleHitRecordCreate(RuleHitRecordBase):
    pass


class RuleHitRecordOut(RuleHitRecordBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GuidanceActionBase(BaseModel):
    rule_hit_id: int
    action_code: str
    action_label: str
    action_type: Optional[str] = "review"
    priority: Optional[str] = "medium"
    status: Optional[str] = "open"
    result_note: Optional[str] = None
    result_snapshot: Optional[Dict[str, Any]] = None


class GuidanceActionOut(GuidanceActionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GuidanceActionUpdate(BaseModel):
    status: str
    result_note: Optional[str] = None
    result_snapshot: Optional[Dict[str, Any]] = None


class MaterialBase(BaseModel):
    name: str
    category: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

class MaterialOut(MaterialBase):
    id: int
    class Config:
        from_attributes = True

# ---------- 搜索与建议 ----------
class SearchSuggestion(BaseModel):
    text: str
    type: str  # family, version, part
    id: int

# ---------- 操作历史记录 ----------
class OperationHistoryBase(BaseModel):
    operation_type: str
    module: str
    entity_id: Optional[int] = None
    before_data: Optional[Dict[str, Any]] = None
    after_data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

class OperationHistoryCreate(OperationHistoryBase):
    pass

class OperationHistoryOut(OperationHistoryBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# ---------- 公式模板中心 ----------
class FormulaTemplateBase(BaseModel):
    template_code: str
    template_name: Optional[str] = None
    product_type_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True

class FormulaTemplateCreate(FormulaTemplateBase):
    pass

class FormulaTemplateOut(FormulaTemplateBase):
    id: int
    class Config:
        from_attributes = True

# ---------- 兼容旧代码的别名 (必须放在定义之后) ----------
FamilyCreate = ModelFamilyCreate
FamilyOut = ModelFamilyOut
PartCreate = VersionPartCreate
PartOut = VersionPartOut
VersionCreate = ModelVersionCreate
VersionOut = ModelVersionOut
ParameterCreate = PartParameterCreate
ParameterOut = PartParameterOut
AliasOut = ModelAliasOut
AttachmentOut = VersionAttachmentOut
