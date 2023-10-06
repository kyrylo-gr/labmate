import ast
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Set


def set_parameters_from_parent(item, parent):
    parameters = ["dont_parse"]
    for param in parameters:
        setattr(item, param, getattr(parent, param))


def get_args_from_list(args: List[ast.arg]):
    return [arg.arg for arg in args]


def get_all_args_from_def(args: ast.arguments):
    variables = (
        get_args_from_list(args.posonlyargs)
        + get_args_from_list(args.args)
        + get_args_from_list(args.kwonlyargs)
    )
    if args.kwarg:
        variables += args.kwarg.arg

    return variables


def get_all_args_from_call(node: ast.Call):
    arguments = []
    for arg in node.args:
        if isinstance(arg, ast.Constant):
            arguments.append(arg.value)
        elif isinstance(arg, ast.Name):
            pass
    for keyword in node.keywords:
        if isinstance(keyword.value, ast.Constant):
            arguments.append(keyword.value.value)
        elif isinstance(keyword.value, ast.Name):
            pass
    return tuple(arguments)


class NameVisitor(ast.NodeVisitor):
    parent = None
    dont_parse = None
    local_vars: Set[str]
    external_vars: Set[str]
    errors: List[str]
    run_on_call: Optional[Callable]

    special_functions_db: Dict[str, Any]

    def __init__(self, ignore_var: Optional[set] = None, **kwargs):
        self.local_vars = ignore_var.copy() if ignore_var else set()
        self.builtins = set(__builtins__.keys())
        self.external_vars = set()
        self.errors = list()
        self.run_on_call = kwargs.get("run_on_call")

        self.special_functions_db = dict()
        super().__init__()

    def visit(self, node, parent=None):
        node.parent = parent  # type: ignore

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "save_acquisition"
        ):
            node.dont_parse = []  # type: ignore
            return

        if isinstance(node, ast.Call) and self.run_on_call:
            errors = self.run_on_call(node, self.special_functions_db)
            if errors:
                self.errors.extend(errors)

        # (node, "run_on_call") and node.run_on_call:  # type: ignore
        #     errors = node.run_on_call(node)  # type: ignore
        #     if errors:
        #         node.errors.extend(errors)  # type: ignore

        if isinstance(node, ast.FunctionDef):
            variables = get_all_args_from_def(node.args)
            node.dont_parse = variables  # type: ignore

        if isinstance(node, ast.Lambda):
            variables = get_args_from_list(node.args.args)
            node.dont_parse = variables  # type: ignore

        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for name in node.names:  # type: ignore
                var = name.asname or name.name
                if var != "*":
                    self.local_vars.add(var)

        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                if node.dont_parse is None:  # type: ignore
                    self.local_vars.add(node.id)
                else:
                    node.dont_parse.append(node.id)  # type: ignore

            if (
                isinstance(node.ctx, ast.Load)
                and (node.id not in self.local_vars)
                and (node.id not in self.builtins)
                and ((node.dont_parse is None) or (node.id not in node.dont_parse))  # type: ignore
            ):
                self.external_vars.add(node.id)

        self.generic_visit(node)

    def generic_visit(self, node):
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        set_parameters_from_parent(item, node)
                        self.visit(item, parent=node)  # type: ignore
            elif isinstance(value, ast.AST):
                set_parameters_from_parent(value, node)
                self.visit(value, parent=node)  # type: ignore


class LintResult(NamedTuple):
    internal_vars: Set[str]
    expernal_vars: Set[str]
    errors: List[str]


def find_variables_from_node(node, ignore_var: Optional[set] = None, **kwargs) -> LintResult:
    """Walk through ast.node and find the variable that was never declared inside this node, but used.

    Variables from ingore_var set is allowed external variables to use.
    Returns (local_vars, external_vars)
    """
    visitor = NameVisitor(ignore_var, **kwargs)
    node.dont_parse = None  # type: ignore
    visitor.visit(node)
    return LintResult(visitor.local_vars, visitor.external_vars, visitor.errors)


def find_variables_from_code(
    code,
    ignore_var: Optional[set] = None,
    run_on_call: Optional[Callable] = None,
) -> LintResult:
    code = code.split("\n")
    for i, line in enumerate(code):
        if "# noqa" in line or "#noqa" in line:
            code[i] = ""
            # code[i] = code[i][:len(code[i]) - len(code[i].lstrip())] + '""'
    try:
        node = ast.parse("\n".join(code))
    except SyntaxError as exception:
        return LintResult(
            set(),
            set(),
            [
                "Syntax error is found during linting. Probably because #noqa is used. "
                "#noqa removes line from the analisys, so don't use it with line breaks.\n"
                f"Error at line {exception.lineno} in {exception.text}"
            ],
        )
    lint_results = find_variables_from_node(node, ignore_var, run_on_call=run_on_call)
    return lint_results


def find_variables_from_file(
    file,
    ignore_var: Optional[set] = None,
    run_on_call: Optional[Callable] = None,
) -> LintResult:
    with open(file, "r", encoding="utf-8") as f:
        code = f.read()
    return find_variables_from_code(code, ignore_var, run_on_call=run_on_call)
