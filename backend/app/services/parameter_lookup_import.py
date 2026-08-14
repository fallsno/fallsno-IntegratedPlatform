HEADER_KEYWORDS = ("参数", "备注", "参考", "查找值", "结果值")


def _stringify_cell(value):
    return str(value or "").strip()


def _looks_like_header(first_value, second_value):
    combined = f"{first_value} {second_value}"
    return any(keyword in combined for keyword in HEADER_KEYWORDS)


def _should_extract_compact_pairs(sheet_name, rows):
    return any(len(row or []) > 2 for row in (rows or []))


def _build_strict_pairs(rows):
    return [
        (_stringify_cell(row[0] if len(row) > 0 else ""), _stringify_cell(row[1] if len(row) > 1 else ""))
        for row in (rows or [])
    ]


def _build_compact_pairs(rows):
    extracted = []
    for row in rows or []:
        compact_values = [_stringify_cell(value) for value in (row or []) if _stringify_cell(value)]
        if len(compact_values) < 2:
            continue
        first_value, second_value = compact_values[0], compact_values[1]
        if _looks_like_header(first_value, second_value):
            continue
        extracted.append((first_value, second_value))
    return extracted


def _extract_source_table(rows):
    if not rows:
        return [], []

    header_row = None
    header_indexes = []
    header_columns = []

    for row in rows:
        values = [_stringify_cell(value) for value in (row or [])]
        non_empty_indexes = [index for index, value in enumerate(values) if value]
        non_empty_values = [values[index] for index in non_empty_indexes]
        if len(non_empty_values) < 3:
            continue
        if not any(keyword in " ".join(non_empty_values) for keyword in HEADER_KEYWORDS):
            continue
        header_row = values
        header_indexes = non_empty_indexes
        header_columns = non_empty_values
        break

    if not header_columns:
        return [], []

    table_rows = []
    header_found = False
    for row in rows:
        values = [_stringify_cell(value) for value in (row or [])]
        if not header_found:
            if values == header_row:
                header_found = True
            continue

        mapped = {}
        has_any_value = False
        for index, column in zip(header_indexes, header_columns):
            value = values[index] if index < len(values) else ""
            mapped[column] = value
            if value:
                has_any_value = True
        if not has_any_value:
            continue
        table_rows.append(mapped)

    return header_columns, table_rows


def build_parameter_lookup_import_preview(rows, sheet_name=None):
    preview_rows = []
    errors = []
    seen_keys = set()
    pairs = (
        _build_compact_pairs(rows)
        if _should_extract_compact_pairs(sheet_name, rows)
        else _build_strict_pairs(rows)
    )
    for index, (lookup_key, result_value) in enumerate(pairs, start=1):
        if not lookup_key:
            errors.append({"row_no": index, "message": "lookup_key 不能为空"})
            continue
        if lookup_key in seen_keys:
            errors.append({"row_no": index, "message": f"lookup_key 重复: {lookup_key}"})
            continue
        if not result_value:
            errors.append({"row_no": index, "message": "result_value 不能为空"})
            continue
        seen_keys.add(lookup_key)
        preview_rows.append(
            {
                "lookup_key": lookup_key,
                "result_value": result_value,
                "sort_order": len(preview_rows),
                "remark": None,
            }
        )
    table_columns, table_rows = _extract_source_table(rows)
    return {
        "rows": preview_rows,
        "errors": errors,
        "table_columns": table_columns,
        "table_rows": table_rows,
    }
