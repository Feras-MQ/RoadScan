"""Map explicit training labels to stable RoadScan labels, never by class position."""
import re

REQUIRED = {'D00', 'D10', 'D20', 'D40'}
ALIASES = {
    'd00': 'D00', 'longitudinalcrack': 'D00',
    'd10': 'D10', 'transversecrack': 'D10',
    'd20': 'D20', 'alligatorcrack': 'D20',
    'd40': 'D40', 'pothole': 'D40',
    'd00longitudinalcrack': 'D00', 'd10transversecrack': 'D10',
    'd20alligatorcrack': 'D20', 'd40pothole': 'D40',
    'other': 'OTHER', 'othercorruption': 'OTHER', 'othersurfacedamage': 'OTHER',
}

def class_mapping(names):
    if not isinstance(names, dict):
        raise ValueError('Class names must identify every class')
    mapped = {}
    for index, name in names.items():
        key = re.sub(r'[^a-z0-9]', '', str(name).lower())
        if key not in ALIASES:
            raise ValueError('Unsupported class label')
        mapped[int(index)] = ALIASES[key]
    values = set(mapped.values())
    if not REQUIRED.issubset(values) or values - REQUIRED - {'OTHER'} or len(values) != len(mapped):
        raise ValueError('Expected four road-damage classes and optional Other Corruption')
    if set(mapped) != set(range(len(mapped))):
        raise ValueError('Class indexes must be contiguous')
    return mapped
