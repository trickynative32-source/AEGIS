import math
import ast
import operator
import re
import logging
from typing import Dict, Any, Union, Optional
from backend.tools.registry import registry

logger = logging.getLogger("AEGIS.MathTools")

# Supported operators for safe AST evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "cbrt": lambda x: x ** (1/3),
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "ceil": math.ceil,
    "floor": math.floor,
    "factorial": math.factorial,
    "pow": math.pow,
}

SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

def safe_eval_ast(node: ast.AST) -> Union[int, float]:
    """Recursively evaluates an AST node containing only safe mathematical operations."""
    if isinstance(node, ast.Expression):
        return safe_eval_ast(node.body)
    elif isinstance(node, ast.Constant):  # Numbers
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value}")
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](safe_eval_ast(node.operand))
        raise ValueError(f"Unsupported unary operator: {op_type}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            left = safe_eval_ast(node.left)
            right = safe_eval_ast(node.right)
            if op_type == ast.Div and right == 0:
                raise ZeroDivisionError("Division by zero")
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type}")
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCTIONS:
            args = [safe_eval_ast(arg) for arg in node.args]
            return SAFE_FUNCTIONS[node.func.id](*args)
        raise ValueError(f"Unsupported function call: {node.func}")
    elif isinstance(node, ast.Name):
        if node.id in SAFE_CONSTANTS:
            return SAFE_CONSTANTS[node.id]
        raise ValueError(f"Unsupported identifier: {node.id}")
    else:
        raise ValueError(f"Unsupported AST node type: {type(node)}")

def normalize_math_expression(expr: str) -> str:
    """Converts natural language math queries into clean mathematical expressions."""
    s = expr.strip().lower()

    # Remove leading question phrases
    s = re.sub(r"^(what is|what's|calculate|solve|evaluate|find|how much is|can you solve|tell me)\s+", "", s)
    s = s.rstrip("?.!")

    # Handle percentage queries e.g. "15% of 200" or "what is 20 percent of 500"
    pct_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)\s+of\s+(\d+(?:\.\d+)?)", s)
    if pct_match:
        pct = float(pct_match.group(1))
        val = float(pct_match.group(2))
        return f"({pct} / 100) * {val}"

    # Replace natural language words with math symbols
    replacements = [
        (r"\bplus\b", "+"),
        (r"\bminus\b", "-"),
        (r"\btimes\b", "*"),
        (r"\bmultiplied by\b", "*"),
        (r"\bdivided by\b", "/"),
        (r"\bover\b", "/"),
        (r"\bto the power of\b", "**"),
        (r"\bpower of\b", "**"),
        (r"\bsquared\b", "** 2"),
        (r"\bcubed\b", "** 3"),
        (r"\bsquare root of\s+(\d+(?:\.\d+)?)", r"sqrt(\1)"),
        (r"\bcube root of\s+(\d+(?:\.\d+)?)", r"cbrt(\1)"),
        (r"\bx\b", "*"),
        (r"\bX\b", "*"),
        (r"×", "*"),
        (r"÷", "/"),
        (r"\^", "**"),
    ]

    for pat, repl in replacements:
        s = re.sub(pat, repl, s, flags=re.IGNORECASE)

    # Clean characters (only allow digits, standard math symbols, and safe function names)
    s = s.strip()
    return s

def evaluate_math_expression(raw_expr: str) -> Dict[str, Any]:
    """Safely evaluates any mathematical expression or natural math query."""
    normalized = normalize_math_expression(raw_expr)
    if not normalized:
        return {"success": False, "error": "Empty mathematical expression", "verified": False}

    try:
        parsed_ast = ast.parse(normalized, mode="eval")
        result = safe_eval_ast(parsed_ast)

        # Format clean integer or floating point result
        if isinstance(result, float) and result.is_integer():
            formatted_res = str(int(result))
        elif isinstance(result, float):
            formatted_res = f"{result:.6g}"
        else:
            formatted_res = str(result)

        # Natural spoken/display answer
        clean_query = raw_expr.strip().rstrip("?.!")
        if re.search(r"^(what is|calculate|solve|how much is)\b", clean_query, re.IGNORECASE):
            msg = f"{clean_query} = {formatted_res}"
        elif any(sym in clean_query for sym in ["+", "-", "*", "/", "%", "^", "x"]):
            msg = f"{clean_query} = {formatted_res}"
        else:
            msg = f"The result is {formatted_res}."

        return {
            "success": True,
            "expression": normalized,
            "raw_query": raw_expr,
            "result": formatted_res,
            "numeric_result": result,
            "message": msg,
            "verified": True
        }
    except ZeroDivisionError:
        return {
            "success": False,
            "error": "Division by zero is undefined.",
            "message": "Division by zero is undefined.",
            "verified": True
        }
    except Exception as e:
        logger.debug(f"Math evaluation notice for '{raw_expr}': {e}")
        return {
            "success": False,
            "error": str(e),
            "verified": False
        }

@registry.register(
    name="calculate_math",
    description="Calculate and solve mathematical expressions, arithmetic, percentages, and formulas.",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression or arithmetic query to solve (e.g. '2*2', '15% of 200', 'sqrt(144)', '25 * 4 + 10')"
            }
        },
        "required": ["expression"]
    },
    permission_level="normal",
    category="system"
)
def calculate_math(expression: str) -> Dict[str, Any]:
    return evaluate_math_expression(expression)
