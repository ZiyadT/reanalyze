import {
  ArrowUpRight,
  FileText,
  Search,
  Sparkles,
  Upload,
} from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50">
      <nav className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-8 py-5">
          <h1 className="text-xl font-bold text-slate-900">
            ReAnalyze
          </h1>
          <span className="text-sm text-slate-500">
            AI Research Workspace
          </span>
        </div>
      </nav>

      <section className="mx-auto max-w-7xl px-8 py-12">
        <h2 className="text-3xl font-bold tracking-tight text-slate-900">
          Your Research Workspace
        </h2>

        <p className="mt-2 text-slate-500">
          Analyze documents, ask questions, and generate insights using AI.
        </p>

        <div className="mt-10 grid gap-6 md:grid-cols-5">
          <div className="rounded-xl border border-slate-200 bg-white p-7 shadow-sm md:col-span-3">
            <Sparkles className="mb-5 h-8 w-8 text-blue-600" />

            <h3 className="text-xl font-semibold text-slate-900">
              Ask your research analyst
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Ask questions about your documents and research.
            </p>

            <textarea
              placeholder="What would you like to research?"
              className="mt-6 min-h-36 w-full resize-none rounded-lg border border-slate-200 p-4 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />

            <button className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-blue-700">
              Start research
              <ArrowUpRight className="h-4 w-4" />
            </button>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-7 shadow-sm md:col-span-2">
            <Upload className="mb-5 h-8 w-8 text-blue-600" />

            <h3 className="text-xl font-semibold text-slate-900">
              Upload documents
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Add PDFs and research materials to your knowledge base.
            </p>

            <div className="mt-6 flex min-h-36 flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-200 bg-slate-50">
              <FileText className="h-9 w-9 text-slate-400" />
              <p className="mt-3 text-sm text-slate-500">
                Document upload coming soon
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}