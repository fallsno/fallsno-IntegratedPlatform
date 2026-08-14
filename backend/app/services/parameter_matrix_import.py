import re

from app.models import ModelVersion


ORIENTATION_ROWS = "parameters_in_rows"
ORIENTATION_COLUMNS = "parameters_in_columns"
RT_ALIAS_PATTERN = re.compile(r"^RT(\d+)$", re.IGNORECASE)
HTS_ALIAS_PATTERN = re.compile(r"^HTS(\d+)$", re.IGNORECASE)
GTR_ALIAS_PATTERN = re.compile(r"^GTR(\d+)$", re.IGNORECASE)
IMPORT_VERSION_SPECS = [
    {
        "version_code": "RT300",
        "family_codes": ["RT"],
        "aliases": ["RT300", "再生300"],
    },
    {
        "version_code": "HTS300",
        "family_codes": ["HTS"],
        "aliases": ["HTS300", "全再生300", "逆流式全再生滚筒", "逆流式再生滚筒"],
    },
    {
        "version_code": "AT240R.0",
        "family_codes": ["AT240R.0"],
        "aliases": ["AT240R.0", "2100311314", "GT240GF1.0"],
    },
    {
        "version_code": "RTS200.0",
        "family_codes": ["RTS200.0"],
        "aliases": ["RTS200.0", "2100414159", "GTRS200B.0", "顺流式再生滚筒"],
    },
    {
        "version_code": "HTS200.0",
        "family_codes": ["HTS200.0"],
        "aliases": ["HTS200.0", "2100469939", "GTRQ200.0", "逆流式全再生滚筒", "逆流式再生滚筒"],
    },
    {
        "version_code": "CTD70G.0",
        "family_codes": ["CTD70G.0"],
        "aliases": ["CTD70G.0", "2100363399", "GFT70Y.0", "双回程干燥冷却滚筒"],
    },
    {
        "version_code": "CTS70G.0",
        "family_codes": ["CTS70G.0"],
        "aliases": ["CTS70G.0", "新图", "单回程干燥冷却滚筒"],
    },
    {
        "version_code": "MT500.0",
        "family_codes": ["MT500.0"],
        "aliases": ["MT500.0", "2100464327", "GTL500A.0", "连续式干燥搅拌滚筒"],
    },
    {
        "version_code": "ST25100.0",
        "family_codes": ["ST25100.0"],
        "aliases": ["ST25100.0", "2100452514", "GTS25100.0", "滚筒筛"],
    },
    {
        "version_code": "WT200.0",
        "family_codes": ["WT200.0"],
        "aliases": ["WT200.0", "2100421831", "JSJ200A.0", "加湿机200", "加湿筒"],
    },
]


def _stringify(cell):
    return str("" if cell is None else cell).strip()


def _normalize_rows(rows):
    normalized = []
    for row in rows or []:
        if not isinstance(row, (list, tuple)):
            continue
        normalized.append([_stringify(cell) for cell in row])
    return normalized


def _trim_trailing_empty(values):
    items = list(values or [])
    while items and not _stringify(items[-1]):
        items.pop()
    return items


def _normalize_version_token(value):
    return re.sub(r"[\s\-_/]+", "", _stringify(value)).upper()


def _build_version_alias_tokens(version_code):
    normalized_code = _stringify(version_code)
    token = _normalize_version_token(normalized_code)
    aliases = {token}

    rt_match = RT_ALIAS_PATTERN.match(token)
    if rt_match:
        aliases.add(_normalize_version_token(f"再生{rt_match.group(1)}"))

    hts_match = HTS_ALIAS_PATTERN.match(token)
    if hts_match:
        aliases.add(_normalize_version_token(f"全再生{hts_match.group(1)}"))

    gtr_match = GTR_ALIAS_PATTERN.match(token)
    if gtr_match:
        aliases.add(_normalize_version_token(f"GTR{gtr_match.group(1)}"))

    return aliases


def get_import_version_spec(version_code):
    original_code = _stringify(version_code)
    normalized_code = _normalize_version_token(original_code)
    for item in IMPORT_VERSION_SPECS:
        if _normalize_version_token(item["version_code"]) == normalized_code:
            return item
    if RT_ALIAS_PATTERN.match(normalized_code):
        return {"version_code": original_code, "family_codes": ["RT"], "aliases": [original_code]}
    if HTS_ALIAS_PATTERN.match(normalized_code):
        return {"version_code": original_code, "family_codes": ["HTS"], "aliases": [original_code]}
    if GTR_ALIAS_PATTERN.match(normalized_code):
        return {"version_code": original_code, "family_codes": ["GTR"], "aliases": [original_code]}
    return None


