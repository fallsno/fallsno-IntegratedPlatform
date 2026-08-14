import ast
import math
import re
from typing import Any, Callable, Dict, Iterable, Tuple


SYMBOL_REPLACEMENTS: Tuple[Tuple[str, str], ...] = (
    ('（', '('),
    ('）', ')'),
    ('【', '('),
    ('】', ')'),
    ('［', '('),
    ('］', ')'),
    ('｛', '('),
    ('｝', ')'),
    ('，', ','),
    ('、', ','),
    ('；', ';'),
    ('：', ':'),
    ('＋', '+'),
    ('－', '-'),
    ('–', '-'),
    ('—', '-'),
    ('×', '*'),
    ('÷', '/'),
    ('％', '%'),
    ('π', 'pi'),
)

FUNCTION_ALIASES = {
    'COS': 'cos',
    'SIN': 'sin',
    'TAN': 'tan',
    'ACOS': 'acos',
    'ASIN': 'asin',
    'ATAN': 'atan',
    'ABS': 'abs',
    'SQRT': 'sqrt',
    'LOG': 'log10',
    'LN': 'log',
    'EXP': 'exp',
    'POW': 'pow',
    'MIN': 'min',
    'MAX': 'max',
    'ROUND': 'round',
    'FLOOR': 'floor',
    'CEIL': 'ceil',
}

SAFE_FUNCTIONS = {
    'abs': abs,
    'acos': math.acos,
    'asin': math.asin,
    'atan': math.atan,
    'ceil': math.ceil,
    'cos': math.cos,
    'exp': math.exp,
    'floor': math.floor,
    'log': math.log,
    'log10': math.log10,
    'max': max,
    'min': min,
    'pow': pow,
    'round': round,
    'sin': math.sin,
    'sqrt': math.sqrt,
    'tan': math.tan,
    'pi': math.pi,
    'e': math.e,
}

RESERVED_IDENTIFIERS = set(SAFE_FUNCTIONS.keys())
EXCEL_FUNCTION_NAMES = ('VLOOKUP', 'HLOOKUP', 'IF', 'IFERROR')
CURVE_FUNCTION_NAMES = ('CURVE2D',)
EQUIP_FUNCTION_NAMES = ('SELECT_EQUIP',)
SPECIAL_FUNCTION_NAMES = (*EXCEL_FUNCTION_NAMES, *CURVE_FUNCTION_NAMES, *EQUIP_FUNCTION_NAMES)
SAFE_NODE_TYPES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.FloorDiv,
    ast.USub,
    ast.UAdd,
)


