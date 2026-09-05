import math
import ast
import operator
import re
import logging
import statistics
from collections import Counter
from typing import Dict, Any, Union, Optional, Tuple, List
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
    "gcd": math.gcd,
    "lcm": math.lcm,
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
                raise ZeroDivisionError("Division by zero is undefined.")
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

def parse_polynomial_side(side_str: str, var: str = "x") -> Tuple[float, float, float]:
    """Parses a polynomial side into coefficients (a*x^2, b*x, c)."""
    s = side_str.replace(" ", "").replace("-", "+-")
    terms = [t for t in s.split("+") if t]
    a, b, c = 0.0, 0.0, 0.0

    for term in terms:
        # Match x^2 or x**2 term
        m2 = re.fullmatch(rf"([+-]?\d*\.?\d*)\*?{var}(?:\^2|\*\*2)", term, re.IGNORECASE)
        if m2:
            coeff = m2.group(1)
            if coeff in ("", "+"): a += 1.0
            elif coeff == "-": a -= 1.0
            else: a += float(coeff)
            continue

        # Match x term
        m1 = re.fullmatch(rf"([+-]?\d*\.?\d*)\*?{var}", term, re.IGNORECASE)
        if m1:
            coeff = m1.group(1)
            if coeff in ("", "+"): b += 1.0
            elif coeff == "-": b -= 1.0
            else: b += float(coeff)
            continue

        # Constant term
        try:
            c += float(term)
        except ValueError:
            pass

    return a, b, c

def solve_algebraic_equation(eq_str: str) -> Optional[Dict[str, Any]]:
    """Solves linear (ax + b = c) and quadratic (ax^2 + bx + c = 0) equations step-by-step."""
    clean = re.sub(r"^(solve|find [a-z] in|calculate|evaluate)\s+", "", eq_str, flags=re.IGNORECASE).strip().rstrip("?.!")
    if "=" not in clean:
        return None

    # Detect variable name (x, y, z, n, etc.)
    var_match = re.search(r"\b([a-zA-Z])\b", clean)
    var = var_match.group(1) if var_match else "x"
    if var.lower() in ("e", "i"):
        var = "x"

    lhs, rhs = clean.split("=", 1)
    a1, b1, c1 = parse_polynomial_side(lhs, var)
    a2, b2, c2 = parse_polynomial_side(rhs, var)

    a = a1 - a2
    b = b1 - b2
    c = c1 - c2

    # Case 1: Quadratic equation (a != 0)
    if abs(a) > 1e-9:
        d = b**2 - 4 * a * c
        steps = [
            f"Equation: {clean}",
            f"Standard form: {a:g}{var}² {'+ ' if b >= 0 else '- '}{abs(b):g}{var} {'+ ' if c >= 0 else '- '}{abs(c):g} = 0",
            f"Discriminant (Δ = b² - 4ac): {b:g}² - 4({a:g})({c:g}) = {d:g}"
        ]

        if d > 1e-9:
            r1 = (-b + math.sqrt(d)) / (2 * a)
            r2 = (-b - math.sqrt(d)) / (2 * a)
            steps.append(f"Roots: {var}₁ = {r1:g}, {var}₂ = {r2:g}")
            msg = f"The solutions to {clean} are {var} = {r1:g} and {var} = {r2:g}."
            return {"success": True, "type": "quadratic", "roots": [r1, r2], "steps": steps, "message": msg, "verified": True}
        elif abs(d) <= 1e-9:
            r = -b / (2 * a)
            steps.append(f"Single repeated root: {var} = {r:g}")
            msg = f"The solution to {clean} is {var} = {r:g}."
            return {"success": True, "type": "quadratic", "roots": [r], "steps": steps, "message": msg, "verified": True}
        else:
            real_part = -b / (2 * a)
            imag_part = math.sqrt(-d) / (2 * a)
            steps.append(f"Complex roots: {var} = {real_part:g} ± {imag_part:g}i")
            msg = f"The complex solutions to {clean} are {var} = {real_part:g} ± {imag_part:g}i."
            return {"success": True, "type": "quadratic", "roots": [f"{real_part:g}+{imag_part:g}i", f"{real_part:g}-{imag_part:g}i"], "steps": steps, "message": msg, "verified": True}

    # Case 2: Linear equation (a == 0, b != 0)
    elif abs(b) > 1e-9:
        root = -c / b
        steps = [
            f"Equation: {clean}",
            f"Standard form: {b:g}{var} = {-c:g}",
            f"Solving for {var}: {var} = {-c:g} / {b:g} = {root:g}"
        ]
        msg = f"For {clean}, {var} = {root:g}."
        return {"success": True, "type": "linear", "roots": [root], "steps": steps, "message": msg, "verified": True}

    return None

