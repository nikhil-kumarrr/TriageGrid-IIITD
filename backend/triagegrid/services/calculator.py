"""Bounded arithmetic evaluation, never eval or executable user code."""
import ast
import re
from decimal import Decimal, localcontext, InvalidOperation


def calculate(text: str) -> str | None:
    text = text.strip().translate(str.maketrans("०१२३४५६७८९×÷−", "0123456789*/-"))
    if len(text) > 250:
        return None
    # Only a standalone expression or a recognised calculation request is accepted.
    match = re.fullmatch(r"(?:(?:what is|calculate|solve|kitna hota hai|कितना होता है)\s+)?([\d.\s()+*/%^-]+)(?:\s*(?:[?=]|kya hai|kitna hai|batao|क्या है))?", text, re.I)
    if not match:
        return None
    expression = match.group(1).strip().replace("^", "**")
    if not re.search(r"[+*/%^-]", expression):
        return None
    try:
        tree = ast.parse(expression, mode="eval")
        if len(list(ast.walk(tree))) > 60:
            raise ValueError("Expression too long")
        def visit(n):
            if isinstance(n, ast.Constant) and type(n.value) in (int, float):
                return Decimal(ast.get_source_segment(expression, n))
            if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
                value = visit(n.operand)
                return value if isinstance(n.op, ast.UAdd) else -value
            if isinstance(n, ast.BinOp):
                a, b = visit(n.left), visit(n.right)
                if isinstance(n.op, ast.Add): value = a + b
                elif isinstance(n.op, ast.Sub): value = a - b
                elif isinstance(n.op, ast.Mult): value = a * b
                elif isinstance(n.op, ast.Div): value = a / b
                elif isinstance(n.op, ast.Mod): value = a % b
                elif isinstance(n.op, ast.Pow) and b == b.to_integral_value() and abs(b) <= 100: value = a ** int(b)
                else: raise ValueError("Unsupported operation")
                if not value.is_finite() or (value and abs(value.adjusted()) > 100):
                    raise ValueError("Result outside supported range")
                return value
            raise ValueError("Unsupported expression")
        with localcontext() as ctx:
            ctx.prec = 28
            value = visit(tree.body)
        result = format(value, 'f')
        if '.' in result: result = result.rstrip('0').rstrip('.')
        return f"{expression.replace('**', '^')} = {result}"
    except (SyntaxError, ValueError, InvalidOperation, ArithmeticError):
        return "Calculation error: check the expression; division by zero and oversized calculations are not supported."
