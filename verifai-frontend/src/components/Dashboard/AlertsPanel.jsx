import React from 'react';

const ALERT_STYLES = {
  warning: 'border-yellow-200 bg-yellow-50 text-yellow-800',
  info: 'border-blue-200 bg-blue-50 text-blue-800',
  critical: 'border-red-200 bg-red-50 text-red-800',
};

const AlertsPanel = ({ alerts }) => {
  return (
    <div className="rounded-xl bg-white p-5 shadow-lg">
      <h3 className="text-lg font-semibold text-gray-800">Alerts</h3>
      <p className="text-sm text-gray-500">System notifications</p>

      <div className="mt-4 space-y-3">
        {alerts?.map((alert, index) => (
          <div
            key={`${alert.title}-${index}`}
            className={`rounded-lg border p-3 ${ALERT_STYLES[alert.level] || ALERT_STYLES.info}`}
          >
            <p className="text-sm font-semibold">{alert.title}</p>
            <p className="text-xs">{alert.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsPanel;
