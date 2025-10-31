import { useQuery, useMutation } from '@tanstack/react-query';
import { getOpenSearchHealth, getOpenSearchStats, refreshIndex } from '@/services/api';

export default function OpsTab() {
  const health = useQuery({ queryKey: ['os-health'], queryFn: getOpenSearchHealth });
  const stats = useQuery({ queryKey: ['os-stats'], queryFn: getOpenSearchStats });
  const refresh = useMutation({ mutationFn: refreshIndex, onSuccess: () => { health.refetch(); stats.refetch(); } });

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="card p-6">
        <h3 className="text-xl font-semibold text-white mb-3">OpenSearch Health</h3>
        <pre className="text-xs text-zinc-300 whitespace-pre-wrap">{JSON.stringify(health.data, null, 2)}</pre>
      </div>
      <div className="card p-6">
        <h3 className="text-xl font-semibold text-white mb-3">Index Stats</h3>
        <pre className="text-xs text-zinc-300 whitespace-pre-wrap">{JSON.stringify(stats.data, null, 2)}</pre>
        <button className="btn btn-primary mt-4" onClick={() => refresh.mutate()} disabled={refresh.isPending}>Refresh Index</button>
      </div>
    </div>
  );
}

