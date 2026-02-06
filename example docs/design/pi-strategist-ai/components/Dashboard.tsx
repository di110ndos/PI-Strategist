import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts';
import { Team, Risk, Dependency } from '../types';
import { Sparkles, Activity, CheckCircle, AlertOctagon } from 'lucide-react';
import * as GeminiService from '../services/gemini';

interface DashboardProps {
  teams: Team[];
  risks: Risk[];
  dependencies: Dependency[];
}

const Dashboard: React.FC<DashboardProps> = ({ teams, risks, dependencies }) => {
  const [analysis, setAnalysis] = useState<{ summary: string; suggestions: string[] } | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [objectives, setObjectives] = useState<string[]>([]);

  const chartData = teams.map(t => ({
    name: t.name,
    Capacity: t.capacity,
    Load: t.features.reduce((sum, f) => sum + f.points, 0),
  }));

  const totalPoints = teams.reduce((acc, t) => acc + t.features.reduce((s, f) => s + f.points, 0), 0);
  const totalCapacity = teams.reduce((acc, t) => acc + t.capacity, 0);
  const healthScore = Math.min(100, Math.max(0, 100 - (Math.abs(totalCapacity - totalPoints) / totalCapacity) * 100));

  const handleSmartAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      const result = await GeminiService.analyzePlan(teams, risks, dependencies);
      setAnalysis({ summary: result.summary, suggestions: result.suggestions });
      
      const objs = await GeminiService.suggestObjectives(teams);
      setObjectives(objs);
    } catch (e) {
      console.error(e);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="p-8 h-full overflow-y-auto">
      <header className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">Program Dashboard</h2>
          <p className="text-slate-500 mt-1">Real-time overview of PI execution health</p>
        </div>
        <button
          onClick={handleSmartAnalyze}
          disabled={isAnalyzing}
          className={`flex items-center space-x-2 px-6 py-3 rounded-lg text-white font-semibold transition-all shadow-lg hover:shadow-xl ${
            isAnalyzing ? 'bg-slate-400 cursor-not-allowed' : 'bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500'
          }`}
        >
          <Sparkles size={20} className={isAnalyzing ? 'animate-spin' : ''} />
          <span>{isAnalyzing ? 'Consulting Gemini...' : 'Analyze Plan'}</span>
        </button>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center space-x-4">
          <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
            <Activity size={24} />
          </div>
          <div>
            <p className="text-slate-500 text-sm font-medium">Total Load</p>
            <p className="text-2xl font-bold text-slate-800">{totalPoints} <span className="text-sm text-slate-400 font-normal">pts</span></p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center space-x-4">
          <div className="p-3 bg-green-100 text-green-600 rounded-lg">
            <CheckCircle size={24} />
          </div>
          <div>
            <p className="text-slate-500 text-sm font-medium">Capacity Health</p>
            <p className="text-2xl font-bold text-slate-800">{healthScore.toFixed(0)}%</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center space-x-4">
          <div className="p-3 bg-amber-100 text-amber-600 rounded-lg">
            <AlertOctagon size={24} />
          </div>
          <div>
            <p className="text-slate-500 text-sm font-medium">Open Risks</p>
            <p className="text-2xl font-bold text-slate-800">{risks.length}</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center space-x-4">
          <div className="p-3 bg-purple-100 text-purple-600 rounded-lg">
            <Sparkles size={24} />
          </div>
          <div>
            <p className="text-slate-500 text-sm font-medium">Dependencies</p>
            <p className="text-2xl font-bold text-slate-800">{dependencies.length}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Chart */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-slate-100">
          <h3 className="text-lg font-bold text-slate-800 mb-6">Capacity vs Load by Team</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748b' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  cursor={{ fill: '#f1f5f9' }}
                />
                <Legend />
                <Bar dataKey="Capacity" fill="#cbd5e1" radius={[4, 4, 0, 0]} barSize={32} />
                <Bar dataKey="Load" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={32}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.Load > entry.Capacity ? '#ef4444' : '#6366f1'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AI Insights Panel */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex flex-col h-full">
          <div className="flex items-center space-x-2 mb-6">
            <Sparkles className="text-violet-600" size={20} />
            <h3 className="text-lg font-bold text-slate-800">Strategist Insights</h3>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 space-y-6">
            {analysis ? (
              <>
                <div className="bg-violet-50 p-4 rounded-lg border border-violet-100">
                  <h4 className="font-semibold text-violet-900 mb-2 text-sm uppercase tracking-wide">Executive Summary</h4>
                  <p className="text-slate-700 text-sm leading-relaxed">{analysis.summary}</p>
                </div>

                <div>
                  <h4 className="font-semibold text-slate-800 mb-3 text-sm uppercase tracking-wide">Key Suggestions</h4>
                  <ul className="space-y-3">
                    {analysis.suggestions.map((s, i) => (
                      <li key={i} className="flex items-start space-x-3 text-sm text-slate-600">
                        <span className="flex-shrink-0 w-6 h-6 bg-slate-100 rounded-full flex items-center justify-center text-xs font-bold text-slate-500">{i + 1}</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                
                {objectives.length > 0 && (
                   <div>
                    <h4 className="font-semibold text-slate-800 mb-3 text-sm uppercase tracking-wide">Proposed Objectives</h4>
                    <ul className="space-y-2">
                      {objectives.map((obj, i) => (
                        <li key={i} className="p-3 bg-slate-50 border-l-4 border-indigo-500 text-sm text-slate-700 italic">
                          "{obj}"
                        </li>
                      ))}
                    </ul>
                   </div>
                )}
              </>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center p-4">
                <Sparkles size={48} className="mb-4 opacity-20" />
                <p>Click "Analyze Plan" to generate AI-driven insights, risk assessments, and objective suggestions.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
