"""Conservative local review state machine; not a substitute for RBAC."""
from fastapi import HTTPException

ACTIONS = {
    'Confirmed': 'confirm',
    'Assigned': 'assign',
    'Resolved': 'resolve',
    'Duplicate': 'duplicate',
}

def validate_transition(previous: str, target: str | None, action: str) -> None:
    if target is None or target == previous:
        return
    if target in ACTIONS and action != ACTIONS[target]:
        raise HTTPException(422, f'{target} requires action {ACTIONS[target]}')
    if target == 'Assigned' and previous != 'Confirmed':
        raise HTTPException(409, 'A human must confirm the report before assignment')
    if target == 'Resolved' and previous not in {'Confirmed', 'Assigned'}:
        raise HTTPException(409, 'A report must be confirmed before closure')
    if previous == 'Resolved' and target not in {'Needs Review'}:
        raise HTTPException(409, 'Reopen resolved reports for review before changing status')
