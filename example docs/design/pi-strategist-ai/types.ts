export interface Feature {
  id: string;
  title: string;
  points: number;
  description?: string;
}

export interface Team {
  id: string;
  name: string;
  capacity: number;
  features: Feature[];
  color: string;
}

export interface Dependency {
  id: string;
  fromFeatureId: string;
  toFeatureId: string;
  description: string;
}

export enum RiskStatus {
  RESOLVED = 'Resolved',
  OWNED = 'Owned',
  ACCEPTED = 'Accepted',
  MITIGATED = 'Mitigated',
  OPEN = 'Open'
}

export interface Risk {
  id: string;
  description: string;
  impact: 'High' | 'Medium' | 'Low';
  status: RiskStatus;
}

export interface AnalysisResult {
  risks: { description: string; impact: 'High' | 'Medium' | 'Low' }[];
  summary: string;
}

export type View = 'dashboard' | 'teams' | 'dependencies' | 'risks';
