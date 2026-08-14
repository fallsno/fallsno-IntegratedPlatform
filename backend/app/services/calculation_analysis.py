"""
计算链智能分析服务
==================
职责：
- 解析公式模板（FormulaTemplate）的依赖关系，构建“目标节点 → 影响链”
- 基于已有计算引擎（calculate_workbench_instance）执行多场景、多参数计算
- 计算各输入参数的敏感性贡献（OAT 单因子扰动 + 归一化占比）
- 生成单参数响应曲线、双参数响应面数据

设计约束：
- 不修改原有计算逻辑，复用 workbench 的模板结构解析与计算引擎
- 与工作台执行（POST /workbench/models/{id}/execute）使用同一数据源
"""
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import (
    FormulaTemplate,
    FormulaTemplateItem,
    FormulaTemplateModule,
    FormulaTemplateScene,
    ModelParameterValue,
    ModelVersion,
    ModelWorkbenchConfig,
    ParameterDefinition,
)
from app.services.workbench_calculator import calculate_workbench_instance, safe_eval


class AnalysisError(Exception):
    pass


# ---------------------------------------------------------------------------
# 数据读取（与 workbench.py 同一套模板结构/参数构建逻辑）
# ---------------------------------------------------------------------------

def _parameter_key_candidates(name: str) -> List[str]:
    """生成参数符号等价名，兼容公式中的下划线写法与参数库名称。"""
    raw = str(name or "").strip()
    if not raw:
        return []
    compact = raw.replace("_", "")
    candidates = [raw, compact, raw.replace("_", " "), raw.replace(" ", "_")]
    semantic_aliases = {
        "电机_额定转矩": ["电机额定转矩", "电机扭矩MN", "电机额定扭矩", "电机_额定扭矩"],
        "减速机_减速比": ["减速比i", "减速比", "传动比"],
        "电机_频率": ["电机频率", "电机转速频率", "电机电源频率"],
    }
    for key, aliases in semantic_aliases.items():
        if raw == key or raw in aliases:
            candidates.extend([key, *aliases])
    return list(dict.fromkeys(candidates))


def _resolve_model_param_name(model_params: Dict[str, Dict[str, Any]], name: str) -> Optional[str]:
    for candidate in _parameter_key_candidates(name):
        if candidate in model_params:
            return candidate
    compact = str(name or "").replace("_", "")
    for existing in model_params:
        if str(existing).replace("_", "") == compact:
            return existing
    return None


def _normalize_variables(variables: Any) -> List[str]:
    if isinstance(variables, dict):
        return [str(name).strip() for name in variables.keys() if str(name).strip()]
    if isinstance(variables, list):
        return [str(name).strip() for name in variables if str(name).strip()]
    return []


def _build_template_structure(db: Session, template: FormulaTemplate) -> Dict[str, Any]:
    modules = (
        db.query(FormulaTemplateModule)
        .filter(FormulaTemplateModule.template_id == template.id)
        .order_by(FormulaTemplateModule.sort_order.asc(), FormulaTemplateModule.id.asc())
        .all()
    )
    template_data = {
        "template_id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "modules": [],
    }
    for mod in modules:
        mod_data = {
            "module_id": mod.id,
            "module_name": mod.module_name,
            "module_code": mod.module_code,
            "sort_order": mod.sort_order or 0,
            "scenes": [],
        }
        scenes = (
            db.query(FormulaTemplateScene)
            .filter(FormulaTemplateScene.module_id == mod.id)
            .order_by(FormulaTemplateScene.sort_order.asc(), FormulaTemplateScene.id.asc())
            .all()
        )
        for sc in scenes:
            sc_data = {
                "scene_id": sc.id,
                "scene_name": sc.scene_name,
                "scene_code": sc.scene_code,
                "scene_type": sc.scene_type,
                "sort_order": sc.sort_order or 0,
                "items": [],
            }
            items = (
                db.query(FormulaTemplateItem)
                .filter(FormulaTemplateItem.scene_id == sc.id)
                .order_by(FormulaTemplateItem.sort_order.asc(), FormulaTemplateItem.id.asc())
                .all()
            )
            for it in items:
                sc_data["items"].append(
                    {
                        "item_id": it.id,
                        "formula_name": it.formula_name,
                        "expression": it.expression,
                        "variables": _normalize_variables(it.variables),
                        "unit": it.unit or "",
                        "sort_order": it.sort_order or 0,
                        "description": it.description or "",
                        "resources": it.resources or [],
                        "output_flag": it.output_flag or "auto",
                    }
                )
            mod_data["scenes"].append(sc_data)
        template_data["modules"].append(mod_data)
    return template_data


