def build_template_items_from_component_flow(flow_payload):
    items = []
    sort_order = 0

    for step in (flow_payload or {}).get("steps", []):
        rows = (step.get("calculation_content") or {}).get("rows", [])
        for row in rows:
            item_type = "formula_binding" if row.get("formula_id") else "parameter"
            items.append(
                {
                    "item_type": item_type,
                    "item_key": f"{flow_payload.get('flow_name')}::{step.get('step_name')}::{row.get('name')}",
                    "item_name": row.get("name") or "未命名参数",
                    "sort_order": sort_order,
                    "group_path": f"{flow_payload.get('flow_name')}/{step.get('step_name')}",
                    "row_snapshot": row,
                }
            )
            sort_order += 1

    return items
