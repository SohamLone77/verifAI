import React from 'react';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

const ConsensusViz = ({ consensus }) => {
  const getDecisionIcon = () => {
    switch (consensus.final_decision) {
      case 'APPROVED':
        return <CheckCircle className="h-12 w-12 text-green-500" />;
      case 'REJECTED':
        return <XCircle className="h-12 w-12 text-red-500" />;
      default:
        return <AlertTriangle className="h-12 w-12 text-yellow-500" />;
    }
  };

  return (
    <div className="rounded-lg bg-gradient-to-r from-gray-50 to-gray-100 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {getDecisionIcon()}
          <div>
            <p className="text-sm text-gray-500">Final Decision</p>
            <p className="text-2xl font-bold text-gray-800">{consensus.final_decision}</p>
          </div>
        </div>

        <div className="text-right">
          <p className="text-sm text-gray-500">Consensus Score</p>
          <p className="text-3xl font-bold text-blue-600">
            {(consensus.final_score * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      <div className="mt-4">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Confidence</span>
          <span>{(consensus.confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="mt-1 h-2 rounded-full bg-gray-200">
          <div
            className="h-2 rounded-full bg-blue-500 transition-all"
            style={{ width: `${consensus.confidence * 100}%` }}
          />
        </div>
      </div>

      {consensus.disagreements && consensus.disagreements.length > 0 && (
        <div className="mt-4 rounded-lg bg-yellow-50 p-3">
          <p className="text-sm font-medium text-yellow-800">Disagreements Detected</p>
          <p className="mt-1 text-xs text-yellow-700">
            {consensus.disagreements.length} disagreement(s) requiring attention
          </p>
        </div>
      )}
    </div>
  );
};

export default ConsensusViz;
