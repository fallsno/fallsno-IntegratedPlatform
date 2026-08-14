class DesignGuidanceValidationError(ValueError):
    pass


ACTION_TEMPLATES = {
    ("template_sync", "high"): [
        {
            "action_code": "template_sync_review_scope",
            "action_label": "复核模板差异并确认覆盖范围",
            "action_type": "review",
            "priority": "high",
        },
        {
            "action_code": "template_sync_compare_target",
            "action_label": "执行重同步前再次比对目标部件",
            "action_type": "verify",
            "priority": "high",
        },
    ],
    ("parameter_import", "warning"): [
        {
            "action_code": "parameter_import_check_mapping",
            "action_label": "核对参数编码与分类",
            "action_type": "review",
            "priority": "medium",
        }
    ],
    ("workbench", "high"): [
        {
            "action_code": "workbench_rerun_formula",
            "action_label": "复核求解输入并重跑公式",
            "action_type": "rerun",
            "priority": "high",
        }
    ],
}

ALLOWED_ACTION_STATUSES = {"open", "in_progress", "resolved", "dismissed"}


def normalize_rule_hit_payload(data):
    payload = data or {}
    source_type = str(payload.get("source_type") or "").strip()
    target_type = str(payload.get("target_type") or "").strip()
    message = str(payload.get("message") or "").strip()
    target_id = int(payload.get("target_id") or 0)
    if not source_type:
        raise DesignGuidanceValidationError("source_type 不能为空")
    if not target_type:
        raise DesignGuidanceValidationError("target_type 不能为空")
    if not target_id:
        raise DesignGuidanceValidationError("target_id 不能为空")
    if not message:
        raise DesignGuidanceValidationError("message 不能为空")
    return {
        "source_type": source_type,
        "target_type": target_type,
        "target_id": target_id,
        "severity": str(payload.get("severity") or "warning").strip() or "warning",
        "message": message,
        "suggestion": str(payload.get("suggestion") or "").strip() or None,
        "status": str(payload.get("status") or "open").strip() or "open",
        "hit_snapshot": payload.get("hit_snapshot") or None,
    }


def build_guidance_actions(hit_payload):
    payload = hit_payload or {}
    source_type = str(payload.get("source_type") or "").strip()
    severity = str(payload.get("severity") or "warning").strip() or "warning"
    templates = ACTION_TEMPLATES.get((source_type, severity)) or ACTION_TEMPLATES.get(
        (source_type, "warning")
    ) or [
        {
            "action_code": f"{source_type or 'guidance'}_review_hit",
            "action_label": "复核命中信息并确认后续处理动作",
            "action_type": "review",
            "priority": "medium",
        }
    ]
    return [
        {
            **item,
            "status": "open",
            "result_note": None,
            "result_snapshot": None,
        }
        for item in templates
    ]


def normalize_guidance_action_update(data):
    payload = data or {}
    status = str(payload.get("status") or "").strip()
    if status not in ALLOWED_ACTION_STATUSES:
        raise DesignGuidanceValidationError("status 非法")
    return {
        "status": status,
        "result_note": str(payload.get("result_note") or "").strip() or None,
        "result_snapshot": payload.get("result_snapshot") or None,
    }


def derive_rule_hit_status(actions):
    action_rows = list(actions or [])
    if not action_rows:
        return "open"
    if any(
        str((row or {}).get("status") or "open").strip() in {"open", "in_progress"}
        for row in action_rows
    ):
        return "open"
    return "resolved"


def build_guidance_summary(rows, action_rows=None):
    rows = list(rows or [])
    action_rows = list(action_rows or [])
    severity_stats = {"high": 0, "warning": 0, "info": 0}
    source_stats = {}
    open_hits = 0
    for row in rows:
        current = row or {}
        severity = str(current.get("severity") or "warning").strip() or "warning"
        severity_stats[severity] = severity_stats.get(severity, 0) + 1
        source_type = str(current.get("source_type") or "unknown").strip() or "unknown"
        source_stats[source_type] = source_stats.get(source_type, 0) + 1
        if str(current.get("status") or "open").strip() != "resolved":
            open_hits += 1
    action_open_count = sum(
        1
        for row in action_rows
        if str((row or {}).get("status") or "open").strip() in {"open", "in_progress"}
    )
    action_resolved_count = sum(
        1
        for row in action_rows
        if str((row or {}).get("status") or "").strip() in {"resolved", "dismissed"}
    )
    return {
        "total_hits": len(rows),
        "open_hits": open_hits,
        "severity_stats": severity_stats,
        "source_stats": source_stats,
        "action_open_count": action_open_count,
        "action_resolved_count": action_resolved_count,
    }