def _build_model_params(
    db: Session,
    model_id: int,
    override_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Dict[str, Any]]:
    params = (
        db.query(ModelParameterValue, ParameterDefinition)
        .join(ParameterDefinition, ModelParameterValue.parameter_id == ParameterDefinition.id)
        .filter(ModelParameterValue.version_id == model_id)
        .all()
    )
    model_params: Dict[str, Dict[str, Any]] = {}
    for p_val, p_def in params:
        model_params[p_def.param_name] = {
            "value": p_val.param_value,
            "unit": p_def.unit_code or "",
        }
    for name, value in (override_params or {}).items():
        param_name = str(name or "").strip()
        if not param_name:
            continue
        resolved_name = _resolve_model_param_name(model_params, param_name) or param_name
        existing = model_params.get(resolved_name, {})
        model_params[resolved_name] = {
            "value": value,
            "unit": existing.get("unit", ""),
        }
        # 同时保留公式符号别名，使 CURVE2D 扫描值能进入实际计算作用域
        for alias in _parameter_key_candidates(param_name):
            model_params.setdefault(alias, model_params[resolved_name])
    # 初始参数也展开业务符号别名，例如“电机频率”与“电机_频率”
    from app.services.drum_design import _iter_equivalent_symbolic_names
    for existing_name, detail in list(model_params.items()):
        aliases = set(_parameter_key_candidates(existing_name))
        aliases.update(_iter_equivalent_symbolic_names(existing_name))
        for alias in aliases:
            model_params.setdefault(alias, detail)
    return model_params


def load_workbench_context(
    db: Session,
    model_id: int,
    module_code: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """读取型号绑定的模板结构 + 型号参数，等价于工作台执行时的数据源。"""
    config = db.query(ModelWorkbenchConfig).filter(ModelWorkbenchConfig.model_version_id == model_id).first()
    if not config or not config.formula_template_id:
        version = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
        template_id = None
        if version and version.family:
            family = version.family
            if family.default_template_code:
                template = db.query(FormulaTemplate).filter(
                    FormulaTemplate.template_code == family.default_template_code
                ).first()
                if template:
                    template_id = template.id
            if not template_id and family.product_type_id:
                template = db.query(FormulaTemplate).filter(
                    FormulaTemplate.product_type_id == family.product_type_id,
                    FormulaTemplate.is_active == True,
                ).first()
                if template:
                    template_id = template.id
            if not template_id:
                template = db.query(FormulaTemplate).filter(FormulaTemplate.is_active == True).first()
                if template:
                    template_id = template.id
        if template_id:
            if not config:
                config = ModelWorkbenchConfig(model_version_id=model_id, formula_template_id=template_id)
                db.add(config)
            else:
                config.formula_template_id = template_id
            db.commit()
            db.refresh(config)

    if not config or not config.formula_template_id:
        raise AnalysisError("该型号未挂载公式模板")

    template = db.query(FormulaTemplate).filter(FormulaTemplate.id == config.formula_template_id).first()
    if not template:
        raise AnalysisError("绑定的公式模板不存在")

    template_data = _build_template_structure(db, template)
    normalized_module_code = str(module_code or "").strip()
    if normalized_module_code:
        template_data["modules"] = [
            m for m in template_data.get("modules", [])
            if str(m.get("module_code") or "").strip() == normalized_module_code
        ]
        if not template_data["modules"]:
            raise AnalysisError("当前型号下不存在该计算模块")

    model_params = _build_model_params(db, model_id)
    return template_data, model_params


# ---------------------------------------------------------------------------
# 依赖链解析
# ---------------------------------------------------------------------------

def _flatten_items(template_data: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], set]:
    items: Dict[str, Dict[str, Any]] = {}
    formula_names: set = set()
    for module in template_data.get("modules", []):
        for scene in module.get("scenes", []):
            for item in scene.get("items", []):
                name = str(item.get("formula_name") or "").strip()
                if not name:
                    continue
                items[name] = item
                formula_names.add(name)
    return items, formula_names


# 常见常量/函数词，不作为输入参数参与扰动
_NON_PARAM_TOKENS = {"π", "PI", "pi", "E", "e"}

