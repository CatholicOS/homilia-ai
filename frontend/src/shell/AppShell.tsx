import { Outlet, Link, useNavigate } from 'react-router-dom';
import ParishSelector from '@/components/ParishSelector';

export default function AppShell() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex flex-col">
      <a href="#main" className="skip-link">Skip to main content</a>
      <header className="sticky top-0 z-40 border-b border-zinc-800 bg-[#0f0f10]/80 backdrop-blur">
        <div className="container-max flex items-center justify-between h-16">
          <Link to="/" className="text-xl font-semibold tracking-wide text-white">
            Homilia
          </Link>
          <div className="flex items-center gap-4">
            <ParishSelector />
            <button className="btn btn-primary" onClick={() => navigate('/chat')}>Start chat</button>
          </div>
        </div>
      </header>

      <main id="main" role="main" className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-zinc-800 py-8 text-sm text-zinc-400">
        <div className="container-max flex items-center justify-between">
          <span>© {new Date().getFullYear()} Homilia</span>
          <nav className="flex gap-6">
            <Link to="/" className="hover:text-zinc-200">Home</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}