def solve_number_theory(query: str) -> Optional[Dict[str, Any]]:
    """Solves GCD, LCM, Prime verification, Prime Factorization, and Factorials."""
    q = query.strip().lower()

    # 1. GCD / HCF: gcd of 48 and 18
    m_gcd = re.search(r"\b(?:gcd|hcf|greatest common (?:divisor|factor))\s+(?:of\s+)?(\d+)\s*(?:and|,)\s*(\d+)", q)
    if m_gcd:
        a, b = int(m_gcd.group(1)), int(m_gcd.group(2))
        res = math.gcd(a, b)
        return {
            "success": True,
            "result": str(res),
            "message": f"The GCD of {a} and {b} is {res}.",
            "verified": True
        }

    # 2. LCM: lcm of 12 and 15
    m_lcm = re.search(r"\b(?:lcm|least common multiple)\s+(?:of\s+)?(\d+)\s*(?:and|,)\s*(\d+)", q)
    if m_lcm:
        a, b = int(m_lcm.group(1)), int(m_lcm.group(2))
        res = math.lcm(a, b)
        return {
            "success": True,
            "result": str(res),
            "message": f"The LCM of {a} and {b} is {res}.",
            "verified": True
        }

    # 3. Prime Check: is 97 prime?
    m_prime = re.search(r"\b(?:is\s+)?(\d+)\s+(?:a\s+)?prime(?:\s+number)?\b", q)
    if m_prime:
        n = int(m_prime.group(1))
        if n < 2:
            is_p = False
            divisor = None
        else:
            is_p = True
            divisor = None
            for i in range(2, int(math.isqrt(n)) + 1):
                if n % i == 0:
                    is_p = False
                    divisor = i
                    break
        if is_p:
            msg = f"{n} is a prime number (only divisible by 1 and itself)."
        else:
            div_note = f" (divisible by {divisor})" if divisor else ""
            msg = f"{n} is not a prime number{div_note}."
        return {"success": True, "result": "Prime" if is_p else "Not Prime", "message": msg, "verified": True}

    # 4. Prime Factors / Factorization: factors of 60, prime factors of 84
    m_factors = re.search(r"\b(?:prime\s+)?factors\s+of\s+(\d+)\b", q)
    if m_factors:
        n = int(m_factors.group(1))
        all_factors = []
        for i in range(1, int(math.isqrt(n)) + 1):
            if n % i == 0:
                all_factors.append(i)
                if i * i != n:
                    all_factors.append(n // i)
        all_factors.sort()

        temp = n
        d = 2
        p_factors = []
        while d * d <= temp:
            while temp % d == 0:
                p_factors.append(d)
                temp //= d
            d += 1
        if temp > 1:
            p_factors.append(temp)

        counts = Counter(p_factors)
        p_str = " * ".join([f"{base}^{exp}" if exp > 1 else str(base) for base, exp in sorted(counts.items())])
        msg = f"The factors of {n} are {', '.join(map(str, all_factors))}. Prime factorization: {n} = {p_str}."
        return {"success": True, "result": str(all_factors), "message": msg, "verified": True}

    # 5. Factorial: factorial of 7, 7!
    m_fact = re.search(r"\b(?:factorial\s+of\s+(\d+)|(\d+)\s*!\s*)\b", q)
    if m_fact:
        num = int(m_fact.group(1) or m_fact.group(2))
        if num > 100:
            return {"success": False, "message": "Number too large for instant factorial.", "verified": False}
        res = math.factorial(num)
        return {"success": True, "result": str(res), "message": f"{num}! = {res}", "verified": True}

    # 6. Permutations and Combinations: nPr, nCr
    m_perm = re.search(r"\b(\d+)\s*P\s*(\d+)\b", q, re.IGNORECASE)
    if m_perm:
        n, r = int(m_perm.group(1)), int(m_perm.group(2))
        if 0 <= r <= n and n <= 100:
            res = math.perm(n, r)
            return {"success": True, "result": str(res), "message": f"{n}P{r} = {res}", "verified": True}

    m_comb = re.search(r"\b(\d+)\s*C\s*(\d+)\b", q, re.IGNORECASE)
    if m_comb:
        n, r = int(m_comb.group(1)), int(m_comb.group(2))
        if 0 <= r <= n and n <= 100:
            res = math.comb(n, r)
            return {"success": True, "result": str(res), "message": f"{n}C{r} = {res}", "verified": True}

    return None

def solve_statistics(query: str) -> Optional[Dict[str, Any]]:
    """Calculates Mean, Median, Mode, Variance, and Standard Deviation."""
    q = query.strip().lower()
    m = re.search(r"\b(mean|average|median|mode|standard deviation|variance)\s+(?:of\s+)?([-\d\s,.]+)", q)
    if not m:
        return None

    op = m.group(1)
    raw_nums = m.group(2)
    nums = [float(x.strip()) for x in re.findall(r"[-+]?\d*\.?\d+", raw_nums) if x.strip()]
    if len(nums) < 2:
        return None

    if op in ("mean", "average"):
        res = statistics.mean(nums)
        msg = f"The mean of the numbers is {res:g}."
    elif op == "median":
        res = statistics.median(nums)
        msg = f"The median of the numbers is {res:g}."
    elif op == "mode":
        try:
            res = statistics.mode(nums)
            msg = f"The mode of the numbers is {res:g}."
        except Exception:
            return {"success": True, "result": "None", "message": "No unique mode found in the numbers.", "verified": True}
    elif op in ("standard deviation", "std dev"):
        res = statistics.stdev(nums)
        msg = f"The sample standard deviation is {res:.4g}."
    elif op == "variance":
        res = statistics.variance(nums)
        msg = f"The sample variance is {res:.4g}."
    else:
        return None

    return {"success": True, "result": str(res), "message": msg, "verified": True}

def solve_geometry(query: str) -> Optional[Dict[str, Any]]:
    """Solves circle area/circumference, triangle hypotenuse, and rectangle area."""
    q = query.strip().lower()

    # Circle: area of circle with radius r
    m_circ_a = re.search(r"\barea of (?:a )?circle with (?:radius|r\s*=)\s*(\d*\.?\d+)", q)
    if m_circ_a:
        r = float(m_circ_a.group(1))
        area = math.pi * (r ** 2)
        return {"success": True, "result": f"{area:.4g}", "message": f"Area of circle with radius {r:g} is pi * {r:g}^2 = {area:.4g}.", "verified": True}

    # Circle circumference
    m_circ_p = re.search(r"\b(?:circumference|perimeter) of (?:a )?circle with (?:radius|r\s*=)\s*(\d*\.?\d+)", q)
    if m_circ_p:
        r = float(m_circ_p.group(1))
        c = 2 * math.pi * r
        return {"success": True, "result": f"{c:.4g}", "message": f"Circumference of circle with radius {r:g} is 2 * pi * {r:g} = {c:.4g}.", "verified": True}

    # Triangle Hypotenuse
    m_hyp = re.search(r"\bhypotenuse\s+(?:of\s+)?(?:triangle\s+)?(?:with\s+)?(?:sides|legs)?\s*(\d*\.?\d+)\s*(?:and|,)\s*(\d*\.?\d+)", q)
    if m_hyp:
        a, b = float(m_hyp.group(1)), float(m_hyp.group(2))
        hyp = math.hypot(a, b)
        return {"success": True, "result": f"{hyp:g}", "message": f"Hypotenuse with legs {a:g} and {b:g} is sqrt({a:g}^2 + {b:g}^2) = {hyp:g}.", "verified": True}

    # Rectangle area
    m_rect = re.search(r"\barea of (?:a )?rectangle with (?:length\s*=?\s*)?(\d*\.?\d+)\s*(?:and|x|\*)\s*(?:width\s*=?\s*)?(\d*\.?\d+)", q)
    if m_rect:
        l, w = float(m_rect.group(1)), float(m_rect.group(2))
        area = l * w
        return {"success": True, "result": f"{area:g}", "message": f"Area of rectangle with length {l:g} and width {w:g} is {l:g} * {w:g} = {area:g}.", "verified": True}

    return None

def solve_unit_conversions(query: str) -> Optional[Dict[str, Any]]:
    """Solves temperature, distance, and weight conversions."""
    q = query.strip().lower()

    # Temperature C to F
    m_c2f = re.search(r"(\d+(?:\.\d+)?)\s*(?:c|celsius|degrees c)\s+to\s+(?:f|fahrenheit)", q)
    if m_c2f:
        c = float(m_c2f.group(1))
        f = c * 9/5 + 32
        return {"success": True, "result": f"{f:g}", "message": f"{c:g} degrees C = {f:g} degrees F", "verified": True}

    # Temperature F to C
    m_f2c = re.search(r"(\d+(?:\.\d+)?)\s*(?:f|fahrenheit|degrees f)\s+to\s+(?:c|celsius)", q)
    if m_f2c:
        f = float(m_f2c.group(1))
        c = (f - 32) * 5/9
        return {"success": True, "result": f"{c:.4g}", "message": f"{f:g} degrees F = {c:.4g} degrees C", "verified": True}

    # Distance km to miles
    m_km2m = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kilometers?)\s+to\s+(?:miles?|mi)", q)
    if m_km2m:
        km = float(m_km2m.group(1))
        mi = km * 0.621371
        return {"success": True, "result": f"{mi:.4g}", "message": f"{km:g} km = {mi:.4g} miles", "verified": True}

    # Distance miles to km
    m_m2km = re.search(r"(\d+(?:\.\d+)?)\s*(?:miles?|mi)\s+to\s+(?:km|kilometers?)", q)
    if m_m2km:
        mi = float(m_m2km.group(1))
        km = mi * 1.60934
        return {"success": True, "result": f"{km:.4g}", "message": f"{mi:g} miles = {km:.4g} km", "verified": True}

    # Weight kg to lbs
    m_kg2lbs = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kilograms?)\s+to\s+(?:lbs|pounds?)", q)
    if m_kg2lbs:
        kg = float(m_kg2lbs.group(1))
        lbs = kg * 2.20462
        return {"success": True, "result": f"{lbs:.4g}", "message": f"{kg:g} kg = {lbs:.4g} lbs", "verified": True}

    # Weight lbs to kg
    m_lbs2kg = re.search(r"(\d+(?:\.\d+)?)\s*(?:lbs|pounds?)\s+to\s+(?:kg|kilograms?)", q)
    if m_lbs2kg:
        lbs = float(m_lbs2kg.group(1))
        kg = lbs / 2.20462
        return {"success": True, "result": f"{kg:.4g}", "message": f"{lbs:g} lbs = {kg:.4g} kg", "verified": True}

    return None

