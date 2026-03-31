import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Users, TrendingUp, RefreshCw } from 'lucide-react';
import AgentCard from './AgentCard';
import ConsensusViz from './ConsensusViz';
import AgentPerformance from './AgentPerformance';

const AgentPanel = ({ content, onReviewComplete }) => {
  const [loading, setLoading] = useState(false);
  const [expandedAgent, setExpandedAgent] = useState(null);
  const [reviewData, setReviewData] = useState(null);
  const [selectedDepth, setSelectedDepth] = useState('standard');

  const performReview = async () => {
    setLoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 2000));

      const mockResponse = {
        consensus: {
          final_decision: 'NEEDS_REVIEW',
          final_score: 0.67,
          consensus_reached: false,
          confidence: 0.72,
          disagreements: [{ agent_a: 'SafetyGuard', agent_b: 'FactChecker' }],
        },
        agent_responses: [
          {
            name: 'SafetyGuard',
            role: 'safety_expert',
            score: 0.85,
            confidence: 0.9,
            reasoning: 'No safety violations detected. Content appears safe.',
            flags: [],
            suggestions: [],
            processing_time_ms: 234,
          },
          {
            name: 'FactChecker',
            role: 'factuality_checker',
            score: 0.45,
            confidence: 0.75,
            reasoning: 'Exaggerated claims detected without supporting evidence.',
            flags: [{ type: 'exaggeration', description: 'Unsubstantiated best ever claim' }],
            suggestions: ['Replace hyperbole with specific benefits'],
            processing_time_ms: 312,
          },
          {
            name: 'BrandGuardian',
            role: 'brand_guardian',
            score: 0.62,
            confidence: 0.82,
            reasoning: 'Brand voice is slightly off-brand. Overpromising tone.',
            flags: [{ type: 'brand_voice', description: 'Overpromising language detected' }],
            suggestions: ['Adjust tone to be more professional'],
            processing_time_ms: 278,
          },
          {
            name: 'LatencyAnalyst',
            role: 'latency_analyst',
            score: 0.92,
            confidence: 0.95,
            reasoning: 'Content length is appropriate. No latency concerns.',
            flags: [],
            suggestions: [],
            processing_time_ms: 156,
          },
        ],
        recommendations: [
          'Replace exaggerated claims with specific, verifiable benefits',
          'Adjust tone to match brand guidelines',
          'Add supporting evidence for key claims',
        ],
        summary:
          'Decision: NEEDS_REVIEW (Score: 0.67) | Agent Scores: SafetyGuard: 0.85, FactChecker: 0.45, BrandGuardian: 0.62, LatencyAnalyst: 0.92 | Key Issues: exaggeration, brand_voice',
      };

      setReviewData(mockResponse);
      if (onReviewComplete) onReviewComplete(mockResponse);
    } catch (error) {
      // Keep silent for demo
      console.error('Review failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const agentCount = reviewData?.agent_responses?.length || 4;

  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-white p-6 shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">Multi-Agent Review Panel</h3>
            <p className="text-sm text-gray-500">{agentCount} specialized agents analyzing content</p>
          </div>

          <div className="flex items-center space-x-3">
            <select
              value={selectedDepth}
              onChange={(e) => setSelectedDepth(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="quick">Quick Review</option>
              <option value="standard">Standard Review</option>
              <option value="deep">Deep Review</option>
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
      </div>

      {reviewData && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <ConsensusViz consensus={reviewData.consensus} />

          <div>
            <h4 className="mb-3 text-lg font-semibold text-gray-800">Agent Analysis</h4>
            <div className="space-y-3">
              {reviewData.agent_responses.map((agent, idx) => (
                <AgentCard
                  key={agent.name}
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
              name: agent.name,
              role: agent.role.replace('_', ' '),
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
