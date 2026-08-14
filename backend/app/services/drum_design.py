import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models import (
    FormulaTemplate,
    FormulaTemplateItem,
    FormulaTemplateModule,
    FormulaTemplateScene,
    ModelFamily,
    ModelFocusMetricConfig,
    ModelParameterValue,
    ModelVersion,
    ModelWorkbenchConfig,
    ParameterDefinition,
    ParameterLookupConfig,
    ParameterLookupDefinition,
    ParameterLookupRow,
    ProductType,
    WorkbenchFormula,
    WorkbenchFormulaModule,
    WorkbenchFormulaModuleSyncLink,
    WorkbenchFormulaParamMapping,
    WorkbenchFormulaScene,
)
from app.services.formula_engine import FormulaEngineError, evaluate_formula_expression
from app.services.drum_catalog import build_drum_tree
from app.services.parameter_lookup_catalog import (
    ParameterLookupValidationError,
    resolve_curve_result_value,
    resolve_lookup_result_value,
)


# 旧版硬编码默认公式已清空。功率计算公式改由公式模板（FormulaTemplate* 表）维护，
# 模板通过 ModelWorkbenchConfig.formula_template_id 挂载到型号，新工作台（NewDesignWorkbench）
# 只从模板表读取公式，不再依赖这里的默认种子。
SCENE_DEFINITIONS = ()


class DrumDesignError(ValueError):
    pass


IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_\u00C0-\uFFFF][A-Za-z0-9_\u00C0-\uFFFF]*")
RESERVED_IDENTIFIERS = {
    "COS", "SIN", "TAN", "ABS", "MIN", "MAX", "ROUND", "PI",
    "CURVE2D", "X2Y", "Y2X", "LINEAR", "LOG", "LN", "EXP",
    "SQRT", "POWER", "INT", "MOD", "FLOOR", "CEIL",
    "IF", "IFERROR", "AND", "OR", "NOT", "TRUE", "FALSE",
    "LOOKUP", "VLOOKUP", "HLOOKUP", "INDEX", "MATCH",
    "SELECT_EQUIP", "SUM", "AVERAGE", "COUNT",
    "DRN", "DL", "SR", "DR",
}
FORMULA_FUNC_RESERVED_UPPER = {n.upper() for n in RESERVED_IDENTIFIERS}
DEFAULT_MODULE_CODE = "power_calc"
DEFAULT_MODULE_NAME = "功率计算"
PARAMETER_ALIAS_SPECS = {
    "电机转速": (("电机_额定转速", None),),
    "传动比": (("减速机_减速比", None), ("减速比", None), ("减速比i", None)),
    "电机效率": (("电机_100%效率", "percent"),),
    "进料量": (("滚筒产量", None), ("产量", None)),
    "滚筒重量": (("筒体重量", None), ("简体重量", None)),
    "电机频率": (("电机_频率", None),),
    "电机额定转矩": (("电机_额定转矩", None),),
    "输出转矩": (("输出扭矩", None),),
    "理论转矩": (("理论扭矩", None),),
    "实际工作滚筒转速": (("滚筒转速", None), ("实际滚筒转速", None), ("工作滚筒转速", None)),
}
PARAMETER_DEFAULT_VALUES = {
    "功率储备系数": 1.0,
}
SYMBOLIC_NAME_ALIAS_GROUPS = {
    "电机转速": ("电机_额定转速", "输入转速nN"),
    "传动比": ("减速机_减速比", "减速比", "减速比i"),
    "电机效率": ("电机_100%效率",),
    "进料量": ("滚筒产量", "产量"),
    "滚筒重量": ("筒体重量", "简体重量"),
    "存料量": ("筒内料重",),
    "电机频率": ("电机_频率", "电机转速频率", "电机电源频率"),
    "电机额定转矩": ("电机_额定转矩", "电机额定扭矩", "电机_额定扭矩"),
    "输出转矩": ("输出扭矩",),
    "理论转矩": ("理论扭矩",),
    "实际工作滚筒转速": ("滚筒转速", "实际滚筒转速", "工作滚筒转速"),
}


def _extract_expression_variables(expression):
    ordered_tokens = []
    for token in IDENTIFIER_PATTERN.findall(str(expression or "")):
        normalized = token.upper()
        if normalized in RESERVED_IDENTIFIERS or token in ordered_tokens:
            continue
        ordered_tokens.append(token)
    return {token: "" for token in ordered_tokens}


def _resolve_tree_type_id_for_version(db: Session, model_id: int):
    tree_payload = build_drum_tree(db)
    for type_node in tree_payload:
        for family in type_node.get("families", []):
            for version in family.get("versions", []):
                if int(version.get("id") or 0) == int(model_id or 0):
                    return int(type_node.get("id") or 0)
    return None


def _is_module_visible_for_tree_type(tree_type_id: Optional[int], module_code: str, module_name: str) -> bool:
    return bool(int(tree_type_id or 0) and str(module_code or "").strip())


def _assert_module_allowed_for_model(db: Session, model_id: int, module_code: str, module_name: str):
    tree_type_id = _resolve_tree_type_id_for_version(db, model_id)
    if _is_module_visible_for_tree_type(tree_type_id, module_code, module_name):
        return
    raise DrumDesignError("当前产品大类不允许使用该计算模块")


def _normalize_numeric_scope(parameters, allowed_keys=None):
    allowed_name_set = None
    if allowed_keys is not None:
        allowed_name_set = {str(item or "").strip() for item in allowed_keys if str(item or "").strip()}
    scope = {}
    for key, value in (parameters or {}).items():
        normalized_key = str(key).strip()
        if allowed_name_set is not None and normalized_key not in allowed_name_set:
            continue
        if value is None or str(value).strip() == "":
            continue
        try:
            scope[normalized_key] = float(value)
        except (TypeError, ValueError) as exc:
            raise DrumDesignError(f"参数 {key} 不是有效数字") from exc
    return scope


def _transform_alias_value(value, transform=None):
    numeric_value = float(value)
    if transform == "percent":
        return numeric_value / 100 if abs(numeric_value) > 1 else numeric_value
    return numeric_value


def _apply_parameter_aliases(scope, full_scope):
    resolved_scope = dict(scope or {})
    full_scope = dict(full_scope or {})
    for target_name, alias_specs in PARAMETER_ALIAS_SPECS.items():
        if target_name in resolved_scope:
            continue
        for alias_name, transform in alias_specs:
            if alias_name not in full_scope:
                continue
            resolved_scope[target_name] = _transform_alias_value(full_scope[alias_name], transform)
            break

    for target_name, default_value in PARAMETER_DEFAULT_VALUES.items():
        if target_name not in resolved_scope:
            resolved_scope[target_name] = float(default_value)
    return _expand_symbolic_alias_values(resolved_scope)


def _iter_equivalent_symbolic_names(name):
    normalized_name = str(name or "").strip()
    if not normalized_name:
        return []

    collected = []
    seen = set()

    def _append(candidate):
        normalized_candidate = str(candidate or "").strip()
        if not normalized_candidate or normalized_candidate in seen:
            return
        seen.add(normalized_candidate)
        collected.append(normalized_candidate)

    _append(normalized_name)
    for canonical_name, alias_names in SYMBOLIC_NAME_ALIAS_GROUPS.items():
        normalized_canonical = str(canonical_name or "").strip()
        normalized_aliases = [str(item or "").strip() for item in alias_names if str(item or "").strip()]
        if normalized_name == normalized_canonical or normalized_name in normalized_aliases:
            _append(normalized_canonical)
            for alias_name in normalized_aliases:
                _append(alias_name)
    return collected


def _expand_symbolic_alias_values(scope):
    expanded_scope = dict(scope or {})
    for key, value in list(expanded_scope.items()):
        for alias_name in _iter_equivalent_symbolic_names(key):
            expanded_scope.setdefault(alias_name, value)
    return expanded_scope


def _resolve_formula_reference_name(name, formula_by_name):
    normalized_name = str(name or "").strip()
    if not normalized_name:
        return ""
    if normalized_name in (formula_by_name or {}):
        return normalized_name
    for alias_name in _iter_equivalent_symbolic_names(normalized_name):
        if alias_name in (formula_by_name or {}):
            return alias_name
    return ""


def _format_lookup_key(value):
    numeric_value = float(value)
    if numeric_value.is_integer():
        return str(int(numeric_value))
    return format(numeric_value, "g")


def _load_active_lookup_result_specs(db: Session):
    configs = (
        db.query(ParameterLookupConfig)
        .filter(ParameterLookupConfig.status == "active")
        .order_by(ParameterLookupConfig.id.asc())
        .all()
    )
    specs = []
    for config in configs:
        target_parameter = (
            db.query(ParameterDefinition)
            .filter(ParameterDefinition.id == config.parameter_id)
            .first()
        )
        input_parameter = (
            db.query(ParameterDefinition)
            .filter(ParameterDefinition.id == config.input_parameter_id)
            .first()
        )
        lookup_definition = (
            db.query(ParameterLookupDefinition)
            .filter(ParameterLookupDefinition.id == config.lookup_id)
            .first()
        )
        if not target_parameter or not input_parameter or not lookup_definition:
            continue
        specs.append(
            {
                "config": config,
                "target_parameter": target_parameter,
                "input_parameter": input_parameter,
                "lookup_definition": lookup_definition,
            }
        )
    return specs


def _collect_required_numeric_parameter_names(scene_formulas=None, db: Session = None):
    formula_names = set()
    dependency_names = set()
    for scene in scene_formulas or []:
        for formula in scene.get("formulas", []):
            formula_name = _get_formula_name(formula)
            if formula_name:
                formula_names.add(formula_name)
            dependency_names.update(_get_formula_dependencies(formula))

    required_names = {name for name in dependency_names if name and name not in formula_names}
    if db is not None:
        for spec in _load_active_lookup_result_specs(db):
            input_name = str(spec["input_parameter"].param_name or "").strip()
            if input_name:
                required_names.add(input_name)
    return required_names


def _build_lookup_results(db: Session, base_scope, resolved_scope, explicit_scope=None, preserve_explicit_names=None):
    if db is None:
        return []

    lookup_results = []
    scope = {**base_scope, **resolved_scope}
    explicit_expanded = _expand_symbolic_alias_values(_normalize_numeric_scope(explicit_scope) if explicit_scope else {})
    preserved_names = set()
    for raw_name in preserve_explicit_names or []:
        for alias_name in _iter_equivalent_symbolic_names(raw_name):
            preserved_names.add(alias_name)
    for spec in _load_active_lookup_result_specs(db):
        input_name = str(spec["input_parameter"].param_name or "").strip()
        target_name = str(spec["target_parameter"].param_name or "").strip()
        if not input_name or not target_name:
            continue
        if input_name not in scope:
            continue

        target_aliases = set(_iter_equivalent_symbolic_names(target_name)) or {target_name}
        if target_aliases & preserved_names:
            explicit_override = next(
                (explicit_expanded.get(alias_name) for alias_name in target_aliases if alias_name in explicit_expanded),
                None,
            )
            if explicit_override is not None:
                for alias_name in target_aliases:
                    resolved_scope[alias_name] = explicit_override
                    scope[alias_name] = explicit_override
                continue

        lookup_key = _format_lookup_key(scope[input_name])
        lookup_row = (
            db.query(ParameterLookupRow)
            .filter(
                ParameterLookupRow.lookup_id == spec["lookup_definition"].id,
                ParameterLookupRow.lookup_key == lookup_key,
            )
            .first()
        )
        if not lookup_row:
            raise DrumDesignError(f"附录“{spec['lookup_definition'].lookup_name}”未找到键值 {lookup_key}")

        try:
            lookup_result = float(lookup_row.result_value)
        except (TypeError, ValueError) as exc:
            raise DrumDesignError(
                f"附录“{spec['lookup_definition'].lookup_name}”结果值不是有效数字: {lookup_row.result_value}"
            ) from exc

        try:
            base_factor = float(spec["config"].base_factor or "1")
        except (TypeError, ValueError) as exc:
            raise DrumDesignError(f"参数 {target_name} 的固定系数不是有效数字") from exc

        resolved_value = base_factor * lookup_result
        resolved_scope[target_name] = resolved_value
        scope[target_name] = resolved_value
        lookup_results.append(
            {
                "scene_code": "lookup_appendix",
                "scene_name": "查表附录",
                "result_code": target_name,
                "result_name": target_name,
                "result_value": format(resolved_value, "g"),
                "unit_code": spec["target_parameter"].unit_code or "",
                "source_formula": target_name,
                "lookup_detail": {
                    "lookup_name": spec["lookup_definition"].lookup_name,
                    "lookup_key": lookup_key,
                    "result_value": lookup_row.result_value,
                    "base_factor": str(spec["config"].base_factor or "1"),
                },
            }
        )

    return lookup_results


