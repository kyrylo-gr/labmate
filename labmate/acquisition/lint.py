import ast
from typing import List, Optional, Tuple


def get_args_from_list(args: List[ast.arg]):
    return [arg.arg for arg in args]


class NameVisitor(ast.NodeVisitor):
    parent = None
    dont_parse = None

    def __init__(self, ignore_var: Optional[set] = None):
        self.local_vars = ignore_var.copy() if ignore_var else set()
        self.builtins = set(__builtins__.keys())
        self.external_vars = set()
        super().__init__()

    def visit(self, node, parent=None, dont_parse=None):
        node.parent = parent  # type: ignore
        node.dont_parse = dont_parse  # type: ignore

        if (isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and
                node.func.attr == "save_acquisition"):
            node.dont_parse = []  # type: ignore
            return

        if isinstance(node, ast.FunctionDef):
            variables = (
                get_args_from_list(node.args.posonlyargs) +
                get_args_from_list(node.args.args) +
                get_args_from_list(node.args.kwonlyargs)
            )
            if node.args.kwarg:
                variables += node.args.kwarg.arg
            node.dont_parse = variables  # type: ignore

        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for name in node.names:
                var = name.asname or name.name
                if var != "*":
                    self.local_vars.add(var)

        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                if node.dont_parse is None:  # type: ignore
                    self.local_vars.add(node.id)
                else:
                    node.dont_parse.append(node.id)  # type: ignore

            if (isinstance(node.ctx, ast.Load) and
                    node.id not in self.local_vars and
                    node.id not in self.builtins):
                if (node.dont_parse is None) or (node.id not in node.dont_parse):  # type: ignore
                    self.external_vars.add(node.id)

        self.generic_visit(node)

    def generic_visit(self, node):
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item, parent=node,
                                   dont_parse=node.dont_parse)  # type: ignore
            elif isinstance(value, ast.AST):
                self.visit(value, parent=node,
                           dont_parse=node.dont_parse)  # type: ignore


def find_variables(node, ignore_var: Optional[set] = None) -> Tuple[set, set]:
    """Walk through ast.node and find the variable that was never declared inside this node, but used.

    Variables from ingore_var set is allowed external variables to use.
    Returns (local_vars, external_vars)
    """
    visitor = NameVisitor(ignore_var)
    visitor.visit(node)
    return visitor.local_vars, visitor.external_vars


def find_variables_from_code(code, ignore_var: Optional[set] = None) -> Tuple[set, set]:
    code = code.split("\n")
    for i, line in enumerate(code):
        if "# noqa" in line or "#noqa" in line:
            code[i] = ""
            # code[i] = code[i][:len(code[i]) - len(code[i].lstrip())] + '""'
    node = ast.parse("\n".join(code))
    return find_variables(node, ignore_var)


def find_variables_from_file(file, ignore_var: Optional[set] = None) -> Tuple[set, set]:
    with open(file, 'r', encoding="utf-8") as f:
        code = f.read()
    return find_variables_from_code(code, ignore_var)
