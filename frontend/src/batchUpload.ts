export type BatchItem = {
  file: File;
  status: 'queued' | 'uploading' | 'saved' | 'failed' | 'unconfirmed' | 'rejected';
  id?: string;
  error?: string;
};

export const MAX_BATCH_FILES = 20;

export function retryFailed(items: BatchItem[]): BatchItem[] {
  // Unknown outcomes may already be saved, so never include them in a bulk retry.
  return items.map(item => item.status === 'failed' ? {...item, status: 'queued', error: undefined} : item);
}

export function prepareBatch(files: File[], maxBytes: number): BatchItem[] {
  if (files.length > MAX_BATCH_FILES) throw new Error('too-many-files');
  return files.map(file => {
    const error = !['image/jpeg', 'image/png', 'image/webp'].includes(file.type) ? 'unsupported' : file.size > maxBytes ? 'too-large' : undefined;
    return {file, status: error ? 'rejected' : 'queued', error};
  });
}

// Finish the current POST before stopping: aborting it could hide an already-saved report.
export async function runBatch(items: BatchItem[], upload: (file: File) => Promise<string>, update: (index: number, item: BatchItem) => void, stopped: () => boolean) {
  for (let index = 0; index < items.length; index++) {
    if (stopped()) break;
    const item = items[index];
    if (item.status !== 'queued') continue;
    update(index, {...item, status: 'uploading', error: undefined});
    try {
      const id = await upload(item.file);
      update(index, {...item, status: 'saved', id, error: undefined});
    } catch (error) {
      const code = error && typeof error === 'object' && 'status' in error ? error.status : undefined;
      const confirmedRejection = typeof code === 'number' && code >= 400 && code < 500;
      update(index, {...item, status: confirmedRejection ? 'failed' : 'unconfirmed', error: error instanceof Error ? error.message : String(error)});
    }
  }
}
