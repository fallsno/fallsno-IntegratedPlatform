import re

from app.models import (
    ModelFamily,
    ModelParameterValue,
    ModelVersion,
    ModuleParameterValue,
    ParameterDefinition,
    ProductType,
    WorkbenchParameterSnapshot,
)
from app.services.parameter_catalog import is_blocked_parameter_identity
from app.services.parameter_matrix_import import get_import_version_spec


class MatrixValidationError(ValueError):
    pass


_PARAMETER_CENTER_ALLOWED_FAMILY_CATEGORIES = ("原生滚筒", "再生滚筒", "干混滚筒")


def _normalize_keyword(value):
    return str(value or "").strip()


def _build_param_code_seed(param_name):
    seed = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", _normalize_keyword(param_name)).strip("_")
    return (seed or "PARAM").upper()


def _should_persist_workbench_parameter_row(row):
    value_type = _normalize_keyword((row or {}).get("value_type") or "basic").lower()
    param_name = _normalize_keyword((row or {}).get("param_name"))
    if value_type == "equipment":
        return False
    if param_name.startswith("电机_") or param_name.startswith("减速机_"):
        return False
    return True


def _extract_capacity_number(*values):
    for value in values:
        text = _normalize_keyword(value)
        if not text:
            continue
        matched = re.search(r"(\d+(?:\.\d+)?)", text)
        if not matched:
            continue
        try:
            return int(float(matched.group(1)))
        except (TypeError, ValueError):
            continue
    return None


def _ensure_parameter_definition(db, param_name, unit_code="", category_name="", param_code=None, value_type="basic", module_id=None):
    name = _normalize_keyword(param_name)
    if not name:
        raise MatrixValidationError("param_name 不能为空")
    if is_blocked_parameter_identity(param_code, name):
        raise MatrixValidationError("禁止创建测试参数或随机占位参数")

    normalized_category = _normalize_keyword(category_name) or "basic"
    normalized_value_type = value_type or "basic"

    existing = (
        db.query(ParameterDefinition)
        .filter(ParameterDefinition.param_name == name)
        .order_by(ParameterDefinition.id.asc())
        .first()
    )
    if existing:
        # 模块级模式下，只复用“同模块内”已有参数；跨模块同名参数视为全新参数，
        # 避免把别的模块的参数挂到当前模块（模块间参数相互独立）。
        if module_id and int(existing.module_id or 0) != int(module_id):
            existing = None
    if existing:
        if unit_code and not existing.unit_code:
            existing.unit_code = _normalize_keyword(unit_code) or None
        if normalized_category and normalized_category != "basic" and (existing.category_code in ("", "basic", "uncategorized")):
            existing.category_code = normalized_category
        if normalized_value_type and normalized_value_type != "basic" and existing.value_type == "basic":
            existing.value_type = normalized_value_type
        if param_code and not existing.param_code.startswith("MATRIX_"):
             # If we provided a specific param code and existing one is auto-generated or missing, we can update it
             pass # But usually we shouldn't change existing param code easily
        db.flush()
        return existing, False

    new_param_code = param_code
    if not new_param_code:
        new_param_code = f"MATRIX_{_build_param_code_seed(name)}"
        duplicate_index = 1
        while (
            db.query(ParameterDefinition)
            .filter(ParameterDefinition.param_code == new_param_code)
            .first()
        ):
            duplicate_index += 1
            new_param_code = f"MATRIX_{_build_param_code_seed(name)}_{duplicate_index}"
    else:
        # Check if provided param_code already exists
        if db.query(ParameterDefinition).filter(ParameterDefinition.param_code == new_param_code).first():
             raise MatrixValidationError(f"参数编码 {new_param_code} 已存在")

    parameter = ParameterDefinition(
        param_code=new_param_code,
        param_name=name,
        display_name=name,
        category_code=normalized_category,
        value_type=normalized_value_type,
        data_type="number",
        unit_code=_normalize_keyword(unit_code) or None,
        status="active",
        module_id=int(module_id) if module_id else None,
    )
    db.add(parameter)
    db.flush()
    return parameter, True