# 公式中出现的保留函数词 / 曲线系列词，不作为变量提取
_RESERVED_TOKENS = {
    "π", "PI", "pi", "E", "e",
    "CURVE2D", "SELECT_EQUIP", "IF",
    "COS", "SIN", "TAN", "SQRT", "ABS", "EXP", "LOG", "LOG10",
    "CURVE", "DRN", "DRS", "X2Y", "Y2X", "LINEAR",
}

_VAR_TOKEN_RE = re.compile(r"[A-Za-z_\u4e00-\u9fa5][A-Za-z0-9_\u4e00-\u9fa5]*")


def _var_names(item: Dict[str, Any]) -> List[str]:
    return [str(v).strip() for v in item.get("variables", []) if str(v or "").strip()]


def _expression_var_names(item: Dict[str, Any], formula_names: Iterable[str]) -> List[str]:
    """从表达式中补漏提取变量（覆盖 CURVE2D 等函数内部的参数引用）。"""
    expr = str(item.get("expression") or "")
    formula_set = set(formula_names)
    # 排除 CURVE2D 表名 / SELECT_EQUIP 分类代码与匹配属性（非数值变量）
    excluded: set = set()
    for m in re.finditer(r"CURVE2D\s*\(\s*([^,\)]+)", expr):
        excluded.add(m.group(1).strip().strip('"\'“”'))
    for m in re.finditer(r"SELECT_EQUIP\s*\(\s*([^,]+)\s*,\s*([^,]+)", expr):
        excluded.add(m.group(1).strip().strip('"\'“”'))
        excluded.add(m.group(2).strip().strip('"\'“”'))
    found: List[str] = []
    for token in _VAR_TOKEN_RE.findall(expr):
        upper = token.upper()
        if upper in _RESERVED_TOKENS:
            continue
        if token in formula_set or token in excluded:
            continue
        if token not in found:
            found.append(token)
    return found


def _collect_chain_formulas(items: Dict[str, Dict[str, Any]], target: str) -> List[str]:
    """从目标节点向上回溯，收集全部上游公式（后序：被依赖的公式在前，目标在最后）。"""
    formula_names = set(items.keys())
    visited: set = set()
    order: List[str] = []

    def dfs(name: str) -> None:
        if name in visited:
            return
        visited.add(name)
        item = items[name]
        referenced = set(_var_names(item)) | set(_expression_var_names(item, formula_names))
        for var in referenced:
            if var in items and var != name:
                dfs(var)
        order.append(name)

    dfs(target)
    return order


def _curve_input_range(db: Optional[Session], items: Dict[str, Dict[str, Any]], chain: List[str], param_name: str) -> Optional[Tuple[float, float]]:
    if db is None:
        return None
    from app.models import ParameterLookupDefinition
    from app.services.parameter_lookup_catalog import get_parameter_lookup_curve_profile
    aliases = set(_parameter_key_candidates(param_name))
    for fname in chain:
        expression = str(items[fname].get("expression") or "")
        match = re.search(r"CURVE2D\s*\(\s*([^,]+)\s*,\s*([^,]+)", expression, re.IGNORECASE)
        if not match or match.group(2).strip() not in aliases:
            continue
        lookup_name = match.group(1).strip().strip('"\'“”')
        lookup = db.query(ParameterLookupDefinition).filter(
            ParameterLookupDefinition.lookup_name == lookup_name,
            ParameterLookupDefinition.status == "active",
        ).order_by(ParameterLookupDefinition.id.desc()).first()
        if not lookup:
            continue
        profile = get_parameter_lookup_curve_profile(db, lookup.id)
        rows = profile.get("table_rows") or []
        axis = profile.get("x_axis_column")
        values = []
        for row in rows:
            try:
                values.append(float(row.get(axis)))
            except (TypeError, ValueError):
                pass
        if values:
            return min(values), max(values)
    return None


def _suggest_range(value: Any) -> Tuple[float, float]:
    try:
        v = float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        v = 0.0
    if not v or abs(v) < 1e-12:
        return (0.0, 1.0)
    span = abs(v) * 0.2
    return (round(v - span, 6), round(v + span, 6))