def normalize_math_expression(expr: str) -> str:
    """Converts natural language math queries into clean mathematical expressions."""
    s = expr.strip().lower()

    # Remove leading question phrases
    s = re.sub(r"^(what is|what's|calculate|solve|evaluate|find|how much is|can you solve|tell me)\s+", "", s)
    s = s.rstrip("?.!")

    # Handle percentage increase / decrease: increase 500 by 20%
    inc_m = re.search(r"increase\s+(\d+(?:\.\d+)?)\s+by\s+(\d+(?:\.\d+)?)\s*%", s)
    if inc_m:
        val, pct = float(inc_m.group(1)), float(inc_m.group(2))
        return f"{val} * (1 + {pct} / 100)"

    dec_m = re.search(r"decrease\s+(\d+(?:\.\d+)?)\s+by\s+(\d+(?:\.\d+)?)\s*%", s)
    if dec_m:
        val, pct = float(dec_m.group(1)), float(dec_m.group(2))
        return f"{val} * (1 - {pct} / 100)"

    # Handle percentage queries e.g. "15% of 200" or "what is 20 percent of 500"
    pct_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)\s+of\s+(\d+(?:\.\d+)?)", s)
    if pct_match:
        pct = float(pct_match.group(1))
        val = float(pct_match.group(2))
        return f"({pct} / 100) * {val}"

    # Handle "what percentage is X of Y"
    pct_is = re.search(r"(?:what\s+)?percentage\s+is\s+(\d+(?:\.\d+)?)\s+of\s+(\d+(?:\.\d+)?)", s)
    if pct_is:
        x, y = float(pct_is.group(1)), float(pct_is.group(2))
        return f"({x} / {y}) * 100"

    # Trigonometry in degrees: sin(30 deg), sin(30 degrees)
    s = re.sub(r"(sin|cos|tan)\((\d+(?:\.\d+)?)\s*(?:deg|degrees)\)", lambda m: f"{m.group(1)}({float(m.group(2)) * math.pi / 180})", s)

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

    s = s.strip()
    return s