def _build_import_alias_map():
    alias_map = {}
    for item in IMPORT_VERSION_SPECS:
        target_code = item["version_code"]
        alias_map[_normalize_version_token(target_code)] = target_code
        for alias in item["aliases"]:
            normalized_alias = _normalize_version_token(alias)
            if normalized_alias:
                alias_map[normalized_alias] = target_code
    return alias_map


def _load_known_version_codes(db):
    rows = db.query(ModelVersion.version_code, ModelVersion.display_name).all() if db else []
    alias_map = {}
    for row in rows:
        version_code = _stringify(row[0])
        display_name = _stringify(row[1])
        if not version_code:
            continue
        for alias in _build_version_alias_tokens(version_code):
            alias_map[alias] = version_code
        if display_name:
            alias_map[_normalize_version_token(display_name)] = version_code
    alias_map.update(_build_import_alias_map())
    return alias_map


def _match_version_code(label, known_versions):
    return known_versions.get(_normalize_version_token(label), "")


def _score_version_axis(labels, known_versions):
    cleaned = [_stringify(item) for item in labels if _stringify(item)]
    if not cleaned:
        return (-1, 0, 0)
    hits = [_match_version_code(item, known_versions) for item in cleaned]
    hits = [item for item in hits if item]
    unique_hits = len(set(hits))
    density = len(hits) / max(len(cleaned), 1)
    return (unique_hits, len(hits), density)


def _score_parameter_axis(labels, known_versions):
    cleaned = [_stringify(item) for item in labels if _stringify(item)]
    if not cleaned:
        return (-1, -1, -1)
    text_count = sum(1 for item in cleaned if not item.replace(".", "", 1).replace("-", "", 1).isdigit())
    version_penalty = sum(1 for item in cleaned if _match_version_code(item, known_versions))
    duplicate_penalty = len(cleaned) - len(set(cleaned))
    return (text_count, -version_penalty, -duplicate_penalty)


def _detect_version_axis(normalized_rows, known_versions, orientation_hint="auto"):
    if not normalized_rows:
        return ORIENTATION_ROWS, 0

    num_rows = len(normalized_rows)
    num_cols = max(len(row) for row in normalized_rows) if normalized_rows else 0

    best_row_score = (-2, 0, 0)
    best_row_index = 0
    for row_idx in range(min(3, num_rows)):
        score = _score_version_axis(normalized_rows[row_idx], known_versions)
        if score > best_row_score:
            best_row_score = score
            best_row_index = row_idx

    best_col_score = (-2, 0, 0)
    best_col_index = 0
    for col_idx in range(min(3, num_cols)):
        col_values = [normalized_rows[r][col_idx] if len(normalized_rows[r]) > col_idx else "" for r in range(num_rows)]
        score = _score_version_axis(col_values, known_versions)
        if score > best_col_score:
            best_col_score = score
            best_col_index = col_idx

    if orientation_hint == ORIENTATION_ROWS:
        return ORIENTATION_ROWS, best_row_index
    elif orientation_hint == ORIENTATION_COLUMNS:
        return ORIENTATION_COLUMNS, best_col_index

    row_is_better = best_row_score[0] > best_col_score[0] or (
        best_row_score[0] == best_col_score[0] and best_row_score[1] >= best_col_score[1]
    )

    if row_is_better and best_row_score[0] > 0:
        return ORIENTATION_ROWS, best_row_index
    elif best_col_score[0] > 0:
        return ORIENTATION_COLUMNS, best_col_index
    else:
        return ORIENTATION_ROWS, 0


def _extract_row_metadata(row, parameter_index, known_versions):
    category_name = _stringify(row[parameter_index - 1]) if parameter_index - 1 >= 0 else ""
    unit_code = ""
    for candidate in row[parameter_index + 1 :]:
        value = _stringify(candidate)
        if not value or _match_version_code(value, known_versions):
            continue
        if len(value) <= 12:
            unit_code = value
            break
    return category_name, unit_code


