from typing import List


def set_module_names_for_sphinx(modules: List[str], new_name: str):
    """ Trick sphinx into displaying the desired module in these objects' documentation. """
    for obj in modules:
        obj.__module__ = new_name
