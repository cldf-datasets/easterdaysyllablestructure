from .Morphology import Morphology
from .Suprasegmentals import Suprasegmentals
from .Sound_inventory import Sound_inventory
from .Syllable_structure import Syllable_structure

PARAM_CLASSES = {
    cls.__name__.replace('_', ' '): cls
    for cls in [Morphology, Sound_inventory, Suprasegmentals, Syllable_structure]}
