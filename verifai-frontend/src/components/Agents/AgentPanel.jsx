import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Users, TrendingUp, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

import { agentAPI } from '../../services/api';
import AgentCard from './AgentCard';
import ConsensusViz from './ConsensusViz';
import AgentPerformance from './AgentPerformance';

const AgentPanel = ({ initialContent = 'This product is the best ever!' }) => {
  const [loading, setLoading] = useState(false);
  const [expandedAgent, setExpandedAgent] = useState(null);
  const [reviewData, setReviewData] = useState(null);
  const [selectedDepth, setSelectedDepth] = useState('standard');
  const [selectedStrategy, setSelectedStrategy] = useState('weighted_voting');
  const [content, setContent] = useState(initialContent);
  const [contextText, setContextText] = useState('');
  const [contextError, setContextError] = useState('');
  const [requiredAgents, setRequiredAgents] = useState([]);

  const agentOptions = [
    { value: 'safety_expert', label: 'Safety Expert' },
    { value: 'factuality_checker', label: 'Factuality Checker' },
    { value: 'brand_guardian', label: 'Brand Guardian' },
    { value: 'latency_analyst', label: 'Latency Analyst' },
    { value: 'compliance_specialist', label: 'Compliance Specialist' },
    { value: 'ux_reviewer', label: 'UX Reviewer' },
  ];

  const toggleRequiredAgent = (role) => {
    setRequiredAgents((prev) =>
      prev.includes(role) ? prev.filter((value) => value !== role) : [...prev, role]
    );
  };

  const performReview = async () => {
    if (!content.trim()) {
      toast.error('Please enter content to review');
      return;
    }

    let parsedContext = null;
    if (contextText.trim()) {
      try {
        parsedContext = JSON.parse(contextText);
      } catch (error) {
        setContextError('Context must be valid JSON');
        toast.error('Context must be valid JSON');
        return;
      }

      if (!parsedContext || typeof parsedContext !== 'object' || Array.isArray(parsedContext)) {
        setContextError('Context must be a JSON object');
        toast.error('Context must be a JSON object');
        return;
      }
    }

    setLoading(true);
    try {
      const payload = {
        content,
        review_depth: selectedDepth,
        strategy: selectedStrategy,
      };

      if (parsedContext) {
        payload.context = parsedContext;
      }

      if (requiredAgents.length > 0) {
        payload.required_agents = requiredAgents;
      }

      const response = await agentAPI.review(payload);

      setReviewData(response);
      toast.success('Multi-agent review completed');
    } catch (error) {
      toast.error('Review failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const agentCount = reviewData?.agent_responses?.length || 5;

  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-white p-6 shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">Multi-Agent Review Panel</h3>
            <p className="text-sm text-gray-500">{agentCount} specialized agents analyzing content</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <select
              value={selectedDepth}
              onChange={(e) => setSelectedDepth(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="quick">Quick Review</option>
              <option value="standard">Standard Review</option>
              <option value="deep">Deep Review</option>
            </select>

            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="weighted_voting">Weighted Voting</option>
              <option value="majority">Majority</option>
              <option value="unanimous">Unanimous</option>
              <option value="dynamic">Dynamic</option>
            </select>

            <button
              onClick={performReview}
              disabled={loading}
              className="flex items-center space-x-2 rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-2 text-white transition-all hover:from-blue-600 hover:to-blue-700 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Users className="h-4 w-4" />
                  <span>Run Multi-Agent Review</span>
                </>
              )}
            </button>
          </div>
        </div>

        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700">Content</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={4}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700">Context (JSON)</label>
          <textarea
            value={contextText}
            onChange={(e) => {
              setContextText(e.target.value);
              if (contextError) setContextError('');
            }}
            rows={3}
            placeholder='{"channel": "email", "audience": "enterprise"}'
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          {contextError && <p className="mt-1 text-xs text-red-600">{contextError}</p>}
        </div>

        <div className="mt-4">
          <p className="text-sm font-medium text-gray-700">Required Agents</p>
          <p className="text-xs text-gray-500">Leave empty to use the default agent set.</p>
          <div className="mt-2 grid gap-2 md:grid-cols-2">
            {agentOptions.map((option) => (
              <label key={option.value} className="flex items-center space-x-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={requiredAgents.includes(option.value)}
                  onChange={() => toggleRequiredAgent(option.value)}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {reviewData && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <ConsensusViz consensus={reviewData.consensus} />

          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-gray-100 bg-white p-4 shadow-sm">
              <p className="text-xs text-gray-500">Processing Time</p>
              <p className="text-lg font-semibold text-gray-800">
                {(reviewData.processing_time_ms || 0).toFixed(0)} ms
              </p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-white p-4 shadow-sm">
              <p className="text-xs text-gray-500">Tokens Used</p>
              <p className="text-lg font-semibold text-gray-800">
                {(reviewData.tokens_used || 0).toLocaleString()}
              </p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-white p-4 shadow-sm">
              <p className="text-xs text-gray-500">Estimated Cost</p>
              <p className="text-lg font-semibold text-gray-800">
                ${Number(reviewData.cost || 0).toFixed(4)}
              </p>
            </div>
          </div>

          <div>
            <h4 className="mb-3 text-lg font-semibold text-gray-800">Agent Analysis</h4>
            <div className="space-y-3">
              {reviewData.agent_responses.map((agent, idx) => (
                <AgentCard
                  key={agent.agent_id || agent.agent_name || idx}
                  agent={agent}
                  isExpanded={expandedAgent === idx}
                  onToggle={() => setExpandedAgent(expandedAgent === idx ? null : idx)}
                />
              ))}
            </div>
          </div>

          <div className="rounded-xl bg-blue-50 p-6">
            <h4 className="mb-3 flex items-center space-x-2 text-lg font-semibold text-blue-800">
              <TrendingUp className="h-5 w-5" />
              <span>Recommendations</span>
            </h4>
            <ul className="space-y-2">
              {reviewData.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start space-x-2 text-sm text-blue-700">
                  <span className="mt-0.5 text-blue-400">-</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-sm text-gray-600">{reviewData.summary}</p>
          </div>

          <AgentPerformance
            performance={reviewData.agent_responses.map((agent) => ({
              name: agent.agent_name || agent.name || 'Agent',
              role: (agent.role || '').replace('_', ' '),
              average_score: agent.score,
              average_latency_ms: agent.processing_time_ms,
            }))}
          />
        </motion.div>
      )}
    </div>
  );
};

export default AgentPanel;
