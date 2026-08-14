import hashlib
import json
from copy import deepcopy
from typing import Any, Dict, Iterable, List


SYNC_MODE_APPEND_MISSING = "append_missing"
SYNC_MODE_OVERWRITE_TEMPLATE_SCOPE = "overwrite_template_scope"
RUNTIME_ROW_FIELDS = ("value", "error", "errorMessage")


def _clone_row_template(row: Dict[str, Any]) -> Dict[str, Any]:
    cloned_row = deepcopy(row or {})
    cloned_row["value"] = ""
    cloned_row["error"] = False
    cloned_row["errorMessage"] = ""
    return cloned_row


def _clone_step_template(step: Dict[str, Any]) -> Dict[str, Any]:
    cloned_step = deepcopy(step or {})
    rows = ((cloned_step.get("calculation_content") or {}).get("rows")) or []
    cloned_step["calculation_content"] = {
        **(cloned_step.get("calculation_content") or {}),
        "rows": [_clone_row_template(row) for row in rows],
    }
    return cloned_step


def _clone_flow_template(flow: Dict[str, Any]) -> Dict[str, Any]:
    cloned_flow = deepcopy(flow or {})
    cloned_flow["steps"] = [_clone_step_template(step) for step in (cloned_flow.get("steps") or [])]
    return cloned_flow


def _index_by_name(items: Iterable[Dict[str, Any]], field_name: str) -> Dict[str, Dict[str, Any]]:
    indexed = {}
    for item in items or []:
        name = str((item or {}).get(field_name) or "").strip()
        if name:
            indexed[name] = item
    return indexed


def _merge_rows(source_rows: List[Dict[str, Any]], target_rows: List[Dict[str, Any]], sync_mode: str) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    stats = {"added_rows": 0, "overwritten_rows": 0}
    source_by_name = _index_by_name(source_rows, "name")
    merged_rows = deepcopy(target_rows or [])

    if sync_mode == SYNC_MODE_OVERWRITE_TEMPLATE_SCOPE:
        result_rows: List[Dict[str, Any]] = []
        used_names = set()
        target_by_name = _index_by_name(target_rows, "name")

        for target_row in target_rows or []:
            row_name = str((target_row or {}).get("name") or "").strip()
            if row_name and row_name in source_by_name:
                result_rows.append(_clone_row_template(source_by_name[row_name]))
                used_names.add(row_name)
                stats["overwritten_rows"] += 1
            else:
                result_rows.append(deepcopy(target_row))

        for source_row in source_rows or []:
            row_name = str((source_row or {}).get("name") or "").strip()
            if row_name and row_name in used_names:
                continue
            result_rows.append(_clone_row_template(source_row))
            stats["added_rows"] += 1

        return result_rows, stats

    target_names = {str((row or {}).get("name") or "").strip() for row in target_rows or [] if str((row or {}).get("name") or "").strip()}
    for source_row in source_rows or []:
        row_name = str((source_row or {}).get("name") or "").strip()
        if row_name and row_name in target_names:
            continue
        merged_rows.append(_clone_row_template(source_row))
        stats["added_rows"] += 1

    return merged_rows, stats


def _merge_steps(source_steps: List[Dict[str, Any]], target_steps: List[Dict[str, Any]], sync_mode: str) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    stats = {"added_steps": 0, "overwritten_steps": 0, "added_rows": 0, "overwritten_rows": 0}
    source_by_name = _index_by_name(source_steps, "step_name")
    target_by_name = _index_by_name(target_steps, "step_name")
    merged_steps: List[Dict[str, Any]] = []
    used_names = set()

    for target_step in target_steps or []:
        step_name = str((target_step or {}).get("step_name") or "").strip()
        if step_name and step_name in source_by_name:
            source_step = source_by_name[step_name]
            source_rows = ((source_step.get("calculation_content") or {}).get("rows")) or []
            target_rows = ((target_step.get("calculation_content") or {}).get("rows")) or []
            merged_rows, row_stats = _merge_rows(source_rows, target_rows, sync_mode)
            merged_step = deepcopy(target_step)

            if sync_mode == SYNC_MODE_OVERWRITE_TEMPLATE_SCOPE:
                merged_step["sort_order"] = source_step.get("sort_order")
                stats["overwritten_steps"] += 1

            merged_step["calculation_content"] = {
                **(merged_step.get("calculation_content") or {}),
                **((source_step.get("calculation_content") or {}) if sync_mode == SYNC_MODE_OVERWRITE_TEMPLATE_SCOPE else {}),
                "rows": merged_rows,
            }
            merged_steps.append(merged_step)
            used_names.add(step_name)
            stats["added_rows"] += row_stats["added_rows"]
            stats["overwritten_rows"] += row_stats["overwritten_rows"]
            continue

        merged_steps.append(deepcopy(target_step))

    for source_step in source_steps or []:
        step_name = str((source_step or {}).get("step_name") or "").strip()
        if step_name and step_name in used_names:
            continue
        merged_steps.append(_clone_step_template(source_step))
        stats["added_steps"] += 1

    return merged_steps, stats


