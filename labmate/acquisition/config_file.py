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
        cc = compile(self.content, '<string>', 'exec')
        eval(cc, module.__dict__)  # pylint: disable=W0123
        return module

    def eval_key(self, key):
        val = self.get(key)
        if val:
            return eval(val)  # pylint: disable=W0123
        return None
