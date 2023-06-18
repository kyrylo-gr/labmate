from typing import Any
from .. import attrdict


class ConfigFile(attrdict.AttrDict):
    def __init__(self, data=None, code=None):
        if data is None:
            data = {}
        super().__init__(data)
        self.content = code

    def eval_as_module(self):
        if self.content is None:
            raise ValueError("Content is not defined")

        module = type(attrdict)("config_module")
        cc = compile(self.content, '<string>', 'exec')  # noqa: DUO110
        eval(cc, module.__dict__)  # pylint: disable=W0123 # noqa: DUO104
        return module

    def eval_key(self, key) -> Any:
        val = self.get(key)
        if val and val.value:
            return eval(val.value)  # pylint: disable=W0123 # noqa: DUO104
        return None
