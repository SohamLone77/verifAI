import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { Activity, DollarSign, RefreshCw, TrendingUp } from 'lucide-react';
import { costAPI } from '../services/api';
import MetricCard from '../components/Dashboard/MetricCard';
import CostBreakdownChart from '../components/Dashboard/CostBreakdownChart';
import RecentActivity from '../components/Dashboard/RecentActivity';
import LoadingSpinner from '../components/Common/LoadingSpinner';

const CostPage = () => {
  const queryClient = useQueryClient();
  const timeRanges = [
    { label: '7D', value: 7 },
    { label: '30D', value: 30 },
    { label: '90D', value: 90 },
  ];
  const [selectedDays, setSelectedDays] = useState(30);
  const [budgetForm, setBudgetForm] = useState({
    daily_budget: '',
    weekly_budget: '',
    monthly_budget: '',
  });

  const {
    data,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery(
    ['cost-dashboard', selectedDays],
    () => costAPI.getDashboard(selectedDays),
    {
      staleTime: 10000,
      refetchInterval: 20000,
    }
  );

  const { data: optimizationsData } = useQuery(
    ['cost-optimizations', selectedDays],
    () => costAPI.getOptimizations(),
    {
      staleTime: 60000,
    }
  );

  const applyMutation = useMutation((id) => costAPI.applyOptimization(id), {
    onSuccess: () => {
      queryClient.invalidateQueries(['cost-optimizations']);
    },
  });

  const budgetMutation = useMutation((payload) => costAPI.setBudget(payload), {
    onSuccess: () => {
      queryClient.invalidateQueries(['cost-dashboard']);
    },
  });

  const summary = data?.summary || {
    totalCost: 0,
    totalReviews: 0,
    averageCost: 0,
    costSaved: 0,
  };

  const costBreakdown = data?.breakdown || { byModel: [], byAgent: [], byTask: [] };
  const budget = data?.budget || {
    budget_limit: 0,
    current_cost: 0,
    remaining: 0,
    usage_percentage: 0,
    status: 'unset',
    daily_budget: null,
    weekly_budget: null,
    monthly_budget: null,
  };
  const recentActivity = data?.recentActivity || [];
  const suggestions = optimizationsData?.suggestions || [];

  const budgetUsage = useMemo(() => {
    const percentage = Math.min(1, Math.max(0, budget.usage_percentage || 0));
    return {
      percent: Math.round(percentage * 100),
      status: budget.status || 'unset',
    };
  }, [budget]);

  const handleBudgetSubmit = () => {
    const payload = {
      daily_budget: budgetForm.daily_budget || null,
      weekly_budget: budgetForm.weekly_budget || null,
      monthly_budget: budgetForm.monthly_budget || null,
    };
    budgetMutation.mutate(payload);
  };

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <p className="text-red-500">Failed to load cost tracking data</p>
          <button className="mt-2 rounded-lg bg-blue-500 px-4 py-2 text-white">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Cost Tracking</h1>
          <p className="text-sm text-gray-500">Usage, budgets, and optimization signals</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex rounded-lg border border-gray-200 bg-white shadow-sm">
            {timeRanges.map((range) => (
              <button
                key={range.value}
                onClick={() => setSelectedDays(range.value)}
                className={`px-3 py-1.5 text-sm transition-colors ${
                  selectedDays === range.value
                    ? 'bg-gray-100 text-gray-800'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                } ${range.value === 90 ? 'rounded-r-lg' : ''} ${
                  range.value === 7 ? 'rounded-l-lg' : ''
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
          <button
            onClick={() => refetch()}
            className="flex items-center space-x-2 rounded-lg bg-white px-4 py-2 shadow-sm hover:bg-gray-50"
          >
            <RefreshCw className={`h-4 w-4 text-gray-500 ${isFetching ? 'animate-spin' : ''}`} />
            <span className="text-sm">{isFetching ? 'Refreshing' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Cost"
          value={summary.totalCost}
          subtitle={`Last ${selectedDays} days`}
          icon={DollarSign}
          color="orange"
        />
        <MetricCard
          title="Average Cost"
          value={summary.averageCost}
          subtitle="Per review"
          icon={TrendingUp}
          color="purple"
        />
        <MetricCard
          title="Total Reviews"
          value={summary.totalReviews}
          subtitle={`Last ${selectedDays} days`}
          icon={Activity}
          color="blue"
        />
        <MetricCard
          title="Savings"
          value={summary.costSaved}
          subtitle="Estimated"
          icon={TrendingUp}
          color="green"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <CostBreakdownChart costData={costBreakdown} />
        <div className="rounded-xl bg-white p-5 shadow-lg">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Budget Status</h3>
            <p className="text-sm text-gray-500">Track spend against your targets</p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Current spend</span>
              <span className="font-semibold text-gray-800">${budget.current_cost.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Budget limit</span>
              <span className="font-semibold text-gray-800">
                {budget.budget_limit ? `$${budget.budget_limit.toFixed(2)}` : 'Not set'}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Remaining</span>
              <span className="font-semibold text-gray-800">${budget.remaining.toFixed(2)}</span>
            </div>

            <div className="h-2 w-full rounded-full bg-gray-100">
              <div
                className={`h-2 rounded-full ${
                  budgetUsage.status === 'critical'
                    ? 'bg-red-500'
                    : budgetUsage.status === 'warning'
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
                }`}
                style={{ width: `${budgetUsage.percent}%` }}
              />
            </div>
            <div className="text-xs text-gray-500">
              {budgetUsage.status === 'unset'
                ? 'Set a budget to enable alerts.'
                : `${budgetUsage.percent}% used`}
            </div>
          </div>

          <div className="mt-6 space-y-3">
            <p className="text-sm font-semibold text-gray-800">Update budgets</p>
            <div className="grid gap-3 sm:grid-cols-3">
              <input
                type="number"
                min="0"
                placeholder={budget.daily_budget ? `Daily ($${budget.daily_budget})` : 'Daily'}
                value={budgetForm.daily_budget}
                onChange={(event) =>
                  setBudgetForm((prev) => ({ ...prev, daily_budget: event.target.value }))
                }
                className="rounded-lg border border-gray-200 px-3 py-2 text-sm"
              />
              <input
                type="number"
                min="0"
                placeholder={budget.weekly_budget ? `Weekly ($${budget.weekly_budget})` : 'Weekly'}
                value={budgetForm.weekly_budget}
                onChange={(event) =>
                  setBudgetForm((prev) => ({ ...prev, weekly_budget: event.target.value }))
                }
                className="rounded-lg border border-gray-200 px-3 py-2 text-sm"
              />
              <input
                type="number"
                min="0"
                placeholder={budget.monthly_budget ? `Monthly ($${budget.monthly_budget})` : 'Monthly'}
                value={budgetForm.monthly_budget}
                onChange={(event) =>
                  setBudgetForm((prev) => ({ ...prev, monthly_budget: event.target.value }))
                }
                className="rounded-lg border border-gray-200 px-3 py-2 text-sm"
              />
            </div>
            <button
              onClick={handleBudgetSubmit}
              className="rounded-lg bg-blue-500 px-4 py-2 text-sm text-white hover:bg-blue-600"
            >
              {budgetMutation.isLoading ? 'Saving...' : 'Save Budget'}
            </button>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <RecentActivity activities={recentActivity} />
        <div className="rounded-xl bg-white p-5 shadow-lg">
          <h3 className="text-lg font-semibold text-gray-800">Optimization Suggestions</h3>
          <p className="text-sm text-gray-500">Quick wins to reduce spend</p>

          <div className="mt-4 space-y-3">
            {suggestions.length === 0 ? (
              <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-500">
                No optimization suggestions yet.
              </div>
            ) : (
              suggestions.map((suggestion) => (
                <div key={suggestion.suggestion_id} className="rounded-lg border border-gray-200 p-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-semibold text-gray-800">{suggestion.title}</p>
                      <p className="text-xs text-gray-500">{suggestion.description}</p>
                    </div>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        suggestion.priority === 'high'
                          ? 'bg-red-100 text-red-700'
                          : suggestion.priority === 'medium'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {suggestion.priority}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                    <span>Est. savings: ${suggestion.estimated_savings.toFixed(2)}</span>
                    <button
                      onClick={() => applyMutation.mutate(suggestion.suggestion_id)}
                      disabled={suggestion.applied || applyMutation.isLoading}
                      className={`rounded-lg px-3 py-1 text-xs ${
                        suggestion.applied
                          ? 'bg-gray-100 text-gray-400'
                          : 'bg-emerald-500 text-white hover:bg-emerald-600'
                      }`}
                    >
                      {suggestion.applied ? 'Applied' : 'Apply'}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CostPage;