class FormulaEngineError(Exception):
    def __init__(self, code: str, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


def _is_number_literal(token: str) -> bool:
    try:
        float(str(token).strip())
        return True
    except (TypeError, ValueError):
        return False


def _format_lookup_key(value: Any) -> str:
    numeric_value = float(value)
    if numeric_value.is_integer():
        return str(int(numeric_value))
    return format(numeric_value, 'g')


def _replace_segment(expression: str, start: int, end: int, replacement: str) -> str:
    return f'{expression[:start]}{replacement}{expression[end:]}'


def _split_function_args(text: str) -> list[str]:
    args = []
    current = []
    depth = 0
    for char in str(text or ''):
        if char == ',' and depth == 0:
            args.append(''.join(current).strip())
            current = []
            continue
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        current.append(char)
    if current:
        args.append(''.join(current).strip())
    return args


def _parse_lookup_reference(token: str) -> tuple[str, str]:
    matched = re.fullmatch(
        r'(?P<name>[\u00C0-\uFFFFA-Za-z0-9_]+)!(?P<range>\$?[A-Z]+\$?(?::\$?[A-Z]+\$?)?)',
        str(token or '').strip(),
    )
    if not matched:
        raise FormulaEngineError('FUNCTION_ARGUMENT_INVALID', f'非法附录引用: {token}')
    return matched.group('name'), matched.group('range')


def normalize_formula_expression(expression: Any) -> str:
    normalized = str(expression or '').strip()
    if normalized.startswith('='):
        normalized = normalized[1:].strip()

    for source, target in SYMBOL_REPLACEMENTS:
        normalized = normalized.replace(source, target)

    normalized = re.sub(r'\bPI\b', 'pi', normalized, flags=re.IGNORECASE)

    for alias, canonical in FUNCTION_ALIASES.items():
        normalized = re.sub(
            rf'\b{alias}\b(?=\s*\()',
            canonical,
            normalized,
            flags=re.IGNORECASE,
        )

    normalized = re.sub(r'\s*([+\-*/^%,()])\s*', r'\1', normalized)
    return normalized.strip()


def _replace_known_variables(expression: str, scope: Dict[str, Any], available_variable_names: Iterable[str], default_missing_value: float = 0.0) -> Tuple[str, Dict[str, Any]]:
    explicit_variables = {name for name in [*available_variable_names, *scope.keys()] if name}

    processed_expression = expression
    mapped_scope: Dict[str, Any] = {}
    
    extracted_tokens = []
    for match in re.finditer(r'([A-Za-z_\u00C0-\uFFFF][A-Za-z0-9_\u00C0-\uFFFF]*)\s*(\()?', processed_expression):
        if not match.group(2):
            extracted_tokens.append(match.group(1))

    all_variable_tokens = {
        token for token in extracted_tokens
        if token not in RESERVED_IDENTIFIERS and not re.fullmatch(r'__var_\d+__', token)
    }

    variable_names = sorted(
        explicit_variables | all_variable_tokens,
        key=len,
        reverse=True,
    )

    for index, variable_name in enumerate(variable_names):
        if variable_name not in processed_expression:
            continue

        if variable_name not in scope:
            # 隐式注册：凡是合法的可用变量，若作用域缺失，自动补齐默认值
            scope[variable_name] = default_missing_value

        safe_identifier = f'__var_{index}__'
        processed_expression = processed_expression.replace(variable_name, safe_identifier)
        mapped_scope[safe_identifier] = scope[variable_name]

    return processed_expression.replace('^', '**'), mapped_scope


def _validate_ast(node: ast.AST) -> None:
    for child in ast.walk(node):
        if not isinstance(child, SAFE_NODE_TYPES):
            raise FormulaEngineError('SYNTAX_ERROR', f'不支持的表达式语法: {type(child).__name__}')

        if isinstance(child, ast.Call):
            if not isinstance(child.func, ast.Name) or child.func.id not in SAFE_FUNCTIONS:
                raise FormulaEngineError('FUNCTION_UNKNOWN', f'未知函数: {ast.unparse(child.func)}')

        if isinstance(child, ast.Name) and child.id not in SAFE_FUNCTIONS and not re.fullmatch(r'__var_\d+__', child.id):
            raise FormulaEngineError('VARIABLE_UNDEFINED', f'变量未定义: {child.id}')


def _format_number(value: float, precision: int) -> str:
    return format(round(value, precision), 'g')


def _resolve_token_value(
    token: str,
    scope: Dict[str, Any],
    *,
    available_variable_names: Iterable[str] | None = None,
    lookup_resolver: Callable[[str, str, int, bool], Any] | None = None,
    curve_resolver: Callable[[str, Any, str, str, str], Any] | None = None,
    equipment_resolver: Callable[[str, str], Any] | None = None,
    precision: int = 4,
    default_missing_value: float = 0.0,
):
    normalized = str(token or '').strip()
    if _is_number_literal(normalized):
        return float(normalized)
    normalized_upper = normalized.upper()
    if normalized_upper == 'TRUE':
        return 'TRUE'
    if normalized_upper == 'FALSE':
        return 'FALSE'
    if normalized in scope:
        return scope[normalized]
    result = evaluate_formula_expression(
        normalized,
        scope,
        available_variable_names=available_variable_names or scope.keys(),
        precision=precision,
        lookup_resolver=lookup_resolver,
        curve_resolver=curve_resolver,
        equipment_resolver=equipment_resolver,
        default_missing_value=default_missing_value,
    )
    return result['value']


def _evaluate_condition(
    expression: str,
    scope: Dict[str, Any],
    *,
    available_variable_names: Iterable[str] | None = None,
    lookup_resolver: Callable[[str, str, int, bool], Any] | None = None,
    curve_resolver: Callable[[str, Any, str, str, str], Any] | None = None,
    equipment_resolver: Callable[[str, str], Any] | None = None,
    precision: int = 4,
    default_missing_value: float = 0.0,
) -> bool:
    condition = str(expression or '').strip()
    for operator in ('>=', '<=', '<>', '>', '<', '='):
        if operator not in condition:
            continue
        left_text, right_text = condition.split(operator, 1)
        left = _resolve_token_value(
            left_text,
            scope,
            available_variable_names=available_variable_names,
            lookup_resolver=lookup_resolver,
            curve_resolver=curve_resolver,
            equipment_resolver=equipment_resolver,
            precision=precision,
            default_missing_value=default_missing_value,
        )
        right = _resolve_token_value(
            right_text,
            scope,
            available_variable_names=available_variable_names,
            lookup_resolver=lookup_resolver,
            curve_resolver=curve_resolver,
            equipment_resolver=equipment_resolver,
            precision=precision,
            default_missing_value=default_missing_value,
        )
        if operator == '>=':
            return left >= right
        if operator == '<=':
            return left <= right
        if operator == '<>':
            return left != right
        if operator == '>':
            return left > right
        if operator == '<':
            return left < right
        return left == right
    return bool(
        _resolve_token_value(
            condition,
            scope,
            available_variable_names=available_variable_names,
            lookup_resolver=lookup_resolver,
            curve_resolver=curve_resolver,
            equipment_resolver=equipment_resolver,
            precision=precision,
            default_missing_value=default_missing_value,
        )
    )


def _replace_one_excel_function(
    expression: str,
    scope: Dict[str, Any],
    *,
    available_variable_names: Iterable[str] | None = None,
    lookup_resolver: Callable[[str, str, int, bool], Any] | None = None,
    curve_resolver: Callable[[str, Any, str, str, str], Any] | None = None,
    equipment_resolver: Callable[[str, str], Any] | None = None,
    precision: int = 4,
    default_missing_value: float = 0.0,
) -> str:
    for index, char in enumerate(expression):
        if char != '(':
            continue
        name_end = index
        name_start = name_end - 1
        while name_start >= 0 and re.fullmatch(r'[A-Za-z0-9_]', expression[name_start]):
            name_start -= 1
        function_name = expression[name_start + 1:name_end].upper()
        if function_name not in SPECIAL_FUNCTION_NAMES:
            continue

        depth = 1
        close_index = index
        while close_index + 1 < len(expression) and depth > 0:
            close_index += 1
            if expression[close_index] == '(':
                depth += 1
            elif expression[close_index] == ')':
                depth -= 1
        if depth != 0:
            raise FormulaEngineError('SYNTAX_ERROR', f'{function_name} 括号未闭合')

        function_start = name_start + 1
        raw_args = expression[index + 1:close_index]
        args = _split_function_args(raw_args)

        if function_name in ('VLOOKUP', 'HLOOKUP'):
            if len(args) != 4:
                raise FormulaEngineError('FUNCTION_ARGUMENT_INVALID', f'{function_name} 需要 4 个参数')
            lookup_value = _resolve_token_value(args[0], scope, available_variable_names=available_variable_names, lookup_resolver=lookup_resolver, precision=precision, default_missing_value=default_missing_value)
            lookup_name, _range_ref = _parse_lookup_reference(args[1])
            result_index = int(
                float(
                    _resolve_token_value(
                        args[2],
                        scope,
                        available_variable_names=available_variable_names,
                        lookup_resolver=lookup_resolver,
                        curve_resolver=curve_resolver,
                        precision=precision,
                        default_missing_value=default_missing_value,
                    )
                )
            )
            range_mode_value = _resolve_token_value(
                args[3],
                scope,
                available_variable_names=available_variable_names,
                lookup_resolver=lookup_resolver,
                curve_resolver=curve_resolver,
                precision=precision,
                default_missing_value=default_missing_value,
            )
            if isinstance(range_mode_value, (int, float)):
                range_mode = '0' if float(range_mode_value) == 0 else format(float(range_mode_value), 'g')
            else:
                range_mode = str(range_mode_value).strip().upper()
            if result_index != 2:
                raise FormulaEngineError('LOOKUP_COLUMN_INVALID', f'{function_name} 首期只支持第 2 列')
            if range_mode not in {'0', 'FALSE'}:
                raise FormulaEngineError('LOOKUP_RANGE_MODE_INVALID', f'{function_name} 首期只支持精确匹配 0/FALSE')
            if lookup_resolver is None:
                raise FormulaEngineError('LOOKUP_NOT_FOUND', f'附录“{lookup_name}”不可用')
            resolved = float(lookup_resolver(lookup_name, _format_lookup_key(lookup_value), result_index, True))
            return _replace_segment(expression, function_start, close_index + 1, format(resolved, 'g'))

        if function_name == 'CURVE2D':
            if len(args) != 5:
                raise FormulaEngineError('FUNCTION_ARGUMENT_INVALID', 'CURVE2D 需要 5 个参数')
            lookup_name = str(args[0] or '').strip()
            if not lookup_name:
                raise FormulaEngineError('FUNCTION_ARGUMENT_INVALID', 'CURVE2D 缺少曲线表')
            input_value = _resolve_token_value(
                args[1],
                scope,
                available_variable_names=available_variable_names,
                lookup_resolver=lookup_resolver,
                curve_resolver=curve_resolver,
                precision=precision,
                default_missing_value=default_missing_value,
            )
            series_key = str(args[2] or '').strip()
            direction = str(args[3] or '').strip().upper()
            lookup_mode = str(args[4] or '').strip().upper()
            if direction not in {'X2Y', 'Y2X'}:
                raise FormulaEngineError('CURVE_DIRECTION_INVALID', f'CURVE2D 不支持的查值方向: {direction}')
            if lookup_mode != 'LINEAR':
                raise FormulaEngineError('CURVE_LOOKUP_MODE_INVALID', f'CURVE2D 不支持的查值方式: {lookup_mode}')
            if curve_resolver is None:
                raise FormulaEngineError('CURVE_PROFILE_MISSING', f'曲线表“{lookup_name}”不可用')
            resolved = curve_resolver(lookup_name, input_value, series_key, direction, lookup_mode)
            if isinstance(resolved, dict):
                resolved_value = resolved.get('value')
            else:
                resolved_value = resolved
            return _replace_segment(expression, function_start, close_index + 1, format(float(resolved_value), 'g'))

        if function_name == 'SELECT_EQUIP':
            if len(args) != 3:
                raise FormulaEngineError('FUNCTION_ARGUMENT_INVALID', 'SELECT_EQUIP 需要 3 个参数: (分类代码, 匹配属性, 目标值)')
            category_code = str(args[0] or '').strip().strip('"\'')
            match_property = str(args[1] or '').strip().strip('"\'')
            target_value = _resolve_token_value(
                args[2],
                scope,
                available_variable_names=available_variable_names,
                lookup_resolver=lookup_resolver,
                curve_resolver=curve_resolver,
                equipment_resolver=equipment_resolver,
                precision=precision,
            )
            if equipment_resolver is None:
                raise FormulaEngineError('EQUIPMENT_RESOLVER_MISSING', '设备选型解析器不可用')
            
            resolved = equipment_resolver(category_code, match_property, target_value)
            if isinstance(resolved, dict):
                resolved_value = resolved.get('value')
            else:
                resolved_value = resolved
            return _replace_segment(expression, function_start, close_index + 1, format(float(resolved_value), 'g'))

        if function_name == 'IF':
            args = _split_function_args(raw_args)
            if len(args) != 3:
                raise FormulaEngineError('FUNCTION_ARGUMENT_INVALID', 'IF 需要 3 个参数')
            branch = (
                args[1]
                if _evaluate_condition(
                    args[0],
                    scope,
                    available_variable_names=available_variable_names,
                    lookup_resolver=lookup_resolver,
                    curve_resolver=curve_resolver,
                    precision=precision,
                )
                else args[2]
            )
            value = _resolve_token_value(
                branch,
                scope,
                available_variable_names=available_variable_names,
                lookup_resolver=lookup_resolver,
                curve_resolver=curve_resolver,
                precision=precision,
            )
            if isinstance(value, str) and not _is_number_literal(value):
                raise FormulaEngineError('RESULT_INVALID', f'IF 返回的结果不是有效数字: {value}')
            return _replace_segment(expression, function_start, close_index + 1, format(float(value), 'g'))

        if len(args) != 2:
            raise FormulaEngineError('FUNCTION_ARGUMENT_INVALID', 'IFERROR 需要 2 个参数')
        try:
            value = _resolve_token_value(
                args[0],
                scope,
                available_variable_names=available_variable_names,
                lookup_resolver=lookup_resolver,
                curve_resolver=curve_resolver,
                precision=precision,
            )
        except FormulaEngineError:
            value = _resolve_token_value(
                args[1],
                scope,
                available_variable_names=available_variable_names,
                lookup_resolver=lookup_resolver,
                curve_resolver=curve_resolver,
                precision=precision,
            )
        return _replace_segment(expression, function_start, close_index + 1, format(float(value), 'g'))
    return expression


def _resolve_excel_functions(
    expression: str,
    scope: Dict[str, Any],
    *,
    available_variable_names: Iterable[str] | None = None,
    lookup_resolver: Callable[[str, str, int, bool], Any] | None = None,
    curve_resolver: Callable[[str, Any, str, str, str], Any] | None = None,
    equipment_resolver: Callable[[str, str, Any], Any] | None = None,
    precision: int = 4,
    default_missing_value: float = 0.0,
) -> str:
    resolved = expression
    while any(f'{name}(' in resolved.upper() for name in SPECIAL_FUNCTION_NAMES):
        next_expression = _replace_one_excel_function(
            resolved,
            scope,
            available_variable_names=available_variable_names,
            lookup_resolver=lookup_resolver,
            curve_resolver=curve_resolver,
            equipment_resolver=equipment_resolver,
            precision=precision,
            default_missing_value=default_missing_value,
        )
        if next_expression == resolved:
            break
        resolved = next_expression
    return resolved


def evaluate_formula_expression(
    expression: Any,
    scope: Dict[str, Any] | None = None,
    *,
    available_variable_names: Iterable[str] | None = None,
    precision: int = 4,
    lookup_resolver: Callable[[str, str, int, bool], Any] | None = None,
    curve_resolver: Callable[[str, Any, str, str, str], Any] | None = None,
    equipment_resolver: Callable[[str, str, Any], Any] | None = None,
    default_missing_value: float = 0.0,
) -> Dict[str, Any]:
    normalized_expression = normalize_formula_expression(expression)
    if not normalized_expression:
        return {
            'value': None,
            'formatted_value': '',
            'normalized_expression': '',
            'processed_expression': '',
            'mapped_scope': {},
        }

    scope = scope or {}
    available_variable_names = available_variable_names or []
    excel_ready_expression = _resolve_excel_functions(
        normalized_expression,
        scope,
        available_variable_names=available_variable_names,
        lookup_resolver=lookup_resolver,
        curve_resolver=curve_resolver,
        equipment_resolver=equipment_resolver,
        precision=precision,
        default_missing_value=default_missing_value,
    )
    processed_expression, mapped_scope = _replace_known_variables(
        excel_ready_expression,
        scope,
        available_variable_names,
        default_missing_value=default_missing_value,
    )

    try:
        parsed = ast.parse(processed_expression, mode='eval')
    except SyntaxError as exc:
        raise FormulaEngineError('SYNTAX_ERROR', f'表达式格式错误: {exc.msg}') from exc

    _validate_ast(parsed)

    try:
        value = eval(compile(parsed, '<formula>', 'eval'), {'__builtins__': {}}, {**SAFE_FUNCTIONS, **mapped_scope})
    except FormulaEngineError as exc:
        raise
    except Exception as exc:
        raise FormulaEngineError('EVALUATION_ERROR', f'公式计算失败: {exc}') from exc

    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise FormulaEngineError('RESULT_INVALID', '计算结果不是有效数字', {'value': value})

    numeric_value = float(value)
    return {
        'value': numeric_value,
        'formatted_value': _format_number(numeric_value, precision),
        'normalized_expression': normalized_expression,
        'processed_expression': processed_expression,
        'mapped_scope': mapped_scope,
    }
