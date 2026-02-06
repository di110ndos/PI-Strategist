import React, { useState, useEffect } from 'react';
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import TeamBoard from './components/TeamBoard';
import DependencyGraph from './components/DependencyGraph';
import RiskRegister from './components/RiskRegister';
import { View, Team, Risk, Dependency, RiskStatus } from './types';

// Mock Data for Initial State
const INITIAL_TEAMS: Team[] = [
  {
    id: 't1', name: 'Alpha Squad', capacity: 40, color: '#3b82f6',
    features: [
      { id: 'f1', title: 'User Authentication', points: 8 },
      { id: 'f2', title: 'Profile Management', points: 5 },
      { id: 'f3', title: 'Email Notifications', points: 3 },
    ]
  },
  {
    id: 't2', name: 'Beta Force', capacity: 35, color: '#8b5cf6',
    features: [
      { id: 'f4', title: 'Payment Gateway', points: 13 },
      { id: 'f5', title: 'Order History', points: 5 },
    ]
  },
  {
    id: 't3', name: 'Gamma Rays', capacity: 30, color: '#10b981',
    features: [
      { id: 'f6', title: 'Admin Dashboard', points: 13 },
      { id: 'f7', title: 'Analytics API', points: 8 },
      { id: 'f8', title: 'Export Tool', points: 20 }, // Overloaded
    ]
  }
];

const INITIAL_RISKS: Risk[] = [
  { id: 'r1', description: 'Payment API latency might impact UX', impact: 'High', status: RiskStatus.OPEN },
  { id: 'r2', description: 'Gamma Rays overloaded in Sprint 3', impact: 'Medium', status: RiskStatus.MITIGATED },
];

const INITIAL_DEPS: Dependency[] = [
  { id: 'd1', fromFeatureId: 'f5', toFeatureId: 'f4', description: 'Order history needs payments' },
  { id: 'd2', fromFeatureId: 'f6', toFeatureId: 'f1', description: 'Admin needs auth' },
  { id: 'd3', fromFeatureId: 'f7', toFeatureId: 'f5', description: 'Analytics needs order data' },
];

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [teams, setTeams] = useState<Team[]>(INITIAL_TEAMS);
  const [risks, setRisks] = useState<Risk[]>(INITIAL_RISKS);
  const [dependencies, setDependencies] = useState<Dependency[]>(INITIAL_DEPS);

  // Auto-generate dependencies based on some logic or manual input would go here
  // For now, we use the static list plus any added via UI (if UI existed for it)

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard teams={teams} risks={risks} dependencies={dependencies} />;
      case 'teams':
        return <TeamBoard teams={teams} setTeams={setTeams} />;
      case 'dependencies':
        return <DependencyGraph teams={teams} dependencies={dependencies} />;
      case 'risks':
        return <RiskRegister risks={risks} setRisks={setRisks} teams={teams} dependencies={dependencies} />;
      default:
        return <Dashboard teams={teams} risks={risks} dependencies={dependencies} />;
    }
  };

  return (
    <div className="flex h-screen w-screen bg-slate-50 font-sans text-slate-900 overflow-hidden">
      <Navigation currentView={currentView} onNavigate={setCurrentView} />
      <main className="flex-1 h-full overflow-hidden relative">
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-[0.03] pointer-events-none"></div>
        {renderView()}
      </main>
    </div>
  );
};

export default App;
