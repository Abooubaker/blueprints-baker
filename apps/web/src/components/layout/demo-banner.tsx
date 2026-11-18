import { FlaskConical } from "lucide-react";
import Link from "next/link";

import { DEMO_MODE, DEMO_PROJECT_ID } from "@/lib/constants";

/**
 * The Pages build is static. Make that visible everywhere in the workspace so
 * "Run pipeline" and "Regenerate" are never mistaken for live computation.
 */
export function DemoBanner() {
  if (!DEMO_MODE) return null;
  return (
    <div className="border-signal/20 bg-signal/[0.06] border-b">
      <div className="mx-auto flex max-w-[1440px] flex-wrap items-center gap-x-2 gap-y-1 px-4 py-2 text-[11px] sm:px-6 lg:px-8">
        <FlaskConical className="text-signal size-3.5 shrink-0" />
        <span className="text-ink font-medium">Static demo.</span>
        <span className="text-muted">
          Everything here is precomputed by the real engine; writes and live agent runs need the
          full API.
        </span>
        <Link
          href={`/projects/${DEMO_PROJECT_ID}/wiring`}
          className="text-signal ml-auto shrink-0 hover:underline"
        >
          Open the wiring plan
        </Link>
      </div>
    </div>
  );
}
