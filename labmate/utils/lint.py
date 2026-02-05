"""Linting module that detects bad practice with AcquisitionAnalysisManager."""

import ast
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Set


def set_parameters_from_parent(item, parent):
    """
    Set parameters from parent object to child object.

    Args:
        item: Child object to set parameters to.
        parent: Parent object to get parameters from.

    Returns:
        None
    """
    parameters = ["dont_parse"]
    for param in parameters:
        setattr(item, param, getattr(parent, param))


def get_args_from_list(args: List[ast.arg]) -> List[str]:
    """Extract the argument names from a list of ast.arg objects.

    Args:
        args: A list of ast.arg objects representing the function arguments.

    Returns:
        A list of strings representing the names of the function arguments.
    """
    return [arg.arg for arg in args]


def get_all_args_from_def(args: ast.arguments) -> List[str]:
    """Return a list of all arguments in a function definition.

    Args:
        args (ast.arguments): The arguments of the function definition.

    Returns:
        A list of all arguments in the function definition.
    """
    variables = (
        get_args_from_list(args.posonlyargs)
        + get_args_from_list(args.args)
        + get_args_from_list(args.kwonlyargs)
    )
    if args.kwarg:
        variables += args.kwarg.arg

    return variables


def get_all_args_from_call(node: ast.Call):
    """Extract all constants and names passed to the AST Call node.

    Args:
        node (ast.Call): The Call node to extract arguments from.

    Returns:
        tuple: A tuple containing all argument values.
    """
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
    """
    A visitor class that traverses the AST and collects information about variable names.

    Attributes:
        parent (ast.AST): The parent node of the current node being visited.
        dont_parse (List[str]): A list of variable names that should not be parsed.
        local_vars (Set[str]): A set of local variable names.
        external_vars (Set[str]): A set of external variable names.
        errors (List[str]): A list of errors encountered during traversal.
        run_on_call (Optional[Callable]): A function to run on each function call node.
        special_functions_db (Dict[str, Any]): A dict of special functions and their attributes.
    """

    parent = None
    dont_parse = None
    local_vars: Set[str]
    external_vars: Set[str]
    errors: List[str]
    run_on_call: Optional[Callable]
    special_functions_db: Dict[str, Any]

    def __init__(self, ignore_var: Optional[Set[str]] = None, **kwargs):
        """Initialize a new instance of the NameVisitor class.

        Args:
            ignore_var (Set[str] | None): A set of variable names to ignore.
            run_on_call (Callable | None): Function to run on every ast.Call node if any provided.
        """
        self.local_vars = ignore_var.copy() if ignore_var else set()
        self.builtins = set(__builtins__.keys())
        self.external_vars = set()
        self.errors = []
        self.run_on_call = kwargs.get("run_on_call")
        self.special_functions_db = {}
        super().__init__()

    def visit(self, node, parent=None):
        """
        Visits a node in the AST.

        Args:
            node (ast.AST): The node to visit.
            parent (Optional[ast.AST]): The parent node of the current node being visited.
        """
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

        if isinstance(node, ast.FunctionDef):
            variables = get_all_args_from_def(node.args)
            self.local_vars.add(node.name)
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
        """
        Visits a node in the AST and its children.

        Args:
            node (ast.AST): The node to visit.
        """
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
    """Represent the result of a linting operation.

    Attributes:
        internal_vars (Set[str]): A set of internal variable names found during linting.
        external_vars (Set[str]): A set of external variable names found during linting.
        errors (List[str]): A list of error messages generated during linting.
    """

    internal_vars: Set[str]
    external_vars: Set[str]
    errors: List[str]


def find_variables_from_node(node, ignore_var: Optional[set] = None, **kwargs) -> LintResult:
    """
    Walk through ast.node and find variables that were never declared inside the node, but are used.

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
    """Find used and unused variables in a given code string.

    Args:
        code: A string containing the code to analyze.
        ignore_var: A set of variable names to ignore during analysis.
        run_on_call: A callable function to run on function calls.

    Returns:
        A LintResult object containing the used and unused variables,
            and any errors encountered during analysis.
    """
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
                "#noqa removes line from the analysis, so don't use it with line breaks.\n"
                f"Error at line {exception.lineno} in {exception.text}"
            ],
        )
    return find_variables_from_node(node, ignore_var, run_on_call=run_on_call)


def find_variables_from_file(
    file,
    ignore_var: Optional[set] = None,
    run_on_call: Optional[Callable] = None,
) -> LintResult:
    """Find all variables in a given file and returns a LintResult object.

    Args:
        file: A string representing the path to the file to be analyzed.
        ignore_var: An optional set of variable names to ignore during analysis.
        run_on_call: An optional callable object to run on each function call found during analysis.

    Returns:
        A LintResult object containing the used and unused variables,
            and any errors encountered during analysis.
    """
    with open(file, encoding="utf-8") as f:
        code = f.read()
    return find_variables_from_code(code, ignore_var, run_on_call=run_on_call)
