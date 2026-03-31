import React from 'react';
import { formatDateTime } from '../../utils/formatters';

const RecentActivity = ({ activities }) => {
  return (
    <div className="rounded-xl bg-white p-5 shadow-lg">
      <h3 className="text-lg font-semibold text-gray-800">Recent Activity</h3>
      <p className="text-sm text-gray-500">Latest system events</p>

      <div className="mt-4 space-y-3">
        {activities?.map((activity, index) => (
          <div key={`${activity.timestamp}-${index}`} className="rounded-lg bg-gray-50 p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">{activity.type}</span>
              <span className="text-xs text-gray-500">
                {formatDateTime(activity.timestamp)}
              </span>
            </div>
            {activity.score !== undefined && (
              <p className="text-xs text-gray-600">Score: {activity.score.toFixed(2)}</p>
            )}
            {activity.cost !== undefined && (
              <p className="text-xs text-gray-600">Cost: ${activity.cost.toFixed(2)}</p>
            )}
            {activity.delta !== undefined && (
              <p className="text-xs text-gray-600">Delta: {activity.delta.toFixed(2)}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentActivity;
