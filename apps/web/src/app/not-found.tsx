import { ArrowLeft, Compass } from "lucide-react";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-6 text-center">
      <div className="border-line bg-elevated text-signal mb-5 flex size-12 items-center justify-center rounded-xl border">
        <Compass className="size-5" />
      </div>
      <p className="text-faint font-mono text-[10px] tracking-[0.2em] uppercase">404</p>
      <h1 className="text-ink mt-2 text-2xl font-medium tracking-tight">
        That route isn&apos;t built.
      </h1>
      <p className="text-muted mt-2 max-w-sm text-sm leading-relaxed">
        The page may be a planned module or the link may be incorrect. Start from the workspace and
        navigate from there.
      </p>
      <Link
        href="/dashboard"
        className="bg-signal text-signal-ink mt-6 inline-flex items-center gap-1.5 rounded-lg px-4 py-2.5 text-sm font-medium"
      >
        <ArrowLeft className="size-4" /> Back to workspace
      </Link>
    </div>
  );
}
