from app.models import (
    ParameterDefinition,
    ParameterLookupConfig,
    ParameterLookupDefinition,
    ParameterLookupRow,
)


class ParameterLookupValidationError(ValueError):
    pass


def normalize_lookup_payload(data):
    lookup_code = str((data or {}).get("lookup_code") or "").strip()
    lookup_name = str((data or {}).get("lookup_name") or "").strip()
    if not lookup_code:
        raise ParameterLookupValidationError("lookup_code 不能为空")
    if not lookup_name:
        raise ParameterLookupValidationError("lookup_name 不能为空")
    return {
        "lookup_code": lookup_code,
        "lookup_name": lookup_name,
        "description": str((data or {}).get("description") or "").strip() or None,
        "status": str((data or {}).get("status") or "active").strip() or "active",
    }


def normalize_lookup_rows(rows):
    normalized = []
    seen_keys = set()
    for index, row in enumerate(rows or [], start=1):
        lookup_key = str((row or {}).get("lookup_key") or "").strip()
        result_value = str((row or {}).get("result_value") or "").strip()
        if not lookup_key:
            raise ParameterLookupValidationError(f"第 {index} 行 lookup_key 不能为空")
        if lookup_key in seen_keys:
            raise ParameterLookupValidationError(f"第 {index} 行 lookup_key 重复: {lookup_key}")
        if not result_value:
            raise ParameterLookupValidationError(f"第 {index} 行 result_value 不能为空")
        seen_keys.add(lookup_key)
        normalized.append(
            {
                "lookup_key": lookup_key,
                "result_value": result_value,
                "sort_order": int((row or {}).get("sort_order") or index - 1),
                "remark": str((row or {}).get("remark") or "").strip() or None,
            }
        )
    return normalized


def _normalize_unique_text_list(values):
    normalized = []
    seen = set()
    for value in values or []:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _parse_curve_numeric(value, label):
    text = str(value or "").strip()
    if not text:
        raise ParameterLookupValidationError(f"{label} 不能为空")
    try:
        return float(text)
    except (TypeError, ValueError) as exc:
        raise ParameterLookupValidationError(f"{label} 不是有效数字: {text}") from exc


def _is_monotonic_points(points):
    if len(points) < 2:
        return False
    increasing = all(points[index]["y"] < points[index + 1]["y"] for index in range(len(points) - 1))
    decreasing = all(points[index]["y"] > points[index + 1]["y"] for index in range(len(points) - 1))
    return increasing or decreasing


def normalize_curve_profile_payload(data):
    payload = data or {}
    x_axis_column = str(payload.get("x_axis_column") or "").strip()
    if not x_axis_column:
        raise ParameterLookupValidationError("x_axis_column 不能为空")

    table_columns = _normalize_unique_text_list(payload.get("table_columns") or [])
    table_rows = payload.get("table_rows") or []
    if not isinstance(table_rows, list) or not table_rows:
        raise ParameterLookupValidationError("table_rows 不能为空")
    if x_axis_column not in table_columns:
        raise ParameterLookupValidationError(f"x_axis_column 不存在于原表列中: {x_axis_column}")

    normalized_rows = []
    for index, row in enumerate(table_rows, start=1):
        if not isinstance(row, dict):
            raise ParameterLookupValidationError(f"第 {index} 行 table_rows 不是有效对象")
        normalized_row = {}
        for column in table_columns:
            normalized_row[column] = str(row.get(column) or "").strip()
        normalized_rows.append(normalized_row)

    raw_series_columns = payload.get("series_columns") or []
    series_columns = []
    if not raw_series_columns:
        raise ParameterLookupValidationError("series_columns 不能为空")
    for index, item in enumerate(raw_series_columns, start=1):
        series_key = str((item or {}).get("series_key") or "").strip()
        source_column = str((item or {}).get("source_column") or "").strip()
        if not series_key:
            raise ParameterLookupValidationError(f"第 {index} 个 series_key 不能为空")
        if not source_column:
            raise ParameterLookupValidationError(f"第 {index} 个 source_column 不能为空")
        if source_column not in table_columns:
            raise ParameterLookupValidationError(f"系列列不存在于原表列中: {source_column}")
        series_columns.append(
            {
                "series_key": series_key,
                "source_column": source_column,
                "reverse_lookup_enabled": bool((item or {}).get("reverse_lookup_enabled", False)),
            }
        )

    note_columns = _normalize_unique_text_list(payload.get("note_columns") or [])
    for column in note_columns:
        if column not in table_columns:
            raise ParameterLookupValidationError(f"备注列不存在于原表列中: {column}")

    normalized = {
        "profile_name": str(payload.get("profile_name") or "").strip() or None,
        "x_axis_column": x_axis_column,
        "table_columns": table_columns,
        "table_rows": normalized_rows,
        "series_columns": series_columns,
        "note_columns": note_columns,
        "default_lookup_mode": str(payload.get("default_lookup_mode") or "LINEAR").strip() or "LINEAR",
        "allow_interpolation": bool(payload.get("allow_interpolation", True)),
    }

    # Validate numeric structure while saving so bad source data is rejected early.
    _build_curve_preview_series(normalized)
    return normalized