def _ensure_model_versions(db, version_codes):
    normalized_codes = [_normalize_keyword(code) for code in (version_codes or []) if _normalize_keyword(code)]
    versions = []
    if normalized_codes:
        versions = (
            db.query(ModelVersion)
            .filter(ModelVersion.version_code.in_(normalized_codes))
            .all()
        )
    versions_by_code = {_normalize_keyword(row.version_code): row for row in versions}

    missing_codes = [code for code in normalized_codes if code not in versions_by_code]
    for code in missing_codes:
        spec = get_import_version_spec(code)
        if not spec:
            raise MatrixValidationError(f"未找到型号: {code}")

        family = None
        for family_code in spec.get("family_codes") or []:
            family = (
                db.query(ModelFamily)
                .filter(ModelFamily.family_code == family_code)
                .order_by(ModelFamily.id.asc())
                .first()
            )
            if family:
                break
        if not family:
            raise MatrixValidationError(f"未找到型号归属系列: {spec['version_code']}")

        version = ModelVersion(
            family_id=family.id,
            version_code=spec["version_code"],
            display_name=spec["version_code"],
            status="active",
        )
        db.add(version)
        db.flush()
        versions_by_code[_normalize_keyword(version.version_code)] = version

    return versions_by_code


def _build_shadow_version_codes(version_code):
    normalized_code = _normalize_keyword(version_code)
    if not normalized_code:
        return []

    shadow_codes = []
    rt_match = re.match(r"^RT(\d+)$", normalized_code, re.IGNORECASE)
    if rt_match:
        shadow_codes.append(f"GTR{rt_match.group(1)}")

    hts_match = re.match(r"^HTS(\d+)$", normalized_code, re.IGNORECASE)
    if hts_match:
        shadow_codes.append(f"GTR{hts_match.group(1)}")

    return [code for code in dict.fromkeys(shadow_codes) if code != normalized_code]


def normalize_matrix_row(data):
    version_id = data.get("version_id")
    parameter_id = data.get("parameter_id")
    if not version_id:
        raise MatrixValidationError("version_id 不能为空")
    if not parameter_id:
        raise MatrixValidationError("parameter_id 不能为空")
    return {
        "version_id": int(version_id),
        "parameter_id": int(parameter_id),
        "param_value": "" if data.get("param_value") is None else str(data.get("param_value")).strip(),
        "value_source": str(data.get("value_source") or "manual").strip(),
        "version_no": str(data.get("version_no") or "draft").strip(),
        "sort_order": int(data.get("sort_order") or 0),
        "remark": str(data.get("remark") or "").strip() or None,
    }


def normalize_workbench_parameter_row(data):
    version_id = data.get("version_id")
    if not version_id:
        raise MatrixValidationError("version_id 不能为空")

    parameter_id = int(data.get("parameter_id") or 0)
    param_name = _normalize_keyword(data.get("param_name"))
    if parameter_id <= 0 and not param_name:
        raise MatrixValidationError("parameter_id 与 param_name 不能同时为空")

    return {
        "version_id": int(version_id),
        "parameter_id": parameter_id,
        "param_code": _normalize_keyword(data.get("param_code")),
        "param_name": param_name,
        "param_value": "" if data.get("param_value") is None else str(data.get("param_value")).strip(),
        "unit_code": _normalize_keyword(data.get("unit_code") or ""),
        "value_type": _normalize_keyword(data.get("value_type") or "basic") or "basic",
        "description": str(data.get("description") or "").strip(),
        "remark": str(data.get("remark") or "").strip() or None,
    }


def normalize_snapshot_payload(data):
    run_key = str(data.get("run_key") or "").strip()
    if not run_key:
        raise MatrixValidationError("run_key 不能为空")
    return {
        "run_key": run_key,
        "version_id": int(data["version_id"]) if data.get("version_id") else None,
        "parameter_id": int(data["parameter_id"]),
        "snapshot_value": str(data.get("snapshot_value") or "").strip(),
        "source_version": str(data.get("source_version") or "").strip() or None,
        "source_type": str(data.get("source_type") or "matrix").strip(),
    }


