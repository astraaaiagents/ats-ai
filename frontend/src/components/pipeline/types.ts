/* ── Pipeline Types ─────────────────────────────────────────────────

   Shared types for pipeline components.
*/

import { type PipelineStage } from "@/lib/api/types";

export interface PipelineCandidate {
  id: string;
  name: string;
  title: string;
  fitScore: number;
  skills: string[];
  stage: PipelineStage;
  jobId?: string;
}
