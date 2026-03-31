import React from 'react';
import { formatCurrency } from '../../utils/formatters';

const SavingsBreakdown = ({ savingsData }) => {
  const total = savingsData?.reduce((sum, item) => sum + item.value, 0) || 0;

  return (
    <div className="rounded-xl bg-white p-5 shadow-lg">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Savings Breakdown</h3>
        <p className="text-sm text-gray-500">Annual impact by category</p>
      </div>

      <div className="space-y-4">
        {savingsData?.map((item) => (
          <div key={item.name} className="rounded-lg bg-gray-50 p-3">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-gray-700">{item.name}</span>
              <span className="text-gray-600">{formatCurrency(item.value)}</span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-gray-200">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-green-500 to-emerald-500"
                style={{ width: `${total ? (item.value / total) * 100 : 0}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SavingsBreakdown;
