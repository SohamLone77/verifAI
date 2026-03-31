import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

const CostBreakdownChart = ({ costData }) => {
  const byModel = costData?.byModel || [];
  const byAgent = costData?.byAgent || [];
  const byTask = costData?.byTask || [];

  return (
    <div className="rounded-xl bg-white p-5 shadow-lg">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Cost Breakdown</h3>
        <p className="text-sm text-gray-500">Split by model, agent, and task</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="h-72">
          <p className="mb-2 text-sm font-medium text-gray-600">By Model</p>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={byModel}
                dataKey="value"
                nameKey="name"
                innerRadius={50}
                outerRadius={90}
                paddingAngle={2}
              >
                {byModel.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="h-72">
          <p className="mb-2 text-sm font-medium text-gray-600">By Agent</p>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={byAgent}
                dataKey="value"
                nameKey="name"
                innerRadius={50}
                outerRadius={90}
                paddingAngle={2}
              >
                {byAgent.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="h-72">
          <p className="mb-2 text-sm font-medium text-gray-600">By Task</p>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={byTask}
                dataKey="value"
                nameKey="name"
                innerRadius={50}
                outerRadius={90}
                paddingAngle={2}
              >
                {byTask.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default CostBreakdownChart;