def build_chain_analysis(
    template_data: Dict[str, Any],
    model_params: Dict[str, Dict[str, Any]],
    target_node: str,
    db: Session = None,
) -> Dict[str, Any]:
    """构建目标节点的完整影响链分析模型。"""
    items, formula_names = _flatten_items(template_data)
    target_node = str(target_node or "").strip()
    if not target_node:
        # 自动选择最丰富的目标节点：优先选输入参数最多的公式，
        # 避免默认选到仅含选型参数的叶子节点（如"输出转速"只有 3 个选型参数）。
        # 按输入参数数降序排列，取第一个。
        used_vars = {v for item in items.values() for v in _var_names(item)}
        # 先排除纯选型参数的叶子节点
        endpoints = [n for n in items if n not in used_vars]
        if endpoints:
            candidates = []
            for fname in items:
                chain_f = _collect_chain_formulas(items, fname)
                input_set: set = set()
                for f in chain_f:
                    item = items[f]
                    for var in _var_names(item):
                        if var in items or var in _NON_PARAM_TOKENS:
                            continue
                        input_set.add(var)
                    for var in _expression_var_names(item, formula_names):
                        if var in items or var in _NON_PARAM_TOKENS:
                            continue
                        input_set.add(var)
                candidates.append((fname, len(input_set)))
            candidates.sort(key=lambda x: -x[1])
            target_node = candidates[0][0]
        else:
            target_node = list(items)[-1]
    if target_node not in items:
        raise AnalysisError(f"目标节点“{target_node}”不存在")

    # 1. 上游公式链（被依赖在前，目标在后）
    chain = _collect_chain_formulas(items, target_node)

    # 2. 输入参数 = 链中公式引用的、非公式结果的叶子变量
    #    （variables 字段 + 表达式补漏，覆盖 CURVE2D 内部参数引用）
    input_names: set = set()
    for fname in chain:
        item = items[fname]
        for var in _var_names(item):
            if var in items or var in _NON_PARAM_TOKENS:
                continue
            input_names.add(var)
        for var in _expression_var_names(item, formula_names):
            if var in items or var in _NON_PARAM_TOKENS:
                continue
            input_names.add(var)
    input_names = sorted(input_names)

    # 3. 计算层级：输入=0，公式=1+max(上游公式层级)
    levels: Dict[str, int] = {}
    for fname in chain:
        lvl = 0
        for var in _var_names(items[fname]):
            if var in items and var in levels:
                lvl = max(lvl, levels[var])
        levels[fname] = lvl + 1

    # 4. 执行一次基准计算，填充节点当前值
    results = calculate_workbench_instance(template_data, model_params, db=db)

    def _node_value(name: str) -> Any:
        detail = results.get(name)
        return detail.get("value") if isinstance(detail, dict) else None

    # 5. 节点列表：输入参数（level 0）→ 公式节点（按 level 升序）
    nodes: List[Dict[str, Any]] = []
    for name in input_names:
        detail = model_params.get(name, {})
        value = detail.get("value") if isinstance(detail, dict) else detail
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = None
        nodes.append({
            "name": name,
            "kind": "input",
            "level": 0,
            "value": numeric,
            "unit": detail.get("unit", "") if isinstance(detail, dict) else "",
        })
    for fname in chain:
        nodes.append({
            "name": fname,
            "kind": "formula",
            "level": levels.get(fname, 1),
            "expression": items[fname].get("expression", ""),
            "unit": items[fname].get("unit", ""),
            "value": _node_value(fname),
            "is_target": fname == target_node,
        })

    # 6. 边：变量 → 引用它的公式
    edges: List[Dict[str, str]] = []
    chain_set = set(chain)
    for fname in chain:
        for var in _var_names(items[fname]):
            if var in input_names or var in chain_set:
                edges.append({"from": var, "to": fname})

    # 7. 输入参数范围建议（前端可编辑）
    inputs: List[Dict[str, Any]] = []
    for name in input_names:
        detail = model_params.get(name, {})
        raw_value = detail.get("value") if isinstance(detail, dict) else detail
        try:
            base_value = float(raw_value)
        except (TypeError, ValueError):
            # 未绑定参数：计算引擎兜底值为 1.0，范围建议也基于 1.0，避免 0 值注入导致除零
            base_value = 1.0
        curve_range = _curve_input_range(db, items, chain, name)
        lo, hi = curve_range or _suggest_range(base_value)
        inputs.append({
            "name": name,
            "value": base_value,
            "min": lo,
            "max": hi,
            "step": round((hi - lo) / 10.0, 6),
            "unit": detail.get("unit", "") if isinstance(detail, dict) else "",
        })

    # 8. 可用目标节点（所有公式结果，供前端选择）
    available_targets = [
        {"name": name, "unit": items[name].get("unit", ""), "expression": items[name].get("expression", "")}
        for name in formula_names
    ]
    available_targets.sort(key=lambda x: x["name"])

    return {
        "target_node": target_node,
        "available_targets": available_targets,
        "inputs": inputs,
        "nodes": nodes,
        "edges": edges,
        "chain_formulas": chain,
        "input_names": input_names,
    }