def _build_curve_preview_series(profile):
    x_axis_column = str((profile or {}).get("x_axis_column") or "").strip()
    table_rows = (profile or {}).get("table_rows") or []
    series_columns = (profile or {}).get("series_columns") or []
    series = []
    warnings = []

    for series_item in series_columns:
        source_column = str((series_item or {}).get("source_column") or "").strip()
        points = []
        for row_index, row in enumerate(table_rows, start=1):
            raw_x = str((row or {}).get(x_axis_column) or "").strip()
            raw_y = str((row or {}).get(source_column) or "").strip()
            if not raw_x and not raw_y:
                continue
            point = {
                "x": _parse_curve_numeric(raw_x, f"第 {row_index} 行 {x_axis_column}"),
                "y": _parse_curve_numeric(raw_y, f"第 {row_index} 行 {source_column}"),
            }
            points.append(point)

        if not points:
            raise ParameterLookupValidationError(f"系列列没有有效数据: {source_column}")

        is_monotonic = _is_monotonic_points(points)
        if len(points) < 2:
            warnings.append(f"系列 {source_column} 有效点少于 2 个，暂不支持插值")
        series.append(
            {
                "series_key": str((series_item or {}).get("series_key") or source_column).strip(),
                "source_column": source_column,
                "reverse_lookup_enabled": bool((series_item or {}).get("reverse_lookup_enabled", False)),
                "is_monotonic": is_monotonic,
                "points": points,
            }
        )
    return series, warnings


def list_parameter_lookups(db):
    return db.query(ParameterLookupDefinition).order_by(ParameterLookupDefinition.lookup_code.asc()).all()


def get_parameter_lookup(db, lookup_id):
    return db.query(ParameterLookupDefinition).filter(ParameterLookupDefinition.id == lookup_id).first()


def get_parameter_lookup_curve_profile(db, lookup_id):
    lookup = get_parameter_lookup(db, lookup_id)
    if not lookup:
        raise ParameterLookupValidationError("lookup not found")
    profile = lookup.curve_profile or {}
    if not profile:
        return {
            "profile_name": None,
            "x_axis_column": "",
            "table_columns": [],
            "table_rows": [],
            "series_columns": [],
            "note_columns": [],
            "default_lookup_mode": "LINEAR",
            "allow_interpolation": True,
        }
    return normalize_curve_profile_payload(profile)


def create_parameter_lookup(db, data):
    payload = normalize_lookup_payload(data)
    duplicated = (
        db.query(ParameterLookupDefinition)
        .filter(ParameterLookupDefinition.lookup_code == payload["lookup_code"])
        .first()
    )
    if duplicated:
        raise ParameterLookupValidationError("lookup_code 已存在")
    row = ParameterLookupDefinition(**payload)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_parameter_lookup(db, lookup_id, data):
    row = get_parameter_lookup(db, lookup_id)
    if not row:
        raise ParameterLookupValidationError("lookup not found")

    payload = normalize_lookup_payload(data)
    duplicated = (
        db.query(ParameterLookupDefinition)
        .filter(ParameterLookupDefinition.lookup_code == payload["lookup_code"])
        .filter(ParameterLookupDefinition.id != lookup_id)
        .first()
    )
    if duplicated:
        raise ParameterLookupValidationError("lookup_code 已存在")

    for key, value in payload.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def delete_parameter_lookup(db, lookup_id):
    row = get_parameter_lookup(db, lookup_id)
    if not row:
        raise ParameterLookupValidationError("lookup not found")

    db.query(ParameterLookupConfig).filter(ParameterLookupConfig.lookup_id == lookup_id).delete()
    db.query(ParameterLookupRow).filter(ParameterLookupRow.lookup_id == lookup_id).delete()
    db.delete(row)
    db.commit()
    return {"lookup_id": int(lookup_id), "deleted": True}