def _format_stat_number(value):
    if value is None:
        return ""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def build_family_matrix(db, family, versions, module_id=None):
    version_ids = [row.id for row in versions]
    parameter_ids = []
    cells = []
    if module_id:
        # 模块级：只取当前模块的参数（定义挂在模块下），值从模块级表读
        parameter_ids = [
            row[0]
            for row in db.query(ParameterDefinition.id)
            .filter(ParameterDefinition.module_id == int(module_id))
            .all()
        ]
        if version_ids and parameter_ids:
            cells = (
                db.query(ModuleParameterValue)
                .filter(
                    ModuleParameterValue.module_id == int(module_id),
                    ModuleParameterValue.version_id.in_(version_ids),
                )
                .all()
            )
    else:
        # 兼容：未指定模块时读旧型号级表
        if version_ids:
            cells = db.query(ModelParameterValue).filter(ModelParameterValue.version_id.in_(version_ids)).all()
        parameter_ids = sorted({row.parameter_id for row in cells})
    parameters = []
    if parameter_ids:
        parameters = (
            db.query(ParameterDefinition)
            .filter(ParameterDefinition.id.in_(parameter_ids))
            .order_by(ParameterDefinition.param_code.asc(), ParameterDefinition.id.asc())
            .all()
        )
    value_map = {}
    remark_map = {}
    for cell in cells:
        value_map[(cell.parameter_id, cell.version_id)] = cell.param_value
        remark_map[(cell.parameter_id, cell.version_id)] = cell.remark
    return {
        "family": {
            "id": family.id,
            "family_code": family.family_code,
            "family_name": family.family_name,
        },
        "versions": [{"id": row.id, "version_code": row.version_code} for row in versions],
        "rows": [
            {
                "parameter_id": param.id,
                "param_code": param.param_code,
                "param_name": param.param_name,
                "display_name": param.display_name,
                "unit_code": param.unit_code,
                "category_code": param.category_code,
                "value_type": param.value_type,
                "description": param.description,
                "remark": remark_map.get((param.id, versions[0].id), "") if len(versions) == 1 else "",
                "values": {
                    version.id: value_map.get((param.id, version.id), "")
                    for version in versions
                },
                "remarks": {
                    version.id: remark_map.get((param.id, version.id), "")
                    for version in versions
                },
            }
            for param in parameters
        ],
    }


def build_parameter_center_matrix(db, keyword=None, module_id=None):
    query = db.query(ParameterDefinition)
    if module_id:
        query = query.filter(ParameterDefinition.module_id == int(module_id))
    keyword = _normalize_keyword(keyword)
    if keyword:
        query = query.filter(
            (ParameterDefinition.param_code.ilike(f"%{keyword}%"))
            | (ParameterDefinition.param_name.ilike(f"%{keyword}%"))
            | (ParameterDefinition.display_name.ilike(f"%{keyword}%"))
        )
    query = query.filter(ParameterDefinition.value_type != "equipment")

    parameters = query.order_by(ParameterDefinition.param_code.asc(), ParameterDefinition.id.asc()).all()
    versions = (
        db.query(ModelVersion)
        .join(ModelFamily, ModelVersion.family_id == ModelFamily.id)
        .outerjoin(ProductType, ModelFamily.product_type_id == ProductType.id)
        .filter(ModelFamily.category.in_(_PARAMETER_CENTER_ALLOWED_FAMILY_CATEGORIES))
        .filter(~ModelFamily.family_code.ilike("WB-AUTO-%"))
        .order_by(
            ModelFamily.sort_order.asc(),
            ModelFamily.id.asc(),
            ModelVersion.capacity_value.asc().nullslast(),
            ProductType.machine_model.asc().nullslast(),
            ModelVersion.created_at.asc(),
            ModelVersion.id.asc(),
        )
        .all()
    )
    value_rows = []
    if parameters and versions:
        if module_id:
            value_rows = (
                db.query(ModuleParameterValue)
                .filter(
                    ModuleParameterValue.module_id == int(module_id),
                    ModuleParameterValue.parameter_id.in_([row.id for row in parameters]),
                    ModuleParameterValue.version_id.in_([row.id for row in versions]),
                )
                .all()
            )
        else:
            value_rows = (
                db.query(ModelParameterValue)
                .filter(
                    ModelParameterValue.parameter_id.in_([row.id for row in parameters]),
                    ModelParameterValue.version_id.in_([row.id for row in versions]),
                )
                .all()
            )
    value_map = {(row.parameter_id, row.version_id): str(row.param_value or "") for row in value_rows}
    return {
        "versions": [
            {
                "id": row.id,
                "family_id": row.family_id,
                "version_code": row.version_code,
                "display_name": row.display_name,
                "capacity_value": row.capacity_value or _extract_capacity_number(
                    row.family.product_type.machine_model if row.family and row.family.product_type else "",
                    row.display_name,
                    row.version_code,
                ),
                "family_code": row.family.family_code if row.family else "",
                "family_name": row.family.family_name if row.family else "",
                "family_category": row.family.category if row.family else "",
                "product_type_id": row.family.product_type_id if row.family else None,
                "product_type_name": row.family.product_type.type_name if row.family and row.family.product_type else "",
                "machine_model": row.family.product_type.machine_model if row.family and row.family.product_type else "",
            }
            for row in versions
        ],
        "rows": [
            {
                "parameter_id": param.id,
                "param_code": param.param_code,
                "param_name": param.param_name,
                "unit_code": param.unit_code,
                "category_code": param.category_code,
                "display_name": param.display_name,
                "default_value": param.default_value,
                "values": {
                    version.id: value_map.get((param.id, version.id), "")
                    for version in versions
                },
            }
            for param in parameters
        ],
    }


