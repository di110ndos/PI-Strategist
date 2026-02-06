import React, { useState } from 'react';
import { Team, Feature } from '../types';
import { Plus, Trash2, Edit2, ChevronRight } from 'lucide-react';

interface TeamBoardProps {
  teams: Team[];
  setTeams: React.Dispatch<React.SetStateAction<Team[]>>;
}

const TeamBoard: React.FC<TeamBoardProps> = ({ teams, setTeams }) => {
  const [activeTeamId, setActiveTeamId] = useState<string>(teams[0]?.id || '');

  const addFeature = (teamId: string) => {
    const title = prompt("Feature Title:");
    if (!title) return;
    const pointsStr = prompt("Story Points:", "5");
    const points = parseInt(pointsStr || "0");

    setTeams(prev => prev.map(t => {
      if (t.id !== teamId) return t;
      return {
        ...t,
        features: [...t.features, { id: Date.now().toString(), title, points }]
      };
    }));
  };

  const removeFeature = (teamId: string, featureId: string) => {
    setTeams(prev => prev.map(t => {
      if (t.id !== teamId) return t;
      return {
        ...t,
        features: t.features.filter(f => f.id !== featureId)
      };
    }));
  };

  const updateCapacity = (teamId: string, newCap: number) => {
    setTeams(prev => prev.map(t => t.id === teamId ? { ...t, capacity: newCap } : t));
  };

  const activeTeam = teams.find(t => t.id === activeTeamId);

  return (
    <div className="p-8 h-full flex flex-col">
       <header className="mb-8">
          <h2 className="text-3xl font-bold text-slate-800">Teams & Backlog</h2>
          <p className="text-slate-500 mt-1">Manage team capacity and feature assignments</p>
        </header>

      <div className="flex flex-1 gap-8 overflow-hidden">
        {/* Team List Sidebar */}
        <div className="w-1/4 bg-white rounded-xl shadow-sm border border-slate-100 overflow-y-auto">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center">
            <h3 className="font-semibold text-slate-700">Teams</h3>
          </div>
          <div className="divide-y divide-slate-50">
            {teams.map(team => {
               const load = team.features.reduce((s, f) => s + f.points, 0);
               const isOverloaded = load > team.capacity;
               
               return (
                <button
                  key={team.id}
                  onClick={() => setActiveTeamId(team.id)}
                  className={`w-full text-left p-4 hover:bg-slate-50 transition-colors flex justify-between items-center ${
                    activeTeamId === team.id ? 'bg-blue-50 border-l-4 border-blue-500' : 'border-l-4 border-transparent'
                  }`}
                >
                  <div>
                    <div className="font-medium text-slate-800">{team.name}</div>
                    <div className={`text-xs mt-1 ${isOverloaded ? 'text-red-500 font-semibold' : 'text-slate-400'}`}>
                      {load} / {team.capacity} pts
                    </div>
                  </div>
                  <ChevronRight size={16} className={`text-slate-300 ${activeTeamId === team.id ? 'text-blue-400' : ''}`} />
                </button>
              );
            })}
          </div>
        </div>

        {/* Active Team Detail */}
        <div className="flex-1 bg-white rounded-xl shadow-sm border border-slate-100 flex flex-col">
          {activeTeam ? (
            <>
              <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-xl">
                <div className="flex items-center space-x-4">
                   <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center font-bold text-lg">
                      {activeTeam.name.substring(0, 1)}
                   </div>
                   <div>
                      <h3 className="text-xl font-bold text-slate-800">{activeTeam.name}</h3>
                      <div className="flex items-center space-x-2 text-sm text-slate-500">
                        <span>Capacity:</span>
                        <input 
                          type="number" 
                          value={activeTeam.capacity}
                          onChange={(e) => updateCapacity(activeTeam.id, parseInt(e.target.value) || 0)}
                          className="w-16 px-2 py-1 border border-slate-200 rounded text-slate-700 focus:outline-none focus:border-blue-500"
                        />
                      </div>
                   </div>
                </div>
                <button
                  onClick={() => addFeature(activeTeam.id)}
                  className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
                >
                  <Plus size={16} />
                  <span>Add Feature</span>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 bg-slate-50/30">
                {activeTeam.features.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400">
                    <p>No features assigned yet.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-4">
                    {activeTeam.features.map(feature => (
                      <div key={feature.id} className="group bg-white p-4 rounded-lg border border-slate-200 shadow-sm hover:shadow-md transition-all flex justify-between items-start">
                        <div>
                          <h4 className="font-semibold text-slate-800">{feature.title}</h4>
                          <span className="inline-block mt-2 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded font-medium">
                            {feature.points} pts
                          </span>
                        </div>
                        <button
                          onClick={() => removeFeature(activeTeam.id, feature.id)}
                          className="text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400">
              Select a team to manage features
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeamBoard;
