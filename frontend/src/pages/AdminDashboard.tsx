import { useSearchParams } from 'react-router-dom';
import UploadTab from './admin/UploadTab';
import DocumentsTab from './admin/DocumentsTab';
import OpsTab from './admin/OpsTab';

export default function AdminDashboard() {
  const [params, setParams] = useSearchParams();
  const tab = params.get('tab') || 'upload';
  const setTab = (t: string) => setParams({ tab: t });

  return (
    <div className="container-max py-10">
      <h2 className="text-3xl font-semibold text-white mb-6">Admin</h2>
      <div className="border-b border-zinc-800 mb-6">
        <nav className="flex gap-6">
          {['upload','documents','ops'].map((t) => (
            <button key={t} className={`py-3 border-b-2 ${tab===t ? 'border-[var(--color-accent)] text-zinc-100' : 'border-transparent text-zinc-400'}`} onClick={() => setTab(t)}>
              {t.charAt(0).toUpperCase()+t.slice(1)}
            </button>
          ))}
        </nav>
      </div>
      {tab === 'upload' && <UploadTab />}
      {tab === 'documents' && <DocumentsTab />}
      {tab === 'ops' && <OpsTab />}
    </div>
  );
}