def build_parameter_distribution(db, parameter_id, module_id=None):
    parameter = (
        db.query(ParameterDefinition)
        .filter(ParameterDefinition.id == parameter_id)
        .first()
    )
    if not parameter:
        raise MatrixValidationError("parameter not found")

    if module_id:
        cells = (
            db.query(ModuleParameterValue)
            .filter(
                ModuleParameterValue.module_id == int(module_id),
                ModuleParameterValue.parameter_id == parameter_id,
            )
            .order_by(ModuleParameterValue.version_id.asc(), ModuleParameterValue.id.asc())
            .all()
        )
    else:
        cells = (
            db.query(ModelParameterValue)
            .filter(ModelParameterValue.parameter_id == parameter_id)
            .order_by(ModelParameterValue.version_id.asc(), ModelParameterValue.id.asc())
            .all()
        )
    version_ids = [row.version_id for row in cells]
    versions = []
    if version_ids:
        versions = (
            db.query(ModelVersion)
            .filter(ModelVersion.id.in_(version_ids))
            .order_by(ModelVersion.id.asc())
            .all()
        )

    family = None
    if versions:
        family = (
            db.query(ModelFamily)
            .filter(ModelFamily.id == versions[0].family_id)
            .first()
        )

    value_map = {row.version_id: str(row.param_value or "") for row in cells}
    return {
        "parameter_id": parameter.id,
        "param_code": parameter.param_code,
        "param_name": parameter.param_name,
        "unit_code": parameter.unit_code,
        "family_id": family.id if family else None,
        "family_code": family.family_code if family else None,
        "values": [
            {
                "version_id": version.id,
                "version_code": version.version_code,
                "param_value": value_map.get(version.id, ""),
            }
            for version in versions
        ],
    }


def save_family_matrix_rows(db, family_id, rows):
    versions = db.query(ModelVersion).filter(ModelVersion.family_id == family_id).all()
    version_ids = {row.id for row in versions}
    normalized_rows = [normalize_matrix_row(row) for row in (rows or [])]
    for row in normalized_rows:
        if row["version_id"] not in version_ids:
            raise MatrixValidationError("version_id 不属于当前系列")

    for row in normalized_rows:
        current = (
            db.query(ModelParameterValue)
            .filter(
                ModelParameterValue.version_id == row["version_id"],
                ModelParameterValue.parameter_id == row["parameter_id"],
            )
            .first()
        )
        if current:
            current.param_value = row["param_value"]
            current.value_source = row["value_source"]
            current.version_no = row["version_no"]
            current.sort_order = row["sort_order"]
            current.remark = row["remark"]
            continue
        db.add(ModelParameterValue(**row))

    db.commit()
    return {"family_id": family_id, "saved_count": len(normalized_rows)}


