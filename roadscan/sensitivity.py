"""Draft-priority sensitivity analysis; never substitutes for measured model results."""
from .core import WEIGHTS, score

def scenarios(detections, width, height):
    baseline, _ = score(detections, width, height)
    result = {'baseline': baseline, 'weights': dict(WEIGHTS), 'variations': []}
    for component in WEIGHTS:
        for multiplier in (0.8, 1.2):
            candidate = dict(WEIGHTS)
            candidate[component] *= multiplier
            total = sum(candidate.values())
            candidate = {k: v / total for k, v in candidate.items()}
            value, parts = score(detections, width, height, candidate)
            result['variations'].append({'component': component, 'multiplier': multiplier,
                                         'weights': candidate, 'score': value,
                                         'difference': None if value is None or baseline is None else round(value-baseline, 2),
                                         'parts': parts})
    return result
