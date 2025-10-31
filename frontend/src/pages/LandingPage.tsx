import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <section className="section bg-[#0f0f10]">
      <div className="container-max text-center">
        <h1 className="text-5xl md:text-6xl font-semibold tracking-tight text-white max-w-3xl mx-auto">
          Calm, scholarly answers from your parish documents
        </h1>
        <p className="mt-6 text-lg text-zinc-300 max-w-2xl mx-auto">
          Upload homilies and bulletins. Ask questions. Receive high-contrast, authoritative responses.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link to="/chat" className="btn btn-primary">Start now</Link>
          <Link to="/admin" className="btn btn-secondary">Admin console</Link>
        </div>
      </div>
    </section>
  );
}

