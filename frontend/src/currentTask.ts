export type CurrentResult<T> = {current: true; value: T} | {current: false};

// Late results and late failures must not update a newer browser session.
export async function currentResult<T>(operation: () => Promise<T>, isCurrent: () => boolean): Promise<CurrentResult<T>> {
  try {
    const value = await operation();
    return isCurrent() ? {current: true, value} : {current: false};
  } catch (error) {
    if (isCurrent()) throw error;
    return {current: false};
  }
}

export async function currentMedia<T extends {getTracks(): {stop(): void}[]}>(acquire: () => Promise<T>, isCurrent: () => boolean): Promise<CurrentResult<T>> {
  return currentResult(async () => {
    const media = await acquire();
    if (!isCurrent()) media.getTracks().forEach(track => track.stop());
    return media;
  }, isCurrent);
}
