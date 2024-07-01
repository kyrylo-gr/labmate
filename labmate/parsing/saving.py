"""This file contains functions that prepare file for saving for further parsing."""

from typing import Dict

from . import parse_str


def append_values_from_modules_to_files(
    configs: Dict[str, str], evals_modules: dict
) -> Dict[str, str]:
    """Update configs dictionary by appending values from modules that is no clear from parsing.

    Args:
        configs (Dict[str, str]): Dictionary of the config files {name: content}.
        It would be modified.
        evals_modules (dict): Dictionary of the modules {name: module}.

    Returns:
        Dict[str, str]: Updated configs dictionary.

    Example:
        see `append_values_from_module_to_file` to get understanding of the idea.

    """
    for file, module in evals_modules.items():
        configs[file] = append_values_from_module_to_file(configs[file], module)
    return configs


def append_values_from_module_to_file(
    body: str, module, separator="  # value: "
) -> str:
    """Add values from a module to a given file body.

    Args:
        body (str): The file body to add values to.
        module (module): The module to extract values from.

    Returns:
        Multiline string of the updated file body with added values.

    Example:
        Let you know your config file `config_file.py`:
        ```
            param1 = 123
            param2 = param1
        ```
        That you import inside your python script:
        ```
        import config_file as config_file_module
        ```
        Than your can append values from the module to the file body:
        ```
            file_content = read_file('config_file.py')
            file_content_with_value = \
                append_values_from_module_to_file(file_content, config_file_module)
        ```
        The output that you get is the following `file_content_with_value`:
        ```
            param1 = 123
            param2 = param1  # value: 123
        ```

    """
    variables = vars(module)
    lines = body.split("\n")
    for i, line in enumerate(lines):
        for key, (val, _) in parse_str(line).items():
            real_val = variables.get(key, "")
            if (
                isinstance(val, str)
                and isinstance(real_val, str)
                and real_val != val.strip("\"'")
            ) or (
                isinstance(val, str)
                and isinstance(real_val, (float, int, complex))
                and not isinstance(real_val, bool)
            ):
                lines[i] += f"{separator}{real_val}"

    return "\n".join(lines)
