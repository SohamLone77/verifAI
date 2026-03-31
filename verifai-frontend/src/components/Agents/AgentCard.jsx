import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  CheckCircle,
  AlertTriangle,
  Brain,
  Clock,
  Award,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

const AgentCard = ({ agent, isExpanded, onToggle }) => {
  const role = agent.role || '';

  const getRoleIcon = (value) => {
    switch (value) {
      case 'safety_expert':
        return <Shield className="h-5 w-5 text-red-500" />;
      case 'factuality_checker':
        return <CheckCircle className="h-5 w-5 text-blue-500" />;
      case 'brand_guardian':
        return <Award className="h-5 w-5 text-purple-500" />;
      case 'latency_analyst':
        return <Clock className="h-5 w-5 text-orange-500" />;
      default:
        return <Brain className="h-5 w-5 text-gray-500" />;
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const displayName = agent.agent_name || agent.name || 'Agent';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border border-gray-200 bg-white shadow-sm"
    >
      <div
        className="flex cursor-pointer items-center justify-between p-4 hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-center space-x-3">
          {getRoleIcon(role)}
          <div>
            <h4 className="font-medium text-gray-800">{displayName}</h4>
            <p className="text-xs text-gray-500">{role.replace('_', ' ')}</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className={`text-lg font-bold ${getScoreColor(agent.score || 0)}`}>
              {((agent.score || 0) * 100).toFixed(0)}%
            </p>
            <p className="text-xs text-gray-500">Score</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-gray-700">
              {((agent.confidence || 0) * 100).toFixed(0)}%
            </p>
            <p className="text-xs text-gray-500">Confidence</p>
          </div>
          {isExpanded ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-gray-100 p-4"
          >
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-700">Reasoning</p>
                <p className="mt-1 text-sm text-gray-600">{agent.reasoning || 'No reasoning provided.'}</p>
              </div>

              {agent.flags && agent.flags.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700">Flags</p>
                  <div className="mt-1 space-y-1">
                    {agent.flags.slice(0, 3).map((flag, idx) => (
                      <div key={idx} className="flex items-center space-x-2 text-sm text-red-600">
                        <AlertTriangle className="h-3 w-3" />
                        <span>{flag.description || flag.type}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {agent.suggestions && agent.suggestions.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700">Suggestions</p>
                  <ul className="mt-1 list-disc pl-4 text-sm text-gray-600">
                    {agent.suggestions.slice(0, 2).map((suggestion, idx) => (
                      <li key={idx}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>Processing: {(agent.processing_time_ms || 0).toFixed(0)}ms</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default AgentCard;