# ---------------------------------------------------------------------------
# 计算执行（统一入口：复用 workbench 计算引擎）
# ---------------------------------------------------------------------------

def _apply_overrides(
    model_params: Dict[str, Dict[str, Any]],
    overrides: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    params = {name: dict(detail) for name, detail in model_params.items()}
    from app.services.drum_design import _iter_equivalent_symbolic_names
    for name, value in overrides.items():
        if value is None:
            continue
        resolved_name = _resolve_model_param_name(params, str(name)) or str(name).strip()
        existing = params.get(resolved_name, {})
        updated = {"value": value, "unit": existing.get("unit", "")}
        aliases = set(_parameter_key_candidates(str(name)))
        aliases.update(_iter_equivalent_symbolic_names(str(name)))
        aliases.add(resolved_name)
        for alias in aliases:
            params[alias] = updated
    return params


def _run_calculation(
    template_data: Dict[str, Any],
    model_params: Dict[str, Dict[str, Any]],
    overrides: Optional[Dict[str, Any]] = None,
    db: Session = None,
) -> Dict[str, Dict[str, Any]]:
    try:
        return calculate_workbench_instance(
            template_data,
            _apply_overrides(model_params, overrides or {}),
            db=db,
        )
    except Exception:
        # 单点计算失败（除零、查表异常等）：返回空结果，由调用方决定断点或跳过
        return {}


# ---------------------------------------------------------------------------
# 多场景计算
# ---------------------------------------------------------------------------

def run_scenarios(
    template_data: Dict[str, Any],
    model_params: Dict[str, Dict[str, Any]],
    target_node: str,
    scenarios: List[Dict[str, Any]],
    db: Session = None,
) -> Dict[str, Any]:
    """对多个设计方案执行全链计算，返回每个场景下所有节点的值。"""
    if not scenarios:
        raise AnalysisError("至少需要一个设计场景")

    outputs: List[Dict[str, Any]] = []
    for sc in scenarios:
        name = str(sc.get("name") or "未命名场景").strip()
        overrides = sc.get("parameters") or {}
        results = _run_calculation(template_data, model_params, overrides, db=db)
        nodes: Dict[str, Dict[str, Any]] = {}
        for fname, detail in results.items():
            nodes[fname] = {
                "value": detail.get("value"),
                "unit": detail.get("unit", ""),
            }
        outputs.append({
            "name": name,
            "target_value": nodes.get(target_node, {}).get("value"),
            "nodes": nodes,
        })

    return {
        "target_node": target_node,
        "scenarios": outputs,
    }


# ---------------------------------------------------------------------------
# 敏感性分析（OAT 单因子扰动 + 归一化贡献占比）
# ---------------------------------------------------------------------------

def compute_sensitivity(
    template_data: Dict[str, Any],
    model_params: Dict[str, Dict[str, Any]],
    target_node: str,
    inputs: List[Dict[str, Any]],
    db: Session = None,
) -> Dict[str, Any]:
    """计算每个输入参数在 [min, max] 范围内对目标结果的贡献占比。

    方法：单因子扰动（One-At-a-Time）。
    对每个参数取 min 与 max 各算一次目标值，|Δ结果| 即为该参数的效应，
    再对所有参数效应归一化为 100% 占比。
    """
    if not inputs:
        raise AnalysisError("请至少选择一个输入参数")

    base_results = _run_calculation(template_data, model_params, db=db)
    base_value = base_results.get(target_node, {}).get("value")

    contributions: List[Dict[str, Any]] = []
    for inp in inputs:
        name = str(inp.get("name") or "").strip()
        try:
            lo = float(inp.get("min"))
            hi = float(inp.get("max"))
        except (TypeError, ValueError):
            raise AnalysisError(f"参数“{name}”的取值范围无效")
        if hi < lo:
            lo, hi = hi, lo

        try:
            r_lo = _run_calculation(template_data, model_params, {name: lo}, db=db).get(target_node, {}).get("value", 0.0)
            r_hi = _run_calculation(template_data, model_params, {name: hi}, db=db).get(target_node, {}).get("value", 0.0)
        except Exception:
            # 单点计算失败（如除零、查表异常）时跳过该参数，避免整次分析中断
            contributions.append({
                "name": name,
                "min": lo,
                "max": hi,
                "min_result": None,
                "max_result": None,
                "base_result": base_value,
                "delta": 0.0,
                "error": "该参数范围内计算失败，已跳过",
            })
            continue
        try:
            delta = abs(float(r_hi) - float(r_lo))
        except (TypeError, ValueError):
            delta = 0.0

        contributions.append({
            "name": name,
            "min": lo,
            "max": hi,
            "min_result": r_lo,
            "max_result": r_hi,
            "base_result": base_value,
            "delta": round(delta, 8),
        })

    total = sum(c["delta"] for c in contributions)
    for c in contributions:
        c["contribution"] = round(c["delta"] / total * 100.0, 2) if total > 0 else 0.0
    contributions.sort(key=lambda c: -c["contribution"])

    return {
        "target_node": target_node,
        "base_result": base_value,
        "total_delta": round(total, 8),
        "contributions": contributions,
    }


# ---------------------------------------------------------------------------
# 单参数响应曲线
# ---------------------------------------------------------------------------

def _linspace(start: float, end: float, num: int) -> List[float]:
    if num <= 1:
        return [start]
    return [round(start + (end - start) * i / (num - 1), 8) for i in range(num)]


def compute_response_curve(
    template_data: Dict[str, Any],
    model_params: Dict[str, Dict[str, Any]],
    target_node: str,
    param: str,
    min_val: float,
    max_val: float,
    steps: int = 21,
    track_intermediate: bool = True,
    db: Session = None,
) -> Dict[str, Any]:
    """单参数扫描，返回目标结果曲线以及中间节点变化序列。"""
    try:
        lo = float(min_val)
        hi = float(max_val)
    except (TypeError, ValueError):
        raise AnalysisError("扫描范围无效")
    if hi < lo:
        lo, hi = hi, lo
    steps = max(2, min(int(steps or 21), 101))

    items, _ = _flatten_items(template_data)
    chain_set = set(_collect_chain_formulas(items, target_node))
    chain_set.discard(target_node)

    xs = _linspace(lo, hi, steps)
    ys: List[Any] = []
    intermediates: Dict[str, List[Any]] = {}

    for x in xs:
        results = _run_calculation(template_data, model_params, {param: x}, db=db)
        ys.append(results.get(target_node, {}).get("value"))
        if track_intermediate:
            for fname in chain_set:
                detail = results.get(fname)
                if detail is not None:
                    intermediates.setdefault(fname, []).append(detail.get("value"))

    series = [
        {"name": fname, "values": values}
        for fname, values in intermediates.items()
    ]

    return {
        "target_node": target_node,
        "param": param,
        "x": xs,
        "y": ys,
        "series": series,
    }


# ---------------------------------------------------------------------------
# 双参数响应面
# ---------------------------------------------------------------------------

def compute_response_surface(
    template_data: Dict[str, Any],
    model_params: Dict[str, Dict[str, Any]],
    target_node: str,
    param1: str,
    param2: str,
    range1: Dict[str, float],
    range2: Dict[str, float],
    grid: int = 15,
) -> Dict[str, Any]:
    """双参数组合网格计算，返回响应面矩阵 z[i][j] = f(x_i, y_j)。"""
    if param1 == param2:
        raise AnalysisError("响应面的两个参数不能相同")
    try:
        x_lo, x_hi = float(range1["min"]), float(range1["max"])
        y_lo, y_hi = float(range2["min"]), float(range2["max"])
    except (TypeError, KeyError, ValueError):
        raise AnalysisError("响应面取值范围无效")
    grid = max(4, min(int(grid or 15), 25))

    xs = _linspace(x_lo, x_hi, grid)
    ys = _linspace(y_lo, y_hi, grid)
    z: List[List[Any]] = []
    for xi in xs:
        row: List[Any] = []
        for yi in ys:
            results = _run_calculation(template_data, model_params, {param1: xi, param2: yi})
            row.append(results.get(target_node, {}).get("value"))
        z.append(row)

    return {
        "target_node": target_node,
        "param1": param1,
        "param2": param2,
        "x": xs,
        "y": ys,
        "z": z,
    }
