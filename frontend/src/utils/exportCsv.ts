/**
 * Export analysis data to CSV using papaparse.
 */

import Papa from 'papaparse';
import type { AnalysisSummary } from '../types';

export function exportSummaryCsv(summary: AnalysisSummary, filename = 'pi_analysis_summary.csv') {
  const rows = [
    { Category: 'Risk', Metric: 'Total Red Flags', Value: summary.risk.total },
    { Category: 'Risk', Metric: 'High Severity', Value: summary.risk.high },
    { Category: 'Risk', Metric: 'Medium Severity', Value: summary.risk.medium },
    { Category: 'Risk', Metric: 'Low Severity', Value: summary.risk.low },
    { Category: 'Capacity', Metric: 'Total Sprints', Value: summary.capacity.total_sprints },
    { Category: 'Capacity', Metric: 'Passing', Value: summary.capacity.passing },
    { Category: 'Capacity', Metric: 'Failing', Value: summary.capacity.failing },
    { Category: 'Capacity', Metric: 'Avg Utilization %', Value: summary.capacity.average_utilization.toFixed(1) },
  ];

  if (summary.deployment) {
    rows.push(
      { Category: 'Deployment', Metric: 'Total Clusters', Value: summary.deployment.total_clusters },
      { Category: 'Deployment', Metric: 'CD Eligible %', Value: Number(summary.deployment.cd_eligible_percentage.toFixed(1)) },
    );
  }

  const csv = Papa.unparse(rows);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
