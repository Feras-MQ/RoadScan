export const reviewStatuses = ['Needs Review', 'Confirmed', 'Assigned', 'Resolved', 'Duplicate'] as const;

const actions: Record<string, string> = {
  Confirmed: 'confirm', Assigned: 'assign', Resolved: 'resolve', Duplicate: 'duplicate',
};

export function canReviewTransition(previous: string, target: string): boolean {
  if (!reviewStatuses.some(status => status === target)) return false;
  if (previous === target || target === 'Needs Review') return true;
  if (previous === 'Resolved') return false;
  if (target === 'Assigned') return previous === 'Confirmed';
  if (target === 'Resolved') return previous === 'Confirmed' || previous === 'Assigned';
  return true;
}

export function reviewPayload(previous: string, status: string, note: string) {
  if (!canReviewTransition(previous, status)) {
    throw new Error('Confirm a report before assigning or resolving it. Reopen resolved reports before changing their status.');
  }
  return {status, note, action: previous === status ? 'review' : actions[status] || 'review'};
}
