"""ConfigFile class."""
from typing import Any
from .. import attrdict


class ConfigFile(attrdict.AttrDict):
    """A dictionary-like object that represents a configuration file.

    This class extends the `attrdict.AttrDict` class to provide additional
    functionality for working with configuration files. In addition to the
    standard dictionary methods, it provides methods for evaluating the
    contents of the file as a Python module and for evaluating a specific
    key in the file.

    Attributes:
        content (str): The contents of the configuration file as a string.
    """

    def __init__(self, data=None, code=None):
        """Initialize a new instance of the `ConfigFile` class.

        Args:
            data (dict, optional): The initial data for the configuration file.
                Defaults to an empty dictionary.
            code (str, optional): The contents of the configuration file as a string.
                Defaults to `None`.
        """
        if data is None:
            data = {}
        super().__init__(data)
        self.content = code

    def eval_as_module(self):
        """Evaluate the contents of the configuration file as a Python module.

        Returns:
            A new module object that contains the evaluated contents of the
            configuration file.
        Raises:
            ValueError: If the contents of the configuration file are not defined.
        """
        if self.content is None:
            raise ValueError("Content is not defined")

        module = type(attrdict)("config_module")
        cc = compile(self.content, "<string>", "exec")  # noqa: DUO110
        eval(cc, module.__dict__)  # pylint: disable=W0123 # noqa: DUO104
        return module

    def eval_key(self, key) -> Any:
        """Evaluate a specific key in the configuration file.

        Args:
            key (str): The key to evaluate.

        Returns:
            The evaluated value of the specified key, or `None` if the key is not
            defined or its value is `None`.
        """
        val = self.get(key)
        if val and val.value:
            return eval(val.value)  # pylint: disable=W0123 # noqa: DUO104
        return None
