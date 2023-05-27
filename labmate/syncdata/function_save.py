import inspect
from typing import Any


class Function:
    code: str = ""
    func = None
    original_name: str = ""

    def __init__(self, code: str):
        index_name = code.find('(')
        if index_name == -1:
            return
        self.original_name = code[4:index_name]
        self.code = 'def current_func' + code[index_name:]

    def def_func(self):
        try:
            if self.code == '':
                raise SyntaxError
            cc = compile(self.code, '<string>', 'single')
            eval(cc)  # pylint: disable=W0123
        except SyntaxError:
            print(f"Function {self.original_name} cannot be loaded.")
        self.func = locals().get('current_func', None)  # type: ignore

    def eval(self, *args, **kwds):
        if self.func is None:
            self.def_func()
        if self.func is None:
            raise ValueError(f"Cannot call run a function defined by:\n{self.code}")
        return self.func(*args, **kwds)  # type: ignore

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self.func is None:
            raise TypeError(
                "Function was never evaluated. "
                "On the first run use the eval(...) method instead.")
        return self.func(*args, **kwds)  # type: ignore


def function_to_str(func):
    if inspect.isfunction(func):
        return inspect.getsource(func)

    raise ValueError(
        f"Function {func.__name__} must be a function and not a module or a class.")