def build_default_scene_formulas(model_id=None):
    scenes = []
    for scene_code, scene_name, formulas in SCENE_DEFINITIONS:
        scenes.append(
            {
                "module_code": DEFAULT_MODULE_CODE,
                "module_name": DEFAULT_MODULE_NAME,
                "scene_code": scene_code,
                "scene_name": scene_name,
                "formulas": [
                    {
                        "id": 0,
                        "model_id": int(model_id or 0),
                        "module_code": DEFAULT_MODULE_CODE,
                        "module_name": DEFAULT_MODULE_NAME,
                        "scene_code": scene_code,
                        "scene_name": scene_name,
                        "name": formula["code"],
                        "expression": formula["expression"],
                        "canonical_expression": formula["expression"],
                        "variables": _extract_expression_variables(formula["expression"]),
                        "source_type": "default",
                        "formula_library_id": None,
                        "sort_order": index,
                        "unit_code": formula["unit"],
                    }
                    for index, formula in enumerate(formulas)
                ],
            }
        )
    return scenes


def serialize_workbench_formula(record):
    return {
        "id": getattr(record, "id", 0) or 0,
        "model_id": getattr(record, "version_id", 0) or 0,
        "module_code": getattr(record, "module_code", DEFAULT_MODULE_CODE) or DEFAULT_MODULE_CODE,
        "module_name": getattr(record, "module_name", DEFAULT_MODULE_NAME) or DEFAULT_MODULE_NAME,
        "scene_code": getattr(record, "scene_code", "") or "",
        "scene_name": getattr(record, "scene_name", "") or "",
        "name": getattr(record, "name", "") or "",
        "expression": getattr(record, "expression", "") or "",
        "canonical_expression": getattr(record, "canonical_expression", None),
        "variables": getattr(record, "variables", None) or _extract_expression_variables(getattr(record, "expression", "")),
        "description": getattr(record, "description", None),
        "resources": getattr(record, "resources", None) or [],
        "source_type": getattr(record, "source_type", "manual") or "manual",
        "formula_library_id": getattr(record, "formula_library_id", None),
        "sort_order": int(getattr(record, "sort_order", 0) or 0),
    }


def _group_scene_formulas(rows, model_id):
    grouped = {}
    for row in rows:
        scene_key = (
            str(row.get("module_code") or DEFAULT_MODULE_CODE),
            str(row.get("scene_code") or ""),
        )
        bucket = grouped.setdefault(
            scene_key,
            {
                "module_code": row.get("module_code", DEFAULT_MODULE_CODE) or DEFAULT_MODULE_CODE,
                "module_name": row.get("module_name", DEFAULT_MODULE_NAME) or DEFAULT_MODULE_NAME,
                "scene_code": row["scene_code"],
                "scene_name": row["scene_name"],
                "formulas": [],
            },
        )
        bucket["formulas"].append(
            {
                **row,
                "model_id": int(model_id or row.get("model_id") or 0),
            }
        )
    for bucket in grouped.values():
        bucket["formulas"].sort(
            key=lambda item: (
                int(item.get("sort_order", 0) or 0),
                int(item.get("id", 0) or 0),
            )
        )
    return list(grouped.values())


def _sanitize_label(value, fallback):
    return str(value or "").strip() or fallback


