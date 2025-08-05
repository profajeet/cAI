"""
Calculator tool extension.
"""
import ast
import operator
from typing import Dict, Any
from .base_tool import BaseTool, ToolSchema, ToolResult


class Calculator(BaseTool):
    """Simple calculator tool for mathematical operations."""
    
    description = "Performs mathematical calculations on expressions"
    
    def _create_schema(self) -> ToolSchema:
        return ToolSchema(
            name="Calculator",
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {
                        "type": "number",
                        "description": "Result of the calculation"
                    },
                    "expression": {
                        "type": "string",
                        "description": "Original expression"
                    }
                }
            },
            required_params=["expression"]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        expression = kwargs["expression"]
        
        try:
            # Safely evaluate the expression
            result = self._safe_eval(expression)
            
            return ToolResult(
                success=True,
                result={
                    "result": result,
                    "expression": expression
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Calculation failed: {str(e)}"
            )
    
    def _safe_eval(self, expression: str) -> float:
        """Safely evaluate a mathematical expression."""
        # Define allowed operators
        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos
        }
        
        def eval_node(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return allowed_operators[type(node.op)](eval_node(node.left), eval_node(node.right))
            elif isinstance(node, ast.UnaryOp):
                return allowed_operators[type(node.op)](eval_node(node.operand))
            else:
                raise ValueError(f"Unsupported operation: {type(node).__name__}")
        
        # Parse and evaluate
        tree = ast.parse(expression, mode='eval')
        return eval_node(tree.body) 