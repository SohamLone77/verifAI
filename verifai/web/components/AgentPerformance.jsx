import React from 'react';

const AgentPerformance = ({ performance }) => {
  const agents = performance || [];

  return (
    <div className="rounded-xl bg-white p-5 shadow-lg">
      <h3 className="text-lg font-semibold text-gray-800">Agent Performance</h3>
      <p className="text-sm text-gray-500">Operational metrics by agent</p>

      <div className="mt-4 space-y-3">
        {agents.map((agent) => (
          <div key={agent.name} className="rounded-lg bg-gray-50 p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">{agent.name}</p>
                <p className="text-xs text-gray-500">{agent.role}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-gray-700">
                  Avg Score: {agent.average_score?.toFixed(2)}
                </p>
                <p className="text-xs text-gray-500">
                  Latency: {agent.average_latency_ms?.toFixed(0)} ms
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentPerformance;
