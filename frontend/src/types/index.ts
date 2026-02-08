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
  risk: {
    total: number;
    high: number;
    medium: number;
    low: number;
  };
  capacity: {
    total_sprints: number;
    passing: number;
    failing: number;
    average_utilization: number;
  };
  deployment?: {
    total_clusters: number;
    cd_eligible_percentage: number;
  };
}

export interface AnalysisResponse {
  analysis_id: string;
  status: string;
  created_at: string;
  results: Record<string, unknown>;
  summary: AnalysisSummary;
}

// ─── Chart Data Types ──────────────────────────────────────────

export interface SprintAnalysisData {
  sprint: {
    name: string;
    total_hours: number;
    net_capacity: number;
    sprint_load: number;
    buffer_hours: number;
    tasks: Array<{ id: string; name: string; hours: number }>;
  };
  status: string;
  utilization_percent: number;
  overflow_hours: number;
  high_risk_tasks: Array<{ id: string; name: string; hours: number }>;
  recommendations: Array<{
    task: { id: string; name: string; hours: number };
    from_sprint: string;
    to_sprint: string;
    reason: string;
    priority: number;
  }>;
}

export interface ResourceData {
  name?: string;
  discipline?: string;
  total_hours: number;
  rate?: number;
  max_hours?: number;
  allocation_percentage?: number;
  sprint_hours?: Record<string, number>;
  project_hours?: Record<string, number>;
  status?: 'over' | 'under' | 'optimal';
}

export interface ProjectData {
  name?: string;
  total_hours: number;
  priority?: number;
  sprint_allocation?: Record<string, number>;
}

export interface PIAnalysisData {
  resources?: Record<string, ResourceData>;
  projects?: Record<string, ProjectData>;
  sprints?: string[];
  total_capacity?: number;
  total_allocated?: number;
  grand_total_hours?: number;
}

// ─── AI Insights Types ─────────────────────────────────────────

export interface AIRecommendation {
  category: string;
  priority: string;
  title: string;
  description: string;
  action_items: string[];
  impact: string;
  affected_resources: string[];
  affected_sprints: string[];
}

export interface RebalancingSuggestion {
  action: string;
  reason: string;
  priority: string;
  impact: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AIInsightsResponse {
  executive_summary: string;
  recommendations: AIRecommendation[];
  risk_assessment: string;
  optimization_opportunities: string[];
  key_metrics_commentary: string;
  rebalancing_suggestions: RebalancingSuggestion[];
}

// ─── PI Objectives Types ──────────────────────────────────────

export interface PIObjective {
  objective_id: string;
  name: string;
  description: string;
  objective_type: 'committed' | 'stretch';
  business_value: number;
  status: 'planned' | 'in_progress' | 'completed' | 'at_risk';
  acceptance_criteria: string;
  linked_stories: string[];
  created_at: string;
  updated_at: string;
}

// ─── Risk Register Types ──────────────────────────────────────

export interface Risk {
  risk_id: string;
  title: string;
  description: string;
  category: 'technical' | 'resource' | 'schedule' | 'scope' | 'external' | 'general';
  probability: number;
  impact: number;
  risk_score: number;
  owner: string;
  mitigation_plan: string;
  status: 'open' | 'mitigating' | 'mitigated' | 'accepted' | 'closed';
  created_at: string;
  updated_at: string;
}

export interface RiskSummary {
  total: number;
  by_status: Record<string, number>;
  average_score: number;
  heat_map: number[][];
}
