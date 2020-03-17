import os
import sys
from typing import Any, List, Dict
import importlib

from organoid_tracker.gui.application import Plugin
from organoid_tracker.gui.window import Window


class _ModulePlugin(Plugin):
    """A plugin that consists of a single .py file."""
    __loaded_script: Any

    def __init__(self, file_name: str):
        self.__loaded_script = _load_file(file_name)

    def init(self, window: Window):
        if hasattr(self.__loaded_script, 'init'):
            self.__loaded_script.init(window)

    def get_menu_items(self, window: Window):
        if hasattr(self.__loaded_script, 'get_menu_items'):
            return self.__loaded_script.get_menu_items(window)
        return {}

    def reload(self):
        importlib.reload(self.__loaded_script)


def _load_file(file: str) -> Any:
    """Loads the Python file as a normal module. A file stored in example_folder/test.py will end up as the module
    `example_folder.test`. In this way, relative imports still work fine."""
    file = os.path.abspath(file)
    if not file.endswith(".py") and not os.path.exists(os.path.join(file, "__init__.py")):
        raise ValueError("Not a Python file or module: " + file)
    parent_folder = os.path.dirname(file)
    grandparent_folder = os.path.dirname(parent_folder)

    # Add to path
    if grandparent_folder not in sys.path:
        sys.path.insert(0, grandparent_folder)

    # Load module
    file_name = os.path.basename(file)
    module_name = os.path.basename(parent_folder) + "." + \
                  (file_name[:-len(".py")] if file_name.endswith(".py") else file_name)
    return importlib.import_module(module_name)


def load_plugins(folder: str) -> List[Plugin]:
    """Loads the plugins in the given folder. The folder must follow the format "example/folder/structure". A plugin in
    "example/folder/structure/plugin_example.py" will be loaded as the module "structure.plugin_example".
    """
    if not os.path.exists(folder):
        print("No plugins folder found at " + os.path.abspath(folder))
        return []

    plugins = []
    for dir_entry in os.scandir(folder):
        file_name = dir_entry.name
        if not file_name.startswith("plugin_"):
            if file_name.endswith(".py"):
                print("Ignoring Python file " + file_name + " in " + folder
                      + " folder: it does not start with \"plugin_\"")
            continue
        if dir_entry.is_dir():
            file_path = os.path.join(folder, file_name)
            plugins.append(_ModulePlugin(file_path))
        elif file_name.endswith(".py"):
            file_path = os.path.join(folder, file_name)
            plugins.append(_ModulePlugin(file_path))
        else:
            print("Ignoring file " + file_name + " in " + folder
                  + " folder: is looks like a plugin, but is not a folder or a Python file.")
    return plugins