def list_parameter_lookup_rows(db, lookup_id):
    return (
        db.query(ParameterLookupRow)
        .filter(ParameterLookupRow.lookup_id == lookup_id)
        .order_by(ParameterLookupRow.sort_order.asc(), ParameterLookupRow.id.asc())
        .all()
    )


def save_parameter_lookup_rows(db, lookup_id, rows):
    normalized_rows = normalize_lookup_rows(rows)
    lookup = get_parameter_lookup(db, lookup_id)
    if not lookup:
        raise ParameterLookupValidationError("lookup not found")
    db.query(ParameterLookupRow).filter(ParameterLookupRow.lookup_id == lookup_id).delete()
    for row in normalized_rows:
        db.add(ParameterLookupRow(lookup_id=lookup_id, **row))
    db.commit()
    return {"lookup_id": int(lookup_id), "saved_count": len(normalized_rows)}


def _derive_lookup_rows_from_curve_profile(profile):
    x_axis_column = str((profile or {}).get("x_axis_column") or "").strip()
    series_columns = (profile or {}).get("series_columns") or []
    table_rows = (profile or {}).get("table_rows") or []
    note_columns = (profile or {}).get("note_columns") or []
    if not x_axis_column or not series_columns or not isinstance(table_rows, list):
        return []

    primary_series = str((series_columns[0] or {}).get("source_column") or "").strip()
    primary_note = str((note_columns[0] or "")).strip() if note_columns else ""
    if not primary_series:
        return []

    derived_rows = []
    for index, row in enumerate(table_rows):
        if not isinstance(row, dict):
            continue
        derived_rows.append(
            {
                "lookup_key": str(row.get(x_axis_column) or "").strip(),
                "result_value": str(row.get(primary_series) or "").strip(),
                "sort_order": index,
                "remark": str(row.get(primary_note) or "").strip() or None if primary_note else None,
            }
        )
    return normalize_lookup_rows(derived_rows)


def save_parameter_lookup_curve_profile(db, lookup_id, data):
    lookup = get_parameter_lookup(db, lookup_id)
    if not lookup:
        raise ParameterLookupValidationError("lookup not found")
    payload = data or {}
    x_axis_column = str(payload.get("x_axis_column") or "").strip()
    table_rows = payload.get("table_rows") or []
    if not x_axis_column or not isinstance(table_rows, list) or not table_rows:
        saved_rows = list_parameter_lookup_rows(db, lookup_id)
        table_columns = ["查找值", "结果值", "备注"]
        derived_rows = [
            {"查找值": str(item.lookup_key or "").strip(), "结果值": str(item.result_value or "").strip(), "备注": str(item.remark or "")}
            for item in saved_rows
        ]
        base = {
            "profile_name": str(payload.get("profile_name") or "").strip() or None,
            "x_axis_column": "查找值",
            "table_columns": table_columns,
            "table_rows": derived_rows,
            "series_columns": payload.get("series_columns") or [],
            "note_columns": ["备注"],
            "default_lookup_mode": str(payload.get("default_lookup_mode") or "LINEAR").strip() or "LINEAR",
            "allow_interpolation": bool(payload.get("allow_interpolation", True)),
        }
        profile = normalize_curve_profile_payload(base)
    else:
        profile = normalize_curve_profile_payload(payload)
    lookup.curve_profile = profile
    if x_axis_column and isinstance(table_rows, list) and table_rows:
        derived_rows = _derive_lookup_rows_from_curve_profile(profile)
        db.query(ParameterLookupRow).filter(ParameterLookupRow.lookup_id == lookup_id).delete()
        for row in derived_rows:
            db.add(ParameterLookupRow(lookup_id=lookup_id, **row))
    db.commit()
    db.refresh(lookup)
    return lookup.curve_profile or profile


def build_parameter_lookup_curve_preview(db, lookup_id):
    lookup = get_parameter_lookup(db, lookup_id)
    if not lookup:
        raise ParameterLookupValidationError("lookup not found")
    profile = get_parameter_lookup_curve_profile(db, lookup_id)
    if not profile.get("x_axis_column") or not profile.get("series_columns"):
        raise ParameterLookupValidationError("curve profile not configured")
    series, warnings = _build_curve_preview_series(profile)
    return {
        "lookup_id": int(lookup.id),
        "lookup_name": lookup.lookup_name,
        "profile_name": profile.get("profile_name"),
        "x_axis_column": profile.get("x_axis_column") or "",
        "series": series,
        "warnings": warnings,
    }