def save_workbench_parameter_rows(db, family_id, rows, module_id=None):
    versions = db.query(ModelVersion).filter(ModelVersion.family_id == family_id).all()
    version_ids = {row.id for row in versions}
    normalized_rows = [
        normalize_workbench_parameter_row(row)
        for row in (rows or [])
        if _should_persist_workbench_parameter_row(row)
    ]
    created_parameter_count = 0

    for row in normalized_rows:
        if row["version_id"] not in version_ids:
            raise MatrixValidationError("version_id 不属于当前系列")

    for row in normalized_rows:
        parameter_id = row["parameter_id"]
        if parameter_id <= 0:
            parameter, created = _ensure_parameter_definition(
                db,
                row["param_name"],
                row["unit_code"],
                "basic",
                row.get("param_code"),
                row.get("value_type", "basic"),
                module_id=module_id,
            )
            parameter_id = parameter.id
            if created:
                created_parameter_count += 1
            if module_id and parameter.module_id is None:
                parameter.module_id = int(module_id)
                db.flush()
        else:
            # Update parameter definition if modified from workbench
            parameter = db.query(ParameterDefinition).filter(ParameterDefinition.id == parameter_id).first()
            if parameter:
                updated = False
                if row.get("value_type") and parameter.value_type != row["value_type"]:
                    parameter.value_type = row["value_type"]
                    updated = True
                if row.get("param_name") and parameter.param_name != row["param_name"]:
                    parameter.param_name = row["param_name"]
                    parameter.display_name = row["param_name"]
                    updated = True
                if row.get("param_code") and parameter.param_code != row["param_code"]:
                    parameter.param_code = row["param_code"]
                    updated = True
                if row.get("unit_code") is not None and parameter.unit_code != row["unit_code"]:
                    parameter.unit_code = row["unit_code"] or None
                    updated = True
                if row.get("description") is not None and parameter.description != row["description"]:
                    parameter.description = row["description"] or None
                    updated = True
                # 参数归属模块：仅当参数还没有模块归属时挂到当前模块，避免跨模块抢走参数
                if module_id and parameter.module_id is None:
                    parameter.module_id = int(module_id)
                    updated = True
                if updated:
                    db.flush()

        if module_id:
            # 模块级：写入模块+型号参数值表
            current = (
                db.query(ModuleParameterValue)
                .filter(
                    ModuleParameterValue.module_id == int(module_id),
                    ModuleParameterValue.version_id == row["version_id"],
                    ModuleParameterValue.parameter_id == parameter_id,
                )
                .first()
            )
            if current:
                current.param_value = row["param_value"]
                current.value_source = "manual"
                current.version_no = current.version_no or "draft"
                current.remark = row.get("remark")
                continue

            db.add(
                ModuleParameterValue(
                    module_id=int(module_id),
                    version_id=row["version_id"],
                    parameter_id=parameter_id,
                    param_value=row["param_value"],
                    value_source="manual",
                    version_no="draft",
                    sort_order=0,
                    remark=row.get("remark"),
                )
            )
            continue

        current = (
            db.query(ModelParameterValue)
            .filter(
                ModelParameterValue.version_id == row["version_id"],
                ModelParameterValue.parameter_id == parameter_id,
            )
            .first()
        )
        if current:
            current.param_value = row["param_value"]
            current.value_source = "manual"
            current.version_no = current.version_no or "draft"
            current.remark = row.get("remark")
            continue

        db.add(
            ModelParameterValue(
                version_id=row["version_id"],
                parameter_id=parameter_id,
                param_value=row["param_value"],
                value_source="manual",
                version_no="draft",
                sort_order=0,
                remark=row.get("remark"),
            )
        )

    db.commit()
    return {
        "family_id": family_id,
        "saved_count": len(normalized_rows),
        "created_parameter_count": created_parameter_count,
    }


