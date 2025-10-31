import { useEffect, useState } from 'react';

type Parish = { id: string; name: string };

export default function ParishSelector() {
  const [parishes, setParishes] = useState<Parish[]>([]);
  const [value, setValue] = useState<string>(localStorage.getItem('selectedParishId') || '');

  useEffect(() => {
    // Placeholder for future /parishes; keep minimal for MVP
    setParishes([
      { id: 'st_marys', name: 'St. Mary’s' },
      { id: 'st_johns', name: 'St. John’s' },
    ]);
  }, []);

  useEffect(() => {
    if (value) localStorage.setItem('selectedParishId', value);
  }, [value]);

  return (
    <select
      aria-label="Select parish"
      className="bg-zinc-900 border border-zinc-700 rounded-md px-3 py-2 text-sm"
      value={value}
      onChange={(e) => setValue(e.target.value)}
    >
      <option value="">Select parish…</option>
      {parishes.map((p) => (
        <option key={p.id} value={p.id}>{p.name}</option>
      ))}
    </select>
  );
}

