"""Contains all custom JSON decoders used."""
import json


class NumbersDecoder(json.JSONDecoder):
    """Decode float and int."""

    def decode(self, s):  # pylint: disable=W0221
        result = super().decode(s)
        return self._decode(result)

    def _decode(self, obj):
        if isinstance(obj, str):
            try:
                obj_check = obj[1:] if obj.startswith('-') else obj
                if obj_check.isnumeric():
                    return int(obj)
                if obj_check.count('.') == 1 and obj_check.replace('.', '').isnumeric():
                    return float(obj)
                return obj
            except ValueError:
                return obj
        if isinstance(obj, dict):
            return {k: self._decode(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._decode(v) for v in obj]
        return obj