def _build_row_oriented_preview(normalized_rows, known_versions, version_row_index=0):
    if not normalized_rows:
        return {
            "orientation": ORIENTATION_ROWS,
            "parameter_headers": [],
            "version_headers": [],
            "rows": [],
            "warnings": ["未读取到可识别的数据行"],
        }

    header_row = _trim_trailing_empty(normalized_rows[version_row_index])
    version_pairs = []
    seen_codes = set()
    for idx, cell in enumerate(header_row):
        version_code = _match_version_code(cell, known_versions)
        if not version_code or version_code in seen_codes:
            continue
        version_pairs.append((idx, version_code))
        seen_codes.add(version_code)
    version_indexes = [idx for idx, _ in version_pairs]

    if not version_indexes:
        return {
            "orientation": ORIENTATION_ROWS,
            "parameter_headers": [],
            "version_headers": [],
            "rows": [],
            "warnings": ["未识别到可用的型号列，请确保Excel中包含系统中已存在的型号编码"],
        }

    version_headers = [version_code for _, version_code in version_pairs]
    first_version_index = version_indexes[0]

    parameter_index = 0
    best_parameter_score = (-1, -1, -1)
    for idx in range(first_version_index):
        candidate_col = [
            normalized_rows[r][idx] if len(normalized_rows[r]) > idx else ""
            for r in range(version_row_index, len(normalized_rows))
        ]
        score = _score_parameter_axis(candidate_col, known_versions)
        if score > best_parameter_score:
            best_parameter_score = score
            parameter_index = idx

    warnings = []
    unknown_headers = [
        _stringify(header_row[idx])
        for idx in range(first_version_index, len(header_row))
        if _stringify(header_row[idx]) and not _match_version_code(header_row[idx], known_versions)
    ]
    if unknown_headers:
        warnings.append(f"存在未命中系统型号的表头值，已跳过: {', '.join(unknown_headers)}")

    preview_rows = []
    current_category = ""
    for raw_row in normalized_rows[version_row_index + 1 :]:
        row = list(raw_row) + [""] * max(0, len(header_row) - len(raw_row))
        param_name = _stringify(row[parameter_index] if len(row) > parameter_index else "")

        if not param_name:
            continue

        category_candidate, unit_code = _extract_row_metadata(row, parameter_index, known_versions)
        if category_candidate:
            current_category = category_candidate

        values = {
            version_code: _stringify(row[col_idx] if len(row) > col_idx else "")
            for col_idx, version_code in version_pairs
        }

        preview_rows.append(
            {
                "param_name": param_name,
                "unit_code": unit_code,
                "category_name": current_category,
                "values": values,
            }
        )

    return {
        "orientation": ORIENTATION_ROWS,
        "parameter_headers": [row["param_name"] for row in preview_rows],
        "version_headers": version_headers,
        "rows": preview_rows,
        "warnings": warnings,
    }


def _build_column_oriented_preview(normalized_rows, known_versions, version_col_index=0):
    if not normalized_rows:
        return {
            "orientation": ORIENTATION_COLUMNS,
            "parameter_headers": [],
            "version_headers": [],
            "rows": [],
            "warnings": ["未读取到可识别的数据行"],
        }

    version_codes = []
    for r in range(len(normalized_rows)):
        cell = normalized_rows[r][version_col_index] if len(normalized_rows[r]) > version_col_index else ""
        code = _match_version_code(cell, known_versions)
        if code and code not in {item[1] for item in version_codes}:
            version_codes.append((r, code))

    if not version_codes:
        return {
            "orientation": ORIENTATION_COLUMNS,
            "parameter_headers": [],
            "version_headers": [],
            "rows": [],
            "warnings": ["未识别到可用的型号行，请确保Excel中包含系统中已存在的型号编码"],
        }

    version_row_indexes = [r for r, _ in version_codes]
    version_headers = [code for _, code in version_codes]

    num_cols = max(len(row) for row in normalized_rows) if normalized_rows else 0
    parameter_indexes = []
    for col_idx in range(num_cols):
        if col_idx == version_col_index:
            continue
        col_values = [normalized_rows[r][col_idx] if len(normalized_rows[r]) > col_idx else "" for r in range(len(normalized_rows))]
        score = _score_parameter_axis(col_values, known_versions)
        if score[0] > 0:
            parameter_indexes.append(col_idx)

    if not parameter_indexes:
        parameter_indexes = [
            idx for idx in range(num_cols) if idx != version_col_index
        ]

    warnings = []
    preview_rows = []

    for col_idx in parameter_indexes:
        param_name = _stringify(normalized_rows[0][col_idx] if len(normalized_rows[0]) > col_idx else "")
        if not param_name:
            continue

        values = {}
        for r, version_code in version_codes:
            value = _stringify(normalized_rows[r][col_idx] if len(normalized_rows[r]) > col_idx else "")
            values[version_code] = value

        preview_rows.append(
            {
                "param_name": param_name,
                "unit_code": "",
                "category_name": "",
                "values": values,
            }
        )

    return {
        "orientation": ORIENTATION_COLUMNS,
        "parameter_headers": [row["param_name"] for row in preview_rows],
        "version_headers": version_headers,
        "rows": preview_rows,
        "warnings": warnings,
    }


def build_parameter_matrix_preview(db, rows, orientation_hint="auto"):
    normalized_rows = _normalize_rows(rows)
    known_versions = _load_known_version_codes(db)
    orientation, version_axis_index = _detect_version_axis(
        normalized_rows,
        known_versions,
        orientation_hint=orientation_hint,
    )
    if orientation == ORIENTATION_ROWS:
        return _build_row_oriented_preview(
            normalized_rows,
            known_versions,
            version_row_index=version_axis_index,
        )
    return _build_column_oriented_preview(
        normalized_rows,
        known_versions,
        version_col_index=version_axis_index,
    )
