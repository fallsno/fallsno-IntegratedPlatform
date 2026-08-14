import re
from copy import deepcopy
from typing import Any, Dict

from app.services.formula_engine import RESERVED_IDENTIFIERS


IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_\u00C0-\uFFFF][A-Za-z0-9_\u00C0-\uFFFF]*")


class FormulaLibraryValidationError(ValueError):
    pass


def _extract_expression_variables(expression: Any) -> list[str]:
    tokens = IDENTIFIER_PATTERN.findall(str(expression or ""))
    ordered_tokens: list[str] = []

    for token in tokens:
        if token in RESERVED_IDENTIFIERS or token in ordered_tokens:
            continue
        ordered_tokens.append(token)

    return ordered_tokens


def _normalize_solve_target(target_key: str, target_data: Any) -> Dict[str, Any]:
    if not isinstance(target_data, dict):
        raise FormulaLibraryValidationError(f"solve_targets.{target_key} 必须是对象")

    expression = str(target_data.get("expression") or "").strip()
    if not expression:
        raise FormulaLibraryValidationError(f"solve_targets.{target_key}.expression 不能为空")

    required_variables = target_data.get("required_variables") or []
    if not isinstance(required_variables, list):
        raise FormulaLibraryValidationError(
            f"solve_targets.{target_key}.required_variables 必须是数组"
        )

    normalized_required_variables = [
        str(item).strip() for item in required_variables if str(item).strip()
    ]
    expected_variables = _extract_expression_variables(expression)

    if set(normalized_required_variables) != set(expected_variables):
        raise FormulaLibraryValidationError(
            "solve_targets."
            f"{target_key}.required_variables 与表达式变量不一致，"
            f"应为 {expected_variables}"
        )

    return {
        "expression": expression,
        "required_variables": normalized_required_variables,
        "description": str(target_data.get("description") or "").strip(),
    }


def validate_formula_payload(payload: Dict[str, Any] | None, *, partial: bool = False) -> Dict[str, Any]:
    data = deepcopy(payload or {})

    if not partial:
        if not str(data.get("name") or "").strip():
            raise FormulaLibraryValidationError("公式名称不能为空")
        if not str(data.get("expression") or "").strip():
            raise FormulaLibraryValidationError("公式表达式不能为空")

    if "canonical_expression" in data and data["canonical_expression"] is not None:
        data["canonical_expression"] = str(data["canonical_expression"]).strip() or None

    if "solve_targets" in data or not partial:
        solve_targets = data.get("solve_targets") or {}
        if not isinstance(solve_targets, dict):
            raise FormulaLibraryValidationError("solve_targets 必须是对象")

        normalized_targets = {
            str(target_key).strip(): _normalize_solve_target(str(target_key).strip(), target_data)
            for target_key, target_data in solve_targets.items()
            if str(target_key).strip()
        }
        data["solve_targets"] = normalized_targets

    return data


def serialize_formula_record(record: Any) -> Dict[str, Any]:
    return {
        "id": getattr(record, "id", None),
        "name": getattr(record, "name", None),
        "expression": getattr(record, "expression", None),
        "variables": getattr(record, "variables", None),
        "description": getattr(record, "description", None),
        "category": getattr(record, "category", None),
        "canonical_expression": getattr(record, "canonical_expression", None),
        "solve_targets": getattr(record, "solve_targets", None) or {},
    }
