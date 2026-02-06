import React from 'react';
import { Risk, RiskStatus, Team, Dependency } from '../types';
import { AlertTriangle, Plus, Check, Shield, User, Archive } from 'lucide-react';
import * as GeminiService from '../services/gemini';

interface RiskRegisterProps {
  risks: Risk[];
  setRisks: React.Dispatch<React.SetStateAction<Risk[]>>;
  teams: Team[];
  dependencies: Dependency[];
}

const RiskRegister: React.FC<RiskRegisterProps> = ({ risks, setRisks, teams, dependencies }) => {
  const [loading, setLoading] = React.useState(false);

  const addRisk = () => {
    const desc = prompt("Risk Description:");
    if (!desc) return;
    setRisks(prev => [...prev, {
      id: Date.now().toString(),
      description: desc,
      impact: 'Medium',
      status: RiskStatus.OPEN
    }]);
  };

  const updateRiskStatus = (id: string, status: RiskStatus) => {
    setRisks(prev => prev.map(r => r.id === id ? { ...r, status } : r));
  };

  const suggestRisks = async () => {
    setLoading(true);
    try {
      const result = await GeminiService.analyzePlan(teams, risks, dependencies);
      if (result && result.risks) {
        const newRisks: Risk[] = result.risks.map((r, i) => ({
          id: `ai-${Date.now()}-${i}`,
          description: r.description,
          impact: r.impact,
          status: RiskStatus.OPEN
        }));
        setRisks(prev => [...prev, ...newRisks]);
      }
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: RiskStatus) => {
    switch (status) {
      case RiskStatus.RESOLVED: return <Check size={16} className="text-green-600" />;
      case RiskStatus.OWNED: return <User size={16} className="text-blue-600" />;
      case RiskStatus.ACCEPTED: return <Archive size={16} className="text-amber-600" />;
      case RiskStatus.MITIGATED: return <Shield size={16} className="text-purple-600" />;
      default: return <AlertTriangle size={16} className="text-red-600" />;
    }
  };

  const getStatusColor = (status: RiskStatus) => {
    switch (status) {
      case RiskStatus.RESOLVED: return 'bg-green-50 border-green-200 text-green-700';
      case RiskStatus.OWNED: return 'bg-blue-50 border-blue-200 text-blue-700';
      case RiskStatus.ACCEPTED: return 'bg-amber-50 border-amber-200 text-amber-700';
      case RiskStatus.MITIGATED: return 'bg-purple-50 border-purple-200 text-purple-700';
      default: return 'bg-red-50 border-red-200 text-red-700';
    }
  };

  const columns = [
    { title: 'Open Risks', status: RiskStatus.OPEN },
    { title: 'ROAMed', status: 'ROAM' } // Virtual group for display
  ];

  return (
    <div className="p-8 h-full flex flex-col">
      <header className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">Risk Register</h2>
          <p className="text-slate-500 mt-1">Manage and ROAM program risks</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={suggestRisks}
            disabled={loading}
            className="px-4 py-2 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 transition-colors font-medium text-sm border border-indigo-200"
          >
            {loading ? 'Scanning...' : 'AI Risk Scan'}
          </button>
          <button
            onClick={addRisk}
            className="flex items-center space-x-2 bg-slate-900 text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors text-sm font-medium"
          >
            <Plus size={16} />
            <span>Add Risk</span>
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                <th className="p-4 font-semibold w-1/2">Description</th>
                <th className="p-4 font-semibold">Impact</th>
                <th className="p-4 font-semibold">Status</th>
                <th className="p-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {risks.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-8 text-center text-slate-400">
                    No risks identified. Good job, or look closer?
                  </td>
                </tr>
              ) : risks.map(risk => (
                <tr key={risk.id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="p-4">
                    <p className="text-slate-800 font-medium">{risk.description}</p>
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      risk.impact === 'High' ? 'bg-red-100 text-red-800' :
                      risk.impact === 'Medium' ? 'bg-orange-100 text-orange-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {risk.impact}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-md border text-xs font-bold uppercase ${getStatusColor(risk.status)}`}>
                      {getStatusIcon(risk.status)}
                      <span>{risk.status}</span>
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex justify-end space-x-2">
                       {/* ROAM Actions */}
                       <button title="Resolve" onClick={() => updateRiskStatus(risk.id, RiskStatus.RESOLVED)} className="p-2 hover:bg-green-100 text-slate-400 hover:text-green-600 rounded"><Check size={16}/></button>
                       <button title="Own" onClick={() => updateRiskStatus(risk.id, RiskStatus.OWNED)} className="p-2 hover:bg-blue-100 text-slate-400 hover:text-blue-600 rounded"><User size={16}/></button>
                       <button title="Accept" onClick={() => updateRiskStatus(risk.id, RiskStatus.ACCEPTED)} className="p-2 hover:bg-amber-100 text-slate-400 hover:text-amber-600 rounded"><Archive size={16}/></button>
                       <button title="Mitigate" onClick={() => updateRiskStatus(risk.id, RiskStatus.MITIGATED)} className="p-2 hover:bg-purple-100 text-slate-400 hover:text-purple-600 rounded"><Shield size={16}/></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default RiskRegister;
