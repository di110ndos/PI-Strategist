/**
 * Export analysis summary to PDF using jspdf + autotable.
 */

import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { AnalysisSummary } from '../types';

export function exportSummaryPdf(summary: AnalysisSummary, title = 'PI Analysis Summary') {
  const doc = new jsPDF();

  doc.setFontSize(18);
  doc.text(title, 14, 20);
  doc.setFontSize(10);
  doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 28);

  // Risk summary table
  autoTable(doc, {
    startY: 35,
    head: [['Risk Metric', 'Value']],
    body: [
      ['Total Red Flags', String(summary.risk.total)],
      ['High Severity', String(summary.risk.high)],
      ['Medium Severity', String(summary.risk.medium)],
      ['Low Severity', String(summary.risk.low)],
    ],
    theme: 'striped',
  });

  // Capacity summary table
  const lastY = (doc as any).lastAutoTable?.finalY ?? 80;
  autoTable(doc, {
    startY: lastY + 10,
    head: [['Capacity Metric', 'Value']],
    body: [
      ['Total Sprints', String(summary.capacity.total_sprints)],
      ['Passing', String(summary.capacity.passing)],
      ['Failing', String(summary.capacity.failing)],
      ['Avg Utilization', `${summary.capacity.average_utilization.toFixed(1)}%`],
    ],
    theme: 'striped',
  });

  // Deployment summary
  if (summary.deployment) {
    const lastY2 = (doc as any).lastAutoTable?.finalY ?? 140;
    autoTable(doc, {
      startY: lastY2 + 10,
      head: [['Deployment Metric', 'Value']],
      body: [
        ['Total Clusters', String(summary.deployment.total_clusters)],
        ['CD Eligible', `${summary.deployment.cd_eligible_percentage.toFixed(1)}%`],
      ],
      theme: 'striped',
    });
  }

  doc.save(`${title.replace(/\s+/g, '_')}.pdf`);
}
