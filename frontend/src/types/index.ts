export interface TraceStep {
  id: string;
  name: string;
  description: string;
  status: "completed" | "active" | "pending";
  timestamp?: string;
  progress?: number; // 0 to 100 for progress bar
}

export interface AuditCheck {
  id: string;
  name: string;
  status: "verified" | "attention" | "pending";
}

export interface Scorecard {
  score: number;
  checks: AuditCheck[];
  summary: string;
}

export interface DocumentSessionState {
  sessionId: string;
  archetype: string;
  documentContent: string;
  status: "idle" | "running" | "paused" | "completed" | "error";
  loopCount: number;
  maxLoops: number;
  scorecard: Scorecard;
  trace: TraceStep[];
}
