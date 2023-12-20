"""Custom additional linter functions for the acquisition module."""
import ast
from typing import Any, Dict

from ..utils.lint import get_all_args_from_call

SPECIAL_FUNCTIONS_LIST = []


def on_call_functions(node: ast.Call, db: Dict[str, Any]):
    """Check if 'save_fig' function is called more then ones with the same arguments.

    Args:
        node (ast.Call): The function call node to check.
        db (Dict[str, Any]): A dict to store information about previous calls.

    Returns:
        List[str]: A list of error messages, if any.
    """
    errors = []
    if isinstance(node.func, ast.Attribute):
        function_name = node.func.attr
        if function_name == "save_fig":
            h = hash(tuple(get_all_args_from_call(node)))
            data = db.setdefault("save_fig", [])
            if h in data:
                errors.append("save_fig with the save arguments is used more then ones.")

            data.append(h)
    return errors