def resolve_curve_result_value(db, lookup_name, input_value, series_key, direction="X2Y", lookup_mode="LINEAR"):
    candidates = (
        db.query(ParameterLookupDefinition)
        .filter(
            ParameterLookupDefinition.lookup_name == str(lookup_name or "").strip(),
            ParameterLookupDefinition.status == "active",
        )
        .order_by(ParameterLookupDefinition.id.desc())
        .all()
    )
    lookup = next((item for item in candidates if item.curve_profile), None) or (candidates[0] if candidates else None)
    if not lookup:
        raise ParameterLookupValidationError(f'曲线表“{lookup_name}”不存在')

    profile = get_parameter_lookup_curve_profile(db, lookup.id)
    if not profile.get("x_axis_column") or not profile.get("series_columns"):
        raise ParameterLookupValidationError(f'附录“{lookup.lookup_name}”尚未配置为曲线')

    series_list, _warnings = _build_curve_preview_series(profile)
    matched_series = next(
        (item for item in series_list if str(item.get("series_key") or "").strip() == str(series_key or "").strip()),
        None,
    )
    if not matched_series:
        raise ParameterLookupValidationError(f'系列“{series_key}”不存在，请重新选择曲线系列')

    points = matched_series.get("points") or []
    if len(points) < 2:
        raise ParameterLookupValidationError(f'系列“{series_key}”有效点不足 2 个，无法进行插值计算')

    direction = str(direction or "").strip().upper()
    lookup_mode = str(lookup_mode or "LINEAR").strip().upper()
    if lookup_mode != "LINEAR":
        raise ParameterLookupValidationError(f"暂不支持的查值方式: {lookup_mode}")

    numeric_input = float(input_value)
    sorted_points = sorted(points, key=lambda item: item["x"])

    if direction == "X2Y":
        axis_values = [point["x"] for point in sorted_points]
        if numeric_input < axis_values[0] or numeric_input > axis_values[-1]:
            raise ParameterLookupValidationError(
                f"当前值超出曲线有效范围 [{format(axis_values[0], 'g')}, {format(axis_values[-1], 'g')}]，系统未启用外推"
            )
        for point in sorted_points:
            if point["x"] == numeric_input:
                return {
                    "lookup": lookup,
                    "value": point["y"],
                    "detail": {
                        "lookup_type": "curve",
                        "lookup_name": lookup.lookup_name,
                        "series_key": matched_series["series_key"],
                        "direction": "X2Y",
                        "lookup_mode": lookup_mode,
                        "input_value": format(numeric_input, "g"),
                        "hit_type": "exact",
                        "left_point": point,
                        "right_point": point,
                    },
                }
        for index in range(len(sorted_points) - 1):
            left_point = sorted_points[index]
            right_point = sorted_points[index + 1]
            if left_point["x"] <= numeric_input <= right_point["x"]:
                ratio = (numeric_input - left_point["x"]) / (right_point["x"] - left_point["x"])
                resolved_value = left_point["y"] + ratio * (right_point["y"] - left_point["y"])
                return {
                    "lookup": lookup,
                    "value": resolved_value,
                    "detail": {
                        "lookup_type": "curve",
                        "lookup_name": lookup.lookup_name,
                        "series_key": matched_series["series_key"],
                        "direction": "X2Y",
                        "lookup_mode": lookup_mode,
                        "input_value": format(numeric_input, "g"),
                        "hit_type": "interpolated",
                        "left_point": left_point,
                        "right_point": right_point,
                    },
                }
        raise ParameterLookupValidationError("曲线插值失败，未找到有效区间")

    if direction != "Y2X":
        raise ParameterLookupValidationError(f"暂不支持的查值方向: {direction}")
    if not matched_series.get("is_monotonic"):
        raise ParameterLookupValidationError(f'系列“{series_key}”不是单调曲线，暂不支持 Y 查 X')

    y_points = sorted(points, key=lambda item: item["y"])
    axis_values = [point["y"] for point in y_points]
    if numeric_input < axis_values[0] or numeric_input > axis_values[-1]:
        raise ParameterLookupValidationError(
            f"当前值超出曲线有效范围 [{format(axis_values[0], 'g')}, {format(axis_values[-1], 'g')}]，系统未启用外推"
        )
    for point in y_points:
        if point["y"] == numeric_input:
            return {
                "lookup": lookup,
                "value": point["x"],
                "detail": {
                    "lookup_type": "curve",
                    "lookup_name": lookup.lookup_name,
                    "series_key": matched_series["series_key"],
                    "direction": "Y2X",
                    "lookup_mode": lookup_mode,
                    "input_value": format(numeric_input, "g"),
                    "hit_type": "exact",
                    "left_point": point,
                    "right_point": point,
                },
            }
    for index in range(len(y_points) - 1):
        left_point = y_points[index]
        right_point = y_points[index + 1]
        if left_point["y"] <= numeric_input <= right_point["y"]:
            ratio = (numeric_input - left_point["y"]) / (right_point["y"] - left_point["y"])
            resolved_value = left_point["x"] + ratio * (right_point["x"] - left_point["x"])
            return {
                "lookup": lookup,
                "value": resolved_value,
                "detail": {
                    "lookup_type": "curve",
                    "lookup_name": lookup.lookup_name,
                    "series_key": matched_series["series_key"],
                    "direction": "Y2X",
                    "lookup_mode": lookup_mode,
                    "input_value": format(numeric_input, "g"),
                    "hit_type": "interpolated",
                    "left_point": left_point,
                    "right_point": right_point,
                },
            }
    raise ParameterLookupValidationError("曲线反查失败，未找到有效区间")


