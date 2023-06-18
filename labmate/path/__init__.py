"""Path module.

Functionality added to classical Path form pathlib:

- sum 2 path or path and str. Action: sum 2 str
- makedirs. Action: os.makedirs
- make_extension
- dirname
- basename


Examples:
---------
>>> from labmate.path import Path
>>> path = Path("some_folder")
>>> path.makedirs()
>>> path = path / "some_file" # -> "some_folder/some_file"
>>> path = path + ".json" # -> "some_folder/some_file.json"
>>> path.basename # -> "some_file.json"

"""

from .path_class import Path, get_file_path  # noqa: F401
