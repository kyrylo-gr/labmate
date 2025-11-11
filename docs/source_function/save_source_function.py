"""Module for analyzing functions and extracting their dependencies."""

import ast
import inspect
from typing import Dict, Set, Any


class FunctionAnalyzer:
    """Analyzes a function and extracts all used functions, variables, classes, and modules."""

    def __init__(self):
        """Initialize the FunctionAnalyzer."""
        self.results: Dict[str, Dict[str, Any]] = {}
        self.visited: Set[str] = set()

    def analyze_function(self, func) -> Dict[str, Dict[str, Any]]:
        """Analyze a function and return a dictionary of all used symbols."""
        self.results = {}
        self.visited = set()
        self._analyze_func(func)
        return self.results

    def _analyze_func(self, func):
        """Recursively analyze a function and its dependencies."""
        print(f"Analyzing {func}")
        if not (inspect.isfunction(func) or inspect.ismethod(func)):
            return
        func_id = self._get_func_id(func)
        if func_id in self.visited:
            return
        self.visited.add(func_id)
        source = self._get_source(func)
        file_path = self._get_file(func)
        used_names = self._get_used_names(source)
        if inspect.isfunction(func):
            globals_dict = func.__globals__
        elif inspect.ismethod(func):
            globals_dict = func.__func__.__globals__
        else:
            globals_dict = {}
        self.results[func_id] = {
            "value": source,
            "type": "function",
            "file": file_path,
            "external_vars": [],
        }
        for name in used_names:
            if name in globals_dict:
                value = globals_dict[name]
                print(f"Value of {name} is {value}")
                if inspect.isfunction(value):
                    sub_id = self._get_func_id(value)
                    self.results[func_id]["external_vars"].append(sub_id)
                    self._analyze_func(value)
                elif inspect.isclass(value):
                    sub_id = self._get_class_id(value)
                    if sub_id not in self.results:
                        self.results[sub_id] = {
                            "value": self._get_source(value),
                            "type": "class",
                            "file": self._get_file(value),
                            "external_vars": [],
                        }
                    self.results[func_id]["external_vars"].append(sub_id)
                elif inspect.ismodule(value):
                    mod_id = value.__name__
                    # Don't save the module itself, just track it for external_vars
                    self.results[func_id]["external_vars"].append(mod_id)
                    print(f"Skipping {name} because it is a module")
                else:
                    var_id = f"{func.__module__}.{name}"
                    if var_id not in self.results:
                        self.results[var_id] = {
                            "type": "variable",
                            "value": repr(value),
                        }
                    self.results[func_id]["external_vars"].append(var_id)
            else:
                # Could be a builtin or closure, skip for now
                print(f"Skipping {name} because it is not in globals_dict")
                continue

    def _get_func_id(self, func):
        """Return a unique identifier for a function."""
        return f"{func.__module__}.{func.__name__}"

    def _get_class_id(self, cls):
        """Return a unique identifier for a class."""
        return f"{cls.__module__}.{cls.__name__}"

    def _get_source(self, obj):
        """Get the source code of an object."""
        try:
            return inspect.getsource(obj)
        except Exception:
            return ""

    def _get_file(self, obj):
        """Get the file path of an object."""
        try:
            return inspect.getfile(obj)
        except Exception:
            return "unknown"

    def _get_used_names(self, source):
        """Parse AST and collect all used names in the source code."""
        used = set()
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used.add(node.id)
                elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                    # Collect the base name of attribute access (e.g., np.random -> np)
                    base = node
                    while isinstance(base, ast.Attribute):
                        base = base.value
                    if isinstance(base, ast.Name):
                        used.add(base.id)
        except Exception:
            pass
        return used


def get_source_functions(func) -> Dict[str, Dict[str, Any]]:
    """Analyze a function and return a dictionary of all used symbols."""
    analyzer = FunctionAnalyzer()
    return analyzer.analyze_function(func)