def get_parameter_lookup_config(db, parameter_id):
    return db.query(ParameterLookupConfig).filter(ParameterLookupConfig.parameter_id == parameter_id).first()


def save_parameter_lookup_config(db, parameter_id, data):
    parameter = db.query(ParameterDefinition).filter(ParameterDefinition.id == parameter_id).first()
    if not parameter:
        raise ParameterLookupValidationError("parameter not found")

    lookup_id = int((data or {}).get("lookup_id") or 0)
    input_parameter_id = int((data or {}).get("input_parameter_id") or 0)
    lookup = db.query(ParameterLookupDefinition).filter(ParameterLookupDefinition.id == lookup_id).first()
    if not lookup:
        raise ParameterLookupValidationError("lookup not found")
    input_parameter = db.query(ParameterDefinition).filter(ParameterDefinition.id == input_parameter_id).first()
    if not input_parameter:
        raise ParameterLookupValidationError("input_parameter not found")

    config = get_parameter_lookup_config(db, parameter_id)
    if not config:
        config = ParameterLookupConfig(parameter_id=parameter_id)
        db.add(config)

    config.lookup_id = lookup_id
    config.input_parameter_id = input_parameter_id
    config.base_factor = str((data or {}).get("base_factor") or "1").strip() or "1"
    config.final_expression = (
        str((data or {}).get("final_expression") or "base_factor*lookup_result").strip()
        or "base_factor*lookup_result"
    )
    config.status = str((data or {}).get("status") or "active").strip() or "active"
    db.commit()
    db.refresh(config)
    return config


def get_active_lookup_by_name(db, lookup_name):
    normalized_name = str(lookup_name or "").strip()
    if not normalized_name:
        return None
    return (
        db.query(ParameterLookupDefinition)
        .filter(
            ParameterLookupDefinition.lookup_name == normalized_name,
            ParameterLookupDefinition.status == "active",
        )
        .first()
    )


def resolve_lookup_result_value(db, lookup_name, lookup_key, *, index=2):
    lookup = get_active_lookup_by_name(db, lookup_name)
    if not lookup:
        raise ParameterLookupValidationError(f"附录“{lookup_name}”不存在或已停用")
    if int(index) != 2:
        raise ParameterLookupValidationError("VLOOKUP 首期只支持第 2 列")

    row = (
        db.query(ParameterLookupRow)
        .filter(
            ParameterLookupRow.lookup_id == lookup.id,
            ParameterLookupRow.lookup_key == str(lookup_key).strip(),
        )
        .first()
    )
    if not row:
        raise ParameterLookupValidationError(f"附录“{lookup_name}”未找到键值 {lookup_key}")

    try:
        numeric_value = float(row.result_value)
    except (TypeError, ValueError) as exc:
        raise ParameterLookupValidationError(
            f"附录“{lookup_name}”结果值不是有效数字: {row.result_value}"
        ) from exc

    return {
        "lookup": lookup,
        "row": row,
        "value": numeric_value,
    }