def evaluate_math_expression(raw_expr: str) -> Dict[str, Any]:
    """
    Comprehensive mathematical solver:
    1. Checks algebraic linear & quadratic equations
    2. Checks number theory (GCD, LCM, Primes, Factors, Permutations)
    3. Checks statistics (Mean, Median, Mode, Stdev)
    4. Checks geometry (Circle, Triangle, Rectangle)
    5. Checks unit conversions
    6. Safely evaluates arithmetic expressions via AST
    """
    if not raw_expr or not raw_expr.strip():
        return {"success": False, "error": "Empty mathematical expression", "verified": False}

    clean_query = raw_expr.strip()

    # 1. Algebraic equations (e.g. 2x + 5 = 15, x^2 - 5x + 6 = 0)
    if "=" in clean_query:
        alg_res = solve_algebraic_equation(clean_query)
        if alg_res:
            return alg_res

    # 2. Number theory (GCD, LCM, Prime, Factors, Factorials)
    nt_res = solve_number_theory(clean_query)
    if nt_res:
        return nt_res

    # 3. Statistics (Mean, Median, Mode, Variance, Stdev)
    stat_res = solve_statistics(clean_query)
    if stat_res:
        return stat_res

    # 4. Geometry (Circle area, hypotenuse, etc.)
    geom_res = solve_geometry(clean_query)
    if geom_res:
        return geom_res

    # 5. Unit conversions (Celsius to Fahrenheit, Km to Miles, etc.)
    conv_res = solve_unit_conversions(clean_query)
    if conv_res:
        return conv_res

    # 6. Standard arithmetic & function evaluation
    normalized = normalize_math_expression(clean_query)
    if not normalized:
        return {"success": False, "error": "Could not normalize mathematical expression", "verified": False}

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

        # Natural, clean format
        expr_clean = re.sub(r"^(what is|what's|calculate|solve|how much is|can you solve)\s+", "", clean_query, flags=re.IGNORECASE).strip().rstrip("?.!")
        if any(sym in expr_clean for sym in ["+", "-", "*", "/", "%", "^", "x"]):
            msg = f"{expr_clean} = {formatted_res}"
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
    description="Calculate and solve mathematical expressions, equations (linear and quadratic), number theory, geometry, statistics, and conversions.",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression or query to solve (e.g. '2*2', '2x + 5 = 15', 'x^2 - 5x + 6 = 0', 'gcd of 48 and 18', 'mean of 10, 20, 30', '15% of 200')"
            }
        },
        "required": ["expression"]
    },
    permission_level="normal",
    category="system"
)
def calculate_math(expression: str) -> Dict[str, Any]:
    return evaluate_math_expression(expression)
