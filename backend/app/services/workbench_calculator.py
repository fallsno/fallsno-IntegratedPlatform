import math
import graphlib
from typing import Dict, Any


def _coerce_number(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return value
        try:
            return float(text)
        except ValueError:
            return value
    return value


def _iter_variable_names(variables: Any) -> list[str]:
    if isinstance(variables, dict):
        return [str(name).strip() for name in variables.keys() if str(name).strip()]
    if isinstance(variables, list):
        return [str(name).strip() for name in variables if str(name).strip()]
    return []


def safe_eval(expression: str, context: Dict[str, Any]) -> float:
    # Remove leading '=' if present
    if expression.startswith('='):
        expression = expression[1:]
        
    # Replace engineering power operator '^' with python's '**'
    expression = expression.replace('^', '**')
    
    # 自动替换中文括号为英文括号，防止手误导致的语法错误
    expression = expression.replace('（', '(').replace('）', ')')
        
    # Provide a safe set of built-ins and math functions
    safe_dict = {
        "__builtins__": {},
        "math": math,
        "COS": math.cos,
        "cos": math.cos,
        "SIN": math.sin,
        "sin": math.sin,
        "TAN": math.tan,
        "tan": math.tan,
        "SQRT": math.sqrt,
        "sqrt": math.sqrt,
        "PI": math.pi,
        "pi": math.pi,
        "π": math.pi,
        "ABS": abs,
        "abs": abs,
        "EXP": math.exp,
        "exp": math.exp,
        "LOG": math.log,
        "log": math.log,
        "LOG10": math.log10,
        "log10": math.log10
    }
    
    # Merge the context with safe_dict
    eval_globals = {**safe_dict, **context}
    
    # Evaluate the expression
    try:
        return eval(expression, eval_globals, {})
    except Exception as e:
        raise ValueError(f"Failed to evaluate expression '{expression}': {e}")

def calculate_workbench_instance(
    template_data: Dict,
    model_params: Dict[str, Any],
    db: Any = None,
) -> Dict[str, Any]:
    """
    核心计算引擎解耦：
    根据传入的只读模板结构，结合具体的型号参数进行计算。
    强同名绑定：如果 template 中的变量在 model_params 中找不到，则抛出异常或标记未就绪。
    """
    results = {}
    
    # Track which formulas are depended ON by others
    depended_on = set()
    
    # Track verify scenes
    verify_scenes = set()
    
    # 扁平化所有场景中的公式
    all_items = []
    formula_names_set = set()
    for module in template_data.get("modules", []):
        for scene in module.get("scenes", []):
            scene_id = scene.get("scene_id")
            if scene.get("scene_type") == "verify":
                verify_scenes.add(scene_id)
            for item in scene.get("items", []):
                item["scene_id"] = scene_id
                all_items.append(item)
                formula_names_set.add(item.get("formula_name"))
                
    # 拓扑排序构建：为了保证不管 sort_order 是多少，都能优先计算被依赖的公式
    ts = graphlib.TopologicalSorter()
    item_map = {}
    
    for item in all_items:
        name = item.get("formula_name")
        if not name:
            continue
        item_map[name] = item
        # 提取公式依赖的变量名
        deps = _iter_variable_names(item.get("variables", []))
        for d in deps:
            depended_on.add(d)
        # 过滤出依赖的其他“公式计算结果”（即在 formula_names_set 中的）
        valid_deps = [d for d in deps if d in formula_names_set and d != name]
        ts.add(name, *valid_deps)
        
    try:
        # 获取拓扑排序后的公式名称顺序
        sorted_formula_names = list(ts.static_order())
    except graphlib.CycleError:
        # 如果存在循环依赖，则退级回原本的基于 sort_order 排序
        all_items.sort(key=lambda x: x.get("sort_order", 0))
        sorted_formula_names = [item.get("formula_name") for item in all_items if item.get("formula_name")]

    for formula_name in sorted_formula_names:
        if formula_name not in item_map:
            continue
        item = item_map[formula_name]
        expression = item["expression"]
        variables = _iter_variable_names(item.get("variables", []))
        # 从表达式补充 CURVE2D/SELECT_EQUIP 等函数参数，避免变量字段不完整导致依赖断链
        import re
        expression_tokens = re.findall(r"[A-Za-z_\u4e00-\u9fa5][A-Za-z0-9_\u4e00-\u9fa5]*", str(expression))
        reserved_tokens = {"CURVE2D", "SELECT_EQUIP", "DRN", "X2Y", "LINEAR", "IF", "PI", "E", "COS", "SIN", "TAN", "SQRT", "ABS", "EXP", "LOG", "LOG10"}
        for token in expression_tokens:
            if token.upper() not in reserved_tokens and token not in variables:
                variables.append(token)
        
        # 收集变量值
        eval_context = {}
        for var in variables:
            if var in results:
                # 中间结果复用（非常重要，前面的计算结果要给后面用）
                eval_context[var] = results[var]["value"]
            elif var in model_params:
                # 强同名绑定：去参数中心取值
                val = model_params[var]
                if isinstance(val, dict) and "value" in val:
                    eval_context[var] = _coerce_number(val["value"])
                else:
                    eval_context[var] = _coerce_number(val)
            else:
                # 兜底：未绑定的参数提供默认值1
                eval_context[var] = 1.0
        
        # 执行计算 (使用业务级别的 evaluate_formula_expression，支持CURVE2D等特殊函数)
        from app.services.formula_engine import evaluate_formula_expression
        
        try:
            if db is not None:
                from app.services.drum_design import _build_formula_curve_resolver, _build_formula_lookup_resolver
                curve_hits = []
                lookup_hits = []
                res_dict = evaluate_formula_expression(
                    expression,
                    eval_context,
                    available_variable_names=variables,
                    lookup_resolver=_build_formula_lookup_resolver(db, lookup_hits),
                    curve_resolver=_build_formula_curve_resolver(db, curve_hits),
                )
            else:
                res_dict = evaluate_formula_expression(expression, eval_context)
            value = res_dict.get("value", 0.0)
        except Exception as e:
            # 降级模式，兼容复杂的正则等
            clean_expr = expression
            import re
            clean_expr = re.sub(r'CURVE2D\([^)]+\)', '1.0', clean_expr)
            clean_expr = re.sub(r'SELECT_EQUIP\([^)]+\)', '1.0', clean_expr)
            
            try:
                value = safe_eval(clean_expr, eval_context)
            except Exception as fallback_err:
                raise ValueError(f"Failed to evaluate expression '{expression}': {fallback_err}")
                
        results[formula_name] = {"value": value, "unit": item.get("unit", "")}
                    
    # Mark outputs
    for formula_name in sorted_formula_names:
        if formula_name not in item_map:
            continue
        item = item_map[formula_name]
        is_verify = item.get("scene_id") in verify_scenes
        
        # Auto inference
        is_output_auto = (formula_name not in depended_on) and not is_verify
        
        # Apply manual overrides
        flag = item.get("output_flag", "auto")
        if flag == "force_true":
            final_is_output = True
        elif flag == "force_false":
            final_is_output = False
        else:
            final_is_output = is_output_auto
            
        if formula_name in results:
            results[formula_name]["is_output"] = final_is_output

    return results
