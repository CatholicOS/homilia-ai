import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getDocumentContent } from '@/services/api';

export default function DocViewerPage() {
  const { encodedKey } = useParams();
  const q = useQuery({
    queryKey: ['doc', encodedKey],
    queryFn: () => getDocumentContent(encodedKey!),
    enabled: !!encodedKey,
  });

  const data = q.data;
  const isPdf = (data?.content_type || '').includes('pdf') || (data?.filename || '').toLowerCase().endsWith('.pdf');

  return (
    <div className="container-max py-8">
      <h2 className="text-2xl font-semibold text-white mb-4">Document</h2>
      {q.isLoading && <div>Loading…</div>}
      {data && (
        <div className="card p-4">
          <div className="text-sm text-zinc-300 mb-4">{data.filename} · {data.content_type}</div>
          {isPdf ? (
            <iframe title="pdf" className="w-full h-[70vh] bg-zinc-950" src={`data:${data.content_type};base64,${data.content}`} />
          ) : data.encoding === 'base64' ? (
            <a className="btn btn-primary" href={`data:${data.content_type};base64,${data.content}`} download={data.filename}>Download</a>
          ) : (
            <pre className="whitespace-pre-wrap text-sm">{data.content}</pre>
          )}
        </div>
      )}
    </div>
  );
}

