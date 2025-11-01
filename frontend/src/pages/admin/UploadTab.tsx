import { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { useMutation } from '@tanstack/react-query';
import { uploadDocument } from '@/services/api';

export default function UploadTab() {
  const [file, setFile] = useState<File | null>(null);
  const [parishId, setParishId] = useState(localStorage.getItem('selectedParishId') || '');
  const [documentType, setDocumentType] = useState('homily');
  const [sermonDate, setSermonDate] = useState<Date | null>(null);

  const formatDate = (d: Date | null): string | undefined => {
    if (!d) return undefined;
    const year = d.getFullYear();
    const month = `${d.getMonth() + 1}`.padStart(2, '0');
    const day = `${d.getDate()}`.padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const m = useMutation({
    mutationFn: () => {
      if (!file || !parishId) throw new Error('Missing file or parish');
      return uploadDocument({ file, parishId, documentType, sermonDate: formatDate(sermonDate) });
    }
  });

  return (
    <div className="card p-6 max-w-2xl">
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-zinc-300 mb-2">Parish</label>
          <input className="w-full bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2" value={parishId} onChange={(e) => setParishId(e.target.value)} placeholder="e.g. st_marys" />
        </div>
        <div>
          <label className="block text-sm text-zinc-300 mb-2">Document type</label>
          <select className="w-full bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2" value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
            <option value="homily">Homily</option>
            <option value="bulletin">Bulletin</option>
            <option value="document">Document</option>
          </select>
        </div>
        <div>
          <label className="block text-sm text-zinc-300 mb-2">Sermon date (optional)</label>
          <DatePicker
            selected={sermonDate}
            onChange={(date: Date | null) => setSermonDate(date)}
            placeholderText="Select date"
            className="w-full bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2"
            calendarClassName="bg-zinc-900 border border-zinc-700 text-zinc-100"
            popperClassName="z-50"
            dateFormat="yyyy-MM-dd"
            isClearable
          />
        </div>
        <div>
          <label className="block text-sm text-zinc-300 mb-2">File</label>
          <input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </div>
        <button className="btn btn-primary" disabled={!file || !parishId || m.isPending} onClick={() => m.mutate()}>
          {m.isPending ? 'Uploading…' : 'Upload'}
        </button>
        {m.isError && <div className="text-red-400 text-sm">{(m.error as any)?.message ?? 'Upload failed'}</div>}
        {m.isSuccess && m.data?.success && <div className="text-green-400 text-sm">Uploaded: {m.data.filename}</div>}
      </div>
    </div>
  );
}

