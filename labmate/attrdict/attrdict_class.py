class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = AttrDict(v)
        self.__dict__ = self

    def __repr__(self) -> str:
        return f'AttrDict: {super().__repr__()}'

    def __add__(self, other):
        result = self.copy()
        result.update(other)
        return AttrDict(result)
