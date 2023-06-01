import json


class StringEncoder(json.JSONEncoder):
    """Classical JSONEncoder will not try to convert objects to a str. This does."""

    def default(self, o):
        if hasattr(o, "__iter__"):
            return [self.default(obj) for obj in iter(o)]
        return str(o)