def _slugify_code(name: str, fallback: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", str(name or "").strip()).strip("_")
    return (normalized or fallback).lower()


def _ensure_module_record(
    db: Session,
    model_id: int,
    module_code: str,
    module_name: str,
    sort_order: int | None = None,
):
    record = (
        db.query(WorkbenchFormulaModule)
        .filter(
            WorkbenchFormulaModule.version_id == model_id,
            WorkbenchFormulaModule.module_code == module_code,
        )
        .first()
    )
    normalized_name = _sanitize_label(module_name, DEFAULT_MODULE_NAME)
    if record:
        changed = False
        if str(record.module_name or "").strip() != normalized_name:
            record.module_name = normalized_name
            changed = True
        if sort_order is not None and int(getattr(record, "sort_order", 0) or 0) != int(sort_order):
            record.sort_order = int(sort_order)
            changed = True
        return record, changed

    record = WorkbenchFormulaModule(
        version_id=model_id,
        module_code=module_code,
        module_name=normalized_name,
        sort_order=int(sort_order or 0),
    )
    db.add(record)
    db.flush()
    return record, True


def _ensure_scene_record(
    db: Session,
    model_id: int,
    module_code: str,
    scene_code: str,
    scene_name: str,
    sort_order: int | None = None,
):
    record = (
        db.query(WorkbenchFormulaScene)
        .filter(
            WorkbenchFormulaScene.version_id == model_id,
            WorkbenchFormulaScene.module_code == module_code,
            WorkbenchFormulaScene.scene_code == scene_code,
        )
        .first()
    )
    normalized_name = _sanitize_label(scene_name, "未命名场景")
    if record:
        changed = False
        if str(record.scene_name or "").strip() != normalized_name:
            record.scene_name = normalized_name
            changed = True
        if sort_order is not None and int(getattr(record, "sort_order", 0) or 0) != int(sort_order):
            record.sort_order = int(sort_order)
            changed = True
        return record, changed

    record = WorkbenchFormulaScene(
        version_id=model_id,
        module_code=module_code,
        scene_code=scene_code,
        scene_name=normalized_name,
        sort_order=int(sort_order or 0),
    )
    db.add(record)
    db.flush()
    return record, True


def _sync_module_name(db: Session, model_id: int, module_code: str, module_name: str):
    normalized_name = _sanitize_label(module_name, DEFAULT_MODULE_NAME)
    module_record, changed = _ensure_module_record(db, model_id, module_code, normalized_name)
    row_count = (
        db.query(WorkbenchFormula)
        .filter(
            WorkbenchFormula.version_id == model_id,
            WorkbenchFormula.module_code == module_code,
        )
        .update({"module_name": normalized_name}, synchronize_session=False)
    )
    return module_record, changed or bool(row_count)


def _sync_scene_name(db: Session, model_id: int, module_code: str, scene_code: str, scene_name: str):
    normalized_name = _sanitize_label(scene_name, "未命名场景")
    scene_record, changed = _ensure_scene_record(
        db,
        model_id,
        module_code,
        scene_code,
        normalized_name,
    )
    row_count = (
        db.query(WorkbenchFormula)
        .filter(
            WorkbenchFormula.version_id == model_id,
            WorkbenchFormula.module_code == module_code,
            WorkbenchFormula.scene_code == scene_code,
        )
        .update({"scene_name": normalized_name}, synchronize_session=False)
    )
    return scene_record, changed or bool(row_count)


def _next_module_sort_order(db: Session, model_id: int) -> int:
    rows = (
        db.query(WorkbenchFormulaModule)
        .filter(WorkbenchFormulaModule.version_id == model_id)
        .all()
    )
    if not rows:
        return 0
    return max(int(getattr(row, "sort_order", 0) or 0) for row in rows) + 1


def _next_module_scene_sort_order(db: Session, model_id: int, module_code: str) -> int:
    rows = (
        db.query(WorkbenchFormulaScene)
        .filter(
            WorkbenchFormulaScene.version_id == model_id,
            WorkbenchFormulaScene.module_code == module_code,
        )
        .all()
    )
    if not rows:
        return 0
    return max(int(getattr(row, "sort_order", 0) or 0) for row in rows) + 1


def _next_formula_sort_order(db: Session, model_id: int, module_code: str, scene_code: str) -> int:
    rows = (
        db.query(WorkbenchFormula)
        .filter(
            WorkbenchFormula.version_id == model_id,
            WorkbenchFormula.module_code == module_code,
            WorkbenchFormula.scene_code == scene_code,
        )
        .all()
    )
    if not rows:
        return 0
    return max(int(getattr(row, "sort_order", 0) or 0) for row in rows) + 1


def _build_formula_module_payload(db: Session, model_id: int):
    module_records = (
        db.query(WorkbenchFormulaModule)
        .filter(WorkbenchFormulaModule.version_id == model_id)
        .order_by(WorkbenchFormulaModule.sort_order.asc(), WorkbenchFormulaModule.id.asc())
        .all()
    )
    scene_records = (
        db.query(WorkbenchFormulaScene)
        .filter(WorkbenchFormulaScene.version_id == model_id)
        .order_by(
            WorkbenchFormulaScene.module_code.asc(),
            WorkbenchFormulaScene.sort_order.asc(),
            WorkbenchFormulaScene.id.asc(),
        )
        .all()
    )
    formula_records = (
        db.query(WorkbenchFormula)
        .filter(WorkbenchFormula.version_id == model_id)
        .order_by(
            WorkbenchFormula.module_code.asc(),
            WorkbenchFormula.scene_code.asc(),
            WorkbenchFormula.sort_order.asc(),
            WorkbenchFormula.id.asc(),
        )
        .all()
    )

    sync_links = (
        db.query(WorkbenchFormulaModuleSyncLink)
        .filter(WorkbenchFormulaModuleSyncLink.target_version_id == model_id)
        .all()
    )
    sync_link_map = {link.target_module_code: link for link in sync_links}
    
    # We also need source version info to display
    source_version_ids = {link.source_version_id for link in sync_links}
    source_versions = {}
    if source_version_ids:
        source_versions = {
            v.id: v for v in db.query(ModelVersion).filter(ModelVersion.id.in_(source_version_ids)).all()
        }

    module_map = {}
    modules = []
    for module_record in module_records:
        sync_link = sync_link_map.get(module_record.module_code)
        sync_info = None
        if sync_link:
            source_version = source_versions.get(sync_link.source_version_id)
            sync_info = {
                "source_version_id": sync_link.source_version_id,
                "source_version_name": source_version.display_name if source_version else str(sync_link.source_version_id),
                "source_module_code": sync_link.source_module_code,
                "sync_status": sync_link.sync_status,
                "last_synced_at": sync_link.last_synced_at.isoformat() if sync_link.last_synced_at else None
            }
            
        module_payload = {
            "module_code": module_record.module_code,
            "module_name": module_record.module_name,
            "scenes": [],
            "sync_info": sync_info
        }
        module_map[module_record.module_code] = module_payload
        modules.append(module_payload)

    scene_map = {}
    for scene_record in scene_records:
        module_payload = module_map.get(scene_record.module_code)
        if module_payload is None:
            module_payload = {
                "module_code": scene_record.module_code,
                "module_name": DEFAULT_MODULE_NAME,
                "scenes": [],
            }
            module_map[scene_record.module_code] = module_payload
            modules.append(module_payload)
        scene_payload = {
            "module_code": scene_record.module_code,
            "module_name": module_payload["module_name"],
            "scene_code": scene_record.scene_code,
            "scene_name": scene_record.scene_name,
            "formulas": [],
        }
        scene_map[(scene_record.module_code, scene_record.scene_code)] = scene_payload
        module_payload["scenes"].append(scene_payload)

    for row in formula_records:
        serialized = serialize_workbench_formula(row)
        module_payload = module_map.get(serialized["module_code"])
        if module_payload is None:
            module_payload = {
                "module_code": serialized["module_code"],
                "module_name": serialized["module_name"],
                "scenes": [],
            }
            module_map[serialized["module_code"]] = module_payload
            modules.append(module_payload)
        scene_key = (serialized["module_code"], serialized["scene_code"])
        scene_payload = scene_map.get(scene_key)
        if scene_payload is None:
            scene_payload = {
                "module_code": serialized["module_code"],
                "module_name": serialized["module_name"],
                "scene_code": serialized["scene_code"],
                "scene_name": serialized["scene_name"],
                "formulas": [],
            }
            scene_map[scene_key] = scene_payload
            module_payload["scenes"].append(scene_payload)
        scene_payload["formulas"].append(serialized)

    for module_payload in modules:
        for scene_payload in module_payload["scenes"]:
            scene_payload["module_name"] = module_payload["module_name"]
            scene_payload["formulas"].sort(
                key=lambda item: (
                    int(item.get("sort_order", 0) or 0),
                    int(item.get("id", 0) or 0),
                )
            )

    flattened_rows = []
    for module_payload in modules:
        for scene_payload in module_payload["scenes"]:
            flattened_rows.extend(scene_payload["formulas"])
    return {"modules": modules, "rows": flattened_rows}


def _filter_formula_module_payload_for_model(db: Session, model_id: int, payload):
    tree_type_id = _resolve_tree_type_id_for_version(db, model_id)
    modules = []
    visible_module_codes = set()
    for module in payload.get("modules", []):
        module_code = str(module.get("module_code") or "").strip()
        module_name = str(module.get("module_name") or "").strip()
        if not _is_module_visible_for_tree_type(tree_type_id, module_code, module_name):
            continue
        visible_module_codes.add(module_code)
        modules.append(module)

    rows = [
        row
        for row in payload.get("rows", [])
        if str(row.get("module_code") or "").strip() in visible_module_codes
    ]
    return {"modules": modules, "rows": rows}


def _ensure_model_default_formulas(db: Session, model_id: int):
    _ensure_model_version(db, model_id)
    changed = False

    # 默认公式种子已清空（功率计算改由公式模板维护），无需再为型号创建空模块骨架，
    # 避免旧版接口每次访问都自动重建一个无场景无公式的 power_calc 残留模块。
    if not SCENE_DEFINITIONS:
        return

    default_module_record, module_created = _ensure_module_record(
        db,
        model_id,
        DEFAULT_MODULE_CODE,
        DEFAULT_MODULE_NAME,
        sort_order=0,
    )
    changed = changed or module_created

    existing_rows = (
        db.query(WorkbenchFormula)
        .filter(WorkbenchFormula.version_id == model_id)
        .all()
    )
    existing_scene_records = {
        (str(record.module_code or "").strip(), str(record.scene_code or "").strip()): record
        for record in db.query(WorkbenchFormulaScene)
        .filter(WorkbenchFormulaScene.version_id == model_id)
        .all()
    }
    existing_keys = {}
    legacy_keys = {}
    should_seed_default_formulas = not existing_rows and not existing_scene_records
    for row in existing_rows:
        module_code = _sanitize_label(getattr(row, "module_code", ""), DEFAULT_MODULE_CODE)
        module_name = _sanitize_label(getattr(row, "module_name", ""), DEFAULT_MODULE_NAME)
        scene_code = str(getattr(row, "scene_code", "") or "").strip()
        scene_name = _sanitize_label(getattr(row, "scene_name", ""), "未命名场景")
        formula_name = str(getattr(row, "name", "") or "").strip()

        if row.module_code != module_code:
            row.module_code = module_code
            changed = True
        if row.module_name != module_name:
            row.module_name = module_name
            changed = True
        if row.scene_name != scene_name:
            row.scene_name = scene_name
            changed = True

        if module_code and scene_code:
            _, module_changed = _ensure_module_record(db, model_id, module_code, module_name)
            _, scene_changed = _ensure_scene_record(db, model_id, module_code, scene_code, scene_name)
            changed = changed or module_changed or scene_changed
        if module_code and scene_code and formula_name:
            existing_keys[(module_code, scene_code, formula_name)] = row
            legacy_keys[(scene_code, formula_name)] = row

    for scene_index, scene in enumerate(build_default_scene_formulas(model_id)):
        scene_key = (DEFAULT_MODULE_CODE, scene["scene_code"])
        existing_scene_record = existing_scene_records.get(scene_key)
        resolved_scene_name = (
            str(existing_scene_record.scene_name or "").strip()
            if existing_scene_record and str(existing_scene_record.scene_name or "").strip()
            else scene["scene_name"]
        )
        _, scene_created = _ensure_scene_record(
            db,
            model_id,
            DEFAULT_MODULE_CODE,
            scene["scene_code"],
            resolved_scene_name,
            sort_order=scene_index,
        )
        changed = changed or scene_created
        for formula in scene.get("formulas", []):
            # 只在“全新空模型”时初始化默认公式。
            # 一旦模型里已经存在用户公式，就不再做“局部补默认公式”，避免把历史默认公式混回当前工作台。
            if not should_seed_default_formulas:
                continue
            key = (
                str(formula.get("module_code") or DEFAULT_MODULE_CODE).strip() or DEFAULT_MODULE_CODE,
                str(formula.get("scene_code") or "").strip(),
                str(formula.get("name") or "").strip(),
            )
            if not key[1] or not key[2]:
                continue
            existing_row = existing_keys.get(key) or legacy_keys.get((key[1], key[2]))
            if existing_row:
                if str(existing_row.module_code or "").strip() != key[0]:
                    existing_row.module_code = key[0]
                    changed = True
                if str(existing_row.module_name or "").strip() != DEFAULT_MODULE_NAME:
                    existing_row.module_name = DEFAULT_MODULE_NAME
                    changed = True
                continue
            row = WorkbenchFormula(
                version_id=model_id,
                module_code=key[0],
                module_name=DEFAULT_MODULE_NAME,
                scene_code=key[1],
                scene_name=resolved_scene_name,
                name=key[2],
                expression=str(formula.get("expression") or "").strip(),
                canonical_expression=str(formula.get("canonical_expression") or "").strip() or None,
                variables=dict(formula.get("variables") or {}),
                source_type=str(formula.get("source_type") or "default").strip() or "default",
                formula_library_id=formula.get("formula_library_id"),
                sort_order=int(formula.get("sort_order", 0) or 0),
            )
            db.add(row)
            changed = True

    if changed:
        db.commit()
        db.refresh(default_module_record)


def list_model_formula_modules(db: Session, model_id: int):
    _ensure_model_default_formulas(db, model_id)
    payload = _build_formula_module_payload(db, model_id)
    return _filter_formula_module_payload_for_model(db, model_id, payload)


def _describe_module_entry(module_code: str, module_name: str) -> str:
    normalized_code = str(module_code or "").strip().lower()
    normalized_name = str(module_name or "").strip()
    if "power" in normalized_code or "功率" in normalized_name:
        return "用于功率、扭矩、转速等主驱动侧计算。"
    if (
        "structure" in normalized_code
        or "结构" in normalized_name
        or "shell" in normalized_code
        or "barrel" in normalized_code
        or "tube" in normalized_code
        or "筒体" in normalized_name
    ):
        return "用于结构强度、载荷和关键部件校核。"
    if (
        "leg" in normalized_code
        or "support" in normalized_code
        or "bearing" in normalized_code
        or "thrust" in normalized_code
        or "roller" in normalized_code
        or "支腿" in normalized_name
    ):
        return "用于支腿承载、挡轮和关键受力校核。"
    return "用于当前产品类型下的专属计算链路。"


def list_type_module_entries(db: Session, type_id: int, version_id: Optional[int] = None):
    tree_payload = build_drum_tree(db)
    type_node = next((item for item in tree_payload if int(item.get("id", 0) or 0) == int(type_id)), None)
    version_ids = [
        int(version.get("id"))
        for family in (type_node or {}).get("families", [])
        for version in family.get("versions", [])
        if version.get("id") is not None
    ]
    if not version_ids:
        return {"type_id": type_id, "modules": []}

    selected_version_id = None
    if version_id and int(version_id) in version_ids:
        selected_version_id = int(version_id)
    else:
        selected_version_id = version_ids[0]

    # 模块入口按“产品大类”归并匹配公式模板：
    # 模板挂在 product_type 上，大类由多个 product_type 归并而成。
    # 收集大类下所有 product_type_id，匹配所有活跃模板，从模板表生成模块入口。
    family_rows = (
        db.query(ModelFamily)
        .filter(ModelFamily.id.in_([int(family.get("id") or 0) for family in (type_node or {}).get("families", [])]))
        .all()
    )
    family_product_type_ids = {
        int(family.product_type_id)
        for family in family_rows
        if int(family.product_type_id or 0) > 0
    }
    template_rows = (
        db.query(FormulaTemplate)
        .filter(
            FormulaTemplate.is_active == True,
            FormulaTemplate.product_type_id.in_(family_product_type_ids) if family_product_type_ids else True,
        )
        .all()
    )
    # 模板可能只挂在同大类某个 product_type 上（如自动创建时挂在首个家族），
    # 因此再按大类名归并补充同大类其它 product_type 上的活跃模板。
    if family_product_type_ids:
        try:
            from app.routers.workbench import _resolve_template_for_product_type
        except ImportError:
            _resolve_template_for_product_type = None
        if _resolve_template_for_product_type is not None:
            for product_type_id in family_product_type_ids:
                sibling = _resolve_template_for_product_type(db, product_type_id)
                if sibling is not None and all(
                    int(row.id) != int(sibling.id) for row in template_rows
                ):
                    template_rows.append(sibling)

    module_entry_map = {}
    for template in template_rows:
        template_modules = (
            db.query(FormulaTemplateModule)
            .filter(FormulaTemplateModule.template_id == template.id)
            .order_by(FormulaTemplateModule.sort_order.asc(), FormulaTemplateModule.id.asc())
            .all()
        )
        for mod in template_modules:
            module_code = _sanitize_label(mod.module_code, DEFAULT_MODULE_CODE)
            module_name = _sanitize_label(mod.module_name, DEFAULT_MODULE_NAME)
            if module_code not in module_entry_map:
                module_entry_map[module_code] = {
                    "module_code": module_code,
                    "module_name": module_name,
                    "module_id": mod.id,
                }

    modules = []
    for module_code, entry in module_entry_map.items():
        if not _is_module_visible_for_tree_type(type_id, module_code, entry["module_name"]):
            continue
        # 从模板表统计场景与公式数量，供入口卡片展示
        scene_count = (
            db.query(FormulaTemplateScene)
            .filter(FormulaTemplateScene.module_id == entry["module_id"])
            .count()
        )
        formula_count = (
            db.query(FormulaTemplateItem)
            .join(FormulaTemplateScene, FormulaTemplateScene.id == FormulaTemplateItem.scene_id)
            .filter(FormulaTemplateScene.module_id == entry["module_id"])
            .count()
        )
        modules.append(
            {
                "module_code": module_code,
                "module_name": entry["module_name"],
                "description": _describe_module_entry(module_code, entry["module_name"]),
                "scene_count": scene_count,
                "formula_count": formula_count,
                "source_type_id": int(type_id),
            }
        )

    modules.sort(key=lambda item: item["module_code"])
    return {"type_id": int(type_id), "modules": modules}


def list_model_formulas(db: Session, model_id: int):
    return list_model_formula_modules(db, model_id)


def build_template_scene_formulas(db: Session, model_id: int):
    """将型号挂载的公式模板（FormulaTemplate* 表）转换为扫描引擎可用的场景公式结构。

    新工作台的公式统一从公式模板中心（FormulaTemplate 系列表）维护，
    型号上可能没有任何 WorkbenchFormula 自定义公式记录。此时影响参数区间反推
    （verification-scan）需要基于模板公式执行，才能算出通过/失败区间，
    否则 execute_design_scenes 无公式可算，扫描结果恒为空。
    """
    config = (
        db.query(ModelWorkbenchConfig)
        .filter(ModelWorkbenchConfig.model_version_id == int(model_id or 0))
        .first()
    )
    if not config or not config.formula_template_id:
        return []

    template = (
        db.query(FormulaTemplate)
        .filter(FormulaTemplate.id == int(config.formula_template_id))
        .first()
    )
    if not template:
        return []

    modules = (
        db.query(FormulaTemplateModule)
        .filter(FormulaTemplateModule.template_id == template.id)
        .order_by(FormulaTemplateModule.sort_order.asc(), FormulaTemplateModule.id.asc())
        .all()
    )

    scenes = []
    for module in modules:
        module_code = _sanitize_label(module.module_code, DEFAULT_MODULE_CODE)
        module_name = _sanitize_label(module.module_name, DEFAULT_MODULE_NAME)
        scene_rows = (
            db.query(FormulaTemplateScene)
            .filter(FormulaTemplateScene.module_id == module.id)
            .order_by(FormulaTemplateScene.sort_order.asc(), FormulaTemplateScene.id.asc())
            .all()
        )
        for scene in scene_rows:
            items = (
                db.query(FormulaTemplateItem)
                .filter(FormulaTemplateItem.scene_id == scene.id)
                .order_by(FormulaTemplateItem.sort_order.asc(), FormulaTemplateItem.id.asc())
                .all()
            )
            formulas = []
            for item in items:
                formula_name = str(item.formula_name or "").strip()
                if not formula_name:
                    continue
                unit = str(item.unit or "").strip()
                formulas.append(
                    {
                        "id": item.id,
                        "model_id": int(model_id or 0),
                        "module_code": module_code,
                        "module_name": module_name,
                        "scene_code": str(scene.scene_code or "").strip(),
                        "scene_name": str(scene.scene_name or "").strip(),
                        "name": formula_name,
                        "expression": str(item.expression or "").strip(),
                        "variables": dict(item.variables or {}),
                        "resources": list(item.resources or []),
                        "unit": unit,
                        "unit_code": unit,
                        "sort_order": int(item.sort_order or 0),
                        "output_flag": str(item.output_flag or "auto") or "auto",
                    }
                )
            scenes.append(
                {
                    "module_code": module_code,
                    "module_name": module_name,
                    "scene_code": str(scene.scene_code or "").strip(),
                    "scene_name": str(scene.scene_name or "").strip(),
                    "model_id": int(model_id or 0),
                    "formulas": formulas,
                }
            )

    return scenes


def load_model_scene_formulas(db: Session, model_id: int):
    modules_payload = list_model_formula_modules(db, model_id)["modules"]
    scenes = []
    for module_payload in modules_payload:
        scenes.extend(module_payload.get("scenes", []))

    if scenes:
        return scenes
    # 型号未配置自定义公式时，回退到挂载的公式模板（FormulaTemplate* 表），
    # 保证影响参数区间反推（verification-scan）能拿到与工作台执行一致的公式链路。
    template_scenes = build_template_scene_formulas(db, model_id)
    if template_scenes:
        return template_scenes
    if not _is_module_visible_for_tree_type(
        _resolve_tree_type_id_for_version(db, model_id),
        DEFAULT_MODULE_CODE,
        DEFAULT_MODULE_NAME,
    ):
        return []
    return build_default_scene_formulas(model_id)


def _ensure_model_version(db: Session, model_id: int):
    version = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if version:
        return version
    raise DrumDesignError("未找到正式型号，禁止自动创建 WB-AUTO 占位型号")


def upsert_model_formula(db: Session, payload):
    _ensure_model_version(db, payload.model_id)
    module_code = _sanitize_label(getattr(payload, "module_code", ""), DEFAULT_MODULE_CODE)
    module_name = _sanitize_label(getattr(payload, "module_name", ""), DEFAULT_MODULE_NAME)
    _assert_module_allowed_for_model(db, payload.model_id, module_code, module_name)
    scene_code = str(payload.scene_code or "").strip()
    scene_name = _sanitize_label(payload.scene_name, "未命名场景")
    formula_name = str(payload.name or "").strip()
    if not scene_code:
        raise DrumDesignError("scene_code 不能为空")
    if not formula_name:
        raise DrumDesignError("name 不能为空")

    expression = str(payload.expression or "").strip()
    extracted_variables = _extract_expression_variables(expression)
    payload_variables = dict(payload.variables or {})
    variables = {
        **extracted_variables,
        **payload_variables,
    }
    validation_scope = {name: 1 for name in variables.keys()}
    try:
        evaluate_formula_expression(
            expression,
            validation_scope,
            available_variable_names=variables.keys(),
            lookup_resolver=lambda lookup_name, lookup_key, col_index, exact: 1.0,
            curve_resolver=lambda lookup_name, input_value, series_key, direction, lookup_mode: {"value": 1.0},
            default_missing_value=1.0,
        )
    except FormulaEngineError as exc:
        raise DrumDesignError(str(exc)) from exc

    _sync_module_name(db, payload.model_id, module_code, module_name)
    _sync_scene_name(db, payload.model_id, module_code, scene_code, scene_name)

    row = None
    if hasattr(payload, "id") and payload.id and payload.id > 0:
        row = db.query(WorkbenchFormula).filter(
            WorkbenchFormula.id == payload.id,
            WorkbenchFormula.version_id == payload.model_id,
        ).first()

    if not row:
        row = (
            db.query(WorkbenchFormula)
            .filter(
                WorkbenchFormula.version_id == payload.model_id,
                WorkbenchFormula.module_code == module_code,
                WorkbenchFormula.scene_code == scene_code,
                WorkbenchFormula.name == formula_name,
            )
            .first()
        )

    is_new_row = not row
    if not row:
        row = WorkbenchFormula(version_id=payload.model_id)
        db.add(row)

    row.module_code = module_code
    row.module_name = module_name
    row.scene_code = scene_code
    row.scene_name = scene_name
    row.name = formula_name
    row.expression = expression
    row.canonical_expression = (
        str(payload.canonical_expression).strip() if payload.canonical_expression else None
    )
    row.variables = variables
    row.description = str(payload.description).strip() if payload.description else None
    row.resources = payload.resources if payload.resources is not None else []
    row.source_type = str(payload.source_type or "manual").strip() or "manual"
    row.formula_library_id = payload.formula_library_id
    if is_new_row:
        row.sort_order = _next_formula_sort_order(db, payload.model_id, row.module_code, row.scene_code)
    elif payload.sort_order is not None:
        row.sort_order = int(payload.sort_order)
    db.commit()
    db.refresh(row)
    return serialize_workbench_formula(row)


def delete_model_formulas_batch(db: Session, model_id: int, formula_ids):
    normalized_ids = []
    for item in formula_ids or []:
        try:
            normalized_id = int(item)
        except (TypeError, ValueError):
            continue
        if normalized_id > 0:
            normalized_ids.append(normalized_id)
    if not normalized_ids:
        raise DrumDesignError("formula_ids 不能为空")

    records = (
        db.query(WorkbenchFormula)
        .filter(WorkbenchFormula.id.in_(normalized_ids))
        .all()
    )
    if len(records) != len(normalized_ids):
        raise DrumDesignError("存在无效公式，无法批量删除")

    model_ids = {int(getattr(record, "version_id", 0) or 0) for record in records}
    if model_ids != {int(model_id)}:
        raise DrumDesignError("存在不属于当前型号的公式")

    deleted_id_set = {int(getattr(record, "id", 0) or 0) for record in records}
    deleted_ids = [item for item in normalized_ids if item in deleted_id_set]
    db.query(WorkbenchFormula).filter(
        WorkbenchFormula.version_id == model_id,
        WorkbenchFormula.id.in_(deleted_ids),
    ).delete(synchronize_session=False)
    db.commit()
    return {
        "success": True,
        "deleted_count": len(deleted_ids),
        "deleted_ids": deleted_ids,
    }


def delete_model_formula(db: Session, model_id: int, formula_id: int):
    record = (
        db.query(WorkbenchFormula)
        .filter(
            WorkbenchFormula.version_id == model_id,
            WorkbenchFormula.id == int(formula_id or 0),
        )
        .first()
    )
    if not record:
        raise DrumDesignError("目标公式不存在")

    deleted_formula_id = int(getattr(record, "id", 0) or 0)
    db.delete(record)
    db.commit()
    return {
        "success": True,
        "deleted_formula_id": deleted_formula_id,
    }


def reorder_model_formulas(db: Session, model_id: int, rows):
    if not rows:
        raise DrumDesignError("未提供需要排序的公式")

    target_ids = [int(item.id) for item in rows]
    records = (
        db.query(WorkbenchFormula)
        .filter(
            WorkbenchFormula.version_id == model_id,
            WorkbenchFormula.id.in_(target_ids),
        )
        .all()
    )
    if len(records) != len(target_ids):
        raise DrumDesignError("存在无效公式，无法排序")

    module_codes = {str(record.module_code or "").strip() for record in records}
    scene_codes = {str(record.scene_code or "").strip() for record in records}
    if len(module_codes) != 1 or len(scene_codes) != 1:
        raise DrumDesignError("仅支持同一模块同一场景内调整顺序")

    order_map = {int(item.id): int(item.sort_order) for item in rows}
    for record in records:
        record.sort_order = order_map[record.id]

    db.commit()

    module_code = next(iter(module_codes))
    scene_code = next(iter(scene_codes))
    updated_rows = (
        db.query(WorkbenchFormula)
        .filter(
            WorkbenchFormula.version_id == model_id,
            WorkbenchFormula.module_code == module_code,
            WorkbenchFormula.scene_code == scene_code,
        )
        .order_by(WorkbenchFormula.sort_order.asc(), WorkbenchFormula.id.asc())
        .all()
    )
    return {"rows": [serialize_workbench_formula(row) for row in updated_rows]}


def _resolve_template_for_model(db: Session, model_id: int):
    """根据型号解析其所属产品大类挂载的公式模板（无则返回 None）。"""
    try:
        from app.routers.workbench import _resolve_template_for_product_type
    except ImportError:
        _resolve_template_for_product_type = None

    version_record = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not version_record or not version_record.family_id:
        return None
    family_record = db.query(ModelFamily).filter(ModelFamily.id == version_record.family_id).first()
    if not family_record or not int(family_record.product_type_id or 0):
        return None
    if _resolve_template_for_product_type is not None:
        return _resolve_template_for_product_type(db, family_record.product_type_id)
    return (
        db.query(FormulaTemplate)
        .filter(
            FormulaTemplate.product_type_id == family_record.product_type_id,
            FormulaTemplate.is_active == True,
        )
        .first()
    )


def _ensure_template_for_model(db: Session, model_id: int):
    """确保型号所属产品大类挂载公式模板；没有时自动创建并挂载，保证所有大类都能建模块。"""
    template = _resolve_template_for_model(db, model_id)
    if template is not None:
        return template

    version_record = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not version_record or not version_record.family_id:
        raise DrumDesignError("型号不存在或未挂接家族，无法创建计算模块")
    family_record = db.query(ModelFamily).filter(ModelFamily.id == version_record.family_id).first()
    product_type_id = int(family_record.product_type_id or 0) if family_record else 0
    if not product_type_id:
        raise DrumDesignError("当前型号未挂接产品大类，无法创建计算模块")

    product_type = db.query(ProductType).filter(ProductType.id == product_type_id).first()
    category = product_type.type_name or "计算"
    try:
        from app.services.drum_catalog import normalize_drum_type_name
        category = normalize_drum_type_name(category)
    except Exception:
        pass

    base_code = _slugify_code(f"TPL_{category}", "tpl") or "TPL_AUTO"
    template_code = base_code
    suffix = 1
    while (
        db.query(FormulaTemplate)
        .filter(FormulaTemplate.template_code == template_code)
        .first()
    ):
        suffix += 1
        template_code = f"{base_code}_{suffix}"

    template = FormulaTemplate(
        template_code=template_code,
        template_name=f"{category}通用模板",
        product_type_id=product_type_id,
        description="首次创建计算模块时自动生成",
        is_active=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def _next_template_module_sort_order(db: Session, template_id: int) -> int:
    last = (
        db.query(FormulaTemplateModule.sort_order)
        .filter(FormulaTemplateModule.template_id == template_id)
        .order_by(FormulaTemplateModule.sort_order.desc(), FormulaTemplateModule.id.desc())
        .first()
    )
    return int(last[0] or 0) + 1 if last else 0


def create_formula_module(db: Session, model_id: int, module_name: str, module_code: str = ""):
    """在型号所属产品大类挂载的模板上新建模块（模板对所有同大类型号共享）。

    产品大类未挂载模板时（如原生/干混滚筒），自动创建并挂载模板，保证所有大类都能新建模块。
    """
    template = _ensure_template_for_model(db, model_id)

    normalized_name = _sanitize_label(module_name, "新计算模块")
    base_code = _sanitize_label(module_code, "") or _slugify_code(normalized_name, "module")
    existing_codes = {
        str(record.module_code or "").strip()
        for record in db.query(FormulaTemplateModule)
        .filter(FormulaTemplateModule.template_id == template.id)
        .all()
    }
    module_code = base_code
    suffix = 1
    while module_code in existing_codes:
        module_code = f"{base_code}_{suffix}"
        suffix += 1

    module_record = FormulaTemplateModule(
        template_id=template.id,
        module_code=module_code,
        module_name=normalized_name,
        sort_order=_next_template_module_sort_order(db, template.id),
    )
    db.add(module_record)
    db.commit()
    return {"module_code": module_code, "module_name": normalized_name, "scenes": []}


def rename_formula_module(db: Session, model_id: int, module_code: str, module_name: str):
    template = _resolve_template_for_model(db, model_id)
    if template is None:
        raise DrumDesignError("当前产品大类未挂载公式模板")

    module_record = (
        db.query(FormulaTemplateModule)
        .filter(
            FormulaTemplateModule.template_id == template.id,
            FormulaTemplateModule.module_code == module_code,
        )
        .first()
    )
    if not module_record:
        raise DrumDesignError("模块不存在")

    normalized_name = _sanitize_label(module_name, module_record.module_name)
    module_record.module_name = normalized_name
    db.commit()

    payload = list_model_formula_modules(db, model_id)
    matched = next((item for item in payload["modules"] if item["module_code"] == module_code), None)
    if not matched:
        raise DrumDesignError("模块不存在")
    return matched


def create_formula_scene(db: Session, model_id: int, module_code: str, scene_name: str):
    module_record = (
        db.query(WorkbenchFormulaModule)
        .filter(
            WorkbenchFormulaModule.version_id == model_id,
            WorkbenchFormulaModule.module_code == module_code,
        )
        .first()
    )
    if not module_record:
        raise DrumDesignError("模块不存在")

    normalized_name = _sanitize_label(scene_name, "未命名场景")
    base_code = _slugify_code(normalized_name, "scene")
    existing_codes = {
        str(record.scene_code or "").strip()
        for record in db.query(WorkbenchFormulaScene)
        .filter(
            WorkbenchFormulaScene.version_id == model_id,
            WorkbenchFormulaScene.module_code == module_code,
        )
        .all()
    }
    scene_code = base_code
    suffix = 1
    while scene_code in existing_codes:
        scene_code = f"{base_code}_{suffix}"
        suffix += 1

    scene_record = WorkbenchFormulaScene(
        version_id=model_id,
        module_code=module_code,
        scene_code=scene_code,
        scene_name=normalized_name,
        sort_order=_next_module_scene_sort_order(db, model_id, module_code),
    )
    db.add(scene_record)
    db.commit()
    return {
        "module_code": module_code,
        "module_name": module_record.module_name,
        "scene_code": scene_code,
        "scene_name": normalized_name,
        "formulas": [],
    }


def rename_formula_scene(db: Session, model_id: int, module_code: str, scene_code: str, scene_name: str):
    scene_record = (
        db.query(WorkbenchFormulaScene)
        .filter(
            WorkbenchFormulaScene.version_id == model_id,
            WorkbenchFormulaScene.module_code == module_code,
            WorkbenchFormulaScene.scene_code == scene_code,
        )
        .first()
    )
    if not scene_record:
        raise DrumDesignError("场景不存在")

    _sync_scene_name(db, model_id, module_code, scene_code, scene_name)
    db.commit()

    payload = list_model_formula_modules(db, model_id)
    matched_module = next(
        (item for item in payload["modules"] if item["module_code"] == module_code),
        None,
    )
    if not matched_module:
        raise DrumDesignError("场景不存在")
    matched_scene = next(
        (item for item in matched_module["scenes"] if item["scene_code"] == scene_code),
        None,
    )
    if not matched_scene:
        raise DrumDesignError("场景不存在")
    return matched_scene


def delete_formula_module(db: Session, model_id: int, module_code: str):
    template = _resolve_template_for_model(db, model_id)
    if template is None:
        raise DrumDesignError("当前产品大类未挂载公式模板")

    module_record = (
        db.query(FormulaTemplateModule)
        .filter(
            FormulaTemplateModule.template_id == template.id,
            FormulaTemplateModule.module_code == module_code,
        )
        .first()
    )
    if not module_record:
        raise DrumDesignError("目标模块不存在")

    scene_ids = [
        row[0]
        for row in db.query(FormulaTemplateScene.id)
        .filter(FormulaTemplateScene.module_id == module_record.id)
        .all()
    ]
    deleted_formula_count = 0
    if scene_ids:
        deleted_formula_count = (
            db.query(FormulaTemplateItem)
            .filter(FormulaTemplateItem.scene_id.in_(scene_ids))
            .delete(synchronize_session=False)
        )
    deleted_scene_count = (
        db.query(FormulaTemplateScene)
        .filter(FormulaTemplateScene.module_id == module_record.id)
        .delete(synchronize_session=False)
    )
    db.delete(module_record)
    db.commit()

    return {
        "success": True,
        "deleted_module_code": module_code,
        "deleted_scene_count": int(deleted_scene_count or 0),
        "deleted_formula_count": int(deleted_formula_count or 0),
    }


def delete_formula_scene(db: Session, model_id: int, module_code: str, scene_code: str):
    scene_record = (
        db.query(WorkbenchFormulaScene)
        .filter(
            WorkbenchFormulaScene.version_id == model_id,
            WorkbenchFormulaScene.module_code == module_code,
            WorkbenchFormulaScene.scene_code == scene_code,
        )
        .first()
    )
    if not scene_record:
        raise DrumDesignError("目标场景不存在")

    deleted_formula_count = (
        db.query(WorkbenchFormula)
        .filter(
            WorkbenchFormula.version_id == model_id,
            WorkbenchFormula.module_code == module_code,
            WorkbenchFormula.scene_code == scene_code,
        )
        .count()
    )

    db.query(WorkbenchFormula).filter(
        WorkbenchFormula.version_id == model_id,
        WorkbenchFormula.module_code == module_code,
        WorkbenchFormula.scene_code == scene_code,
    ).delete(synchronize_session=False)
    db.delete(scene_record)
    db.commit()

    return {
        "success": True,
        "deleted_module_code": module_code,
        "deleted_scene_code": scene_code,
        "deleted_formula_count": int(deleted_formula_count or 0),
    }


def _get_formula_name(formula):
    return str(formula.get("name") or formula.get("code") or "").strip()


def _get_formula_dependencies(formula):
    expression_variables = _extract_expression_variables(formula.get("expression"))
    persisted_variables = formula.get("variables") or {}
    merged_variables = {
        **expression_variables,
        **persisted_variables,
    }
    return [
        str(name).strip()
        for name in merged_variables.keys()
        if str(name).strip() and str(name).strip().upper() not in FORMULA_FUNC_RESERVED_UPPER
    ]


def _build_formula_index(scene_formulas):
    formula_by_name = {}
    ordered_formulas = []
    for scene in scene_formulas or []:
        for formula in scene.get("formulas", []):
            formula_name = _get_formula_name(formula)
            if not formula_name:
                continue
            normalized_formula = {
                **formula,
                "scene_code": scene.get("scene_code", formula.get("scene_code", "")),
                "scene_name": scene.get("scene_name", formula.get("scene_name", "")),
            }
            formula_by_name[formula_name] = normalized_formula
            ordered_formulas.append(normalized_formula)

    return formula_by_name, ordered_formulas


def _build_formula_lookup_resolver(db: Session, lookup_hits):
    def _resolver(lookup_name, lookup_key, col_index, exact):
        try:
            resolved = resolve_lookup_result_value(
                db,
                lookup_name,
                lookup_key,
                index=col_index,
            )
        except ParameterLookupValidationError as exc:
            error_code = "LOOKUP_NOT_FOUND"
            if "第 2 列" in str(exc):
                error_code = "LOOKUP_COLUMN_INVALID"
            raise FormulaEngineError(error_code, str(exc)) from exc

        lookup_hits.append(
            {
                "lookup_name": resolved["lookup"].lookup_name,
                "lookup_key": str(lookup_key),
                "result_value": resolved["row"].result_value,
                "base_factor": "",
            }
        )
        return resolved["value"]

    return _resolver


def _build_formula_curve_resolver(db: Session, curve_hits):
    def _resolver(lookup_name, input_value, series_key, direction, lookup_mode):
        try:
            resolved = resolve_curve_result_value(
                db,
                lookup_name,
                input_value,
                series_key,
                direction=direction,
                lookup_mode=lookup_mode,
            )
        except ParameterLookupValidationError as exc:
            message = str(exc)
            error_code = "CURVE_PROFILE_MISSING"
            if "不存在" in message and "系列" in message:
                error_code = "CURVE_SERIES_NOT_FOUND"
            elif "不是单调曲线" in message:
                error_code = "CURVE_DIRECTION_INVALID"
            elif "超出曲线有效范围" in message:
                error_code = "CURVE_OUT_OF_RANGE"
            elif "尚未配置为曲线" in message:
                error_code = "CURVE_PROFILE_MISSING"
            raise FormulaEngineError(error_code, message) from exc

        detail = {
            **(resolved.get("detail") or {}),
            "input_value": format(float(input_value), "g"),
        }
        curve_hits.append(detail)
        return resolved["value"]

    return _resolver


def _resolve_formula_value(
    formula_name,
    formula_by_name,
    base_scope,
    resolved_scope,
    result_cache,
    resolving,
    db: Session = None,
    preserve_explicit_names=None,
    explicit_expanded=None,
):
    if preserve_explicit_names and explicit_expanded is not None:
        protected_aliases = set()
        for raw_name in preserve_explicit_names or []:
            for a in _iter_equivalent_symbolic_names(raw_name):
                protected_aliases.add(a)
        formula_aliases = set(_iter_equivalent_symbolic_names(formula_name)) or {formula_name}
        if formula_aliases & protected_aliases:
            override = next(
                (explicit_expanded.get(a) for a in formula_aliases if explicit_expanded.get(a) is not None),
                None,
            )
            if override is not None:
                try:
                    numeric_override = float(override)
                except (TypeError, ValueError):
                    numeric_override = None
                if numeric_override is not None:
                    resolved_scope[formula_name] = numeric_override
                    for alias_name in formula_aliases:
                        resolved_scope.setdefault(alias_name, numeric_override)
                    if abs(numeric_override - int(numeric_override)) < 1e-12:
                        formatted = str(int(numeric_override))
                    else:
                        formatted = format(numeric_override, "g")
                    cache_payload = {
                        "value": numeric_override,
                        "formatted_value": formatted,
                        "lookup_detail": None,
                    }
                    result_cache[formula_name] = cache_payload
                    return numeric_override

    if formula_name in resolved_scope:
        cached_value = resolved_scope[formula_name]
        if formula_name not in result_cache:
            try:
                numeric_val = float(cached_value)
                if abs(numeric_val - int(numeric_val)) < 1e-12:
                    formatted = str(int(numeric_val))
                else:
                    formatted = format(numeric_val, "g")
            except (TypeError, ValueError):
                numeric_val = cached_value
                formatted = str(cached_value or "")
            result_cache[formula_name] = {
                "value": numeric_val,
                "formatted_value": formatted,
                "lookup_detail": None,
            }
        return resolved_scope[formula_name]
    if formula_name in resolving:
        raise FormulaEngineError(
            "CIRCULAR_DEPENDENCY",
            f"公式存在循环依赖: {' -> '.join([*resolving, formula_name])}",
        )

    formula = formula_by_name.get(formula_name)
    if not formula:
        raise FormulaEngineError("VARIABLE_UNDEFINED", f"变量未定义: {formula_name}")

    resolving.append(formula_name)
    dependency_names = _get_formula_dependencies(formula)
    dependency_scope = _expand_symbolic_alias_values({**base_scope, **resolved_scope})
    for dependency_name in dependency_names:
        if dependency_name in dependency_scope:
            continue
        resolved_dependency_formula_name = _resolve_formula_reference_name(dependency_name, formula_by_name)
        if resolved_dependency_formula_name:
            dependency_scope[dependency_name] = _resolve_formula_value(
                resolved_dependency_formula_name,
                formula_by_name,
                base_scope,
                resolved_scope,
                result_cache,
                resolving,
                db=db,
                preserve_explicit_names=preserve_explicit_names,
                explicit_expanded=explicit_expanded,
            )

    lookup_hits = []
    curve_hits = []
    result = evaluate_formula_expression(
        formula.get("expression"),
        dependency_scope,
        available_variable_names=dependency_names,
        default_missing_value=1.0,
        lookup_resolver=_build_formula_lookup_resolver(db, lookup_hits) if db is not None else None,
        curve_resolver=_build_formula_curve_resolver(db, curve_hits) if db is not None else None,
    )

    result["lookup_detail"] = curve_hits[-1] if curve_hits else (lookup_hits[-1] if lookup_hits else None)
    resolved_scope[formula_name] = result["value"]
    for alias_name in _iter_equivalent_symbolic_names(formula_name):
        resolved_scope.setdefault(alias_name, result["value"])
    result_cache[formula_name] = result
    resolving.pop()
    return result["value"]


def _resolve_mapped_base_scope(db: Session, model_id: int, module_code: str, base_scope, required_names, explicit_scope=None):
    mappings = (
        db.query(WorkbenchFormulaParamMapping)
        .filter(
            WorkbenchFormulaParamMapping.target_version_id == model_id,
            WorkbenchFormulaParamMapping.module_code == module_code,
        )
        .all()
    )
    
    missing_mappings = []
    for mapping in mappings:
        if mapping.source_param_name in required_names and str(mapping.mapping_status or "") != "ready":
            missing_mappings.append(mapping.source_param_name)
            
    if missing_mappings:
        raise DrumDesignError(f"当前公式存在 {len(missing_mappings)} 项基础参数待补映射，暂无法完成计算。")

    mapped_scope = dict(base_scope or {})
    explicit_expanded = _expand_symbolic_alias_values(_normalize_numeric_scope(explicit_scope) if explicit_scope else {})
    explicit_protect_names = set(explicit_expanded.keys())

    for mapping in mappings:
        if str(mapping.mapping_status or "") != "ready" or not mapping.target_parameter_id:
            continue
        source_param_name = str(mapping.source_param_name or "").strip()
        source_equivalents = set(_iter_equivalent_symbolic_names(source_param_name))
        if source_param_name in mapped_scope:
            continue
        if source_equivalents & explicit_protect_names:
            for equiv_name in source_equivalents:
                if equiv_name in explicit_expanded and equiv_name not in mapped_scope:
                    mapped_scope[equiv_name] = explicit_expanded[equiv_name]
            continue
        target_value = (
            db.query(ModelParameterValue)
            .filter(
                ModelParameterValue.version_id == model_id,
                ModelParameterValue.parameter_id == mapping.target_parameter_id,
            )
            .first()
        )
        if target_value and str(target_value.param_value or "").strip():
            try:
                mapped_scope[source_param_name] = float(target_value.param_value)
            except ValueError:
                pass
    return mapped_scope

def execute_design_scenes(parameters, scene_formulas=None, db: Session = None, preserve_explicit_names=None):
    normalized_scenes = scene_formulas or build_default_scene_formulas()
    required_numeric_names = _collect_required_numeric_parameter_names(normalized_scenes, db)
    raw_numeric_scope = _normalize_numeric_scope(parameters)
    full_numeric_scope = _expand_symbolic_alias_values(raw_numeric_scope)
    base_scope = _normalize_numeric_scope(parameters, allowed_keys=required_numeric_names)
    base_scope = _apply_parameter_aliases(base_scope, full_numeric_scope)
    explicit_user_scope = _expand_symbolic_alias_values(raw_numeric_scope)

    # Resolve mapped parameters for each module
    if db and normalized_scenes:
        for scene in normalized_scenes:
            model_id = int(scene.get("model_id") or 0)
            module_code = str(scene.get("module_code") or DEFAULT_MODULE_CODE)
            if model_id > 0:
                mapped_scope = _resolve_mapped_base_scope(
                    db, model_id, module_code, base_scope, required_numeric_names,
                    explicit_scope=parameters,
                )
                base_scope.update(mapped_scope)

    for key, value in explicit_user_scope.items():
        if value is not None:
            base_scope[key] = value
                
    results = []
    warnings = []
    formula_by_name, ordered_formulas = _build_formula_index(normalized_scenes)
    resolved_scope = {}
    result_cache = {}
    results.extend(
        _build_lookup_results(
            db,
            base_scope,
            resolved_scope,
            explicit_scope=parameters,
            preserve_explicit_names=preserve_explicit_names,
        )
    )
    for formula in ordered_formulas:
        formula_name = _get_formula_name(formula)
        if not formula_name:
            continue
        try:
            _resolve_formula_value(
                formula_name,
                formula_by_name,
                base_scope,
                resolved_scope,
                result_cache,
                [],
                db=db,
                preserve_explicit_names=preserve_explicit_names,
                explicit_expanded=explicit_user_scope,
            )
            result = result_cache[formula_name]
            results.append(
                {
                    "scene_code": formula.get("scene_code", ""),
                    "scene_name": formula.get("scene_name", ""),
                    "result_code": formula_name,
                    "result_name": formula_name,
                    "result_value": result["formatted_value"],
                    "unit_code": formula.get("unit_code") or formula.get("unit"),
                    "source_formula": formula_name,
                    "lookup_detail": result.get("lookup_detail"),
                }
            )
        except FormulaEngineError as exc:
            warnings.append(f"公式 {formula_name} 计算失败: {exc}")
    return {"results": results, "scope": {**base_scope, **resolved_scope}, "warnings": warnings}


def analyze_single_parameter(payload, scene_formulas=None):
    target_parameter = str(payload.target_parameter or "").strip()
    if not target_parameter:
        raise DrumDesignError("target_parameter 不能为空")

    target_aliases = set(_iter_equivalent_symbolic_names(target_parameter)) or {target_parameter}
    normalized_input_scope = _expand_symbolic_alias_values(_normalize_numeric_scope(payload.parameters))
    base_scope_candidates = {
        key: value for key, value in normalized_input_scope.items()
        if key in target_aliases or (not target_aliases)
    }
    base_value = next((value for key, value in base_scope_candidates.items() if key in target_aliases), None)
    if base_value is None:
        fallback_scope = _normalize_numeric_scope(payload.parameters, allowed_keys={target_parameter})
        base_value = fallback_scope.get(target_parameter)
    if base_value is None:
        raise DrumDesignError(f"参数 {target_parameter} 不存在或未提供数值")

    result_name = str(payload.result_name or "推荐电机功率").strip()
    steps = max(int(payload.steps or 5), 3)
    delta_ratio = max(float(payload.delta_ratio or 0.2), 0.01)
    midpoint = steps // 2
    x_axis = []
    values = []
    reverse_index = _build_reverse_dependency_index(scene_formulas or [])
    impacted_names = _collect_impacted_formula_names(target_parameter, reverse_index)

    for index in range(steps):
        if steps == 1:
            ratio = 1.0
        else:
            spread = (index - midpoint) / max(midpoint, 1)
            ratio = 1 + spread * delta_ratio
        varied_value = base_value * ratio
        scenario_payload = _strip_impacted_formula_explicit_values(
            payload.parameters,
            impacted_names,
            preserve_names=target_aliases,
        )
        for alias_name in target_aliases:
            scenario_payload[alias_name] = varied_value
        execution = execute_design_scenes(
            scenario_payload,
            scene_formulas=scene_formulas,
            preserve_explicit_names=target_aliases,
        )
        result_map = {row["result_name"]: row["result_value"] for row in execution["results"]}
        x_axis.append(format(varied_value, "g"))
        values.append(str(result_map.get(result_name, "")))

    return {
        "target_parameter": target_parameter,
        "result_name": result_name,
        "x_axis": x_axis,
        "values": values,
    }


def analyze_impact_for_result(payload, scene_formulas=None):
    target_result_name = str(payload.target_result_name or "").strip()
    if not target_result_name:
        raise DrumDesignError("target_result_name 不能为空")

    # 1. Execute base design to get base values
    base_execution = execute_design_scenes(
        payload.parameters,
        scene_formulas=scene_formulas,
    )
    base_scope = base_execution.get("scope", {})
    
    if target_result_name not in base_scope:
        raise DrumDesignError(f"计算结果中未找到目标指标: {target_result_name}")
        
    base_result_value = base_scope[target_result_name]
    if base_result_value == 0:
        # If base result is 0, sensitivity calculation might divide by zero.
        # We can add a small epsilon or just handle it.
        pass

    # 2. Build dependency graph
    forward_index = _build_forward_dependency_index(scene_formulas)
    affecting_names = _collect_affecting_parameter_names(target_result_name, forward_index)
    
    # 3. Determine parameter types
    calculated_names = set(forward_index.keys())
    
    impacts = []
    reverse_index = _build_reverse_dependency_index(scene_formulas or [])
    
    for param_name in affecting_names:
        if param_name not in base_scope:
            continue
            
        param_value = base_scope[param_name]
        if param_value == 0:
            delta = 0.01 # small absolute change if 0
        else:
            delta = param_value * 0.01 # 1% change
            
        if delta == 0:
            continue
            
        # Perturb parameter
        varied_value = param_value + delta
        
        target_aliases = set(_iter_equivalent_symbolic_names(param_name)) or {param_name}
        impacted_names = _collect_impacted_formula_names(param_name, reverse_index)
        
        scenario_payload = _strip_impacted_formula_explicit_values(
            payload.parameters,
            impacted_names,
            preserve_names=target_aliases,
        )
        for alias_name in target_aliases:
            scenario_payload[alias_name] = varied_value
            
        # Execute with perturbed parameter
        execution = execute_design_scenes(
            scenario_payload,
            scene_formulas=scene_formulas,
            preserve_explicit_names=target_aliases,
        )
        
        varied_scope = execution.get("scope", {})
        varied_result_value = varied_scope.get(target_result_name, base_result_value)
        
        # Calculate sensitivity
        delta_result = varied_result_value - base_result_value
        
        if base_result_value != 0 and param_value != 0:
            sensitivity = (delta_result / base_result_value) / (delta / param_value)
        else:
            # Fallback if base is 0
            sensitivity = delta_result / delta if delta != 0 else 0
            
        if abs(sensitivity) < 1e-6:
            continue # No impact
            
        if sensitivity > 0:
            direction = "positive"
        else:
            direction = "negative"
            
        abs_sens = abs(sensitivity)
        if abs_sens >= 1.0:
            impact_level = "high"
        elif abs_sens >= 0.1:
            impact_level = "medium"
        else:
            impact_level = "low"
            
        param_type = "calculated" if param_name in calculated_names else "input"
        if param_name in PARAMETER_DEFAULT_VALUES and param_name not in payload.parameters:
            param_type = "constant"
            
        impacts.append({
            "parameter_name": param_name,
            "impact_level": impact_level,
            "direction": direction,
            "sensitivity": sensitivity,
            "parameter_type": param_type
        })
        
    # Sort by absolute sensitivity descending
    impacts.sort(key=lambda x: abs(x["sensitivity"]), reverse=True)
    
    return {
        "target_result_name": target_result_name,
        "impacts": impacts
    }


def _build_reverse_dependency_index(scene_formulas):
    reverse_index = {}
    for scene in scene_formulas or []:
        for formula in scene.get("formulas", []):
            name = _get_formula_name(formula)
            if not name:
                continue
            deps = _get_formula_dependencies(formula)
            for dep in deps:
                for dep_name in _iter_equivalent_symbolic_names(dep):
                    if dep_name not in reverse_index:
                        reverse_index[dep_name] = []
                    reverse_index[dep_name].append(name)
    return reverse_index


def _build_forward_dependency_index(scene_formulas):
    forward_index = {}
    for scene in scene_formulas or []:
        for formula in scene.get("formulas", []):
            name = _get_formula_name(formula)
            if not name:
                continue
            deps = _get_formula_dependencies(formula)
            forward_index[name] = list(deps)
    return forward_index


def _collect_affecting_parameter_names(target_result_name, forward_index):
    affecting = set()
    queue = [target_result_name]
    while queue:
        current = queue.pop(0)
        parents = forward_index.get(current, [])
        for parent in parents:
            if parent not in affecting:
                affecting.add(parent)
                queue.append(parent)
    return affecting


def _collect_impacted_formula_names(target_parameter, reverse_index):
    impacted = set()
    queue = [target_parameter]
    while queue:
        current = queue.pop(0)
        children = reverse_index.get(current, [])
        for child in children:
            if child not in impacted:
                impacted.add(child)
                queue.append(child)
    return impacted


def _strip_impacted_formula_explicit_values(parameters, impacted_names, preserve_names=None):
    next_parameters = dict(parameters or {})
    if not next_parameters or not impacted_names:
        return next_parameters
    preserved = {str(name or "").strip() for name in (preserve_names or []) if str(name or "").strip()}
    removable_names = set()
    for impacted_name in impacted_names:
        normalized_name = str(impacted_name or "").strip()
        if not normalized_name or normalized_name in preserved:
            continue
        removable_names.add(normalized_name)
        for alias_name in _iter_equivalent_symbolic_names(normalized_name):
            alias_key = str(alias_name or "").strip()
            if alias_key and alias_key not in preserved:
                removable_names.add(alias_key)
    for raw_key in list(next_parameters.keys()):
        normalized_key = str(raw_key or "").strip()
        if normalized_key in removable_names and normalized_key not in preserved:
            next_parameters.pop(raw_key, None)
    return next_parameters


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_scan_values(current_value, scan_start, scan_end, scan_step, steps):
    start = scan_start if scan_start is not None else current_value * 0.8
    end = scan_end if scan_end is not None else current_value * 1.2
    if scan_step and scan_step > 0:
        values = []
        cursor = start
        guard = 0
        while cursor <= end + (scan_step / 10) and guard < 1000:
            values.append(cursor)
            cursor += scan_step
            guard += 1
        return values
    normalized_steps = max(int(steps or 21), 3)
    if normalized_steps == 1:
        return [start]
    gap = (end - start) / (normalized_steps - 1)
    return [start + gap * index for index in range(normalized_steps)]


def _merge_scan_ranges(points):
    pass_ranges = []
    fail_ranges = []
    active = None
    for point in points:
        status = point["pass_status"]
        if status not in {"pass", "fail"}:
            active = None
            continue
        bucket = pass_ranges if status == "pass" else fail_ranges
        if active and active["status"] == status:
            active["end"] = point["parameter_value"]
            continue
        active = {
            "start": point["parameter_value"],
            "end": point["parameter_value"],
            "status": status,
        }
        bucket.append(active)
    return pass_ranges, fail_ranges


def _collect_verification_rules(scene_formulas):
    rules = {}
    for scene in scene_formulas or []:
        for formula in scene.get("formulas", []):
            name = _get_formula_name(formula)
            if not name:
                continue
            for resource in formula.get("resources", []) or []:
                rtype = resource.get("type")
                if rtype == "verification_rule":
                    rules[name] = resource
                    break
                # 关注指标配置（focus_metric_config）也作为校核规则参与扫描：
                # range 模式转 between，compare 模式转 targetParam + operator
                if rtype == "focus_metric_config":
                    if resource.get("mode") == "range":
                        rules[name] = {
                            "type": "verification_rule",
                            "operator": "between",
                            "rangeMin": resource.get("rangeMin"),
                            "rangeMax": resource.get("rangeMax"),
                        }
                    else:
                        rules[name] = {
                            "type": "verification_rule",
                            "targetParam": str(resource.get("targetParam") or "").strip(),
                            "operator": str(resource.get("operator") or ">=").strip() or ">=",
                            "tolerance": resource.get("tolerance"),
                        }
                    break
    return rules


def _collect_model_focus_metric_rules(db: Session, model_id: int):
    """从 model_focus_metric_configs 表合并型号级关注指标配置为扫描校核规则。

    关注指标配置（合理区间/对比参数规则）按型号独立存储在数据库中，
    并不一定写入公式的 resources 字段，因此扫描引擎需要额外合并这部分规则，
    否则会出现「结果 X 未配置校核规则」导致影响参数区间反推失败。
    """
    rules = {}
    rows = (
        db.query(ModelFocusMetricConfig)
        .filter(ModelFocusMetricConfig.version_id == model_id)
        .all()
    )
    for row in rows:
        metric_name = str(row.metric_name or "").strip()
        if not metric_name:
            continue
        config = dict(row.config or {})
        if not config:
            continue
        if config.get("mode") == "range":
            rules[metric_name] = {
                "type": "verification_rule",
                "operator": "between",
                "rangeMin": config.get("rangeMin"),
                "rangeMax": config.get("rangeMax"),
            }
        else:
            rules[metric_name] = {
                "type": "verification_rule",
                "targetParam": str(config.get("targetParam") or "").strip(),
                "operator": str(config.get("operator") or ">=").strip() or ">=",
                "tolerance": config.get("tolerance"),
            }
    return rules


def analyze_verification_scan(db: Session, payload):
    result_name = str(payload.result_name or "").strip()
    scan_parameter = str(payload.scan_parameter or "").strip()
    if not result_name:
        raise DrumDesignError("result_name 不能为空")
    if not scan_parameter:
        raise DrumDesignError("scan_parameter 不能为空")

    scan_aliases = set(_iter_equivalent_symbolic_names(scan_parameter)) or {scan_parameter}
    scope = _expand_symbolic_alias_values(_normalize_numeric_scope(payload.parameters))
    current_parameter_value = next((value for key, value in scope.items() if key in scan_aliases), None)
    if current_parameter_value is None:
        fallback_scope = _normalize_numeric_scope(payload.parameters)
        current_parameter_value = fallback_scope.get(scan_parameter)
    if current_parameter_value is None:
        raise DrumDesignError(f"参数 {scan_parameter} 不存在或未提供数值")

    scene_formulas = load_model_scene_formulas(db, payload.model_id)
    verification_rules = _collect_verification_rules(scene_formulas)
    # 合并型号级关注指标配置（model_focus_metric_configs 表），
    # 保证「合理区间 / 对比参数规则」在公式资源缺失时也能参与影响参数区间反推
    verification_rules.update(_collect_model_focus_metric_rules(db, payload.model_id))
    rule = verification_rules.get(result_name)
    if not rule:
        raise DrumDesignError(f"结果 {result_name} 未配置校核规则")
    reverse_index = _build_reverse_dependency_index(scene_formulas)
    impacted_names = _collect_impacted_formula_names(scan_parameter, reverse_index)

    points = []
    unit_code = ""
    min_margin = None
    worst_parameter_value = ""
    current_point = None
    scanned_values = set()

    # 自动扩大扫描窗口：默认围绕当前值 ±20%；若未覆盖到“符合规则”的区间，
    # 逐步外扩（最多 5 轮），直到找到通过/失败分界，保证能反推出符合规则的影响参数区间。
    rounds = 0
    span_ratio = 0.2
    max_rounds = 5
    explicit_bounds = payload.scan_start is not None or payload.scan_end is not None

    while True:
        rounds += 1
        if explicit_bounds:
            scan_values = _build_scan_values(
                current_parameter_value,
                payload.scan_start,
                payload.scan_end,
                payload.scan_step,
                payload.steps,
            )
        else:
            scan_start = current_parameter_value * (1 - span_ratio)
            scan_end = current_parameter_value * (1 + span_ratio)
            if scan_end < scan_start:
                scan_start, scan_end = scan_end, scan_start
            scan_values = _build_scan_values(
                current_parameter_value,
                scan_start,
                scan_end,
                payload.scan_step,
                payload.steps,
            )

        for value in scan_values:
            if value in scanned_values:
                continue
            scanned_values.add(value)
            scenario_payload = _strip_impacted_formula_explicit_values(
                payload.parameters,
                impacted_names,
                preserve_names=scan_aliases,
            )
            for alias_name in scan_aliases:
                scenario_payload[alias_name] = value
            execution = execute_design_scenes(
                scenario_payload,
                scene_formulas=scene_formulas,
                db=db,
                preserve_explicit_names=scan_aliases,
            )
            result_rows = execution.get("results", [])
            result_row = next((row for row in result_rows if row["result_name"] == result_name), None)
            if not result_row:
                continue

            actual_value = _safe_float(result_row.get("result_value"))
            target_name = str(rule.get("targetParam") or "").strip()
            theory_row = next((row for row in result_rows if row["result_name"] == target_name), None)
            theory_value = _safe_float(theory_row.get("result_value") if theory_row else execution.get("scope", {}).get(target_name))
            unit_code = result_row.get("unit_code") or unit_code or ""
            margin_value = None
            pass_status = "unknown"
            operator = str(rule.get("operator") or ">=").strip() or ">="
            if actual_value is not None:
                if operator == "between":
                    min_value = _safe_float(rule.get("rangeMin"))
                    max_value = _safe_float(rule.get("rangeMax"))
                    if min_value is not None or max_value is not None:
                        lower_ok = actual_value >= min_value if min_value is not None else True
                        upper_ok = actual_value <= max_value if max_value is not None else True
                        margin_value = min(
                            (actual_value - min_value) if min_value is not None else float("inf"),
                            (max_value - actual_value) if max_value is not None else float("inf"),
                        )
                        pass_status = "pass" if (lower_ok and upper_ok) else "fail"
                elif theory_value is not None:
                    if operator in {">", ">="}:
                        margin_value = actual_value - theory_value
                        pass_status = "pass" if (actual_value > theory_value if operator == ">" else actual_value >= theory_value) else "fail"
                    elif operator in {"<", "<="}:
                        margin_value = theory_value - actual_value
                        pass_status = "pass" if (actual_value < theory_value if operator == "<" else actual_value <= theory_value) else "fail"
                    elif operator == "==":
                        tolerance = float(rule.get("tolerance") or 0)
                        margin_value = tolerance - abs(actual_value - theory_value)
                        pass_status = "pass" if abs(actual_value - theory_value) <= tolerance else "fail"
            if margin_value is not None and (min_margin is None or margin_value < min_margin):
                min_margin = margin_value
                worst_parameter_value = format(value, "g")

            point = {
                "parameter_value": format(value, "g"),
                "actual_value": "" if actual_value is None else format(actual_value, "g"),
                "theory_value": "" if theory_value is None else format(theory_value, "g"),
                "margin_value": "" if margin_value is None else format(margin_value, "g"),
                "pass_status": pass_status,
            }
            points.append(point)
            if abs(value - current_parameter_value) < 1e-9:
                current_point = point

        # 判断是否需要继续扩大扫描窗口
        determined = [p for p in points if p["pass_status"] in {"pass", "fail"}]
        has_pass = any(p["pass_status"] == "pass" for p in determined)
        has_fail = any(p["pass_status"] == "fail" for p in determined)
        if explicit_bounds or rounds >= max_rounds:
            break
        if has_pass and has_fail:
            # 已找到通过/失败分界，无需继续外扩
            break
        span_ratio = min(span_ratio * 1.8, 20.0)

    scan_values = [float(p["parameter_value"]) for p in points]

    if not current_point and points:
        current_point = min(points, key=lambda item: abs(float(item["parameter_value"]) - current_parameter_value))

    pass_ranges, fail_ranges = _merge_scan_ranges(points)
    usable_ranges_text = "、".join([f"{row['start']} ~ {row['end']}" for row in pass_ranges])

    return {
        "result_name": result_name,
        "scan_parameter": scan_parameter,
        "unit_code": unit_code,
        "scan_start": format(scan_values[0], "g") if scan_values else "",
        "scan_end": format(scan_values[-1], "g") if scan_values else "",
        "scan_step": format(payload.scan_step, "g") if payload.scan_step else (format(scan_values[1] - scan_values[0], "g") if len(scan_values) > 1 else ""),
        "points": points,
        "pass_ranges": pass_ranges,
        "fail_ranges": fail_ranges,
        "summary": {
            "current_parameter_value": "" if current_point is None else current_point["parameter_value"],
            "current_actual_value": "" if current_point is None else current_point["actual_value"],
            "current_theory_value": "" if current_point is None else current_point["theory_value"],
            "current_margin_value": "" if current_point is None else current_point["margin_value"],
            "current_pass_status": "unknown" if current_point is None else current_point["pass_status"],
            "min_margin_value": "" if min_margin is None else format(min_margin, "g"),
            "worst_parameter_value": worst_parameter_value,
            "usable_ranges_text": usable_ranges_text,
        },
        "warnings": execution.get("warnings", []) if 'execution' in locals() else [],
    }


def build_case_compare_payload(mode, case_ids=None, family_id=None, cases=None):
    normalized_mode = str(mode or "same_model").strip() or "same_model"
    case_ids = [int(item) for item in (case_ids or []) if item]
    normalized_cases = list(cases or [])

    if not case_ids and not normalized_cases and not family_id:
        raise DrumDesignError("缺少对比对象")

    if normalized_cases:
        result_names = []
        seen_names = set()
        for case in normalized_cases:
            for row in case.results:
                if row.result_name in seen_names:
                    continue
                seen_names.add(row.result_name)
                result_names.append(row.result_name)

        rows = []
        for result_name in result_names:
            row_values = {}
            numeric_values = []
            for case in normalized_cases:
                matched = next((item for item in case.results if item.result_name == result_name), None)
                value = "" if matched is None else str(matched.result_value)
                row_values[case.case_name] = value
                try:
                    numeric_values.append(float(value))
                except (TypeError, ValueError):
                    continue
            delta = ""
            if len(numeric_values) >= 2:
                delta = format(max(numeric_values) - min(numeric_values), "g")
            rows.append({"result_name": result_name, "values": row_values, "delta": delta})
        return {"mode": normalized_mode, "rows": rows}

    return {"mode": normalized_mode, "rows": []}

def list_formula_sync_targets(db: Session, source_model_id: int, scope_type: str, version_ids=None):
    source_version = _ensure_model_version(db, source_model_id)
    base_query = db.query(ModelVersion).join(ModelFamily, ModelVersion.family_id == ModelFamily.id)
    rows = base_query.filter(ModelVersion.id != source_model_id, ModelVersion.status != "deleted").all()
    if scope_type == "same_family":
        rows = [row for row in rows if int(row.family_id or 0) == int(source_version.family_id or 0)]
    elif scope_type == "manual":
        allowed = {int(item) for item in version_ids or [] if int(item) != int(source_model_id)}
        rows = [row for row in rows if int(row.id) in allowed]
    return {
        "targets": [
            {
                "version_id": row.id,
                "version_code": row.version_code,
                "family_id": row.family_id,
                "family_code": row.family.family_code if row.family else None,
                "product_type_id": row.family.product_type_id if row.family else None,
                "product_type_name": row.family.product_type.type_name if row.family and row.family.product_type else None,
                "enabled": True,
            }
            for row in rows
        ]
    }

def _build_formula_module_sync_preview_target(db: Session, source_model_id: int, source_module: dict, target: dict):
    target_version_id = target["version_id"]
    target_payload = list_model_formula_modules(db, target_version_id)
    target_module = next((item for item in target_payload["modules"] if item["module_code"] == source_module["module_code"]), None)
    
    new_modules = []
    new_scenes = []
    new_formulas = []
    conflicts = []
    
    if not target_module:
        new_modules.append(source_module["module_name"])
        for scene in source_module.get("scenes", []):
            new_scenes.append(scene["scene_name"])
            for formula in scene.get("formulas", []):
                new_formulas.append(formula["name"])
    else:
        target_scene_codes = {scene["scene_code"]: scene for scene in target_module.get("scenes", [])}
        for scene in source_module.get("scenes", []):
            if scene["scene_code"] not in target_scene_codes:
                new_scenes.append(scene["scene_name"])
                for formula in scene.get("formulas", []):
                    new_formulas.append(formula["name"])
            else:
                target_scene = target_scene_codes[scene["scene_code"]]
                target_formula_names = {formula["name"]: formula for formula in target_scene.get("formulas", [])}
                for formula in scene.get("formulas", []):
                    if formula["name"] not in target_formula_names:
                        new_formulas.append(formula["name"])
                    else:
                        conflicts.append({
                            "scene_code": scene["scene_code"],
                            "formula_name": formula["name"],
                            "action": "overwrite"
                        })
                        
    source_params = set()
    for scene in source_module.get("scenes", []):
        for formula in scene.get("formulas", []):
            for param_name in formula.get("variables", {}):
                source_params.add(param_name)
                
    auto_mappings = []
    missing_mappings = []
    
    # Check if target model has these parameters
    # 首先获取所有的parameter_id
    param_value_ids = db.query(ModelParameterValue.parameter_id).filter(
        ModelParameterValue.version_id == target_version_id
    ).all()
    
    # 提取ID列表
    param_ids = [pv[0] for pv in param_value_ids]
    
    # 查询对应的参数定义
    target_param_dict = {}
    candidate_parameters = []
    
    if param_ids:
        params = db.query(ParameterDefinition).filter(
            ParameterDefinition.id.in_(param_ids)
        ).all()
        
        target_param_dict = {p.param_name: p for p in params}
        
        candidate_parameters = [
            {
                "id": p.id,
                "param_code": p.param_code,
                "param_name": p.param_name,
                "category_code": p.category_code,
                "status": p.status
            }
            for p in params
        ]
    
    for param_name in source_params:
        if param_name in target_param_dict:
            auto_mappings.append({
                "source_param_name": param_name,
                "target_parameter_id": target_param_dict[param_name].id,
                "target_param_name": param_name,
                "mapping_mode": "auto_same_name",
                "mapping_status": "ready",
                "candidate_parameters": candidate_parameters
            })
        else:
            missing_mappings.append({
                "source_param_name": param_name,
                "target_parameter_id": None,
                "target_param_name": None,
                "mapping_mode": "auto_same_name",
                "mapping_status": "missing",
                "candidate_parameters": candidate_parameters
            })
            
    return {
        "target_version_id": target_version_id,
        "target_version_code": target["version_code"],
        "status": "ready" if not missing_mappings else "partial",
        "new_modules": new_modules,
        "new_scenes": new_scenes,
        "new_formulas": new_formulas,
        "conflicts": conflicts,
        "auto_mappings": auto_mappings,
        "missing_mappings": missing_mappings
    }

def preview_formula_module_sync(db: Session, source_model_id: int, source_module_code: str, scope_type: str, target_version_ids=None):
    source_payload = list_model_formula_modules(db, source_model_id)
    source_module = next((item for item in source_payload["modules"] if item["module_code"] == source_module_code), None)
    if not source_module:
        raise DrumDesignError("源模块不存在")
    targets = list_formula_sync_targets(db, source_model_id, scope_type, target_version_ids)["targets"]
    return {
        "source": {
            "model_id": source_model_id,
            "module_code": source_module["module_code"],
            "module_name": source_module["module_name"],
        },
        "targets": [_build_formula_module_sync_preview_target(db, source_model_id, source_module, target) for target in targets],
    }

def _sync_module_to_target(db: Session, source_model_id: int, source_module_code: str, target_version_id: int, conflict_actions: list, allow_missing: bool):
    source_payload = list_model_formula_modules(db, source_model_id)
    source_module = next((item for item in source_payload["modules"] if item["module_code"] == source_module_code), None)
    if not source_module:
        raise DrumDesignError("源模块不存在")
        
    target_version = _ensure_model_version(db, target_version_id)
    preview_target = _build_formula_module_sync_preview_target(db, source_model_id, source_module, {"version_id": target_version_id, "version_code": target_version.version_code})
    
    if preview_target["missing_mappings"] and not allow_missing:
        return {"skipped_target_count": 1}
        
    summary = {
        "success_target_count": 1,
        "created_module_count": 0,
        "created_scene_count": 0,
        "created_formula_count": 0,
        "overwritten_formula_count": 0,
        "missing_mapping_count": len(preview_target["missing_mappings"])
    }
    
    target_payload = list_model_formula_modules(db, target_version_id)
    target_module = next((item for item in target_payload["modules"] if item["module_code"] == source_module_code), None)
    if not target_module:
        create_formula_module(db, target_version_id, source_module["module_name"])
        summary["created_module_count"] += 1
        target_payload = list_model_formula_modules(db, target_version_id)
        target_module = next((item for item in target_payload["modules"] if item["module_code"] == source_module_code), None)
        
    conflict_map = {(a.scene_code, a.formula_name): a.action for a in conflict_actions if a.target_version_id == target_version_id}
    
    target_scene_codes = {scene["scene_code"]: scene for scene in target_module.get("scenes", [])}
    for source_scene in source_module.get("scenes", []):
        if source_scene["scene_code"] not in target_scene_codes:
            create_formula_scene(db, target_version_id, source_module_code, source_scene["scene_name"])
            summary["created_scene_count"] += 1
            
        for formula in source_scene.get("formulas", []):
            is_conflict = any(c["scene_code"] == source_scene["scene_code"] and c["formula_name"] == formula["name"] for c in preview_target["conflicts"])
            action = conflict_map.get((source_scene["scene_code"], formula["name"]), "overwrite")
            if is_conflict and action != "overwrite":
                continue
                
            payload = type("Payload", (), {
                "id": None,
                "model_id": target_version_id,
                "module_code": source_module_code,
                "module_name": source_module["module_name"],
                "scene_code": source_scene["scene_code"],
                "scene_name": source_scene["scene_name"],
                "name": formula["name"],
                "expression": formula["expression"],
                "canonical_expression": formula.get("canonical_expression"),
                "variables": formula.get("variables", {}),
                "source_type": formula.get("source_type", "manual"),
                "formula_library_id": formula.get("formula_library_id"),
                "sort_order": formula.get("sort_order", 0)
            })()
            upsert_model_formula(db, payload)
            if is_conflict:
                summary["overwritten_formula_count"] += 1
            else:
                summary["created_formula_count"] += 1
                
    # Handle parameter mappings
    db.query(WorkbenchFormulaParamMapping).filter(
        WorkbenchFormulaParamMapping.target_version_id == target_version_id,
        WorkbenchFormulaParamMapping.module_code == source_module_code
    ).delete(synchronize_session=False)
    
    for m in preview_target["auto_mappings"]:
        db.add(WorkbenchFormulaParamMapping(
            target_version_id=target_version_id,
            module_code=source_module_code,
            source_param_name=m["source_param_name"],
            target_parameter_id=m["target_parameter_id"],
            target_param_name=m["target_param_name"],
            mapping_mode=m["mapping_mode"],
            mapping_status=m["mapping_status"],
            source_version_id=source_model_id,
            source_module_code=source_module_code
        ))
    for m in preview_target["missing_mappings"]:
        db.add(WorkbenchFormulaParamMapping(
            target_version_id=target_version_id,
            module_code=source_module_code,
            source_param_name=m["source_param_name"],
            target_parameter_id=m["target_parameter_id"],
            target_param_name=m["target_param_name"],
            mapping_mode=m["mapping_mode"],
            mapping_status=m["mapping_status"],
            source_version_id=source_model_id,
            source_module_code=source_module_code
        ))
        
    # Handle sync link
    sync_link = db.query(WorkbenchFormulaModuleSyncLink).filter(
        WorkbenchFormulaModuleSyncLink.source_version_id == source_model_id,
        WorkbenchFormulaModuleSyncLink.source_module_code == source_module_code,
        WorkbenchFormulaModuleSyncLink.target_version_id == target_version_id,
        WorkbenchFormulaModuleSyncLink.target_module_code == source_module_code
    ).first()
    if not sync_link:
        sync_link = WorkbenchFormulaModuleSyncLink(
            source_version_id=source_model_id,
            source_module_code=source_module_code,
            target_version_id=target_version_id,
            target_module_code=source_module_code
        )
        db.add(sync_link)
    
    sync_link.sync_status = "partial" if preview_target["missing_mappings"] else "ready"
    sync_link.last_sync_mode = "manual"
    sync_link.last_sync_summary = summary
    
    db.flush()
    return summary

def execute_formula_module_sync(db: Session, source_model_id: int, source_module_code: str, payload):
    preview = preview_formula_module_sync(
        db,
        source_model_id,
        source_module_code,
        "manual",
        payload.target_version_ids,
    )
    summary = {
        "success_target_count": 0,
        "skipped_target_count": 0,
        "failed_target_count": 0,
        "created_module_count": 0,
        "created_scene_count": 0,
        "created_formula_count": 0,
        "overwritten_formula_count": 0,
        "missing_mapping_count": 0,
    }
    for target in preview["targets"]:
        result = _sync_module_to_target(
            db=db,
            source_model_id=source_model_id,
            source_module_code=source_module_code,
            target_version_id=target["target_version_id"],
            conflict_actions=payload.conflict_actions,
            allow_missing=target["target_version_id"] in set(payload.allow_missing_mapping_targets or []),
        )
        for key in summary:
            summary[key] += int(result.get(key, 0) or 0)
    db.commit()
    return summary

def list_formula_param_mappings(db: Session, target_model_id: int, module_code: str):
    mappings = db.query(WorkbenchFormulaParamMapping).filter(
        WorkbenchFormulaParamMapping.target_version_id == target_model_id,
        WorkbenchFormulaParamMapping.module_code == module_code
    ).all()
    
    # 获取目标模型的所有参数定义
    # 首先获取所有的parameter_id
    param_value_ids = db.query(ModelParameterValue.parameter_id).filter(
        ModelParameterValue.version_id == target_model_id
    ).all()
    
    # 提取ID列表
    param_ids = [pv[0] for pv in param_value_ids]
    
    # 查询对应的参数定义
    candidate_parameters = []
    if param_ids:
        params = db.query(ParameterDefinition).filter(
            ParameterDefinition.id.in_(param_ids)
        ).all()
        
        candidate_parameters = [
            {
                "id": p.id,
                "param_code": p.param_code,
                "param_name": p.param_name,
                "category_code": p.category_code,
                "status": p.status
            }
            for p in params
        ]
    
    result = []
    for m in mappings:
        result.append({
            "source_param_name": m.source_param_name,
            "target_parameter_id": m.target_parameter_id,
            "target_param_name": m.target_param_name,
            "mapping_mode": m.mapping_mode,
            "mapping_status": m.mapping_status,
            "candidate_parameters": candidate_parameters
        })
    return result

def save_formula_param_mappings(db: Session, target_model_id: int, module_code: str, mappings):
    for m in mappings:
        record = db.query(WorkbenchFormulaParamMapping).filter(
            WorkbenchFormulaParamMapping.target_version_id == target_model_id,
            WorkbenchFormulaParamMapping.module_code == module_code,
            WorkbenchFormulaParamMapping.source_param_name == m.source_param_name
        ).first()
        if record:
            record.target_parameter_id = m.target_parameter_id
            record.target_param_name = m.target_param_name
            record.mapping_mode = "manual"
            record.mapping_status = "ready"
            
    db.flush()
    
    missing_count = db.query(WorkbenchFormulaParamMapping).filter(
        WorkbenchFormulaParamMapping.target_version_id == target_model_id,
        WorkbenchFormulaParamMapping.module_code == module_code,
        WorkbenchFormulaParamMapping.mapping_status != "ready"
    ).count()
    
    if missing_count == 0:
        sync_link = db.query(WorkbenchFormulaModuleSyncLink).filter(
            WorkbenchFormulaModuleSyncLink.target_version_id == target_model_id,
            WorkbenchFormulaModuleSyncLink.target_module_code == module_code
        ).first()
        if sync_link and sync_link.sync_status == "partial":
            sync_link.sync_status = "ready"
            
    db.commit()
    return {"success": True}
