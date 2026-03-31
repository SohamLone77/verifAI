import React from 'react';
import AgentPanel from '../components/Agents/AgentPanel';

const AgentsPage = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Multi-Agent Review</h1>
        <p className="text-sm text-gray-500">Run agent consensus checks against content.</p>
      </div>
      <AgentPanel />
    </div>
  );
};

export default AgentsPage;
