from pkg_resources import get_distribution

from verarandom.errors import *
from verarandom._random_generator import *
from verarandom.random_org_v1 import *
from verarandom._utils import set_module_names_for_sphinx


__version__ = get_distribution(__name__).version


objects_with_modified_module_names = [RandomConfig, VeraRandom, VeraRandomQuota]
set_module_names_for_sphinx(objects_with_modified_module_names, __name__)

__ALL__ = [
    *objects_with_modified_module_names, errors, random_org_v1, HTTPError,
]