def save_imported_parameter_matrix(db, orientation, parameter_rows):
    rows = parameter_rows or []
    version_codes = sorted(
        {
            _normalize_keyword(version_code)
            for row in rows
            for version_code in (row.get("values") or {}).keys()
            if _normalize_keyword(version_code)
        }
    )
    required_version_codes = set(version_codes)
    for version_code in version_codes:
        required_version_codes.update(_build_shadow_version_codes(version_code))
    versions_by_code = _ensure_model_versions(db, sorted(required_version_codes))

    imported_parameter_count = len(rows)
    saved_value_count = 0
    warnings = []
    for row in rows:
        parameter, _created = _ensure_parameter_definition(
            db,
            row.get("param_name"),
            row.get("unit_code") or "",
            row.get("category_name") or "",
        )

        pending_values = {}
        for version_code, raw_value in (row.get("values") or {}).items():
            normalized_code = _normalize_keyword(version_code)
            if not normalized_code:
                continue
            value = _normalize_keyword(raw_value)
            target_codes = [normalized_code, *_build_shadow_version_codes(normalized_code)]
            for target_code in target_codes:
                existing_value = pending_values.get(target_code)
                if existing_value is not None and existing_value != value:
                    warnings.append(
                        f"参数 {parameter.param_name} 的旧代号 {target_code} 命中多个来源，已保留首个值"
                    )
                    continue
                pending_values[target_code] = value

        for target_code, value in pending_values.items():
            version = versions_by_code[target_code]
            current = (
                db.query(ModelParameterValue)
                .filter(
                    ModelParameterValue.version_id == version.id,
                    ModelParameterValue.parameter_id == parameter.id,
                )
                .first()
            )
            if current:
                current.param_value = value
                current.value_source = "import"
                current.version_no = current.version_no or "draft"
                saved_value_count += 1
                continue
            db.add(
                ModelParameterValue(
                    version_id=version.id,
                    parameter_id=parameter.id,
                    param_value=value,
                    value_source="import",
                    version_no="draft",
                    sort_order=0,
                )
            )
            saved_value_count += 1

    db.commit()
    return {
        "orientation": orientation,
        "imported_parameter_count": imported_parameter_count,
        "saved_value_count": saved_value_count,
        "warnings": list(dict.fromkeys(warnings)),
    }


def delete_model_parameter_value(db, version_id, parameter_id):
    row = (
        db.query(ModelParameterValue)
        .filter(
            ModelParameterValue.version_id == version_id,
            ModelParameterValue.parameter_id == parameter_id,
        )
        .first()
    )
    if not row:
        raise MatrixValidationError("model parameter value not found")
    db.delete(row)
    db.commit()
    return {"version_id": version_id, "parameter_id": parameter_id, "deleted": True}


def save_workbench_snapshot_rows(db, run_key, rows):
    raw_rows = rows or []
    if not raw_rows:
        raise MatrixValidationError("rows 不能为空")

    db.query(WorkbenchParameterSnapshot).filter(WorkbenchParameterSnapshot.run_key == run_key).delete()
    normalized_rows = [
        normalize_snapshot_payload({**row, "run_key": run_key})
        for row in raw_rows
    ]
    for row in normalized_rows:
        db.add(WorkbenchParameterSnapshot(**row))
    db.commit()
    return {"run_key": run_key, "saved_count": len(normalized_rows)}


def get_latest_workbench_snapshot(db, version_id):
    # Find the latest run_key for this version
    latest_snapshot = (
        db.query(WorkbenchParameterSnapshot.run_key)
        .filter(WorkbenchParameterSnapshot.version_id == version_id)
        .order_by(WorkbenchParameterSnapshot.created_at.desc())
        .first()
    )
    if not latest_snapshot:
        return {"run_key": None, "rows": []}

    run_key = latest_snapshot[0]
    rows = (
        db.query(WorkbenchParameterSnapshot)
        .filter(WorkbenchParameterSnapshot.run_key == run_key)
        .all()
    )
    return {
        "run_key": run_key,
        "rows": [
            {
                "parameter_id": r.parameter_id,
                "snapshot_value": r.snapshot_value,
                "source_type": r.source_type
            } for r in rows
        ]
    }


def build_parameter_stats(db, parameter_id):
    rows = (
        db.query(ModelParameterValue)
        .filter(ModelParameterValue.parameter_id == parameter_id)
        .order_by(ModelParameterValue.id.asc())
        .all()
    )
    values = []
    for row in rows:
        try:
            values.append(float(str(row.param_value).strip()))
        except (TypeError, ValueError):
            continue
    if not values:
        return {"min_value": "", "max_value": "", "avg_value": "", "sample_count": 0}
    return {
        "min_value": _format_stat_number(min(values)),
        "max_value": _format_stat_number(max(values)),
        "avg_value": _format_stat_number(sum(values) / len(values)),
        "sample_count": len(values),
    }


def delete_parameter_definition(db, parameter_id):
    row = db.query(ParameterDefinition).filter(ParameterDefinition.id == parameter_id).first()
    if not row:
        raise MatrixValidationError("parameter not found")
    db.query(ModelParameterValue).filter(ModelParameterValue.parameter_id == parameter_id).delete()
    db.delete(row)
    db.commit()
    return {"parameter_id": parameter_id, "deleted": True}
