import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteDocument, getDocumentsByParish } from '@/services/api';

export default function DocumentsTab() {
  const qc = useQueryClient();
  const parishId = localStorage.getItem('selectedParishId') || '';

  const q = useQuery({
    queryKey: ['docs', parishId],
    queryFn: () => getDocumentsByParish(parishId),
    enabled: !!parishId,
  });

  const del = useMutation({
    mutationFn: (fileId: string) => deleteDocument(fileId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['docs'] }),
  });

  return (
    <div className="space-y-4">
      <div className="grid gap-3">
        {q.isLoading && <div>Loading…</div>}
        {q.data?.results?.map((r: any) => (
          <div key={r.file_id} className="card p-4 flex items-center justify-between">
            <div>
              <div className="text-zinc-100 font-medium">{r.filename}</div>
              <div className="text-zinc-400 text-sm">{r.document_type} · chunks: {r.chunk_count}</div>
            </div>
            <div className="flex gap-2">
              <a className="btn btn-secondary" href={`/doc/${encodeURIComponent(r.s3_key || r.file_id)}`}>View</a>
              <button className="btn btn-secondary" onClick={() => del.mutate(r.file_id)} disabled={del.isPending}>Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

