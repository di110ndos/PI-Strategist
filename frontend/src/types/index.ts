/**
 * Shared TypeScript types for the application.
 */

// ─── Red Flag Types ─────────────────────────────────────────────

export interface RedFlagItem {
  term: string;
  category: string;
  severity: 'critical' | 'moderate' | 'low';
  suggested_metric: string;
  negotiation_script: string;
}

export interface LineRedFlags {
  line: string;
  line_number: number;
  flags: RedFlagItem[];
}

// ─── Obligation Types ───────────────────────────────────────────

export interface ObligationItem {
  text: string;
  obligation_type: string;
  keyword: string;
}

export interface ObligationsResult {
  total: number;
  binding_count: number;
  commitment_count: number;
  negative_count: number;
  obligations: ObligationItem[];
}

// ─── SLA Types ──────────────────────────────────────────────────

export interface SLAFindingItem {
  text: string;
  metric_type: string;
  value: string | null;
  is_valid: boolean;
  issues: string[];
}

export interface SLAResult {
  total: number;
  valid_count: number;
  invalid_count: number;
  findings: SLAFindingItem[];
}

// ─── Quick Check Types ──────────────────────────────────────────

export interface QuickCheckResponse {
  red_flags: LineRedFlags[];
  obligations: ObligationsResult;
  sla: SLAResult;
  summary: {
    red_flags: { total: number; critical: number; moderate: number; low: number };
    obligations: { total: number; binding: number; commitment: number };
    sla: { total: number; valid: number; invalid: number };
  };
}

// ─── File Upload Types ──────────────────────────────────────────

export interface UploadedFile {
  file_id: string;
  filename: string;
  file_type: 'ded' | 'excel';
  size_bytes: number;
  uploaded_at: string;
}

// ─── Analysis Types ─────────────────────────────────────────────

export interface AnalysisSummary {
  risk: { total: number; critical: number; moderate: number; low: number };
  capacity: { total_sprints: number; passing: number; failing: number };
  deployment: { clusters: number };
}

export interface AnalysisResponse {
  analysis_id: string;
  status: string;
  created_at: string;
  results: Record<string, unknown>;
  summary: AnalysisSummary;
}
