import ast
from typing import Optional, Tuple


class NameVisitor(ast.NodeVisitor):
    def __init__(self, ignore_var: Optional[set] = None):
        self.local_vars = ignore_var.copy() if ignore_var else set()
        self.external_vars = set()
        super().__init__()

    def visit(self, node):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for name in node.names:
                var = name.asname or name.name
                if var != "*":
                    self.local_vars.add(var)
        if isinstance(node, ast.Name):
            # print(node.id, node.ctx)
            # print_node(child)
            if isinstance(node.ctx, ast.Store):
                self.local_vars.add(node.id)
            if isinstance(node.ctx, ast.Load) and node.id not in self.local_vars:
                self.external_vars.add(node.id)
        # print(node)
        self.generic_visit(node)


def find_variables(node, ignore_var: Optional[set] = None) -> Tuple[set, set]:
    """Walk through ast.node and find the variable that was never declared
    inside this node, but used.
    Variables from ingore_var set is allowed external variables to use.
    Returns (local_vars, external_vars)"""
    visitor = NameVisitor(ignore_var)
    visitor.visit(node)
    return visitor.local_vars, visitor.external_vars


def find_variables_from_code(code, ignore_var: Optional[set] = None) -> Tuple[set, set]:
    code = code.split("\n")
    for i, line in enumerate(code):
        if "# noqa" in line or "#noqa" in line:
            code[i] = code[i][:len(code[i]) - len(code[i].lstrip())] + '""'
    node = ast.parse("\n".join(code))
    return find_variables(node, ignore_var)


def find_variables_from_file(file, ignore_var: Optional[set] = None) -> Tuple[set, set]:
    with open(file, 'r', encoding="utf-8") as f:
        code = f.read()
    return find_variables_from_code(code, ignore_var)
