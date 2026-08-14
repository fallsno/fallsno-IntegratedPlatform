import re


class ParameterCatalogValidationError(ValueError):
    pass


_BLOCKED_PARAM_CODE_PATTERNS = (
    r".*_TEST$",
    r"^MN_PRIMARY_",
    r"^MN_SECONDARY_",
    r"^MOTOR_INPUT_PRIMARY_",
    r"^MOTOR_INPUT_SECONDARY_",
    r"^MN_RT300_",
    r"^MOTOR_FREQ_RT300_",
    r"^WB-AUTO-",
)


def is_blocked_parameter_identity(param_code="", param_name=""):
    code = str(param_code or "").strip()
    name = str(param_name or "").strip()
    if any(re.match(pattern, code, re.IGNORECASE) for pattern in _BLOCKED_PARAM_CODE_PATTERNS):
        return True
    if re.fullmatch(r"[0-9]{6,}[A-Za-z0-9_]*", name):
        return True
    return False


def normalize_parameter_payload(data):
    code = str((data or {}).get("param_code") or "").strip()
    name = str((data or {}).get("param_name") or "").strip()
    if not code:
        raise ParameterCatalogValidationError("param_code 不能为空")
    if not name:
        raise ParameterCatalogValidationError("param_name 不能为空")
    if is_blocked_parameter_identity(code, name):
        raise ParameterCatalogValidationError("禁止创建测试参数或随机占位参数")

    display_name = str((data or {}).get("display_name") or name).strip() or name
    category_code = str((data or {}).get("category_code") or "uncategorized").strip() or "uncategorized"
    value_type = str((data or {}).get("value_type") or "basic").strip() or "basic"
    data_type = str((data or {}).get("data_type") or "number").strip() or "number"
    status = str((data or {}).get("status") or "active").strip() or "active"
    unit_code = str((data or {}).get("unit_code") or "").strip() or None
    precision = int((data or {}).get("precision") or 2)
    default_value = (data or {}).get("default_value")
    description = str((data or {}).get("description") or "").strip() or None

    return {
        "param_code": code,
        "param_name": name,
        "display_name": display_name,
        "category_code": category_code,
        "value_type": value_type,
        "data_type": data_type,
        "unit_code": unit_code,
        "precision": precision,
        "default_value": None if default_value is None else str(default_value),
        "description": description,
        "status": status,
    }