def _merge_flows(source_flows: List[Dict[str, Any]], target_flows: List[Dict[str, Any]], sync_mode: str) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    stats = {
        "added_flows": 0,
        "overwritten_flows": 0,
        "added_steps": 0,
        "overwritten_steps": 0,
        "added_rows": 0,
        "overwritten_rows": 0,
    }
    source_by_name = _index_by_name(source_flows, "flow_name")
    merged_flows: List[Dict[str, Any]] = []
    used_names = set()

    for target_flow in target_flows or []:
        flow_name = str((target_flow or {}).get("flow_name") or "").strip()
        if flow_name and flow_name in source_by_name:
            source_flow = source_by_name[flow_name]
            merged_steps, step_stats = _merge_steps(
                source_flow.get("steps") or [],
                target_flow.get("steps") or [],
                sync_mode,
            )
            merged_flow = deepcopy(target_flow)
            if sync_mode == SYNC_MODE_OVERWRITE_TEMPLATE_SCOPE:
                merged_flow["sort_order"] = source_flow.get("sort_order")
                stats["overwritten_flows"] += 1
            merged_flow["steps"] = merged_steps
            merged_flows.append(merged_flow)
            used_names.add(flow_name)
            for key, value in step_stats.items():
                stats[key] += value
            continue

        merged_flows.append(deepcopy(target_flow))

    for source_flow in source_flows or []:
        flow_name = str((source_flow or {}).get("flow_name") or "").strip()
        if flow_name and flow_name in used_names:
            continue
        merged_flows.append(_clone_flow_template(source_flow))
        stats["added_flows"] += 1

    return merged_flows, stats


def compute_source_signature(source_flows: List[Dict[str, Any]]) -> str:
    payload = json.dumps(source_flows or [], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_sync_result(source_flows: List[Dict[str, Any]], target_flows: List[Dict[str, Any]], sync_mode: str) -> Dict[str, Any]:
    if sync_mode not in {SYNC_MODE_APPEND_MISSING, SYNC_MODE_OVERWRITE_TEMPLATE_SCOPE}:
        raise ValueError(f"不支持的同步策略: {sync_mode}")

    merged_flows, stats = _merge_flows(source_flows or [], target_flows or [], sync_mode)
    return {
        "flows": merged_flows,
        "stats": stats,
        "sync_mode": sync_mode,
        "source_signature": compute_source_signature(source_flows or []),
    }


def summarize_sync_result(sync_result: Dict[str, Any]) -> Dict[str, int]:
    stats = sync_result.get("stats") or {}
    return {
        "added_flows": int(stats.get("added_flows") or 0),
        "updated_steps": int(stats.get("overwritten_steps") or 0),
        "affected_rows": int(stats.get("added_rows") or 0) + int(stats.get("overwritten_rows") or 0),
    }


def select_links_for_resync(source_component_id: int, links: Iterable[Dict[str, Any]], target_component_ids: List[int] | None = None) -> List[Dict[str, Any]]:
    target_component_ids = set(target_component_ids or [])
    selected_links = []

    for link in links or []:
        if link.get("source_component_id") != source_component_id:
            continue
        if target_component_ids and link.get("target_component_id") not in target_component_ids:
            continue
        selected_links.append(deepcopy(link))

    return selected_links
